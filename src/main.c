/*
 * Fused Glass Lighting
 * ---------------------------------------------------------------------------
 * Seeed XIAO ESP32-C3 (ESP-IDF). Presence-controlled filament lighting, gated by
 * an HLK-LD2410S 24 GHz radar and dimmed by a potentiometer, powered from a USB
 * power bank that needs a periodic dummy load while the lamp is dark.
 *
 * One source, two boards (select with a build flag, see platformio.ini):
 *
 *   FGL_BOARD_REV_F (default)  The hand-wired prototype: two LD1500SB (CN5711)
 *       linear modules, 1 kHz PWM on their commoned CE pads. Behaviour unchanged
 *       from the Rev F firmware apart from the task watchdog (below).
 *
 *   FGL_BOARD_G2  The G2 controller board (docs/g2_decisions.md): one TPS61500
 *       SEPIC driving a series filament string.
 *         - D7/GPIO20 drives EN with 19.53 kHz PWM; DIMC turns it into an analog
 *           FB reference, so I_LED = duty x I_ceiling and there is no flicker.
 *         - D6/GPIO21 reads the JP1 shunt: low = 244 mA ceiling (shunt on 2-3),
 *           high = 488 mA (shunt on 1-2, or no shunt: then the hardware is at
 *           244 mA and the firmware under-drives, which is the safe direction).
 *         - D2/GPIO4 reads VSENSE = VOUT / 13 and guards the string:
 *             * every start runs at a low probe current first and checks VOUT:
 *               open string or reversed filament (VOUT near OVP), short (VOUT ~0),
 *               and a per-piece window (fixed at build time, or learned once and
 *               kept in NVS); any fault turns the driver off and retries later;
 *             * while lit: the same open/short checks, and the 5 W LED power cap.
 *         - The pot is read in calibrated millivolts, full scale 1.85 V, so every
 *           unit reaches 100 % despite pot and 3V3 tolerance (G1 audit M1).
 *         - The radar UART pins idle with pull-ups (G1 audit L2).
 *         - D8/GPIO8 reads the JP2 shunt at power-on (R29 pull-up; D18, D19):
 *           low (shunt on 1-2) = manual mode: the radar is ignored and the
 *           string stays lit at the pot setting for as long as the switch is
 *           on, with the same start check and guards. High (shunt on 2-3, or
 *           no shunt) = radar mode, as before.
 *
 *   Both: the main task is on the task watchdog, which reboots the chip if the
 *   loop hangs, so the keep-alive load or the driver can't be left stuck on
 *   (G1 audit L4, design review F7).
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
#include "esp_task_wdt.h"
#include "esp_log.h"

#if !defined(FGL_BOARD_G2) && !defined(FGL_BOARD_REV_F)
#define FGL_BOARD_REV_F
#endif
#if defined(FGL_BOARD_G2) && defined(FGL_BOARD_REV_F)
#error "Define only one of FGL_BOARD_G2 and FGL_BOARD_REV_F"
#endif

#ifdef FGL_BOARD_G2
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "nvs_flash.h"
#include "nvs.h"
#define BOARD_NAME "G2"
#else
#define BOARD_NAME "Rev F"
#endif

static const char *TAG = "fused_glass";

/* ------------------------------------------------------------------ */
/*  Pin assignments (XIAO ESP32-C3)                                    */
/* ------------------------------------------------------------------ */
/*
 * Constraints that produced these maps:
 *   - Only D0-D3 can wake the chip from deep sleep (light sleep: any GPIO).
 *   - Only A0/A1/A2 (GPIO2/3/4) are on ADC1. A3/GPIO5 is ADC2 and Seeed
 *     documents it as unreliable.
 *   - D0 (GPIO2), D8 (GPIO8), D9 (GPIO9) are strapping pins. G2 uses D8 for
 *     JP2: GPIO8 only matters for download boot (GPIO9 low), where GPIO8 low
 *     is invalid, so move JP2 off 1-2 before forcing download with BOOT.
 *   - D6 (GPIO21) is U0TXD and D7 (GPIO20) is U0RXD. The ROM boot log comes
 *     out of GPIO21; GPIO20 has a ~45 k pull-up at reset (G2: R18 2.2 k holds
 *     EN low against it).
 */
#define POT_ADC_CHANNEL     ADC_CHANNEL_3       /* D1  / GPIO3  ADC1_CH3      */
#define RADAR_GPIO          GPIO_NUM_5          /* D3  / GPIO5  LD2410S OT2   */
#define KEEPALIVE_GPIO      GPIO_NUM_10         /* D10 / GPIO10 MOSFET gate   */
#define RADAR_TX_GPIO       GPIO_NUM_6          /* D4  / GPIO6  -> radar RX   */
#define RADAR_RX_GPIO       GPIO_NUM_7          /* D5  / GPIO7  <- radar TX   */

