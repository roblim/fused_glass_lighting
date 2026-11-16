"""Write the routed fgl_g2 board into a KiCad 9 .kicad_pcb (zones unfilled)."""
import json, math, pickle, sys
from sx import Sym, find, find1
from geom import Board, OX, OY, uid, rot
from place import W, H, PX, PY, XC, UX, UY

S = Sym
b = pickle.load(open('board.pkl', 'rb'))
r = json.load(open('routes.json'))
T = b.tree
NET = b.nets

# ---- net names as the schematic has them (the board was created with bare names) ----
RENAME = {'Net-(Q1-Pad3)': '/KA_D'}
KEEP = {'', 'GND', '+5V', '+3V3'}


def newname(n):
    return RENAME.get(n, n if n in KEEP else '/' + n)


def f(v):
    return round(float(v), 4)


def at(x, y):
    return [S('at'), f(x + OX), f(y + OY)]


def xy(x, y):
    return [S('xy'), f(x + OX), f(y + OY)]


items = []
# ---- tracks / vias ----
for t in r['tracks']:
    if (round(t['x1'], 4), round(t['y1'], 4)) == (round(t['x2'], 4), round(t['y2'], 4)):
        continue
    items.append([S('segment'), [S('start'), f(t['x1'] + OX), f(t['y1'] + OY)], [S('end'), f(t['x2'] + OX), f(t['y2'] + OY)],
                  [S('width'), f(t['w'])], [S('layer'), t['layer']], [S('net'), NET[t['net']]], [S('uuid'), uid()]])
seen = set()
for v in r['vias']:
    k = (round(v['x'], 3), round(v['y'], 3))
    if k in seen:
        continue
    seen.add(k)
    items.append([S('via'), at(v['x'], v['y']), [S('size'), f(v['size'])], [S('drill'), f(v['drill'])],
                  [S('layers'), 'F.Cu', 'B.Cu'], [S('net'), NET[v['net']]], [S('uuid'), uid()]])

# ---- board outline: W x H, 1.5 mm corner radius ----
R = 1.5


def line(x1, y1, x2, y2, layer='Edge.Cuts', w=0.1):
    return [S('gr_line'), [S('start'), f(x1 + OX), f(y1 + OY)], [S('end'), f(x2 + OX), f(y2 + OY)],
            [S('stroke'), [S('width'), w], [S('type'), S('default')]], [S('layer'), layer], [S('uuid'), uid()]]


def arc(cx, cy, a0, a1, layer='Edge.Cuts', w=0.1, rad=R):
    pts = [(cx + rad * math.cos(math.radians(a)), cy + rad * math.sin(math.radians(a))) for a in (a0, (a0 + a1) / 2, a1)]
    return [S('gr_arc'), [S('start'), f(pts[0][0] + OX), f(pts[0][1] + OY)], [S('mid'), f(pts[1][0] + OX), f(pts[1][1] + OY)],
            [S('end'), f(pts[2][0] + OX), f(pts[2][1] + OY)], [S('stroke'), [S('width'), w], [S('type'), S('default')]],
            [S('layer'), layer], [S('uuid'), uid()]]


items += [line(R, 0, W - R, 0), line(W, R, W, H - R), line(W - R, H, R, H), line(0, H - R, 0, R),
          arc(W - R, R, 270, 360), arc(W - R, H - R, 0, 90), arc(R, H - R, 90, 180), arc(R, R, 180, 270)]


# ---- GND pours, both layers ----
def zone(net, layer, name, pts):
    return [S('zone'), [S('net'), NET[net]], [S('net_name'), newname(net)], [S('layer'), layer],
            [S('uuid'), uid()], [S('name'), name], [S('hatch'), S('edge'), 0.5],
            [S('connect_pads'), [S('clearance'), 0.3]], [S('min_thickness'), 0.25],
            [S('filled_areas_thickness'), S('no')],
            [S('fill'), [S('thermal_gap'), 0.3], [S('thermal_bridge_width'), 0.45]],
            [S('polygon'), [S('pts')] + [xy(*p) for p in pts]]]


board_poly = [(0, 0), (W, 0), (W, H), (0, H)]
items.append(zone('GND', 'F.Cu', 'GND top', board_poly))
items.append(zone('GND', 'B.Cu', 'GND bottom', board_poly))


# ---- silkscreen ----
def text(s, x, y, size=1.0, th=0.15, layer='F.SilkS', ang=0, justify=None, mirror=False):
    e = [S('effects'), [S('font'), [S('size'), size, size], [S('thickness'), th]]]
    j = [S(justify)] if justify else []
    if mirror:
        j.append(S('mirror'))
    if j:
        e.append([S('justify')] + j)
    a = at(x, y)
    if ang:
        a.append(ang)
    return [S('gr_text'), s, a, [S('layer'), layer], [S('uuid'), uid()], e]


