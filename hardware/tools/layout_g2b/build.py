"""Build the 90 x 60 mm fgl_g2 layout (D19): placement, hand routing, maze routing, GND vias, stitching.

Input: orig.kicad_pcb (the unplaced board KiCad created from the schematic).
Output: routes.json + board.pkl for emit.py.
"""
import math, json, pickle
import numpy as np
from geom import Board, rot
from place import PLACE, W, H
import hand
from router import Grid, route, to_segments, LAYERS, G, Shape

b = Board('orig.kicad_pcb')
for r, (x, y, a) in PLACE.items():
    b.place(r, x, y, a)

h = hand.build(b)
tracks = []   # (net, layer, w, (x1,y1), (x2,y2))
vias = []     # (net, x, y, size, drill)
for net, layer, w, pts in h.tracks:
    for a, c in zip(pts, pts[1:]):
        if a != c:
            tracks.append((net, layer, w, a, c))
vias += h.vias

grid = Grid(W, H)
pads = b.pads()
for p in pads:
    if p['kind'] == 'np_thru_hole':
        grid.add_hole(p['cx'], p['cy'], p['drill'][0] / 2 if p['drill'] else p['w'] / 2)
    elif p['layers']:
        grid.add_pad(p)
for t in tracks:
    grid.add_track(t[0], t[1], t[2], t[3], t[4])
for v in vias:
    grid.add_via(*v)

# ---- keep-outs for auto-routed copper ----
# solid GND on B.Cu under the SEPIC switching loop (U2 right half, L1 pad 2, C4, D5, L2, C5/C6)
from place import UX, UY
grid.keepout_rect(['B.Cu'], UX - 0.4, UY - 4.5, UX + 16.8, UY + 13.0)
# B.Cu VBUS link at the USB-C connector is hand routed
jx, jy, _ = b.fp_pos('J1')
grid.keepout_rect(['B.Cu'], jx - 6.2, jy - 3.2, jx - 5.0, jy + 3.2)
# no vias under the JP1 / JP2 legends (silkscreen over a via is clipped)
grid.keepout_rect([], 24.0, 26.4, 41.6, 32.2, vias=True)


def comp_cells(net, items_pads, extra_tracks):
    sh = []
    for p in items_pads:
        lay = [l for l in LAYERS if l in p['layers'] or '*.Cu' in p['layers']]
        sh.append(Shape('rect', net, lay, cx=p['cx'], cy=p['cy'], w=p['w'], h=p['h'], ang=p['ang'],
                        circle=(p['shape'] == 'circle')))
    for t in extra_tracks:
        if t[0] == 'seg':
            sh.append(Shape('seg', net, [t[1]], ax=t[2][0], ay=t[2][1], bx=t[3][0], by=t[3][1], r=0.05))
        else:
            sh.append(Shape('circle', net, LAYERS, cx=t[1][0], cy=t[1][1], r=0.25))
    return grid.net_cells(sh)


#   net, width, via cost, B.Cu penalty
ROUTE = [
    ('VOUT', 0.8, 30, 1.6, {'R24.1'}),
    ('VOUT', 0.3, 15, 1.2),
    ('+5V', 0.6, 30, 1.5, {'D4.2'}),
    ('+5V', 0.5, 20, 1.3),
    ('VBUS_F', 0.5, 30, 1.5),
    ('KA_D', 0.6, 30, 1.5),
    ('XIAO_5V', 0.5, 25, 1.4),
    ('LED_RTN', 0.4, 15, 1.2),
    ('SW_N', 0.3, 15, 1.2),
    ('CC1', 0.25, 10, 1.0),
    ('CC2', 0.25, 10, 1.0),
    ('+3V3', 0.4, 20, 1.3),
    ('RADAR_3V3', 0.4, 20, 1.3),
    ('ISEL', 0.25, 15, 1.2),
    ('RADAR_MODE', 0.25, 15, 1.2),
    ('ISEL_IO', 0.25, 15, 1.2),
    ('VSENSE', 0.25, 15, 1.2),
    ('DIM_PWM', 0.25, 15, 1.2),
    ('KA_DRV', 0.25, 15, 1.2),
    ('KA_G', 0.25, 15, 1.2),
    ('UART_TX', 0.25, 15, 1.2),
    ('UART_RX', 0.25, 15, 1.2),
    ('RADAR_OT2', 0.25, 15, 1.2),
    ('RADAR_RX', 0.25, 15, 1.2),
    ('RADAR_TX', 0.25, 15, 1.2),
    ('RADAR_OT2_C', 0.25, 15, 1.2),
    ('ADC_POT', 0.25, 15, 1.2),
    ('POT_W', 0.25, 15, 1.2),
    ('POT_HI', 0.25, 15, 1.2),
    ('Q2_G', 0.3, 15, 1.2),
    ('DRV_EN', 0.25, 15, 1.2),
    ('SS', 0.25, 15, 1.2),
    ('DIMC', 0.25, 15, 1.2),
    ('COMP', 0.25, 15, 1.2),
    ('FREQ', 0.25, 15, 1.2),
    ('OVP', 0.25, 15, 1.2),
    ('RS2_B', 0.5, 15, 1.2),
    ('STR2', 0.8, 15, 1.2), ('STR3', 0.8, 15, 1.2), ('STR4', 0.8, 15, 1.2),
    ('SW', 0.8, 30, 2.0), ('SEP_B', 0.8, 30, 2.0), ('VBUS_IN', 0.8, 30, 1.5),
]
log = []


