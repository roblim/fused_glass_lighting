"""Find silkscreen spots for the references that are not on F.SilkS.

usage: refspots.py board.kicad_pcb out.kicad_pcb REF [REF ...]
Used 2026-10-28 for C2, C4, C15, JP2, R13, R15, R16; apply_refs.py then copies the result into the
KiCad-formatted board. JP2's label is pinned level with the header, on its left.
Obstacles: pads (+0.2), visible silk text and silk graphics (+0.15), board edge (0.5).
Tented vias are not obstacles. Prefers the spot closest to the part's own courtyard
and outside other parts' courtyards.
"""
import sys, math
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geom import Board, rot, OX, OY
from sx import find, find1, Sym
import numpy as np

src, dst, refs = sys.argv[1], sys.argv[2], sys.argv[3:]
b = Board(src)
W, H = 90.0, 60.0
SIZE = 0.8


def tbox(cx, cy, s, size, ang):
    w = len(s) * size * 0.85 + 0.2; h = size + 0.2
    if ang % 180 == 90:
        w, h = h, w
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def ov(a, c, m=0.0):
    return a[0] < c[2] + m and c[0] < a[2] + m and a[1] < c[3] + m and c[1] < a[3] + m


def box_seg_d(bx, ax, ay, bx2, by2):
    # min distance from a box to a segment (sampled)
    best = 9e9
    for t in np.linspace(0, 1, 25):
        x = ax + (bx2 - ax) * t; y = ay + (by2 - ay) * t
        dx = max(bx[0] - x, 0, x - bx[2]); dy = max(bx[1] - y, 0, y - bx[3])
        best = min(best, math.hypot(dx, dy))
    return best


pads = []
for p in b.pads():
    if 'F.Cu' not in p['layers'] and '*.Cu' not in p['layers']:
        continue
    a = math.radians(p['ang'])
    hw = abs(p['w'] / 2 * math.cos(a)) + abs(p['h'] / 2 * math.sin(a))
    hh = abs(p['w'] / 2 * math.sin(a)) + abs(p['h'] / 2 * math.cos(a))
    pads.append((p['ref'], (p['cx'] - hw, p['cy'] - hh, p['cx'] + hw, p['cy'] + hh)))

texts = []   # (owner, box)
segs = []    # (owner, x1, y1, x2, y2, halfwidth)
for ref, fp in b.fps.items():
    fx, fy, fr = b.fp_pos(ref)
    for t in find(fp, 'property') + find(fp, 'fp_text'):
        ly = find1(t, 'layer')
        if not ly or ly[1] != 'F.SilkS' or find1(t, 'hide'):
            continue
        if t[0] == 'property' and ref in refs and t[1] == 'Reference':
            continue
        s = t[2] if t[0] == 'fp_text' else t[2]
        if s == '${REFERENCE}':
            s = ref
        ta = find1(t, 'at')
        dx, dy = rot(float(ta[1]), float(ta[2]), fr)
        sz = float(find1(find1(find1(t, 'effects'), 'font'), 'size')[1])
        ang = float(ta[3]) if len(ta) > 3 else 0.0
        texts.append((ref, tbox(fx + dx, fy + dy, s, sz, ang)))
    for g in fp:
        if not (isinstance(g, list) and g and g[0] in ('fp_line', 'fp_rect', 'fp_arc', 'fp_circle', 'fp_poly')):
            continue
        ly = find1(g, 'layer')
        if not ly or ly[1] != 'F.SilkS':
            continue
        st = find1(g, 'stroke'); w = float(find1(st, 'width')[1]) if st else 0.12
        pts = []
        if g[0] == 'fp_line':
            pts = [(find1(g, 'start'), find1(g, 'end'))]
        elif g[0] == 'fp_rect':
            s_, e_ = find1(g, 'start'), find1(g, 'end')
            x0, y0, x1, y1 = float(s_[1]), float(s_[2]), float(e_[1]), float(e_[2])
            c = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            for i in range(4):
                (ax, ay), (bx_, by_) = c[i], c[(i + 1) % 4]
                pa = rot(ax, ay, fr); pb = rot(bx_, by_, fr)
                segs.append((ref, fx + pa[0], fy + pa[1], fx + pb[0], fy + pb[1], w / 2))
            continue
        elif g[0] == 'fp_arc':
            pts = [(find1(g, 'start'), find1(g, 'mid')), (find1(g, 'mid'), find1(g, 'end'))]
        elif g[0] == 'fp_circle':
            c = find1(g, 'center'); e = find1(g, 'end')
            cx, cy = float(c[1]), float(c[2]); rr = math.hypot(float(e[1]) - cx, float(e[2]) - cy)
            q = [(cx + rr * math.cos(k * math.pi / 6), cy + rr * math.sin(k * math.pi / 6)) for k in range(13)]
            for (ax, ay), (bx_, by_) in zip(q, q[1:]):
                pa = rot(ax, ay, fr); pb = rot(bx_, by_, fr)
                segs.append((ref, fx + pa[0], fy + pa[1], fx + pb[0], fy + pb[1], w / 2))
            continue
        elif g[0] == 'fp_poly':
            q = [(float(v[1]), float(v[2])) for v in find1(g, 'pts')[1:]]
            for (ax, ay), (bx_, by_) in zip(q, q[1:] + q[:1]):
                pa = rot(ax, ay, fr); pb = rot(bx_, by_, fr)
                segs.append((ref, fx + pa[0], fy + pa[1], fx + pb[0], fy + pb[1], w / 2))
            continue
        for s_, e_ in pts:
            pa = rot(float(s_[1]), float(s_[2]), fr); pb = rot(float(e_[1]), float(e_[2]), fr)
            segs.append((ref, fx + pa[0], fy + pa[1], fx + pb[0], fy + pb[1], w / 2))