def rect(x0, y0, x1, y1, layer='F.SilkS', w=0.15):
    return [line(x0, y0, x1, y0, layer, w), line(x1, y0, x1, y1, layer, w),
            line(x1, y1, x0, y1, layer, w), line(x0, y1, x0, y0, layer, w)]


J2x = b.pad('J2', '1')['cx']; J2y = b.pad('J2', '1')['cy']
J4x = b.pad('J4', '1')['cx']; J4y = b.pad('J4', '1')['cy']
J3x = b.pad('J3', '1')['cx']; J3y = b.pad('J3', '1')['cy']
jp = b.pad('JP1', '2')
silk = [
    text('FUSED GLASS LIGHTING', 14.5, 18.4, 1.0, 0.15),
    text('controller rev G2  2026-10', 14.5, 20.2, 0.8, 0.12),
    text('5V IN', 69.6, 10.0, 0.9, 0.15),
    text('LED STRING: PORT 1 + -> NEXT -> PORT 2 + ... last port END', 37.0, 57.0, 0.0, 0.0),  # placeholder, dropped below
    text('POT', J2x + 3.0, J2y - 3.6, 0.9, 0.15),
    text('RADAR', J4x + 4.0, J4y - 3.6, 0.9, 0.15),
    text('RADAR MODULE', J3x + 5.08, J3y - 3.4, 0.8, 0.12),
    text('JLCJLCJLCJLC', 50.0, 40.5, 0.8, 0.12, 'B.SilkS', mirror=True),
    # 250 / 500 mA jumper
    text('JP1 open: 250mA', jp['cx'] - 10.4, jp['cy'] - 0.65, 0.8, 0.12),
    text('bridge all 3: 500mA', jp['cx'] - 10.4, jp['cy'] + 0.65, 0.8, 0.12),
    # XIAO outline (USB-C toward the left board edge)
    text('XIAO ESP32C3', XC[0] - 3.0, XC[1] - 5.0, 0.8, 0.12),
    text('USB <', XC[0] - 8.3, XC[1] + 0.2, 0.8, 0.12, ang=90),
]
silk = [s for s in silk if 'LED STRING' not in s[1]]
for k, n in enumerate(range(4)):
    silk.append(text(f'PORT {n + 1}', PX[n] + 3.5, PY + 5.1, 0.8, 0.12))
for lab, dx in (('G', 0), ('W', 2), ('CW', 4), ('SW', 6)):
    silk.append(text(lab, J2x + dx, J2y - 2.3, 0.8, 0.12))
for lab, dx in (('3V3', 0), ('G', 2), ('TX', 4), ('RX', 6), ('OT2', 8)):
    silk.append(text(lab, J4x + dx, J4y - 2.3, 0.8, 0.12))
for lab, k in (('3V3', 0), ('GND', 1), ('TX', 2), ('RX', 3), ('OT2', 4)):
    silk.append(text(lab, J3x + 2.54 * k, J3y - 2.3, 0.8, 0.12))
items += silk
x0, y0, x1, y1 = XC[0] - 10.5, XC[1] - 9.5, XC[0] + 10.1, XC[1] + 9.5
items += rect(x0, y0, x1, y1)

# ---- reference designators: small, upright, placed clear of pads ----
pads = b.pads()
placed_boxes = []


def text_box(cx, cy, s, size):
    w = len(s) * size * 0.72 + 0.2; h = size + 0.2
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def overlaps(bx, ax):
    return bx[0] < ax[2] and ax[0] < bx[2] and bx[1] < ax[3] and ax[1] < bx[3]


pad_boxes = []
for p in pads:
    hw = max(p['w'], p['h']) / 2 + 0.15
    pad_boxes.append((p['cx'] - hw, p['cy'] - hw, p['cx'] + hw, p['cy'] + hw))
gtext_boxes = []
for it in items:
    if it[0] == 'gr_text' and find1(it, 'layer')[1] == 'F.SilkS':
        a = find1(it, 'at'); sz = find1(find1(find1(it, 'effects'), 'font'), 'size')[1]
        bx = text_box(float(a[1]) - OX, float(a[2]) - OY, it[1], sz)
        if len(a) > 3:     # rotated 90: swap extents
            cx, cy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
            hw, hh = (bx[3] - bx[1]) / 2, (bx[2] - bx[0]) / 2
            bx = (cx - hw, cy - hh, cx + hw, cy + hh)
        gtext_boxes.append(bx)
