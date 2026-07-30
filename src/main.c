#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_pm.h"
#include "esp_timer.h"
#include "esp_log.h"

static const char *TAG = "fused_glass";

/* --- Pin assignments --- */
#define POT_ADC_CHANNEL     ADC_CHANNEL_3       /* GPIO3 (D1) = ADC1 channel 3 */
#define MOTION_SENSOR_GPIO  GPIO_NUM_5          /* D3 - digital input */
#define LED_PWM_GPIO        GPIO_NUM_4          /* D2 - LEDC PWM output to MOSFET gate */

/* --- LEDC (PWM) configuration --- */
#define LEDC_SPEED_MODE     LEDC_LOW_SPEED_MODE /* ESP32-C3 only has low-speed mode */
#define LEDC_TIMER          LEDC_TIMER_0
#define LEDC_CHANNEL        LEDC_CHANNEL_0
#define LEDC_DUTY_RES       LEDC_TIMER_13_BIT   /* 13-bit: 0-8191 */
#define LEDC_FREQUENCY      5000                /* 5 kHz - no audible buzz, no visible flicker */
#define LEDC_MAX_DUTY       ((1 << 13) - 1)     /* 8191 */
#define MIN_ON_DUTY         410                 /* ~5% of 8191: minimum visible brightness */

/* --- Timing --- */
#define OCCUPANCY_TIMEOUT_MS    (10 * 1000)     /* 10 seconds */
#define POLL_ACTIVE_MS          50              /* 50 ms when LEDs are on (pot + sensor) */
#define POLL_IDLE_MS            200             /* 200 ms when LEDs are off (sensor only) */
#define FADE_ON_OFF_MS          500             /* fade duration for on/off transitions */
#define FADE_ADJUST_MS          100             /* fade duration for live pot adjustments */

/* --- ADC --- */
#define ADC_SAMPLES             8               /* number of samples to average */
#define ADC_HYSTERESIS          50              /* ~0.6% of 8191, prevents jitter */

/* --- Debug --- */
#define DEBUG_LOGGING           1               /* debug logs enabled */

/* --- M-out-of-N motion filtering --- */
#define MOTION_WINDOW_N         5               /* window size: last N readings */
#define MOTION_THRESHOLD_M      3               /* require M HIGH readings to trigger */

/* --- State machine --- */
typedef enum {
    STATE_LEDS_OFF,
    STATE_LEDS_ON,
} led_state_t;

static adc_oneshot_unit_handle_t adc1_handle = NULL;

/* ------------------------------------------------------------------ */
/*  Initialization                                                     */
/* ------------------------------------------------------------------ */

static void init_power_management(void)
{
    esp_pm_config_t pm_config = {
        .max_freq_mhz = 160,
        .min_freq_mhz = 40,            /* XTAL frequency — lowest for maximum power savings */
        .light_sleep_enable = false,    /* disabled: conflicts with LEDC PWM */
    };
    ESP_ERROR_CHECK(esp_pm_configure(&pm_config));
    ESP_LOGI(TAG, "Power management enabled (DFS only, 40-160 MHz)");
}

static void init_ledc(void)
{
    /* Configure GPIO4 as output LOW before enabling LEDC to prevent glitch */
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << LED_PWM_GPIO),
        .mode         = GPIO_MODE_OUTPUT,
        .pull_up_en   = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&io_conf));
    gpio_set_level(LED_PWM_GPIO, 0);

    ledc_timer_config_t timer_conf = {
        .speed_mode       = LEDC_SPEED_MODE,
        .timer_num        = LEDC_TIMER,
        .duty_resolution  = LEDC_DUTY_RES,
        .freq_hz          = LEDC_FREQUENCY,
        .clk_cfg          = LEDC_AUTO_CLK,
    };
    ESP_ERROR_CHECK(ledc_timer_config(&timer_conf));

    ledc_channel_config_t channel_conf = {
        .gpio_num       = LED_PWM_GPIO,
        .speed_mode     = LEDC_SPEED_MODE,
        .channel        = LEDC_CHANNEL,
        .intr_type      = LEDC_INTR_DISABLE,
        .timer_sel      = LEDC_TIMER,
        .duty           = 0,
        .hpoint         = 0,
        .flags.output_invert = 0,
    };
    ESP_ERROR_CHECK(ledc_channel_config(&channel_conf));

    ESP_ERROR_CHECK(ledc_fade_func_install(0));
}

static void init_motion_sensor(void)
{
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << MOTION_SENSOR_GPIO),
        .mode         = GPIO_MODE_INPUT,
        .pull_up_en   = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&io_conf));
}

static void init_adc(void)
{
    adc_oneshot_unit_init_cfg_t init_cfg = {
        .unit_id  = ADC_UNIT_1,
        .ulp_mode = ADC_ULP_MODE_DISABLE,
    };
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&init_cfg, &adc1_handle));

    adc_oneshot_chan_cfg_t chan_cfg = {
        .bitwidth = ADC_BITWIDTH_DEFAULT,
        .atten    = ADC_ATTEN_DB_12,
    };
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc1_handle, POT_ADC_CHANNEL, &chan_cfg));
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

static int read_potentiometer_averaged(void)
{
    int sum = 0;
    int raw = 0;
    for (int i = 0; i < ADC_SAMPLES; i++) {
        ESP_ERROR_CHECK(adc_oneshot_read(adc1_handle, POT_ADC_CHANNEL, &raw));
        sum += raw;
    }
    return sum / ADC_SAMPLES;
}

