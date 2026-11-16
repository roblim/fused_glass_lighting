"""Minimal KiCad 7-format schematic writer.

Symbols are copied from the KiCad libraries (or a project .kicad_sym), flattened
if derived, and placed on a 1.27 mm grid. Every connected pin gets a short wire
stub ending in a net label or a power symbol, so connectivity is explicit and
can be checked from KiCad's own netlist export. Files written here open in
KiCad 7, 8 and 9 (8/9 upgrade the format on save).
"""
import math
import os
import re
import uuid

KICAD_SYMBOLS = next((p for p in (
    os.environ.get("KICAD_SYMBOL_DIR", ""),
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols",
    "/usr/share/kicad/symbols") if p and os.path.isdir(p)), "/usr/share/kicad/symbols")
GRID = 1.27
POWER_NETS = {"GND": "power:GND", "+5V": "power:+5V", "+3V3": "power:+3V3"}


_UUID_NS = uuid.UUID("6f1c2b8e-0d7a-4f43-9a51-3c2b1f0e9d10")
_uuid_counter = [0]


def _u():
    """Deterministic UUIDs, so regenerating an unchanged design gives an identical file."""
    _uuid_counter[0] += 1
    return str(uuid.uuid5(_UUID_NS, str(_uuid_counter[0])))


def _f(v):
    v = round(v, 4)
    return str(int(v)) if v == int(v) else ("%.4f" % v).rstrip("0").rstrip(".")


def _q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def snap(v):
    return round(round(v / GRID) * GRID, 4)


# ---------------------------------------------------------------- library access
def _block(text, name):
    i = text.find('(symbol "%s"' % name)
    if i < 0:
        raise KeyError(name)
    depth, j, n = 0, i, len(text)
    while j < n:
        c = text[j]
        if c == '"':
            j += 1
            while text[j] != '"':
                j += 2 if text[j] == "\\" else 1
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
        j += 1
    raise ValueError("unbalanced " + name)


def _top_level_children(blk):
    """Yield (start, end) spans of the direct children of the outer list."""
    depth, j, start = 0, 0, None
    while j < len(blk):
        c = blk[j]
        if c == '"':
            j += 1
            while blk[j] != '"':
                j += 2 if blk[j] == "\\" else 1
        elif c == "(":
            depth += 1
            if depth == 2:
                start = j
        elif c == ")":
            if depth == 2:
                yield start, j + 1
            depth -= 1
        j += 1


class Library:
    def __init__(self, extra=None):
        self.cache = {}
        self.extra = extra or {}      # nickname -> path

    def text(self, nick):
        if nick not in self.cache:
            path = self.extra.get(nick, os.path.join(KICAD_SYMBOLS, nick + ".kicad_sym"))
            self.cache[nick] = open(path).read()
        return self.cache[nick]

    def symbol(self, lib_id):
        """Flattened symbol text renamed to lib_id, plus its pins."""
        nick, name = lib_id.split(":")
        txt = self.text(nick)
        blk = _block(txt, name)
        m = re.search(r'\(extends "([^"]+)"\)', blk)
        if m:
            parent = _block(txt, m.group(1))
            pname = m.group(1)
            # properties from the derived symbol, graphics/pins from the parent
            props = [blk[a:b] for a, b in _top_level_children(blk)
                     if blk[a:b].startswith("(property")]
            body = []
            for a, b in _top_level_children(parent):
                part = parent[a:b]
                if part.startswith("(property"):
                    continue
                if part.startswith('(symbol "%s_' % pname):
                    part = part.replace('(symbol "%s_' % pname, '(symbol "%s_' % name, 1)
                body.append(part)
            head = re.match(r'\(symbol "[^"]+"((?:\s*\((?:pin_names|pin_numbers|power|in_bom|on_board|exclude_from_sim)[^()]*(?:\([^()]*\))*[^()]*\))*)', parent)
            flags = head.group(1) if head else ""
            blk = '(symbol "%s"%s\n %s\n %s)' % (name, flags, "\n ".join(props), "\n ".join(body))
        pins = parse_pins(blk, name)
        blk = blk.replace('(symbol "%s"' % name, '(symbol "%s"' % lib_id, 1)
        return blk, pins