# report silk texts that land on pads
for it, bx in zip([i for i in items if i[0] == 'gr_text' and find1(i, 'layer')[1] == 'F.SilkS'], gtext_boxes):
    hits = [p['ref'] + '.' + p['num'] for p, pb in zip(pads, pad_boxes) if overlaps(bx, pb)]
    if hits:
        print('silk text on pads:', it[1], hits)
# the XIAO outline and the port legends (footprint text) also block reference placement
gtext_boxes += [(x0 - 0.1, y0 - 0.1, x1 + 0.1, y0 + 0.1), (x0 - 0.1, y1 - 0.1, x1 + 0.1, y1 + 0.1),
                (x0 - 0.1, y0, x0 + 0.1, y1), (x1 - 0.1, y0, x1 + 0.1, y1)]
for n in range(4):
    for dx, s in ((0, '+'), (3.5, 'NEXT'), (7, 'END')):
        gtext_boxes.append(text_box(PX[n] + dx, PY + 3.8, s, 0.9))
via_boxes = [(v['x'] - 0.35, v['y'] - 0.35, v['x'] + 0.35, v['y'] + 0.35) for v in r['vias']]
crts = {ref: b.courtyard(ref) for ref in b.fps}
SIZE = 0.8
report = []
for ref, fp in b.fps.items():
    prop = [p for p in find(fp, 'property') if p[1] == 'Reference'][0]
    if ref.startswith('H'):
        if not find1(prop, 'hide'):
            prop.insert(3, [S('hide'), S('yes')])
        continue
    fx, fy, fr = b.fp_pos(ref)
    c = crts[ref]
    cands = []
    cx, cy = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2
    tw = len(ref) * SIZE * 0.72
    for d in (0.0, 0.4, 0.8, 1.2, 1.6, 2.0, 2.4, 2.8):
        cands += [(cx, c[1] - 0.6 - d), (cx, c[3] + 0.6 + d), (c[0] - tw / 2 - 0.4 - d, cy), (c[2] + tw / 2 + 0.4 + d, cy)]
    if ref in ('J5', 'J6', 'J7', 'J8', 'L1', 'L2', 'J2', 'J4'):
        cands = [(cx, cy - 1.0 if ref.startswith('J') else cy)] + cands     # on the part body
    best = None
    for (x, y) in cands:
        bx = text_box(x, y, ref, SIZE)
        if bx[0] < 0.3 or bx[1] < 0.3 or bx[2] > W - 0.3 or bx[3] > H - 0.3:
            continue
        bad = sum(overlaps(bx, pb) for pb in pad_boxes) * 10 + sum(overlaps(bx, pb) for pb in placed_boxes + gtext_boxes) * 10
        bad += sum(overlaps(bx, vb) for vb in via_boxes) * 0.5
        bad += sum(overlaps(bx, cb) for k, cb in crts.items() if k != ref and not k.startswith('H')) * 3
        if best is None or bad < best[0]:
            best = (bad, x, y, bx)
        if bad == 0:
            break
    _, x, y, bx = best
    if best[0] >= 10:
        report.append((ref, best[0]))
        find1(prop, 'layer')[1] = 'F.Fab'
    else:
        placed_boxes.append(bx)
    lx, ly = rot(x - fx, y - fy, -fr)
    pa = find1(prop, 'at')
    pa[1:] = [f(lx), f(ly)] + ([0.0] if fr else [])
    eff = find1(prop, 'effects'); font = find1(eff, 'font')
    sz = find1(font, 'size'); sz[1:] = [SIZE, SIZE]
    th = find1(font, 'thickness')
    if th: th[1] = 0.12
print('refs moved to F.Fab (no clean spot):', report)

T += items

# solid zone connection for THT GND pads whose thermal spokes are blocked by neighbouring tracks
for ref, num in (('J3', '2'), ('J4', '2')):
    for p in find(b.fps[ref], 'pad'):
        if p[1] == num and not find1(p, 'zone_connect'):
            p.append([S('zone_connect'), 2])

# rename nets everywhere (board net table, pads, zones already carry new names)
def walk(x):
    if isinstance(x, list):
        if len(x) == 3 and x[0] == 'net' and isinstance(x[2], str) and not isinstance(x[2], Sym):
            x[2] = newname(x[2])
        for i in x:
            walk(i)
walk(T)
b.save(sys.argv[1] if len(sys.argv) > 1 else 'fgl_g2.kicad_pcb')
print('segments', sum(1 for i in items if i[0] == 'segment'), 'vias', sum(1 for i in items if i[0] == 'via'))
