#!/usr/bin/env python3
"""Clear the label overlaps Flux's schematic review found (2026-10-28). Connectivity unchanged.

usage: tidy_g2_labels.py fgl_g2.kicad_sch

- JP1: the GND symbol on pin 2 sat between the RS2_B and ISEL labels. RS2_B and ISEL now
  leave pins 1 and 3 vertically (up and down), and GND hangs off a short stub on pin 2.
- JP2: the GND symbol on pin 1 sat on the RADAR_MODE wire; it now hangs off a stub that
  steps up and away from pin 2's wire.
- VBUS_IN: the PWR_FLAG now connects by a wire to F1's input instead of a second
  VBUS_IN label running alongside its own stub, and sits below the section title.
- F1 and Q2: Reference and Value no longer print on top of each other or of VBUS_IN.
"""
import re, sys
from schlib import wire, label, f

path = sys.argv[1]
t = open(path).read()


def drop(kind, pattern):
    """Remove the one top-level item of `kind` whose text matches `pattern`."""
    global t
    hits = [m for m in re.finditer(r'\n\t\(%s[ \n].*?\n\t\)' % kind, t, re.S) if re.search(pattern, m.group(0))]
    assert len(hits) == 1, (kind, pattern, len(hits))
    m = hits[0]
    t = t[:m.start()] + t[m.end():]


def wire_pat(x1, y1, x2, y2):
    return r'\(xy %s %s\) \(xy %s %s\)' % tuple(re.escape(f(v)) for v in (x1, y1, x2, y2))


def label_pat(name, x, y):
    return r'\(label "%s"\n\t\t\(at %s %s ' % (re.escape(name), re.escape(f(x)), re.escape(f(y)))


def move_symbol(ref, x, y, rot):
    global t
    i = t.index(f'(property "Reference" "{ref}"')
    st = t.rfind('\n\t(symbol\n', 0, i); en = t.index('\n\t)', i) + 3
    blk = t[st:en]
    m = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
    dx, dy = x - float(m.group(1)), y - float(m.group(2))
    blk = blk[:m.start()] + f'\n\t\t(at {f(x)} {f(y)} {f(rot)})' + blk[m.end():]
    blk = re.sub(r'\n\t\t\t\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)',
                 lambda k: f'\n\t\t\t(at {f(float(k.group(1)) + dx)} {f(float(k.group(2)) + dy)} {k.group(3)})', blk)
    t = t[:st] + blk + t[en:]


def set_field(ref, name, x, y, ang):
    global t
    i = t.index(f'(property "Reference" "{ref}"')
    st = t.rfind('\n\t(symbol\n', 0, i); en = t.index('\n\t)', i) + 3
    blk = t[st:en]
    blk = re.sub(r'(\(property "%s" "[^"]*"\n\t\t\t)\(at [^)]*\)' % name,
                 lambda k: k.group(1) + f'(at {f(x)} {f(y)} {f(ang)})', blk, count=1)
    t = t[:st] + blk + t[en:]


new = []
W = lambda *p: new.extend(wire(*p[i], *p[i + 1]) for i in range(len(p) - 1))

# JP2 (pins at x 99.06; pin 1 = 175.26 GND, pin 2 = 177.8 RADAR_MODE)
drop('wire', wire_pat(99.06, 175.26, 96.52, 175.26))
move_symbol('#PWR059', 93.98, 172.72, 270)
W((99.06, 175.26), (96.52, 175.26), (96.52, 172.72), (93.98, 172.72))

# JP1 (pins at x 215.9; 1 = 187.96 RS2_B, 2 = 190.5 GND, 3 = 193.04 ISEL)
for y in (187.96, 190.5, 193.04):
    drop('wire', wire_pat(215.9, y, 213.36, y))
drop('label', label_pat('RS2_B', 213.36, 187.96))
drop('label', label_pat('ISEL', 213.36, 193.04))
move_symbol('#PWR030', 210.82, 190.5, 270)
W((215.9, 187.96), (213.36, 187.96), (213.36, 185.42))
new.append(label('RS2_B', 213.36, 185.42, 90, 'left bottom'))
W((215.9, 190.5), (210.82, 190.5))
W((215.9, 193.04), (213.36, 193.04), (213.36, 195.58))
new.append(label('ISEL', 213.36, 195.58, 270, 'right bottom'))

# VBUS_IN: PWR_FLAG wired to F1 pin 1 (68.58, 40.64)
drop('wire', wire_pat(60.96, 27.94, 60.96, 30.48))
drop('label', label_pat('VBUS_IN', 60.96, 30.48))
drop('wire', wire_pat(68.58, 40.64, 66.04, 40.64))
drop('label', label_pat('VBUS_IN', 66.04, 40.64))
move_symbol('#FLG007', 60.96, 38.1, 0)                # clear of the section title; 2.54 mm stub
W((60.96, 38.1), (60.96, 40.64), (68.58, 40.64))         # (verify_netlist finds a flag's net there)
new.append(label('VBUS_IN', 60.96, 40.64, 180, 'right bottom'))

# F1 and Q2 fields (both symbols rotated 90: a field at angle 90 prints horizontally,
# right-aligned to its anchor)
set_field('F1', 'Reference', 72.39, 36.83, 90)
set_field('F1', 'Value', 75.57, 44.45, 90)
set_field('Q2', 'Reference', 116.84, 33.02, 90)
set_field('Q2', 'Value', 116.84, 35.56, 90)

ins = t.index('\n\t(sheet_instances')
t = t[:ins] + '\n' + ''.join(new).rstrip('\n') + t[ins:]
open(path, 'w').write(t)
print('done')
