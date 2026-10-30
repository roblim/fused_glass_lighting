# Rev G1 Netlist, Power and BOM Audit

Date: 2026-10-22. Reviewer: Claude. Scope: `hardware/kicad/fgl_g1/` at repo commit `2b4ee9f` (the Oct 22 layout commit), checked as an independent second pass on top of [`design_review.md`](design_review.md).

## Verdict

**I found no wiring errors.** I checked every pin of every IC against its datasheet, and checked the PCB pad by pad against the schematic netlist. The UART is not crossed. There are no differential pairs and no floating enable inputs on any IC. Every capacitor is rated at 5× or more of its rail.

The findings below are tolerance, robustness and documentation issues. **M1 needs a firmware change before the pot calibration is written.** The other findings are optional, or belong in the next revision.

## Method

| Check | How | Result |
|---|---|---|
| Schematic ↔ PCB parity | Parsed `fgl_g1.net` and every pad in `fgl_g1.kicad_pcb`, then compared each ref.pin → net pair | **0 mismatches.** No extra nets, and no-connects are respected |
| IC pinouts | AL8860 (Diodes datasheet), ESP32-C3 datasheet v2.4 Table 2-1, HLK-LD2410S protocol V1.00, AO3400A, the KiCad SOT-23, TSOT-23-5 and D_SMA pad conventions, and the XIAO edge-pad order | Pass. Details below |
| XIAO footprint | Read `fgl.pretty/XIAO_ESP32C3_Castellated.kicad_mod`. Pads 1–7 run down the left side and 8–14 up the right, with pad 14 (5V) at top right next to the USB-C edge | Pass |
| BOM | `bom.csv`, `bom_jlcpcb.csv` and the JLCPCB copies. Checked LCSC ↔ MPN on lcsc.com for C25337, C53728, C125330 and C15850. Footprints compared against the netlist | Pass. One cosmetic item (B1) |
| CPL rotations | `make_cpl.py` compared with matthewlai/JLCKicadTools `cpl_rotations_db.csv` | Matches: SOT-23 −90, TSOT-23 180, HRO USB-C 180 |
| DRC | `DRC.rpt`: 79 warnings, all silkscreen and library-path, with 0 unconnected | Agreed. That run had no schematic-parity section, so the parity check above stands in for it |

## 1. Pin-to-pin accuracy

| Interface | Netlist | Datasheet | Status |
|---|---|---|---|
| AL8860 U2/U3 (TSOT-25) | 1 SW → L/D anode, 2 GND, 3 CTRL → DIM_CTRL, 4 SET → R3/R4 low side and LED+, 5 VIN → +5V | 1 SW, 2 GND, 3 CTRL, 4 SET, 5 VIN | ✓ |
| Buck topology | VIN → Rs → SET → LED+ … LED− → L → SW. Schottky anode on SW, cathode on VIN | Standard AL8860 high-side-sense buck | ✓ |
| UART | XIAO D4/GPIO6 (TX) → J3.4 radar RX. J3.3 radar OT1/TX → XIAO D5/GPIO7 (RX) | LD2410S: pin 3 = UART_TX, pin 4 = UART_RX | ✓ Not swapped. The firmware has no UART code yet, so configure UART1 with TX = GPIO6 and RX = GPIO7 |
| LD2410S J3 | 1 3V3, 2 GND, 3 OT1/TX, 4 RX, 5 OT2 | Same, supply 3.0–3.6 V | ✓ 1:1 with the module. The cable must also be straight-through |
| Radar wake | OT2 → GPIO5, with R7 100 k to GND | OT2 high = present | ✓ |
| Pot | 3V3 → R5 47 k → J2.1, wiper J2.2 → R6 1 k → GPIO3 (ADC1_CH3), C6 100 n. J2.3 GND | Wiper max 2.245 V, inside the C3's 12 dB range | ✓ but see M1 and L1 |
| Keep-alive Q1 | G ← R10 100 Ω ← GPIO10, R11 100 k G–S. S = GND, D → R12 → +5V | AO3400A SOT-23: 1 G, 2 S, 3 D | ✓ |
| Diodes | D2/D3 K → +5V, A → SW. D4 A → +5V, K → XIAO 5V. D1 K → +5V, A → GND | D_SMA / SOD-123F pad 1 = K | ✓ |
| USB-C J1 | CC1 (A5) and CC2 (B5) each with their own 5.1 k to GND. VBUS A4/A9/B4/B9 → F1. GND A1/A12/B1/B12 and shield → GND. D±/SBU NC | A separate Rd per CC pin is required | ✓ |