def in_pad(p, x, y, tol=0.01):
    lx, ly = rot(x - p['cx'], y - p['cy'], -p['ang'])
    return abs(lx) <= p['w'] / 2 + tol and abs(ly) <= p['h'] / 2 + tol


def components(net, skip=()):
    """Union-find over this net's pads, tracks and vias. Returns list of (pads, segs) groups."""
    items = [('pad', p) for p in pads if p['net'] == net and f"{p['ref']}.{p['num']}" not in skip]
    items += [('trk', t) for t in tracks if t[0] == net]
    items += [('via', v) for v in vias if v[0] == net]
    par = list(range(len(items)))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i

    def pts(it):
        k, o = it
        if k == 'trk': return [(o[3], o[1]), (o[4], o[1])]
        if k == 'via': return [((o[1], o[2]), 'both')]
        return []

    def seg_hit(q, l, t):
        # point q lies on track t (same layer) within its half width
        if l != 'both' and l != t[1]:
            return False
        (ax, ay), (bx, by) = t[3], t[4]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        u = 0 if L2 == 0 else max(0, min(1, ((q[0] - ax) * dx + (q[1] - ay) * dy) / L2))
        return math.hypot(q[0] - ax - u * dx, q[1] - ay - u * dy) <= t[2] / 2 + 0.01

    for i, a in enumerate(items):
        for j in range(i + 1, len(items)):
            b2 = items[j]
            hit = False
            if a[0] == 'pad' and b2[0] == 'pad':
                # same-net pads of one footprint that overlap (stacked USB-C pins, EP vias)
                pa, pb = a[1], b2[1]
                hit = pa['ref'] == pb['ref'] and in_pad(pa, pb['cx'], pb['cy'])
            elif a[0] == 'pad' or b2[0] == 'pad':
                p, o = (a[1], b2) if a[0] == 'pad' else (b2[1], a)
                for (q, l) in pts(o):
                    if (l == 'both' or l in p['layers'] or '*.Cu' in p['layers']) and in_pad(p, *q):
                        hit = True
            else:
                for (q, l) in pts(a):
                    if b2[0] == 'trk' and seg_hit(q, l, b2[1]):
                        hit = True
                for (q, l) in pts(b2):
                    if a[0] == 'trk' and seg_hit(q, l, a[1]):
                        hit = True
            if hit:
                par[f(i)] = f(j)
    groups = {}
    for i, it in enumerate(items):
        groups.setdefault(f(i), []).append(it)
    out = []
    for g in groups.values():
        gp = [o for k, o in g if k == 'pad']
        gs = [('seg', o[1], o[3], o[4]) for k, o in g if k == 'trk'] + [('via', (o[1], o[2])) for k, o in g if k == 'via']
        out.append((gp, gs))
    out.sort(key=lambda g: -(len(g[0]) * 10 + len(g[1])))
    return out



# ---- FB: its own 0.25 mm trace from U2 pin 9 to R21's pad (Kelvin), kept off the rest of LED_RTN ----
from router import CLR
fbp = b.pad('U2', '9'); r21p = b.pad('R21', '1')
def is_pad(s, p):
    return s.kind == 'rect' and abs(s.k['cx'] - p['cx']) < 1e-6 and abs(s.k['cy'] - p['cy']) < 1e-6
avoid = {l: np.zeros((grid.nx, grid.ny), bool) for l in LAYERS}
for s_ in grid.shapes:
    near_fb = (s_.kind == 'circle' and abs(s_.k['cx'] - h.fbv[0]) < 1e-6 and abs(s_.k['cy'] - h.fbv[1]) < 1e-6) or \
        (s_.kind == 'seg' and (abs(s_.k['bx'] - h.fbv[0]) < 1e-6 and abs(s_.k['by'] - h.fbv[1]) < 1e-6))
    if s_.net != 'LED_RTN' or is_pad(s_, fbp) or is_pad(s_, r21p) or near_fb:
        continue
    if s_.win is None:
        grid._window(s_)
    i0, j0, d = s_.win
    for l in s_.layers:
        avoid[l][i0:i0 + d.shape[0], j0:j0 + d.shape[1]] |= d < CLR + 0.125
