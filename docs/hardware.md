# Fused Glass Lighting: Hardware

Motion-activated backlighting for a fused-glass artwork:

- A Seeed XIAO ESP32C3 drives a series string of LED filaments, one to four of them, 3 V or 12 V in any mix. The default is one 12 V 600 mm warm-white filament at about 150 mA.
- A 24 GHz HLK-LD2410S radar turns the light on when someone is present and off 25 s after they leave.
- A pot with a built-in switch sets brightness and turns the whole system off at its counter-clockwise stop.
- A 20,000–30,000 mAh USB power bank inside the frame powers everything. It is charged through a USB-C panel inlet on the frame (B08HS6X44P).

This is the canonical hardware document.

- **Current design:** Rev G2. Decisions and reasoning: [`g2_decisions.md`](g2_decisions.md).
- **Earlier review:** the Oct 15 review of Rev F, the firmware and G1 is [`design_review.md`](design_review.md).
- **Firmware:** [`../src/main.c`](../src/main.c).

## Status (2026-10-28)

| Revision | What | State |
|---|---|---|
| Rev F | Hand-wired prototype on one full-size ElectroCookie board, LD1500SB linear driver modules | **Built and working.** Firmware flashed, presence detection and dimming confirmed. Open safety items P1 and P3 in the review |
| Rev G1 | Single PCB, 2 × AL8860 buck at 303 mA, 5 V USB-C input | **Superseded 2026-10-23, do not order.** Laid out Oct 22 (DRC clean, gerbers in `hardware/kicad/fgl_g1/jlcpcb/`), but 303 mA per 3 V filament is too close to the edge (G2 decision D1). Kept for reference |
| **Rev G2** | Single PCB, TPS61500 SEPIC driving one series string through 4 push-in ports, 244/488 mA, power switch, socketed XIAO and radar | **Laid out (Oct 23).** ERC clean. Netlist and PCB pad nets both verified against hand-written intent. DRC: 0 errors, 0 unconnected (zones filled). JLCPCB gerbers, BOM and CPL are in `hardware/kicad/fgl_g2/jlcpcb/`. Makers' 3D models added and the Degson outline fixed (Oct 24). Oct 24 audit fixes made (Oct 25, D16): EN pull-down, 100 V output caps, lower OVP, JP1 as a shunt header, soft-start, firmware guards. Layout DFM pass after Gemini's review (Oct 26, D17): vias off the pads, thermal reliefs on J3/J4 GND, more ground stitching, an assembly drawing. JP2 radar/manual jumper added (Oct 27, D18). Relaid out at 90 × 60 mm with horizontal-entry ports, the R29 pull-up and room for rework (Oct 28, D19). **Before ordering:** check JLCPCB's placement preview, confirm fuse and port stock, check header pin length against the 5 mm sockets, and build and flash the G2 firmware with PlatformIO ([`g2_decisions.md`](g2_decisions.md#open-items-before-ordering-g2)) |

## Files

