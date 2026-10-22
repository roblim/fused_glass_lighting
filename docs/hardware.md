# Fused Glass Lighting: Hardware

Motion-activated backlighting for a fused-glass artwork:

- A Seeed XIAO ESP32C3 drives two 30 cm, 3 V LED filaments at about 300 mA each.
- A 24 GHz HLK-LD2410S radar turns the light on when someone is present and off 25 s after they leave.
- A potentiometer sets brightness.
- A 20,000–30,000 mAh USB power bank inside the frame powers everything. It is charged through a USB-C panel inlet on the frame (B08HS6X44P).

This is the canonical hardware document. The reasoning behind every current decision is in [`design_review.md`](design_review.md). Firmware is [`../src/main.c`](../src/main.c).

## Status (2026-10-22)

| Revision | What | State |
|---|---|---|
| Rev F | Hand-wired prototype on one full-size ElectroCookie board, LD1500SB linear driver modules | **Built and working.** Firmware flashed, presence detection and dimming confirmed. Open safety items P1 and P3 in the review |
| Rev G1 | Single PCB, AL8860 buck drivers, 5 V USB-C input | **Layout done (Oct 22), ready to order.** Schematic Oct 15 (ERC clean, netlist verified). PCB laid out on 66 × 44 mm, 2 layers; KiCad 9.0.7 DRC 0 errors, 0 unconnected. JLCPCB gerbers, BOM and CPL in `hardware/kicad/fgl_g1/jlcpcb/`. Firmware needs the G1 changes (review §2) |

## Files

| Path | Contents |
|---|---|
| `hardware/kicad/fgl_g1/` | G1 KiCad 9 project: schematic (the master), PCB (laid out, zones filled), PDF, `ERC.rpt`, `DRC.rpt`, `bom.csv`, `bom_jlcpcb.csv`, netlist, `verification.txt`, project symbols (`fgl.kicad_sym`) and the XIAO footprint (`fgl.pretty`) |
| `hardware/kicad/fgl_g1/jlcpcb/` | JLCPCB order files: `fgl_g1-gerbers-jlcpcb.zip`, `fgl_g1-bom-jlcpcb.csv`, `fgl_g1-cpl-jlcpcb.csv` (with rotation corrections), the raw KiCad position file and `make_cpl.py` |
| `hardware/tools/layout_g1/` | The scripts that produced the G1 placement and routing (kept for reference; the `.kicad_pcb` is now the master) |
| `hardware/kicad/fgl_rev_f/` | Rev F as-built schematic and PDF. These replace the Perplexity PNG drawings |
| `hardware/tools/` | Schematic generators, the netlist verifier, the BOM script and the power model. See [`../hardware/README.md`](../hardware/README.md) |
| `docs/design_review.md` | The design review (Oct 15) |
| `docs/archive/hardware_rev_f.md` | The Oct 6 Rev F build and bring-up document, with corrections at the top |
| `docs/archive/main_previous_iteration.c.txt` | Firmware from before Rev F |

## Requirements (fixed)

