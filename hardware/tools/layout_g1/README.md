# G1 layout generator

Scripts that produced the Rev G1 placement and routing in `../../kicad/fgl_g1/fgl_g1.kicad_pcb` (2026-10-22).
The KiCad file is now the source of truth; edit it in KiCad. These are kept so the reasoning is reproducible.

| File | What |
|---|---|
| `place.py` | Every footprint position/rotation (board-local mm, 66 x 44 board, origin = KiCad (100,100)) |
| `hand.py` | Hand-routed copper: buck cells (Kelvin sense, hot loop), USB-C input, +5V bus, keep-alive, XIAO pin escapes |
| `router.py` | Small 2-layer grid maze router used for the low-current signals |
| `build.py` | Places, hand-routes, maze-routes the rest, adds GND vias and stitching. Input: `fgl_g1_unplaced.kicad_pcb` copied to `orig.kicad_pcb` |
| `emit.py` | Writes tracks, vias, GND pours, XIAO keep-out, outline and silkscreen into a `.kicad_pcb` |
| `render.py` | Matplotlib preview of placement/routing |

Run: `cp fgl_g1_unplaced.kicad_pcb orig.kicad_pcb && python3 build.py && python3 emit.py out.kicad_pcb`,
then open in KiCad 9, fill zones (B) and run DRC. Zones are written unfilled.