| Path | Contents |
|---|---|
| `hardware/kicad/fgl_g2/` | **G2** project: schematic (`fgl_g2.kicad_sch`, the master), PCB (laid out, zones filled), PDF, netlist, `ERC.rpt`, `DRC.rpt`, `verification.txt`, `bom.csv`, `bom_jlcpcb.csv`, layout preview `fgl_g2_layout.png`, 3D render `fgl_g2_3d.png`, assembly drawing `fgl_g2_assembly.pdf` (every reference designator, and parts by reference), project symbols, the port footprints (`fgl.pretty`) and the 3D models (`3dmodels/`: makers' models, D15, and a simplified JL212R port model, D19) |
| `hardware/kicad/fgl_g2/jlcpcb/` | G2 JLCPCB order files: `fgl_g2-gerbers-jlcpcb.zip`, `fgl_g2-bom-jlcpcb.csv`, `fgl_g2-cpl-jlcpcb.csv` (with rotation corrections), the raw KiCad position file, `make_cpl.py` and the unzipped `gerbers/` |
| `hardware/tools/layout_g2/` | The scripts that produced the G2 placement and routing (kept for reference; the `.kicad_pcb` is now the master) |
| `docs/g2_decisions.md` | **G2** decisions, reasoning, values, BOM sourcing, open items and bring-up tests |
| `docs/g2_netlist_audit.md`, `docs/g2_layout_dfm_audit.md` | Reviews of G2: the Oct 24 netlist/power/BOM audit, and Gemini's Oct 25 layout and DFM review. Each ends with a resolution section |
| `hardware/tools/sepic_design.py` | G2 SEPIC checks: switch peak current, voltages, RHPZ |
| `hardware/kicad/fgl_g1/` | G1 (superseded) KiCad 9 project: schematic (the master), PCB (laid out, zones filled), PDF, `ERC.rpt`, `DRC.rpt`, `bom.csv`, `bom_jlcpcb.csv`, netlist, `verification.txt`, project symbols (`fgl.kicad_sym`) and the XIAO footprint (`fgl.pretty`) |
| `hardware/kicad/fgl_g1/jlcpcb/` | JLCPCB order files: `fgl_g1-gerbers-jlcpcb.zip`, `fgl_g1-bom-jlcpcb.csv`, `fgl_g1-cpl-jlcpcb.csv` (with rotation corrections), the raw KiCad position file and `make_cpl.py` |
| `hardware/tools/layout_g1/` | The scripts that produced the G1 placement and routing (kept for reference; the `.kicad_pcb` is now the master) |
| `hardware/kicad/fgl_rev_f/` | Rev F as-built schematic and PDF. These replace the Perplexity PNG drawings |
| `hardware/tools/` | Schematic generators, the netlist verifier, the BOM script and the power model. See [`../hardware/README.md`](../hardware/README.md) |
| `docs/design_review.md` | The design review (Oct 15) |
| `docs/archive/hardware_rev_f.md` | The Oct 6 Rev F build and bring-up document, with corrections at the top |
| `docs/archive/main_previous_iteration.c.txt` | Firmware from before Rev F |

## Requirements (as of 2026-10-23)

1. **Filaments.** One to four, warm white, in one series string; 3 V (≤ 300 mm) and 12 V (600 mm) mixable. Brightness comes from filament length, not current density. The prototype piece needed about 1.7 W of LED power (about 115 lm): one 12 V 600 mm at 150 mA, or 4 × 3 V 300 mm at 150 mA. Larger or more opaque pieces need headroom up to 244 mA, or 488 mA for personal projects.
2. **Maximum runtime** from a USB power bank, plain 5 V. Any bank, so no PD.
3. **XIAO ESP32C3**, PlatformIO with ESP-IDF.
4. **Interchangeable bank.** The end user may fit any 20,000–30,000 mAh bank. Design target: B0DQPD24ZD (20,000 mAh, built-in cables).
5. **Off-delay 25 s.**
6. **Minimal hand assembly.** JLCPCB fits everything, including the through-hole parts. The XIAO (bought with headers) and the radar plug in, and filaments go into push-in terminals.

The old requirement of exactly two filaments at 300 mA each was dropped on Oct 23 (G2 decision D1). 300 mA came from a convection model, not a filament rating. Adafruit recommends 50 mA, and DFRobot's published ratings show that derating is what buys lifetime.

## Rev G2 (current design)

Schematic: [`fgl_g2.pdf`](../hardware/kicad/fgl_g2/fgl_g2.pdf). Everything below is detailed with reasoning in [`g2_decisions.md`](g2_decisions.md).

```
Bank ── J1 USB-C (Rd 5.1 k to SW_N) ── F1 PTC 1.5 A ── Q2 P-FET (on when the pot switch closes) ──┬── U2 TPS61500 SEPIC ── VOUT ── J5 ── J6 ── J7 ── J8 ── R20/R21 ── GND
                                                                                                  ├── Q1 + R12 keep-alive
                                                                                                  └── D4 ── J9/J10 XIAO sockets ── 3V3 ── FB1 ── radar J3 (socket) / J4 (cable), pot J2
```

- **Driver:** TPS61500 as a SEPIC (TI SLVA904): L1 = L2 = 10 µH, C4 10 µF 50 V coupling, D5 SS36, 1.17 MHz, OVP 27.7 V, output caps rated 100 V. It runs any string from one 3 V filament to 24 V. With the driver off there is no DC path to the LEDs.
- **Current:** 0.2 V / 0.82 Ω = 244 mA. Moving the JP1 shunt to pins 1–2 gives 488 mA and tells the firmware (D4). The firmware dims below the ceiling by PWM on EN (analog dimming through DIMC), I = duty × I_max.
- **Sensing:** VSENSE = VOUT / 13 on D2, for the 5 W power cap, a low-current check at every start, and open/short/reversed-filament detection (D5, D16).
- **Ports:** J5–J8 are JILN JL212R push-in terminals along the top edge, with the wires entering parallel to the board and the release buttons on the same face (D19), and + / NEXT / END legends behind them. Fill from port 1; the last filament's − goes to END.
- **Power switch:** the pot's switch (J2 pin 4) grounds SW_N. That connects the USB-C Rd resistors (the bank sees an attach and wakes) and turns Q2 on, softly over about 1 ms (C16). Off means 0 mA and the bank sleeps.
- **Sockets:** the XIAO plugs into J9/J10 (5 mm low-profile). The radar plugs into J3, or uses the J4 cable connector.
- **Keep-alive:** unchanged, with a firmware setting to turn it off.
- **Radar or manual (JP2, D18):** with the JP2 shunt on pins 1–2 the firmware ignores the radar and keeps the string lit whenever the switch is on, dimmed by the pot. On 2–3, or with no shunt, the radar switches it as before.

| XIAO | GPIO | G2 net | Notes |
|---|---|---|---|
| D1 | 3 | ADC_POT | ADC1_CH3 |
| D2 | 4 | VSENSE | ADC1_CH4, VOUT / 13 |
| D3 | 5 | RADAR_OT2 | Wake, high = present |
| D4 | 6 | UART_TX → radar RX | 115200 8N1 |
| D5 | 7 | UART_RX ← radar OT1/TX | |
| D6 | 21 | ISEL_IO | Low = 244 mA (JP1 shunt on 2–3); via R22 1 k, GPIO21 toggles at boot |
| D7 | 20 | DIM_PWM | 19.53 kHz to TPS61500 EN; R18 2.2 k holds EN low through reset |
| D8 | 8 | RADAR_MODE | JP2: low = manual (shunt on 1–2). R29 10 k pull-up (D19). Strapping pin: move the shunt off 1–2 before forcing download mode with BOOT |
| D10 | 10 | KA_DRV | Keep-alive gate |
| D0, D9 | 2, 9 | NC | Strapping pins (D9 is BOOT) |

| Connector | Pins | Goes to |
|---|---|---|
| J1 | USB-C, HRO TYPE-C-31-M-12 | The bank's output cable |
| J2 | JST-PH 4, numbered like the pot: 1 CCW + switch common (GND), 2 wiper, 3 CW (3V3 through 47 k), 4 switch | 100 kΩ linear pot with built-in switch, off at CCW. 1:1 cable to pot terminals 1–3 |
| J3 | 1×5 2.54 mm socket, 5 mm: 3V3, GND, OT1/TX, RX, OT2 (signals through R26–R28, 1 k) | LD2410S plugs in directly |
| J4 | JST-PH 5, same pinout as J3 | LD2410S on a cable |
| J5–J8 | JILN JL212R push-in, horizontal entry: 1 +, 2 NEXT, 3 END | Filaments (22 AWG pigtails) |
| J9, J10 | 1×7 2.54 mm sockets, 5 mm | XIAO (pins 1–7, 8–14) |

**Setting up a piece:**

1. **Switch off before wiring the ports.** An open string sits near 28 V with the output capacitor charged (silkscreen: "SWITCH OFF BEFORE WIRING PORTS").
2. **Set the current range with the JP1 shunt:** on pins 2–3 (left) for 244 mA, on 1–2 (right, by the "1") for 488 mA. With no shunt the board runs at 244 mA and the firmware dims to half of what it intends: safe, but dim.
3. **Choose radar or manual with the JP2 shunt** (switch off first; it is read at power-on): on pins 2–3 (left) for radar, on 1–2 (right, by the "1") for manual. Manual means the lamp is lit whenever the switch is on; use the pot to dim it and its switch to turn it off. No shunt = radar. If you ever force download mode with the XIAO's BOOT button, move the shunt off 1–2 first.
4. **Set the piece maximum** in `platformio.ini` (`FGL_MAX_CURRENT_MA`, default 150 mA, clamped to the JP1 range) and flash the `seeed_xiao_esp32c3_g2` build.
5. **First start learns the string.** The voltage at a low probe current is stored. A later start that reads outside ±15 % of it is refused (the light stays off, retry every 30 s), which catches a reversed filament or a port wired wrong. To fix a window at build time instead, set `FGL_STRING_VMIN_MV`/`FGL_STRING_VMAX_MV`.
6. **After rewiring on purpose, relearn:** within 10 s of switching on, turn the knob fully clockwise and back to the minimum. The lamp blinks off once, and the next start learns the new string.

**Power** (model, SEPIC at 84 %): one 12 V 600 mm filament at 150 mA uses 1.64 W of LED power and 416 mA from the bank. That gives 7.2 days on 20 Ah at 4 h/day, or 10.8 days on 30 Ah. Idle is 4.05 mA with keep-alive and 0.72 mA without; switched off, 0. In manual mode the lamp is lit for as long as it is switched on: about 29 h on 20 Ah at 150 mA. More in [`g2_decisions.md`](g2_decisions.md#power-and-runtime-power_modelpy).

**Cost:** about $4.0 per board in JLCPCB-fitted parts at quantity 10, which is about $1.65 more than G1. Excludes the PCB, assembly fees, the XIAO and the radar.

**Layout** (90 × 60 mm, 2 layers, D19; the first layout was 74 × 58 mm, D15):

- The ports run along the top edge, wire entry at the edge, 15 mm apart. USB-C is on the right edge and the XIAO in the bottom-left (its USB-C at the left edge).
- The radar socket is in the bottom-right corner. The pot and radar-cable connectors are on the bottom edge. M3 holes in the four corners, 3.5 mm in.
- Parts are spread for hand rework: at least 0.72 mm between courtyards, median about 1 mm (the 74 × 58 mm board had a median of 0.3 mm). The small parts under the XIAO and the radar are reached by unplugging the module.
- Both layers carry GND pours. B.Cu is kept solid under the SEPIC. Vias are tented and kept at least 0.25 mm from every SMD pad.
- **Widths:**
  - 1.0 mm: +5V spine, LED_RTN bus, string chain.
  - 0.8 mm: VBUS and VOUT.
  - 0.25–0.4 mm: signals.

**Ordering at JLCPCB** (files in `hardware/kicad/fgl_g2/jlcpcb/`):

1. **Board:** upload `fgl_g2-gerbers-jlcpcb.zip`. 2 layers, 1.6 mm, HASL lead-free or ENIG.
2. **Assembly:** turn on PCB Assembly, top side, and upload `fgl_g2-bom-jlcpcb.csv` and `fgl_g2-cpl-jlcpcb.csv`.
   - JLCPCB fits 62 parts, through-hole ports, sockets and the JP1 and JP2 headers included.
   - D1 (TVS) is left off on purpose. You plug in the XIAO and the radar, and fit the JP1 and JP2 shunts (two C5305, ordered as loose parts).
3. **Check the placement preview before paying.** The CPL corrects SOT-23 (−90°) and the HRO USB-C (180°). It also applies 270° to U2 and the sockets, which is unconfirmed. Check these in particular:
   - U2's pin 1 (top right of the IC as placed, SW pins toward L1);
   - the SS36/SS14 cathode bands;
   - the port blocks' wire entry and buttons toward the top board edge;
   - the JST-PH openings toward the board edge;
   - J1's mouth at the right edge;
   - JP1's and JP2's square pin 1 on the right (under the "1").
4. **Order number:** choose "Specify a location". `JLCJLCJLCJLC` on the bottom silkscreen marks the spot.
5. **Stock:** re-check F1 (low stock) and the extended parts before ordering.

**Off-board parts:**

- filaments: DFRobot FIT0926 12 V 600 mm 2200 K, or 3 V types (see D1)
- LD2410S
- XIAO ESP32C3 with pre-soldered headers
- 100 kΩ linear pot with switch
- JST-PH 4-pin cable, and a 5-pin cable if the radar is remote
- 22 AWG filament pigtails

## Rev G1 (superseded 2026-10-23)

Kept as a record of the Oct 15–22 design. Don't order it: see G2 decision D1.

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

### What the firmware had to do on G1 (G2 list: g2_decisions.md, open item 5; the G2 build is in `src/main.c`)

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
| Oct 15 | G1 redrawn from scratch: 5 V without PD, AL8860, analog dimming, input PTC, edge-pad XIAO footprint | [design_review.md](design_review.md) |
| Oct 22 | G1 laid out (66 × 44 mm, DRC clean) | Ready to order, before the filament review |
| **Oct 23** | **Rev G2: one series string through 4 push-in ports, TPS61500 SEPIC (TI SLVA904), 244/488 mA ceiling plus firmware trim, 5 W cap with string-voltage sense, pot power switch that also releases the USB-C attach, socketed XIAO and radar, keep-alive setting. G1 superseded** | 303 mA per 3 V filament was too close to the edge; mixing filaments, fewer hand-solder joints, any string length. [g2_decisions.md](g2_decisions.md) |
| Oct 23 | G2 laid out (74 × 58 mm, DRC clean, JLCPCB files made) | [g2_decisions.md D15](g2_decisions.md#d15-layout-2026-10-23) |
| Oct 24 | G2 3D view uses the makers' models (Degson, Hi-Link, LCSC/EasyEDA, and the XIAO model Seeed links to on GrabCAD). The Degson outline was found mirrored and fixed (pads unchanged). 6 mm header pins may stop modules about 2 mm above the 5 mm sockets | [g2_decisions.md D15](g2_decisions.md#3d-models-2026-10-24) |
| Oct 25 | G2 audit fixes: R18 2.2 k (EN low through boot and flashing), C5/C6 100 V, OVP 27.7 V (24 V strings), JP1 as a 1×3 header with a shunt, Q2 soft-start (R14 10 k + C16), silkscreen wiring warning. Firmware: G2 build with start-up probe and string guards, pot clamp, radar RX pull-up, task watchdog | [g2_decisions.md D16](g2_decisions.md#d16-fixes-from-the-oct-24-audit-2026-10-25), [g2_netlist_audit.md](g2_netlist_audit.md) |
| Oct 26 | G2 layout DFM pass after Gemini's review: 25 fan-out vias moved off pads, J3/J4 GND pins on thermal reliefs, 12 GND stitching vias added, assembly drawing added. The radar does not overhang L2 (measured); bring-up test G2-T11 checks for interference | [g2_decisions.md D17](g2_decisions.md#d17-layout-dfm-pass-after-geminis-review-2026-10-26), [g2_layout_dfm_audit.md](g2_layout_dfm_audit.md) |
| Oct 27 | G2: JP2 header on XIAO D8 selects radar or manual mode (shunt 1–2 = manual: lit whenever switched on, pot dims). GPIO8's internal pull-up instead of a resistor (no room by J10). Firmware reads it at power-on. Bring-up test G2-T12 | [g2_decisions.md D18](g2_decisions.md#d18-jp2-radar-or-manual-mode-2026-10-27) |
| Oct 28 | G2 relaid out at 90 × 60 mm: horizontal-entry push-in ports (JILN JL212R; Degson DG212R fits the same footprint) so the leads leave the board edge whichever way it is mounted; R29 10 k pull-up on D8; C16 to 0603; parts spread for rework; TP5 moved clear of the radar. Bring-up test G2-T13 | [g2_decisions.md D19](g2_decisions.md#d19-90--60-mm-relayout-horizontal-entry-ports-r29-room-for-rework-2026-10-28) |

Rejected along the way:

- **9 V PD with a CH224K:** less efficient here, more parts, and depends on the bank.
- **PAM2804:** 6.5 V absolute maximum.
- **LD3190SB modules:** a module can't be placed by the fab.
- **Mean Well LDD:** 9 V minimum input.
- **Boost driver with the filaments in series:** rejected Oct 15 for lack of a suitable part. Superseded on Oct 23: the TPS61500 SEPIC does it.
- **PD 9/12 V input for G2:** about a 2 % gain at these powers, and it rules out non-PD banks.
- **1 A current option:** limits the string to about 10 V from 5 V, and would need 4 A switching parts and buck-boost.
- **Li-ion cell direct:** capacity.
- **Dimming to extend runtime:** total light per charge is flat.

## Sources

- G2 sources (TPS61500, SLVA904, filament ratings, Degson, Seeed): [`g2_decisions.md`](g2_decisions.md#sources)

- AL8860 datasheet: https://cdn.sparkfun.com/assets/3/f/5/8/b/AL8860.pdf
- CN5711 datasheet: https://electronperdido.com/wp-content/uploads/2024/04/CN5711-datasheet.pdf
- XIAO ESP32C3 wiki: https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/
- HLK-LD2410S serial protocol V1.00: https://www.tinytronics.nl/product_files/006002_HLK-LD2410S%20serial%20communication%20protocol-V1.00.pdf
- Seeed KiCad library (XIAO pad geometry): https://github.com/Seeed-Studio/OPL_Kicad_Library
- LD1500SB module listing: https://www.amazon.com/dp/B0F1K97V61
- AITRIP PD trigger: https://www.amazon.com/dp/B0D7CFSCP6
- Power-bank auto-off behaviour: https://powerbankzone.com/power-bank-keeps-switching-off/
