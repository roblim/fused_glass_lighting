/*
 * Fused Glass Lighting - Rev F
 * ---------------------------------------------------------------------------
 * Seeed XIAO ESP32-C3 (ESP-IDF) driving two 30 cm 3 V LED filaments at 300 mA
 * through a pair of CN5711 linear constant-current modules, gated by an
 * HLK-LD2410S 24 GHz presence radar and dimmed by a potentiometer.
 *
 * Powered from a 25,000 mAh USB powerbank, which requires a periodic dummy
 * load to stop the bank from shutting itself off while the lamp is dark.
 *
 * Changes from the previous iteration (MOSFET + XYC-WB-DC on a wall supply):
 *   - PWM moved from 5 kHz to 1 kHz. The CN5711 CE pin is specified below
 *     2 kHz; 5 kHz would produce erratic regulation, not just dimming error.
 *   - Output drives the commoned CE pins of both driver modules instead of a
 *     MOSFET gate. Same polarity (active high), so the logic is unchanged.
 *   - Off-delay shortened 60 s -> 25 s. Battery, not mains.
 *   - Explicit light sleep while dark, with GPIO wake on the radar.
 *   - Powerbank keep-alive pulse on D10.
 *   - Sensor watchdog stretched from 5 min to 12 h. The LD2410S reports
 *     STATIC presence, so a continuous HIGH for hours is legitimate now.
 * ---------------------------------------------------------------------------
 */

#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_pm.h"
#include "esp_sleep.h"
#include "esp_timer.h"
#include "esp_log.h"

static const char *TAG = "fused_glass";

/* ------------------------------------------------------------------ */
/*  Pin assignments (XIAO ESP32-C3)                                    */
/* ------------------------------------------------------------------ */
/*
 * Constraints that produced this map:
 *   - Only D0-D3 can wake the chip from light sleep.
 *   - Only A0/A1/A2 (GPIO2/3/4) are on ADC1. A3/GPIO5 is ADC2 and Seeed
 *     documents it as unreliable.
 *   - D0 (GPIO2), D8 (GPIO8), D9 (GPIO9) are strapping pins.
 *   - D6 (GPIO21) is U0TXD. The boot log comes out of it, so the radar
 *     UART must not live there or every reset injects garbage into the
 *     sensor's RX pin.
 *
 * Putting the radar on D3 works because it only needs a logic level, which
 * makes GPIO5's ADC2 problem irrelevant and keeps ADC1 free for the pot.
 */
#define POT_ADC_CHANNEL     ADC_CHANNEL_3       /* D1  / GPIO3  ADC1_CH3      */
#define RADAR_GPIO          GPIO_NUM_5          /* D3  / GPIO5  LD2410S OT2   */
#define DRIVER_CE_GPIO      GPIO_NUM_4          /* D2  / GPIO4  -> both CE    */
#define KEEPALIVE_GPIO      GPIO_NUM_10         /* D10 / GPIO10 MOSFET gate   */
/* D4 / GPIO6 -> radar RX, D5 / GPIO7 <- radar TX. Config only, unused here. */

/* ------------------------------------------------------------------ */
/*  LEDC (PWM) configuration                                           */
/* ------------------------------------------------------------------ */
#define LEDC_SPEED_MODE     LEDC_LOW_SPEED_MODE /* C3 has low-speed only      */
#define LEDC_TIMER          LEDC_TIMER_0
#define LEDC_CHANNEL        LEDC_CHANNEL_0
#define LEDC_DUTY_RES       LEDC_TIMER_13_BIT   /* 0-8191                     */
#define LEDC_FREQUENCY      1000                /* CN5711 CE: must be < 2 kHz */
#define LEDC_MAX_DUTY       ((1 << 13) - 1)

/*
 * Minimum on-duty, 5% of full scale. At 1 kHz that is a 50 us pulse, which is
 * long enough for the CN5711 current loop to settle. Shorter pulses make a
 * linear regulator stutter rather than dim smoothly. Raise this if the bottom
 * of the pot travel flickers.
 */
#define MIN_ON_DUTY         410

/* ------------------------------------------------------------------ */
/*  Timing                                                             */
/* ------------------------------------------------------------------ */
#define OCCUPANCY_TIMEOUT_MS    (25 * 1000)     /* off-delay, retriggerable   */
#define POLL_ACTIVE_MS          50              /* pot + sensor while lit     */
#define FADE_ON_OFF_MS          500
#define FADE_ADJUST_MS          100

