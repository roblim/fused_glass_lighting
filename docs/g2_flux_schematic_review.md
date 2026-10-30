> Flux.ai's schematic review of Rev G2, 2026-10-28, kept as Flux wrote it. Its footnote markers (`[^flux:cite:…]`) point to sources inside Flux and have no definitions here; its links point to the Flux copy of the project. The **Resolution** section at the end (added the same day) gives the verdict and what was done for each finding. Decisions: [`g2_decisions.md`](g2_decisions.md), D19 follow-ups.

# Schematic Review Findings

## Result and scope

**Two schematic-level electrical concerns are supported by the reviewed connections and manufacturer evidence: a bootloader-strapping conflict in manual mode, and an input-protection coordination gap.** The USB-C return arrangement is state-dependent and is not established as an unconditional defect. Schematic label overlaps also need cleanup. No circuit changes were made.

Reviewed all 74 component records and 42 nets, then re-read the affected component pins and nets during the datasheet-backed pass. Sources included the TPS61500 datasheet, TI SEPIC application report SLVA904, Espressif ESP32-C3 datasheet, Seeed XIAO documentation/schematic, AO3400A/AO3401A datasheets, SMF6.0A datasheet, XC6210 datasheet and USB Type-C specification. The XIAO contains its own regulator, reset and clock circuits; these are not treated as missing carrier-board components.

Fresh checks at **2026-10-29 00:13:07 UTC** returned eight successful ERC categories with zero errors/warnings: floating input, no-connect violation, single-pin net, driver conflict, pin-to-pin conflict, missing power, shorted two-terminal component and missing designator. Other requested checks that were not returned are not claimed as passed. Schematic-legibility results reported 3 label-collision warnings and 21 visible-connectivity warnings. These are not electrical opens.

## 1. Manual-mode jumper conflicts with bootloader entry

**Severity: Warning — programming/recovery limitation, not a demonstrated normal-boot failure.**

