# Design Review: Firmware, Rev F Prototype and Rev G1

Date: 2026-10-15. Reviewer: Claude, as the board's electrical engineer.

This review and the Rev G1 KiCad project were redone from scratch on Oct 15 at Rob's request. The Oct 14 versions are kept, unchanged, in the handoff folder under `superseded/2026-10-14_claude_session/`. Where this review reaches a different conclusion from the Oct 14 one, [section 7](#7-what-changed-from-the-oct-14-version) says so.

## Scope and method

| Item | What was reviewed | How it was checked | Status |
|---|---|---|---|
| Firmware | `src/main.c` at `a631148`, `sdkconfig.defaults`, `platformio.ini` | Read in full | **Not compiled or run here** |
| Rev F prototype | As built: Rob's description (Oct 14) plus the Oct 6 wiring table | Schematic redrawn in KiCad; netlist checked against a hand-written list of connections | Pass. Two items are unconfirmed (P2, ballast position) |
| Rev G1 | New design, drawn from scratch in `hardware/kicad/fgl_g1/` | `verify_netlist.py` compares KiCad's exported netlist with `g1_expected.py`, which was written by hand and doesn't import the generator. It also checks no-connects, power sources, pads against footprints, and BOM fields | Pass. 24 nets, 106 connections |
| KiCad ERC | | Run in KiCad 9.0.7 on Rob's Mac after upgrading the file and updating symbols from the KiCad 9 libraries. Update PCB from Schematic checked that every footprint resolves | Pass. 0 errors, 0 warnings. 46 footprints, 0 warnings. The KiCad 9 netlist also passes the verifier |
| Power and runtime | | `hardware/tools/power_model.py`, which lists every input and its source | Modelled, not measured |
| Datasheet facts | AL8860, LD2410S, XIAO ESP32C3, CN5711 | Read from the documents in [Sources](#sources) | Checked |
| Part numbers | Every LCSC number in the BOM | Checked on lcsc.com or jlcpcb.com on Oct 15 | Checked. Stock changes, so re-check at order time |

To show the verifier finds real faults, it was run on a netlist with radar pins 3 and 4 swapped. It failed with the expected four errors. That swap is the miswire in Perplexity's G1, where the J3 pin order didn't match the LD2410S.

Nothing here has been measured on hardware. Every conclusion that depends on a measurement is listed as a test in [section 6](#6-tests).

## Summary

| # | Severity | Area | Finding | Action |
|---|---|---|---|---|
| P1 | **High** | Rev F | No overcurrent protection. A filament lead shorted to ground below the ballast puts 1.06 A through the 2 W resistor, which is 5.3 W, inside a wooden frame. The bank's own trip (2–3 A) won't see it. | Fuse each channel now. G1 adds F1 and removes the ballasts |
| P3 | **High** | Both | A 20–30 Ah Li-ion bank is charged inside a closed frame next to the drivers | Certified bank, airflow, thermal and pass-through tests (T4) |
| F1 | **High** | Firmware | Keep-alive pulses only run while the lamp is dark. Below about 25% brightness the lamp draws less than many banks' auto-off threshold, so the bank can switch off while lit. | Pulse whenever the estimated load is under ~120 mA |
| P2 | Medium | Rev F | 10 k pull-down on the driver enable net: specified on Oct 6, not mentioned on Oct 14 | Confirm (T6). Without it the filaments flash on at every reset and flash |
| F3 | Medium | Firmware | With the radar fault latched, the dark state polls awake (~15 mA) with no keep-alive, so the bank switches off | Sleep on the timer and keep pulsing |
| F4 | Medium | Firmware | The real off-delay is the radar's own hold (10–120 s, default not published) plus 25 s | Set the LD2410S hold and range over UART at boot |
| F5 | Medium | Firmware | `ADC_RAW_AT_MAX` is measured per unit. That doesn't scale to 10–20 boards | Calibrated millivolts, fixed full scale |
| F2 | Medium | G1 firmware | G1 dimming is different: 19.5 kHz into an RC filter, with a 0.3 V offset in the AL8860's analog curve | Board config plus a new mapping (F2) |
| P4 | Medium | Rev F | Channel currents were set by trimmer and not recorded | Measure and record (T2) |
| X1 | Low | Both | The XIAO's charge LED may run continuously with no battery fitted | Check (T5). If it's lit, remove its resistor |
| F6–F11 | Low | Firmware | Logging on by default, no task watchdog, CPU wake during each pulse, 12 h radar watchdog, stale comments | [Section 2](#2-firmware) |

### Same brightness, Rev F against G1

From `power_model.py`, using these assumptions:

- Bank: 85% of the rated capacity usable at 3.7 V.
- Filament: 2.80 V at 300 mA.
- Keep-alive: fitted.

| | Rev F (built) | Rev G1 |
|---|---|---|
| Lit, full brightness | 3.10 W (621 mA) | 2.06 W (411 mA) |
| Dark (radar armed, light sleep) | ~4.2 mA | ~4.1 mA (1.1 mA without the keep-alive) |
| 20,000 mAh, continuous | 20 h | 31 h |
| 20,000 mAh, 4 h/day | 4.9 days | 7.3 days |
| 30,000 mAh, 4 h/day | 7.4 days | 10.9 days |

## 1. Rev F prototype (as built)

Schematic: `hardware/kicad/fgl_rev_f/fgl_rev_f.pdf`. The LD1500SB is a CN5711 linear current *sink*. The filament's + lead is the module's L+, which is IN+, which is the 5 V rail ([CN5711 datasheet](https://electronperdido.com/wp-content/uploads/2024/04/CN5711-datasheet.pdf), [module listing](https://www.amazon.com/dp/B0F1K97V61)).

### P1 (High): no overcurrent protection

There are three ways a filament fault can go:

| Fault | Current | Who stops it |
|---|---|---|
| Filament + lead to ground, **below** the 4.7 Ω ballast | 5 V / 4.7 Ω = 1.06 A, so 5.3 W in a 2 W resistor | **Nothing.** Total draw is ~1.4 A, under the bank's trip |
| + lead to ground, **above** the ballast | Rail short | The bank's overcurrent trip, 2–3 A typical |
| − lead to ground | The CN5711 still regulates | Nothing needed |

The first case is the dangerous one. The ballast heads for several hundred °C in a wooden frame, and that state is stable.

**Action now:**

- Put a resettable fuse in each channel's L+ lead, about 0.5 A hold and 1.0 A trip. A 1206 or radial PTC soldered inline is enough. Normal current is 0.3 A, and the 1.06 A fault trips it.
- Check that no bare filament tab or solder joint can touch anything metal in the frame: hanging wire, clips, a metal back.

G1 removes the ballast entirely and has an input PTC (D5).

### P2 (Medium): CE pull-down

The Oct 6 build document observed on hardware that the LD1500SB EN pads pull up internally. With EN undriven, both channels run at full current. That happens:

- from power-up until `init_ledc()`
- during USB flashing
- after a panic

Light sleep was the fourth case, and the firmware's `gpio_sleep_sel_dis()` fixes it. Only a resistor fixes the other three. The Oct 6 wiring table has 10 kΩ from the CE net to GND. Your Oct 14 description didn't mention it, so the Rev F schematic shows R3 as "(confirm)".

**Test T6:** in a dark room, unplug and replug the bank. A full-brightness flash before the fade-in means R3 is missing.

### P3 (High, also applies to G1): charging a Li-ion bank inside the frame

The frame's USB-C inlet charges the bank in place, so the frame becomes a charging enclosure for 74–111 Wh of lithium cells. Next to it, Rev F's two ballasts dissipate 0.42 W each and the two CN5711s about 0.24 W each.

- **Use a certified bank** (UL 2056 or IEC 62133). B0DQPD24ZD's certification wasn't checked, and the end user may fit any bank, so put this requirement in the frame's instructions.
- **Give the bank airflow.** Don't wrap it in foam. Keep the driver board away from it.
- **Test T4, pass-through:** plug and unplug the charger with the lamp on and with it off. Some banks drop their output for a moment, which reboots the XIAO. That's harmless, since the firmware boots dark and relights on presence. Some banks give no output at all while charging, which isn't harmless: note it for the end-user instructions.
- **Test T4, temperature:** after an hour lit while charging inside the closed frame, the bank's surface should stay below about 45 °C.

### P4 (Medium): channel currents

At ~300 mA the module trimmer sits near 11% of its 47 kΩ travel. One degree of rotation moves the current about 8 mA. Two hand-set trimmers also drift independently.

**Test T2:** measure each channel in series with a meter, and record the current and the filament voltage in `docs/hardware.md`. Re-trim if the channels differ by more than about 5%.

### P5 (Info): thermal state

The model puts the CN5711 junction at about 96 °C with the 4.7 Ω ballast at 25 °C ambient, against a 135 °C foldback point. Inside the frame it will run hotter. Foldback shows up as the brightness sagging over the first 30–45 minutes. Check this once, in the frame.

### P6 (Info): keep-alive with this bank

You confirmed the bank stays awake with the PD trigger alone. The keep-alive costs ~3 mA of the ~4.2 mA dark draw. Keep it, because the frame is meant to accept other banks. The firmware option in F1 lets an installer turn it off.

## 2. Firmware

`src/main.c` at `a631148`. The structure is sound. These choices are right and should survive the G1 changes:

- An explicit light-sleep loop instead of automatic light sleep. An LEDC timer would otherwise hold a PM lock, and a fade could glitch.
- `gpio_sleep_sel_dis()` on the CE and keep-alive pads, with the comment that explains why.
- The XTAL-clocked LEDC timer, so frequency scaling can't move the PWM frequency.
- Hysteresis applied in ADC counts rather than duty.
- Wake sources armed and torn down outside the loop, with the reasoning written down.
- An integer square-law brightness curve (no soft-float `pow`).

Checked and *not* a problem: overlapping fades when the pot moves quickly. `ledc_set_fade_with_time()` waits for the previous fade's semaphore rather than returning an error, so `ESP_ERROR_CHECK` won't trip.

### F1 (High): keep-alive gap while lit

`keepalive_pulse()` is only called from `idle_sleep_until_presence()`. What the bank sees while lit (`power_model.py`):

| Brightness | Rev F (PWM duty) | G1 (analog) |
|---|---|---|
| 100% | 621 mA | 411 mA |
| 25% | 171 mA | 116 mA |
| 10% | 81 mA | 60 mA |
| 5% (Rev F floor `MIN_ON_DUTY`) | 51 mA | 42 mA |

Banks commonly switch off below 45–100 mA held for 15–60 s ([Power Bank Zone](https://powerbankzone.com/power-bank-keeps-switching-off/)). A dim setting plus someone standing in front of the piece can therefore turn the lamp off, and it stays off until someone unplugs the bank.

**Fix:**

- Estimate the load from the current brightness. Pulse 200 ms every 10 s whenever the estimate is below about 120 mA, in every state.
- Drive the pulse from an `esp_timer` while lit. A pulse only loads the rail, so it doesn't affect the light.
- Add a build flag (`FGL_KEEPALIVE=0`) for banks proven to stay on.

### F2 (Medium, G1): dimming

G1 drives both AL8860 CTRL pins from D2 through R8 (2.2 k), R9 (10 k to GND) and C7 (1 µF). The datasheet says CTRL from 0.3 V to 2.5 V sets the output "from 0 to 100% of I_OUT_NOM linearly". Below 0.2 V the output is off, and above 2.5 V it clamps at 100% ([AL8860 datasheet](https://cdn.sparkfun.com/assets/3/f/5/8/b/AL8860.pdf)). The 0.3 V offset matters: a proportional mapping would be wrong at the dim end.

- **Timer:** LEDC at 19.53 kHz, 11-bit, XTAL clock (40 MHz / 2048). Ripple on CTRL is about 19 mV p-p and the RC settles in 1.8 ms.
- **Mapping:** V_CTRL = 2.705 V × duty. For a target fraction k of full current, duty = (0.3 + 2.2k) / 2.705.
  - 100% is duty 0.924.
  - The datasheet's recommended 5% floor is duty 0.152.
  - Off is duty 0, plus `ledc_stop(…, 0)`.
- **Perceptual curve:** apply it to k, not to duty. Keep the existing square law.
- **Calibration:** confirm the offset and slope on the first board (T8). The datasheet gives no accuracy figure for analog dimming, and the two channels may not match at the dim end. If they differ visibly below 20%, the PWM fallback (C7 not fitted, ≤ 500 Hz) is accurate to 1% down to 1% duty.
- **One firmware:** `-DFGL_BOARD_REV_F` (1 kHz on the CE pads, current mapping) or `-DFGL_BOARD_G1` (above).

### F3 (Medium): sensor-fault path

When the 12 h stuck-HIGH watchdog latches, the dark state skips sleep and spins at 50 ms intervals. That's 15–20 mA awake with no keep-alive, so with most banks it ends with the bank off.

**Fix:** while latched, light-sleep on the 10 s timer only (no GPIO wake), pulse the keep-alive, and check OT2 on each wake.

### F4 (Medium): radar hold time and range

The LD2410S holds OT2 high for its own "unmanned delay", parameter 0x06, 10–120 s. Hi-Link doesn't publish the default ([LD2410S protocol V1.00](https://www.tinytronics.nl/product_files/006002_HLK-LD2410S%20serial%20communication%20protocol-V1.00.pdf)). The firmware's 25 s starts at the falling edge, so the lamp actually stays on for (radar hold + 25 s).

The UART is already wired (D4/D5, 115200 8N1). At boot:

1. Enable configuration (`0x00FF`).
2. Read parameters 0x05, 0x06 and 0x0A (`0x0071`) and log them.
3. Write the hold, the farthest gate and the nearest gate (`0x0070`).
4. End configuration (`0x00FE`).

Then choose the firmware delay. For example, radar hold 10 s plus firmware 15 s gives a real 25 s. Setting the farthest gate is also how to stop the next room triggering the lamp.

### F5 (Medium): ADC calibration

`ADC_RAW_AT_MAX` = 2950 was measured on this unit. With 10–20 boards each would need its own constant. Instead:

- Use `adc_cali_create_scheme_curve_fitting()` and work in millivolts.
- Set full scale at 95% of nominal (2.24 V × 0.95 ≈ 2.13 V) and clamp above it, so every unit reaches 100% despite 3V3 and resistor tolerance.

G1's 47 k + 100 k divider has the same ratio as Rev F's 4.7 k + 10 k, so nominal full scale is unchanged.

### F6–F11 (Low)

- **F6:** `DEBUG_LOGGING 1` is compiled in. Make it a build flag (`-DFGL_DEBUG`), default off.
- **F7:** the main task isn't on the task watchdog. Add `esp_task_wdt_add()` and reset it each loop and around sleeps. A hang currently freezes the outputs where they are.
- **F8:** the 200 ms keep-alive pulse keeps the CPU awake through `vTaskDelay`. That costs about 0.3 mA averaged. To fix it, hold the pin with `gpio_hold_en()` and light-sleep 200 ms on the timer.
- **F9:** the 12 h stuck-HIGH watchdog turns the lamp off in a room that is genuinely occupied for 12 hours, such as a gallery or a waiting room. Consider re-arming the radar over UART when it trips, rather than distrusting it.
- **F10:** DFS max is 160 MHz. Nothing here needs more than 80 MHz.
- **F11:** the header comments still say "CN5711 modules" and "25,000 mAh". Update them with the board config.

## 3. Rev G1 architecture

Schematic: `hardware/kicad/fgl_g1/fgl_g1.pdf`. One board, single 5 V rail:

```
Bank ── J1 USB-C (5.1 k Rd on CC1, CC2) ── F1 PTC 0.75 A ──┬── U2 AL8860 ── filament 1 (J4)
                                                            ├── U3 AL8860 ── filament 2 (J5)
                                                            ├── Q1 + R12 keep-alive (152 mA pulses)
                                                            └── D4 ── XIAO 5V ── XIAO 3V3 ── radar, pot
```

### D1: 5 V USB-C sink, no PD

Two 5.1 kΩ resistors (Rd) on CC1 and CC2 make the board a plain USB-C sink, so the bank supplies 5 V and nothing else. Reasons:

1. **Efficiency.** The AL8860 is more efficient at 5 V than at 9 V. The catch diode conducts for (1 − D) of each cycle, and D is 0.63 at 5 V against 0.36 at 9 V. Switching frequency and edge losses also rise at 9 V. Each bank also boosts its cell to 9 V less efficiently than to 5 V.

   | VIN | Frequency | Duty | Efficiency per channel |
   |---|---|---|---|
   | 4.5 V | 177 kHz | 0.70 | 88.4% |
   | **5.0 V** | **216 kHz** | **0.63** | **87.7%** |
   | 9.0 V | 376 kHz | 0.36 | 84.3% |

2. **Safety.** With no PD there is no way for any part to see more than the 5.5 V USB limit from a compliant source. The Perplexity G1's CH224K would have asked for 20 V if its configuration resistor were missing or cracked.
3. **Interchangeable banks.** Every USB-C bank sources 5 V into Rd, and so does every USB-A bank through an A-to-C cable.
4. **Fewer parts.** No PD controller, no second 5 V regulator, no inductor for it.

The cost of 5 V is that the AL8860's 4.5 V minimum input leaves 0.25 V below the USB 4.75 V floor. The cable, J1 and the PTC drop about 0.1 V at 0.41 A. In practice a hysteretic buck keeps regulating until VIN approaches V_LED plus its losses, about 3.3 V here, but that is outside the datasheet's range.

**PD as a keep-awake trick:** your bank stays on with the PD trigger alone. Whether it also stays on with plain Rd is unknown, which is test T1. The board doesn't depend on the answer, because the keep-alive is fitted either way.

### D2: AL8860 hysteretic buck, one per filament

| Option | Input | Efficiency, 5 V → 2.8 V at 0.3 A | Dimming | Why not |
|---|---|---|---|---|
| CN5711 / LD1500SB (Rev F) | 2.8–6 V | ~56% (linear) | PWM < 2 kHz | Efficiency; needs ballasts; thermal foldback |
| PAM2804 | 2.5–6 V, 6.5 V absolute max | ~90% | PWM | 6.5 V absolute max is too close for a cable hot-plug |
| PT4115 | 6–30 V | | | Doesn't run from 5 V |
| **AL8860WT-7** | **4.5–40 V** | **~88%** | **Analog 0.3–2.5 V, or PWM ≤ 500 Hz** | Chosen |
| BP1360 (LCSC's suggested alternative, $0.12) | Not checked | | | Datasheet not reviewed. Worth evaluating if driver cost matters at volume |

The AL8860 gives up about 2 points to a synchronous part, but its 40 V rating absorbs USB hot-plug ringing without a TVS. It also has a 0.1 V sense voltage, so only 30 mW is lost per channel in the sense resistor. Its own dissipation is about 25 mW, so thermal is not a concern.

Per channel:

- **R3/R4 = 0.33 Ω 1%** (1206), so I = 0.1 V / 0.33 Ω = 303 mA. The datasheet's sense-voltage range is 96–104 mV, so the worst case is 291–315 mA. Two channels could therefore differ by up to 8%, though typically much less. T8 measures it.
- **L1/L2 = 47 µH**, Sunlord SWPA6045S470MT: 1.4 A saturation, 0.2 Ω. The datasheet recommends 33–100 µH. Peak current is 0.36 A.
- **D2/D3 = SS14.**
- **Loop timing:** at 5 V, the on-time is 2.9 µs, comfortably above the datasheet's 500 ns minimum. Duty is 0.63, inside the recommended 25–75%.

The filament's + lead is VIN minus 0.1 V on a high-side-sense buck. Neither lead is ground-referenced, and neither may touch the frame.

**Why two drivers:** filaments in parallel on one driver split current by forward-voltage mismatch, and in series they need about 6 V, which a 5 V rail can't supply.

### D3: analog dimming through an RC on CTRL

PWM at the AL8860's ≤ 500 Hz is 100% light modulation at 500 Hz. That bands in photographs of the artwork, and some people notice it in peripheral vision. Filtered to DC, the LED current is steady, and LEDs also give more light per watt at reduced current than at full current chopped.

**Fallback:** leave C7 unfitted and use PWM at ≤ 500 Hz.

### D4: CTRL held off by hardware

R9 (10 k) holds DIM_CTRL near 0 V whenever D2 isn't driving it: reset, flashing, a panic, or light sleep. That is below the 0.2 V off threshold. This replaces Rev F's CE pull-down and its firmware workaround.

The datasheet doesn't give CTRL's internal pull-up. Its soft-start of 1.5 ms per nF implies a source of order 1 MΩ, which with R9 leaves CTRL at tens of mV. Test T7 confirms it.

### D5: input PTC

F1 is a Littelfuse 1206L075: 0.75 A hold, 1.5 A trip, 90 mΩ.

**Normal load:**

- Maximum is 0.41 A lit. The keep-alive only runs below 120 mA, so it never adds to full brightness.
- Hold current derates to about 0.6 A at 50 °C, which still leaves margin.

**Faults it covers:**

- **+ lead to ground:** current flows through R3/R4 only. The PTC trips in seconds at 2–3 A. Worst case, the 1206 sense resistor fails open first, and that channel goes dark.
- **− lead to ground:** the AL8860's switch is bypassed. The PTC trips.

### D6: keep-alive

- Q1 AO3400A is specified at Vgs = 2.5 V (48 mΩ), so the XIAO's 3.3 V gate drive switches it fully. The pulse is the designed 152 mA, not the ~115 mA of Rev F's 2N7000.
- R12 is 33 Ω 1 W 2512: 0.76 W peak, 15 mW average.
- It sits on the 5 V input, so the bank sees the full 152 mA.
- It may be left unfitted for a bank proven to stay on.

### D7: MCU, pot and radar

- **XIAO supply:** fed from +5V through D4 (SS14), as Seeed requires when powering the 5V pin. D4 also blocks back-feed when the XIAO's own USB-C is used for programming ([Seeed wiki](https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/)).
- **XIAO footprint:** `fgl:XIAO_ESP32C3_Castellated`. It has Seeed's 14 edge pads only. The pad geometry comes from Seeed's OPL_Kicad_Library (CC BY-SA 4.0).
  - Seeed's own footprint also has underside pads for VBAT, EN and the JTAG pins. Two of those duplicate D2–D5.
  - They're omitted, and copper must stay out from under the module.
  - The XIAO ESP32C3 uses an external U.FL antenna, so no antenna keep-out is needed.
- **Pot:**
  - 100 k linear pot below a 47 k top leg, so the wiper reaches 2.24 V at most. That's inside the C3's linear ADC range, and the divider draws 22 µA.
  - R6 (1 k) and C6 (100 nF) give ESD protection and a low-impedance sampling node if a panel knob is fitted.
  - Your trimmer kit has 100 kΩ (code 104).
- **Radar:**
  - J3 is 1:1 with the LD2410S header (1 3V3, 2 GND, 3 OT1/TX, 4 RX, 5 OT2), per Hi-Link's pin table.
  - R7 (100 k) holds the wake pin low if the radar cable is unplugged.
  - C8/C9 decouple 3V3 at the connector.
- **Unconnected pins:** the strapping pins D0/D8/D9 and UART0's D6/D7 are left unconnected.

### D8: deliberately left out

- **TVS on VBUS:** D1 (SMF6.0A) is on the board but DNP. Its leakage would show up in the idle budget, and the USB-C source turns VBUS on only after it sees Rd. Fit it if test T9 (hot-plugging a live USB-A to C cable) shows more than 6.5 V on +5V.
- **Reverse polarity:** USB-C is keyed.
- **USB data lines:** not connected. Programming goes through the XIAO's own port.

### X1 (Low): the XIAO's charge LED

Seeed wires the XIAO's red LED to its ETA4054 charger. One detailed write-up reports that it stays lit whenever 5 V is present with no battery ([Mischianti](https://mischianti.org/seeed-studio-xiao-esp32-c3-high-resolution-pinout-datasheet-schema-and-specs/)). That is the case in both builds, and it would add a few mA to the dark draw.

At 4 h/day the effect is small: 7.3 against 7.1 days on 20,000 mAh for 2 mA. At lighter use it matters more.

**Test T5:** look at the XIAO in the dark build. If the LED is on, remove its series resistor on each XIAO before installation.

### BOM, cost and assembly

`hardware/kicad/fgl_g1/bom.csv` lists every part. `bom_jlcpcb.csv` is the JLCPCB upload: 31 SMD placements.

**Hand-soldered:** the XIAO (U1) and the four through-hole JST-PH connectors (J2–J5). They're genuine JST parts with exact KiCad footprints. The SMD JST S3B variant was out of stock on Oct 15.

**Parts cost per board at 20 boards**, approximate LCSC prices on Oct 15:

| Group | Parts | Cost |
|---|---|---|
| Drivers | 2 × AL8860 (~$0.48 each), 2 × inductor | ~$1.2 |
| Connectors | USB-C ($0.14), 4 × JST (~$0.25 total) | ~$0.4 |
| Protection and keep-alive | PTC, MOSFET, diodes, power resistors | ~$0.3 |
| Passives | Remaining resistors and capacitors | ~$0.2 |
| **Total** | | **≈ $2.1** |

**JLCPCB fees on top, per order:**

- Roughly $3 for each extended part type. About six of these parts are extended.
- Assembly setup.
- About $5 for 10 two-layer boards.

**Per unit at 20 boards:** about $15–25 including the XIAO ($5 from Seeed, $10 on Amazon), the radar and two filaments, excluding the bank.

**Lower cost at more than ~100 units:** replace the XIAO with an ESP32-C3-MINI module, an LDO and a programming header.

| Ref | Part | LCSC | Class |
|---|---|---|---|
| U2, U3 | AL8860WT-7 | C125330 | Extended |
| L1, L2 | SWPA6045S470MT 47 µH | C36414 | Extended |
| R3, R4 | 1206W4F330LT5E 0.33 Ω 1% | C25337 | |
| F1 | 1206L075THYR | C99563 | |
| J1 | HRO TYPE-C-31-M-12 | C165948 | |
| Q1, R12 | AO3400A, 25121WF330JT4E 33 Ω 1 W | C20917, C53728 | |
| D2–D4 | SS14 | C2480 | Basic |
| J2–J5 | JST S3B/S5B/S2B-PH-K-S | C157929, C157923, C173752 | Hand |

## 4. Layout rules for G1

- **Buck loop:** per channel, keep the loop VIN cap (C2/C3) → R3/R4 → J4/J5 → L1/L2 → U2/U3 SW → D2/D3 → VIN cap as small as possible, over unbroken ground.
- **Sense resistor:** route R3/R4 as a Kelvin pair to U2/U3 VIN and SET.
- **Filament connectors:** put J4/J5 next to their channel. The filament leads carry the inductor's ripple current.
- **Radar:** keep J3 and its traces away from L1/L2 and the SW nodes.
- **XIAO:** put it at a board edge with its USB-C reachable, and keep copper out from under it.
- **USB-C:** put J1 at an edge. Run VBUS and GND through F1 with short, wide copper.
- **Mounting:** place H1–H4 (M3) to suit the frame.
- **Test points:** TP1–TP5 on the top side.

## 5. Problems in the discarded Perplexity G1 (for the record)

1. **J3 radar pin order was 3V3, GND, OUT, RX, TX.** The LD2410S header is 3V3, GND, OT1/TX, RX, OT2. The radar's TX would have driven the wake pin.
2. **Keep-alive sat after the 5 V buck.** At a 9 V contract the bank would have seen about 90 mA, which is inside the shut-off band.
3. **The 9 V PD request depended on the bank.** "Falls back to 5 V" was asserted, not verified.
4. **Dimming was PWM-only at 400 Hz.**
5. **No input protection.**
6. **The XIAO footprint was a placeholder,** and only one part had an LCSC number.
7. **ERC was reported clean, but connectivity was never checked against intent.** That is how item 1 survived.

## 6. Tests

**Before layout, on the prototype:**

- **T1. Bank without PD.** Power a bare XIAO from the bank through the XIAO's own USB-C, which presents Rd and no PD, the same as G1. Run firmware with keep-alive off and light sleep on. Is the bank still on after an hour?
- **T2. Filament Vf and current per channel at full brightness.** Record both.
- **T3. LD2410S parameters.** Read the hold, farthest gate and nearest gate over UART (F4).
- **T4. Pass-through and temperature.** P3.
- **T5. XIAO charge LED.** Is it lit with the lamp dark? X1.
- **T6. Power-up flash.** P2.

**First G1 board:**

- **T7. CTRL at reset.** TP3 below 0.2 V with the XIAO held in reset and with the XIAO removed.
- **T8. Current.** Each filament at 303 mA ±5% at full brightness, measured in series at J4/J5. Then measure current against duty at 5%, 10%, 25%, 50% and 100% on both channels, to fit the F2 mapping and check channel matching.
- **T9. Hot-plug.** Scope +5V while plugging in a live USB-A to C cable. Fit D1 above 6.5 V.
- **T10. Thermal.** After 45 minutes lit inside the frame: AL8860, L1/L2 and the bank's surface.
- **T11. Dark current, measured on the bank** (USB holds the chip awake). Expect about 1.1 mA plus 3 mA keep-alive, plus any charge LED.
- **T12. ERC.** Done on Oct 15 in KiCad 9.0.7.
  - Before the symbol update: 0 errors, and 61 warnings, all "symbol doesn't match library copy" for R_Small, AO3400A and the power symbols.
  - After updating shapes and pins from the KiCad 9 libraries: 0 errors, 0 warnings.

## 7. What changed from the Oct 14 version

Both reviews reach the same architecture: 5 V with no PD, AL8860, analog dimming, an input PTC, and the keep-alive on the input. Before redoing it I had read the Oct 14 review once. Every number in this one was recomputed, every datasheet fact re-read and every part number re-checked. These are the differences:

- **AL8860 analog curve.** Oct 14 treated CTRL as proportional, with 0.3 V giving 12%. The datasheet text says 0.3–2.5 V maps to 0–100%. The firmware mapping in F2 uses the offset.
- **PTC.** 0.75 A hold instead of 1.1 A. It trips faster on a lead fault and still has margin at 0.41 A.
- **Catch and feed diodes.** SS14 instead of B5819W, which was out of stock at LCSC on Oct 15.
- **XIAO footprint.** Edge pads only, so the underside VBAT, EN and JTAG pads can't short to anything.
- **Pot input.** A 1 k series resistor (R6) for ESD on the ADC pin.
- **TVS.** D1 placed but DNP, with a test that decides it.
- **Rev F P1.** Adds the specific below-ballast fault (5.3 W in a 2 W part) and a per-channel fuse for the prototype.
- **New findings:** X1 (charge LED), F9 (12 h watchdog in an occupied room), and the CPU-awake cost of each keep-alive pulse.
- **Verification.** A new connectivity checker with a mutation test. KiCad project renamed `fgl_g1` (was `fgl_controller_g1`).

## 8. Invoice INV-2026-1005 against the as-built parts

The invoice priced the bench-substitution variant. The build used different resistors.

| Invoiced | As built |
|---|---|
| 10 resistors from the 1/2 W kit, including 4 × 10 Ω ballast, 22 Ω keep-alive and 2 ISET resistors | 2 × 4.7 Ω 2 W and 33 Ω 2 W from the Chanzon 2 W kit (not invoiced). No ISET resistors. The 1/2 W kit supplied 4.7 k, 100 Ω, 100 k, and 10 k if R3 is fitted |

The difference is cents. The invoice wasn't changed, since it may already have been sent. To correct it, edit `items` in `inv.py`.

## Sources

- AL8860 datasheet (Diodes): 4.5–40 V input; 96/100/104 mV sense; ripple 0.4 × I; CTRL 0.3–2.5 V for 0–100%, < 0.2 V off; PWM ≤ 500 Hz; 33–100 µH; 500 ns minimum on-time; 147 °C/W. [SparkFun mirror](https://cdn.sparkfun.com/assets/3/f/5/8/b/AL8860.pdf)
- HLK-LD2410S serial protocol V1.00: pin table, 115200 8N1, parameters 0x05, 0x06, 0x0A. [Tinytronics](https://www.tinytronics.nl/product_files/006002_HLK-LD2410S%20serial%20communication%20protocol-V1.00.pdf)
- XIAO ESP32C3 (5V pin diode, pin map, strapping pins, ADC1 pins): [Seeed wiki](https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/)
- XIAO charger and charge LED: [Mischianti](https://mischianti.org/seeed-studio-xiao-esp32-c3-high-resolution-pinout-datasheet-schema-and-specs/)
- XIAO footprint geometry: [Seeed-Studio/OPL_Kicad_Library](https://github.com/Seeed-Studio/OPL_Kicad_Library), commit b0035c5
- CN5711 datasheet (low-side sink, 300 °C/W, 135 °C regulation): [electronperdido.com](https://electronperdido.com/wp-content/uploads/2024/04/CN5711-datasheet.pdf)
- Power-bank auto-off behaviour: [Power Bank Zone](https://powerbankzone.com/power-bank-keeps-switching-off/)
- LCSC part pages, checked 2026-10-15:
  - [C125330 AL8860WT-7](https://www.lcsc.com/product-detail/C125330.html)
  - [C36414 SWPA6045S470MT](https://jlcpcb.com/partdetail/C36414)
  - [C99563 1206L075THYR](https://www.lcsc.com/product-detail/C99563.html)
  - [C165948 TYPE-C-31-M-12](https://www.lcsc.com/product-detail/C165948.html)
  - [C25337 0.33 Ω](https://www.lcsc.com/product-detail/C25337.html)
  - [C53728 33 Ω 1 W](https://www.lcsc.com/product-detail/C53728.html)
  - [C20917 AO3400A](https://www.lcsc.com/product-detail/C20917.html)
  - [C2480 SS14](https://www.lcsc.com/product-detail/C2480.html)
  - [C173752 S2B-PH-K-S](https://www.lcsc.com/product-detail/C173752.html)
  - [C157923 S5B-PH-K-S](https://www.lcsc.com/product-detail/C157923.html)
  - [C157929 S3B-PH-K-S](https://jlcpcb.com/partdetail/C157929)
  - [C178260 SMF6.0A](https://lcsc.com/product-detail/TVS_SMF6-0A_C178260.html)
  - The 0603 resistors and capacitors listed in `bom.csv`