#ifdef FGL_BOARD_G2
#define DRIVER_PWM_GPIO     GPIO_NUM_20         /* D7  / GPIO20 -> TPS61500 EN (via R17) */
#define ISEL_GPIO           GPIO_NUM_21         /* D6  / GPIO21 <- JP1 (via R22, R23 pull-up) */
#define VSENSE_ADC_CHANNEL  ADC_CHANNEL_4       /* D2  / GPIO4  ADC1_CH4, VOUT / 13 */
#define MODE_GPIO           GPIO_NUM_8          /* D8  / GPIO8  <- JP2 (R29 10 k pull-up) */
#else
#define DRIVER_PWM_GPIO     GPIO_NUM_4          /* D2  / GPIO4  -> both CE    */
#endif

/* ------------------------------------------------------------------ */
/*  LEDC (PWM) configuration                                           */
/* ------------------------------------------------------------------ */
#define LEDC_SPEED_MODE     LEDC_LOW_SPEED_MODE /* C3 has low-speed only      */
#define LEDC_TIMER          LEDC_TIMER_0
#define LEDC_CHANNEL        LEDC_CHANNEL_0

#ifdef FGL_BOARD_G2
/*
 * 40 MHz XTAL / 2^11 = 19.53 kHz, inside the TPS61500's 200 Hz - 40 kHz analog
 * dimming range, and far above anything a camera or an eye can see. The chip
 * chops its 200 mV reference at this duty and filters it on DIMC (C7, 1 uF with
 * an internal 25 k), so the LED current is DC: I = duty x I_ceiling.
 */
#define LEDC_DUTY_RES       LEDC_TIMER_11_BIT
#define LEDC_FREQUENCY      19531
#define LEDC_MAX_DUTY       ((1 << 11) - 1)
#else
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
#endif

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

/*
 * Task watchdog. The longest the main task legitimately blocks is one light
 * sleep (10 s) plus a keep-alive pulse, so 15 s never fires in normal running.
 * On expiry the chip panics and reboots: every output pin returns to its reset
 * state and the board's pull-downs turn the driver and the keep-alive off.
 */
#define TASK_WDT_TIMEOUT_MS     15000

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

#ifdef FGL_BOARD_G2
/*
 * Pot: 3V3 -> R5 47 k -> 100 k pot -> GND, so the wiper tops out near 2.24 V.
 * Full scale is set at 1.85 V, below the lowest wiper maximum with a -30 % pot,
 * 3V3 at -2 % and the ADC's own error (G1 audit M1). Anything above reads 100 %.
 */
#define POT_FULL_SCALE_MV       1850
#define POT_HYSTERESIS_MV       40              /* ~2 %, kills wiper jitter   */
#else
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
#endif

#define DEBUG_LOGGING           1

#ifdef FGL_BOARD_G2
/* ------------------------------------------------------------------ */
/*  G2 string current and guards                                       */
/* ------------------------------------------------------------------ */
#define CEILING_LOW_MA          244     /* 0.2 V / 0.82 R  (JP1 shunt on 2-3)        */
#define CEILING_HIGH_MA         488     /* R20 || R21      (JP1 shunt on 1-2)        */

#ifndef FGL_MAX_CURRENT_MA
#define FGL_MAX_CURRENT_MA      150     /* per-piece maximum at full knob            */
#endif
#define MIN_CURRENT_PERMILLE    50      /* bottom of the knob: 5 % of the maximum    */

/*
 * Start-up probe. The driver comes up at 10 % of the piece's maximum (at least
 * 10 mA), and VOUT is read once the 30 ms soft start and the 25 ms DIMC filter
 * have settled. Only a string that passes is ramped to the knob setting.
 */
#define PROBE_PERMILLE          100
#define PROBE_MIN_MA            10
#define PROBE_SETTLE_MS         200

/*
 * VOUT limits. OVP is 27.7 V typical (26.4 V minimum; R15 110 k / R16 5.1 k), and
 * the longest supported string is 24 V, so anything at or above 25.5 V means the
 * string is open: a missing END wire, a loose push-in, or a filament fitted
 * backwards whose reverse breakdown is above OVP. Below 1.5 V the output is
 * shorted (one 3 V filament reads ~2.5 V even at the probe current).
 */
#define VOUT_OPEN_MV            25500
#define VOUT_SHORT_MV           1500
#define VSENSE_DIVIDER          13      /* (R24 120 k + R25 10 k) / R25 10 k         */

/*
 * Per-piece window for VOUT at the probe current. A filament fitted backwards
 * whose reverse breakdown is below OVP doesn't look open; it shows up as a
 * string voltage that doesn't match the piece. Either fix the window at build
 * time with FGL_STRING_VMIN_MV / FGL_STRING_VMAX_MV, or let the first good start
 * learn it (stored in NVS). To relearn after rewiring on purpose: within 10 s of
 * switching on, turn the knob fully clockwise and back to the minimum.
 */