Observed connections:
- [JP2](https://www.flux.ai/:handle/:documentSlug?fit=JP2) pin 1 is GND and pin 2 is /RADAR_MODE.
- /RADAR_MODE connects directly to [U1](https://www.flux.ai/:handle/:documentSlug?fit=U1) D8_GPIO8 and socket J10 pin 2. R29 provides a 10 kΩ pull-up.
- JP2's documented manual setting is a shunt across pins 1–2. This hard-grounds GPIO8; the pull-up cannot override the shunt.

The ESP32-C3 boot table requires **GPIO8 high and GPIO9 low for Joint Download Boot**. SPI boot allows GPIO8 either level when GPIO9 is high. Thus the fitted manual-mode shunt prevents the documented download strapping combination during reset; it does not by itself prove that normal firmware cannot boot.[^flux:cite:src_page_31_boot_mode_gpio2_gpio8_gpio9_29ed9158a6]

**Action:** move the mode-select input to a non-strapping GPIO, or explicitly require removing/moving the JP2 shunt before manual bootloader entry. Add that requirement beside the jumper and in programming instructions if the wiring is retained. JP2 pin 3 being intentionally unconnected is not itself a fault: the pull-up selects the other logic state.

## 2. Input TVS does not establish a safe clamp for the XIAO regulator

**Severity: Warning — confirmed ratings/protection gap, not a claim that a transient has occurred.**

Observed path: /VBUS_F → [Q2](https://www.flux.ai/:handle/:documentSlug?fit=Q2) → +5V → [D4](https://www.flux.ai/:handle/:documentSlug?fit=D4) → /XIAO_5V → U1. [D1](https://www.flux.ai/:handle/:documentSlug?fit=D1) is an SMF6.0A with cathode on /VBUS_F and anode on GND; its polarity is correct.

The selected TVS has 6 V reverse standoff, **6.67–7.37 V breakdown at 10 mA**, and **10.3 V maximum clamping at 19.4 A**, at 25°C.[^flux:cite:src_md_4fe590891a7217e1] The published XIAO schematic identifies its onboard regulator as **XC6210B332MR** and shows its input power path.[^flux:cite:src_md_d146f68de7c9b353] The XC6210 absolute maximum input is **6.5 V**, while its operating range ends at **6.00 V**.[^flux:cite:src_page_5_absolute_maximum_ratings_tr_td_colspan_2__7aad60c2ba][^flux:cite:src_md_5df444d6556fdecf]

Consequently, D1's specified clamp is not a guarantee that the module regulator stays within its input limit. Q2 is a switch and D4 a series diode, not a regulated overvoltage cutoff. No surge waveform, source impedance or measured clamp waveform was supplied, so actual voltage at the regulator and damage are **not** asserted.

**Action:** coordinate protection at /XIAO_5V with the regulator's limit—prefer a suitably rated input overvoltage-disconnect/limiting power path, or a clamp network whose voltage is verified at the specified surge current. Do not simply choose a TVS by its nominal standoff voltage. D1 is also marked Exclude from Pick & Place; retain that only with an explicit manual-population step if its protection is required.

## 3. Schematic readability: ground labels overlap other signals

**Severity: Warning — presentation, not a netlist short.**

The fresh label-collision check identifies:
- GND decoration at [JP1](https://www.flux.ai/:handle/:documentSlug?fit=JP1) overlapping the /ISEL wire.
- GND decoration at JP2 overlapping the /RADAR_MODE wire.
- /VBUS_IN decoration overlapping its own wire near [J1](https://www.flux.ai/:handle/:documentSlug?fit=J1).

**Action:** move these decorations and extend their stubs so the ground and signal labels are distinct. Preserve net membership. The 21 visible-connectivity warnings primarily concern nearby pins connected by repeated labels instead of direct wires, including /DRV_EN and the SEPIC nodes. Drawing those local connections explicitly would make the power stage easier to audit; they must not be reported as electrical disconnections.

## Correction to the preliminary USB-C finding

The preliminary review called the CC return a concrete electrical issue too broadly. The exact finding is:
- J1 CC1 → R1 (5.1 kΩ) → /SW_N.
- J1 CC2 → R2 (5.1 kΩ) → /SW_N.
- /SW_N also reaches J2 SW and R14 (10 kΩ); R14 reaches Q2 gate, with R13 (100 kΩ) to /VBUS_F.

**When the external switch grounds /SW_N, both CC pins have their own 5.1 kΩ return to ground. Sharing that grounded endpoint is not the same as shorting CC1 directly to CC2.** When the switch opens, those pull-downs lose their ground return, and the two CC pins remain linked through the two resistors. The external switch mechanism is not drawn as an explicit switch element, so its contact behavior cannot be proved from the connector alone.

The USB-C sink functional model terminates both CC pins to ground through Rd.[^flux:cite:src_md_c7b83d7df6a29b4e] The source uses continued presence of Rd for detach detection and removes VBUS on detach.[^flux:cite:src_page_155_6_the_source_monitors_the_continued_pre_a5ca31899f]

Therefore switching Rd may be intended to request source detachment in the off state. **No unconditional USB-C failure is claimed.** If the intended behavior is to remain attached while switching only the load, connect R1/R2 directly to GND and leave /SW_N for gate control. If source detachment is intentional, annotate it and validate both switch states and cable orientations; this review does not certify the custom off-state network as compliant.

## Power-stage and component findings not classified as defects

### Pin assignments and decoupling
The reviewed U2 pin numbers match the datasheet: SW 1/2, VIN 3, EN 4, SS 5, DIMC 6, AGND 7, COMP 8, FB 9, FREQ 10, OVP 11 and PGND 12–14.[^flux:cite:src_md_d6e00def85ed62e5] The schematic grounds AGND, PGND and EP. Input bypass is present: C2 = 10 µF and C3 = 100 nF on +5V, plus C1 = 10 µF. The 3.3 V rail has C10/C11 = 10 µF/100 nF; radar after FB1 has C13/C14 = 10 µF/100 nF. Physical capacitor placement and ground-return quality require layout inspection.

### Current limiting and output protection
The LED return connects U2 FB to R20 = 0.82 Ω to ground. Shunting JP1 pins 1–2 adds R21 = 0.82 Ω in parallel. The nominal FB regulation voltage is 200 mV and programs LED current through the feedback resistance.[^flux:cite:src_page_13_8_2_1_2_2_programming_the_led_current_le_e53b3285eb] The nominal single-resistor current calculated with the native calculator is 0.243902 A; paralleling the equal resistor doubles that setting. These are circuit settings, not a verified rating for the external filaments. Missing individual LED series resistors is not a demonstrated fault in this regulated-current arrangement.

R15 = 110 kΩ and R16 = 5.1 kΩ give nominal OVP **27.736843 V**, using the manufacturer's equation:[^flux:cite:src_page_13_8_2_1_2_1_programming_the_overvoltage_pr_fc5e59e5a1]

$$V_{OVP}=1.229\,\mathrm{V}\times\left(\frac{R1}{R2}+1\right)$$

At that nominal output, R24 = 120 kΩ and R25 = 10 kΩ produce /VSENSE = **2.133603 V**. The ESP32-C3 calibrated ATTEN3 effective range is 0–2500 mV.[^flux:cite:src_md_c405a1dbbac04342] No nominal range violation is found; firmware attenuation/calibration, component tolerances, startup sequencing and transients were not verified. These simple nominal calculations are not a tolerance or dynamic sign-off.

### Dimming and pull resistors
U2 EN has R17 = 1 kΩ in series and R18 = 2.2 kΩ to ground. Its specified high threshold is 1.2 V minimum and low threshold 0.4 V maximum.[^flux:cite:src_page_5_table_tr_td_colspan_2_parameter_td_td_tes_da7a592be7] C7 = 1 µF on DIMC selects filtered analog dimming; floating DIMC would instead select pure PWM dimming.[^flux:cite:src_page_13_8_2_1_2_3_implementing_dimming_the_tps61_8028b0387d] Thus /DIM_PWM can correctly name the input waveform without implying pure-PWM output operation. Q1 has a 100 Ω series gate resistor and a 100 kΩ gate pull-down. No missing pull resistor is established for those controls.

### SEPIC and compensation
L1–C4–L2–D5 connectivity is a SEPIC, not an incorrectly wired boost converter. C9 = 100 nF is connected from COMP to ground. The main boost application recommends 470 nF,[^flux:cite:src_page_14_8_2_1_2_7_selecting_the_compensation_cap_0da89209ab] but TI's separate SEPIC example uses 15 nF with discrete inductors and 33 nF with coupled inductors.[^flux:cite:src_md_99f808e6ddd2fcd0] **The difference alone does not establish that C9 is wrong. Do not blindly replace it with the boost-example value.** TI's SEPIC procedure targets more than 60° phase margin and crossover at least ten times below the lowest right-half-plane zero.[^flux:cite:src_md_f6dce044670924dd][^flux:cite:src_md_95027ca6cc9e56b8] Actual stability remains unverified without the operating load and loop analysis/measurement.

## Explicit limits and unresolved evidence

- LD2410S manufacturer-manual extraction remained pending after a waited retry. Its supply and physical pinout are therefore not given final datasheet sign-off here. The two schematic connector options share consistent five-net assignments, but that is not proof of external cable orientation.
- XIAO logical GPIO assignments were compared with Seeed's pin map, but precise socket viewing orientation and physical mating were not signed off. The schematic extraction did not resolve all numbered module-header assignments.
- Numeric MOSFET pin assignments were not fully verified from the retrieved drawing evidence. No pin-swap defect is claimed.
- Filament forward voltage/current ratings, actual USB source capability, operating input tolerance and firmware were not supplied. Power-budget sufficiency, inductor saturation at the operating point, fuse adequacy and resistor/transistor temperatures cannot be declared failed or passed from the available evidence.
- No PCB routing/DRC or simulation was performed. Missing star grounding, excessive trace length, inadequate termination, capacitor placement and EMI are not inferred from schematic distances.

## Recommended next actions

1. Remove the GPIO8/manual-mode bootloader conflict, or document the programming workaround.
2. Specify the input surge requirement and coordinate the XIAO power-path protection with its regulator limit.
3. Clean up the jumper ground-label overlaps and draw the SEPIC local connections explicitly.
4. With the actual filament ratings and input range, verify the power budget and SEPIC loop before manufacturing.

## Resolution (2026-10-28)

| Finding | Verdict | Done |
|---|---|---|
| 1. JP2 manual-mode shunt blocks download boot | Correct, and known from D18: GPIO8 low with GPIO9 low is an invalid boot combination. No other free XIAO pin is safe (D0 must be high at boot, D9 is BOOT) | "Remove shunt to flash" added to the silkscreen under the JP2 legend and to the flashing step in `hardware.md`. Bring-up test G2-T12 now tries a normal USB flash with the shunt on, to learn whether the XIAO's USB reset also needs GPIO8 high |
| 2. D1 cannot keep the XIAO regulator within its limit | Correct: XC6210 is 6.0 V operating, 6.5 V absolute maximum (Torex datasheet); SMF6.0A breakdown is 6.67 V minimum, so D1 (not fitted) would not protect it. In practice the board requests only 5 V (no PD; D+/D- unconnected), and the soft start keeps Q2 off through a plug-in ring, so the XIAO is no more exposed than on its own USB | G2-T6 now scopes the XIAO's 5V pin (J10 pin 7) during live USB-A plug-ins, switch on and off, both plug orientations; limit 6.0 V. If it fails, the fix is an input over-voltage cut-off in G3, not D1; until then use USB-C-to-C only. The schematic's D1 note now points at G2-T6 |
| 3. Label overlaps; SEPIC drawn with repeated labels | Correct (presentation only) | GND symbols at JP1 and JP2 moved off the neighbouring signal wires; VBUS_IN's power flag wired to F1; F1 and Q2 reference/value no longer overprint. Section 2 redrawn with wires: power path along the top, U2 below with its control pins fanned out to their parts, one label per net. KiCad's netlist is identical before and after (nets, names, parts, fields); `verify_netlist.py` passes; ERC 0 errors |
| USB-C CC resistors returned through SW_N | Intentional (D16): with the switch off, Rd floats so the bank sees no sink and sleeps; the schematic note says so | G2-T6 now covers both plug orientations, in both switch states |
| C9 = 100 nF vs TI's 470 nF boost example | Agreed with Flux: keep. Chosen from SLVA904's SEPIC procedure (crossover below a tenth of the 43 kHz RHP zero) | G2-T3 measures the loop |
| Open limits (LD2410S pinout, XIAO socket orientation, MOSFET pins) | Already verified in the Oct 24 netlist audit ([`g2_netlist_audit.md`](g2_netlist_audit.md)): radar TX/RX against Hi-Link's protocol document, socket pad coordinates against the XIAO pin order, SOT-23 pins against the AOS datasheets | None |
