#!/usr/bin/env python3
"""Redraw section 2 of the G2 schematic (TPS61500 SEPIC) with wires instead of repeated labels.

usage: redraw_g2_sepic.py fgl_g2.kicad_sch

Same parts, same nets, same net names: each net in the section is drawn as wires, with one
label naming it (and labels only where a net leaves the section: DIM_PWM from the MCU,
VOUT and LED_RTN to the ports and sense resistors). Three redundant +5V symbols go.
Layout (mm, 1.27 grid): power path along y = 45.72, left to right
  +5V -> C2, C3 -> L1 -> SW -> C4 -> SEP_B (L2 to GND) -> D5 -> VOUT (R15/R16, C5, C6),
U2 below with SW, OVP and FB on its right, and EN, DIMC, SS, COMP, FREQ fanned out to the
left: R17/R18 on EN, then C7, C8, C9, R19 in a row below.
"""
import re, sys
from schlib import Sch, wire, junction, label, f

path = sys.argv[1]
s = Sch(path)
txt = s.text
X0, Y0, X1, Y1 = 157.48, 22.86, 302.26, 132.08          # section 2 box

# ---- 1. drop the section's wires and labels (the section title text stays) ----
drop = [it for it in s.items_in(X0, Y0, X1, Y1) if str(it[0]) in ('wire', 'label', 'junction')]
uuids = []
for it in drop:
    u = [x for x in it if isinstance(x, list) and str(x[0]) == 'uuid'][0][1]
    uuids.append(u)


def remove_block(t, u, kinds=('wire', 'label', 'junction', 'symbol')):
    i = t.index(f'(uuid "{u}")')
    st = max(t.rfind(f'\n\t({k}', 0, i) for k in kinds)
    en = t.index('\n\t)', i) + 3
    return t[:st] + t[en:]


for u in uuids:
    txt = remove_block(txt, u)
print(f'removed {len(uuids)} wires/labels')


# ---- 2. move symbols ----
def block_of(t, ref):
    i = t.index(f'(property "Reference" "{ref}"')
    st = t.rfind('\n\t(symbol\n', 0, i)
    en = t.index('\n\t)', i) + 3
    return st, en


for ref in ('#PWR012', '#PWR017', '#PWR019'):            # redundant +5V symbols
    st, en = block_of(txt, ref)
    txt = txt[:st] + txt[en:]

# columns (x) of the parts on U2's left: fields print to the right of each part, so each
# column leaves room for the previous part's value text ("100n 50V" is about 9.5 mm)
COL = {'DIMC': 173.99, 'SS': 185.42, 'COMP': 200.66, 'FREQ': 214.63}
UX, UY = 232.41, 81.28                                   # U2: left pins 2.54 mm right of FREQ
R = UX + 15.24                                           # U2 right-hand pin x
SWX = R + 5.08                                           # SW node
C4X = SWX + 2.54                                         # C4 (pin 1 on the SW node)
SBX = C4X + 5.08                                         # SEP_B node, L2
D5X = SBX + 5.08                                         # D5 (anode 2.54 left, cathode 2.54 right)
VX = D5X + 3.81                                          # VOUT node just right of D5's cathode: R15/R16
C5X, C6X = VX + 5.08, VX + 19.05                         # output capacitors
R17X, R18X = 161.29, 168.91
P = {   # ref: (x, y, rot)
    'U2': (UX, UY, 0),
    '#PWR015': (165.1, 45.72, 0),                         # +5V
    'C2': (170.18, 50.8, 0), '#PWR016': (170.18, 55.88, 0),
    'C3': (182.88, 50.8, 0), '#PWR018': (182.88, 55.88, 0),
    'L1': (220.98, 45.72, 90),
    'C4': (C4X, 45.72, 90),
    'L2': (SBX, 55.88, 0), '#PWR020': (SBX, 62.23, 0),
    'D5': (D5X, 45.72, 180),
    'C5': (C5X, 50.8, 0), '#PWR021': (C5X, 55.88, 0),
    'C6': (C6X, 50.8, 0), '#PWR022': (C6X, 55.88, 0),
    'R15': (VX, 71.12, 0),
    'R16': (VX, 86.36, 0), '#PWR023': (VX, 91.44, 0),
    'R17': (R17X, 63.5, 0),
    'R18': (R18X, 78.74, 0), '#PWR024': (R18X, 83.82, 0),
    'C7': (COL['DIMC'], 101.6, 0), '#PWR025': (COL['DIMC'], 106.68, 0),
    'C8': (COL['SS'], 101.6, 0), '#PWR026': (COL['SS'], 106.68, 0),
    'C9': (COL['COMP'], 101.6, 0), '#PWR027': (COL['COMP'], 106.68, 0),
    'R19': (COL['FREQ'], 101.6, 0), '#PWR028': (COL['FREQ'], 106.68, 0),
    '#PWR013': (UX - 2.54, UY + 20.32, 0), '#PWR014': (UX + 2.54, UY + 20.32, 0),   # AGND, PGND
}
FIELDS = {  # explicit Reference / Value placement: (dx, dy, justify, angle) from the symbol
    'R17': ((2.54, -1.27, 'left', 0), (2.54, 1.27, 'left', 0)),
    'R18': ((-2.54, -1.27, 'right', 0), (-2.54, 1.27, 'right', 0)),
    # C4 and D5 sit in the power path: both fields above it, centred (a field on a
    # 90-degree symbol is stored at 90 to print horizontally)
    'C4': ((0, -6.35, None, 90), (0, -3.81, None, 90)),
    'D5': ((0, -6.35, None, 0), (0, -3.81, None, 0)),
}
for ref, (x, y, rot) in P.items():
    st, en = block_of(txt, ref)
    blk = txt[st:en]
    m = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
    ox, oy = float(m.group(1)), float(m.group(2))
    dx, dy = x - ox, y - oy
    blk = blk[:m.start()] + f'\n\t\t(at {f(x)} {f(y)} {f(rot)})' + blk[m.end():]

    def mv(mm):
        return f'\n\t\t\t(at {f(float(mm.group(1)) + dx)} {f(float(mm.group(2)) + dy)} {mm.group(3)})'
    blk = re.sub(r'\n\t\t\t\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', mv, blk)
    if ref in FIELDS:
        for name, (fx, fy, just, ang) in zip(('Reference', 'Value'), FIELDS[ref]):
            pm = re.search(r'\(property "%s" "[^"]*"\n\t\t\t\(at [^)]*\)(.*?)\n\t\t\)' % name, blk, re.S)
            body = pm.group(0)
            body = re.sub(r'\n\t\t\t\(at [^)]*\)', f'\n\t\t\t(at {f(x + fx)} {f(y + fy)} {ang})', body, count=1)
            if just:
                body = re.sub(r'\(justify \w+\)', f'(justify {just})', body)
            else:
                body = re.sub(r'\n\t\t\t\t\(justify \w+\)', '', body)
            blk = blk[:pm.start()] + body + blk[pm.end():]
    txt = txt[:st] + blk + txt[en:]

