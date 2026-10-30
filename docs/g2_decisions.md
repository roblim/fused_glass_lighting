# Rev G2: decisions and reasoning

Rev G2 replaces the Rev G1 controller design. This document records what changed, why, and what still has to be checked. Decided 2026-10-23; the fixes from the Oct 24 audit are in D16 (2026-10-25), the layout DFM pass after Gemini's review is in D17 (2026-10-26), the JP2 radar/manual jumper is in D18 (2026-10-27), and the 90 × 60 mm relayout with horizontal-entry ports and the R29 pull-up is in D19 (2026-10-28).

- **Schematic:** `hardware/kicad/fgl_g2/`
- **Design checks:** `hardware/tools/sepic_design.py`
- **Power and runtime:** `hardware/tools/power_model.py`

G1 is kept as it was on 2026-10-22: laid out, with gerbers, in `hardware/kicad/fgl_g1/`. It is superseded and should not be ordered (see D1).

## Summary

| | G1 (superseded) | G2 |
|---|---|---|
| Filaments | Exactly two 3 V 300 mm, one buck channel each, 303 mA | One series string of up to four filaments, any mix of 3 V and 12 V, from one 3 V filament up to 24 V of string |
| Driver | 2 × AL8860 buck (5 V in, string must be below 5 V) | 1 × TI TPS61500 as a SEPIC (TI SLVA904), string above or below 5 V |
| Current | 303 mA fixed (sense resistor) | 244 mA, or 488 mA with the JP1 shunt on 1-2 (no soldering); firmware trims below (for example 150 mA) |
| Outputs | 2 × JST-PH, hand-soldered | 4 × horizontal 3-pole push-in (JILN JL212R footprint; DEGSON DG212R ordered), wire entry parallel to the board at its top edge, fitted by JLCPCB, legends + / NEXT / END (D19; Degson DG250 45° ports before) |
| Input | 5 V USB-C (Rd only), 0.75 A PTC | Same USB-C, 2 A hold PTC (D12), plus a soft-starting power switch that also releases the USB-C attach |
| MCU | XIAO soldered by its castellated edge | XIAO plugs into 5 mm low-profile sockets |
| Radar | JST-PH pigtail | Plugs straight into a socket on the board, or a JST-PH pigtail (both fitted) |
| Brightness pot | 3-wire | 4-wire pot with built-in switch: counter-clockwise dims, click past the stop = whole system off |
| Firmware sensing | none | String voltage (power cap, open/short/reversed detection, low-current start check), current-range jumper |
| Presence | Radar only | Radar, or manual mode with the JP2 shunt on 1-2: lit whenever switched on, dimmed by the pot |

## D1. Filament current: 303 mA was too close to the edge

Adafruit recommends at most 50 mA for its 300 mm 3 V filament (5503). G1 ran each filament at 303 mA. That value came from the Rev F build and a convection model, never from a filament rating.

No supplier publishes a real datasheet with lifetime or temperature curves. The best available specs are DFRobot's:

- **FIT0926 (12 V 600 mm, 2200 K):** 500 mA, 6 W, 400 lm, 320 LEDs, life 5,000–10,000 h, ambient −30 to +55 °C.
- **FIT0927 (24 V 1.2 m):** 300 mA at 22 V, 6.6 W, 500 lm, 640 LEDs. DFRobot recommends 21–22 V for long-term use.

Comparing per metre and per LED, with LED counts for the 3 V parts from Kitronik and Ledbe (about 200 per 300 mm):

| | Power per metre | Current per LED (estimate) |
|---|---|---|
| DFRobot rated (12 V / 24 V) | 10 / 5.5 W/m | ~4–6 mA |
| G1 (2 × 300 mm at 303 mA) | 2.8 W/m | ~1.5 mA |
| **G2 default: one 12 V 600 mm at 150 mA** | 2.7 W/m | ~1.9 mA, 30 % of rating |
| G2 alternative: 4 × 3 V 300 mm at 150 mA | 1.4 W/m | ~0.75 mA |
| Adafruit's 50 mA | 0.5 W/m | ~0.25 mA |

Other suppliers' ratings for similar 300 mm 3 V filaments run from 25 mA (Kitronik) and 80 mA (DFRobot 260 mm) through under 200 mA (Ledbe) to 300 mA (Zionsville, iFuture). Adafruit's figure is conservative, but its own 12 V product is rated at 20 times the power per metre.

**Decision:** drive at about half or less of the best published rating, and get brightness from filament length rather than current density. The prototype piece looked right in daylight at about 1.7 W of LED power. That equals one 12 V 600 mm filament at 150 mA, about 115 lm estimated from DFRobot's 67–76 lm/W. Lifetime ratings are quoted at rated power, so derating is what buys a long life.

## D2. One series string, not one driver per filament

The driver sets the current, so every filament in a series string carries the same current and the voltages simply add. Drop in the wiring is negligible: about 0.03 V per metre of 28 AWG at 150 mA.

That makes 3 V and 12 V filaments mixable on one board with no jumpers or modes. One more filament is just a longer string.

Rules for mixing:

- **Brightness per length:** at a given current it scales with the filament's voltage per length. A 12 V 600 mm and a 3 V 150 mm look alike; a 3 V 300 mm looks about half as bright. Use filaments with the same voltage per length within a piece when an even glow matters.
- **Current limit:** the most fragile filament sets the maximum current.
- **Failure:** one open filament, or a wrong terminal, darkens the whole string. The voltage sense (D5) detects it.
- **Total voltage: up to 24 V.** Any mix whose nominal voltages add up to 24 V or less: with one filament per port: up to two 12 V filaments, up to four 3 V, or one 12 V with up to three 3 V. Four ports do not mean four 12 V filaments: a 48 V string can't light. The SEPIC stops at OVP (27.7 V, a fault limit, not an operating point), the firmware reads that as an open string (VOUT ≥ 25.5 V, D5) and retries every 30 s. Nothing is damaged.

## D3. TPS61500 as a SEPIC

A boost converter cannot run a string below its 5 V input. Two 3 V filaments (about 5.5 V) would glow when off, and one 3 V filament would see an uncontrolled current limited only by the fuse.

A SEPIC regulates above and below the input, and its coupling capacitor C4 blocks DC. That gives no leakage when off and no uncontrolled path into a short string.

