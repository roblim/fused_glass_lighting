"""KiCad position CSV + board -> JLCPCB CPL for fgl_g2, with JLCPCB position and rotation corrections.

usage (in this folder): python3 make_cpl.py

Why corrections are needed: JLCPCB places each part with its own footprint for that LCSC part
(from the EasyEDA library), not ours. Two conventions differ:

- Position. JLCPCB's footprint origin is the centre of the part's pads. KiCad's is wherever the
  library author put it: the body centre for most SMD parts (same thing), but pin 1 for pin headers,
  sockets, JST connectors and our JL212R port blocks, and an off-centre point for the HRO USB-C.
  KiCad's position file reports that origin. So every row here uses the centre of the footprint's
  pad bounding box, computed from the board file, not the KiCad origin.
- Rotation. Each library draws its parts at 0 degrees in its own orientation; the difference
  depends on the individual JLCPCB footprint, so it is keyed by LCSC part number (C157923 and
  C157926 are both JST PH horizontal yet differ by 180 degrees).

ROT below is the rotation to add to KiCad's. Every entry was checked against JLCPCB's placement
preview of this board (2026-10-29, first order): "verified" means the preview matched the board
(pin 1 dot, body and pins over our pads); "fixed" means the preview showed it wrong with the
previous correction and the value here is derived from what the preview showed. Fixed entries
must be confirmed in the preview of the corrected CPL before paying, and so must UNVERIFIED
entries (a part not yet seen in any preview). Parts not listed get 0.
"""
import csv, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools', 'layout_g2b'))
from geom import Board, OX, OY   # noqa: E402

ROT = {   # LCSC: (degrees added to KiCad's rotation, status, what)
    'C20917':    (180, 'fixed 2026-10-29', 'AO3400A SOT-23 (was -90: body shown 90 deg off)'),
    'C15127':    (180, 'fixed 2026-10-29', 'AO3401A SOT-23 (was -90: body shown 90 deg off)'),
    'C165948':   (0,   'fixed 2026-10-29', 'HRO TYPE-C-31-M-12 USB-C (was 180: pins shown at the mouth)'),
    'C71160':    (270, 'verified 2026-10-29', 'TPS61500 HTSSOP-14, pin 1 dot at the SW end'),
    'C27985230': (270, 'verified 2026-10-29', '1x5 socket J3 (symmetric)'),
    'C27985232': (270, 'verified 2026-10-29', '1x7 sockets J9/J10 (symmetric)'),
    'C49257':    (270, 'fixed 2026-10-29', '1x3 header JP1/JP2 (was 0: shown across the pin row)'),
    'C157923':   (180, 'fixed 2026-10-29', 'JST S5B-PH-K J4 (was 0: shown facing inward)'),
    'C157926':   (0,   'verified 2026-10-29', 'JST S4B-PH-K J2 orientation'),
    'C2962951':  (180, 'fixed 2026-10-29', 'JILN JL212R ports (J5-J8 alternate) (was 0: wire face inward)'),
    'C7603454':  (180, 'UNVERIFIED', 'DEGSON DG212R ports J5-J8 (assumed drawn like the JL212R; check the preview)'),
    'C2480':     (0,   'verified 2026-10-29', 'SS14 SMA, cathode band'),
    'C2903825':  (0,   'verified 2026-10-29', 'SS36 SMA, cathode band'),
}

bom = {}
for row in csv.DictReader(open(os.path.join(HERE, '..', 'bom_jlcpcb.csv'))):
    for d in row['Designator'].split(','):
        bom[d.strip()] = row
b = Board(os.path.join(HERE, '..', 'fgl_g2.kicad_pcb'))


def pad_centre(ref):
    xs, ys = [], []
    for p in b.pads(ref):
        a = math.radians(p['ang'])
        hw = abs(p['w'] / 2 * math.cos(a)) + abs(p['h'] / 2 * math.sin(a))
        hh = abs(p['w'] / 2 * math.sin(a)) + abs(p['h'] / 2 * math.cos(a))
        xs += [p['cx'] - hw, p['cx'] + hw]; ys += [p['cy'] - hh, p['cy'] + hh]
    return (min(xs) + max(xs)) / 2 + OX, (min(ys) + max(ys)) / 2 + OY


out, skipped, moved = [], [], []
for r in csv.DictReader(open(os.path.join(HERE, 'fgl_g2-pos-kicad.csv'))):
    ref = r['Ref']
    if ref not in bom:
        skipped.append(ref); continue
    lcsc = bom[ref]['LCSC Part #']
    corr = ROT.get(lcsc, (0, '', ''))[0]
    cx, cy = pad_centre(ref)                       # KiCad coordinates, y down
    kx, ky = float(r['PosX']), -float(r['PosY'])
    if math.hypot(cx - kx, cy - ky) > 0.01:
        moved.append((ref, round(cx - kx, 2), round(cy - ky, 2)))
    rot = (float(r['Rot']) + corr) % 360
    out.append([ref, f'{cx:.4f}mm', f'{-cy:.4f}mm', 'Top', f'{rot:g}', lcsc])
with open(os.path.join(HERE, 'fgl_g2-cpl-jlcpcb.csv'), 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for o in out:
        w.writerow(o[:5])
missing = sorted(set(bom) - {o[0] for o in out})
print('CPL rows', len(out), '| in pos but not JLC BOM (hand/DNP):', skipped, '| in BOM but missing from CPL:', missing)
print('moved from the KiCad origin to the pad centre (dx, dy mm):', moved)
for o in out:
    if o[5] in ROT:
        c, st, what = ROT[o[5]]
        print(f'  {o[0]:4} rot {o[4]:>3}  (+{c})  {st:20} {what}')