/*
 * Stuck-sensor watchdog. The previous sensor was Doppler-only, so a HIGH
 * lasting more than a few minutes meant a fault. The LD2410S detects
 * stationary people, so someone reading in the room legitimately holds OT2
 * high indefinitely. Only a full half-day of unbroken HIGH is suspicious.
 */
#define SENSOR_WATCHDOG_MS      (12 * 60 * 60 * 1000LL)

/* ------------------------------------------------------------------ */
/*  Powerbank keep-alive                                               */
/* ------------------------------------------------------------------ */
/*
 * Powerbanks shut down when they see no meaningful load, typically below
 * 45-100 mA sustained for 15-60 s. Idle draw here is under 1 mA. A 33 ohm
 * dummy load pulsed briefly resets the bank's timer for ~3 mA average, where
 * holding the load continuously would cost 152 mA.
 *
 * Tune against your specific bank. If it still sleeps, LENGTHEN THE PULSE
 * before shortening the period - reliable detection matters more than
 * frequency.
 */
#define KEEPALIVE_PULSE_MS      200
#define KEEPALIVE_PERIOD_US     (10ULL * 1000ULL * 1000ULL)

/* ------------------------------------------------------------------ */
/*  ADC                                                                */
/* ------------------------------------------------------------------ */
#define ADC_SAMPLES             32
/*
 * The pot wiper is capped at about 2.25 V by a 4.7k top-leg resistor above
 * the 10k pot, because the C3 ADC goes badly nonlinear approaching 3.3 V. That
 * ceiling reads roughly 2960 counts rather than 4095.  Note the resistor sits
 * between 3V3 and the pot, NOT in series with the wiper -- a series resistor
 * into a high-impedance ADC pin would attenuate nothing.
 *
 * MEASURE THIS during bring-up: turn the pot fully clockwise, read the raw
 * value, and set the constant to what you actually see. If it is left too
 * high the lamp never reaches full brightness; too low and the top of the
 * knob travel does nothing.
 */
#define ADC_RAW_AT_MAX          2950
#define ADC_HYSTERESIS          75              /* ~2%, kills wiper jitter    */

#define DEBUG_LOGGING           1

/* ------------------------------------------------------------------ */
/*  Motion filtering                                                   */
/* ------------------------------------------------------------------ */
/*
 * The LD2410S already filters internally, so this is now belt-and-braces
 * against a noisy or failing module rather than the primary defence it was
 * with the bare Doppler sensor.
 */
#define MOTION_WINDOW_N         5
#define MOTION_THRESHOLD_M      3

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
        .max_freq_mhz       = 160,
        .min_freq_mhz       = 40,
        .light_sleep_enable = false,
    };
    ESP_ERROR_CHECK(esp_pm_configure(&pm_config));
    /*
     * Automatic light sleep stays off: an active LEDC timer holds a PM lock,
     * so the system could never enter it while the lamp is lit, and letting
     * it fire mid-fade would glitch the output. Instead we call
     * esp_light_sleep_start() explicitly once the filaments are dark, which
     * is the only time sleeping is safe or useful.
     */
    ESP_LOGI(TAG, "Power management: DFS 40-160 MHz, manual light sleep");
}

static void init_ledc(void)
{
    /* Park CE low before the peripheral takes the pin, or the filaments
     * flash at full current on every reset. */
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << DRIVER_CE_GPIO),
        .mode         = GPIO_MODE_OUTPUT,
        .pull_up_en   = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&io_conf));
    gpio_set_level(DRIVER_CE_GPIO, 0);

    ledc_timer_config_t timer_conf = {
        .speed_mode      = LEDC_SPEED_MODE,
        .timer_num       = LEDC_TIMER,
        .duty_resolution = LEDC_DUTY_RES,
        .freq_hz         = LEDC_FREQUENCY,
        /* XTAL rather than APB: dynamic frequency scaling must not be able
         * to drag the PWM frequency up past the CN5711's 2 kHz ceiling. */
        .clk_cfg         = LEDC_USE_XTAL_CLK,
    };
    ESP_ERROR_CHECK(ledc_timer_config(&timer_conf));

    ledc_channel_config_t channel_conf = {
        .gpio_num            = DRIVER_CE_GPIO,
        .speed_mode          = LEDC_SPEED_MODE,
        .channel             = LEDC_CHANNEL,
        .intr_type           = LEDC_INTR_DISABLE,
        .timer_sel           = LEDC_TIMER,
        .duty                = 0,
        .hpoint              = 0,
        .flags.output_invert = 0,
    };
    ESP_ERROR_CHECK(ledc_channel_config(&channel_conf));
    ESP_ERROR_CHECK(ledc_fade_func_install(0));

    /*
     * CRITICAL - do not remove. With CONFIG_PM_ENABLE the IDF startup path runs
     * esp_sleep_config_gpio_isolate(), which sets EVERY valid GPIO to
     * GPIO_MODE_DISABLE + GPIO_FLOATING for the duration of each light sleep.
     * That includes this pin. A floating CE lets the CN5711's internal pull-up
     * enable both drivers, so the filaments came on at full 300 mA for the whole
     * sleep and switched off only during the brief keep-alive wake - the exact
     * inverse of the intended behaviour, and a steady 600 mA drain on a
     * powerbank that is supposed to be idling.
     *
     * gpio_sleep_sel_dis() opts the pad out of that automatic switching, so it
     * holds the level ledc_stop() parked it at. Must be called after
     * ledc_channel_config(), which reconfigures the pad.
     */
    ESP_ERROR_CHECK(gpio_sleep_sel_dis(DRIVER_CE_GPIO));
}