def parse_pins(blk, name):
    """[(number, name, etype, x, y, angle, hidden)] for unit 0/1, body style 1."""
    pins = []
    for sub in re.finditer(r'\(symbol "%s_(\d+)_(\d+)"' % re.escape(name), blk):
        unit, style = int(sub.group(1)), int(sub.group(2))
        if unit not in (0, 1) or style not in (0, 1):
            continue
        sb = _block(blk[sub.start():], "%s_%s_%s" % (name, sub.group(1), sub.group(2)))
        for pm in re.finditer(r'\(pin (\w+) \w+\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)\s*\(length [-\d.]+\)(\s*hide)?'
                              r'.*?\(name "([^"]*)".*?\(number "([^"]*)"', sb, re.S):
            et, x, y, a, hid, nm, num = pm.groups()
            pins.append((num, nm, et, float(x), float(y), int(float(a)), bool(hid)))
    return pins


# ---------------------------------------------------------------- schematic
class Schematic:
    def __init__(self, project, title, rev, date, company, comments=(), paper="A3", lib=None):
        self.project, self.title, self.rev, self.date = project, title, rev, date
        self.company, self.comments, self.paper = company, comments, paper
        _uuid_counter[0] = 0
        self.root = _u()
        self.lib = lib or Library()
        self.libsyms = {}
        self.items = []
        self.pwr_n = 0
        self.points = {}          # (x,y) -> ref:pin, to catch accidental overlaps
        self.parts = []           # (ref, lib_id, value, fields, dnp)

    # -- primitives
    def _use(self, lib_id):
        if lib_id not in self.libsyms:
            self.libsyms[lib_id] = self.lib.symbol(lib_id)
        return self.libsyms[lib_id]

    def wire(self, x1, y1, x2, y2):
        self.items.append('(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid %s))'
                          % (_f(x1), _f(y1), _f(x2), _f(y2), _u()))

    def label(self, net, x, y, outward):
        ang = {"right": 0, "up": 90, "left": 180, "down": 270}[outward]
        just = "left" if outward in ("right", "up") else "right"
        self.items.append('(label %s (at %s %s %d) (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify %s bottom)) (uuid %s))'
                          % (_q(net), _f(x), _f(y), ang, just, _u()))

    def noconnect(self, x, y):
        self.items.append('(no_connect (at %s %s) (uuid %s))' % (_f(x), _f(y), _u()))

    def text(self, s, x, y, size=1.27, bold=False):
        b = " bold" if bold else ""
        self.items.append('(text %s (at %s %s 0) (effects (font (size %s %s)%s) (justify left top)) (uuid %s))'
                          % (_q(s), _f(x), _f(y), _f(size), _f(size), b, _u()))

    def box(self, x1, y1, x2, y2, title):
        self.items.append('(rectangle (start %s %s) (end %s %s) (stroke (width 0.254) (type dash) (color 110 110 110 1)) (fill (type none)) (uuid %s))'
                          % (_f(x1), _f(y1), _f(x2), _f(y2), _u()))
        self.text(title, x1 + 1.27, y1 + 1.27, 1.8, True)

    def power(self, net, x, y, outward):
        lib_id = POWER_NETS[net]
        self._use(lib_id)
        if net == "GND":
            rot = {"down": 0, "right": 90, "up": 180, "left": 270}[outward]
        else:
            rot = {"up": 0, "left": 90, "down": 180, "right": 270}[outward]
        self.pwr_n += 1
        ref = "#PWR%03d" % self.pwr_n
        vx, vy = {"down": (0, 4.2), "up": (0, -4.2), "left": (-5.5, 0), "right": (5.5, 0)}[outward] \
            if net != "GND" else {"down": (0, 5.0), "up": (0, -5.0), "left": (-5.0, 0), "right": (5.0, 0)}[outward]
        self.items.append(
            '(symbol (lib_id %s) (at %s %s %d) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid %s)\n'
            '  (property "Reference" %s (at %s %s 0) (effects (font (size 1.27 1.27)) hide))\n'
            '  (property "Value" %s (at %s %s 0) (effects (font (size 1.27 1.27))))\n'
            '  (property "Footprint" "" (at %s %s 0) (effects (font (size 1.27 1.27)) hide))\n'
            '  (property "Datasheet" "" (at %s %s 0) (effects (font (size 1.27 1.27)) hide))\n'
            '  (pin "1" (uuid %s))\n'
            '  (instances (project %s (path "/%s" (reference %s) (unit 1)))))'
            % (_q(lib_id), _f(x), _f(y), rot, _u(), _q(ref), _f(x), _f(y), _q(net),
               _f(x + vx), _f(y + vy), _f(x), _f(y), _f(x), _f(y), _u(),
               _q(self.project), self.root, _q(ref)))

    def pwr_flag(self, net, x, y):
        """PWR_FLAG with a stub downwards to a label or power symbol."""
        self._use("power:PWR_FLAG")
        self.pwr_n += 1
        ref = "#FLG%03d" % self.pwr_n
        self.items.append(
            '(symbol (lib_id "power:PWR_FLAG") (at %s %s 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid %s)\n'
            '  (property "Reference" %s (at %s %s 0) (effects (font (size 1.27 1.27)) hide))\n'
            '  (property "Value" "PWR_FLAG" (at %s %s 0) (effects (font (size 1 1)) hide))\n'
            '  (property "Footprint" "" (at %s %s 0) (effects (font (size 1.27 1.27)) hide))\n'
            '  (property "Datasheet" "" (at %s %s 0) (effects (font (size 1.27 1.27)) hide))\n'
            '  (pin "1" (uuid %s))\n'
            '  (instances (project %s (path "/%s" (reference %s) (unit 1)))))'
            % (_f(x), _f(y), _u(), _q(ref), _f(x), _f(y), _f(x), _f(y - 3), _f(x), _f(y), _f(x), _f(y),
               _u(), _q(self.project), self.root, _q(ref)))
        self.wire(x, y, x, y + 2.54)
        self._terminate(net, x, y + 2.54, "down")

    def _terminate(self, net, x, y, outward):
        if net in POWER_NETS:
            self.power(net, x, y, outward)
        else:
            self.label(net, x, y, outward)

    # -- parts
    def place(self, lib_id, ref, value, x, y, nets, rot=0, footprint="", fields=None,
              ref_at=None, val_at=None, stub=2.54, dnp=False, hide_value=False, mirror=None,
              on_board=True, stubs=None):
        """nets: {pin number or pin name: net | 'NC'}; unlisted pins must not exist.
        stubs: optional {pin number: stub length} to stagger crowded labels."""
        x, y = snap(x), snap(y)
        blk, pins = self._use(lib_id)
        fields = dict(fields or {})
        seen_xy = {}
        used_keys = set()
        pin_uuids = []
        for num, nm, et, px, py, ang, hid in pins:
            pin_uuids.append('(pin %s (uuid %s))' % (_q(num), _u()))
            key = num if num in nets else nm
            if key not in nets:
                raise KeyError("%s pin %s/%s has no net" % (ref, num, nm))
            used_keys.add(key)
            r = math.radians(rot)
            rx = px * math.cos(r) - py * math.sin(r)
            ry = px * math.sin(r) + py * math.cos(r)
            ax, ay = round(x + rx, 4), round(y - ry, 4)
            out = (ang + 180 + rot) % 360
            outward = {0: "right", 90: "up", 180: "left", 270: "down"}[out]
            net = nets[key]
            if (ax, ay) in seen_xy:            # stacked pins
                if seen_xy[(ax, ay)] != net:
                    raise ValueError("%s stacked pins disagree" % ref)
                continue
            seen_xy[(ax, ay)] = net
            if (ax, ay) in self.points:
                raise ValueError("%s pin %s lands on %s" % (ref, num, self.points[(ax, ay)]))
            self.points[(ax, ay)] = "%s:%s" % (ref, num)
            if net == "NC":
                self.noconnect(ax, ay)
                continue
            dx, dy = {"right": (1, 0), "left": (-1, 0), "up": (0, -1), "down": (0, 1)}[outward]
            st = (stubs or {}).get(num, stub)
            if net in POWER_NETS and outward in ("left", "right"):
                st = max(stub, 5.08)       # keep a sideways power symbol clear of the body
            ex, ey = ax + dx * st, ay + dy * st
            self.wire(ax, ay, ex, ey)
            if net.startswith("="):        # wire stub only; joins another stub end
                continue
            self._terminate(net, ex, ey, outward)
        extra = set(nets) - used_keys
        if extra:
            raise KeyError("%s: nets for unknown pins %s" % (ref, sorted(extra)))
        ref_at = ref_at or (x + 2.54, y - 1.27)
        val_at = val_at or (x + 2.54, y + 1.27)
        props = [
            '(property "Reference" %s (at %s %s %d) (effects (font (size 1.27 1.27)) (justify left)))' % (_q(ref), _f(ref_at[0]), _f(ref_at[1]), rot % 180),
            '(property "Value" %s (at %s %s %d) (effects (font (size 1.27 1.27)) (justify left)%s))' % (_q(value), _f(val_at[0]), _f(val_at[1]), rot % 180, " hide" if hide_value else ""),
            '(property "Footprint" %s (at %s %s 0) (effects (font (size 1.27 1.27)) hide))' % (_q(footprint), _f(x), _f(y)),
            '(property "Datasheet" %s (at %s %s 0) (effects (font (size 1.27 1.27)) hide))' % (_q(fields.pop("Datasheet", "")), _f(x), _f(y)),
        ]
        for k, v in fields.items():
            props.append('(property %s %s (at %s %s 0) (effects (font (size 1.27 1.27)) hide))' % (_q(k), _q(v), _f(x), _f(y)))
        self.items.append(
            '(symbol (lib_id %s) (at %s %s %d) (unit 1) (in_bom yes) (on_board %s) (dnp %s) (uuid %s)\n  %s\n  %s\n'
            '  (instances (project %s (path "/%s" (reference %s) (unit 1)))))'
            % (_q(lib_id), _f(x), _f(y), rot, "yes" if on_board else "no", "yes" if dnp else "no", _u(), "\n  ".join(props),
               " ".join(pin_uuids), _q(self.project), self.root, _q(ref)))
        f2 = dict(fields)
        self.parts.append(dict(ref=ref, lib_id=lib_id, value=value, footprint=footprint,
                               dnp=dnp, fields=f2))

    # -- output
    def write(self, path):
        libs = "\n".join(b for b, _ in self.libsyms.values())
        com = "".join(" (comment %d %s)" % (i + 1, _q(c)) for i, c in enumerate(self.comments))
        s = ('(kicad_sch (version 20230121) (generator eeschema)\n'
             '  (uuid %s)\n  (paper %s)\n'
             '  (title_block (title %s) (date %s) (rev %s) (company %s)%s)\n'
             '  (lib_symbols\n%s\n  )\n%s\n'
             '  (sheet_instances (path "/" (page "1")))\n)\n'
             % (self.root, _q(self.paper), _q(self.title), _q(self.date), _q(self.rev), _q(self.company),
                com, libs, "\n".join(self.items)))
        open(path, "w").write(s)


def write_project(dirpath, name, sym_libs=(), fp_libs=()):
    """Minimal .kicad_pro plus sym-lib-table / fp-lib-table for project libraries."""
    open(os.path.join(dirpath, name + ".kicad_pro"), "w").write(
        '{\n  "meta": {"filename": "%s.kicad_pro", "version": 1},\n'
        '  "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},\n'
        '  "boards": [], "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},\n'
        '  "sheets": [], "text_variables": {}\n}\n' % name)
    if sym_libs:
        open(os.path.join(dirpath, "sym-lib-table"), "w").write(
            "(sym_lib_table\n" + "".join(
                '  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s")(options "")(descr "%s"))\n' % t
                for t in sym_libs) + ")\n")
    if fp_libs:
        open(os.path.join(dirpath, "fp-lib-table"), "w").write(
            "(fp_lib_table\n" + "".join(
                '  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s")(options "")(descr "%s"))\n' % t
                for t in fp_libs) + ")\n")