#define WINDOW_PERMILLE         150     /* +/- 15 % of the learned value             */
#define WINDOW_MIN_MV           600     /* ... but never tighter than +/- 0.6 V      */
#define RELEARN_WINDOW_MS       10000

#define LED_POWER_CAP_MW        5000    /* D5: SLVA904's 6 W example peaks at 2.9 A  */
#define FAULT_RETRY_MS          30000   /* driver stays off this long after a fault  */
#define SHORT_CHECK_DELAY_MS    300     /* ignore VOUT ~0 right after a (re)start    */
#endif

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

#ifdef FGL_BOARD_G2
typedef enum {
    FAULT_NONE = 0,
    FAULT_OPEN,         /* VOUT near OVP: open string or reversed filament  */
    FAULT_SHORT,        /* VOUT ~0 while driven                             */
    FAULT_WINDOW,       /* VOUT at the probe current doesn't match the piece */
} drv_fault_t;

static const char *fault_name(drv_fault_t f)
{
    switch (f) {
    case FAULT_OPEN:   return "open string or reversed filament (VOUT near OVP)";
    case FAULT_SHORT:  return "shorted output (VOUT ~0)";
    case FAULT_WINDOW: return "string voltage doesn't match this piece";
    default:           return "none";
    }
}

static adc_cali_handle_t cali_pot    = NULL;
static adc_cali_handle_t cali_vsense = NULL;
static uint32_t ceiling_ma  = CEILING_HIGH_MA;   /* re-read from JP1 at every start */
#if !(defined(FGL_STRING_VMIN_MV) && defined(FGL_STRING_VMAX_MV))
static uint32_t win_ref_mv  = 0;                 /* 0 = not learned yet             */
#endif
static uint32_t last_vout_mv = 0;
static bool manual_mode     = false;             /* JP2 on 1-2, read at power-on    */
#define MANUAL_MODE()       (manual_mode)
#else
#define MANUAL_MODE()       (false)
#endif

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

static void init_task_watchdog(void)
{
    esp_task_wdt_config_t cfg = {
        .timeout_ms     = TASK_WDT_TIMEOUT_MS,
        .idle_core_mask = 0,        /* watch this task only, not the idle task */
        .trigger_panic  = true,     /* panic -> reboot -> outputs back to reset state */
    };
    /* CONFIG_ESP_TASK_WDT_INIT=y starts the TWDT at boot (5 s, no panic). */
    esp_err_t err = esp_task_wdt_reconfigure(&cfg);
    if (err == ESP_ERR_INVALID_STATE) {
        err = esp_task_wdt_init(&cfg);
    }
    ESP_ERROR_CHECK(err);
    ESP_ERROR_CHECK(esp_task_wdt_add(NULL));
    ESP_LOGI(TAG, "Task watchdog: %d ms, panic + reboot", TASK_WDT_TIMEOUT_MS);
}

static void init_ledc(void)
{
    /* Park the driver input low before the peripheral takes the pin, or the
     * filaments flash on at every reset. */
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << DRIVER_PWM_GPIO),
        .mode         = GPIO_MODE_OUTPUT,
        .pull_up_en   = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&io_conf));
    gpio_set_level(DRIVER_PWM_GPIO, 0);

    ledc_timer_config_t timer_conf = {
        .speed_mode      = LEDC_SPEED_MODE,
        .timer_num       = LEDC_TIMER,
        .duty_resolution = LEDC_DUTY_RES,
        .freq_hz         = LEDC_FREQUENCY,
        /* XTAL rather than APB: dynamic frequency scaling must not be able
         * to move the PWM frequency (Rev F: past the CN5711's 2 kHz ceiling). */
        .clk_cfg         = LEDC_USE_XTAL_CLK,
    };
    ESP_ERROR_CHECK(ledc_timer_config(&timer_conf));

    ledc_channel_config_t channel_conf = {
        .gpio_num            = DRIVER_PWM_GPIO,
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
     * That includes this pin. On Rev F a floating CE lets the CN5711's internal
     * pull-up enable both drivers, so the filaments came on at full 300 mA for
     * the whole sleep. (G2 has R18 to hold EN low, but the pin should still be
     * driven, not floated.)
     *
     * gpio_sleep_sel_dis() opts the pad out of that automatic switching, so it
     * holds the level ledc_stop() parked it at. Must be called after
     * ledc_channel_config(), which reconfigures the pad.
     */
    ESP_ERROR_CHECK(gpio_sleep_sel_dis(DRIVER_PWM_GPIO));
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

#ifdef FGL_BOARD_G2
    /*
     * The radar UART isn't driven yet (radar configuration over UART is a later
     * firmware item), but its pins go off-board through R26/R27. With pull-ups
     * they idle at the UART mark level instead of floating when no radar is
     * fitted (G1 audit L2). When the UART driver is added, call
     * gpio_pullup_en(RADAR_RX_GPIO) after uart_set_pin() to keep RX defined.
     */
    gpio_config_t uart_conf = {
        .pin_bit_mask = (1ULL << RADAR_TX_GPIO) | (1ULL << RADAR_RX_GPIO),
        .mode         = GPIO_MODE_INPUT,
        .pull_up_en   = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&uart_conf));
