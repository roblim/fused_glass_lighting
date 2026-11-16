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

---

## Second pass (2026-10-29)

Flux re-ran the review with our answers to its four questions (Addendum A below), on its import from 2026-10-28, before the loop, J1-via and silkscreen changes. Kept as Flux wrote it, headings demoted one level; its links are Flux's signed copies.

### PCB Layout and DFM Review (second pass)

> **Session handoff / verification caveat (2026-10-29):** Execution stopped when ACUs ran out. The operating requirements below were recorded, but the latest power reassessment still needs the bounded corrections listed here before its numeric verdicts are relied on. No placement, routing, circuit, BOM selections, manufacturing profile, or stackup were changed this session; D1 remains unfitted. JLCPCB is the intended vendor, but the effective profile remains Custom (no base profile).
>
> **Confirmed correction:** fresh silkscreen check returned **total 39**; a report of four warnings was a paginated subset, not an improvement. The exact 5 W / 488 mA crossover is about **10.246 V**, not the coarse-grid 10.6 V point. The power script at `/root/check/power_envelope.py` on computer `dfm-check` samples only 44 string voltages and must include both exact power/current crossover points before updating worst-case values. Its 80% converter efficiency and 0.5 W housekeeping load are assumptions, not measured performance. A failed assumed scenario does **not** establish that the physical board fails at 5 W. The fuse's estimated 55 °C hold rating and inductor saturation rating came from unvalidated web-table data; manufacturer evidence must be verified before definitive pass/fail claims. In particular, a maximum-column saturation figure is not a guaranteed minimum rating. Compare each inductor's own peak separately, not the sum used for switch current.
>
> **Pending bounded follow-up:** correct/re-run the envelope script at exact crossover points with independent confirmation; validate fuse/inductor evidence and supplier URLs; compare measured geometry against current JLCPCB public capabilities even though no saved Flux profile was found; keep thermal and switch-overshoot checks unverified. Remove the claim that U2's 0.65 mm pitch is the board's finest pitch without checking USB-C. The existing ZIP is a historical review-only package, not geometrically stale merely because requirements changed. Replacing F1 alone cannot solve an input-power shortfall. No remedy is approved.
>
> **Open user clarification:** should every filament combination above 24 V be excluded (recommended/default), despite “any mix” of up to four 12 V filaments implying as much as 48 V? Is 1.4 A a measured draw, power-bank limit, or enforced current cap (temporary default: source limit)? Preserve existing parts and firmware limits until the user approves a change. Before release, select either a lower verified power envelope or substantiate 5 W using efficiency/source-budget measurements and a fuse suitable for the actual 55 °C operating conditions.


Read-only review of fgl_g2 (90 × 60 mm, 2-layer copper, 74 schematic components / 73 layout elements). No placement, routing, circuit or BOM selection was changed. Not a fab DFM approval. **Overall verdict: NOT released for bare-board fabrication or JLCPCB PCBA.** Updated 2026-10-29 with user requirements (Addendum A).