TI documents exactly this use in [SLVA904, "TPS61500 SEPIC Configuration"](https://www.ti.com/lit/an/slva904/slva904.pdf) (April 2018). Its worked example is 5–18 V in, 12.3 V at 500 mA, which is close to G2's case.

Alternatives considered (LCSC prices, 2026-10-23):

| Option | Price (10 / 100) | Why not |
|---|---|---|
| TPS61500 boost only | $1.23 / $0.77 | Needs at least three 3 V filaments or one 12 V; unsafe with a single 3 V |
| **TPS61500 SEPIC** | same + ~$0.35 (L2, C4) | **Chosen** |
| TI LM3410 SEPIC | $2.46 / $2.06 | 24 V switch limits the string to about 18 V; pulse dimming only; low stock |
| TI TPS92692 controller | $1.66 | Out of stock; 4.5 V minimum input is too close to a sagging 5 V bank; external FET |
| TI LM3421 controller | $3.32 / $2.84 | Same 4.5 V input problem; external FET |
| ADI LT3952 | | Obsolete |

### Values (`sepic_design.py`)

| Part | Value | Reason |
|---|---|---|
| L1, L2 | 10 µH, SWPA8040S100MT (4.1 A sat), not coupled | TI used 4.7 µH. 10 µH halves the ripple, which keeps the switch peak below the 3 A minimum limit when the bank sags to 4.5 V. SLVA904's coupled inductor is limited to about 430 mA |
| C4 (coupling) | 10 µF 50 V 1206, X5R (Samsung CL31A106KBHNNNE, JLCPCB basic, since 2026-10-29; X7R CL31B before) | Sits at VIN (≤ 5.25 V); ripple ≤ 34 mV. X5R is rated to 85 °C, enough at a 55 °C ambient |
| D5 | SS36 (60 V, 3 A) | Sees VIN + VOUT ≈ 35 V |
| C5, C6 | 10 µF 100 V X7S 1210 (Murata GRM32EC72A106KE05L) + 100 nF 100 V | Output. 100 V keeps more than 2× margin over the worst-case OVP (29.1 V) and keeps most of C5's capacitance there (D16, audit M2) |
| R19 (FREQ) | 82 k → ~1.17 MHz | Datasheet: 80 k → 1.2 MHz |
| R15 / R16 (OVP) | 110 k / 5.1 k → 27.7 V (26.4–29.1 V worst case) | Switch at OVP sees 33.5 V typical and 35.1 V worst case (OVP and resistors at their limits, 5.5 V in), against the 40 V absolute maximum: 12 % margin. Longest supported string 24 V (D16, audit M3; was 120 k → 30.1 V) |
| R20, R21 (sense) | 0.82 Ω 1 % 1206 | 0.2 V / 0.82 Ω = 244 mA; both in parallel = 488 mA; 49 mW each |
| C9 (COMP) | 100 nF | Lowest right-half-plane zero (the main stability limit) is 43 kHz (5 W into 12 V at 4.5 V in), so crossover must stay below 4.3 kHz. SLVA904 measured 1.7 kHz with 15 nF and 4.7 µH; 100 nF and 10 µH is lower still. Tune between 15 and 470 nF on the bench |
| C8 (SS) | 100 nF | About 30 ms soft-start |
| C7 (DIMC) | 1 µF | Analog dimming: the PWM on EN becomes the FB reference (200 Hz–40 kHz); I_LED = duty × I_max, no flicker |
| R17 / R18 | 1 k series / 2.2 k to GND on EN | GPIO20 (U0RXD) has a ~45 k pull-up at reset, so R18 must be stiff: EN stays ≤ 0.22 V (VIL 0.4 V) even with a 30 k pull-up, and reaches 2.27 V (VIH 1.2 V) when driven. Was 100 k, which let the driver run at its ceiling during every boot and USB flash (D16, audit H1). The series resistor protects EN if the XIAO is powered from its own USB while VIN is off |

Worst-case switch peak is 2.18 A, against the 3.0 A minimum limit (27 % margin, with inductance and frequency each 20 % low).

| Case (VIN 4.5 V) | Duty | Input current | Switch peak | Switch voltage |
|---|---|---|---|---|
| One 3 V filament at 244 mA | 0.42 | 0.18 A | 0.67 A | 7.8 V |
| One 12 V 600 mm at 150 mA | 0.72 | 0.43 A | 1.01 A | 15.9 V |
| 12 V or 4 × 3 V at the 5 W cap | 0.73 | 1.31 A | 2.18 A | 16.8 V |
| 24 V string at the 5 W cap | 0.84 | 1.31 A | 2.02 A | 29.0 V |

## D4. Current: 244 mA or 488 mA ceiling, firmware below it

The hardware ceiling is the safety limit, so a firmware bug cannot exceed it:

JP1 is a 2.54 mm 1×3 pin header (pin 1 RS2_B, pin 2 GND, pin 3 ISEL) with one shunt, so the range is set without soldering (D16):

- **Shunt on 2–3:** R20 only, **244 mA**. ISEL is grounded, so the firmware reads 244.
- **Shunt on 1–2:** R21 is added in parallel, **488 mA**. ISEL stays high (R23), so the firmware reads 488.
- **No shunt:** the hardware is at 244 mA, but ISEL is high, so the firmware assumes 488 and asks for half the current it wants. That errs dim, never bright.

One shunt can't produce the old solder jumper's unsafe half-bridge (488 mA in hardware while the firmware assumed 244). Silkscreen: "JP1 shunt 1-2 (right): 488 mA" and "JP1 shunt 2-3 (left): 244 mA", with "1" over the square pin. On the 488 mA setting R21's current passes through the shunt; a contact resistance of 20 mΩ lowers the ceiling by about 1 %.

The firmware stores a per-piece maximum, for example 150 mA (61 % duty), and the pot's full travel maps onto zero to that maximum. Accuracy is about ±3–4 %: FB ±2.5 %, Rs 1 %.

The 1 A option was rejected. From a 5 V bank, 1 A limits the string to about 10 V, and it would need a 4 A switch, a 3 A fuse and buck-boost parts throughout.

## D5. String-voltage sense and a 5 W power cap

VSENSE = VOUT / 13 (R24 120 k, R25 10 k) goes to D2/GPIO4, an ADC1 input. OVP (27.7 V) reads as 2.13 V. It draws nothing when the driver is off, because C4 blocks DC.

The firmware uses it to:

- **cap LED power at 5 W** (VOUT × I_set), which is about 1.25 A from a 5 V bank and up to about 1.4 A when the bank sags to 4.5 V (F1 is sized for that at 55 °C, D12);
- **check every start at low current:** the driver comes up at 10 % of the piece maximum (at least 10 mA) and VOUT is read before anything brighter is allowed (D16);
- **flag an open string or a reversed filament:** VOUT ≥ 25.5 V (near OVP);
- **flag a shorted output:** VOUT ≤ 1.5 V while lit;
- **flag a string that doesn't match the piece:** VOUT at the probe current outside a per-piece window (fixed at build time, or learned once and stored in NVS). This catches a reversed filament whose reverse breakdown is below OVP;
- **report what is connected:** one 12 V filament reads about 11 V, three 3 V filaments about 8.4 V.

The cap is 5 W, not 6, because SLVA904's own 6 W example peaks at 2.93 A in the switch.

## D6. Outputs: four Degson push-in ports with an END terminal

*Since 2026-10-28 (D19) the ports are horizontal-entry blocks (JILN JL212R, ordered as the same-size DEGSON DG212R since 2026-10-29); the wiring scheme below (+ / NEXT / END) is unchanged.*

- **Ports:** J5–J8 are Degson DG250-3.5-03P-11-00A(H) (JLCPCB C7588159, extended part, wave-soldered). This is a WAGO 250-series equivalent at about a third of the price that JLCPCB can fit; WAGO isn't stocked at LCSC.
- **Wire:** 22–16 AWG. Use 22 AWG pigtails on the filaments; ferrules are optional.
- **Terminals:** 1 **+** (string in), 2 **NEXT** (to the next port's +), 3 **END** (string return). Fill ports in order; the last filament's − goes to END. PORT 4's NEXT is also END.
- **Wire with the power switch off.** With an open string VOUT sits near OVP (~28 V) with C5 charged; pushing a filament in then dumps that charge into it. Silkscreen: "SWITCH OFF BEFORE WIRING PORTS" (D16).
- **Why END:** no shorting links are ever needed in empty ports. One filament means + and END of port 1.
- **Silkscreen:** large legends, no colour coding (polarity is shown by the legends).
- **A single port plus an off-board chain board** was considered. Four on-board ports were chosen because they need no extra parts.

Footprint `fgl.pretty/TerminalBlock_Degson_DG250-3.5-03P` comes from Degson's drawing DG250-3.5-XXP-1Y-00A&Z(H) and was checked against Degson's STEP model on 2026-10-24:

- one pin per pole, staggered: odd poles in row A, even in row B, 5.0 mm apart;
- 1.2 mm holes;
- body 3.5 × N + 1.5 mm long, 12 mm deep, rear edge 2.35 mm beyond row A;
- the wire entry is on the row-B side (row B is the row nearer the entry), so on this board it faces the top edge;
- seen from above with the entry at the top, pin 1 is 1.8 mm from the left end of the body and the last pin is 3.2 mm from the right end.

Before 2026-10-24 the outline (silkscreen, fab and courtyard) was mirrored, with 3.2 mm at pin 1, so the drawn body sat 1.4 mm left of the real one. The pads were always right. The fix moved only graphics (D15).

## D7. Input stays plain 5 V USB-C (no PD)

The SEPIC is about 84 % efficient, roughly what a bank's own boost to 9 or 12 V achieves. Cutting cable current saves about 2 % at these powers.

PD would rule out non-PD banks, add a controller, and still require handling banks that fall back to 5 V.

The board's CC pins carry only the 5.1 k sink resistors (R1, R2), so it can't read how much current the bank's USB-C port advertises. Full power (5 W, up to about 1.4 A) needs a bank whose USB-C port supplies at least 1.5 A at 5 V; nearly all do (most advertise 3 A). At the default setting (one 12 V filament at 150 mA, about 1.6 W) the board draws about 0.42 A, which any USB source supplies. Noted after Flux's second layout review (2026-10-29). The TPS61500 accepts 2.9–18 V, so a PD front end could be added later if a bigger project ever needs more than about 10 W.

## D8. Power switch on the pot

The pot has a built-in switch (off at the counter-clockwise stop) on J2 pin 4, SW_N.

- **SW_N to GND (switch on):** the USB-C Rd resistors (R1/R2) reach ground, so a USB-C bank sees a fresh sink attach and turns VBUS on. Q2 (AO3401A P-FET) turns on and feeds +5V.
- **Switch off:** the Rd resistors float, so the bank sees nothing attached and sleeps. R13 holds Q2 off. Board draw is 0.
- **Why both:** Q2 also cuts non-compliant banks and USB-A-to-C cables, which ignore Rd. On those, some banks still need a button press to wake, which no board design can fix.
- **Switch current:** under 0.5 mA, so any small pot switch's rating is fine. R14 keeps cable ESD off Q2's gate.
- **Soft start (D16):** R14 is 10 k and C16 (100 nF, gate to source) ramps Q2's gate over ~1 ms, so Q2 conducts over about 0.5 ms and +5V's ~22 µF charges at about 0.2 A instead of an amps-level spike. Turn-off takes ~10 ms (R13 × C16); the bank drops VBUS anyway once Rd floats. With the switch open, the CC pins now see 5.1 k + 110 k to VBUS_F, still read as open by every Rp level.

Switching on always starts at minimum brightness, because the click is at the dim end. Cutting the whole system, not just the LEDs, gives zero draw and lets the bank sleep.

## D9. XIAO on low-profile sockets

The XIAO ESP32C3 is ordered with pre-soldered headers and plugs into J9/J10:

- **Sockets:** Hong Cheng HC-PM254-5.0H-1x7PZ (C27985232), 5 mm insulator, 3 mm pins, fitted by JLCPCB.
- **Geometry:** from Seeed's OPL_Kicad_Library XIAO-ESP32-C3-DIP: rows 15.24 mm apart, pin 1 (D0) at the USB-C end. J9 pin k = XIAO pin k; J10 pin k = XIAO pin 7 + k.
- **Height:** module top about 9 mm above the board if the header pins seat fully, or about 11 mm if they bottom out in the sockets first (see the pin-length item in D15).
- **USB-C:** the XIAO's own USB-C faces the board edge for flashing.
- **Schematic:** U1 is drawn for clarity but marked "not on board"; KiCad leaves it out of the netlist and the PCB.

## D10. Radar plugs into the board, pigtail kept

- **J3:** a 1×5 2.54 mm 5 mm socket (HC-PM254-5.0H-1x5PZ, C27985230). The LD2410S (20 × 20 mm, 2.54 mm header) plugs in with its antenna facing away from the board.
- **J4:** a JST-PH 5-pin wired in parallel, for a remote sensor. Use one or the other.
- **Mounting side:** one. Flip the whole board in the frame when the sensor needs to face the other way. A second footprint was rejected for space, and JLCPCB fits one side per order.
- **Placement:** the radar sits at the far end from the SEPIC. FB1 (600 Ω ferrite) with C13/C14 filters its 3.3 V.
- **Sensor view:** ±60°. Glass, wood and plastic are fine in front of it; metal and foil aren't. The board's position now sets where the sensor looks.

## D11. Keep-alive stays, with a firmware off switch

Q1 and R12 are unchanged (152 mA pulses, 3 mA average).

The firmware pulses only while the board draws less than the bank's threshold: dark, or dimmed below about 30 %. A saved setting, on by default, can turn it off. Leaving R12 unfitted is the hard off.

Measured cost against benefit (20 Ah, 4 h/day, one 12 V filament at 150 mA):

- **Runtime cost:** +3.6 % runtime without the pulse, +7 % at half brightness.
- **Idle without the pulse:** about 0.7 mA, once the 10 s wake used only for the pulse is also dropped.
- **Risk of turning it off:** a bank that needs the pulse would switch off and leave the lamp dead, so the default stays on.

## D12. Fuse: 2 A hold (was 1.5 A)

F1 is a Brightking SMD1812B200TF/16 (LCSC C269145, 1812): 2.0 A hold, 3.5 A trip at 23 °C, 16 V, R1max 0.075 Ω. It replaced the SMD1812B150TF/8 (C269137, 1.5 A hold) on 2026-10-29, before the first order.

**Why it changed.** A PTC's hold current falls as it warms. Brightking's derating table gives the 1.5 A part 1.10 A at 50 °C and 1.02 A at 60 °C, about 1.06 A at the 55 °C we allow inside a closed frame. The 5 W cap draws about 1.25 A at 5 V and up to about 1.4 A at 4.5 V (D5), so the old fuse would have heated, tripped and cycled the lamp at full power in a warm frame. Flux's second layout review found this (2026-10-29); the original choice only compared 1.25 A with the 23 °C rating. The 2 A part holds 1.67 A at 50 °C and 1.50 A at 60 °C (about 1.58 A at 55 °C), 13 % above the 4.5 V worst case, and its lower resistance drops about 0.1 V instead of 0.17 V at 1.4 A.

**What it still protects.** It trips at 3.5 A (23 °C), so a short downstream of it is still cut off by the fuse or by the bank's own current limit, whichever comes first; most banks limit at 2.4–3.5 A. The 16 V rating also covers the hot-plug ringing on VBUS_F that G2-T6 measures (a PTC only needs the rating when it has tripped).

**Checks.** G2-T2 now also runs inside the closed frame and logs the input current and F1's temperature. If F1 runs close to its derated hold there, the firmware cap can come down (about 3.5 W keeps the input under 1.0 A). Same 1812 footprint and 3D model; no layout change. Re-check JLCPCB stock at order time; LCSC C20812 (RUILON SMD1812P200TF16, 2 A hold) is the fallback, after checking its derating table.

## D13. New revision folder

G1 was laid out and committed on 2026-10-22 with gerbers ready. G2 changes most of the power path, the connectors and the pin map, so it is a new project, `fgl_g2`, not an edit of G1.

`gen_g2.py` draws the first version and `g2_expected.py` states the intent independently. Once the schematic is saved in KiCad 9, the KiCad file becomes the master and the generator refuses to overwrite it, as for G1.

## D14. Carried over from the Oct 22 G1 audit

[`g1_netlist_audit.md`](g1_netlist_audit.md) found no wiring errors in G1. Two of its low-severity items apply to G2 and are fixed here:

- **L1, pot pin order:** J2 is now numbered like a pot: 1 = CCW end + switch common (GND), 2 = wiper, 3 = CW end, 4 = switch. A 1:1 cable to pot terminals 1–3 then gives clockwise = brighter.
- **L3, ESD on cable-exposed GPIOs:** R26–R28 (1 k) are in series on the radar UART and OT2 lines, between the XIAO and J3/J4. R7 (OT2 pull-down) is on the XIAO side.

Its other items, in G2 terms:

- **M1 (pot full-scale clamp ≈ 1.85 V):** done in firmware (2026-10-25): the G2 build reads the pot in calibrated mV with full scale at 1.85 V.
- **L2 (UART_RX floats with no radar):** done: the G2 build holds both radar UART pins with pull-ups. An unplugged pot means the board is off.
- **L4 (keep-alive fail-safe):** done: the main task is on the task watchdog (15 s, panic and reboot) in both builds; an AC-coupled gate remains optional.
- **I2 (USB-A hot-plug):** test G2-T6 checks that the XIAO's 5V pin stays at or below 6.0 V when a live USB-A cable is plugged in. D1 (the TVS, not fitted) can't guarantee that (it starts conducting at 6.67 V); if the test fails, use USB-C-to-C only and add an input over-voltage cut-off in G3.
- **Not applicable:** L5, L6 and I1 concern the AL8860 and its dimming RC, which G2 doesn't have.

## D15. Layout (2026-10-23)

*Superseded on 2026-10-28 by the 90 × 60 mm layout in D19; kept as the record of the first layout.*

The board is 74 × 58 mm, 2 layers, with 1.5 mm corners and four M3 holes. The scripts that placed and routed it are in `hardware/tools/layout_g2/`. A preview image is in `hardware/kicad/fgl_g2/fgl_g2_layout.png`.

**Where things are:**

- **Top edge:** the four ports, PORT 1 (J5) on the left. The wire entry faces the edge, and the legends + / NEXT / END and PORT n sit under each port.
- **Under the ports:** the string chain (NEXT of one port to + of the next) runs on top, row to row. A 1 mm LED_RTN bus joins every END pin underneath it.
- **Right edge:** the USB-C input. Current flows right to left: J1 → F1 → Q2 → a 1 mm +5V spine along y ≈ 16 → L1 → U2.
- **Middle:** the SEPIC.
  - U2 is rotated so that SW, VIN, EN, SS and DIMC face up, and COMP, FB, FREQ, OVP and PGND face down.
  - L1's SW pad is 2 mm from the SW pins. C4 is directly below L1, then D5 and L2. C5 and C6 are next to D5's cathode.
  - The hot loop is C4 → D5 → C5 → GND vias → solid B.Cu ground → U2's exposed-pad vias. It is about 8 × 12 mm. It isn't the tightest possible loop, but the bottom layer under it is solid ground: auto-routed copper is kept off B.Cu there.
- **Bottom-left:** the XIAO sockets, with the USB-C at the left edge and a silkscreen outline. The low parts underneath are the VSENSE divider, the pot filter and the ISEL resistors. They sit under the plugged-in module, which clears them by about 5 mm.
- **Bottom edge:** the pot connector J2 and the radar cable J4. The radar socket J3 is in the bottom-right corner, and the module sits over the low parts there.

**Sensing:**

- R20 and R21 (0.82 Ω) take LED_RTN from the bus.
- FB is a separate 0.25 mm trace from R21's pad. It reaches U2 through a via and B.Cu, so it carries no LED current.
- The VSENSE divider is at the XIAO, about 25 mm from the switch node.

**Changes made during layout:**

- **U2 thermal vias:** enlarged from 0.2/0.5 mm to 0.3/0.6 mm. JLCPCB's standard 2-layer process starts at 0.3 mm. KiCad will report this as "footprint differs from library" for U2, and that's expected.
- **Degson courtyard:** trimmed to the body. The port row now ends at y = 12.6 (after the 2026-10-24 outline fix).
- **Thermal spokes:** J3 pin 2 and J4 pin 2 (GND) connected solidly to the pour, because neighbouring tracks left them only one spoke. Changed to thermal reliefs on 2026-10-26 (D17).
- **Design rules:** copied from G1, which follows JLCPCB's standard process: 0.2 mm clearance, 0.5 mm copper-to-edge, 0.3 mm minimum drill, 0.8 mm minimum silkscreen text.

**Still on the fab layer, not the silkscreen:** the references of R15, R16, C2 and C4. There was no clear spot for them, and the assembly drawing and CPL still carry them. (Every part has a silkscreen reference since 2026-10-28, D19.)

### 3D models (2026-10-24)

The parts that matter mechanically now use the makers' own 3D models, stored in `hardware/kicad/fgl_g2/3dmodels/` and referenced through `${KIPRJMOD}`, so they travel with the project. `hardware/tools/set_3d_models.py` attaches them and records each transform and how it was worked out.

| Ref | Part | Model source |
|---|---|---|
| J5–J8 | Degson DG250-3.5-03P-11-00A(H) | Degson, from the product page (`DG250-3.5-03P-11-00A&Z(H).stp`) |
| J3 (module) | Hi-Link HLK-LD2410S | Hi-Link's official download folder (`HLK-LD2410S-3D.zip`), linked from hlktech.net |
| J1 | HRO TYPE-C-31-M-12 | JLCPCB/EasyEDA official library (LCSC C165948) |
| F1 | Brightking SMD1812B150TF/8 | JLCPCB/EasyEDA official library (LCSC C269137). It is a generic 1812 model, 4.5 × 3.2 × 1.0 mm |
| J9, J10 | Hong Cheng HC-PM254-5.0H-1x7PZ | JLCPCB/EasyEDA official library (LCSC C27985232) |
| J3 (socket) | Hong Cheng HC-PM254-5.0H-1x5PZ | Derived from the 1×7 model (`tools/trim_socket_1x5.py`), because the library's own 1×5 model (C27985230) is 8.5 mm tall and the part is 5.0 mm |
| XIAO (on J9/J10) | Seeed XIAO ESP32C3 | The GrabCAD model that Seeed's wiki links to (`XIAO_ESP32C3.step`). It is a community model by Maurice Pannard, drawn from Seeed's DXF; the SoC shield was corrected from a Seeed drawing. Its author notes that the USB-C and the antenna connector are approximate. Placed by fitting all 14 pins to the J9/J10 pads (exact fit) |
| XIAO headers | Pre-soldered 2.54 mm headers | No maker model; KiCad's stock 1×7 header, upside down |

The other parts keep KiCad's stock models, which already match: the JST-PH connectors, U2, the inductors, the diodes, the transistors and the passives. The models from the JLCPCB/EasyEDA library are © JLCEDA/EasyEDA ([easyeda.com](https://easyeda.com), [lceda.cn](https://lceda.cn)).

Before this, the USB-C and F1 showed nothing in KiCad 9: the model files they pointed to aren't in KiCad 9.0.7's library. The ports had no model, and the sockets used KiCad's 8.5 mm generic socket.

**Found while doing this:**

- **Degson outline was mirrored** (D6). Fixed on the board and in `fgl.pretty`. Only graphics moved, and the courtyard's rear now stops 0.5 mm behind the body.
- **Header pins against the 5 mm sockets.** In the socket model the contacts end 1.0 mm above the board, so a pin can go in about 4 mm. Standard male headers, including the LD2410S's in Hi-Link's model, have 6 mm pins below the plastic. Such a module stops about 2 mm above the socket top unless its pins are trimmed to about 4 mm. The 3D view shows the radar and the XIAO at that raised height. This is mechanical only: the contacts still grip the pins. Check it with the first sockets and modules, and trim the pins if the extra height matters in the frame.

## D16. Fixes from the Oct 24 audit (2026-10-25)

[`g2_netlist_audit.md`](g2_netlist_audit.md) found no wiring errors, one design-intent error (H1) and several margins. All are addressed:

| Audit item | Change |
|---|---|
| **H1** EN high during boot and USB flashing (GPIO20 reset pull-up) | R18 100 k → **2.2 k** (C4190, the part G1 used). EN ≤ 0.22 V at reset with any plausible pull-up (D3 table) |
| **M1** CPL vs the JST-PH rotation rule | Not changed: the preview check stays the gate. `make_cpl.py` now flags the JP1 header too. JST-PH J2/J4 openings must face the bottom edge |
| **M2** Output capacitors at 1.6× OVP | C5 → 10 µF 100 V X7S **1210** (Murata GRM32EC72A106KE05L, C576517); C6 → 100 nF 100 V (CL10B104KC8NNNC, C15725). Now 3.4× the worst-case OVP |
| **M3** Switch margin at OVP | R15 120 k → **110 k** (0603WAF1103T5E, C25805): OVP 27.7 V, switch ≤ 35.1 V worst case. Longest supported string 24 V |
| **M4** Hot-connecting into a charged output; reversed filaments | Firmware guards (below) and the silkscreen warning "SWITCH OFF BEFORE WIRING PORTS" |
| **L1** JP1 half-bridge | JP1 is a 1×3 pin header with a shunt (C49257 header fitted by JLCPCB; C5305 shunt, loose). See D4 |
| **L2** Q2 hard turn-on | R14 1 k → **10 k**, new **C16** 100 nF 0402 gate-to-source (CL05B104KO5NNNC, C1525). See D8 |
| **B1–B3** BOM tidy | U1 listed once (`make_bom.py` skips parts that `BOM_EXTRA` lists); the shunt has its own line; capacitor values carry their voltage, resistor values their tolerance; the JP1 legend gives exact currents (244/488 mA) |

**Layout changes** (the `.kicad_pcb` stays the master; edits were made to it directly, then zone-filled and checked in KiCad 9.0.7):

- **C5:** 1206 → 1210 in place. The pads keep the same pitch and only grow; courtyards clear C9, C6, TP6 and D5.
- **JP1:** the solder jumper next to R21 is gone. The 1×3 header sits horizontally at (122.5, 116.8) in the clear area between the PORT 1 VOUT track and the LED_RTN column, with pin 1 (square) on the right. RS2_B runs from R21 pad 2 through a via and a 0.6 mm B.Cu track to pin 1. ISEL runs from pin 3 on B.Cu to a new via that joins the old ISEL route to R22/R23. A GND via in the wedge between the two tracks stitches the pour island under pin 2.
- **TP3** moved 1.2 mm right and 0.6 mm down to clear JP1's courtyard, and its track was re-joined. The GND stitching via that sat under JP1 pin 1, and the old jumper's GND via, were removed.
- **C16:** 0402 between Q2 and R13, with its pads on the Q2_G and VBUS_F tracks.
- **Silkscreen:** the JP1 legend (above), "1" over its square pin, and "SWITCH OFF BEFORE WIRING PORTS" under the board title. The R13 and C16 references are on the fab layer, like R15, R16, C2 and C4.
- **Result:** DRC 0 errors, 0 unconnected pads. 69 warnings: J1's silkscreen at the board edge (2, as before) and one library-path notice per stock footprint (67). `verify_pcb.py` passes (181 pads, 67 footprints).
- **3D render:** `fgl_g2_3d.png` was re-rendered on 2026-10-26 (D17) and shows these changes.

**Firmware guards** (`src/main.c`, build `seeed_xiao_esp32c3_g2`; details in its header comment):

- **Every start** (each time someone arrives): the driver comes up at the probe current, 10 % of the piece maximum and at least 10 mA. VOUT is read after 200 ms. Only a string that passes is faded up to the knob setting.
- **Open or reversed (VOUT ≥ 25.5 V), short (≤ 1.5 V), or outside the piece window:** EN low, the reason logged, and a retry after 30 s, light-sleeping in between with keep-alive pulses.
- **While lit:** the same open/short checks every 50 ms, and the 5 W cap from the measured VOUT.
- **Window:** set at build time with `FGL_STRING_VMIN_MV`/`FGL_STRING_VMAX_MV`, or learned on the first good start and kept in NVS (±15 %, at least ±0.6 V). After rewiring on purpose, relearn: within 10 s of switching on, turn the knob fully clockwise and back to the minimum. The lamp blinks off once to confirm, and relearns at the next start.
- **JP1:** read at every start (low = 244 mA). A piece maximum (`FGL_MAX_CURRENT_MA`, default 150 mA) above the ceiling is clamped to it.

## D17. Layout DFM pass after Gemini's review (2026-10-26)

Gemini reviewed the layout from the review package's plots and renders: [`g2_layout_dfm_audit.md`](g2_layout_dfm_audit.md). Each finding was checked against `fgl_g2.kicad_pcb` and the 3D model; the resolution is at the end of that file. Changes:

- **Fan-out vias off the pads.** Gemini named C3, C7, C8 and R18, whose GND vias sat 0.12 mm from their pads. A board-wide check found 24 more vias in the same autorouter pattern, including one 0.06 mm from C5 that the D16 change to a 1210 left behind. 25 vias in all moved, with their stub tracks, to at least 0.25 mm from every SMD pad, keeping ≥ 0.25 mm to other-net copper. Three stay close because there is no clear spot: the POT_W via by R6 (0.125 mm, under the XIAO), the ground via shared by input caps C1/C2 (0.137 mm) and the LED_RTN via by R19 (0.225 mm). All vias are tented on both sides, so no via is open next to a pad.
- **J3 and J4 pin 2 (GND) on thermal reliefs** instead of solid connections, for better hole fill when JLCPCB solders these through-hole parts and for rework. KiCad needs at least two spokes per layer:
  - J4: the spoke pattern is turned 45° (`thermal_bridge_angle 45`), which gives the oval pad spokes past the UART_RX via;
  - J3: RADAR_OT2_C's run under the socket moved down from y 155.9 to 156.9 (still ~1 mm inside the board edge), and two GND vias at (153.27, 156.1) and (155.81, 156.1) tie the strip of top-layer ground under the pins to the bottom pour. Its default diagonal spokes reach that strip.
- **Ground stitching.** Ten GND vias added in the area between the XIAO and U2 where the VOUT, +5V, DIM_PWM, ISEL, RS2_B and LED_RTN diagonals cut the pours, each ≥ 0.55 mm from other-net copper on both layers and ≥ 2.5 mm from other GND vias. The fast-switching loop is not in this area (it is over solid B.Cu by U2, D15), so this is tidying rather than a fix. The VOUT diagonal was not rerouted.
- **Assembly drawing.** `fgl_g2_assembly.pdf`: page 1 is the top fab layer with every reference designator (including the six that are not on the silkscreen: R13, R15, R16, C2, C4, C16), scaled to A4; page 2 lists every part by reference with its value and MPN. Fab-layer text was tidied for it (duplicate references hidden on C16, R13, R15, R16; references moved off the pins of J3, J9, J10 and JP1, and TP5's off C14; J5–J8 given fab references). The silkscreen is unchanged.
- **Radar over L2: no change.** Gemini read the top render as the radar module overhanging L2. Measured in the 3D model, the module's edge stops 0.9 mm short of L2 in plan, and its underside is about 8.4 mm above the board against L2's 4.2 mm height. Magnetic pickup from L2 is unlikely through the module's ground plane, but G2-T11 checks it.
- **TP5 is covered by the radar** when it is plugged into J3. TP5 is RADAR_OT2 (presence). With the radar in place, probe it at XIAO D3 (J9 pin 4), or at J4 pin 5 (the radar side of R28).

Result: DRC 0 errors, 0 unconnected pads, the same 69 warnings (J1 silkscreen at the edge, 2; library-path notices, 67). `verify_pcb.py` passes. Vias 116 → 128. Gerbers and drill files regenerated; the position file and CPL are unchanged (no part moved).

## D18. JP2: radar or manual mode (2026-10-27)

Some pieces will hang where presence switching isn't wanted, or the radar won't be fitted. JP2 lets the owner turn presence detection off with a shunt; the lamp is then controlled by hand with the pot and its switch.

- **Part:** a second 1x3 2.54 mm header with a loose shunt, the same parts as JP1 (C49257 header, C5305 shunt), so no new JLCPCB part types.
- **Pins:** 1 = GND (square pad, on the right, like JP1), 2 = RADAR_MODE to XIAO D8 (GPIO8, J10 pin 2), 3 = parking (no connection).
  - Shunt on **1-2 (right): manual.** D8 reads low.
  - Shunt on **2-3 (left), or no shunt: radar**, as before. D8 reads high.
- **Why D8:** it was the only free XIAO pin that is safe for this. D0 (GPIO2) must be high at boot, and D9 (GPIO9) is the BOOT button: low at reset selects download mode. GPIO8 only matters in download boot (GPIO9 low), where GPIO8 low is an invalid combination. So **move the shunt off 1-2 before forcing download mode with BOOT**; normal power-on and USB flashing through the auto-reset are unaffected. GPIO8 was already unconnected (floating) on the board until now, so radar mode is no change from D17. The silkscreen says "Remove shunt to flash" under the JP2 legend (added 2026-10-28 after Flux's review), since the normal USB flash may need download mode too (G2-T12 checks).
- **No external pull-up** (changed in D19: R29, 10 k, now pulls D8 up). A pull-up resistor next to J10 pin 2 was planned, but there is no room: VOUT's 0.3 mm track runs between J10 pins 2 and 3 on F.Cu, KA_DRV passes below on B.Cu, and C11 and the VOUT diagonal sit above. The firmware enables GPIO8's internal pull-up (about 45 k) instead. With nothing driving the pin and a short track, that is enough, and the firmware reads it five times at power-on and takes the majority.
- **Placement:** pin 1 at (114.54, 130.0), horizontal (rotated -90°, pin 1 on the right like JP1), between the JP1 legend and C11, outside the XIAO and radar keep-outs. Found by an exhaustive search for a spot clear of courtyards and copper on both layers.
- **Route:** J10 pad 2 → JP2 pad 2 on B.Cu, 0.25 mm, 11.1 mm, no vias (found with the grid router in `tools/router.py`). Closest other-net copper is a +3V3 via at 0.303 mm. JP2 pad 1 joins the GND pour.
- **Silkscreen:** "JP2 1-2 (right): manual" and "JP2 2-3 (left): radar" to the right of the header, and a "1" by pin 1. The C11 reference moved 0.35 mm to clear the legend.
- **Firmware:** `read_manual_mode()` at power-on (G2 build). Manual mode treats presence as always true: the string goes through the normal low-current start check and lights at the pot setting, never times out, and never sleeps waiting for the radar. The open/short/window guards and the 5 W cap still apply, and a fault still turns the string off and retries after 30 s. The radar stuck-HIGH watchdog is skipped. The mode is logged at boot. It is read once, so move the shunt with the switch off.
- **Runtime in manual mode** is continuous: about 29 h on a 20 Ah bank (43 h on 30 Ah) at 150 mA on one 12 V filament (`power_model.py`'s 416 mA). The bank's low-load shutoff matters more here: at a dim setting the lamp may draw less than the bank's threshold for hours, so the "keep-alive while lit" firmware item becomes important (Open items).

Result: ERC 0 errors (68 warnings, all the library-path artefact); netlist check passes (42 nets, 175 connections, 9 no-connects, 73 parts) and a mutation test with JP2 pins 1 and 2 swapped fails as it should; DRC with zones filled 0 errors, 0 unconnected, 70 warnings (J1 silkscreen at the edge, 2; library-path notices, 68); `verify_pcb.py` passes (184 pads, 68 footprints). Gerbers, drill files, position file, CPL (61 placements, JP2 flagged for a rotation check like JP1), BOM, assembly drawing, layout image and 3D render regenerated.

## D19. 90 × 60 mm relayout: horizontal-entry ports, R29, room for rework (2026-10-28)

Two problems with the 74 × 58 mm board: the Degson DG250 ports take the wires at 45°, which points them at the glass or at the back of the frame depending on which way the board is mounted (it is flipped to point the radar either way, D10); and parts sat close together (median gap between courtyards 0.3 mm, 47 parts with less than 0.5 mm), which makes hand rework hard. The long side may be up to 100 mm, so the board was laid out again at 90 × 60 mm.

- **Ports:** J5–J8 are now JILN JL212R-35003B01 (LCSC C2962951), 3-pole 3.5 mm push-in blocks with the wire entering parallel to the board. The release buttons are on the same face as the wire holes, so a port can be wired and released from the board edge whichever way the board faces. Body 11.2 × 12.3 × 8.5 mm, buttons 1.5 mm proud of the wire face; 0.2–1.5 mm² (28–14 AWG); two pins per pole, rows 7 mm apart. Degson DG212R-THR-3.5-03P (C7603454) has the same size and hole pattern (both follow Phoenix SPT 1,5/3-H-3,5), so it can replace it without a board change. Stock at JLCPCB on 2026-10-28: 238 JILN and 68 Degson, roughly 75 boards together.
- **Footprint and model:** `fgl.pretty/TerminalBlock_JILN_JL212R-3.5-03P_Horizontal`, drawn from the JILN and Degson drawings (1.2 mm holes, 2.0 mm pads). The 3D model is a simplified one built from the same drawings (`hardware/tools/make_port_step.py`): black body, white buttons, pins; no maker model was available. The ports sit along the top edge with the button fronts 0.3 mm inside it, 15 mm apart so a finger fits between them. The + / NEXT / END legends are behind each port.
- **R29:** a 10 k 0603 pull-up (C25804, basic part) from +3V3 to RADAR_MODE, directly above JP2 pin 2. The firmware still enables GPIO8's internal pull-up as well. With the shunt on 1-2, R29 draws 0.33 mA, while the lamp is lit anyway.
- **C16:** 0402 → 0603 (Yageo CC0603KRX7R9BB104, C14663, 100 nF 50 V X7R, the same part as C3), so no 0402 is left on the board.
- **Placement (`hardware/tools/layout_g2b/`):** the same arrangement as D15, spread out: ports along the top; USB-C, fuse, soft-start switch and keep-alive load on the right; the SEPIC in the middle with U2's small parts at about 1 mm from the chip; the XIAO bottom-left with its USB-C at the left edge; the radar bottom-right; pot and radar-cable connectors on the bottom edge; M3 holes in the four corners (3.5 mm in). Every part had at least 0.72 mm of clear space between its courtyard and the nearest one (median about 1 mm; courtyards already include 0.25 mm around the body). The switching-loop parts have since been pulled closer together (0.35–0.5 mm, see the Flux layout follow-up below). The VSENSE divider, pot filter and ISEL resistors stay under the plug-in XIAO and the radar's series resistors and filter under the radar module; unplug the module to reach them. TP5 (RADAR_OT2) is now outside the radar module.
- **Routing:** hand-routed power stage and input as in D15, with the port chain run under the port bodies between their two pin rows, and the LED_RTN bus behind the ports. FB is a separate 0.25 mm trace from R21's pad (Kelvin), routed before anything else and kept off the rest of LED_RTN. The remaining nets were maze-routed. The B.Cu keep-out under the switching loop is kept. Every via, routed or stitching, stays at least 0.25 mm from every SMD pad (the D17 rule, now enforced by the router with no exceptions). No vias under the JP1/JP2 legends. 154 vias, including 83 GND stitching vias and one placed to stop a B.Cu island by JP2.
- **Silkscreen:** "SWITCH OFF BEFORE WIRING PORTS" and the board name at the top left (moved to the top right on 2026-10-29, see the follow-up below); JP1 and JP2 legends next to the jumpers with a "1" by each pin 1. Every part has its reference on the silkscreen, in 0.8 mm text (0.15 mm stroke since the clarity pass) next to the part (see the follow-up below; the first D19 board left seven on the fab layer).

Result: ERC 0 errors (69 library-path warnings); netlist check passes (42 nets, 177 connections, 9 no-connects, 74 parts) and a mutation test with R29's pins swapped fails as it should; DRC with zones filled 0 errors, 0 unconnected, 71 warnings (J1 silkscreen at the edge, 2; library-path notices, 69); `verify_pcb.py` passes (186 pads, 69 footprints); the thermal-spoke check passes (at least two spokes on every pad that relies on them); firmware comment updated and compile-checked. Gerbers, drill files, position file, CPL (62 placements; JL212R ports flagged for a rotation check), BOM, assembly drawing, layout image and 3D renders regenerated.

**Follow-up, the same day: a silkscreen reference for every part.** The first D19 board had seven references on the fab layer only: C15 (under the XIAO) and JP2 (named by its legend) by choice, and C2, C4, R13, R15 and R16 by mistake. The layout script had found clear spots for those five but left them on the fab layer, where the 74 × 58 mm board had them; the D19 note above first said only C15 and JP2 were missing. All seven are now on the silkscreen, in the same 0.8 mm text as the rest, each beside its own part: JP2 to the left of its header, C15 below its pads (seen with the XIAO unplugged). The four mounting holes are the only footprints without a reference. 1.0 mm text for every reference was tried and rejected: it also passes DRC, but in the dense groups (around U2, the XIAO resistor row, the radar filter) labels end up nearer a neighbour than their own part, which is worse for rework than smaller text. Placement: `layout_g2b/refspots.py` (keeps clear of pads, silk text and silk lines) and `apply_refs.py` (copies the result into the board without re-serialising it); `emit.py` now moves a placed reference back to the silkscreen. Only the top silkscreen changed: DRC is the same (0 errors, 0 unconnected, 71 warnings, no silkscreen overlap or silkscreen-on-pad warnings), `verify_pcb.py` passes, every other gerber and drill file and the position file are identical apart from dates. The assembly drawing lost its duplicate C2 and C4 labels.

**Follow-up: datasheet links.** Flux's import flagged 17 parts as missing a datasheet: no placed part had its Datasheet field filled, and parts on generic KiCad symbols (diodes, fuse, headers, sockets, test points) got nothing from the symbol either. Every purchased part now has a link in the schematic and on the board (64 of 74; the six test points and four mounting holes are bare copper and have none), filled by `hardware/tools/set_datasheets.py` from each part's LCSC number. The links are PDFs, checked on 2026-10-28: LCSC's own copies on datasheet.lcsc.com, and TI's current copy for the TPS61500. `www.lcsc.com/datasheet/C<n>.pdf` was not used because it returns a viewer page, not the PDF. The XIAO links to Seeed's wiki page. U1's MPN field is now just `113991054`, with "order with pre-soldered headers" moved to its Note, and the loose shunt's MPN is `2.54` (BOOMELE's part number), so tools that look parts up by MPN find them. Connectivity, footprints and every fab file are unchanged: the netlist has the same nets and footprints, ERC 0 errors (69 library-path warnings), DRC the same 71 warnings, and the gerbers are identical apart from dates. Changed outputs: netlist, schematic PDF, `bom.csv` (the U1 and shunt rows) and page 2 of the assembly drawing.

**Follow-up: Flux schematic review.** Flux reviewed the schematic on 2026-10-28 ([`g2_flux_schematic_review.md`](g2_flux_schematic_review.md), with a resolution for each finding). What changed:
- **JP2 and flashing (Flux finding 1, correct and already known from D18).** The shunt on 1-2 holds GPIO8 low, and GPIO8 low with GPIO9 low is an invalid boot combination, so download mode may not start. No other XIAO pin was free and safe. Added: "Remove shunt to flash" on the silkscreen under the JP2 legend, the same instruction in the flashing step, and a G2-T12 step that tries a normal USB flash with the shunt on to see whether it is really needed.
- **Input protection (finding 2, correct).** The XIAO's regulator (XC6210) is rated 6.0 V operating and 6.5 V absolute maximum, and D1 (SMF6.0A) starts conducting at 6.67 V, so fitting D1 cannot protect it. In practice the board only asks for 5 V (no PD, D+/D- unconnected) and the soft start keeps Q2 off through a plug-in ring, so the XIAO is no worse off than on its own USB. G2-T6 now measures the XIAO's 5V pin (limit 6.0 V) in both plug orientations, and says the fix if it fails is an input over-voltage cut-off in G3, not D1.
- **Schematic readability (finding 3).** Section 2 (the SEPIC) is drawn with wires instead of a label on every pin: power path left to right along the top (+5V, C2/C3, L1, SW, C4, SEP_B with L2, D5, VOUT with C5/C6 and the OVP divider), U2 below with its control pins fanned out to R17/R18 and C7, C8, C9, R19. Each net keeps one label naming it, and labels only remain where a net leaves the section (DIM_PWM, VOUT, LED_RTN). The GND symbols at JP1 and JP2 no longer sit on the neighbouring signal wires, VBUS_IN's power flag is wired to F1 instead of carrying a second label, and the F1 and Q2 reference/value texts no longer overprint. Scripts: `hardware/tools/redraw_g2_sepic.py`, `tidy_g2_labels.py`. The netlist is identical (same nets, same names, same parts and fields); a geometric connectivity check of the drawing and `verify_netlist.py` both pass.
- **USB-C CC resistors switched through SW_N (finding 4).** Intentional (D16): with the switch off, Rd floats, the bank sees nothing attached and sleeps. The schematic note already says so. G2-T6 now covers both plug orientations.
- **C9 at 100 nF (power-stage notes).** Flux agreed it should not be changed to TI's boost-example value; G2-T3 measures the loop.
- Board: only the top silkscreen changed (the new line). DRC the same (0 errors, 0 unconnected, 71 warnings); every other gerber, the drill files and the position file are identical apart from dates.

**Follow-up: Flux layout and DFM review.** Flux reviewed the board on 2026-10-28 ([`g2_flux_pcb_review.md`](g2_flux_pcb_review.md), with a resolution for each finding). Most of its blockers came from the import, not the design: its BOM merged parts with different MPNs into one row (our `bom_jlcpcb.csv` has one row per LCSC part), and the "starved" U2 exposed pad is connected solidly to the pour on the board. Two points were real and were fixed:
- **Switching loop tightened.** The loop is U2's SW pins → C4 → D5 → C5 → GND → U2's PGND pins. C4 now sits under L1, straight below L1's SW pad; D5 stands vertically below C4's SEP_B end; C5 and C6 sit next to D5's cathode, with their GND pads over the solid B.Cu ground below U2. Measured through the pad centres, the loop encloses about 52 mm² instead of 74 mm², its perimeter is 35 mm instead of 41 mm, and C5's GND pad is 7.6 mm from U2's PGND pins instead of 10.5 mm. L2 moved 1 mm right to make room. New positions (mm from the board's top-left corner): C4 (50.4, 30.9) 0°, D5 (51.9, 36.3) 90°, C5 (47.4, 39.0) and C6 (47.4, 41.7) 180°, L2 (58.4, 36.0). The cost is less rework room inside the loop: courtyard gaps C4–U2 0.35 mm, C5–C6 0.37 mm, D5–L2 0.40 mm, L1–C4 0.50 mm, against 0.72 mm minimum elsewhere. C4 is a 1206, C5 a 1210, C6 an 0603 and D5 an SMA; each can still be reached with an iron from its free side.
- **J1 ground vias.** The two GND vias by J1's shield tabs were 0.12 mm from the shield pads (same net, so not a DRC error, but under JLCPCB's 0.2 mm minimum copper gap). The router now keeps vias 0.25 mm from through-hole pads as well as SMD pads; they are now 0.35 mm from the shield and 0.32 mm from J1's GND pins.
- Flux's other points are answered in the review's resolution table: the input caps (C2 belongs at L1's input, where a SEPIC draws its input current; C3 is 3 mm from VIN), FB (already a Kelvin trace from R21's pad), the 0.4 mm VBUS_F neck (Q2's gate network, not the power path), component stress (D3's table: switch node 33.5 V typical against 40 V), and the remaining DFM notes.

Result: DRC with zones filled 0 errors, 0 unconnected, the same 71 warnings; `verify_pcb.py` passes (186 pads, 69 footprints); the thermal-spoke check passes (the same pads as before, each with at least two spokes); netlist, schematic and BOM unchanged. All 66 connections routed, 152 vias (81 stitching). Copper, mask, paste, silkscreen and drill files, position file and CPL (C4, C5, C6, D5, L2 moved; D5 now at 90°, in the rotation-check list as before), assembly drawing, layout image and 3D renders regenerated.

**Follow-up: silkscreen clarity pass.** R19's reference sat to the left of C9, nearer C9 than R19. A check of every reference (`layout_g2b/labelcheck.py`: the gap from each label to its own part and to the nearest other part, plus size and stroke) and a look at the plotted silkscreen found a few more that were ambiguous or cramped, and that every text stroke on the top silkscreen was below JLCPCB's minimum. Changes (`layout_g2b/relabel.py`, `silk_tidy.py`):
- **C9, R19, R16, R15:** all four references now sit in one row directly below their own parts (C9's was above C9, R19's beside C9). R19's and R15's are set 0.4 mm outward so the three R labels don't run together.
- **XIAO resistor row (C15, R25, R24, R6, C12, R5, R23, R22):** at 2.4 mm pitch the horizontal references ran together ("R25R24"); each now stands vertically above its own part. They are under the plugged-in XIAO, as before.
- **JP2:** was squeezed against C10's pad; now vertical against the header's left end.
- **R13:** sat between Q2 and R13; now on R13's left, in line with C16 and R14 below it. **R12:** sat just under R14's pads; now below R12. **C3:** sat between R18 and U2's label; now above C3.
- **C4, C5, C7, R29:** moved in to their own parts (they were 0.7–1.1 mm away; C4's was nearer L2).
- **Pin legends:** "RX OT2" on J4 and "3V3 GND" on J3 ran together at 2.0/2.54 mm pitch; OT2, 3V3 and GND moved 0.16–0.3 mm apart, each still over its own pin.
- **Stroke:** JLCPCB's character specification is 0.8 mm minimum height with a 0.15 mm minimum stroke (1.0 mm and 0.2 mm recommended). The references and most legends were 0.8 mm with a 0.12 mm stroke; all 98 are now 0.15 mm. Text height stays 0.8 mm: 1.0 mm was tried earlier the same day and labels in the dense groups ended up nearer a neighbour. The footprints' own silkscreen outlines stay at KiCad's 0.12 mm.

Every reference is now at least as near its own part as any other, apart from five checked by eye: F1 and Q1 (centred above their parts, nothing nearer), J10 (beside its header), and R16/R15 (directly below their parts, with C5's own label beside C5). Only `F_Silkscreen.gto` changed among the fab files; DRC the same (0 errors, 0 unconnected, 71 warnings, no silkscreen overlap or silkscreen-on-pad warnings); `verify_pcb.py` passes; position file and CPL unchanged.

**Follow-up (2026-10-29): board name and warning moved to the top right.** At the top left they were squeezed between J5, TP3, TP4 and C11. The top-right corner, between J8 and the H2 mounting hole and above the USB input, held only tented stitching vias. The board name ("FUSED GLASS LIGHTING", 0.9 mm) and "rev G2 2026-10" now sit at the top of that corner, and "SWITCH OFF BEFORE / WIRING PORTS" below them, enlarged to 1.0 mm text with a 0.18 mm stroke so the warning stands out. The name stays 0.9 mm because it has to fit the 16 mm between J8 and the hole. Script: `layout_g2b/move_titles.py` (each spot checked clear of pads, other silkscreen and the edge). Only `F_Silkscreen.gto` changed; DRC the same (0 errors, 0 unconnected, 71 warnings); `verify_pcb.py` passes.

**Follow-up (2026-10-29): Flux's second layout review.** Given our answers to its questions, Flux added a power-envelope check and some questions of its own ([`g2_flux_pcb_review.md`](g2_flux_pcb_review.md), second-pass section, with resolutions). New and acted on: F1's hold current at 55 °C (now a 2 A part, D12), the supported string range stated explicitly (up to 24 V total, D2), the USB-C current the bank must supply for full power (D7), a closed-frame run in G2-T2 and a radar-through-the-glass test (G2-T14). Flux reviewed its import from before 2026-10-28, so its J1 via, loop and silkscreen findings were already fixed; its other repeats are answered in the first-pass table.

**Follow-up (2026-10-30): off-board parts.** Sources for the pot, knob, filaments, XIAO, radar, USB-C panel extension and power bank are in [`g2_sourcing.md`](g2_sourcing.md). Two changes came out of it: U1's MPN is now **102010633** (XIAO ESP32C3 pre-soldered; 113991054 is the bare board), and the pot is now a Same Sky PTN09S1-H100115K1B with a push-on Cliff K21 knob, so the knob can sit in a recess with no set screw to reach. New test G2-T15 qualifies the power bank in the closed frame.

**Follow-up (2026-10-29): JLCPCB placement corrections.** JLCPCB's placement preview of the first order showed twelve parts in the wrong place or orientation. Cause: JLCPCB places each part with its own (EasyEDA) footprint, whose origin is the centre of the pads; KiCad's origin is pin 1 for pin headers, sockets, JST connectors and our JL212R ports, and off-centre for the HRO USB-C, and the position file reports KiCad's origin. The rotation table in `make_cpl.py` also had wrong or missing entries, taken from a community table for KiCad's generic footprints and never checked against JLCPCB's actual parts. `make_cpl.py` now puts every part at the centre of its pads (computed from the board) and keys rotations by LCSC part, each marked verified or fixed against the preview:
- moved to the pad centre: J1 (−1.46 mm), J2 (3.0), J3 (5.08), J4 (4.0), J5–J8 (3.5, 3.5), J9 and J10 (7.62), JP1 and JP2 (2.54);
- rotation fixed: J5–J8 and J4 +180°; JP1 and JP2 +270° (they showed across their pin row); J1 0° (was 180°, its pins showed at the mouth); Q1 and Q2 SOT-23 +180° (was −90°; the preview showed both bodies 90° off, which the first check missed);
- confirmed unchanged: U2 (pin 1 dot at the SW end), D4 and D5 (cathode bands), J2, J3, J9, J10 orientations.
The fixed entries must be confirmed in the preview of the corrected files before paying (checklist in `hardware.md`).


**Follow-up (2026-10-29): cost and stock.** Of the ten extended SMD parts (about $3 each per order in JLCPCB's Economic loading fees), only C4 had a functionally equivalent basic part: Samsung CL31A106KBHNNNE (C13585), the X5R version of the same 10 µF 50 V 1206; C4 sits at VIN, so X5R's 85 °C rating is enough. SS210 (C14996, basic) for D5 and the 50 V 100 nF (C14663) for C6 were considered and not taken: the first costs efficiency on every board for a one-off $3, the second gives up the 2× margin over the worst-case OVP (D16, audit M2). The other seven (U2, L1/L2, J1, F1, R20/R21, R12) have no basic equivalent, even allowing a layout change: no basic LED driver or SEPIC controller with OVP and analog dimming, no basic power inductor near 3 A saturation, no basic USB-C receptacle or PTC fuse in JLCPCB's current basic list, no basic 0.82 Ω sense resistor (another value would change the 244/488 mA ceilings), and replacing R12 with parallel basic resistors would save $3 for a layout change and less pulse margin. Ports: JLCPCB was 12 JL212R short of the 20 needed, so J5–J8 are ordered as the DEGSON DG212R-THR-3.5-03P-13-1000A(H) (C7603454), the same-size alternative chosen with the footprint in D19. Its JLCPCB rotation has not been seen in a preview (`make_cpl.py` assumes it is drawn like the JL212R).


## XIAO pins (G2)

| XIAO | GPIO | Net | Use |
|---|---|---|---|
| D0 | 2 | NC | Strapping pin |
| D1 | 3 | ADC_POT | Pot wiper, ADC1_CH3 |
| D2 | 4 | VSENSE | VOUT / 13, ADC1_CH4 |
| D3 | 5 | RADAR_OT2 | Wake, high = present (through R28, R7 pull-down) |
| D4 | 6 | UART_TX | To radar RX through R26, 115200 8N1 |
| D5 | 7 | UART_RX | From radar OT1/TX through R27 |
| D6 | 21 | ISEL_IO | Low = 244 mA (JP1 shunt on 2–3), high = 488 mA (shunt on 1–2, or none); through R22 (1 k) because GPIO21 is UART0 TX and toggles at boot. R23 100 k pull-up |
| D7 | 20 | DIM_PWM | LEDC 19.53 kHz → EN. UART0 RX has a ~45 k pull-up at reset; R18 (2.2 k) holds EN below 0.4 V until the firmware drives it |
| D8 | 8 | RADAR_MODE | JP2: low = manual (shunt on 1-2), high = radar (2-3 or none). R29 10 k pull-up (D19), internal pull-up too. Strapping pin: move the shunt off 1-2 before forcing download mode (D18) |
| D9 | 9 | NC | Strapping pin (BOOT button) |
| D10 | 10 | KA_DRV | Keep-alive gate |

## Power and runtime (`power_model.py`)

These are model estimates (SEPIC at a flat 84 %), for a 20 Ah bank at 4 h/day:

| Configuration | LED power | Bank current | 20 Ah | 30 Ah |
|---|---|---|---|---|
| G1 as drawn: 2 × 3 V at 303 mA | 1.70 W | 411 mA | 7.3 d | 10.9 d |
| **G2: one 12 V 600 mm at 150 mA** (prototype brightness) | 1.64 W | 416 mA | **7.2 d** | **10.8 d** |
| G2: one 12 V 600 mm at 244 mA | 2.73 W | 684 mA | 4.5 d | 6.7 d |
| G2: 2 × 3 V 300 mm at 244 mA | 1.37 W | 351 mA | 8.5 d | 12.7 d |
| G2: 4 × 3 V 300 mm at 150 mA | 1.63 W | 415 mA | 7.2 d | 10.8 d |
| G2: 5 W cap (488 mA setting) | 5.00 W | 1.25 A | 2.5 d | 3.7 d |

Idle (switch on, dark) is 4.05 mA with keep-alive and 0.72 mA without. Switched off, it is 0.

## Cost

Parts fitted by JLCPCB come to about $4.0 per board at quantity 10, using LCSC prices from 2026-10-23. The Degson price is estimated from TME's 2-pole price. This excludes the PCB, assembly fees, the XIAO and the radar.

Compared with G1:

- **Parts:** about +$1.65 per board. The SEPIC, ports, jumper and voltage sense add about $1.25; the sockets, radar socket and power switch add about $0.40.
- **Per order:** extended-part fees of about $3 per unique extended part, and a small through-hole soldering charge for J2–J10.

Filaments probably save more than the board adds. A DFRobot 12 V 600 mm costs $5.90, against $9.00 for two Adafruit 3 V 300 mm, with half the solder joints.

## BOM sourcing (checked 2026-10-23; new parts 2026-10-24)

| Ref | Part | LCSC | Stock (LCSC unless noted) |
|---|---|---|---|
| U2 | TPS61500PWPR | C71160 | 7,087 |
| L1, L2 | Sunlord SWPA8040S100MT | C37429 | 8,790 at JLCPCB |
| D5 | LGE SS36 | C2903825 | 11,640 |
| C4 | Samsung CL31A106KBHNNNE (10 µF 50 V X5R 1206, JLCPCB basic; CL31B106KBHNNNE C89632 X7R before 2026-10-29) | C13585 | JLCPCB basic |
| C5 | Murata GRM32EC72A106KE05L (10 µF 100 V X7S 1210) | C576517 | 35,535 (2026-10-24) |
| C6 | Samsung CL10B104KC8NNNC (100 nF 100 V X7R 0603) | C15725 | 363,300 (2026-10-24) |
| C16 | Yageo CC0603KRX7R9BB104 (100 nF 50 V X7R 0603; 0402 before D19) | C14663 | JLCPCB basic, 41 M (2026-10-28) |
| R29 | 0603WAF1002T5E (10 k) | C25804 | JLCPCB basic, 38 M (2026-10-28) |
| F1 | Brightking SMD1812B200TF/16 (2 A hold, D12; SMD1812B150TF/8 C269137 before 2026-10-29) | C269145 | recheck at order |
| Q2 | AOS AO3401A | C15127 | 133,930 |
| R20, R21 | UNI-ROYAL 1206W4F820LT5E (0.82 Ω 1 %) | C30568 | 77,150 |
| R15 | 0603WAF1103T5E (110 k 1 %) | C25805 | 92,000 (2026-10-24) |
| R24 | 0603WAF1203T5E (120 k) | C25808 | 755,000 |
| R18 | 0603WAF2201T5E (2.2 k 1 %) | C4190 | as G1 |
| JP1, JP2 | BOOMELE 2.54-1*3P pin header | C49257 | 166,660 (2026-10-24) |
| JP1, JP2 shunts (2) | BOOMELE 2.54 mm shunt, open top (loose, not placed) | C5305 | 735,500 (2026-10-24) |
| R19 | 0603WAF8202T5E (82 k) | C23254 | 960,900 |
| FB1 | Sunlord GZ1608D601TF | C1002 | JLCPCB basic |
| J2 | JST S4B-PH-K-S | C157926 | 36,250 |
| J3 | Hong Cheng HC-PM254-5.0H-1x5PZ | C27985230 | 6,417 |
| J4 | JST S5B-PH-K-S | C157923 | 59,840 |
| J5–J8 | DEGSON DG212R-THR-3.5-03P-13-1000A(H) (horizontal push-in, same size and holes as the JILN JL212R-35003B01 C2962951, which JLCPCB was 12 short of on 2026-10-29) | C7603454 | 68 at JLCPCB on 2026-10-28; recheck (20 needed for 5 boards) |
| J9, J10 | Hong Cheng HC-PM254-5.0H-1x7PZ | C27985232 | 15,048 |

Unchanged from G1: USB-C C165948, AO3400A C20917, SS14 C2480, 33 Ω 2512 C53728, and the 0603/0805 passives.

The full list is `hardware/kicad/fgl_g2/bom.csv`. Parts that are not on the assembled board (pot, knob, filaments, XIAO, radar, cables, power bank): [`g2_sourcing.md`](g2_sourcing.md).

## Verification so far

- **Netlist check:** `verify_netlist.py` against `g2_expected.py` passes for both the KiCad 7 and the KiCad 9.0.7 netlist exports: 41 nets, 170 connections, 9 no-connects, footprint pads and BOM fields.
- **Mutation test:** a netlist with two filament-port pins swapped fails with the expected four errors.
- **G1 and Rev F:** both still pass with the updated tools.
- **KiCad 9.0.7 "Update PCB from Schematic":** every footprint resolved (U1 skipped as intended).
- **Schematic saved in KiCad 9:** symbols updated from the library. ERC: 0 errors, 0 warnings.
- **Layout DRC (KiCad 9.0.7, zones filled):** 0 errors, 0 unconnected pads. The remaining warnings are of two kinds:
  - J1's silkscreen is clipped by the board edge. This is expected, because the receptacle overhangs the edge.
  - "Footprint library not found" for every part. This comes from the scripting session's library paths; the GUI resolves them. Report: `fgl_g2/DRC.rpt`.
- **After the 3D-model and outline update (2026-10-24):** DRC is unchanged (0 errors, 0 unconnected, the same 68 warnings), `verify_pcb.py` still passes, and the gerbers were regenerated. Only the top silkscreen changed; copper, mask, paste, edge and drill files are identical apart from their dates. A 3D view render is in `fgl_g2/fgl_g2_3d.png`.
- **PCB against intent:** `verify_pcb.py` checks every pad's net on the board against `g2_expected.py` and passes: 179 pads, 66 footprints. A board with one pad's net changed fails it.
- **After the audit fixes (2026-10-25, D16):**
  - netlist: `verify_netlist.py` passes, 41 nets, 172 connections, 9 no-connects, 72 parts. A mutation test (JP1 pins 1 and 3 swapped) fails as it should;
  - ERC (KiCad 9.0.7 CLI): 0 errors. All 67 warnings are "footprint not found in library": that CLI resolves stock footprint libraries from the wrong path on this Mac. The footprints are checked by DRC (0 footprint errors) and by `verify_netlist.py` against KiCad's library files;
  - DRC with zones filled: 0 errors, 0 unconnected pads. 69 warnings: 2 for J1's silkscreen and 67 library-path notices;
  - PCB against intent: `verify_pcb.py` passes, 181 pads, 67 footprints;
  - firmware: no PlatformIO build was possible in the session that made these changes (its registry was unreachable), so `src/main.c` was compiled without linking against the ESP-IDF v5.5.0 headers, with `-Wall -Wextra -Werror`, for Rev F, G2, and G2 with a fixed window: all clean. A misspelled API call fails as it should. **Build and flash with PlatformIO before trusting it.**
- **After the layout DFM pass (2026-10-26, D17):** DRC with zones filled 0 errors, 0 unconnected, the same 69 warnings; `verify_pcb.py` passes (181 pads, 67 footprints); no via is closer than 0.25 mm to an SMD pad except the three listed in D17; J3/J4 pin 2 have at least two spokes on each layer. Gerbers regenerated; the CPL and position file are unchanged.
- **After adding JP2 (2026-10-27, D18):** ERC 0 errors (68 library-path warnings); netlist 42 nets, 175 connections, 9 no-connects, 73 parts, and a JP2 pin-swap mutation fails; DRC with zones filled 0 errors, 0 unconnected, 70 warnings; `verify_pcb.py` passes (184 pads, 68 footprints); firmware compile-checked with `-Werror` for Rev F, G2 and G2 with a fixed window.
- **After the 90 × 60 mm relayout (2026-10-28, D19):** ERC 0 errors (69 library-path warnings); netlist 42 nets, 177 connections, 9 no-connects, 74 parts, and an R29 pin-swap mutation fails; DRC with zones filled 0 errors, 0 unconnected, 71 warnings; `verify_pcb.py` passes (186 pads, 69 footprints); no via within 0.25 mm of an SMD pad; the thermal-spoke check passes; firmware compile-checked with `-Werror` for Rev F, G2 and G2 with a fixed window.
- **After adding the missing silkscreen references (2026-10-28, D19 follow-up):** DRC with zones filled 0 errors, 0 unconnected, the same 71 warnings; `verify_pcb.py` passes (186 pads, 69 footprints); only `F_Silkscreen.gto` differs from the previous gerbers (other files identical apart from dates); position file identical.
- **After adding datasheet links (2026-10-28, D19 follow-up):** netlist identical in nets and footprints; `verify_netlist.py` passes (42 nets, 177 connections, 9 no-connects, 74 parts); ERC 0 errors; DRC the same 71 warnings; `verify_pcb.py` passes; gerbers unchanged.
- **After Flux's schematic review (2026-10-28, D19 follow-up):** schematic redrawn in section 2 and labels tidied; KiCad's netlist identical to the previous one; `verify_netlist.py` passes (42 nets, 177 connections, 9 no-connects, 74 parts); ERC 0 errors (69 library-path warnings); one silkscreen line added; DRC the same 71 warnings; only `F_Silkscreen.gto` changed among the gerbers.
- **After Flux's layout review (2026-10-28, D19 follow-up):** switching loop tightened and J1's GND vias moved; DRC with zones filled 0 errors, 0 unconnected, 71 warnings; `verify_pcb.py` passes (186 pads, 69 footprints); thermal-spoke check passes; J1's GND vias 0.35 mm from the shield pads (were 0.12 mm); netlist and BOM unchanged.
- **After the silkscreen clarity pass (2026-10-28, D19 follow-up):** 20 references and 3 pin legends moved, all top-silkscreen text strokes 0.15 mm; `labelcheck.py` reviewed; DRC 0 errors, 0 unconnected, the same 71 warnings; `verify_pcb.py` passes; only `F_Silkscreen.gto` changed.
- **After moving the board name and warning (2026-10-29, D19 follow-up):** DRC 0 errors, 0 unconnected, 71 warnings; `verify_pcb.py` passes; only `F_Silkscreen.gto` changed.
- **After the fuse change and placement corrections (2026-10-29):** netlist differs only in F1's value, LCSC, MPN and datasheet; `verify_netlist.py` passes (42 nets, 177 connections, 9 no-connects, 74 parts); ERC 0 errors (69 library-path warnings); `verify_pcb.py` passes; gerbers unchanged; CPL rows moved or rotated for J1–J10, JP1, JP2, Q1 and Q2 only.
- **Fab outputs:** in `fgl_g2/jlcpcb/`:
  - gerbers and drill files (zip);
  - BOM (62 placements);
  - CPL with JLCPCB rotation corrections (`make_cpl.py`);
  - the raw KiCad position file.

## Open items before ordering G2

1. ~~Save the schematic in KiCad 9~~ (done: ERC clean, netlist re-verified).
2. ~~**Degson footprint**~~ (checked against Degson's STEP; outline fixed, pads unchanged; D6, D15). Still worth a look with the first real part.
3. ~~Layout~~ (done, D15).
   - ~~**Check the 3D view in KiCad**~~ (makers' models added, D15). The header pin length against the 5 mm sockets still needs checking with real parts.
   - **Check JLCPCB's placement preview** for every part `make_cpl.py` lists. HTSSOP U2, the sockets, the JST-PH connectors, the Degson ports, the SMA diodes and the inductors have unconfirmed rotations.
4. **Fuse stock** (D12; the 2 A part, C269145, since 2026-10-29).
5. **Firmware.** Done on 2026-10-25 (`-DFGL_BOARD_G2`, D16):
   - ~~pin moves: DIM_PWM to D7, VSENSE on D2, ISEL on D6~~;
   - ~~analog-dimming curve (I = duty × I_max, no 0.3 V offset)~~;
   - ~~5 W power cap from VSENSE~~;
   - ~~start check at low current, open/short/window guards~~;
   - ~~pot clamp, RX pull-up, task watchdog (D14)~~.

   Still to do:
   - **Build and flash with PlatformIO.** It is compile-checked only (see Verification).
   - Saved maximum current and keep-alive setting with a setup mode (the maximum is a build flag for now).
   - Error blink codes (faults are logged over USB only).
   - Keep-alive pulses while lit below the bank threshold (design review F1). More important with JP2 in manual mode, where a dim lamp can run below the threshold for hours (D18).
   - Skip the 10 s wake when keep-alive is off.
   - Radar configuration over UART (F4).
6. **CPL rotations:** the first preview (2026-10-29) found twelve parts wrong; `make_cpl.py` was corrected (D19 follow-up). Check the corrected preview against the checklist in `hardware.md` before paying.
7. **Port stock and fit (D19):** on 2026-10-29 JLCPCB was 12 JL212R short of the 20 needed for five boards, so J5–J8 are ordered as DEGSON DG212R (C7603454; 68 on 2026-10-28); check stock and its rotation in the preview. Order a few loose parts first to check the footprint and the push-in action with the 22 AWG filament pigtails.

## Bring-up tests (G2)

| Test | What | Pass |
|---|---|---|
| G2-T1 | One 3 V filament at 244 mA, VIN 4.5–5.25 V | Stable current (TP3 = 0.2 V ± 3 %), no audible noise, switch node clean |
| G2-T2 | 24 V string (two 12 V) at the 5 W cap, VIN 4.5 V; then the same for 1 h inside the closed frame (glass front, back on), logging the bank's input current and the temperatures of F1, Q2, D5, U2 and L1 (thermocouple or IR camera through the open back at the end) | Open bench: stable; U2 and L1 below 85 °C; peak switch current (current probe on L1 + L2) below 2.5 A. In the frame: no fuse trip or cycling; input current below 1.45 A; F1 below 70 °C (its hold falls to 1.45 A at 70 °C); U2, L1, D5 below 100 °C. If F1 runs close, lower the firmware power cap (D12) |
| G2-T3 | Loop response: step the PWM duty 20 % ↔ 80 % at both extremes | No ringing above 10 %; change C9 if needed |
| G2-T4 | Open string (remove END wire), lit and at start | VOUT clamps at ~27.7 V; firmware logs an open fault and turns EN off; scope SW with a short ground spring: peaks below 38 V |
| G2-T5 | Filament surface temperature, closed frame, 1 h at the chosen current | ≤ 50–55 °C; inside of the frame ≤ 55 °C (DFRobot ambient limit) |
| G2-T6 | Power switch with the target bank (C-to-C) and with a USB-A-to-C cable, each with the plug both ways round. Hot-plug: with a live USB-A charger or bank on a USB-A-to-C cable, scope the XIAO's 5V pin (J10 pin 7, ground at TP2, short ground spring, single-shot trigger at 5.5 V) while plugging the cable into J1: ten times with the switch on and ten with it off, half of them with the plug flipped. Probe +5V (TP1) and VBUS_F (Q2's source) too, for reference | Switch off = 0 mA and switch on = bank wakes without a button press (C-to-C), in both plug orientations; +5V rises over ~0.5 ms with no bank trip (C16 soft start). Hot-plug: the XIAO's 5V pin never above 6.0 V (its XC6210 regulator: 6.0 V operating, 6.5 V absolute maximum). D1 is not the fix if it fails: an SMF6.0A only starts conducting at 6.67 V, so it can't hold 6.0 V. Use C-to-C only and add an input over-voltage cut-off in G3. VBUS_F may ring higher: only F1, Q2 (30 V), R13 and C16 see it |
| G2-T7 | Idle current, switch on, dark, keep-alive on and off | ~4.0 mA and ~0.7 mA (charge LED item X1 may add to both) |
| G2-T8 | JP1 shunt on 2–3, on 1–2, and removed | 244 / 488 / 244 mA ± 4 % at full duty (TP3); D6 reads low / high / high |
| G2-T9 | EN at reset: hold the XIAO in reset, then in download mode (BOOT held) | EN (R18) below 0.4 V and no light in both, with a bank connected |
| G2-T10 | Firmware guards: start with END removed; one 3 V filament fitted backwards (expendable filament); learned window, then add a filament without relearning; then relearn | Open and window faults logged with EN off and a 30 s retry; no light from the reversed filament; after the relearn gesture the new string lights |
| G2-T11 | Radar next to L2: radar plugged into J3, presence idle (nobody in range), driver at the 5 W cap and then off; repeat with the radar on the J4 cable | No extra presence events with the driver running compared with it off. If there are, use the J4 cable for that piece (and note it for G3) |
| G2-T12 | JP2: shunt on 1-2, on 2-3, and removed, with and without the radar fitted; then hold BOOT with the shunt on 2-3 and plug in USB; then, with the shunt on 1-2, flash the firmware over the XIAO's USB without touching BOOT (`pio run -t upload`) | 1-2: logs MANUAL, lights at power-on through the start check, follows the pot, stays lit with nobody in range past the 25 s off-delay, and a removed END wire still faults and retries. 2-3 and none: logs RADAR and behaves as before. Download mode entered with the shunt off 1-2. USB flash with the shunt on 1-2: record whether it works. If it fails, "remove the JP2 shunt before flashing" (already on the silkscreen and in the flashing step) is required, not only advisable |
| G2-T14 | Radar through the actual glass: the board in the frame behind the finished piece (and behind any dichroic or iridized areas, whose metal-oxide coatings can block 24 GHz), radar on J3; walk toward and across the front at 1, 2 and 4 m; repeat with the sensor on the J4 cable at the frame edge | Presence detected at the range the piece needs, through the glass. If a coated area blocks it, mount the sensor on the J4 cable where it looks through plain glass or past the piece |
| G2-T15 | The chosen power bank (one unit before buying ten), with the board in the closed frame: (a) switch on with the pot, both plug orientations; (b) idle at 0 % for 2 h and at the lowest dim setting for 2 h with keep-alive on; (c) plug a USB-C charger into the frame inlet while the lamp is lit, then unplug; (d) 2 h at the 5 W cap, logging the bank's surface temperature (thermocouple taped to the case) and the frame air | (a) wakes without a button press; (b) never switches off; (c) no reset or flicker longer than the firmware tolerates, and the bank charges; (d) bank surface below 40 °C. If (d) fails, vent the back or move the bank; if (c) fails, document "switch off before charging" ([`g2_sourcing.md`](g2_sourcing.md#using-a-bank-inside-a-frame-safety)) |
| G2-T13 | Ports (D19): a 22 AWG stranded pigtail in each port, with and without pressing the button; pull test; release from the board edge with the board mounted both ways round | Wires hold under a firm pull; each releases with its button from the edge; nothing on the board blocks the buttons or the wire path |

TP5 (RADAR_OT2) is outside the radar module since D19; on the 74 × 58 mm board it sat under it (D17).

## Sources

- [TI SLVA904, TPS61500 SEPIC Configuration](https://www.ti.com/lit/an/slva904/slva904.pdf)
- [TI TPS61500 datasheet](https://www.ti.com/lit/gpn/tps61500)
- [DFRobot FIT0926 12 V 600 mm spec sheet (DigiKey)](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/6240/DFROBOT%20FIT0926.pdf)
- [DFRobot 24 V 1.2 m filament](https://www.dfrobot.com/product-2680.html)
- [Adafruit nOOds 3 V 300 mm](https://www.adafruit.com/product/5503)
- [Adafruit nOOds 12 V 600 mm](https://www.adafruit.com/product/5731)
- [Zionsville Lighting flexible filaments](https://www.zionsvillelighting.com/flexible-led-filament/)
- [Kitronik 300 mm 3 V](https://kitronik.co.uk/products/flexible-led-noodle-filaments-300mm-3v)
- [Degson DG250-3.5 product page and drawing](https://www.degson.com/content/details_552_879717.html)
- [Seeed OPL_Kicad_Library (XIAO-ESP32-C3-DIP)](https://github.com/Seeed-Studio/OPL_Kicad_Library)
- [Degson DG250-3.5 03P product page (STEP, DXF, PDF)](https://www.degson.com/content/details_552_879713.html)
- [Hi-Link LD2410S product page](https://www.hlktech.net/index.php?id=1176) and [download folder (3D model, manual)](https://drive.google.com/drive/folders/1wC8KC-DaNavNbpeVouZ1HdiBzZ9YrAcg)
- [LCSC HC-PM254-5.0H-1x5PZ (5 mm insulator height)](https://www.lcsc.com/product-detail/C27985230.html)
- [Seeed XIAO ESP32C3 3D model on GrabCAD](https://grabcad.com/library/seeed-studio-xiao-esp32-c3-1)