# ---- 3. wires, junctions, labels ----
new = []
W = lambda *pts: new.extend(wire(*pts[i], *pts[i + 1]) for i in range(len(pts) - 1))
J = lambda x, y: new.append(junction(x, y))
L = lambda *a, **k: new.append(label(*a, **k))
Lx = UX - 15.24                                           # U2 left-hand pin x
Y = 45.72                                                 # power path

# input rail: +5V, C2, C3, VIN riser, L1
W((165.1, Y), (170.18, Y), (182.88, Y), (208.28, Y), (217.17, Y))
W((170.18, Y), (170.18, 48.26)); W((170.18, 53.34), (170.18, 55.88))
W((182.88, Y), (182.88, 48.26)); W((182.88, 53.34), (182.88, 55.88))
W((208.28, Y), (208.28, UY - 10.16), (Lx, UY - 10.16))   # VIN (pin 3)
J(170.18, Y); J(182.88, Y); J(208.28, Y)
# SW node: L1 -> C4 pin 1, down to U2 pins 1 and 2
W((224.79, Y), (SWX, Y))
W((SWX, Y), (SWX, UY - 10.16), (SWX, UY - 7.62))
W((R, UY - 10.16), (SWX, UY - 10.16)); W((R, UY - 7.62), (SWX, UY - 7.62))
J(SWX, Y); J(SWX, UY - 10.16)
L('SW', SWX, UY - 7.62, 0)
# SEP_B: C4 pin 2 -> L2 (to GND) -> D5 anode
W((C4X + 2.54, Y), (SBX, Y), (D5X - 2.54, Y))
W((SBX, Y), (SBX, 52.07)); W((SBX, 59.69), (SBX, 62.23))
J(SBX, Y)
L('SEP_B', SBX, 52.07, 90)
# VOUT: D5 cathode -> divider, C5, C6
W((D5X + 2.54, Y), (VX, Y), (C5X, Y), (C6X, Y))
W((C5X, Y), (C5X, 48.26)); W((C5X, 53.34), (C5X, 55.88))
W((C6X, Y), (C6X, 48.26)); W((C6X, 53.34), (C6X, 55.88))
W((VX, Y), (VX, 68.58))
J(VX, Y); J(C5X, Y)
L('VOUT', C6X, Y, 0)
# OVP divider R15 / R16 and U2 pin 11
W((VX, 73.66), (VX, UY - 2.54), (VX, 83.82))
W((R, UY - 2.54), (VX, UY - 2.54))
W((VX, 88.9), (VX, 91.44))
J(VX, UY - 2.54)
L('OVP', VX, UY - 2.54, 0)
# FB (pin 9) -> LED_RTN (R20/R21 and the ports, section 3)
W((R, UY + 2.54), (R + 5.08, UY + 2.54))
L('LED_RTN', R + 5.08, UY + 2.54, 0)
# U2 ground pins
W((UX - 2.54, UY + 17.78), (UX - 2.54, UY + 20.32)); W((UX + 2.54, UY + 17.78), (UX + 2.54, UY + 20.32))
# EN: DIM_PWM -> R17 -> DRV_EN (R18 to GND) -> pin 4
W((R17X, 60.96), (R17X, 58.42))
L('DIM_PWM', R17X, 58.42, 90)
W((R17X, 66.04), (R17X, UY - 7.62), (R18X, UY - 7.62), (Lx, UY - 7.62))
W((R18X, UY - 7.62), (R18X, 76.2)); W((R18X, 81.28), (R18X, 83.82))
J(R18X, UY - 7.62)
L('DRV_EN', R18X, UY - 7.62, 0)
# DIMC, SS, COMP, FREQ fanned out to C7, C8, C9, R19 (outer pin to the outer column)
for name, pin_dy in (('DIMC', -5.08), ('SS', -2.54), ('COMP', 0.0), ('FREQ', 2.54)):
    x = COL[name]
    W((Lx, UY + pin_dy), (x, UY + pin_dy), (x, 93.98), (x, 99.06))
    W((x, 104.14), (x, 106.68))
    L(name, x, 93.98, 90)

ins = txt.index('\n\t(sheet_instances')
txt = txt[:ins] + '\n' + ''.join(new).rstrip('\n') + txt[ins:]
open(path, 'w').write(txt)
print(f'added {sum(1 for n in new if "(wire" in n)} wires, {sum(1 for n in new if "(junction" in n)} junctions, '
      f'{sum(1 for n in new if "(label" in n)} labels')