#endif
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

    /* Same sleep-isolation problem as the driver pin: a floating gate on the
     * dummy-load MOSFET leaves conduction undefined for the whole sleep, which
     * is precisely the interval the keep-alive exists to keep cheap. */
    ESP_ERROR_CHECK(gpio_sleep_sel_dis(KEEPALIVE_GPIO));
}

#ifdef FGL_BOARD_G2
static adc_cali_handle_t make_cali(adc_channel_t chan)
{
    adc_cali_handle_t h = NULL;
    adc_cali_curve_fitting_config_t cfg = {
        .unit_id  = ADC_UNIT_1,
        .chan     = chan,
        .atten    = ADC_ATTEN_DB_12,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    if (adc_cali_create_scheme_curve_fitting(&cfg, &h) != ESP_OK) {
        ESP_LOGW(TAG, "ADC calibration unavailable on channel %d; using nominal scaling", (int)chan);
        h = NULL;
    }
    return h;
}
#endif

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
#ifdef FGL_BOARD_G2
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc1_handle, VSENSE_ADC_CHANNEL, &chan_cfg));
    cali_pot    = make_cali(POT_ADC_CHANNEL);
    cali_vsense = make_cali(VSENSE_ADC_CHANNEL);
#endif
}

#ifdef FGL_BOARD_G2
static void init_isel(void)
{
    /* GPIO21 is UART0 TX during the ROM boot; from here on it's an input. */
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << ISEL_GPIO),
        .mode         = GPIO_MODE_INPUT,
        .pull_up_en   = GPIO_PULLUP_ENABLE,     /* R23 100 k is the real pull-up */
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&io_conf));
}

/*
 * JP2: radar or manual mode. R29 (10 k, D19) pulls GPIO8 up, and the internal
 * pull-up is enabled as well, so it reads high with no shunt or the shunt on
 * 2-3 (radar); the shunt on 1-2 ties it to GND (manual). Read once at
 * power-on: move the shunt with the switch off.
 */
static bool read_manual_mode(void)
{
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << MODE_GPIO),
        .mode         = GPIO_MODE_INPUT,
        .pull_up_en   = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type    = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&io_conf));
    vTaskDelay(pdMS_TO_TICKS(2));               /* let the pin settle on the weak pull-up */
    int low = 0;
    for (int i = 0; i < 5; i++) {               /* majority of 5, in case of a loose shunt */
        low += gpio_get_level(MODE_GPIO) == 0;
        vTaskDelay(pdMS_TO_TICKS(1));
    }
    return low >= 3;
}

static uint32_t read_ceiling_ma(void)
{
    /* Low only with the shunt on 2-3. High means 1-2 (488 mA) or no shunt
     * (hardware at 244 mA, so assuming 488 under-drives: safe). */
    return gpio_get_level(ISEL_GPIO) ? CEILING_HIGH_MA : CEILING_LOW_MA;
}

#if defined(FGL_STRING_VMIN_MV) && defined(FGL_STRING_VMAX_MV)
#define WINDOW_FIXED 1
#else
#define WINDOW_FIXED 0
#endif

static void init_window(void)
{
#if WINDOW_FIXED
    ESP_LOGI(TAG, "String window fixed at build time: %d-%d mV at the probe current",
             FGL_STRING_VMIN_MV, FGL_STRING_VMAX_MV);
#else
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);
    nvs_handle_t h;
    if (nvs_open("fgl", NVS_READONLY, &h) == ESP_OK) {
        uint32_t v = 0;
        if (nvs_get_u32(h, "vprobe_mv", &v) == ESP_OK) {
            win_ref_mv = v;
        }
        nvs_close(h);
    }
    if (win_ref_mv) {
        ESP_LOGI(TAG, "Learned string voltage at the probe current: %lu mV", (unsigned long)win_ref_mv);
    } else {
        ESP_LOGI(TAG, "No learned string voltage yet; the first good start will learn it");
    }
#endif
}

#if !WINDOW_FIXED
static void window_store(uint32_t mv)
{
    nvs_handle_t h;
    if (nvs_open("fgl", NVS_READWRITE, &h) == ESP_OK) {
        if (mv) {
            nvs_set_u32(h, "vprobe_mv", mv);
        } else {
            nvs_erase_key(h, "vprobe_mv");
        }
        nvs_commit(h);
        nvs_close(h);
    }
    win_ref_mv = mv;
}
#endif
#endif /* FGL_BOARD_G2 */

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

