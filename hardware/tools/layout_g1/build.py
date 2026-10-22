"""Build the fgl_g1 layout: placement, hand routing, maze routing, GND vias, pours, outline, silk."""
import math, json, sys
import numpy as np
from sx import Sym, find, find1
from geom import Board, OX, OY, uid, rot
from place import PLACE, W, H, JY, X1, X2
import hand
from router import Grid, route, to_segments, LAYERS, G

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

# keep-outs
# 1) no copper or vias on F.Cu under the XIAO (castellated module, underside pads omitted)
ux, uy, _ = b.fp_pos('U1')
XIAO_KO = (ux + 2.55, uy - 20.6, ux + 15.25, uy - 0.35)
grid.keepout_rect(['F.Cu'], *XIAO_KO)
# 2) keep auto-routed copper off B.Cu under the buck stages (solid GND under the hot loops)
for X in (X1, X2):
    grid.keepout_rect(['B.Cu'], X - 10.4, JY + 2.0, X + 1.9, JY + 16.2)
    grid.keepout_rect(['F.Cu'], X - 10.4, JY - 1.0, X + 0.6, JY + 16.2, vias=False)   # cell interior: hand-routed only
# 2b) nothing auto-routed along the filament-connector strip at the top edge
grid.keepout_rect(['F.Cu'], 0.0, 0.0, X2 + 3.3, JY + 2.6, vias=False)
grid.keepout_rect(['F.Cu', 'B.Cu'], 0.0, 0.0, X2 + 3.3, JY + 2.0)
# 3) input connector area on B.Cu (VBUS link) is hand routed; leave it alone
grid.keepout_rect(['B.Cu'], 6.0, 26.0, 11.0, 37.0)

def comp_cells(net, items_pads, extra_tracks):
    from router import Shape
    sh = []
    for p in items_pads:
        lay = [l for l in LAYERS if l in p['layers'] or '*.Cu' in p['layers']]
        sh.append(Shape('rect', net, lay, cx=p['cx'], cy=p['cy'], w=p['w'], h=p['h'], ang=p['ang'], circle=(p['shape'] == 'circle')))
    for t in extra_tracks:
        if t[0] == 'seg':
            sh.append(Shape('seg', net, [t[1]], ax=t[2][0], ay=t[2][1], bx=t[3][0], by=t[3][1], r=0.05))
        else:
            sh.append(Shape('circle', net, LAYERS, cx=t[1][0], cy=t[1][1], r=0.25))
    return grid.net_cells(sh)

ROUTE = [  # net, width, via-cost, B.Cu penalty
    ('/UART_RX', 0.25, 15, 1.0),
    ('/UART_TX', 0.25, 15, 1.0),
    ('/RADAR_OT2', 0.25, 15, 1.0),
    ('+3V3', 0.4, 25, 1.4),
    ('/KA_DRV', 0.3, 20, 1.3),
    ('/DIM_PWM', 0.25, 25, 1.4),
    ('/DIM_CTRL', 0.3, 20, 1.3),
    ('/ADC_POT', 0.25, 20, 1.3),
    ('/POT_W', 0.25, 20, 1.3),
    ('/POT_HI', 0.25, 20, 1.3),
]
log = []

def in_pad(p, x, y, tol=0.01):
    lx, ly = rot(x - p['cx'], y - p['cy'], -p['ang'])
    return abs(lx) <= p['w'] / 2 + tol and abs(ly) <= p['h'] / 2 + tol

def components(net):
    """Union-find over this net's pads, tracks and vias. Returns list of (pads, segs) groups."""
    items = [('pad', p) for p in pads if p['net'] == net]
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
    for i, a in enumerate(items):
        for j in range(i + 1, len(items)):
            b2 = items[j]
            hit = False
            if a[0] == 'pad' and b2[0] == 'pad':
                continue
            if a[0] == 'pad' or b2[0] == 'pad':
                p, o = (a[1], b2) if a[0] == 'pad' else (b2[1], a)
                for (q, l) in pts(o):
                    if (l == 'both' or l in p['layers'] or '*.Cu' in p['layers']) and in_pad(p, *q):
                        hit = True
            else:
                for (q, l) in pts(a):
                    for (r, m) in pts(b2):
                        if math.hypot(q[0] - r[0], q[1] - r[1]) < 0.02 and (l == m or 'both' in (l, m)):
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