static void init_radar(void)
{
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << RADAR_GPIO),
        .mode         = GPIO_MODE_INPUT,
        .pull_up_en   = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&io_conf));
}

static void init_keepalive(void)
{
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << KEEPALIVE_GPIO),
        .mode         = GPIO_MODE_OUTPUT,
        .pull_up_en   = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&io_conf));
    gpio_set_level(KEEPALIVE_GPIO, 0);

    /* Same sleep-isolation problem as the CE pin: a floating gate on the
     * dummy-load MOSFET leaves conduction undefined for the whole sleep, which
     * is precisely the interval the keep-alive exists to keep cheap. */
    ESP_ERROR_CHECK(gpio_sleep_sel_dis(KEEPALIVE_GPIO));
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

/*
 * Map pot position onto a perceptually even ramp.
 *
 * Perceived brightness tracks roughly duty^(1/2.2), so a linear mapping
 * crowds all the visible change into the bottom third of the travel. A square
 * law is visually indistinguishable from gamma 2.2 at this resolution and
 * stays in integer math - the C3 is RISC-V with no FPU, so pow() would drag
 * in soft-float.
 *
 * MIN_ON_DUTY is folded in, so any duty returned here is actually visible.
 */
static uint32_t adc_to_duty(int adc_value)
{
    if (adc_value < 0)              adc_value = 0;
    if (adc_value > ADC_RAW_AT_MAX) adc_value = ADC_RAW_AT_MAX;

    const uint32_t span = LEDC_MAX_DUTY - MIN_ON_DUTY;
    uint64_t sq = (uint64_t)adc_value * (uint64_t)adc_value;
    return MIN_ON_DUTY +
           (uint32_t)(sq * span / ((uint64_t)ADC_RAW_AT_MAX * ADC_RAW_AT_MAX));
}

static void set_led_brightness(uint32_t target_duty, uint32_t fade_ms)
{
    ESP_ERROR_CHECK(ledc_set_fade_with_time(
        LEDC_SPEED_MODE, LEDC_CHANNEL, target_duty, fade_ms));
    ESP_ERROR_CHECK(ledc_fade_start(
        LEDC_SPEED_MODE, LEDC_CHANNEL, LEDC_FADE_NO_WAIT));
}

/*
 * M-out-of-N motion filter. Returns true once at least MOTION_THRESHOLD_M of
 * the last MOTION_WINDOW_N readings were HIGH.
 */
static bool motion_filter(int raw_reading)
{
    static int buffer[MOTION_WINDOW_N];
    static int index = 0;

    buffer[index] = raw_reading;
    index = (index + 1) % MOTION_WINDOW_N;

    int count = 0;
    for (int i = 0; i < MOTION_WINDOW_N; i++) {
        count += (buffer[i] != 0);
    }
    return count >= MOTION_THRESHOLD_M;
}

/* Preload the window so a wake-from-sleep lights the lamp immediately
 * instead of waiting MOTION_THRESHOLD_M poll intervals. */
static void motion_filter_prime(int value)
{
    for (int i = 0; i < MOTION_WINDOW_N; i++) {
        (void)motion_filter(value);
    }
}

static void keepalive_pulse(void)
{
    gpio_set_level(KEEPALIVE_GPIO, 1);
    vTaskDelay(pdMS_TO_TICKS(KEEPALIVE_PULSE_MS));
    gpio_set_level(KEEPALIVE_GPIO, 0);
}