static int read_adc_raw_averaged(adc_channel_t chan)
{
    int sum = 0;
    int raw = 0;
    for (int i = 0; i < ADC_SAMPLES; i++) {
        ESP_ERROR_CHECK(adc_oneshot_read(adc1_handle, chan, &raw));
        sum += raw;
    }
    return sum / ADC_SAMPLES;
}

#ifdef FGL_BOARD_G2
static int adc_mv(adc_cali_handle_t cali, int raw)
{
    int mv = 0;
    if (cali && adc_cali_raw_to_voltage(cali, raw, &mv) == ESP_OK) {
        return mv;
    }
    return raw * 2500 / 4095;   /* nominal 12 dB scaling, uncalibrated */
}

/* The pot reading the brightness logic works in: calibrated millivolts. */
static int read_potentiometer(void)
{
    return adc_mv(cali_pot, read_adc_raw_averaged(POT_ADC_CHANNEL));
}

static uint32_t read_vout_mv(void)
{
    int mv = adc_mv(cali_vsense, read_adc_raw_averaged(VSENSE_ADC_CHANNEL));
    return mv > 0 ? (uint32_t)mv * VSENSE_DIVIDER : 0;
}

static uint32_t piece_max_ma(void)
{
    return FGL_MAX_CURRENT_MA < ceiling_ma ? FGL_MAX_CURRENT_MA : ceiling_ma;
}

static uint32_t ma_to_duty(uint32_t ma)
{
    if (ma >= ceiling_ma) {
        return LEDC_MAX_DUTY;
    }
    return (ma * LEDC_MAX_DUTY + ceiling_ma / 2) / ceiling_ma;
}

/*
 * Knob -> string current, square law (perceived brightness ~ current^(1/2.2);
 * a square law is indistinguishable at this resolution and stays in integer
 * math). The bottom of the knob is 5 % of the piece maximum, so the lamp is
 * visibly on at the lowest setting. The 5 W LED power cap is applied using the
 * last measured string voltage.
 */
static uint32_t pot_to_ma(int pot_mv)
{
    if (pot_mv < 0)                 pot_mv = 0;
    if (pot_mv > POT_FULL_SCALE_MV) pot_mv = POT_FULL_SCALE_MV;
    const uint32_t imax = piece_max_ma();
    const uint32_t imin = imax * MIN_CURRENT_PERMILLE / 1000;
    uint64_t sq = (uint64_t)pot_mv * (uint64_t)pot_mv;
    uint32_t ma = imin + (uint32_t)(sq * (imax - imin) /
                                    ((uint64_t)POT_FULL_SCALE_MV * POT_FULL_SCALE_MV));
    if (last_vout_mv > 0) {
        uint32_t cap_ma = (uint32_t)((uint64_t)LED_POWER_CAP_MW * 1000 / last_vout_mv);
        if (ma > cap_ma) {
            ma = cap_ma;
        }
    }
    return ma;
}

static uint32_t pot_to_duty(int pot_mv)
{
    return ma_to_duty(pot_to_ma(pot_mv));
}

