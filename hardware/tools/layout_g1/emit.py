"""Write the routed board into a KiCad 9 .kicad_pcb."""
import json, math, pickle, sys
from sx import Sym, find, find1
from geom import Board, OX, OY, uid, rot
from place import W, H, JY, X1, X2

S = Sym
b = pickle.load(open('board.pkl', 'rb'))
r = json.load(open('routes.json'))
T = b.tree
NET = b.nets


def at(x, y):
    return [S('at'), round(x + OX, 4), round(y + OY, 4)]


def xy(x, y):
    return [S('xy'), round(x + OX, 4), round(y + OY, 4)]


def f(v):
    return round(float(v), 4)


items = []
# ---- tracks / vias ----
for t in r['tracks']:
    if (t['x1'], t['y1']) == (t['x2'], t['y2']):
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

# ---- board outline: 66 x 44 mm, 1.5 mm corner radius ----
R = 1.5
def line(x1, y1, x2, y2, layer='Edge.Cuts', w=0.1):
    return [S('gr_line'), [S('start'), f(x1 + OX), f(y1 + OY)], [S('end'), f(x2 + OX), f(y2 + OY)],
            [S('stroke'), [S('width'), w], [S('type'), S('default')]], [S('layer'), layer], [S('uuid'), uid()]]
def arc(cx, cy, a0, a1, layer='Edge.Cuts', w=0.1):
    pts = []
    for a in (a0, (a0 + a1) / 2, a1):
        pts.append((cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a))))
    return [S('gr_arc'), [S('start'), f(pts[0][0] + OX), f(pts[0][1] + OY)], [S('mid'), f(pts[1][0] + OX), f(pts[1][1] + OY)],
            [S('end'), f(pts[2][0] + OX), f(pts[2][1] + OY)], [S('stroke'), [S('width'), w], [S('type'), S('default')]],
            [S('layer'), layer], [S('uuid'), uid()]]
items += [line(R, 0, W - R, 0), line(W, R, W, H - R), line(W - R, H, R, H), line(0, H - R, 0, R),
          arc(W - R, R, 270, 360), arc(W - R, H - R, 0, 90), arc(R, H - R, 90, 180), arc(R, R, 180, 270)]

# ---- zones ----
def zone(net, layer, name, pts, keepout=None, prio=0):
    z = [S('zone'), [S('net'), NET[net] if net else 0], [S('net_name'), net or ''], [S('layer'), layer],
         [S('uuid'), uid()], [S('name'), name], [S('hatch'), S('edge'), 0.5]]
    if prio:
        z.append([S('priority'), prio])
    z += [[S('connect_pads'), [S('clearance'), 0.3 if not keepout else 0]], [S('min_thickness'), 0.25],
          [S('filled_areas_thickness'), S('no')]]
    if keepout:
        z.append([S('keepout'), [S('tracks'), S('not_allowed')], [S('vias'), S('not_allowed')], [S('pads'), S('allowed')],
                  [S('copperpour'), S('not_allowed')], [S('footprints'), S('allowed')]])
        z.append([S('fill'), [S('thermal_gap'), 0.5], [S('thermal_bridge_width'), 0.5]])
    else:
        z.append([S('fill'), [S('thermal_gap'), 0.3], [S('thermal_bridge_width'), 0.45]])
    z.append([S('polygon'), [S('pts')] + [xy(*p) for p in pts]])
    return z

board_poly = [(0, 0), (W, 0), (W, H), (0, H)]
items.append(zone('GND', 'F.Cu', 'GND top', board_poly))
items.append(zone('GND', 'B.Cu', 'GND bottom', board_poly))
x0, y0, x1, y1 = r['xiao_ko']
items.append(zone(None, 'F.Cu', 'XIAO keep-out (module underside)', [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], keepout=True))

# ---- silkscreen ----
def text(s, x, y, size=1.0, th=0.15, layer='F.SilkS', ang=0, justify=None, mirror=False):
    e = [S('effects'), [S('font'), [S('size'), size, size], [S('thickness'), th]]]
    j = []
    if justify:
        j.append(S(justify))
    if mirror:
        j.append(S('mirror'))
    if j:
        e.append([S('justify')] + j)
    a = at(x, y)
    if ang:
        a.append(ang)
    return [S('gr_text'), s, a, [S('layer'), layer], [S('uuid'), uid()], e]

