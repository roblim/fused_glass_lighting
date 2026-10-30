# G2 layout generator

These scripts produced the Rev G2 placement and routing in `../../kicad/fgl_g2/fgl_g2.kicad_pcb` (2026-10-23).
The KiCad file is now the source of truth, so edit it in KiCad. The scripts are kept so the reasoning can be reproduced.

| File | What |
|---|---|
| `fgl_g2_unplaced.kicad_pcb` | Input: the board KiCad 9 created from the schematic, before placement. Two patches were made: the port courtyards match the current `fgl.pretty` footprint, and the U2 thermal vias are 0.3 mm drill / 0.6 mm pad (the library has 0.2 / 0.5) |
| `place.py` | Every footprint position and rotation. Board-local mm on a 74 × 58 mm board; origin = KiCad (100, 100) |
| `hand.py` | Hand-routed copper: USB-C VBUS/CC escapes, fuse → P-FET → +5V spine, SEPIC power stage (SW, SEP_B, VOUT), controller pin escapes, port chain and LED_RTN bus |
| `router.py` | 2-layer grid maze router, 0.1 mm grid, 0.2 mm clearance + margin |
| `build.py` | Places, hand-routes, maze-routes everything else (power nets first, wide), drops a GND via at every GND pad and adds stitching vias. Keeps auto-routed copper off B.Cu under the switching loop |
| `emit.py` | Writes tracks, vias, both GND pours, outline (1.5 mm corners), silkscreen and reference placement. Renames nets to the schematic's names (`/VOUT`, `/KA_D`, …) |
| `render.py`, `show.py` | Matplotlib previews and courtyard-overlap check |

Run:

```
cp fgl_g2_unplaced.kicad_pcb orig.kicad_pcb
python3 build.py && python3 emit.py out.kicad_pcb
```

Then fill the zones in KiCad 9 (B in pcbnew, or the swig `ZONE_FILLER`) and run DRC. Zones are written unfilled.
