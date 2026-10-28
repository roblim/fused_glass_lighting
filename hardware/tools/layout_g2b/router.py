"""Small 2-layer grid maze router (Dijkstra/A* on a 0.1 mm grid) with clearance-inflated obstacles."""
import heapq, math
import numpy as np
from geom import rot

G = 0.1
CLR = 0.2 + 0.06          # netclass clearance + quantisation margin
EDGE = 0.5 + 0.06
LAYERS = ('F.Cu', 'B.Cu')


class Shape:
    """Copper (or keep-out) primitive with a cached distance window."""
    def __init__(self, kind, net, layers, **k):
        self.kind, self.net, self.layers, self.k = kind, net, set(layers), k
        self.win = None


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return np.hypot(px - ax, py - ay)
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0, 1)
    return np.hypot(px - (ax + t * dx), py - (ay + t * dy))


class Grid:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.nx, self.ny = int(round(W / G)) + 1, int(round(H / G)) + 1
        self.xs = np.arange(self.nx) * G
        self.ys = np.arange(self.ny) * G
        self.shapes = []
        self.holes = []      # (x, y, r) any drilled hole
        self.keep = {l: np.zeros((self.nx, self.ny), bool) for l in LAYERS}  # track keep-out
        self.keep_via = np.zeros((self.nx, self.ny), bool)
        # board edge distance
        X, Y = np.meshgrid(self.xs, self.ys, indexing='ij')
        self.edge_d = np.minimum(np.minimum(X, W - X), np.minimum(Y, H - Y))

    # ---- shape registration ----
    def add_pad(self, p):
        lay = [l for l in LAYERS if l in p['layers'] or '*.Cu' in p['layers']]
        self.shapes.append(Shape('rect', p['net'], lay, cx=p['cx'], cy=p['cy'], w=p['w'], h=p['h'], ang=p['ang'],
                                 circle=(p['shape'] == 'circle'), smd=(p.get('kind') == 'smd')))
        if p['drill']:
            self.holes.append((p['cx'], p['cy'], max(p['drill']) / 2))

    def add_hole(self, x, y, r):
        self.holes.append((x, y, r))
        self.shapes.append(Shape('circle', '__hole__', LAYERS, cx=x, cy=y, r=r + 0.25 - CLR + 0.05))

    def add_track(self, net, layer, w, a, b):
        self.shapes.append(Shape('seg', net, [layer], ax=a[0], ay=a[1], bx=b[0], by=b[1], r=w / 2))

    def add_via(self, net, x, y, size, drill):
        self.shapes.append(Shape('circle', net, LAYERS, cx=x, cy=y, r=size / 2))
        self.holes.append((x, y, drill / 2))

    def keepout_rect(self, layers, x0, y0, x1, y1, vias=True):
        i0, i1 = int(x0 / G), int(math.ceil(x1 / G)); j0, j1 = int(y0 / G), int(math.ceil(y1 / G))
        for l in layers:
            self.keep[l][i0:i1 + 1, j0:j1 + 1] = True
        if vias:
            self.keep_via[i0:i1 + 1, j0:j1 + 1] = True

    # ---- distance windows ----
    def _window(self, s, reach=3.0):
        k = s.k
        if s.kind == 'seg':
            x0, x1 = min(k['ax'], k['bx']), max(k['ax'], k['bx'])
            y0, y1 = min(k['ay'], k['by']), max(k['ay'], k['by'])
            R = k['r']
        elif s.kind == 'circle':
            x0 = x1 = k['cx']; y0 = y1 = k['cy']; R = k['r']
        else:
            R = math.hypot(k['w'], k['h']) / 2
            x0 = x1 = k['cx']; y0 = y1 = k['cy']
        i0 = max(0, int((x0 - R - reach) / G)); i1 = min(self.nx - 1, int((x1 + R + reach) / G) + 1)
        j0 = max(0, int((y0 - R - reach) / G)); j1 = min(self.ny - 1, int((y1 + R + reach) / G) + 1)
        X, Y = np.meshgrid(self.xs[i0:i1 + 1], self.ys[j0:j1 + 1], indexing='ij')
        if s.kind == 'seg':
            d = seg_dist(X, Y, k['ax'], k['ay'], k['bx'], k['by']) - k['r']
        elif s.kind == 'circle':
            d = np.hypot(X - k['cx'], Y - k['cy']) - k['r']
        else:
            if k['circle']:
                d = np.hypot(X - k['cx'], Y - k['cy']) - k['w'] / 2
            else:
                a = math.radians(k['ang'])
                # inverse of KiCad rotation
                dx, dy = X - k['cx'], Y - k['cy']
                lx = dx * math.cos(a) - dy * math.sin(a)
                ly = dx * math.sin(a) + dy * math.cos(a)
                qx = np.abs(lx) - k['w'] / 2; qy = np.abs(ly) - k['h'] / 2
                d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0)
        s.win = (i0, j0, d)

    def masks(self, net, hw, via_r=0.3):
        """blocked[layer] for a track of half-width hw; via_bad for vias."""
        blocked = {l: (self.edge_d < EDGE + hw) | self.keep[l] for l in LAYERS}
        via_bad = (self.edge_d < EDGE + via_r) | self.keep_via
        for s in self.shapes:
            if s.net == net and s.net != '__hole__':
                if s.kind == 'rect':            # never put a via inside a pad, even a same-net one
                    if s.win is None:
                        self._window(s)
                    i0, j0, d = s.win
                    # D17: a via stays 0.25 mm clear of SMD pads, same net included
                    via_bad[i0:i0 + d.shape[0], j0:j0 + d.shape[1]] |= d < via_r + (0.3 if s.k.get('smd') else 0.1)
                continue
            if s.win is None:
                self._window(s)
            i0, j0, d = s.win
            sl = (slice(i0, i0 + d.shape[0]), slice(j0, j0 + d.shape[1]))
            for l in s.layers:
                blocked[l][sl] |= d < CLR + hw
            via_bad[sl] |= d < CLR + via_r
        X, Y = None, None
        for (hx, hy, hr) in self.holes:   # hole-to-hole for vias
            i0 = max(0, int((hx - hr - 1.5) / G)); i1 = min(self.nx - 1, int((hx + hr + 1.5) / G) + 1)
            j0 = max(0, int((hy - hr - 1.5) / G)); j1 = min(self.ny - 1, int((hy + hr + 1.5) / G) + 1)
            XX, YY = np.meshgrid(self.xs[i0:i1 + 1], self.ys[j0:j1 + 1], indexing='ij')
            via_bad[i0:i1 + 1, j0:j1 + 1] |= np.hypot(XX - hx, YY - hy) < hr + 0.15 + 0.3
        return blocked, via_bad

    def net_cells(self, shapes, hw=0.0):
        """Cells inside the given same-net copper shapes, per layer."""
        out = {l: np.zeros((self.nx, self.ny), bool) for l in LAYERS}
        for s in shapes:
            if s.win is None:
                self._window(s)
            i0, j0, d = s.win
            sl = (slice(i0, i0 + d.shape[0]), slice(j0, j0 + d.shape[1]))
            for l in s.layers:
                out[l][sl] |= d < -0.02
        return out