Review artifacts (EDA computer `dfm-check`; REVIEW ONLY, not a production package). Gerber/KiCad/BOM/PnP exports predate Addendum A; geometry unchanged since, so results remain valid but the ZIP is **stale as a package** and must be regenerated for release:
- [gerber-check.json](https://cdn2.flux.ai/flux-comment-files/files/commentFileId-2f021afa85d67653343ced1c90744a4b178de1d947136c5a748ce2632b39239a.json?GoogleAccessId=fleet-agent-worker%40graviton-mvp.iam.gserviceaccount.com&Expires=4946839612&Signature=KHoCwCEmZr6o7C%2Bs3Cd%2FAAad%2FZdTi5kWaMDMO26FMG3XKazPj4pUfU%2B3AgsENmjYNaT%2BBPiVoe0yfP75LYLiom1bayMbuMe%2BqgoXCSdpx6EkVfDgtTbXOPdUPOmWvfOm2BwOFnk1ZN7noQ1xVBtAIl0fGeTclAglrUM6%2F3CtBQCG8k%2Bv4tEh9KI8Qxcv%2FXErTf%2FfOgtNri6XEou2ZbUJLpvTFUZYYDdvwbXnjqhn3Ct7dlCa2%2FCcR8uLRR7tU5QsZG0WRx%2FX2rt5j2AbAa0Za4FjG%2FKYMLbZOpJcLyn3cVPaYsrbhfzilGH8XaUR5bI7Sl7imlaFFlY1N0fPcOIrFg%3D%3D)
- [drc.json](https://cdn2.flux.ai/flux-comment-files/files/commentFileId-39f9eafa4d239ffa970d1b96062b41905f329dce8fd23c22ffa7ec06ec888ca7.json?GoogleAccessId=fleet-agent-worker%40graviton-mvp.iam.gserviceaccount.com&Expires=4946839613&Signature=ng9j50uCtbrLOaw04s464Rcw2jYrVD45JKVUIwKIZJeYFIX7%2FLvqqiBKSBXq5EdpK0MLIzkgp8isJulITXDkL%2Biscxhvj6VL9pqjlbpmsnFgxHDDx38oqXbZGjpwdQqMoAt3i%2Bq4pYZbw5NpWH128yF3gwScpSymd3ajRx6Z5WrChaJTC1L%2BFv5P26Iw5aSk8JKtuUfkYhBeHrETARvWvenQbfA1bqOcpes5mzgHTceMZsLnRPhVMporxr8aniJh1twj3KVmGn7hOnLBTrPCrnrUDBxPyE%2FFBIflDOBw3jjK16lNESvwvYnHz9e0v5BliIaEfSVC0GYzeDyrCKsVAw%3D%3D) (KiCad DRC)
- [placement-check.json](https://cdn2.flux.ai/flux-comment-files/files/commentFileId-f2c12bafeea42bfb2698b0036c298574880892e6cd9828d129fcacc77405fcd9.json?GoogleAccessId=fleet-agent-worker%40graviton-mvp.iam.gserviceaccount.com&Expires=4946839613&Signature=NXu9Xx6TzyBtl%2B84hpHeort3ex4VrcVel%2FrfA7Pg%2FcYJ3sknw2toKCRLQuvGIOI1UYJ0uykyxK64eiwd1vcCZTUuMgVL6z54kjf6VeJsnpD3MpBTcHCg%2Bxf80AERdy5fp%2FYTaV6IaHy6ARcBnzfrpnbp44x94EnM5wvqNC6Q9FlniasxB2mG3GZmUoNOFzTeDvvMAG1EwXofvxmsSew0MmZQgavQjhOg%2BRLhPonVWovLK%2BXyTN9xLY4EG7EQ%2BihzEcb%2FCSJ5Wgd%2FGL7FHS6Bd%2F5MmRE6cp6Er3wjR4W7cI0vJiNSC4hyhRAvOEFtlf4PzmCEWO64LY775KZ8%2FO41NQ%3D%3D)
- [top.png](https://cdn2.flux.ai/flux-comment-files/files/commentFileId-3ac81b80badd657d9d84840d3dbd84f57f589e0d5068a4be2e13c942d4f6733a.png?GoogleAccessId=fleet-agent-worker%40graviton-mvp.iam.gserviceaccount.com&Expires=4946839613&Signature=otw3hYxcMpbnq30JzCA5rJge7NaQEljKIZKeCtTbAHPfNHY8oZTcdHBvE4xz5uunKLKBkKC4i3TR%2B07HqpJfzw2v2oW3906kdJur2ZplTPIo%2Bo2Q1%2FF5NGzgRtMB2DxxiS8ZyRAbJahZBV9XrUnAOz6vQ9GszB2s6ydaphn5LAfxSaOdG%2BLVkhvIr7n1wq%2FJrzGfMkviymGrWxXLlEazUHJesFvq74w4vFT%2Fi5Tls38gEx1frS03QhTuAkylqJBrtVRmGuoeJbLLEoDArcb2C7PHz3d2hTw9xxcRNBcel5wbDnCeZtEqgVdoonEvtIeVfshP17bl0NMKL4oSjmtXwA%3D%3D)
- [bottom.png](https://cdn2.flux.ai/flux-comment-files/files/commentFileId-aa258712435b34c5cddec3aa01b09e5bd50770fbba973b4e9d578ee60d4cc7f0.png?GoogleAccessId=fleet-agent-worker%40graviton-mvp.iam.gserviceaccount.com&Expires=4946839614&Signature=rukRIPT949Wgq81qzZDn4JKQWqspHKSLUM7gQePUwA4VPtJ5UZdWX6bACPqrJ59oxzrIe3zq9WxoGUtL4iJuPEZndvv3i9tZN4Xgx%2B2jVSUdOtNBsjV1x93zk6ZLJnX9YeMZvZg2yqB3IlF%2B5yPcjCG5QcOSo7NwVPvUh3csdIyQYo9WCOaIoaiR7o8P5Yeat%2FmS6HAhdFnRHZiuF6kZ5oVYohjD12WjmDDjGvNhiUSZ%2BprUStY%2BgnaJ86VZAWgMyGaVvhmYULzSqJzzyN0yORGbUdB4%2BC5wx7IS352YEHTAquiG6WMtqIWHBhP5pEg2K%2BgfMxkaACzoB8IlAXTeGQ%3D%3D)
- [fglg2-REVIEW-ONLY-not-production.zip](https://cdn2.flux.ai/flux-comment-files/files/commentFileId-12bde9e656cf2838c1ece0213e9e8b8bc495532912203dfb2285e770530500f6.zip?GoogleAccessId=fleet-agent-worker%40graviton-mvp.iam.gserviceaccount.com&Expires=4946839614&Signature=fjLZIXgy34uJ0cG421wqb5ujvpRyFCRvaIeku%2F2rw8rqTq0%2FUoqAucrmKYlxUIzknmGZd41sDH892tr8U08U4fkM89m2YscJsTy57io7i%2BXMfz0Ql1%2BYMN1w6HUO54DdZccP6t7xivJEoHvXo1YAsBd3LS4pPWM2hLv5v7La0wTTfb8JXrx51n4NbmQiKuhU29vmIIaJVrnyy1OLowNfmUVQUY4xz88AWAI6b%2B%2FDoZ0GREKy%2FSbpLDA%2BGa9rVUR16%2BzaLiajl4eRaGyAxaUzQNPdIoJz4cgdPynTR0BCJJ8efhR9m%2BoH1dCCzAzuuJTsI3dgIA429VJpi5nUOhw8KQ%3D%3D)
- [power_envelope.py](https://cdn2.flux.ai/flux-comment-files/files/commentFileId-da973e25bf78e3a1b0f73c66336a06c53b7647ef6a8c01af7ee6f3c92cee59d5.py?GoogleAccessId=fleet-agent-worker%40graviton-mvp.iam.gserviceaccount.com&Expires=4946842046&Signature=Yl7ok9CT91Hh36yEkofD8eIs%2FnhVoRjpH0rIkesR6mJGo%2B9R6m0NAIV0GiabsPAoj238FmqSdigVqx0T6xHmoHFAQR%2FbcHLRm5FoK5a52B8Jq0KasTQnfQcfg55nqdDxcGeYrLfH0YmKkLR7t5QVSYLqV2FGWlvgEaOGox07yPW5WHwtBxDZtpY9zGTVaHppcuacwonfjhf%2Bh26t3ZJ8ucvfpj7US4nZfy4ZiVSezeAxsm9suNZ0rEN8krsaPyShctnLxQKGZSJkdGBJgASMNok7g3mBVPSy7vps5dDzYuzRN02M8Yay2QCp3ktg6SmYUiRfDkPriW%2FRpx5XFAQNTg%3D%3D) / [power_envelope.txt](https://cdn2.flux.ai/flux-comment-files/files/commentFileId-d6bd198e133878031c273db9b7c0279a3bbf164c00c45c6410f2feebd1ba710e.txt?GoogleAccessId=fleet-agent-worker%40graviton-mvp.iam.gserviceaccount.com&Expires=4946842045&Signature=PBu9pzFUHfddnhHPrR72lFnK2tM9u%2FZEf1SGCQQZnt%2Fh31Z61yJ6OXmzw1jmKEhzD8zVkchrdGh%2BuV2qGyyNYYKGrNiaZKpdG9tGdkIBI5mY3J%2B8ijEZVYn29b0BqsAb3KeLzqVGxcWgVeUm3%2FfjIrkADZJl6WmG3yFz2ZiH7mAogNFLKTohUA0lZaMzwJPyZs8EkpapOhsenl0jSE80tFqpcGMJvkRrbAaN9ZltbAdTRmPkr045wFKhPWcrANiyF8Ds6R2QEp5jIoegmJ7NfHgNHtq1mQEWIeYWv9RVtTE5qs87PDdP9katyLCREuH1mlfJmBG4cKPUvdzre%2FWuZA%3D%3D) (Addendum A scripted check)

#### 1. Connectivity and DRC findings

##### User requirements (sourced from user, 2026-10-29)
- One series string of 1–4 filaments, any mix of 3 V / 12 V types; stated supported string 2.7–24 V; OVP 27.7 V nominal.
- Constant-current analog dimming via filtered DIMC. JP1 2–3 ceiling 244 mA; JP1 1–2 ceiling 488 mA; firmware default 150 mA; firmware LED output-power cap 5 W.
- USB-C power-bank input 4.5–5.25 V, about 1.4 A maximum input.
- Ambient 55 °C inside closed glass-front frame; board may face either direction.
- JLCPCB fab + Standard PCBA, 2 copper layers, 1.6 mm FR4, 1 oz; lead-free HASL or ENIG acceptable. THT push-in ports/sockets intended.
- D1 left unfitted. User statement: D1 starts at 6.67 V and cannot protect XIAO 5V (rationale not independently validated). Proposed test pointer: existing test G2-T6 checks the XIAO 5V pin (not run/passed).
- WiFi/Bluetooth unused; XIAO antenna connector intentionally empty. Radar looks out through the glass.

**Spec contradiction (open):** four 12 V nominal filaments ≈ 48 V conflicts with the 2.7–24 V supported range. Default: combinations above 24 V are prohibited; OVP 27.7 V is a fault limit, not an operating allowance. No redesign attempted.

##### Manufacturing target (Addendum A)
- Before/after: manufacturing profile **Custom (no base profile)**, stackup slot **none**. **No change applied (diff: none).**
- Reason: the library has no JLCPCB manufacturing profile and no JLCPCB 2-layer stackup (only JLC 4-layer stackups and generic Flux profiles). Applying a generic profile would replace the project's custom `Via size` ruleset (0.6/0.3 mm) without representing JLCPCB. The layout stackup already matches the requested build: Standard 2 Layer, 1.499 mm core (≈1.6 mm finished), 35 µm (1 oz) copper, imported vias 0.8/0.4 and 0.6/0.3 mm.
- Finish default: lead-free HASL recorded as economical default (finest pitch is U2 HTSSOP 0.65 mm, generally HASL-compatible); ENIG acceptable if the assembler prefers flatter pads for the EP. Not a fab-confirmed choice.
- JLCPCB Standard PCBA THT capability for J9/J10 sockets and push-in ports is **not verified**; confirm per part at order time.

##### Check table
| Check | Result | Notes |
|---|---|---|
| Native airwires / overlapping copper / ERC (fresh 02:47Z) | 0 / 0 / 0 | Evidence, not full release proof |
| Native switching power stage (fresh) | **4 errors, 2 warnings** | C2/C3 vs U2 (P1-1) |
| Native component outside board (fresh) | 5 warnings | J1, H1–H4 body only |
| Native silk label overlap (fresh) | 4 warnings this run (R27, R24, C11, R28); 39 in earlier run | Labels over pads |
| Native redundant copper | 83–88 groups | Mostly GND stitching; do not bulk delete |
| Gerber geometry check | **Fail** | Geometry only; cannot prove absence of opens/shorts |
| – min copper gap | Warn | 0.121 mm top at (37.56, 5.74), same-net GND via to J1 shield; 0.19997 mm J1 VBUS–GND pad pitch. No JLCPCB Flux profile, so judged against JLCPCB's public capability only as unverified reference; same-net features are not clearance violations but are a minimum-feature/CAM question |
| – silk over mask openings | Fail | 109 regions, 6.1 mm², mostly U2 thermal pad |
| – outline | Pass | 90.05 × 60.05 mm |
| KiCad DRC | **FAIL / 280 unresolved** | 0 unconnected; 8 short flags from netless TP polygons (export artifact); 23 starved_thermal and 19 sliver unverified |
| Placement check | Pass | 62 rows, 0 outside; U1, D1 excluded from PnP; 12 connector origin offsets to confirm |
| gerbv renders | Pass (visual) | Bottom JLCJLCJLCJLC order-number placeholder (JLC uses this; keep) |
| IPC-356 | Pass with note | 6 testpoint records with correct nets, refdes `-1` |
| Power envelope (scripted, Addendum A) | **Fail** (input budget, F1) | See table below |
| Mask bridge/sliver, annular ring & drill-to-copper from fab files, paste/stencil, copper thermal, enclosure thermal at 55 °C | **Not run** | Needs fab CAM / bench test |

##### Power envelope check (Addendum A, scripted)
Method: SEPIC CCM waveforms sampled at 400 and 800 points/period plus an independent closed form (Iin+Iout+ΔI); difference 0.000 % (triangular waveforms are exact). Operating envelope ILED = min(JP ceiling, 5 W / Vstring), Vstring 2.7–24 V, worst Vin 4.5 V, L = 8 µH (10 µH −20 %).

Inputs: user values above; FB 200 mV [^flux:cite:src_md_c2882317d2052ac5]; current limit 3 A min [^flux:cite:src_page_6_table_tr_td_colspan_2_parameter_td_td_tes_9f6ced657f]; SW 40 V abs max [^flux:cite:src_page_4_table_tr_td_td_td_min_td_td_max_td_td_uni_2c263e7148]; fSW ≈ 1.2 MHz from R19 = 82 kΩ vs datasheet table 80 kΩ → 1200 kHz [^flux:cite:src_page_10_table_tr_td_r4_k_td_td_f_sub_sw_sub_khz__90f5d8815a]; Q2 RDS(on) 60 mΩ max at −4.5 V [^flux:cite:src_md_c96ea7f58d0f2a72]. Web evidence (not Flux-validated datasheet citations): SWPA8040S100MT Isat 3.6 A max-col / Irms 3.3 A / DCR 38 mΩ (Sunlord table via distributor); SMD1812B150TF/8 hold 1.50 A @23 °C, 1.10 A @50 °C, 1.02 A @60 °C → 1.06 A @55 °C interpolated, R1max 0.12 Ω (Brightking table); SS36 60 V, 0.75 V @3 A. **Assumed:** efficiency 80 % (datasheet says up to 93 % [^flux:cite:src_md_139f1b1a2f80c57e]); housekeeping 0.5 W (XIAO + radar + misc); Q2 hot factor 1.4.

Setpoints: Vstring 3 V → 244/488 mA; 12 V → 244/417 mA; 24 V → 208 mA (5 W cap); firmware default 150 mA at 24 V = 3.6 W (not full max). Worst current case Vstring ≈ 10.6 V, ILED 0.471 A (5 W / 488 mA crossover), D = 0.72, Iin(conv) 1.415 A, ΔI 0.34 A.

| Check | Demand | Capacity | Margin | Verdict | Reason |
|---|---|---|---|---|---|
| Switch peak vs TPS61500 limit 3 A min | 2.22 A | 3.0 A | 1.35 | warn | >1.2 but η assumed |
| Inductor peak vs Isat | 2.22 A | 3.6 A | 1.62 | warn | web source, η assumed |
| L1 RMS vs Irms | 1.42 A | 3.3 A | 2.33 | warn | assumed η |
| SW node, 24 V string | 30.2 V | 40 V | 1.32 | ok | excludes ringing (not measured) |
| SW node at OVP 27.7 V nominal | 33.7 V | 40 V | 1.19 | warn | OVP tolerance + ringing unmeasured |
| D5 reverse | 33.7 V | 60 V | 1.78 | ok | |
| Input power vs 4.5 V × 1.4 A | 6.87 W | 6.30 W | 0.92 | **fail** | needs η ≥ 87.8 % with 0.5 W housekeeping |
| Input current vs F1 hold @55 °C | 1.53 A | 1.06 A | 0.69 | **fail** | still fails at η 88 % (≈1.40 A) |
| Input current vs user 1.4 A | 1.53 A | 1.4 A | 0.92 | **fail** | 1.4 A source (measured / power-bank limit / claim) unknown |

Other results: D5 loss ≤ 0.41 W; Q2 ≈ 0.20 W at 1.53 A (hot); R20/R21 ≈ 0.049 W each at 244 mA (1206); F1 drop up to 0.18 V (board VIN ≈ 4.32 V at 4.5 V source). USB-C: R1/R2 5.1 kΩ CC pull-downs only identify a sink; they do not guarantee 1.5 A/3 A — the board cannot read source advertisement, so ~1.4 A is only safe from sources that advertise ≥1.5 A. Component temperatures at 55 °C ambient: θJA figures (U2 45.2 °C/W [^flux:cite:src_page_5_table_tr_td_rowspan_3_colspan_2_thermal_m_a1c3007d1a], Q2 100–125 °C/W) are reference-board values, not proof for this enclosed PCB → **not verified**.

##### Prioritized findings
**P0 (release blockers)**
- **P0-1 BOM grouping (confirmed).** Parts carry real MPN/Manufacturer/LCSC/Datasheet properties (L1/L2 SWPA8040S100MT C37429; D5 SS36 C2903825; D4 SS14 C2480; C4 CL31B106KBHNNNE 10 µF 50 V; C5 GRM32EC72A106KE05L 10 µF 100 V; C6 CL10B104KC8NNNC; F1 SMD1812B150TF/8 C269137; J1 TYPE-C-31-M-12 C165948; D1 SMF6.0A; U1 Seeed 113991054). `fglg2-bom.csv` groups by part UID (C1–C16 six variants; D4/D5 one row). Normalize and split by MPN before PCBA.
- **P0-2 Input power/fuse at max envelope (confirmed by script, conditional on assumed η/housekeeping).** At 5 W LED and 55 °C, input ≈1.5 A exceeds F1 derated hold (~1.06 A) → nuisance trip expected; also exceeds the 4.5 V × 1.4 A budget unless η ≥ 88 %. Options for the user: lower firmware power cap, or change F1 (BOM decision), then bench-measure.

**P1**
- **P1-1 Input capacitor placement (native errors).** C2/C3 split 11 mm; C3 hot loop 19.7 vs 10.4 mm floor; GND gaps 14.5/9 mm. SEPIC adaptation of a boost datasheet [^flux:cite:src_md_e3793a13b242cda9]; continuous SEPIC input current does not excuse a distant C3. Datasheet asks for a ground plane and short SW path [^flux:cite:src_md_52d1b914c6cd098d]. Peak switch current ~2.2 A at max envelope raises significance.
- **P1-2 U2 exposed pad (not verified good).** EP to analog ground with thermal vias [^flux:cite:src_page_3_tr_td_thermal_pad_td_td_td_td_td_td_solde_516df29e3d]. KiCad starved_thermal U2 pad 15_16 bottom 1 spoke vs 2; tenting/plugging, windowpane paste, wicking unverified. Board may face either way: bottom EP copper to glass/frame isolation conditional.
- **P1-3 Feedback sense routing (conditional).** No dedicated Kelvin return R20/R21 → U2. ILED = V_FB / R_sense ≈ 0.2 V / 0.82 Ω ≈ 244 mA (488 mA with two in parallel) — setpoints.
- **P1-4 Switch-node voltage margin.** 33.7 V at nominal OVP plus unmeasured ringing vs 40 V abs max (margin 1.19). Bench-measure SW overshoot at 24 V string and OVP event. C4 bias = VIN; C5/C6 = VOUT.
- **P1-5 VBUS_F 0.4 mm neck near Q2** carries ~1.4–1.5 A; ampacity/temperature rise at 55 °C not verified (1 oz now known; still needs calculation or bench check).
- **P1-6 Thermal at 55 °C closed frame — not verified** (U2, D5, L1/L2, F1, Q2). Bench test at 5 W in enclosure required.
- **P1-7 Radar through glass (conditional).** Glass transmission, metallic/low-E coatings, standoff and 55 °C radar operation need evidence or bench check.

**P2**
- 0.121 mm same-net gap at J1: CAM/min-feature question only.
- Silk over U2 thermal pad; label-over-pad hits (fresh: R27, R24, C11, R28).
- H1–H4: center-to-edge 3.5 mm, NPTH confirmed; screw copper clearance and head keepout unverified.
- 8 acute trace joints (no acid traps), e.g. /ADC_POT (-31.2,-13.175) 17.4°.
- TP mapping: TP4 = +3V3, TP5 = /RADAR_OT2. KiCad export TP polygons netless (8 short flags) — export issue.
- Operational constraint: with the XIAO antenna connector empty, firmware must never enable WiFi/BLE transmit (no firmware change made).

##### Contradictions resolved
- **U1 absent from layout:** intentional Exclude from PCB; XIAO plugs into J9/J10. XIAO ESP32C3 uses an external U.FL antenna (Seeed wiki: https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/); radios unused, connector empty by design. No carrier RF trace.
- **GND area figure:** fill outline counted as full rectangle; Gerber copper clipped to edge.
- **J1:** power-only USB-C; no D+/D- nets.

##### Margin table (manufacturing)
| Item | Measured | Reference | Verdict |
|---|---|---|---|
| Top copper gap | 0.121 mm (same net) | No JLCPCB Flux profile; JLC public capability unverified | Warn / not verified |
| Bottom copper gap | 0.282 mm | same | Not verified vs fab CAM |
| Outline | 90.05 × 60.05 mm | — | Pass |
| Thermal (U2 etc.) | — | — | Not verified |
| Trace ampacity | — | — | Not verified |

#### 2. Routed critical nets
None. No USB data, RF or controlled-impedance nets on the carrier (J1 power-only; XIAO radio unused, external U.FL empty; radar antenna on module). No EM simulation run.

#### 3. Repair plan (not executed; needs user approval)
1. **Placement:** move C3 (and C2) adjacent to U2 VIN/PGND; tighten D5/C5/C6 output loop; confirm H1–H4 screw keepouts.
2. **Connectivity:** add Kelvin sense return R20/R21 → U2; reconcile U2 EP spokes/vias against Gerbers.
3. **Clearances:** resolve 0.121 mm J1 feature in JLC CAM review; widen VBUS_F neck after ampacity check; move silk off pads/EP.
4. **Power/release:** resolve P0-2 (firmware cap or F1 change, user decision); normalize/split BOM by MPN; regenerate exports (current ZIP stale); confirm THT assembly per part with JLCPCB; run JLC CAM (mask, annular ring, paste); confirm PnP origins; bench tests: SW overshoot, 5 W at 55 °C in frame, radar through glass, G2-T6 XIAO 5V. D1 stays unfitted.

**Remaining user decisions:** (1) filament combinations above 24 V — default prohibited; (2) P0-2 remedy: reduce firmware power cap at low input vs change F1 — default: no change, treat 5 W at 55 °C as unsupported until bench-verified; (3) confirm what the 1.4 A input figure is (measured, power-bank limit, or firmware cap) — default: treat as power-bank limit. Existing MPNs retained; D1 unfitted; finish default lead-free HASL.

### Resolution of the second pass (2026-10-29)

| Finding | Verdict | Done |
|---|---|---|
| P0-2 Input current vs F1 hold at 55 °C | Correct, and new. Brightking's derating table puts the 1.5 A part at about 1.06 A at 55 °C; the 5 W cap draws about 1.25 A at 5 V and up to about 1.4 A at 4.5 V. Flux's 1.53 A uses 80 % efficiency and 0.5 W housekeeping, more pessimistic than our 84 % and about 0.4 W, but the conclusion holds either way | F1 changed to SMD1812B200TF/16 (C269145): 2 A hold, about 1.58 A at 55 °C, 3.5 A trip, same footprint (D12). G2-T2 gains a 1 h run in the closed frame logging input current and F1, Q2, D5, U2, L1 temperatures |
| Input power vs "4.5 V × 1.4 A" | The 1.4 A was our computed draw at the 5 W cap and 4.5 V, not a bank limit | Answered. D7 now notes the bank's USB-C port must supply at least 1.5 A at 5 V for full power; the board can't read the advertisement (Rd only) |
| Spec contradiction: four 12 V filaments = 48 V | Our "1–4 filaments, 2.7–24 V" meant strings up to 24 V total | D2 states it: up to 24 V total, one filament per port. Above that the SEPIC stops at OVP and the firmware reports an open string; nothing is damaged |
| Switch peak 2.2 A vs 3 A limit; SW node 33.7 V at OVP vs 40 V | Agree with the numbers (D3 has 33.5 V typical, 35.1 V worst) | Measured in G2-T2 (peak switch current below 2.5 A) and G2-T4 (SW peaks below 38 V) |
| P1-5 VBUS_F 0.4 mm neck "carries ~1.4–1.5 A" | Not so: rechecked on the board, F1 → Q2 source is 0.8 mm; the 0.4 mm segment is R13 → C16 in Q2's gate network, which carries no load current | None |
| P1-6 Thermal at 55 °C in a closed frame | Not verified by calculation; agree it needs a bench test | Closed-frame run added to G2-T2 |
| P1-7 Radar through glass | Fair: plain glass is fine for 24 GHz, but dichroic and iridized glass carry metal-oxide coatings that can attenuate it | New bring-up test G2-T14; the J4 cable lets the sensor sit where it sees through plain glass |
| Silkscreen over pads (R27, R24, C11, R28), J1 0.121 mm gap, output loop | Flux's import predates the 2026-10-28 fixes | Already fixed: no silkscreen-over-copper or overlap warnings in KiCad DRC; J1 vias 0.35 mm from the shield; loop tightened |
| P0-1 BOM grouping, P1-1 C2/C3, P1-2 U2 EP, P1-3 Kelvin FB, holes, acute joints, netless TPs | Repeats of the first pass | See the first-pass resolution table |
| "Standard PCBA" in Flux's notes | Economic PCBA also handles our through-hole parts for 2–30 boards | Ordering steps in `hardware.md` use Economic |
| Wi-Fi/BLE never enabled with the antenna empty | Agreed; the firmware turns no radio on | None |