for g in b.tree:
    if not (isinstance(g, list) and g and g[0] in ('gr_text', 'gr_line', 'gr_rect')):
        continue
    ly = find1(g, 'layer')
    if not ly or ly[1] != 'F.SilkS':
        continue
    if g[0] == 'gr_text':
        a = find1(g, 'at'); eff = find1(g, 'effects')
        sz = float(find1(find1(eff, 'font'), 'size')[1])
        ang = float(a[3]) if len(a) > 3 else 0.0
        bx = tbox(float(a[1]) - OX, float(a[2]) - OY, g[1], sz, ang)
        if find1(eff, 'justify'):
            w_ = bx[2] - bx[0]; bx = (bx[0] + w_ / 2, bx[1], bx[2] + w_ / 2, bx[3])
        texts.append(('_', bx))
    elif g[0] == 'gr_line':
        s_, e_ = find1(g, 'start'), find1(g, 'end')
        segs.append(('_', float(s_[1]) - OX, float(s_[2]) - OY, float(e_[1]) - OX, float(e_[2]) - OY, 0.075))

crt = {r: b.courtyard(r) for r in b.fps if not r.startswith('H')}


def gap(bx, c):
    dx = max(c[0] - bx[2], 0, bx[0] - c[2]); dy = max(c[1] - bx[3], 0, bx[1] - c[3])
    return math.hypot(dx, dy)


results = {}
for ref in refs:
    c = crt[ref]
    best = None
    PIN = {'JP2': ((c[1] + c[3]) / 2, 'left')}     # beside the header, level with it
    for ang in (0.0, 90.0):
        xs = np.arange(c[0] - 3.5, c[2] + 3.5, 0.1); ys = np.arange(c[1] - 3.5, c[3] + 3.5, 0.1)
        if ref in PIN:
            if ang: continue
            ys = [PIN[ref][0]]; xs = np.arange(c[0] - 2.5, c[0], 0.05)
        for x in xs:
            for y in ys:
                bx = tbox(x, y, ref, SIZE, ang)
                if bx[0] < 0.5 or bx[1] < 0.5 or bx[2] > W - 0.5 or bx[3] > H - 0.5:
                    continue
                if any(ov(bx, pb, 0.2) for _, pb in pads):
                    continue
                if any(ov(bx, tb, 0.15) for _, tb in texts):
                    continue
                if any(box_seg_d(bx, *s[1:5]) < s[5] + 0.15 for s in segs
                       if ov(bx, (min(s[1], s[3]), min(s[2], s[4]), max(s[1], s[3]), max(s[2], s[4])), 1.0)):
                    continue
                own = gap(bx, c)
                others = [k for k, cb in crt.items() if k != ref and ov(bx, cb)]
                # ambiguous if it sits closer to another part than to its own
                near_other = min(gap(bx, cb) for k, cb in crt.items() if k != ref)
                score = own * 3 + len(others) * 1.5 + (2.0 if near_other < own else 0) + (0.3 if ang else 0)
                if best is None or score < best[0]:
                    best = (score, round(float(x), 2), round(float(y), 2), ang, own, others)
    results[ref] = best
    print(ref, 'courtyard', [round(v, 2) for v in c], '->', best)
    if best:
        texts.append((ref, tbox(best[1], best[2], ref, SIZE, best[3])))

# write: put each reference on F.SilkS at the chosen spot
for ref, best in results.items():
    if not best:
        continue
    fp = b.fps[ref]
    fx, fy, fr = b.fp_pos(ref)
    prop = [p for p in find(fp, 'property') if p[1] == 'Reference'][0]
    find1(prop, 'layer')[1] = 'F.SilkS'
    h = find1(prop, 'hide')
    if h:
        prop.remove(h)
    lx, ly = rot(best[1] - fx, best[2] - fy, -fr)
    ta = find1(prop, 'at')
    ta[1:] = [round(lx, 3), round(ly, 3), float(best[3])]   # absolute text angle as KiCad stores it
    font = find1(find1(prop, 'effects'), 'font')
    find1(font, 'size')[1:] = [SIZE, SIZE]
    th = find1(font, 'thickness')
    if th:
        th[1] = 0.12
b.save(dst)