def route(grid, net, src, dst, hw, via_r=0.3, via_cost=25.0, b_pen=1.4, avoid=None):
    """src/dst: dict layer->bool array. Returns list of (layer, i, j) cells or None."""
    blocked, via_bad = grid.masks(net, hw, via_r)
    if avoid is not None:
        for l in LAYERS:
            blocked[l] = blocked[l] | avoid[l]
    nx, ny = grid.nx, grid.ny
    INF = float('inf')
    dist = np.full((2, nx, ny), INF)
    prev = {}
    pq = []
    dpts = []
    for li, l in enumerate(LAYERS):
        ii, jj = np.nonzero(dst[l] & ~blocked[l])
        dpts += list(zip(ii[::7], jj[::7]))
    if not dpts:
        return None, 'no reachable target cells'
    dpts = np.array(dpts)

    def h(i, j):
        return np.min(np.hypot(dpts[:, 0] - i, dpts[:, 1] - j)) * 0.999

    for li, l in enumerate(LAYERS):
        ii, jj = np.nonzero(src[l] & ~blocked[l])
        for i, j in zip(ii, jj):
            dist[li, i, j] = 0
            heapq.heappush(pq, (h(i, j), 0.0, li, i, j))
    if not pq:
        return None, 'no free source cells'
    steps = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)]
    dstF, dstB = dst['F.Cu'], dst['B.Cu']
    bF, bB = blocked['F.Cu'], blocked['B.Cu']
    goal = None
    hcache = {}
    while pq:
        f, g, li, i, j = heapq.heappop(pq)
        if g > dist[li, i, j]:
            continue
        if (dstF if li == 0 else dstB)[i, j]:
            goal = (li, i, j); break
        bl = bF if li == 0 else bB
        pen = 1.0 if li == 0 else b_pen
        for di, dj, c in steps:
            a, b2 = i + di, j + dj
            if a < 0 or b2 < 0 or a >= nx or b2 >= ny or bl[a, b2]:
                continue
            ng = g + c * pen
            if ng < dist[li, a, b2]:
                dist[li, a, b2] = ng
                prev[(li, a, b2)] = (li, i, j)
                key = (a, b2)
                hv = hcache.get(key)
                if hv is None:
                    hv = h(a, b2); hcache[key] = hv
                heapq.heappush(pq, (ng + hv, ng, li, a, b2))
        if not via_bad[i, j]:
            lo = 1 - li
            if not (bB if lo == 1 else bF)[i, j]:
                ng = g + via_cost
                if ng < dist[lo, i, j]:
                    dist[lo, i, j] = ng
                    prev[(lo, i, j)] = (li, i, j)
                    heapq.heappush(pq, (ng + hcache.get((i, j), h(i, j)), ng, lo, i, j))
    if goal is None:
        return None, 'no path'
    path = [goal]
    while path[-1] in prev:
        path.append(prev[path[-1]])
    path.reverse()
    return (path, blocked), 'ok'