**Reset and enable pins:**

- **AL8860 CTRL** is the only enable input on the board, and R9 holds it low. The ESP32-C3 datasheet lists GPIO4 (MTMS) at reset as "IE" only, with no internal pull. So during reset and flashing nothing fights R9.
- **Q1's gate** is held by R11.
- **The XIAO's EN** has its own RC and button on the module, and the underside EN pad is deliberately left off the footprint.

**Strapping pins:** GPIO2, 8 and 9 are left NC, which keeps the XIAO's own defaults. Rev F already runs the same way.

**Differential pairs:** none on the board. J1's D± is NC, and USB data goes through the XIAO's own port.

## 2. Power delivery

**Rails:**

```
VBUS_IN ─F1─ +5V ─┬─ U2 VIN  (C2 10µ + C4 100n)
                  ├─ U3 VIN  (C3 10µ + C5 100n)
                  ├─ C1 10µ bulk, D1 TVS (DNP), R12/Q1 keep-alive
                  └─ D4 ─ XIAO_5V ─ [XIAO LDO] ─ +3V3 ─┬─ J3 radar (C8 10µ + C9 100n)
                                                        └─ R5 → pot
```

**Decoupling per IC:**

| IC | Supply pin | Local decoupling | Note |
|---|---|---|---|
| U2 AL8860 | VIN | C2 10 µF + C4 100 nF. C4 is about 2.8 mm from U2 | ✓ See L5 |
| U3 AL8860 | VIN | C3 10 µF + C5 100 nF | ✓ See L5 |
| U1 XIAO | 5V, 3V3 | Decoupled on the module. Nothing extra is needed on XIAO_5V | ✓ |
| LD2410S (off-board) | 3V3 | C8 10 µF + C9 100 nF at J3 | ✓ |

**Voltage ratings, against the 2× rule:**

| Part | Rated | Rail | Ratio |
|---|---|---|---|
| C1/C2/C3 (CL21A106KAYNNNE, X5R) | 25 V | 5 V | 5× ✓ |
| C8 (same part) | 25 V | 3.3 V | 7.6× ✓ |
| C4/C5/C9 (CC0603KRX7R9BB104, X7R) | 50 V | 5 V / 3.3 V | ≥ 10× ✓ |
| C6 (same part) | 50 V | ≤ 2.25 V | ✓ |
| C7 (CL10A105KB8NNNC, X5R) | 50 V | ≤ 2.7 V | ✓ |
| F1 1206L075 | 8 V (LCSC table) | 5 V | ✓ |

## 3. Passive verification

| Item | Value | Calculation | Status |
|---|---|---|---|
| Sense R3/R4 | 0.33 Ω 1% 1206 ¼ W | 0.100 V / 0.33 Ω = 303 mA. 30 mW against 250 mW | ✓ |
| Inductor L1/L2 | 47 µH | t_on 2.9 µs, t_off 1.7 µs, f ≈ 216 kHz, duty 0.63. Peak ≈ 0.36 A | ✓ Recomputed and agrees with the review |
| CC Rd R1/R2 | 5.1 k 1% | USB-C Rd = 5.1 kΩ ±10% | ✓ |
| Dimming RC R8/R9/C7 | 2.2 k / 10 k / 1 µF | Full scale 3.3 × 10/12.2 = 2.705 V (> 2.5 V clamp). τ = 1.8 k × 1 µF = 1.8 ms. Ripple at 19.5 kHz ≈ 19 mV p-p | ✓ See I1 |
| Pot divider R5 + pot | 47 k + 100 k | 3.3 × 100/147 = 2.245 V nominal, 22 µA | ✓ See M1 |
| Pot filter R6/C6 | 1 k / 100 nF | Fine for a knob | ✓ |
| OT2 pull-down R7 | 100 k | 33 µA while present | ✓ |
| Q1 gate R10/R11 | 100 Ω / 100 k | 3.3 V gate against the 2.5 V Rds(on) spec | ✓ |
| Keep-alive R12 | 33 Ω 1 W 2512 | 152 mA, 0.76 W peak (0.83 W at 5.25 V), 15 mW average | ✓ See L4 |
| LED current-limit resistors | — | None needed. The filaments are current-regulated, and the XIAO's LEDs are on the module | — |