items += [
    text('FUSED GLASS LIGHTING', 27.5, 27.4, 1.0, 0.15),
    text('controller rev G1  2026-10', 27.5, 29.3, 0.8, 0.12),
    text('5V IN', 13.6, 35.6, 0.9, 0.15),
    text('FIL 1', X1 - 6.6, 2.0, 0.9, 0.15),
    text('FIL 2', X2 - 6.6, 2.0, 0.9, 0.15),
    text('+', X1 + 1.9, JY + 2.05, 0.9, 0.15), text('+', X2 + 1.9, JY + 2.05, 0.9, 0.15),
    text('POT', 19.4, 38.2, 0.9, 0.15),
    text('RADAR', 48.6, 37.6, 0.9, 0.15),
    text('LD2410S', 48.6, 39.0, 0.8, 0.12),
    text('3V3 GND TX RX OT2', 51.0, 40.4, 0.8, 0.12),
    text('3V3 W GND', 18.4, 39.6, 0.8, 0.12),
    text('JLCJLCJLCJLC', 52.0, 42.3, 0.8, 0.12, 'B.SilkS', mirror=True),
]

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
        gtext_boxes.append(text_box(float(a[1]) - OX, float(a[2]) - OY, it[1], sz))
via_boxes = [(v['x'] - 0.35, v['y'] - 0.35, v['x'] + 0.35, v['y'] + 0.35) for v in r['vias']]
crts = {ref: b.courtyard(ref) for ref in b.fps}
SIZE = 0.8
report = []
for ref, fp in b.fps.items():
    prop = [p for p in find(fp, 'property') if p[1] == 'Reference'][0]
    if ref.startswith('H'):
        # hide hole refs
        if not find1(prop, 'hide'):
            prop.insert(3, [S('hide'), S('yes')])
        continue
    fx, fy, fr = b.fp_pos(ref)
    c = crts[ref]
    cands = []
    cx, cy = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2
    tw = len(ref) * SIZE * 0.72
    for d in (0.0, 0.4, 0.8, 1.2):
        cands += [(cx, c[1] - 0.6 - d), (cx, c[3] + 0.6 + d), (c[0] - tw / 2 - 0.4 - d, cy), (c[2] + tw / 2 + 0.4 + d, cy)]
    if ref == 'U1':
        cands = [(fx + 8.9, fy - 10.5)] + cands       # centre of the module outline
    OVR = {'R3': (X1 + 3.25, JY + 3.6), 'R4': (X2 + 3.25, JY + 3.6)}
    if ref in OVR:
        cands = [OVR[ref]]
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
        # no clean spot: move the reference to the fab layer instead of printing it over a pad
        report.append((ref, best[0]))
        find1(prop, 'layer')[1] = 'F.Fab'
    else:
        placed_boxes.append(bx)
    # reference "at" is relative to the footprint, unrotated frame
    lx, ly = rot(x - fx, y - fy, -fr)
    pa = find1(prop, 'at')
    pa[1:] = [f(lx), f(ly)] + ([f(fr)] if fr else [])     # absolute text angle = fp angle -> reads with board? normalise below
    ang = fr % 360
    if 90 < ang <= 270:
        ang = (ang + 180) % 360
    # text angle stored absolute: make it 0 so every ref reads left-to-right
    pa[1:] = [f(lx), f(ly)] + ([0.0] if fr else [])
    eff = find1(prop, 'effects'); font = find1(eff, 'font')
    sz = find1(font, 'size'); sz[1:] = [SIZE, SIZE]
    th = find1(font, 'thickness')
    if th: th[1] = 0.12
print('ref placement conflicts:', report)

# insert before the end of the board
T += items
b.save(sys.argv[1] if len(sys.argv) > 1 else 'fgl_g1.kicad_pcb')
print('segments', sum(1 for i in items if i[0] == 'segment'), 'vias', sum(1 for i in items if i[0] == 'via'))
