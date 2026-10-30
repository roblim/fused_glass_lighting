"""Move silkscreen references to hand-chosen spots (2026-10-28 clarity pass), checking each is clear.

usage: relabel.py board.kicad_pcb placed.kicad_pcb
then:  apply_refs.py placed.kicad_pcb board.kicad_pcb <refs printed>
       silk_tidy.py board.kicad_pcb        (0.15 mm text strokes, three pin legends spread)
       labelcheck.py board.kicad_pcb       (every reference against its neighbours)

Each entry lists candidate spots (centre x, y in mm from the board's top-left corner, text angle)
in order of preference; the first one clear of pads (0.2 mm), other silkscreen (0.15 mm) and the
board edge (0.5 mm) is used. Then labelcheck.py confirms every moved reference is nearer its own
part than any other.

- R19 sat left of C9, nearer C9 than R19. The C9 / R19 / R16 / R15 row now has every reference
  directly below its own part, in one line; R19 and R15 are set 0.4 mm outward so the three
  R labels don't run together.
- R25 ... R22 and C15 (the row under the XIAO, 2.4 mm pitch): horizontal references ran together
  ("R25R24"); they now stand vertically above each part.
- JP2: its reference was squeezed against C10's pad; now vertical, against the header's left end.
- R12: its reference sat just under R14's pads; now below R12.
- C3: its reference sat between R18 and U2's label; now above C3.
- R13: sat between Q2 and R13; now on R13's left, in line with C16 and R14 below it.
- C4, C5, C7, R29: moved up to their parts (were 0.7-1.1 mm away, C4's nearer L2 than C4).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geom import Board, rot
from sx import find, find1
from refspots import obstacles, clear, tbox
from labelcheck import labels, check

SIZE = 0.8
ROW_Y = 39.6            # centre of the vertical references above the XIAO resistor row
SPOTS = {
    'C9':  [(40.8, 36.75, 0)],
    'R16': [(45.9, 36.75, 0)],
    'R19': [(43.0, 36.75, 0)],
    'R15': [(48.8, 36.75, 0)],
    'JP2': [(15.65, 29.8, 90)],
    'R12': [(74.6, 36.55, 0), (74.6, 36.75, 0)],
    'C3':  [(46.9, 21.05, 0)],
    'R13': [(71.0, 25.1, 0)],
    'C4':  [(53.5, 30.5, 0)],
    'C5':  [(44.3, 38.7, 0)],
    'C7':  [(37.3, 25.75, 0)],
    'R29': [(19.85, 23.65, 0)],
}
for r in ('C15', 'R25', 'R24', 'R6', 'C12', 'R5', 'R23', 'R22'):
    SPOTS[r] = [(None, ROW_Y, 90), (None, ROW_Y - 0.2, 90)]

src, dst = sys.argv[1], sys.argv[2]
b = Board(src)
pads, texts, segs = obstacles(b, list(SPOTS))
done = {}
for ref, cands in SPOTS.items():
    fx, fy, fr = b.fp_pos(ref)
    for x, y, ang in cands:
        x = fx if x is None else x
        bx = tbox(x, y, ref, SIZE, ang)
        if clear(bx, pads, texts, segs):
            done[ref] = (x, y, ang); texts.append((ref, bx)); break
    else:
        print('no clear spot:', ref)
for ref, (x, y, ang) in done.items():
    fx, fy, fr = b.fp_pos(ref)
    prop = [p for p in find(b.fps[ref], 'property') if p[1] == 'Reference'][0]
    lx, ly = rot(x - fx, y - fy, -fr)
    find1(prop, 'at')[1:] = [round(lx, 3), round(ly, 3), float(ang)]
    print(ref, (x, y, ang))
b.save(dst)
L, bad, crt = check(Board(dst), quiet=True)
for ref in done:
    l = L[ref]
    print(f"{ref:4} own {l['own']:.2f}  nearest other {l['near'][1]} {l['near'][0]:.2f}")
print('refs:', ' '.join(done))