1. **Exactly two filaments.** Four were rejected for battery life.
2. **Bright.** The filaments backlight glass. 300 mA each, about 126 lm total.
3. **Maximum runtime** from a USB power bank.
4. **XIAO ESP32C3**, PlatformIO with ESP-IDF.
5. **Interchangeable bank.** The end user may fit any 20,000–30,000 mAh bank. Design target: B0DQPD24ZD (20,000 mAh, built-in cables, offers 9 V PD; G1 doesn't use it).
6. **Off-delay 25 s.**

300 mA comes from a convection model (Rev B, not measured). It puts the junction near 60 °C, against the 85 °C condition for about 30,000 h life. Dimming doesn't stretch the battery: total light per charge is flat within 7% between 100 and 300 mA.

## Rev G1 (PCB)

Schematic: [`fgl_g1.pdf`](../hardware/kicad/fgl_g1/fgl_g1.pdf).

```
Bank ── J1 USB-C (5.1 k Rd on CC1, CC2) ── F1 PTC 0.75 A ──┬── U2 AL8860 ── filament 1 (J4)
                                                            ├── U3 AL8860 ── filament 2 (J5)
                                                            ├── Q1 + R12 keep-alive (152 mA pulses)
                                                            └── D4 ── XIAO 5V ── XIAO 3V3 ── radar, pot
```

- **Power:**
  - 5 V only, no PD negotiation, so any USB-C or USB-A bank works.
  - The F1 PTC protects against a pinched filament lead.
  - D1 (TVS) is on the board but not fitted.
- **Drivers:**
  - Each filament has its own AL8860 hysteretic buck.
  - 0.33 Ω sense gives 0.1 V / 0.33 Ω = 303 mA, with 47 µH (L1/L2) and SS14 catch diodes (D2/D3).
  - Modelled at 88% efficient at 5 V, about 216 kHz.
- **Filament leads are not ground-referenced** (high-side sense). Neither lead may touch the frame.
- **Brightness:**
  - D2 → R8 2.2 k → DIM_CTRL, with R9 10 k and C7 1 µF to GND.
  - The firmware runs 19.5 kHz PWM, which the RC turns into a DC level, so the light is flicker-free.
  - CTRL 0.3–2.5 V gives 0–100%.
  - R9 holds the filaments off whenever D2 isn't driving: reset, flashing, a panic, or sleep.
  - Fallback: leave C7 off and use PWM at ≤ 500 Hz.
- **Keep-alive:** AO3400A with 33 Ω 1 W. It can be left off for banks proven to stay on.
- **XIAO:**
  - Fed through D4 (SS14).
  - Hand-soldered on its 14 edge pads.
  - The underside pads (VBAT, EN, JTAG) are left off the footprint; keep copper out from under it.

### Pins

| XIAO | GPIO | G1 net | Rev F net | Notes |
|---|---|---|---|---|
| D1 | 3 | ADC_POT | ADC_POT | ADC1_CH3 |
| D2 | 4 | DIM_PWM | CE_PWM (LD1500SB EN) | G1: 19.5 kHz into the RC. Rev F: 1 kHz |
| D3 | 5 | RADAR_OT2 | RADAR_OT2 | Light-sleep wake, high = present. G1 has R7 100 k pull-down |
| D4 | 6 | UART_TX → radar RX | same | 115200 8N1 |
| D5 | 7 | UART_RX ← radar OT1/TX | same | |
| D10 | 10 | KA_DRV | KA_DRV | Keep-alive gate |
| D0, D8, D9 | 2, 8, 9 | NC | NC | Strapping pins. D9 is BOOT |
| D6, D7 | 21, 20 | NC | NC | UART0 boot log |

Why these pins: only D0–D3 wake the chip, only GPIO2/3/4 are on ADC1, and GPIO21 carries the boot log.

### Connectors (JST-PH 2.0 mm, through-hole, side entry)

| Ref | Pins | Goes to |
|---|---|---|
| J1 | USB-C, HRO TYPE-C-31-M-12 | The bank's output cable |
| J2 | 1 CW end (fed from 3V3 through 47 k), 2 wiper, 3 CCW end (GND) | 100 kΩ linear pot or trimmer |
| J3 | 1 3V3, 2 GND, 3 OT1/TX, 4 RX, 5 OT2 | HLK-LD2410S. **1:1 with the module's header** |
| J4, J5 | 1 filament + (anode), 2 filament − | Filaments |

### Power budget

From `hardware/tools/power_model.py`. Assumptions:

- Bank: 85% of the rated capacity usable at 3.7 V.
- Filament: 2.80 V at 300 mA.
- XIAO: 20 mA while lit.

None of this is measured yet. Tests T2 and T11 in the review cover it.

| State | G1 | Rev F |
|---|---|---|
| Full brightness | 2.06 W, 411 mA | 3.10 W, 621 mA |
| Dark, radar armed | ~1.1 mA + 3.0 mA keep-alive average | ~4.2 mA |

| Bank | G1 continuous | G1 at 4 h/day | G1 at 8 h/day | Rev F at 4 h/day |
|---|---|---|---|---|
| 20,000 mAh | 31 h | 7.3 days | 3.7 days | 4.9 days |
| 25,000 mAh | 38 h | 9.1 days | 4.7 days | 6.1 days |
| 30,000 mAh | 46 h | 10.9 days | 5.6 days | 7.4 days |

**Keep-alive while dimmed.** Below about 25% brightness the lamp draws under 120 mA, which is within many banks' auto-off band. The firmware must pulse whenever the load is low, not only when the lamp is dark (review F1).

### BOM

- [`bom.csv`](../hardware/kicad/fgl_g1/bom.csv): 24 lines, with LCSC and MPN on every placed part.
- [`bom_jlcpcb.csv`](../hardware/kicad/fgl_g1/bom_jlcpcb.csv): 31 SMD placements for JLCPCB.
- **Hand-soldered:** U1 (XIAO, Seeed 113991054) and J2–J5.
- **Not fitted:** D1.
- **Parts cost:** about $2.10 per board at 20 boards, excluding the XIAO. Review §3 has the breakdown.

**Off-board parts:**

- 2 × filament (B0CV83D25S)
- LD2410S (B0DBSKL6BC)
- 100 kΩ pot
- JST-PH cable assemblies
- the bank's USB-C cable

### What the firmware must do on G1

Review §2 has the detail.

- **Build config:**
  - `-DFGL_BOARD_G1`: LEDC at 19.53 kHz, 11-bit, XTAL clock. Mapping duty = (0.3 + 2.2k) / 2.705 for a current fraction k: 100% at 0.924, 5% floor at 0.152, off at 0.
  - `-DFGL_BOARD_REV_F`: the current 1 kHz behaviour.
- **Keep-alive:** pulse whenever the estimated load is below ~120 mA, in every state. `-DFGL_KEEPALIVE=0` disables it.
- **Radar at boot:** set the LD2410S hold (parameter 0x06) and its gate range over UART.
- **Pot:** calibrated millivolts with full scale at ~2.13 V, so there's no per-unit constant.
- **Watchdog and logging:** add a task watchdog. Logging off by default.

### Layout (Oct 22)

- **Board:** 66 × 44 mm, 2 layers, 1.6 mm, 1.5 mm corner radius. M3 holes 3.5 mm in from each corner; move them if the frame needs other positions.
- **Edges:**
  - Top: J4 (FIL 1) and J5 (FIL 2), with "+" at pin 1. The XIAO's USB-C is on the top edge too; the module is flush with the edge so a cable can be plugged in.
  - Left: J1, the 5 V USB-C input.
  - Bottom: J2 (pot) and J3 (radar).
- **Buck cells:**
  - Each channel is a compact cell under its connector.
  - The hot loop (10 µF → SS14 → AL8860 SW/GND) is on the top layer over unbroken bottom-layer GND.
  - R3/R4 are Kelvin-routed to VIN and SET.
  - The LED path surrounds the sense resistor's +5V pad, so +5V reaches it through a via and a short bottom-layer stub under the inductor.
- **Radar:**
  - J3 is at the opposite corner from L1/L2.
  - The XIAO's D3–D5 order is mirrored relative to the LD2410S header, so the three lines run on the bottom layer, straight down to J3.
- **XIAO:**
  - No top-layer copper or vias under the module (a rule area).
  - The bottom-layer GND pour and the 3V3 and XIAO 5V feeds pass under it on the far side of the board.
- **Widths:**
  - Filament paths 0.8 mm, +5V bus 1.0 mm, VBUS 0.6 mm, 3V3 and XIAO 5V 0.4–0.5 mm, signals 0.25–0.3 mm.
  - Clearance 0.2 mm. Vias 0.6/0.3 mm (0.8/0.4 mm on power).
  - Everything is inside JLCPCB's standard 2-layer rules.
- **GND:** pours on both layers, with 32 stitching vias.
- **DRC (KiCad 9.0.7, zones filled):** 0 errors, 0 unconnected pads. The 79 warnings are cosmetic: connector outlines and the XIAO's "USB-C" silkscreen running past the board edge (the fab clips them), the XIAO footprint's own silkscreen clipped at its pads, and library-path notices from the headless check.

**Ordering at JLCPCB** (files in `hardware/kicad/fgl_g1/jlcpcb/`):

1. Upload `fgl_g1-gerbers-jlcpcb.zip`: 2 layers, 1.6 mm. The defaults are fine. Lead-free HASL or ENIG.
2. Turn on PCB Assembly, top side. Upload `fgl_g1-bom-jlcpcb.csv` and `fgl_g1-cpl-jlcpcb.csv`.
3. JLCPCB places 31 parts. D1 (TVS) is deliberately left off. You solder U1 (XIAO) and J2–J5 yourself.
4. **Check the placement preview before paying:**
   - The pin-1 dot on U2, U3 and Q1.
   - The cathode band on D2/D3 (left, +5V side) and D4 (right, toward the XIAO).
   - J1's mouth at the board edge.

   The CPL applies the usual JLCPCB corrections (SOT-23 −90°, TSOT-23 180°, HRO USB-C 180°). Fix any part that still looks wrong in the preview.
5. `JLCJLCJLCJLC` on the bottom silkscreen marks where JLCPCB prints its order number. Choose "Specify a location" when ordering.
6. Re-check stock for the extended parts (AL8860, SWPA6045S) at order time.

### Before layout, and on the first board

Review §4–6:

- **Before layout:** tests T1–T6 on the prototype.
- **Layout:** tight buck loops, Kelvin-routed sense resistors, J3 away from the inductors, and the XIAO's USB-C at an edge.
- **First board:** tests T7–T11. T12 (ERC in KiCad 9) is done.

## Rev F prototype (as built)

Schematic: [`fgl_rev_f.pdf`](../hardware/kicad/fgl_rev_f/fgl_rev_f.pdf).

| Subsystem | As built |
|---|---|
| Board | One full-size ElectroCookie solderable breadboard |
| Power entry | AITRIP USB-C PD trigger (B0D7CFSCP6), **5 V, button-locked**, from the B0DQPD24ZD bank. No fuse |
| MCU | XIAO ESP32C3, 5V pin fed through a 1N5819 |
| Drivers | 2 × LD1500SB (B0F1K97V61): CN5711 linear sink, 5 pads (IN+, IN−, EN, L+, L−). L+ is IN+ inside the module. EN pads commoned to D2 |
| Current set | On-module trimmer (1 k + 47 k), about 300 mA. Measured, not recorded |
| Ballast | One 4.7 Ω 2 W per filament. Position (above or below the filament) not recorded |
| Dimming | 10 kΩ trimmer with a 4.7 kΩ top leg and 100 nF at the wiper. `ADC_RAW_AT_MAX` = 2950. 1 kHz PWM to both EN pads |
| Keep-alive | 2N7000, 100 Ω gate, 100 kΩ pull-down, 33 Ω 2 W. The bank also stays awake with the PD trigger alone (tested) |
| Radar | LD2410S on 3V3 with 10 µF + 100 nF. OT2 → D3, UART → D4/D5 |
| Decoupling | 10 µF electrolytic at each module input |
| Wire | 22 AWG stranded |
| **Unconfirmed** | **R3, a 10 kΩ CE pull-down** (in the Oct 6 wiring table) |

Open prototype actions (review §1):

- **P1:** a 0.5 A PTC in each filament's + lead, and check the frame for anything metal near the filament tabs.
- **P2:** confirm R3. Look for a full-brightness flash at power-up.
- **P3:** bank certification, airflow, and pass-through and temperature tests.
- **P4:** record each channel's current and Vf.

## Decision log

| Date | Decision | Why |
|---|---|---|
| Aug 1 | HLK-LD2410S radar (not XYC-WB-DC, LD2410C, LD2420 or PIR) | Detects stationary people at 0.1–0.45 mA. The C variant draws 80 mA, the LD2420 50 mA |
| Aug 1 | 300 mA per filament, two filaments | Brightness against longevity. Four filaments rejected for battery life |
| Aug 2 | Power bank, not a bare 18650 | A single 18650 gives 4.8 h against ~26 h. Capacity beats efficiency |
| Aug 4 | LD1500SB linear modules for the prototype | Available quickly. Linear needs a 4.7 Ω ballast at 5 V to stay out of foldback |
| Aug 4 | Two drivers, never parallel filaments on one | One CN5711 at 600 mA reaches about 167 °C junction; Vf mismatch |
| Aug 5 | Keep-alive pulse from firmware | 3 mA average against 150 mA for a constant load |
| Oct 6 | CE pull-down plus `gpio_sleep_sel_dis()` | Light sleep floats the pads, and the LD1500SB EN pulls high |
| Oct 5 | PCB with buck drivers for 10–20 units (JLCPCB) | About 50% more runtime, no ballast heat |
| Oct 14 | Perplexity G1 KiCad discarded | Radar miswire, keep-alive placement, unverified 9 V PD fallback |
| **Oct 15** | **G1 redrawn from scratch: 5 V without PD, AL8860, analog dimming, input PTC, edge-pad XIAO footprint** | [design_review.md](design_review.md) |

Rejected along the way:

- **9 V PD with a CH224K:** less efficient here, more parts, and depends on the bank.
- **PAM2804:** 6.5 V absolute maximum.
- **LD3190SB modules:** a module can't be placed by the fab.
- **Mean Well LDD:** 9 V minimum input.
- **Boost driver with the filaments in series:** no suitable part.
- **Li-ion cell direct:** capacity.
- **Dimming to extend runtime:** total light per charge is flat.

## Sources

- AL8860 datasheet: https://cdn.sparkfun.com/assets/3/f/5/8/b/AL8860.pdf
- CN5711 datasheet: https://electronperdido.com/wp-content/uploads/2024/04/CN5711-datasheet.pdf
- XIAO ESP32C3 wiki: https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/
- HLK-LD2410S serial protocol V1.00: https://www.tinytronics.nl/product_files/006002_HLK-LD2410S%20serial%20communication%20protocol-V1.00.pdf
- Seeed KiCad library (XIAO pad geometry): https://github.com/Seeed-Studio/OPL_Kicad_Library
- LD1500SB module listing: https://www.amazon.com/dp/B0F1K97V61
- AITRIP PD trigger: https://www.amazon.com/dp/B0D7CFSCP6
- Power-bank auto-off behaviour: https://powerbankzone.com/power-bank-keeps-switching-off/