def clear_line(bl, a, b):
    (i0, j0), (i1, j1) = a, b
    n = int(max(abs(i1 - i0), abs(j1 - j0)) * 2) + 1
    for t in np.linspace(0, 1, n):
        i = int(round(i0 + (i1 - i0) * t)); j = int(round(j0 + (j1 - j0) * t))
        if bl[i, j]:
            return False
    return True


def to_segments(path, blocked):
    """Split by layer, string-pull each run, return [('seg',layer,(x,y),(x,y)) | ('via',(x,y))]."""
    out = []
    runs = []
    cur = [path[0]]
    for c in path[1:]:
        if c[0] != cur[-1][0]:
            runs.append(cur); cur = [c]
        else:
            cur.append(c)
    runs.append(cur)
    for k, run in enumerate(runs):
        li = run[0][0]; l = LAYERS[li]
        pts = [(c[1], c[2]) for c in run]
        bl = blocked[l]
        # string pulling restricted to 0/45/90 degree segments where possible, else any angle
        sp = [pts[0]]
        i = 0
        while i < len(pts) - 1:
            j = len(pts) - 1
            while j > i + 1 and not clear_line(bl, pts[i], pts[j]):
                j -= 1
            sp.append(pts[j]); i = j
        for a, b in zip(sp, sp[1:]):
            out.append(('seg', l, (a[0] * G, a[1] * G), (b[0] * G, b[1] * G)))
        if k < len(runs) - 1:
            e = runs[k][-1]
            out.append(('via', (e[1] * G, e[2] * G)))
    return out