for net, w, vc, bp in ROUTE:
    comps = components(net)
    done, routed = list(comps[0][0]), list(comps[0][1])
    rest = comps[1:]
    while rest:
        src = comp_cells(net, done, routed)
        dpads = [p for g in rest for p in g[0]]
        dsegs = [s for g in rest for s in g[1]]
        dst = comp_cells(net, dpads, dsegs)
        avoid = None
        if net in ('/UART_RX', '/UART_TX', '/RADAR_OT2'):
            # radar lines run on B.Cu straight down to J3 (their pin order is mirrored vs the XIAO)
            avoid = {'F.Cu': np.ones((grid.nx, grid.ny), bool), 'B.Cu': np.zeros((grid.nx, grid.ny), bool)}
            for p in dpads + done:
                if p['ref'] in ('R7', 'TP5'):
                    i0, j0 = int((p['cx'] - 3) / G), int((p['cy'] - 3) / G)
                    avoid['F.Cu'][max(i0, 0):i0 + 60, max(j0, 0):j0 + 60] = False
        res, msg = route(grid, net, src, dst, w / 2, via_cost=vc, b_pen=bp, avoid=avoid)
        if res is None:
            log.append(f'FAIL {net}: {msg} remaining {[(p["ref"], p["num"]) for p in dpads]}')
            break
        path, blocked = res
        segs = to_segments(path, blocked)
        # snap route ends that land inside a same-net via onto the via centre (clean KiCad connectivity)
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
        # finish at the exact pad centre when a route end lies inside a same-net pad (ovals, roundrects)
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
        log.append(f'ok {net} -> {[ (p["ref"]+"."+p["num"]) for p in hitg[0]]} ({len(segs)} items)')
print('\n'.join(log))

# ---- GND vias for every GND SMD pad that has no hand-routed GND connection yet ----
def touches(p, net):
    for t in tracks:
        if t[0] != net:
            continue
        for q in (t[3], t[4]):
            dx, dy = q[0] - p['cx'], q[1] - p['cy']
            lx, ly = rot(dx, dy, -p['ang'])
            if abs(lx) <= p['w'] / 2 + 0.01 and abs(ly) <= p['h'] / 2 + 0.01:
                return True
    return False

blockedG, via_badG = grid.masks('GND', 0.25)
for p in pads:
    if p['net'] != 'GND' or p['kind'] != 'smd' or touches(p, 'GND'):
        continue
    best = None
    for rr in np.arange(1.0, 3.01, 0.1):
        for k in range(36):
            a = 2 * math.pi * k / 36
            x, y = p['cx'] + rr * math.cos(a), p['cy'] + rr * math.sin(a)
            i, j = int(round(x / G)), int(round(y / G))
            if not (0 <= i < grid.nx and 0 <= j < grid.ny) or via_badG[i, j]:
                continue
            ok = True
            for t in np.linspace(0, 1, 30):
                xi = int(round((p['cx'] + (x - p['cx']) * t) / G)); yj = int(round((p['cy'] + (y - p['cy']) * t) / G))
                lx, ly = rot(xi * G - p['cx'], yj * G - p['cy'], -p['ang'])
                inside = abs(lx) <= p['w'] / 2 and abs(ly) <= p['h'] / 2
                if not inside and blockedG['F.Cu'][xi, yj]:
                    ok = False; break
            if ok:
                best = (x, y); break
        if best:
            break
    if not best:
        print('NO GND VIA for', p['ref'], p['num']); continue
    x, y = round(best[0], 2), round(best[1], 2)
    tracks.append(('GND', 'F.Cu', 0.4, (p['cx'], p['cy']), (x, y)))
    vias.append(('GND', x, y, 0.6, 0.3))
    grid.add_track('GND', 'F.Cu', 0.4, (p['cx'], p['cy']), (x, y))
    grid.add_via('GND', x, y, 0.6, 0.3)
    blockedG, via_badG = grid.masks('GND', 0.25)

# ---- GND stitching vias on a 4 mm grid wherever both pours will exist ----
_, via_bad = grid.masks('GND', 0.25, via_r=0.3 + 0.35)   # extra margin so the pour flows round them
crts = [b.courtyard(r) for r in b.fps if not r.startswith('H')]
stitch = 0
for x in np.arange(2.5, W - 1.0, 5.0):
    for y in np.arange(2.5, H - 1.0, 5.0):
        i, j = int(round(x / G)), int(round(y / G))
        if via_bad[i, j] or any(c[0] - 0.4 < x < c[2] + 0.4 and c[1] - 0.4 < y < c[3] + 0.4 for c in crts):
            continue
        vias.append(('GND', float(x), float(y), 0.6, 0.3)); grid.add_via('GND', float(x), float(y), 0.6, 0.3)
        stitch += 1
print('stitching vias', stitch)

json.dump({'tracks': [dict(net=t[0], layer=t[1], w=t[2], x1=t[3][0], y1=t[3][1], x2=t[4][0], y2=t[4][1]) for t in tracks],
           'vias': [dict(net=v[0], x=v[1], y=v[2], size=v[3], drill=v[4]) for v in vias],
           'xiao_ko': XIAO_KO}, open('routes.json', 'w'), indent=0)
import pickle
pickle.dump(b, open('board.pkl', 'wb'))
