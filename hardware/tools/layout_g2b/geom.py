"""Board model helpers: footprint placement and global pad geometry (fgl_g1, fgl_g2)."""
import math, uuid
from sx import parse, ser, find, find1, Sym

OX, OY = 100.0, 100.0          # board-local (0,0) maps to KiCad (100,100)


def rot(x, y, deg):
    """KiCad footprint rotation (deg CCW on screen, y down)."""
    a = math.radians(deg)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)


def uid():
    return str(uuid.uuid4())


class Board:
    def __init__(self, path):
        self.tree = parse(open(path).read())
        self.fps = {}
        self.nets = {}
        for n in find(self.tree, 'net'):
            self.nets[n[2]] = int(n[1])
        for fp in find(self.tree, 'footprint'):
            ref = [p[2] for p in find(fp, 'property') if p[1] == 'Reference'][0]
            self.fps[ref] = fp
            # remember original local pad angle (file stores absolute angle)
            at = find1(fp, 'at')
            a0 = float(at[3]) if len(at) > 3 else 0.0
            for p in find(fp, 'pad'):
                pa = find1(p, 'at')
                pang = float(pa[3]) if len(pa) > 3 else 0.0
                p.append(['_local_angle', pang - a0])
            for t in find(fp, 'property') + find(fp, 'fp_text'):
                ta = find1(t, 'at')
                if ta is None:
                    continue
                tang = float(ta[3]) if len(ta) > 3 else 0.0
                t.append(['_local_angle', tang - a0])

    # ---------- placement ----------
    def place(self, ref, x, y, r=0.0):
        fp = self.fps[ref]
        at = find1(fp, 'at')
        at[1:] = [float(x + OX), float(y + OY)] + ([float(r)] if r else [])
        for p in find(fp, 'pad'):
            la = find1(p, '_local_angle')[1]
            pa = find1(p, 'at')
            a = (la + r) % 360
            pa[1:] = [pa[1], pa[2]] + ([float(a)] if a else [])
        for t in find(fp, 'property') + find(fp, 'fp_text'):
            ta = find1(t, 'at')
            la = find1(t, '_local_angle')
            if ta is None or la is None:
                continue
            a = (la[1] + r) % 360
            ta[1:] = [ta[1], ta[2]] + ([float(a)] if a else [])

    def fp_pos(self, ref):
        at = find1(self.fps[ref], 'at')
        return float(at[1]) - OX, float(at[2]) - OY, (float(at[3]) if len(at) > 3 else 0.0)

    # ---------- geometry ----------
    def pads(self, ref=None):
        """Yield dicts: ref,num,net,cx,cy,w,h,ang,shape,layers,drill (board-local mm)."""
        refs = [ref] if ref else list(self.fps)
        out = []
        for r in refs:
            fp = self.fps[r]
            fx, fy, fr = self.fp_pos(r)
            for p in find(fp, 'pad'):
                pa = find1(p, 'at')
                lx, ly = float(pa[1]), float(pa[2])
                dx, dy = rot(lx, ly, fr)
                sz = find1(p, 'size')
                pw, ph = float(sz[1]), float(sz[2])
                if str(p[3]) == 'custom':
                    # true copper extent of a custom pad = bounding box of its primitives (symmetric)
                    ex = [pw / 2]; ey = [ph / 2]
                    prims = find1(p, 'primitives') or []
                    for g in prims:
                        if not isinstance(g, list):
                            continue
                        if g[0] == 'gr_circle':
                            c = find1(g, 'center'); e = find1(g, 'end')
                            rr = math.hypot(float(e[1]) - float(c[1]), float(e[2]) - float(c[2]))
                            ex.append(abs(float(c[1])) + rr); ey.append(abs(float(c[2])) + rr)
                        elif g[0] == 'gr_poly':
                            for q in find1(g, 'pts')[1:]:
                                ex.append(abs(float(q[1]))); ey.append(abs(float(q[2])))
                    pw, ph = 2 * max(ex), 2 * max(ey)
                n = find1(p, 'net')
                dr = find1(p, 'drill')
                lay = find1(p, 'layers')[1:]
                drill = None
                if dr:
                    nums = [float(v) for v in dr[1:] if not isinstance(v, list) and v != 'oval']
                    drill = nums
                out.append(dict(ref=r, num=p[1], kind=str(p[2]), shape=str(p[3]),
                                net=n[2] if n else '', cx=fx + dx, cy=fy + dy,
                                w=pw, h=ph,
                                ang=(find1(p, '_local_angle')[1] + fr) % 360,
                                layers=[str(l) for l in lay], drill=drill))
        return out

    def pad(self, ref, num):
        for p in self.pads(ref):
            if p['num'] == num:
                return p
        raise KeyError((ref, num))

    def courtyard(self, ref):
        """Axis-aligned courtyard bbox in board-local coords."""
        fp = self.fps[ref]
        fx, fy, fr = self.fp_pos(ref)
        pts = []
        for g in fp:
            if isinstance(g, list) and g and g[0] in ('fp_line', 'fp_rect', 'fp_circle', 'fp_poly'):
                ly = find1(g, 'layer')
                if not ly or ly[1] not in ('F.CrtYd', 'B.CrtYd'):
                    continue
                if g[0] == 'fp_circle':
                    c = find1(g, 'center'); e = find1(g, 'end')
                    cx, cy = float(c[1]), float(c[2])
                    rr = math.hypot(float(e[1]) - cx, float(e[2]) - cy)
                    pts += [(cx - rr, cy - rr), (cx + rr, cy + rr), (cx - rr, cy + rr), (cx + rr, cy - rr)]
                else:
                    for k in ('start', 'end'):
                        e = find1(g, k)
                        if e:
                            pts.append((float(e[1]), float(e[2])))
        if fr in (0.0,):
            g = pts
        else:
            g = [rot(x, y, fr) for x, y in pts]
        xs = [fx + x for x, _ in g]; ys = [fy + y for _, y in g]
        return min(xs), min(ys), max(xs), max(ys)

    def save(self, path):
        def strip(x):
            if isinstance(x, list):
                return [strip(i) for i in x if not (isinstance(i, list) and i and i[0] == '_local_angle')]
            return x
        open(path, 'w').write(ser(strip(self.tree)) + '\n')
