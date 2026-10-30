"""Small helpers for reading and editing a KiCad 9 schematic as text.

Pin positions of placed symbols, items inside a region, and builders for wires,
labels, junctions and power symbols in KiCad's own formatting. Used by the G2
schematic clean-up scripts.
"""
import math, re, sys, os, uuid

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'layout_g2b'))
from sx import parse, find, find1  # noqa: E402


def U():
    return str(uuid.uuid4())


def f(v):
    s = f'{v:.4f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


class Sch:
    def __init__(self, path):
        self.path = path
        self.text = open(path).read()
        self.tree = parse(self.text)
        self.lib = {}
        for s in find(find1(self.tree, 'lib_symbols'), 'symbol'):
            self.lib[s[1]] = s

    # ---- library pins (symbol coordinates, y up) ----
    def lib_pins(self, lib_id, unit=1):
        out = {}
        sym = self.lib[lib_id]
        for sub in find(sym, 'symbol'):
            m = re.match(r'.*_(\d+)_(\d+)$', sub[1])
            if m and int(m.group(1)) not in (0, unit):
                continue
            for p in find(sub, 'pin'):
                at = find1(p, 'at')
                num = find1(p, 'number')[1]
                name = find1(p, 'name')[1]
                out.setdefault(num, (float(at[1]), float(at[2]), name))
        return out

    def placed(self):
        """[(ref, lib_id, x, y, rot, mirror, node)] for every placed symbol."""
        res = []
        for s in find(self.tree, 'symbol'):
            lid = find1(s, 'lib_id')
            if lid is None:
                continue
            at = find1(s, 'at')
            mir = find1(s, 'mirror')
            ref = [p[2] for p in find(s, 'property') if p[1] == 'Reference'][0]
            res.append((ref, lid[1], float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0,
                        str(mir[1]) if mir else None, s))
        return res

    def pin_xy(self, ref):
        """{pin number: (x, y, name)} on the sheet for a placed symbol."""
        for r, lid, x, y, rot, mir, s in self.placed():
            if r == ref:
                out = {}
                for num, (px, py, name) in self.lib_pins(lid).items():
                    if mir == 'x':
                        py = -py
                    elif mir == 'y':
                        px = -px
                    a = math.radians(rot)
                    rx = px * math.cos(a) - py * math.sin(a)
                    ry = px * math.sin(a) + py * math.cos(a)
                    out[num] = (round(x + rx, 4), round(y - ry, 4), name)
                return out
        raise KeyError(ref)

    def items_in(self, x0, y0, x1, y1):
        """wires, labels, junctions, no_connects and texts whose points are all inside the box."""
        def inside(px, py):
            return x0 <= px <= x1 and y0 <= py <= y1
        res = []
        for it in self.tree:
            if not isinstance(it, list):
                continue
            k = str(it[0])
            if k == 'wire':
                pts = find1(it, 'pts')[1:]
                if all(inside(float(p[1]), float(p[2])) for p in pts):
                    res.append(it)
            elif k in ('label', 'junction', 'no_connect', 'text', 'global_label', 'hierarchical_label'):
                at = find1(it, 'at')
                if inside(float(at[1]), float(at[2])):
                    res.append(it)
        return res


# ---- text builders in KiCad 9 formatting ----
def wire(x1, y1, x2, y2):
    return (f'\t(wire\n\t\t(pts\n\t\t\t(xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})\n\t\t)\n'
            f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n')


def junction(x, y):
    return (f'\t(junction\n\t\t(at {f(x)} {f(y)})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n'
            f'\t\t(uuid "{U()}")\n\t)\n')


def label(name, x, y, ang=0, justify='left bottom'):
    return (f'\t(label "{name}"\n\t\t(at {f(x)} {f(y)} {f(ang)})\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {justify})\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n')
