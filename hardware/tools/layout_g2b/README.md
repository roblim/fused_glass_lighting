# G2 layout generator, 90 × 60 mm (D19)

These scripts produced the 90 × 60 mm Rev G2 placement and routing in `../../kicad/fgl_g2/fgl_g2.kicad_pcb` (2026-10-28, decision D19 in `docs/g2_decisions.md`).
The KiCad file is the source of truth, so edit it in KiCad. The scripts are kept so the reasoning can be reproduced. They are the 74 × 58 mm scripts (`../layout_g2/`) with a new placement, the horizontal-entry ports and a few rules added.

| File | What |
|---|---|
| `make_orig.py` | Makes the unplaced input board from the D18 board: keeps every footprint as it was (properties, 3D models, U2's thermal vias, fab text), drops copper, zones and graphics, swaps J5–J8 to the JL212R footprint, C16 to 0603, and adds R29 |
| `place.py` | Every footprint position and rotation on the 90 × 60 mm board; origin = KiCad (100, 100) |
| `gaps.py` | Smallest courtyard-to-courtyard gap for every footprint (rework spacing check) |
| `hand.py` | Hand-routed copper: USB-C VBUS/CC escapes, fuse → P-FET → +5V spine with the R13 ∥ C16 soft start, SEPIC power stage, controller pin escapes, the FB stub and via, port chain (under the port bodies) and LED_RTN bus, R29 → JP2 |
| `router.py` | 2-layer grid maze router, 0.1 mm grid, 0.2 mm clearance + margin; vias kept 0.25 mm clear of SMD pads, same net included |
| `build.py` | Places, hand-routes, routes FB from its via to R21's pad first (Kelvin, kept off the rest of LED_RTN), maze-routes everything else, drops a GND via at every GND pad and adds stitching vias plus one island-fixing via |
| `emit.py` | Writes tracks, vias, both GND pours, outline, silkscreen and reference placement; puts the `/` back on net names |
| `refspots.py`, `apply_refs.py` | Silkscreen reference placement for parts that have none: searches a clear spot by each part (pads, silk text and silk lines kept clear), then copies the result into the KiCad-formatted board without re-serialising it |
| `render.py`, `show.py` | Matplotlib previews and courtyard-overlap check |

Run:

```
cp fgl_g2_unplaced.kicad_pcb orig.kicad_pcb      # the input make_orig.py made from the D18 board
python3 build.py && python3 emit.py out.kicad_pcb
```

Then fill the zones in KiCad 9 and run DRC. Zones are written unfilled. Two fab-layer references (C15, JP2) were hidden by hand afterwards; `emit.py` now does that itself.

On 2026-10-28 every part got a silkscreen reference. `emit.py` had placed C2, C4, R13, R15 and R16 cleanly but left them on F.Fab, because the input board carried them there from the 74 × 58 mm layout; it now moves a placed reference back to F.SilkS. The seven missing references (those five, plus C15 and JP2) were added with:

```
python3 refspots.py ../../kicad/fgl_g2/fgl_g2.kicad_pcb placed.kicad_pcb C2 C4 C15 JP2 R13 R15 R16
python3 apply_refs.py placed.kicad_pcb ../../kicad/fgl_g2/fgl_g2.kicad_pcb C2 C4 C15 JP2 R13 R15 R16
```
