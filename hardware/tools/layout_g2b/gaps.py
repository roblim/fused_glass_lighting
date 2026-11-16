"""Smallest courtyard-to-courtyard gap for every footprint (rework spacing check)."""
from geom import Board
from place import PLACE
b = Board('orig.kicad_pcb')
for r, (x, y, a) in PLACE.items():
    b.place(r, x, y, a)
refs = [r for r in b.fps if not r.startswith('H')]
C = {r: b.courtyard(r) for r in b.fps}
def gap(A, B):
    dx = max(B[0] - A[2], A[0] - B[2], 0); dy = max(B[1] - A[3], A[1] - B[3], 0)
    return (dx * dx + dy * dy) ** 0.5
rows = []
for r in refs:
    g = min((gap(C[r], C[o]), o) for o in b.fps if o != r)
    rows.append((round(g[0], 2), r, g[1]))
rows.sort()
for g, r, o in rows[:30]:
    print(f'{g:5.2f}  {r:4s} - {o}')