static uint32_t adc_to_duty(int adc_value)
{
    return (uint32_t)((int64_t)adc_value * LEDC_MAX_DUTY / 4095);
}

static void set_led_brightness(uint32_t target_duty, uint32_t fade_ms)
{
    ESP_ERROR_CHECK(ledc_set_fade_with_time(
        LEDC_SPEED_MODE, LEDC_CHANNEL, target_duty, fade_ms));
    ESP_ERROR_CHECK(ledc_fade_start(
        LEDC_SPEED_MODE, LEDC_CHANNEL, LEDC_FADE_NO_WAIT));
}

/*
 * M-out-of-N motion filter.
 * Shifts a new reading into a circular buffer and returns true only when
 * at least MOTION_THRESHOLD_M of the last MOTION_WINDOW_N readings are HIGH.
 * This filters brief radar noise spikes (HVAC, fans, curtains) while still
 * responding quickly to real human presence (~250ms worst-case latency at
 * 50ms polling).
 */
static bool motion_filter(int raw_reading)
{
    static int buffer[MOTION_WINDOW_N];
    static int index = 0;
    static bool initialized = false;

    if (!initialized) {
        memset(buffer, 0, sizeof(buffer));
        initialized = true;
    }

    buffer[index] = raw_reading;
    index = (index + 1) % MOTION_WINDOW_N;

    int count = 0;
    for (int i = 0; i < MOTION_WINDOW_N; i++) {
        count += (buffer[i] != 0);
    }
    return count >= MOTION_THRESHOLD_M;
}

/* ------------------------------------------------------------------ */
/*  Main application                                                   */
/* ------------------------------------------------------------------ */

void app_main(void)
{
    ESP_LOGI(TAG, "Fused Glass Lighting - Initializing...");

    init_power_management();
    init_ledc();
    init_motion_sensor();
    init_adc();

    ESP_LOGI(TAG, "Initialization complete.");

    led_state_t state = STATE_LEDS_OFF;
    int64_t last_motion_time_ms = 0;
    uint32_t applied_duty = 0;

#if DEBUG_LOGGING
    int debug_counter = 0;
#endif

    while (1) {
        /* Read motion sensor and run through M-out-of-N filter */
        int raw_motion = gpio_get_level(MOTION_SENSOR_GPIO);
        bool motion = motion_filter(raw_motion);

        int64_t now_ms = esp_timer_get_time() / 1000;

#if DEBUG_LOGGING
        /* Print debug info every ~1 second */
        debug_counter++;
        int loops_per_sec = (state == STATE_LEDS_ON) ? (1000 / POLL_ACTIVE_MS) : (1000 / POLL_IDLE_MS);
        if (debug_counter >= loops_per_sec) {
            ESP_LOGI(TAG, "DEBUG: state=%s  raw_motion=%d  filtered=%d  applied_duty=%lu",
                     state == STATE_LEDS_OFF ? "OFF" : "ON",
                     raw_motion, motion, (unsigned long)applied_duty);
            debug_counter = 0;
        }
#endif

        switch (state) {
        case STATE_LEDS_OFF:
            if (motion) {
                int adc_raw = read_potentiometer_averaged();
                uint32_t desired_duty = adc_to_duty(adc_raw);
                if (desired_duty < MIN_ON_DUTY) desired_duty = MIN_ON_DUTY;
                ESP_LOGI(TAG, "Motion detected. LEDs ON (duty=%lu)", (unsigned long)desired_duty);
                applied_duty = desired_duty;
                set_led_brightness(applied_duty, FADE_ON_OFF_MS);
                last_motion_time_ms = now_ms;
                state = STATE_LEDS_ON;
            }
            break;

        case STATE_LEDS_ON:
            if (motion) {
                last_motion_time_ms = now_ms;
            }

            /* Update brightness if potentiometer changed beyond hysteresis */
            {
                int adc_raw = read_potentiometer_averaged();
                uint32_t desired_duty = adc_to_duty(adc_raw);
                if (desired_duty < MIN_ON_DUTY) desired_duty = MIN_ON_DUTY;
                int diff = (int)desired_duty - (int)applied_duty;
                if (diff > ADC_HYSTERESIS || diff < -ADC_HYSTERESIS) {
                    ESP_LOGI(TAG, "Brightness adjusted: %lu -> %lu",
                             (unsigned long)applied_duty, (unsigned long)desired_duty);
                    applied_duty = desired_duty;
                    set_led_brightness(applied_duty, FADE_ADJUST_MS);
                }
            }

            /* Check occupancy timeout */
            if ((now_ms - last_motion_time_ms) >= OCCUPANCY_TIMEOUT_MS) {
                ESP_LOGI(TAG, "No motion for 10s. LEDs OFF.");
                set_led_brightness(0, FADE_ON_OFF_MS);
                applied_duty = 0;
                state = STATE_LEDS_OFF;
            }
            break;
        }

        /* Poll faster when active (pot tracking), slower when idle (save power) */
        uint32_t delay_ms = (state == STATE_LEDS_ON) ? POLL_ACTIVE_MS : POLL_IDLE_MS;
        vTaskDelay(pdMS_TO_TICKS(delay_ms));
    }
}