# the pad itself (where the bus also lands) is allowed
i0, i1 = int((r21p['cx'] - 1.2) / G), int((r21p['cx'] + 1.2) / G) + 1
j0, j1 = int((r21p['cy'] - 1.2) / G), int((r21p['cy'] + 1.2) / G) + 1
for l in LAYERS:
    avoid[l][i0:i1, j0:j1] = False
src = comp_cells('LED_RTN', [], [('via', h.fbv)]); dst = comp_cells('LED_RTN', [r21p], [])
res, msg = route(grid, 'LED_RTN', src, dst, 0.125, via_cost=15, b_pen=1.0, avoid=avoid)
assert res is not None, 'FB route: ' + msg
for s_ in to_segments(*res):
    if s_[0] == 'seg':
        tracks.append(('LED_RTN', s_[1], 0.25, s_[2], s_[3])); grid.add_track('LED_RTN', s_[1], 0.25, s_[2], s_[3])
    else:
        vias.append(('LED_RTN', s_[1][0], s_[1][1], 0.6, 0.3)); grid.add_via('LED_RTN', s_[1][0], s_[1][1], 0.6, 0.3)
log.append('ok FB Kelvin route')

for net, w, vc, bp, *skip in ROUTE:
    comps = components(net, skip[0] if skip else ())
    if not comps:
        log.append(f'?? {net}: no pads'); continue
    done, routed = list(comps[0][0]), list(comps[0][1])
    rest = comps[1:]
    while rest:
        src = comp_cells(net, done, routed)
        dpads = [p for g in rest for p in g[0]]
        dsegs = [s for g in rest for s in g[1]]
        dst = comp_cells(net, dpads, dsegs)
        res, msg = route(grid, net, src, dst, w / 2, via_cost=vc, b_pen=bp)
        if res is None:
            log.append(f'FAIL {net}: {msg} remaining {[(p["ref"], p["num"]) for p in dpads]}')
            break
        path, blocked = res
        segs = to_segments(path, blocked)
        netvias = [(v[1], v[2]) for v in vias if v[0] == net]

        def snap(q):
            for (vx, vy) in netvias:
                if math.hypot(q[0] - vx, q[1] - vy) < 0.3:
                    return (vx, vy)
            return q
        if segs and segs[0][0] == 'seg':
            segs[0] = ('seg', segs[0][1], snap(segs[0][2]), segs[0][3])
        if segs and segs[-1][0] == 'seg':
            segs[-1] = ('seg', segs[-1][1], segs[-1][2], snap(segs[-1][3]))
        netpads = [p for p in pads if p['net'] == net]

        def padfix(q, layer):
            for p in netpads:
                if (layer in p['layers'] or '*.Cu' in p['layers']) and in_pad(p, *q, tol=0) and \
                        math.hypot(q[0] - p['cx'], q[1] - p['cy']) > 1e-3:
                    return (p['cx'], p['cy'])
            return None
        if segs and segs[-1][0] == 'seg':
            c = padfix(segs[-1][3], segs[-1][1])
            if c: segs.append(('seg', segs[-1][1], segs[-1][3], c))
        if segs and segs[0][0] == 'seg':
            c = padfix(segs[0][2], segs[0][1])
            if c: segs.insert(0, ('seg', segs[0][1], c, segs[0][2]))
        li, i, j = path[-1]
        hitg = None
        for g in rest:
            c = comp_cells(net, g[0], g[1])
            if c[LAYERS[li]][i, j]:
                hitg = g; break
        for s in segs:
            if s[0] == 'seg':
                tracks.append((net, s[1], w, s[2], s[3]))
                grid.add_track(net, s[1], w, s[2], s[3])
            else:
                vias.append((net, s[1][0], s[1][1], 0.6, 0.3))
                grid.add_via(net, s[1][0], s[1][1], 0.6, 0.3)
        routed += segs + list(hitg[1])
        done += hitg[0]
        rest.remove(hitg)
        log.append(f'ok {net} -> {[(p["ref"] + "." + p["num"]) for p in hitg[0]]} ({len(segs)} items)')
print('\n'.join(l for l in log if not l.startswith('ok')) or 'all routed')
print(sum(1 for l in log if l.startswith('ok')), 'connections routed')


# ---- GND vias for every GND SMD pad that has no GND track yet ----
def touches(p, net):
    for t in tracks:
        if t[0] != net:
            continue
        for q in (t[3], t[4]):
            if in_pad(p, *q):
                return True
    return False