#define POT_HYSTERESIS  POT_HYSTERESIS_MV
#else /* Rev F */
static int read_potentiometer(void)
{
    return read_adc_raw_averaged(POT_ADC_CHANNEL);
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
static uint32_t pot_to_duty(int adc_value)
{
    if (adc_value < 0)              adc_value = 0;
    if (adc_value > ADC_RAW_AT_MAX) adc_value = ADC_RAW_AT_MAX;

    const uint32_t span = LEDC_MAX_DUTY - MIN_ON_DUTY;
    uint64_t sq = (uint64_t)adc_value * (uint64_t)adc_value;
    return MIN_ON_DUTY +
           (uint32_t)(sq * span / ((uint64_t)ADC_RAW_AT_MAX * ADC_RAW_AT_MAX));
}

#define POT_HYSTERESIS  ADC_HYSTERESIS
#endif

static void set_led_brightness(uint32_t target_duty, uint32_t fade_ms)
{
    ESP_ERROR_CHECK(ledc_set_fade_with_time(
        LEDC_SPEED_MODE, LEDC_CHANNEL, target_duty, fade_ms));
    ESP_ERROR_CHECK(ledc_fade_start(
        LEDC_SPEED_MODE, LEDC_CHANNEL, LEDC_FADE_NO_WAIT));
}

#ifdef FGL_BOARD_G2
/* Immediate, no fade: used for the probe and for turning the driver off on a
 * fault. EN low for > 10 ms shuts the TPS61500 down. */
static void driver_set_duty_now(uint32_t duty)
{
    ledc_fade_stop(LEDC_SPEED_MODE, LEDC_CHANNEL);
    ESP_ERROR_CHECK(ledc_set_duty(LEDC_SPEED_MODE, LEDC_CHANNEL, duty));
    ESP_ERROR_CHECK(ledc_update_duty(LEDC_SPEED_MODE, LEDC_CHANNEL));
}

/*
 * Bring the string up at the probe current and check it before anything
 * brighter is allowed. On success the driver is left at the probe current and
 * the caller fades to the knob setting. On a fault the driver is off.
 */
static drv_fault_t driver_start_checked(void)
{
    ceiling_ma = read_ceiling_ma();
    uint32_t probe_ma = piece_max_ma() * PROBE_PERMILLE / 1000;
    if (probe_ma < PROBE_MIN_MA) {
        probe_ma = PROBE_MIN_MA;
    }
    driver_set_duty_now(ma_to_duty(probe_ma));
    vTaskDelay(pdMS_TO_TICKS(PROBE_SETTLE_MS));
    esp_task_wdt_reset();

    uint32_t v = read_vout_mv();
    ESP_LOGI(TAG, "Start: ceiling %lu mA (JP1), max %lu mA, probe %lu mA -> VOUT %lu mV",
             (unsigned long)ceiling_ma, (unsigned long)piece_max_ma(),
             (unsigned long)probe_ma, (unsigned long)v);

    drv_fault_t f = FAULT_NONE;
    if (v >= VOUT_OPEN_MV) {
        f = FAULT_OPEN;
    } else if (v <= VOUT_SHORT_MV) {
        f = FAULT_SHORT;
    } else {
#if WINDOW_FIXED
        if (v < FGL_STRING_VMIN_MV || v > FGL_STRING_VMAX_MV) {
            f = FAULT_WINDOW;
        }
#else
        if (win_ref_mv == 0) {
            window_store(v);
            ESP_LOGI(TAG, "Learned this piece's string voltage: %lu mV at the probe current",
                     (unsigned long)v);
        } else {
            uint32_t tol = win_ref_mv * WINDOW_PERMILLE / 1000;
            if (tol < WINDOW_MIN_MV) {
                tol = WINDOW_MIN_MV;
            }
            if (v + tol < win_ref_mv || v > win_ref_mv + tol) {
                f = FAULT_WINDOW;
                ESP_LOGW(TAG, "Expected %lu +/- %lu mV. If the filaments were rewired on purpose, "
                              "relearn: within 10 s of switching on, turn the knob fully up and back down.",
                         (unsigned long)win_ref_mv, (unsigned long)tol);
            }
        }
#endif
    }
    if (f != FAULT_NONE) {
        driver_set_duty_now(0);
        last_vout_mv = 0;
    } else {
        last_vout_mv = v;
    }
    return f;
}

/* While lit: the string must not open (VOUT climbs to OVP) or short (VOUT ~0).
 * Also refreshes the voltage the 5 W cap uses. */
static drv_fault_t driver_check_running(int64_t ms_since_start)
{
    uint32_t v = read_vout_mv();
    if (v >= VOUT_OPEN_MV) {
        return FAULT_OPEN;
    }
    if (v <= VOUT_SHORT_MV && ms_since_start >= SHORT_CHECK_DELAY_MS) {
        return FAULT_SHORT;
    }
    last_vout_mv = v;
    return FAULT_NONE;
}
#endif /* FGL_BOARD_G2 */

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
    esp_task_wdt_reset();
}

/* Stop the PWM path with the driver input low, ready for light sleep. */
static void driver_park(void)
{
    ESP_ERROR_CHECK(ledc_stop(LEDC_SPEED_MODE, LEDC_CHANNEL, 0));
    ESP_ERROR_CHECK(ledc_timer_pause(LEDC_SPEED_MODE, LEDC_TIMER));
    gpio_set_level(DRIVER_PWM_GPIO, 0);
}

/* Bring the PWM path back up, still at zero, ready to fade. */
static void driver_unpark(void)
{
    ESP_ERROR_CHECK(ledc_timer_resume(LEDC_SPEED_MODE, LEDC_TIMER));
    ESP_ERROR_CHECK(ledc_set_duty(LEDC_SPEED_MODE, LEDC_CHANNEL, 0));
    ESP_ERROR_CHECK(ledc_update_duty(LEDC_SPEED_MODE, LEDC_CHANNEL));
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

    driver_park();

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
        esp_task_wdt_reset();
        esp_light_sleep_start();
        esp_task_wdt_reset();
    }

    ESP_ERROR_CHECK(gpio_wakeup_disable(RADAR_GPIO));
    ESP_ERROR_CHECK(esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_TIMER));
    ESP_ERROR_CHECK(esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_GPIO));

    driver_unpark();
    motion_filter_prime(1);
}

#ifdef FGL_BOARD_G2
/*
 * After a driver fault the string stays dark for FAULT_RETRY_MS even if someone
 * is present. Sleep through it on the timer (no radar wake), still pulsing the
 * keep-alive, instead of polling awake at ~15 mA (design review F3).
 */
