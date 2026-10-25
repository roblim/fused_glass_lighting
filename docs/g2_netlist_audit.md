# Rev G2 Netlist, Power and BOM Audit

Date: 2026-10-24. Reviewer: Claude. Scope: `hardware/kicad/fgl_g2/` at commit `99dcb6d` on branch `rev-g2` (PR #1): schematic, netlist, PCB, BOMs and the JLCPCB files. This is an independent second pass on [`g2_decisions.md`](g2_decisions.md). The G1 audit it follows is [`g1_netlist_audit.md`](g1_netlist_audit.md).

## Verdict

**The wiring matches intent and the datasheets.** The PCB agrees pad for pad with the schematic. The SEPIC is connected the way TI's SLVA904 describes. The UART is not crossed. The XIAO sockets are in the right order and not mirrored.

**One design-intent error needs a BOM change before ordering (H1).** The XIAO pin chosen for DIM_PWM has an internal pull-up at reset, so the driver turns on at its full current ceiling on every boot and during USB flashing. The fix is one resistor value, with no layout change.

Two ordering checks follow from the CPL (M1). One capacitor pair fails the 2× voltage rule on the output (M2). The other items are margins, firmware behaviour and BOM tidying.

## Method

| Check | How | Result |
|---|---|---|
| Schematic ↔ PCB parity | Parsed `fgl_g2.net` (XML) and every pad in `fgl_g2.kicad_pcb`, then compared each ref.pin → net pair | **0 mismatches**, no extra nets, no-connects respected. U1 is excluded from the board, as intended |
| IC pinouts | TPS61500 datasheet (PWP pin table, electrical characteristics), ESP32-C3 datasheet v2.4 Table 2-1, HLK-LD2410S protocol V1.00, AO3400A/AO3401A, and the KiCad SOT-23 and D_SMA pad conventions | Pass, except H1 |
| Socket geometry | Pad coordinates of J9/J10 transformed to board coordinates and compared with the XIAO DIP pin order | Pass. Details in §1 |
| BOM | `bom.csv` and both JLCPCB BOM copies (identical). LCSC pages checked on Oct 24 for C2903825, C269137, C89632, and JLCPCB for C7588159 | Pass, with the tidying in §4 |
| CPL rotations | `make_cpl.py` compared with matthewlai/JLCKicadTools `cpl_rotations_db.csv` | Two differences (M1) |
| Existing checks | `ERC.rpt` (0/0), `DRC.rpt` (68 warnings: 66 library-path, 2 J1 silkscreen; 0 unconnected), `verification.txt` (netlist and PCB verifiers pass) | Agreed |

## 1. Pin-to-pin accuracy

| Interface | Netlist | Datasheet / intent | Status |
|---|---|---|---|
| TPS61500 U2 (HTSSOP-14) | 1, 2 SW; 3 VIN = +5V; 4 EN = DRV_EN; 5 SS; 6 DIMC; 7 AGND; 8 COMP; 9 FB = LED_RTN; 10 FREQ; 11 OVP; 12–14 PGND; 15 EP = GND | Same. "Solder the thermal pad to the analog ground" | ✓ |
| SEPIC power path | +5V → L1 → SW. C4 between SW and SEP_B. L2 from SEP_B to GND. D5 anode on SEP_B, cathode on VOUT. C5/C6 on VOUT | SLVA904 SEPIC | ✓ |
| Current sense | VOUT → J5 + … string … END → LED_RTN → FB and R20 to GND. R21 from LED_RTN to JP1.1 | 0.2 V FB | ✓ |
| String chain | J5.2 → J6.1, J6.2 → J7.1, J7.2 → J8.1. J8.2 and all four pin 3s (END) are on LED_RTN | D6 | ✓ |
| Radar UART | GPIO6 (TX) → R26 → J3.4/J4.4 (radar RX). J3.3/J4.3 (radar TX) → R27 → GPIO7 (RX) | LD2410S pin 3 = TX, pin 4 = RX | ✓ Not swapped |
| Radar header | J3 and J4: 1 3V3 (through FB1), 2 GND, 3 OT1/TX, 4 RX, 5 OT2 → R28 → GPIO5, with R7 on the XIAO side | Hi-Link pin table | ✓ |
| XIAO sockets | J9.k = XIAO pin k (pin 1 NC), J10.k = XIAO pin 7 + k (J10.2, J10.3 NC). On the board, XIAO pin 1 is at (105.88, 153.62) and pin 14 (5V) directly across at (105.88, 138.38); pins 7 and 8 face each other at x = 121.12 | DIP order with the USB at the pin 1/14 end, towards the left edge. Not mirrored | ✓ |
| Pot J2 | 1 GND (CCW + switch common), 2 wiper → R6 → GPIO3, 3 CW ← R5 47 k ← 3V3, 4 SW_N | Fixes G1 L1: a 1:1 cable gives clockwise = brighter | ✓ |
| Power switch | Q2 AO3401A: 1 G ← R14 ← SW_N, 2 S = VBUS_F, 3 D = +5V, R13 G–S. CC1/CC2 each have their own 5.1 k to SW_N | High-side P-FET, body diode blocks VBUS when off | ✓ (see below) |
| Keep-alive | Q1 AO3400A as in G1 | | ✓ |
| Diodes | D4: A on +5V, K on XIAO_5V. D5: A on SEP_B, K on VOUT. D1: K on VBUS_F, A on GND (DNP) | Pad 1 = K | ✓ |
| ISEL | GPIO21 → R22 1 k → ISEL, with R23 100 k to 3V3 and JP1.3 | GPIO21 toggles at boot; R22 limits it into a bridged JP1 | ✓ |
| VSENSE | VOUT → R24 120 k → GPIO4 (ADC1_CH4), R25 10 k and C15 to GND | VOUT / 13 | ✓ |

**USB-C attach through the pot switch (D8).** With the switch open, each CC pin sees 5.1 k + 101 k (R14 + R13) to VBUS_F rather than to ground. I worked this through for every source pull-up level:

- **Default Rp (56 k to 5 V):** the CC pin sits at about 3.3 V.
- **1.5 A Rp (22 k):** about 4.1 V.
- **3 A Rp (10 k):** about 4.6 V.

Each is above that level's open threshold (1.6 V, 1.6 V and 2.6 V), so the source sees no sink, as intended. With the switch closed, Rd goes to ground and Q2's gate is pulled to −5 V Vgs, which is inside the AO3401A's ±12 V. Zero draw when off is confirmed: with a USB-A cable, every node sits at VBUS, so no current flows.

**Enables and resets:**

- **TPS61500 EN:** has a pull-down, but see H1.
- **Q1's gate:** held by R11.
- **Q2's gate:** held by R13.
- **The XIAO's EN:** on the module.

**Strapping pins:** GPIO2, 8 and 9 are NC, as in G1.

**Differential pairs:** none. J1's D± are NC.

## 2. Power delivery

```
VBUS_IN ─F1─ VBUS_F ─Q2─ +5V ─┬─ L1 ─ SW ─C4─ SEP_B ─D5─ VOUT ─ ports ─ LED_RTN ─ R20 (‖R21) ─ GND
                              │                └─L2─ GND        (C5 10µ + C6 100n)
                              ├─ U2 VIN (C3 100n, 2.8 mm away); bulk C1, C2 10 µF
                              ├─ R12/Q1 keep-alive
                              └─ D4 ─ XIAO 5V ─ [XIAO LDO] ─ +3V3 (C10 10µ + C11 100n) ─┬─ FB1 ─ RADAR_3V3 (C13 10µ + C14 100n)
                                                                                         └─ R5 → pot
```

**Decoupling per IC:**

| IC | Pin | Local decoupling | Status |
|---|---|---|---|
| U2 TPS61500 | VIN | C3 100 nF about 2.8 mm from pin 3; C1/C2 10 µF at L1's input. The input current is continuous through L1, so the VIN pin carries only the IC's own supply | ✓ |
| U2 | VOUT side | C5 10 µF + C6 100 nF next to D5's cathode | ✓ but see M2 |
| U1 XIAO | 3V3 | C10 + C11 at the socket, plus the module's own caps | ✓ |
| LD2410S | 3V3 | FB1 with C13 + C14 at J3/J4 | ✓ |

**Voltage ratings, against the 2× rule:**

| Part | Rated | Worst-case voltage | Ratio |
|---|---|---|---|
| C1, C2, C10, C13 (10 µF 25 V X5R) | 25 V | 5.5 V / 3.3 V | ≥ 4.5× ✓ |
| C3, C11, C12, C14, C15, C8, C9 (100 nF 50 V) | 50 V | ≤ 5.5 V | ✓ |
| C4 coupling (10 µF 50 V X7R 1206) | 50 V | ≈ VIN, 5.5 V across the capacitor | 9× ✓ |
| C7 DIMC (1 µF 50 V) | 50 V | ≤ 0.2 V | ✓ |
| **C5 output (10 µF 50 V X7R 1206)** | 50 V | **30.2 V at OVP (up to 31.7 V worst case)** | **1.6× ✗ (M2)** |
| **C6 output (100 nF 50 V)** | 50 V | same | **1.6× ✗ (M2)** |
| D5 SS36 | 60 V | VIN + VOUT ≈ 37.7 V | 1.6×, acceptable for a Schottky |
| U2 SW (absolute max) | 40 V | 37.7 V worst case at OVP | **6% margin (M3)** |
| Q1, Q2 | 30 V | 5.5 V | ✓ |
| F1 SMD1812B150TF/8 | 8 V | 5.5 V | ✓ |

## 3. Passive verification

| Item | Value | Calculation | Status |
|---|---|---|---|
| Sense R20 (‖ R21) | 0.82 Ω 1% 1206 | 0.200 V / 0.82 Ω = 244 mA; in parallel 488 mA; 49 mW each, against 250 mW. FB ±2.5% + Rs 1% → ±3.5% | ✓ |
| OVP R15/R16 | 120 k / 5.1 k | 1.229 V × 24.53 = 30.15 V typ; 31.05 V with the OVP threshold at its 1.266 V max; 31.7 V with the resistors at their 1% limits too | ✓ but see M3 |
| FREQ R19 | 82 k | Datasheet: 80 k → 1.2 MHz, so ≈ 1.17 MHz | ✓ |
| Max duty | — | 28 V string at VIN 4.5 V: D ≈ 0.864 ideal, ≈ 0.87 with losses, against the 89% minimum Dmax | ✓ Tight (I1) |
| Switch current | — | 2.18 A worst-case peak (design doc) against the 3.0 A minimum limit | ✓ |
| Soft start C8 | 100 nF | 100 nF × 1.8 V / 6 µA = 30 ms | ✓ |
| DIMC C7 | 1 µF | Datasheet: > 0.1 µF selects analog dimming, internal 25 kΩ, so τ = 25 ms. 19.5 kHz is inside the 200 Hz–40 kHz analog range | ✓ |
| COMP C9 | 100 nF | Between SLVA904's 15 nF and the datasheet's boost example of 470 nF. Bench-tune at G2-T3 | ✓ |
| **EN divider R17/R18** | 1 k / 100 k | With GPIO20's ~45 kΩ reset pull-up: EN ≈ 2.2 V, above the 1.2 V VIH | **✗ H1** |
| VSENSE R24/R25/C15 | 120 k / 10 k / 100 nF | 30.15 V → 2.32 V; 31.5 V → 2.42 V, inside the 12 dB ADC range. τ 0.9 ms | ✓ |
| Q2 gate R14/R13 | 1 k / 100 k | Vgs −4.95 V on, 0 V off | ✓ See L2 |
| ISEL R22/R23 | 1 k / 100 k | 3.3 mA worst case from GPIO21 into a bridged JP1 | ✓ |
| Radar series R26–R28 | 1 k | ≈ 5 ns RC at 115200 baud; OT2 into R7 gives a 100/101 divider | ✓ Fixes G1 L3 |
| FB1 | 600 Ω at 100 MHz | Radar current is well under the part's rating | ✓ |
| Pot R5/R6/C12 | 47 k / 1 k / 100 nF | As G1. The G1 M1 clamp (≈ 1.85 V full scale) still applies in firmware | ✓ (firmware) |
| Keep-alive R10/R11/R12 | as G1 | | ✓ (G1 L4 still applies) |

**Termination resistors:** none are missing, for the same reasons as G1. The UART is slow, there are no high-speed nets, and the CC lines carry their Rd. R26–R28 are the series resistors G1 lacked.

## 4. BOM consistency

- All 66 board footprints have a BOM line, an MPN and an LCSC number. The exceptions are the solder jumper JP1, the mounting holes and the test points, which correctly have none.
- `bom_jlcpcb.csv` and `jlcpcb/fgl_g2-bom-jlcpcb.csv` are identical: 58 placements, matching the CPL's 58 rows. D1 is correctly absent (DNP).
- **Footprints match the parts:**
  - LGE SS36 (C2903825) is SMA (DO-214AC), 60 V 3 A. That matches D_SMA. Many SS36s are SMC, so this was worth confirming.
  - TPS61500**PWP**R is HTSSOP-14.
  - F1 is 1812.
  - J2 and J4 are side-entry S*B-PH-K parts on `_Horizontal` footprints.
- No crystal. The feedback networks (R15/R16, R19, R20/R21) all have values.
- **B1:** `bom.csv` lists **U1 twice** (two rows of quantity 1, with slightly different text). It doesn't affect the JLCPCB order, but a purchaser would buy two XIAOs. Remove one row in `make_bom.py`.
- **B2:** JP1's Value says "500mA", and the silkscreen says "JP1 open: 250mA" and "bridge all 3: 500mA". The design values are 244 and 488 mA. The rounding is harmless, but the firmware and docs use 244/488. Use the exact figures on the next silkscreen pass.
- **B3:** as in G1, the 100 nF and 1 µF Value fields don't show voltage or dielectric.
- **Stock on Oct 24:**
  - F1 (C269137) still shows **110** at LCSC. That covers 10 boards with no spare. Any 1812, 1.5 A hold, ≥ 6 V PTC substitutes.
  - JLCPCB's page for the Degson ports (C7588159) confirms an extended through-hole part but shows no stock figure. Check it in the order flow.

## 5. Findings

| # | Severity | Finding | Action |
|---|---|---|---|
| **H1** | **High** | **The driver turns on at full ceiling current during every boot, reset and USB flash.** DIM_PWM is on GPIO20 (D7, U0RXD). The ESP32-C3 datasheet (Table 2-1) gives that pin "IE, WPU" at reset: input with the ~45 kΩ internal pull-up on. Through R17 (1 k) against R18 (100 k) ‖ the TPS61500's internal 800 k pull-down, EN sits at **≈ 2.0–2.5 V**, above the 1.2 V VIH. The ROM keeps UART0 RX pulled up in download mode, and nothing reconfigures the pin until the firmware sets up LEDC. So after the 30 ms soft start, the string runs at 100% of the JP1 ceiling (244 or 488 mA): a flash at every switch-on, and continuous light for the whole of a USB flashing session. This is the Rev F P2 problem again, and it bypasses the firmware's per-piece maximum (for example 150 mA). `g2_decisions.md` (XIAO pin table, D3) says "UART0 RX is an input at boot, so EN stays low"; the datasheet contradicts that. | **Change R18 from 100 k to 2.2 k** (same 0603 footprint; the 0603WAF2201T5E, LCSC C4190, used in G1). EN at reset then stays ≤ 0.22 V even with a 30 k pull-up, below the 0.4 V VIL, while the driven-high level is 2.27 V (above 1.2 V) at 1 mA. Moving DIM_PWM instead doesn't work: the only free pins with no reset pull are strapping pins. Correct the D3 note and the pin table. Add a bring-up check: EN below 0.4 V with the XIAO held in reset and in download mode |
| **M1** | **Medium** | **The CPL departs from the rotation table it cites.** `make_cpl.py` applies no correction to `JST_PH_S*` footprints, but `cpl_rotations_db.csv` has `"^JST_PH_S",180`. J2 and J4 are fitted by JLCPCB for the first time in G2 (in G1 they were hand-soldered). A single row of holes accepts a 180° error, which would leave the connector with its mouth facing into the board and pin 1 swapped. Separately, the 270° PinSocket correction in `make_cpl.py` isn't in that table. A 180° error there is harmless, because an unkeyed socket is symmetric, and a 90° error can't be inserted. | In JLCPCB's placement preview, confirm J2's and J4's openings face the bottom edge, and rotate them if not. Then update `make_cpl.py` with whatever the preview shows, and correct its docstring about the PinSocket source |
| **M2** | Medium | **The output capacitors fail the 2× rule.** C5 (10 µF 50 V X7R 1206) and C6 (100 nF 50 V) sit on VOUT, which reaches 30–31.7 V at OVP: 1.6×. At 28–30 V the 1206 10 µF keeps roughly a third of its capacitance from DC bias, so it acts like a ~3 µF capacitor. Ripple still works out to about 40 mV at 1.17 MHz, so it functions. But the effective output C feeds the loop compensation that G2-T3 tunes. | Use ≥ 63 V parts: for example 10 µF 100 V X7R 1210 (or two 4.7 µF 100 V 1206) for C5, and 100 nF 100 V 0603 for C6. Swapping C5 to 1210 needs a footprint change; if the layout is frozen, keep 50 V for the first build and note it |
| **M3** | Medium | **The switch-voltage margin at OVP is thin.** In a SEPIC the switch sees VIN + VOUT + Vd. With OVP at its datasheet maximum (1.266 V), 1% resistors, 5.5 V USB and the diode: **37.7 V against the 40 V absolute maximum** (30.15 V + 5.0 V + 0.5 V = 35.7 V typical), before any ringing at the SW node. An open string is a routine event with push-in terminals, so the board will regularly sit there. | Scope SW at G2-T4 (open string) with a short ground spring. If peaks exceed ~38 V, change R15 to 110 k: OVP becomes 27.7 V typ, 29.1 V max, and the SW worst case 35.1 V, at the cost of about 2 V of the longest string (≈ 26 V instead of 28 V) |
| **M4** | Medium (firmware and instructions) | **Two wiring mistakes can hurt a filament.** (a) With an open string, VOUT sits at the ~30 V OVP level with C5 charged. Pushing a filament into a port at that moment dumps C5's energy into it at many times its rated current. (b) A filament fitted backwards blocks, so VOUT climbs toward 30 V reversed across it. LED reverse ratings are typically only ~5 V and don't cover reverse current. A reversed 3 V filament (parallel LEDs) may break down and then carry the full setpoint in reverse. | Firmware: when VSENSE shows an open string, drop EN (VOUT bleeds off through R24/R25 in a few seconds) and retry periodically at low current. Start every power-up at about 10% duty and check VSENSE against the saved per-piece voltage window before ramping. Instructions and silkscreen: wire ports only with the switch off |
| L1 | Low | **ISEL can be bridged wrongly.** Bridging only JP1 pads 1–2 gives 488 mA while the firmware believes 244 mA, which doubles every firmware current setting (already noted in D4). Bridging only 2–3 is the safe direction (less current than the firmware assumes). | Keep the silkscreen. Optionally replace JP1 with two 0 Ω 0603 positions next revision, so a half-bridge isn't possible |
| L2 | Low | **Q2 switches on hard into the +5V capacitance.** R14 (1 k) and the gate charge give a sub-µs turn-on into ~20 µF of +5V capacitance. Compliant USB-C banks don't care, but some USB-A banks trip on large inrush. | Optional: 1 µF from Q2 gate to source (across R13) gives a ~1 ms ramp. Check during G2-T6 |
| L3 | Low | **The G1 items carried into G2 still stand.** Pot full-scale ≈ 1.85 V (G1 M1), the RX pull-up in firmware (G1 L2), and the keep-alive fail-safe watchdog (G1 L4) | Firmware, as listed in `g2_decisions.md` D14 |
| I1 | Info | **Maximum duty is close to the limit at the longest string.** The longest string at the lowest input runs at D ≈ 0.87 against the 89% minimum Dmax. If the bank sags further, current drops below the setpoint (dimmer, not unsafe) | G2-T2 already covers it |
| I2 | Info | **EN is back-fed with the XIAO on its own USB.** With the XIAO powered from its own USB and VIN off, DIM_PWM high reaches EN through R17. R17 limits any current into U2's ESD structure to a couple of mA | No action |

## Sources

- [TI TPS61500 datasheet](https://www.ti.com/lit/gpn/tps61500): PWP pinout, EN VIH 1.2 V / VIL 0.4 V, Ren 400–1600 kΩ, 10 ms EN shutdown delay, VREF 195–205 mV, VOVP 1.192–1.266 V, ILIM 3 A min, Dmax 89% min, SW 40 V absolute max, DIMC > 0.1 µF with 25 kΩ internal, analog dimming 200 Hz–40 kHz, 80 k → 1.2 MHz, SS 6 µA to 1.8 V
- [TI SLVA904, TPS61500 SEPIC Configuration](https://www.ti.com/lit/an/slva904/slva904.pdf)
- [ESP32-C3 datasheet v2.4](https://documentation.espressif.com/esp32-c3_datasheet_en.pdf): Table 2-1 (GPIO20/U0RXD "IE, WPU" at reset; GPIO4, GPIO10 "IE"; GPIO21 "WPU", output enabled), RPU 45 kΩ typical
- [HLK-LD2410S serial protocol V1.00](https://www.tinytronics.nl/product_files/006002_HLK-LD2410S%20serial%20communication%20protocol-V1.00.pdf)
- [matthewlai/JLCKicadTools cpl_rotations_db.csv](https://raw.githubusercontent.com/matthewlai/JLCKicadTools/master/jlc_kicad_tools/cpl_rotations_db.csv): `^JST_PH_S` 180, `^HTSSOP-` 270, no PinSocket entry
- LCSC / JLCPCB, checked 2026-10-24: [C2903825 SS36](https://www.lcsc.com/product-detail/C2903825.html), [C269137 PTC](https://www.lcsc.com/product-detail/C269137.html), [C89632 10 µF 50 V](https://www.lcsc.com/product-detail/C89632.html), [C7588159 Degson](https://jlcpcb.com/partdetail/C7588159)