SKIP_GND_VIA = {('U2', '15')}     # exposed pad: thermal vias are in the footprint
# D17 rule: no via closer than 0.25 mm to any SMD pad (via edge to pad edge)
from shapely.geometry import Point as _Pt, box as _box
from shapely import affinity as _aff
SMD = []
for p in pads:
    if p['kind'] == 'smd' and not (p['ref'] == 'U2' and p['num'] in ('15', '')):
        g = _box(-p['w'] / 2, -p['h'] / 2, p['w'] / 2, p['h'] / 2)
        g = _aff.translate(_aff.rotate(g, -p['ang'], origin=(0, 0)), p['cx'], p['cy'])
        SMD.append(g)
def smd_ok(x, y, r=0.3):
    q = _Pt(x, y)
    return all(g.distance(q) >= r + 0.25 for g in SMD)
blockedG, via_badG = grid.masks('GND', 0.25)
missing = []
for p in pads:
    if p['net'] != 'GND' or p['kind'] != 'smd' or (p['ref'], p['num']) in SKIP_GND_VIA or touches(p, 'GND'):
        continue
    best = None
    for rr in np.arange(0.9, 3.01, 0.1):
        for k in range(36):
            a = 2 * math.pi * k / 36
            x, y = p['cx'] + rr * math.cos(a), p['cy'] + rr * math.sin(a)
            i, j = int(round(x / G)), int(round(y / G))
            if not (0 <= i < grid.nx and 0 <= j < grid.ny) or via_badG[i, j] or not smd_ok(x, y):
                continue
            ok = True
            for tt in np.linspace(0, 1, 30):
                xi = int(round((p['cx'] + (x - p['cx']) * tt) / G)); yj = int(round((p['cy'] + (y - p['cy']) * tt) / G))
                if not in_pad(p, xi * G, yj * G, tol=0) and blockedG['F.Cu'][xi, yj]:
                    ok = False; break
            if ok:
                best = (x, y); break
        if best:
            break
    if not best:
        missing.append((p['ref'], p['num'])); continue
    x, y = round(best[0], 2), round(best[1], 2)
    tracks.append(('GND', 'F.Cu', 0.4, (p['cx'], p['cy']), (x, y)))
    vias.append(('GND', x, y, 0.6, 0.3))
    grid.add_track('GND', 'F.Cu', 0.4, (p['cx'], p['cy']), (x, y))
    grid.add_via('GND', x, y, 0.6, 0.3)
    blockedG, via_badG = grid.masks('GND', 0.25)
print('GND pads without a via:', missing)

# ---- GND stitching vias on a 5 mm grid where both pours will exist ----
_, via_bad = grid.masks('GND', 0.25, via_r=0.3 + 0.35)
crts = [b.courtyard(r) for r in b.fps if not r.startswith('H')]
stitch = 0
for x in np.arange(2.5, W - 1.0, 5.0):
    for y in np.arange(2.5, H - 1.0, 5.0):
        i, j = int(round(x / G)), int(round(y / G))
        if via_bad[i, j] or not smd_ok(x, y) or any(c[0] - 0.4 < x < c[2] + 0.4 and c[1] - 0.4 < y < c[3] + 0.4 for c in crts):
            continue
        vias.append(('GND', float(x), float(y), 0.6, 0.3)); grid.add_via('GND', float(x), float(y), 0.6, 0.3)
        stitch += 1
print('stitching vias', stitch)

# ---- extra GND vias where a pour would otherwise be an island (found by zone-fill checks) ----
EXTRA_GND_VIAS = [(22.4, 32.0)]
_, via_bad = grid.masks('GND', 0.25, via_r=0.3 + 0.05)
for (x0, y0) in EXTRA_GND_VIAS:
    best = None
    for rr in np.arange(0, 1.51, 0.1):
        for k in range(24 if rr else 1):
            a = 2 * math.pi * k / 24
            x, y = round(x0 + rr * math.cos(a), 2), round(y0 + rr * math.sin(a), 2)
            i, j = int(round(x / G)), int(round(y / G))
            if not via_bad[i, j] and smd_ok(x, y):
                best = (x, y); break
        if best:
            break
    assert best, ('no spot for extra GND via near', x0, y0)
    vias.append(('GND', best[0], best[1], 0.6, 0.3)); grid.add_via('GND', best[0], best[1], 0.6, 0.3)
    print('extra GND via', best)

json.dump({'tracks': [dict(net=t[0], layer=t[1], w=t[2], x1=t[3][0], y1=t[3][1], x2=t[4][0], y2=t[4][1]) for t in tracks],
           'vias': [dict(net=v[0], x=v[1], y=v[2], size=v[3], drill=v[4]) for v in vias]},
          open('routes.json', 'w'), indent=0)
pickle.dump(b, open('board.pkl', 'wb'))