**Termination resistors:** none are missing. The UART runs at 115200 baud over a short cable, so its edges are far slower than any cable delay and termination does nothing. There are no USB data lines or high-speed nets. The USB-C CC lines are terminated by R1/R2. The only resistors I'd add on signal lines are series resistors for ESD (L3), not termination.

## 4. BOM consistency

- All 46 schematic symbols have footprints. Placed parts carry an MPN and LCSC number, except U1, which is hand-fitted. H1–H4 and TP1–TP5 are correctly excluded from the BOM.
- `bom_jlcpcb.csv` has 18 lines and 31 placements, and matches the CPL's 31 rows. D1 is correctly absent (DNP).
- The footprints match the parts:
  - S*B-PH-K is the side-entry part, matching the `_Horizontal` footprints.
  - AL8860**WT** is TSOT-25.
  - SS14 (MDD) is SMA.
  - SWPA6045S has the exact library footprint.
- The board has no crystal. The only feedback network is R3/R4, and both have values.
- **B1 (cosmetic):** the Value field for C4–C7 and C9 doesn't show voltage or dielectric, and the Value field for R6, R7, R10 and R11 doesn't show tolerance. The MPNs do carry this information, and every resistor in the BOM is 1%. Adding it to the Value field would make the BOM self-checking at a glance.

## 5. Findings