/*
 * Sleep until the radar asserts, surfacing every KEEPALIVE_PERIOD_US to poke
 * the powerbank so it does not cut the rail.
 *
 * The LEDC channel is stopped and its timer paused first. Duty is already
 * zero at this point, so nothing visible happens; this just prevents the
 * timer from being left half-clocked across the sleep boundary.
 *
 * Note for bench work: with a USB cable attached, the USB Serial/JTAG console
 * holds the system awake and idle current will read far higher than the ~5.7
 * mA design figure. Measure on the powerbank alone.
 */
static void idle_sleep_until_presence(void)
{
    /* Already occupied - nothing to sleep through. Return without touching the
     * PWM path so we do not stop, pause and immediately resume the timer. This
     * is the boot case: the radar asserts within a few ms of power-up. */
    if (gpio_get_level(RADAR_GPIO)) {
        motion_filter_prime(1);
        return;
    }

    ESP_ERROR_CHECK(ledc_stop(LEDC_SPEED_MODE, LEDC_CHANNEL, 0));
    ESP_ERROR_CHECK(ledc_timer_pause(LEDC_SPEED_MODE, LEDC_TIMER));
    gpio_set_level(DRIVER_CE_GPIO, 0);

    /*
     * Both wakeup sources are armed unconditionally, outside the loop, and torn
     * down unconditionally after it. Do not move the timer enable back inside:
     * the radar can already be HIGH on entry, the loop then runs zero times, and
     * esp_sleep_disable_wakeup_source() returns ESP_ERR_INVALID_STATE for a
     * source that was never enabled - which ESP_ERROR_CHECK turns into a reboot
     * loop. The sleep duration persists across wakeups, so arming it once here
     * covers every iteration.
     */
    ESP_ERROR_CHECK(gpio_wakeup_enable(RADAR_GPIO, GPIO_INTR_HIGH_LEVEL));
    ESP_ERROR_CHECK(esp_sleep_enable_gpio_wakeup());
    ESP_ERROR_CHECK(esp_sleep_enable_timer_wakeup(KEEPALIVE_PERIOD_US));

    while (gpio_get_level(RADAR_GPIO) == 0) {
        keepalive_pulse();
        esp_light_sleep_start();
    }

    ESP_ERROR_CHECK(gpio_wakeup_disable(RADAR_GPIO));
    ESP_ERROR_CHECK(esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_TIMER));
    ESP_ERROR_CHECK(esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_GPIO));

    /* Bring the PWM path back up, still at zero, ready to fade. */
    ESP_ERROR_CHECK(ledc_timer_resume(LEDC_SPEED_MODE, LEDC_TIMER));
    ESP_ERROR_CHECK(ledc_set_duty(LEDC_SPEED_MODE, LEDC_CHANNEL, 0));
    ESP_ERROR_CHECK(ledc_update_duty(LEDC_SPEED_MODE, LEDC_CHANNEL));

    motion_filter_prime(1);
}

/* ------------------------------------------------------------------ */
/*  Main application                                                   */
/* ------------------------------------------------------------------ */