static void sleep_until(int64_t until_ms)
{
    driver_park();
    for (;;) {
        int64_t left_ms = until_ms - esp_timer_get_time() / 1000;
        if (left_ms <= 0) {
            break;
        }
        uint64_t us = (uint64_t)left_ms * 1000ULL;
        if (us > KEEPALIVE_PERIOD_US) {
            us = KEEPALIVE_PERIOD_US;
        }
        keepalive_pulse();
        ESP_ERROR_CHECK(esp_sleep_enable_timer_wakeup(us));
        esp_task_wdt_reset();
        esp_light_sleep_start();
        esp_task_wdt_reset();
    }
    ESP_ERROR_CHECK(esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_TIMER));
    driver_unpark();
}
#endif

/* ------------------------------------------------------------------ */
/*  Main application                                                   */
/* ------------------------------------------------------------------ */

void app_main(void)
{
    ESP_LOGI(TAG, "Fused Glass Lighting (%s) - initializing", BOARD_NAME);

    init_power_management();
    init_ledc();
#ifdef FGL_BOARD_G2
    init_isel();
#endif
    init_radar();
    init_keepalive();
    init_adc();
#ifdef FGL_BOARD_G2
    init_window();
    manual_mode = read_manual_mode();
    ESP_LOGI(TAG, "JP2: %s", manual_mode
             ? "shunt on 1-2 -> MANUAL mode: radar ignored, lit while the switch is on"
             : "shunt on 2-3 (or none) -> RADAR mode");
    ceiling_ma = read_ceiling_ma();
    ESP_LOGI(TAG, "JP1: %s -> %lu mA ceiling; piece maximum %lu mA",
             ceiling_ma == CEILING_LOW_MA ? "shunt on 2-3" : "shunt on 1-2 (or none)",
             (unsigned long)ceiling_ma, (unsigned long)piece_max_ma());
#endif
    init_task_watchdog();

    if (MANUAL_MODE()) {
        ESP_LOGI(TAG, "Ready. PWM %d Hz, manual mode (no off-delay)", LEDC_FREQUENCY);
    } else {
        ESP_LOGI(TAG, "Ready. PWM %d Hz, off-delay %d s",
                 LEDC_FREQUENCY, OCCUPANCY_TIMEOUT_MS / 1000);
    }

    led_state_t state          = STATE_LEDS_OFF;
    int64_t last_motion_ms     = 0;
    uint32_t applied_duty      = 0;
    int applied_pot            = 0;
    bool sensor_fault_latched  = false;
    int64_t continuous_high_ms = -1;
#ifdef FGL_BOARD_G2
    int64_t started_ms         = 0;
    int64_t fault_until_ms     = 0;     /* driver stays off until then */
#if !WINDOW_FIXED
    bool relearn_top_seen      = false;
    bool relearn_done          = false;
#endif
#endif

#if DEBUG_LOGGING
    int debug_counter  = 0;
    int last_raw_motion = -1;
#endif

    while (1) {
        esp_task_wdt_reset();
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

        if (!MANUAL_MODE() && !sensor_fault_latched && continuous_high_ms >= 0 &&
            (now_ms - continuous_high_ms) >= SENSOR_WATCHDOG_MS) {
            sensor_fault_latched = true;
            ESP_LOGW(TAG, "Radar stuck HIGH for over %lld h - distrusting it "
                          "until a clean LOW reading",
                     (long long)(SENSOR_WATCHDOG_MS / 3600000LL));
        }

        bool motion = motion_filter(raw_motion) && !sensor_fault_latched;
        if (MANUAL_MODE()) {
            /* Manual mode: always "present", so the string lights at power-on,
             * never times out, and never sleeps waiting for the radar. Faults
             * still turn it off and retry after FAULT_RETRY_MS. */
            motion = true;
        }

#if defined(FGL_BOARD_G2) && !WINDOW_FIXED
        /* Relearn gesture: within 10 s of power-up, knob fully up, then back down. */
        if (!relearn_done && now_ms < RELEARN_WINDOW_MS) {
            int pot = read_potentiometer();
            if (pot >= POT_FULL_SCALE_MV * 95 / 100) {
                relearn_top_seen = true;
            } else if (relearn_top_seen && pot <= POT_FULL_SCALE_MV / 10) {
                relearn_done = true;
                window_store(0);
                ESP_LOGW(TAG, "Relearn requested: the next start learns this piece's string voltage");
                if (state == STATE_LEDS_ON) {
                    /* Visible confirmation: drop out, then restart (and learn). */
                    driver_set_duty_now(0);
                    vTaskDelay(pdMS_TO_TICKS(400));
                    applied_duty = 0;
                    state = STATE_LEDS_OFF;
                }
            }
        }
#endif

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
             * pot= is the live reading (raw counts on Rev F, calibrated mV on G2),
             * sampled here rather than reported from applied_pot, which only
             * updates once the reading moves more than the hysteresis. On Rev F
             * it is what bring-up step 8 calibrates ADC_RAW_AT_MAX against.
             */
            int pot_now = read_potentiometer();
#ifdef FGL_BOARD_G2
            ESP_LOGI(TAG, "DEBUG: state=%s radar=%d filtered=%d pot=%dmV duty=%lu vout=%lumV",
                     state == STATE_LEDS_OFF ? "OFF" : "ON",
                     raw_motion, motion, pot_now, (unsigned long)applied_duty,
                     (unsigned long)last_vout_mv);
#else
            ESP_LOGI(TAG, "DEBUG: state=%s radar=%d filtered=%d adc=%d duty=%lu",
                     state == STATE_LEDS_OFF ? "OFF" : "ON",
                     raw_motion, motion, pot_now, (unsigned long)applied_duty);
#endif
            debug_counter = 0;
        }
#endif

        switch (state) {
        case STATE_LEDS_OFF:
#ifdef FGL_BOARD_G2
            if (motion && now_ms < fault_until_ms) {
                /* Someone is here but the string faulted recently: stay dark
                 * until the retry time, asleep. */
                sleep_until(fault_until_ms);
                break;
            }
            if (motion) {
                drv_fault_t f = driver_start_checked();
                if (f != FAULT_NONE) {
                    ESP_LOGW(TAG, "Driver fault: %s. Off; retry in %d s.",
                             fault_name(f), FAULT_RETRY_MS / 1000);
                    fault_until_ms = esp_timer_get_time() / 1000 + FAULT_RETRY_MS;
                    applied_duty = 0;
                    break;
                }
                applied_pot  = read_potentiometer();
                applied_duty = pot_to_duty(applied_pot);
                ESP_LOGI(TAG, "%s ON (%lu mA, duty=%lu)",
                         manual_mode ? "Manual mode." : "Presence detected.",
                         (unsigned long)pot_to_ma(applied_pot), (unsigned long)applied_duty);
                set_led_brightness(applied_duty, FADE_ON_OFF_MS);
                last_motion_ms = now_ms;
                started_ms = now_ms;
                state = STATE_LEDS_ON;
            } else if (!sensor_fault_latched && now_ms >= RELEARN_WINDOW_MS) {
                /* Stay awake for the first 10 s so the relearn gesture can be
                 * seen; after that, sleep until someone shows up. */
                idle_sleep_until_presence();
                continuous_high_ms = -1;
            }
#else
            if (motion) {
                applied_pot  = read_potentiometer();
                applied_duty = pot_to_duty(applied_pot);
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
#endif
            break;

        case STATE_LEDS_ON:
            if (motion) {
                last_motion_ms = now_ms;
            }

#ifdef FGL_BOARD_G2
            {
                drv_fault_t f = driver_check_running(now_ms - started_ms);
                if (f != FAULT_NONE) {
                    driver_set_duty_now(0);
                    ESP_LOGW(TAG, "Driver fault while lit: %s. Off; retry in %d s.",
                             fault_name(f), FAULT_RETRY_MS / 1000);
                    fault_until_ms = now_ms + FAULT_RETRY_MS;
                    applied_duty = 0;
                    last_vout_mv = 0;
                    state = STATE_LEDS_OFF;
                    break;
                }
            }
#endif

            /*
             * Track the pot. Hysteresis is compared in pot units (raw counts on
             * Rev F, mV on G2), not duty: under the square law the duty-per-count
             * slope is tiny at the dim end, so a fixed duty threshold would make
             * the bottom of the travel feel dead.
             */
            {
                int pot  = read_potentiometer();
                int diff = pot - applied_pot;
                uint32_t desired = pot_to_duty(pot);
#ifdef FGL_BOARD_G2
                /* The 5 W cap can move the duty without the knob moving. A 1 %
                 * deadband keeps VOUT noise from re-fading every poll. */
                int cap_delta = (int)pot_to_duty(applied_pot) - (int)applied_duty;
                bool capped_change = (cap_delta > LEDC_MAX_DUTY / 100 || cap_delta < -(LEDC_MAX_DUTY / 100));
#else
                bool capped_change = false;
#endif
                if (diff > POT_HYSTERESIS || diff < -POT_HYSTERESIS || capped_change) {
                    if (capped_change && !(diff > POT_HYSTERESIS || diff < -POT_HYSTERESIS)) {
                        pot = applied_pot;
                        desired = pot_to_duty(pot);
                    }
                    if (desired != applied_duty) {
                        ESP_LOGI(TAG, "Brightness %lu -> %lu",
                                 (unsigned long)applied_duty,
                                 (unsigned long)desired);
                        set_led_brightness(desired, FADE_ADJUST_MS);
                    }
                    applied_pot  = pot;
                    applied_duty = desired;
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
