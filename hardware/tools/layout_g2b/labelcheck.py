"""Silkscreen reference clarity check: is each reference nearer its own part than any other?

usage: labelcheck.py board.kicad_pcb [png x0 y0 x1 y1]

For every reference on F.SilkS: the gap from its text box to its own part (courtyard box) and to
the nearest other part, plus size, stroke and angle. A reference is flagged when another part is
as near as its own (within 0.25 mm), when it is more than 1 mm from its own part, when it reads
upside down (180 or 270), or when its text is under 0.8 mm or its stroke under 0.15 mm.
Mounting holes (H*) are not parts here; test points are.
With a png path, also draws the region with each reference joined to its own part.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geom import Board, rot
from sx import find, find1


def tbox(cx, cy, s, size, ang):
    w = len(s) * size * 0.85 + 0.2 - 0.2; h = size     # glyph box (no margin)
    if ang % 180 == 90:
        w, h = h, w
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def gap(a, c):
    dx = max(c[0] - a[2], 0, a[0] - c[2]); dy = max(c[1] - a[3], 0, a[1] - c[3])
    return math.hypot(dx, dy)


def labels(b):
    out = {}
    for ref, fp in b.fps.items():
        fx, fy, fr = b.fp_pos(ref)
        for t in find(fp, 'property'):
            if t[1] != 'Reference':
                continue
            ly = find1(t, 'layer')
            if not ly or ly[1] != 'F.SilkS' or find1(t, 'hide'):
                continue
            ta = find1(t, 'at')
            dx, dy = rot(float(ta[1]), float(ta[2]), fr)
            font = find1(find1(t, 'effects'), 'font')
            sz = float(find1(font, 'size')[1]); th = find1(font, 'thickness')
            ang = float(ta[3]) if len(ta) > 3 else 0.0
            out[ref] = dict(x=fx + dx, y=fy + dy, size=sz, stroke=float(th[1]) if th else sz * 0.15,
                            ang=ang % 360, box=tbox(fx + dx, fy + dy, ref, sz, ang))
    return out


def check(b, quiet=False):
    crt = {r: b.courtyard(r) for r in b.fps if not r.startswith('H')}
    L = labels(b)
    bad = []
    for ref, l in sorted(L.items()):
        own = gap(l['box'], crt[ref])
        near = sorted((gap(l['box'], c), k) for k, c in crt.items() if k != ref)[0]
        why = []
        if near[0] < own + 0.25:
            why.append(f'{near[1]} as near ({near[0]:.2f})')
        if own > 1.0:
            why.append('far from own part')
        if l['ang'] in (180.0, 270.0):
            why.append('upside down')
        if l['size'] < 0.8 or l['stroke'] < 0.15:
            why.append(f"size {l['size']} stroke {l['stroke']}")
        l.update(own=own, near=near, why=why)
        if why:
            bad.append(ref)
        if not quiet:
            print(f"{ref:5} own {own:4.2f}  nearest other {near[1]:5} {near[0]:4.2f}  "
                  f"size {l['size']} stroke {l['stroke']} ang {l['ang']:.0f}  {'; '.join(why)}")
    return L, bad, crt


if __name__ == '__main__':
    b = Board(sys.argv[1])
    L, bad, crt = check(b)
    no = [r for r in b.fps if r not in L and not r.startswith('H')]
    print(f'{len(L)} references on the silkscreen; flagged: {bad}; none: {no}')
    if len(sys.argv) > 2:
        import matplotlib; matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        png = sys.argv[2]; x0, y0, x1, y1 = map(float, sys.argv[3:7])
        fig, ax = plt.subplots(figsize=(14, 14 * (y1 - y0) / (x1 - x0)))
        for p in b.pads():
            w, h = p['w'], p['h']
            if p['ang'] % 180 == 90:
                w, h = h, w
            ax.add_patch(Rectangle((p['cx'] - w / 2, p['cy'] - h / 2), w, h, fc='#e0b060', ec='none'))
        for r, c in crt.items():
            ax.add_patch(Rectangle((c[0], c[1]), c[2] - c[0], c[3] - c[1], fill=False, ec='grey', lw=0.5))
        for r, l in L.items():
            c = crt[r]; bx = l['box']
            col = 'red' if l['why'] else 'black'
            ax.text(l['x'], l['y'], r, ha='center', va='center', fontsize=7, color=col,
                    rotation=l['ang'] if l['ang'] in (90, 270) else 0)
            ax.plot([l['x'], (c[0] + c[2]) / 2], [l['y'], (c[1] + c[3]) / 2], color=col, lw=0.4, alpha=0.5)
        ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect('equal')
        fig.savefig(png, dpi=110, bbox_inches='tight')
