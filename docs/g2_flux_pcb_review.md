> Flux.ai's PCB layout and DFM review of Rev G2, 2026-10-28, kept as Flux wrote it. Its footnote markers (`[^flux:cite:…]`) point to sources inside Flux and have no definitions here; its artefact links are Flux's signed copies. Flux worked from its own import of the KiCad project, so some findings describe the import rather than the board. The **Resolution** section at the end (added the same day) gives the verdict and what was done for each finding. Decisions: [`g2_decisions.md`](g2_decisions.md), D19 follow-ups.

# PCB Layout and DFM Review

Read-only review of fgl_g2 (90 × 60 mm, 2-layer copper, 74 schematic components / 73 layout elements). No design changes were made. Scope limits: no fab or assembler selected, no LED string voltage, current mode or ambient temperature supplied. This is not a fab DFM approval. **Overall verdict: NOT released for bare-board fabrication or PCBA.**

Review artifacts (EDA computer `dfm-check`, `/root/out`; REVIEW ONLY, not a production package):
- [gerber-check.json](https://cdn2.flux.ai/flux-comment-files/files/commentFileId-2f021afa85d67653343ced1c90744a4b178de1d947136c5a748ce2632b39239a.json?GoogleAccessId=fleet-agent-worker%40graviton-mvp.iam.gserviceaccount.com&Expires=4946839612&Signature=KHoCwCEmZr6o7C%2Bs3Cd%2FAAad%2FZdTi5kWaMDMO26FMG3XKazPj4pUfU%2B3AgsENmjYNaT%2BBPiVoe0yfP75LYLiom1bayMbuMe%2BqgoXCSdpx6EkVfDgtTbXOPdUPOmWvfOm2BwOFnk1ZN7noQ1xVBtAIl0fGeTclAglrUM6%2F3CtBQCG8k%2Bv4tEh9KI8Qxcv%2FXErTf%2FfOgtNri6XEou2ZbUJLpvTFUZYYDdvwbXnjqhn3Ct7dlCa2%2FCcR8uLRR7tU5QsZG0WRx%2FX2rt5j2AbAa0Za4FjG%2FKYMLbZOpJcLyn3cVPaYsrbhfzilGH8XaUR5bI7Sl7imlaFFlY1N0fPcOIrFg%3D%3D)
- [drc.json](https://cdn2.flux.ai/flux-comment-files/files/commentFileId-39f9eafa4d239ffa970d1b96062b41905f329dce8fd23c22ffa7ec06ec888ca7.json?GoogleAccessId=fleet-agent-worker%40graviton-mvp.iam.gserviceaccount.com&Expires=4946839613&Signature=ng9j50uCtbrLOaw04s464Rcw2jYrVD45JKVUIwKIZJeYFIX7%2FLvqqiBKSBXq5EdpK0MLIzkgp8isJulITXDkL%2Biscxhvj6VL9pqjlbpmsnFgxHDDx38oqXbZGjpwdQqMoAt3i%2Bq4pYZbw5NpWH128yF3gwScpSymd3ajRx6Z5WrChaJTC1L%2BFv5P26Iw5aSk8JKtuUfkYhBeHrETARvWvenQbfA1bqOcpes5mzgHTceMZsLnRPhVMporxr8aniJh1twj3KVmGn7hOnLBTrPCrnrUDBxPyE%2FFBIflDOBw3jjK16lNESvwvYnHz9e0v5BliIaEfSVC0GYzeDyrCKsVAw%3D%3D) (KiCad DRC)
- [placement-check.json](https://cdn2.flux.ai/flux-comment-files/files/commentFileId-f2c12bafeea42bfb2698b0036c298574880892e6cd9828d129fcacc77405fcd9.json?GoogleAccessId=fleet-agent-worker%40graviton-mvp.iam.gserviceaccount.com&Expires=4946839613&Signature=NXu9Xx6TzyBtl%2B84hpHeort3ex4VrcVel%2FrfA7Pg%2FcYJ3sknw2toKCRLQuvGIOI1UYJ0uykyxK64eiwd1vcCZTUuMgVL6z54kjf6VeJsnpD3MpBTcHCg%2Bxf80AERdy5fp%2FYTaV6IaHy6ARcBnzfrpnbp44x94EnM5wvqNC6Q9FlniasxB2mG3GZmUoNOFzTeDvvMAG1EwXofvxmsSew0MmZQgavQjhOg%2BRLhPonVWovLK%2BXyTN9xLY4EG7EQ%2BihzEcb%2FCSJ5Wgd%2FGL7FHS6Bd%2F5MmRE6cp6Er3wjR4W7cI0vJiNSC4hyhRAvOEFtlf4PzmCEWO64LY775KZ8%2FO41NQ%3D%3D)
- [top.png](https://cdn2.flux.ai/flux-comment-files/files/commentFileId-3ac81b80badd657d9d84840d3dbd84f57f589e0d5068a4be2e13c942d4f6733a.png?GoogleAccessId=fleet-agent-worker%40graviton-mvp.iam.gserviceaccount.com&Expires=4946839613&Signature=otw3hYxcMpbnq30JzCA5rJge7NaQEljKIZKeCtTbAHPfNHY8oZTcdHBvE4xz5uunKLKBkKC4i3TR%2B07HqpJfzw2v2oW3906kdJur2ZplTPIo%2Bo2Q1%2FF5NGzgRtMB2DxxiS8ZyRAbJahZBV9XrUnAOz6vQ9GszB2s6ydaphn5LAfxSaOdG%2BLVkhvIr7n1wq%2FJrzGfMkviymGrWxXLlEazUHJesFvq74w4vFT%2Fi5Tls38gEx1frS03QhTuAkylqJBrtVRmGuoeJbLLEoDArcb2C7PHz3d2hTw9xxcRNBcel5wbDnCeZtEqgVdoonEvtIeVfshP17bl0NMKL4oSjmtXwA%3D%3D)
- [bottom.png](https://cdn2.flux.ai/flux-comment-files/files/commentFileId-aa258712435b34c5cddec3aa01b09e5bd50770fbba973b4e9d578ee60d4cc7f0.png?GoogleAccessId=fleet-agent-worker%40graviton-mvp.iam.gserviceaccount.com&Expires=4946839614&Signature=rukRIPT949Wgq81qzZDn4JKQWqspHKSLUM7gQePUwA4VPtJ5UZdWX6bACPqrJ59oxzrIe3zq9WxoGUtL4iJuPEZndvv3i9tZN4Xgx%2B2jVSUdOtNBsjV1x93zk6ZLJnX9YeMZvZg2yqB3IlF%2B5yPcjCG5QcOSo7NwVPvUh3csdIyQYo9WCOaIoaiR7o8P5Yeat%2FmS6HAhdFnRHZiuF6kZ5oVYohjD12WjmDDjGvNhiUSZ%2BprUStY%2BgnaJ86VZAWgMyGaVvhmYULzSqJzzyN0yORGbUdB4%2BC5wx7IS352YEHTAquiG6WMtqIWHBhP5pEg2K%2BgfMxkaACzoB8IlAXTeGQ%3D%3D)
- [fglg2-REVIEW-ONLY-not-production.zip](https://cdn2.flux.ai/flux-comment-files/files/commentFileId-12bde9e656cf2838c1ece0213e9e8b8bc495532912203dfb2285e770530500f6.zip?GoogleAccessId=fleet-agent-worker%40graviton-mvp.iam.gserviceaccount.com&Expires=4946839614&Signature=fjLZIXgy34uJ0cG421wqb5ujvpRyFCRvaIeku%2F2rw8rqTq0%2FUoqAucrmKYlxUIzknmGZd41sDH892tr8U08U4fkM89m2YscJsTy57io7i%2BXMfz0Ql1%2BYMN1w6HUO54DdZccP6t7xivJEoHvXo1YAsBd3LS4pPWM2hLv5v7La0wTTfb8JXrx51n4NbmQiKuhU29vmIIaJVrnyy1OLowNfmUVQUY4xz88AWAI6b%2B%2FDoZ0GREKy%2FSbpLDA%2BGa9rVUR16%2BzaLiajl4eRaGyAxaUzQNPdIoJz4cgdPynTR0BCJJ8efhR9m%2BoH1dCCzAzuuJTsI3dgIA429VJpi5nUOhw8KQ%3D%3D)

## 1. Connectivity and DRC findings

### Check table
| Check | Result | Notes |
|---|---|---|
| Native airwires / overlapping copper / ERC | Pass (0/0/0) | Evidence, not full release proof |
| Native switching power stage | **4 errors, 2 warnings** | C2/C3 placement vs U2 (see P1-1) |
| Native component outside board | 5 warnings | J1, H1–H4 body only |
| Native silk label overlap | 39 warnings | Labels over pads |
| Native redundant copper | 83–88 groups (varies by run) | Mostly GND stitching; do not bulk delete |
| Gerber geometry check (flux-gerber-check) | **Fail** | Geometry only; cannot prove absence of opens/shorts |
| – min copper gap (baseline 0.2 mm generic assumption, no fab) | Warn | 0.121 mm top at (37.56, 5.74), same-net GND via to J1 shield; 0.19997 mm J1 VBUS–GND pad pitch (rounding) |
| – silk over mask openings | Fail | 109 regions, 6.1 mm², mostly U2 thermal pad |
| – outline | Pass | 90.05 × 60.05 mm |
| KiCad DRC (kicad-cli) | **FAIL / 280 unresolved** | 0 unconnected; 8 short flags from netless TP polygons (export artifact); 23 starved_thermal and 19 sliver findings unverified |
| Placement check | Pass | 62 rows, 0 outside; U1, D1 excluded from PnP; 12 connector origin offsets to confirm with assembler |
| gerbv renders | Pass (visual) | Bottom has JLCJLCJLCJLC order-number placeholder |
| IPC-356 | Pass with note | `fglg2.d356` contains 6 testpoint 327 records with correct nets, refdes shown as `-1` |
| Mask bridge / sliver, annular ring & drill-to-copper from fab files, paste/stencil, actual copper thermal | **Not run** | No fab profile; requires fab CAM |

### Prioritized findings
**P0 (release blocker)**
- **P0-1 BOM grouping (confirmed).** Components already carry real MPN/Manufacturer/LCSC/Datasheet properties (e.g. L1/L2 SWPA8040S100MT Sunlord C37429 10 µH; D5 SS36 LGE C2903825; D4 SS14 MDD C2480; C4 CL31B106KBHNNNE 10 µF 50 V C89632; C5 GRM32EC72A106KE05L 10 µF 100 V Murata C576517; C6 CL10B104KC8NNNC 100 nF 100 V; F1 SMD1812B150TF/8 Brightking C269137; J1 TYPE-C-31-M-12 HRO C165948; D1 SMF6.0A Jingdao C178260; U1 Seeed 113991054). But `fglg2-bom.csv` groups rows by part UID, merging different parts: C1–C16 has six MPN/value variants in one row; D4/D5 are one row. BOM must be normalized and split by MPN before PCBA. TPs and mounting holes need no procurement MPN.

**P1**
- **P1-1 Input capacitor placement (native errors, confirmed; performance significance conditional).** C2/C3 bank orientations differ and are split 11 mm; C3 hot loop 19.7 mm vs 10.4 mm floor; GND gaps C2 14.5 mm, C3 9 mm; C3.1→C2.1 +5V trace 16.6 mm. The schematic adapts TPS61500 as SEPIC; the datasheet describes a boost topology [^flux:cite:src_md_e3793a13b242cda9], so guidance applies by analogy. A continuous SEPIC input current does not excuse a distant C3 VIN bypass. Datasheet asks for a ground plane and short SW path [^flux:cite:src_md_52d1b914c6cd098d].
- **P1-2 U2 exposed pad (not verified good).** EP must connect to analog ground with thermal vias [^flux:cite:src_page_3_tr_td_thermal_pad_td_td_td_td_td_td_solde_516df29e3d]; θJA 45.2 °C/W, θJC(bottom) 5.8 °C/W [^flux:cite:src_page_5_table_tr_td_rowspan_3_colspan_2_thermal_m_a1c3007d1a]. KiCad starved_thermal includes U2 pad 15_16 bottom with 1 spoke vs 2; must be reconciled against actual Gerber copper. Via tenting/plugging, stencil windowpane and solder-wicking risk not verified. Bottom EP exposure / metal enclosure isolation conditional.
- **P1-3 Feedback sense routing (conditional).** No dedicated Kelvin return from R20/R21 to U2. FB reference 200 mV typ (195–205 mV) [^flux:cite:src_md_c2882317d2052ac5]. Nominal setpoints ILED = V_FB / R_sense ≈ 0.2 V / 0.82 Ω ≈ 244 mA (or 488 mA if two senses in parallel) — setpoints only, not validated loads.
- **P1-4 Component stress verification not done.** Ratings are known. C4 DC bias is VIN; output C5/C6 see VOUT; diode D5 and SW node stress ≈ VIN + VOUT plus overshoot. Abs max SW 40 V, VIN 20 V [^flux:cite:src_page_4_table_tr_td_td_td_min_td_td_max_td_td_uni_2c263e7148]; current limit 3 A min / 3.8 A typ, OVP 1.229 V typ [^flux:cite:src_page_6_table_tr_td_colspan_2_parameter_td_td_tes_9f6ced657f]. Stress, ripple and thermal margin require LED string voltage and current mode.
- **P1-5 Copper widths.** 0.4 mm neck on VBUS_F near Q2. Width/current margin unknown pending loads, copper weight and temperature; no fixed width prescribed.

**P2**
- 0.121 mm same-net gap at J1: minimum-feature question for the selected fab, not a short or universal fail.
- Silk over U2 thermal pad and 39 label-over-pad hits (will be clipped).
- Mounting holes H1–H4: center-to-edge 3.5 mm; NPTH confirmed by drill attribute; screw copper clearance and head keepout unverified.
- 8 acute trace joints (no acid traps), e.g. /ADC_POT (-31.2,-13.175) 17.4°.
- TP mapping: TP4 = +3V3, TP5 = /RADAR_OT2.
- KiCad export: TP polygons netless (8 short flags) — export issue only.

### Contradictions resolved
- **U1 absent from layout:** intentional, Exclude from PCB; XIAO plugs into sockets J9/J10. The XIAO ESP32C3 uses an external U.FL antenna (Seeed wiki: https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/), not an onboard PCB antenna. The carrier has no RF trace; antenna cable/FPC placement and metal clearance still needed. Radar module antenna mechanics remain conditional.
- **GND area figure:** fill outline is a full 90 × 60 rectangle counted as area; Gerber copper is clipped to the board edge.
- **J1:** power-only USB-C; no D+/D- nets.

### Margin table (baseline assumptions, no fab selected)
| Item | Measured | Baseline (generic, not vendor) | Verdict |
|---|---|---|---|
| Top copper gap | 0.121 mm (same net) | 0.2 mm | Warn |
| Bottom copper gap | 0.282 mm | 0.2 mm | Not verified vs fab |
| Outline | 90.05 × 60.05 mm | — | Pass |
| Thermal (U2) | — | — | Not verified |
| Trace ampacity | — | — | Not verified |

## 2. Routed critical nets
None. No USB data, RF or controlled-impedance nets exist on the carrier (J1 power-only, XIAO antenna external U.FL). No EM simulation run.

## 3. Repair plan (not executed)
1. **Placement:** move C3 (and C2) adjacent to U2 VIN/GND with short GND return; tighten D5/C5/C6 output loop; confirm screw keepouts at H1–H4.
2. **Connectivity:** add Kelvin sense return R20/R21 → U2; reconcile U2 EP thermal spokes/vias against Gerbers.
3. **Clearances:** resolve 0.121 mm J1 feature per selected fab; widen VBUS_F neck once loads known; move silk off pads/EP.
4. **Release:** normalize BOM and split by MPN; remove order-number placeholder unless fab uses it; run fab CAM (mask, annular ring, paste); confirm PnP origins; decide D1 population (kept excluded by default).

**Decisions only the user can provide (block validation/release, not this review):** LED string voltage + current mode + ambient (no safe default); fab/assembler (no vendor default); enclosure and antenna cable/FPC clearance (default: insulated open-bench prototype only). Existing MPNs retained by default.

## Resolution (2026-10-28)

| Finding | Verdict | Done |
|---|---|---|
| P0-1 BOM rows merge different parts | Flux's own BOM export, not ours: `fgl_g2/jlcpcb/fgl_g2-bom-jlcpcb.csv` has 39 rows, one per LCSC part, and every placed part has its MPN, manufacturer, LCSC number and datasheet | None |
| P1-1 Input caps C2/C3 far from U2 | Not a problem for a SEPIC. The input current flows continuously through L1, so the 10 µF bulk cap C2 belongs at L1's +5V pad, where it is. VIN only supplies the controller (a few mA); its 100 nF decoupler C3 is 3.3 mm from the VIN pin. The fast-switching loop is on the output side (next row) | None |
| Switching-loop tightening (repair plan item 1) | Worth doing: it is the loop that carries the switched current edges | Loop U2 SW → C4 → D5 → C5 → GND → PGND: C4 under L1, D5 vertical below C4, C5/C6 beside D5's cathode over solid B.Cu ground. About 52 mm² enclosed instead of 74, perimeter 35 mm instead of 41, C5 GND to PGND 7.6 mm instead of 10.5. Courtyard gaps in the loop now 0.35–0.5 mm |
| P1-2 U2 exposed pad starved (1 spoke) | Import artefact: on the board, pad 15 and its 16 thermal vias (0.3/0.6 mm) connect solidly to both pours (`zone_connect 2`), no spokes. Vias are tented both sides. Stencil and thermal are JLCPCB's standard for the footprint | None; G2-T3 runs the driver at full load |
| P1-3 No Kelvin FB return | FB is already a separate 0.25 mm trace from R21's pad, routed first and kept off the LED_RTN bus (D19). The sense resistors and U2 share the solid ground pour | None |
| P1-4 Stress not verified | Done in D3 (`sepic_design.py`): switch node 33.5 V typical, 35.1 V worst case, against 40 V; D5 SS36 60 V; C4 50 V; C5 100 V (3.4× worst-case OVP). String up to 24 V, 244/488 mA ceiling, 5 W cap | None |
| P1-5 0.4 mm neck on VBUS_F | The neck is the branch to Q2's gate network (R13 ∥ C16), which carries no load current; the power path F1 → Q2 → +5V is wide copper | None |
| J1 0.121 mm same-net gap | Real: two GND vias 0.12 mm from J1's shield pads, under JLCPCB's 0.2 mm | Router now keeps vias 0.25 mm from through-hole pads as well as SMD pads. The vias are now 0.35 mm from the shield |
| Silk over the U2 thermal pad, 39 labels over pads | KiCad DRC reports no silkscreen-over-pad or overlap warnings on the board; JLCPCB clips silkscreen at mask openings anyway | None |
| Mounting holes | KiCad's `MountingHole_3.2mm_M3` (NPTH, no pad), 3.5 mm from each edge; the pours keep their clearance. Screw and standoff to be chosen with the frame | None |
| Acute trace joints | Accepted: modern etching does not trap acid at these angles | None |
| JLCJLCJLCJLC on the bottom silkscreen | Intentional: JLCPCB's order-number placeholder, so the number is printed there and not somewhere visible | None |
| Netless TP polygons, IPC-356 refdes `-1`, outside-board warnings for J1 and H1–H4 | Import or export artefacts; J1 overhangs the edge by design | None |
| Decisions Flux asked for | String: 1–4 filaments in series, 2.7–24 V, OVP 27.7 V. Constant current with analog dimming, 244 or 488 mA ceiling (JP1), firmware default 150 mA, 5 W cap. Input 4.5–5.25 V USB-C, up to about 1.4 A. Ambient up to 55 °C behind the glass. Fab and assembly: JLCPCB, 2 layers, 1.6 mm, 1 oz, standard PCBA. D1 stays unfitted (G2-T6). The XIAO's antenna is unused: the firmware turns no radio on | Recorded here |