| # | Severity | Finding | Action |
|---|---|---|---|
| **M1** | **Medium** | **The planned pot full-scale clamp (2.13 V) is above the wiper's maximum for ordinary pot tolerance.** Wiper max = 3V3 × Rp / (Rp + 47 k). With a pot 10% low and 3V3 at 3.234 V it is 2.117 V. At −20% it is 2.03 V, and at −30% it is 1.93 V. Those units never reach 100% brightness. Typical trimmers and kit pots are ±20–30%. | Put full scale at **≈ 1.85 V** in the F5 firmware (covers a −30% pot, 3V3 at −2% and the L2 pull-down). The resolution cost is negligible at 12 bits. Alternatively, specify a ±10% pot *and* keep the clamp at ≤ 2.08 V |
| L1 | Low | **J2's pin order is the reverse of normal pot numbering.** J2 is 1 = CW end, 2 = wiper, 3 = CCW end (GND). On most pots, terminal 1 is CCW and terminal 3 is CW. A straight 1:1 cable makes the knob work backwards. It's harmless, but it will happen on some units. | Say "J2.1 → pot terminal 3" in the cable drawing. Or swap the silkscreen and schematic labels so the cable can be 1:1 (J2.1 = GND end) next revision |
| L2 | Low | **Two inputs float with their off-board cable unplugged.** ADC_POT floats with J2 unplugged (random brightness). UART_RX floats with J3 unplugged (noise frames). OT2 is already covered by R7. | A 1 MΩ pull-down from POT_W to GND makes an unplugged pot read 0. It costs about 3% at full scale, which the 1.85 V clamp in M1 absorbs. Enable the RX pull-up in firmware |
| L3 | Low | **Cable-exposed GPIOs have no series resistance.** J3.3/J3.5 go straight to GPIO7/GPIO5, and GPIO6 goes straight to J3.4. The pot wiper does have R6. | Next revision: 220 Ω–1 kΩ series on all three J3 signal lines. At 115200 baud this has no timing cost |
| L4 | Low | **The keep-alive is a 0.8 W heater with only firmware between it and "always on".** A hang with GPIO10 high puts 0.76–0.83 W continuously into R12 inside the frame, and draws 152 mA from the bank. A panic is fine: it resets the chip, and R11 turns Q1 off. | Make sure F7 (task watchdog) lands. For a hardware fail-safe, AC-couple the gate: a 10 µF series capacitor with R11 gives τ ≈ 1 s, so a stuck-high pin turns Q1 off within about a second, and a 200 ms pulse still reaches > 2.5 V |
| L5 | Low | **The input caps are a little under the AL8860's recommendation.** The datasheet asks for "10 µF or higher X7R" close to VIN. The 0805 X5R 10 µF/25 V gives roughly 5–7 µF at 5 V because of DC bias. Input ripple is still only tens of mV at 0.3 A, so this doesn't matter in practice. | Optional: 22 µF 0805/1206 X5R in the same footprint at the next BOM revision |
| L6 | Low (optional) | **The filament leads carry the full inductor ripple.** That is ≈ 120 mA p-p at ~216 kHz, along 30 cm filaments plus cable. It's an antenna for switching harmonics. Regulation is unaffected, because Rs is in series with the inductor. | Next revision: a DNP footprint for ~1 µF/10 V across J4/J5 pins 1–2, so the ripple stays on the board. It doesn't affect regulation or open-LED behaviour |
| I1 | Info | **CTRL off-state margin depends on an unpublished value.** The AL8860 datasheet gives no CTRL pull-up value; it says only that CTRL "floating" means enabled. The off threshold is 0.2 V (typical, falling) and the on threshold 0.25 V (rising). With both CTRL pins tied, R9 holds the node at 0.23 V if each internal pull-up is 200 kΩ to 2.5 V, at 0.08 V if 600 kΩ, and at 0.03 V if 1.5 MΩ. The 1.5 ms/nF soft-start figure points to the high end, so it's probably fine, but it's unproven. | T7 is the real check. If TP3 reads > 0.15 V with the XIAO in reset, change to R8 = 1.0 k and R9 = 4.7 k: full scale 2.72 V, τ 0.82 ms, ripple ~40 mV, and the firmware mapping constant goes from 2.705 to 2.721 |
| I2 | Info | **Hot-plug of a USB-A source.** USB-C sources only switch VBUS on after they see Rd, so only USB-A-to-C cables hot-plug a live rail. My rough estimate for a 1 m cable: ~1 µH, ~18 µF of effective ceramic, ~0.3 Ω loop including F1. That gives ζ ≈ 0.6, so overshoot is only a few percent. T9 with D1 DNP is a reasonable plan. | Run T9 specifically with a USB-A bank and an A-to-C cable |
| I3 | Info | **The firmware isn't G1-ready yet.** It still uses Rev F naming and the 1 kHz CE PWM, and has no UART code. On G1 the existing 1 kHz output would ripple ~0.4 V through the RC, and its low duty settings fall below the 0.2 V off threshold. | Already tracked as F2/F4. Don't flash Rev F firmware onto G1 except as a smoke test |

## Sources

- [AL8860 datasheet (Diodes, SparkFun mirror)](https://cdn.sparkfun.com/assets/3/f/5/8/b/AL8860.pdf): TSOT-25 pinout, VEN(ON) 0.25 V / VEN(OFF) 0.2 V, CTRL −0.3 to +6 V, ISHDN 50/80 µA, "10 µF or higher X7R", 1.5 ms/nF soft-start
- [ESP32-C3 datasheet v2.4](https://documentation.espressif.com/esp32-c3_datasheet_en.pdf): Table 2-1 reset states (GPIO4 "IE", GPIO9 and GPIO20 "IE, WPU"), Table 2-2 power-up glitches, RPU/RPD 45 kΩ
- [HLK-LD2410S serial protocol V1.00](https://www.tinytronics.nl/product_files/006002_HLK-LD2410S%20serial%20communication%20protocol-V1.00.pdf): pin table, 3.0–3.6 V, 115200 8N1
- [matthewlai/JLCKicadTools cpl_rotations_db.csv](https://raw.githubusercontent.com/matthewlai/JLCKicadTools/master/jlc_kicad_tools/cpl_rotations_db.csv)
- LCSC: [C25337](https://www.lcsc.com/product-detail/C25337.html), [C53728](https://www.lcsc.com/product-detail/C53728.html), [C125330](https://www.lcsc.com/product-detail/C125330.html) (11,390 in stock on Oct 22), [C15850](https://www.lcsc.com/product-detail/C15850.html), [C99563](https://www.lcsc.com/product-detail/C99563.html)
