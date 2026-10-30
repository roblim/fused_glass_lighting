"""Top-silkscreen text tidy (2026-10-28): strokes up to JLCPCB's minimum, three pin legends spread.

usage: silk_tidy.py board.kicad_pcb

JLCPCB's character specification (checked 2026-10-28): 0.8 mm minimum height, 0.15 mm minimum
stroke, width-to-height 1:5 to 1:6; thinner strokes are widened at the factory or print blurred.
The G2 references and most legends were 0.8 mm at 0.12 mm (1:6.7). Edits the KiCad file as text:
only the thickness line inside F.SilkS text blocks changes. Footprint silkscreen lines (KiCad's
library 0.12 mm) are left alone.

Pin legends: at J4's 2 mm pitch "RX" and "OT2" ran together, and at J3 "3V3" and "GND"; OT2 moves
0.3 mm right, 3V3 0.2 mm left and GND 0.16 mm right (each still over its own pin).
"""
import re, sys

MIN = 0.15
path = sys.argv[1]
t = open(path).read()
n = 0


def fix(m):
    global n
    blk = m.group(0)
    if '(layer "F.SilkS")' not in blk or '(hide yes)' in blk:
        return blk

    def th(k):
        global n
        if float(k.group(1)) < MIN:
            n += 1
            return f'(thickness {MIN})'
        return k.group(0)
    return re.sub(r'\(thickness ([\d.]+)\)', th, blk)


# a text block: property / fp_text / gr_text up to its closing paren at the same indent
t = re.sub(r'(?m)^(\t+)\((?:property "Reference"|fp_text \w+|gr_text) .*?\n\1\)', fix, t, flags=re.S)
for name, old, new in (('OT2', '147.4', '147.7'), ('3V3', '170.2', '170'), ('GND', '172.74', '172.9')):
    t, k = re.subn(r'(gr_text "%s"\n\t\t\(at )%s ' % (name, re.escape(old)), lambda m: m.group(1) + new + ' ', t)
    print(f'legend {name}: {"moved" if k else "already moved or not found"}')
open(path, 'w').write(t)
print(f'{n} text strokes raised to {MIN} mm')