void app_main(void)
{
    ESP_LOGI(TAG, "Fused Glass Lighting (Rev F) - initializing");

    init_power_management();
    init_ledc();
    init_radar();
    init_keepalive();
    init_adc();

    ESP_LOGI(TAG, "Ready. PWM %d Hz, off-delay %d s",
             LEDC_FREQUENCY, OCCUPANCY_TIMEOUT_MS / 1000);

    led_state_t state          = STATE_LEDS_OFF;
    int64_t last_motion_ms     = 0;
    uint32_t applied_duty      = 0;
    int applied_adc            = 0;
    bool sensor_fault_latched  = false;
    int64_t continuous_high_ms = -1;

#if DEBUG_LOGGING
    int debug_counter  = 0;
    int last_raw_motion = -1;
#endif

    while (1) {
        int raw_motion = gpio_get_level(RADAR_GPIO);
        int64_t now_ms = esp_timer_get_time() / 1000;

        /* Watchdog against a sensor stuck HIGH (EMI, module failure). */
        if (raw_motion) {
            if (continuous_high_ms < 0) {
                continuous_high_ms = now_ms;
            }
        } else {
            continuous_high_ms = -1;
            if (sensor_fault_latched) {
                sensor_fault_latched = false;
                ESP_LOGI(TAG, "Radar watchdog cleared (clean LOW reading)");
            }
        }

        if (!sensor_fault_latched && continuous_high_ms >= 0 &&
            (now_ms - continuous_high_ms) >= SENSOR_WATCHDOG_MS) {
            sensor_fault_latched = true;
            ESP_LOGW(TAG, "Radar stuck HIGH for over %lld h - distrusting it "
                          "until a clean LOW reading",
                     (long long)(SENSOR_WATCHDOG_MS / 3600000LL));
        }

        bool motion = motion_filter(raw_motion) && !sensor_fault_latched;

#if DEBUG_LOGGING
        if (raw_motion != last_raw_motion) {
            ESP_LOGI(TAG, "DEBUG: raw edge %d -> %d at t=%lldms (state=%s, duty=%lu)",
                     last_raw_motion, raw_motion, (long long)now_ms,
                     state == STATE_LEDS_OFF ? "OFF" : "ON",
                     (unsigned long)applied_duty);
            last_raw_motion = raw_motion;
        }
        if (++debug_counter >= (1000 / POLL_ACTIVE_MS)) {
            /*
             * adc= is the live pot reading and is what bring-up step 8
             * calibrates ADC_RAW_AT_MAX against. It is sampled here rather than
             * reported from applied_adc, which only updates once the reading
             * moves more than ADC_HYSTERESIS and so can sit a good 75 counts
             * stale - enough to spoil the calibration it is needed for.
             *
             * Note it is the pre-clamp value: adc_to_duty() saturates at
             * ADC_RAW_AT_MAX, so duty= cannot show you how far past the current
             * constant the knob actually reaches. That is the whole measurement.
             */
            int adc_now = read_potentiometer_averaged();
            ESP_LOGI(TAG, "DEBUG: state=%s radar=%d filtered=%d adc=%d duty=%lu",
                     state == STATE_LEDS_OFF ? "OFF" : "ON",
                     raw_motion, motion, adc_now, (unsigned long)applied_duty);
            debug_counter = 0;
        }
#endif

        switch (state) {
        case STATE_LEDS_OFF:
            if (motion) {
                applied_adc  = read_potentiometer_averaged();
                applied_duty = adc_to_duty(applied_adc);
                ESP_LOGI(TAG, "Presence detected. ON (duty=%lu)",
                         (unsigned long)applied_duty);
                set_led_brightness(applied_duty, FADE_ON_OFF_MS);
                last_motion_ms = now_ms;
                state = STATE_LEDS_ON;
            } else if (!sensor_fault_latched) {
                /*
                 * Nothing to do until someone shows up. Sleeping here is what
                 * makes the powerbank last days rather than hours: idle drops
                 * from roughly 25 mA to well under 1 mA, plus the keep-alive.
                 *
                 * A latched sensor fault keeps us awake and polling so the
                 * watchdog can observe the LOW reading that clears it.
                 */
                idle_sleep_until_presence();
                continuous_high_ms = -1;
            }
            break;

        case STATE_LEDS_ON:
            if (motion) {
                last_motion_ms = now_ms;
            }

            /*
             * Track the pot. Hysteresis is compared in raw ADC counts, not
             * duty: under the square law the duty-per-count slope is tiny at
             * the dim end, so a fixed duty threshold would make the bottom of
             * the travel feel dead.
             */
            {
                int adc_raw = read_potentiometer_averaged();
                int diff    = adc_raw - applied_adc;
                if (diff > ADC_HYSTERESIS || diff < -ADC_HYSTERESIS) {
                    uint32_t desired = adc_to_duty(adc_raw);
                    ESP_LOGI(TAG, "Brightness %lu -> %lu",
                             (unsigned long)applied_duty,
                             (unsigned long)desired);
                    applied_adc  = adc_raw;
                    applied_duty = desired;
                    set_led_brightness(applied_duty, FADE_ADJUST_MS);
                }
            }

            if ((now_ms - last_motion_ms) >= OCCUPANCY_TIMEOUT_MS) {
                ESP_LOGI(TAG, "No presence for %d s. OFF.",
                         OCCUPANCY_TIMEOUT_MS / 1000);
                set_led_brightness(0, FADE_ON_OFF_MS);
                /* Let the fade finish before the sleep path stops LEDC. */
                vTaskDelay(pdMS_TO_TICKS(FADE_ON_OFF_MS + 50));
                applied_duty = 0;
                state = STATE_LEDS_OFF;
            }
            break;
        }

        /*
         * STATE_LEDS_ON always polls at this rate. STATE_LEDS_OFF normally
         * blocks in idle_sleep_until_presence() and arrives here with presence
         * already asserted, where one extra tick before lighting is invisible.
         * The delay is not optional though: with a sensor fault latched, OFF
         * skips the sleep entirely, and without a yield here the main loop
         * spins flat out, starving the IDLE task and collapsing the M-out-of-N
         * window to microseconds - exactly when the filter is meant to be
         * diagnosing a bad sensor.
         */
        vTaskDelay(pdMS_TO_TICKS(POLL_ACTIVE_MS));
    }
}
