"""Move the board name and the port-wiring warning to the clear upper-right corner (2026-10-29).

usage: move_titles.py board.kicad_pcb

They sat cramped at the top left, between J5, TP3, TP4 and C11. The upper right, between J8 and
the H2 mounting hole and above the USB input, was empty apart from tented stitching vias. The
board name and revision go at the top of that corner and the warning below them. The warning
grows to 1.0 mm text with a 0.18 mm stroke so it stands out; the name stays 0.9 mm because at
that height it must fit between J8 and the H2 hole (16 mm). Each new spot is checked clear of
pads (0.2 mm), other silkscreen (0.15 mm) and the board edge with `refspots.py`'s rules.
Edits the KiCad file as text: only each text's position, size and stroke lines change.
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geom import Board, OX, OY
from refspots import obstacles, clear, tbox

X = 74.9                     # centre line of the corner block (J8 body ends at 66.35, H2's at 83.05)
NEW = {   # text: (centre x, centre y, size, stroke), mm from the board's top-left corner
    'FUSED GLASS LIGHTING': (X, 2.6, 0.9, 0.15),
    'rev G2  2026-10':      (X, 4.0, 0.8, 0.15),
    'SWITCH OFF BEFORE':    (X, 8.9, 1.0, 0.18),
    'WIRING PORTS':         (X, 10.5, 1.0, 0.18),
}

path = sys.argv[1]
t = open(path).read()
b = Board(path)
pads, texts, segs = obstacles(b, [])
old = {}
for name in NEW:
    m = re.search(r'\(gr_text "%s"\n\t\t\(at ([\d.]+) ([\d.]+)' % re.escape(name), t)
    old[name] = (float(m.group(1)) - OX, float(m.group(2)) - OY)
# leave the four texts themselves out of the obstacles
moving = [tbox(x, y, n, 0.9 if 'FUSED' in n else 0.8, 0) for n, (x, y) in old.items()]
texts = [(o, bx) for o, bx in texts if not any(abs(bx[0] - m[0]) < 0.3 and abs(bx[1] - m[1]) < 0.3 for m in moving)]
for name, (x, y, size, th) in NEW.items():
    bx = tbox(x, y, name, size, 0)
    ok = clear(bx, pads, texts, segs)
    print(f'{name:22} ({x}, {y}) {size} mm  box x {bx[0]:.2f}-{bx[2]:.2f} y {bx[1]:.2f}-{bx[3]:.2f}  {"clear" if ok else "NOT CLEAR"}')
    assert ok, name
    texts.append(('_', bx))
    pat = (r'(\(gr_text "%s"\n\t\t\(at )[\d.]+ [\d.]+( 0\)\n\t\t\(layer "F.SilkS"\)\n\t\t\(uuid "[^"]+"\)\n'
           r'\t\t\(effects\n\t\t\t\(font\n\t\t\t\t\(size )[\d.]+ [\d.]+(\)\n\t\t\t\t\(thickness )[\d.]+\)') % re.escape(name)
    t, n = re.subn(pat, lambda m: f'{m.group(1)}{x + OX:g} {y + OY:g}{m.group(2)}{size:g} {size:g}{m.group(3)}{th:g})', t)
    assert n == 1, (name, n)
open(path, 'w').write(t)
