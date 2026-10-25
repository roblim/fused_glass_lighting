"""KiCad position CSV -> JLCPCB CPL for fgl_g2, with JLC rotation corrections.

Corrections: SOT-23 and HRO USB-C as checked for G1 (matthewlai/JLCKicadTools cpl_rotations_db.csv,
2026-10-22). The HTSSOP and pin-socket entries follow the same table's TSSOP / PinSocket rules and
are UNCONFIRMED for these exact footprints, as are the JST PH and Degson parts (no correction).
Always check every part in JLCPCB's placement preview before paying.
"""
import csv, re
CORR = [(r'^TSOT-23', 180), (r'^SOT-23', -90), (r'^USB_C_Receptacle_HRO_TYPE-C-31-M-12', 180),
        (r'HTSSOP-', 270), (r'^PinSocket_1x0[57]_P2.54mm_Vertical', 270)]
CHECK = (r'HTSSOP-', r'^PinSocket_', r'^PinHeader_', r'^JST_PH_', r'^TerminalBlock_Degson', r'^D_SMA', r'^L_Sunlord')
bom = {}
for row in csv.DictReader(open('../bom_jlcpcb.csv')):
    for d in row['Designator'].split(','):
        bom[d.strip()] = row
out, skipped = [], []
for r in csv.DictReader(open('fgl_g2-pos-kicad.csv')):
    ref = r['Ref']
    if ref not in bom:
        skipped.append(ref); continue
    rot = float(r['Rot'])
    corr = next((c for p, c in CORR if re.search(p, r['Package'])), 0)
    out.append([ref, f"{float(r['PosX']):.4f}mm", f"{float(r['PosY']):.4f}mm", 'Top', f"{(rot + corr) % 360:g}",
                r['Package'], corr])
with open('fgl_g2-cpl-jlcpcb.csv', 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for o in out:
        w.writerow(o[:5])
missing = sorted(set(bom) - {o[0] for o in out})
print('CPL rows', len(out), '| in pos but not JLC BOM (hand/DNP):', skipped, '| in BOM but missing from CPL:', missing)
for o in out:
    if o[6]:
        print('  corrected', o[0], o[5], 'kicad', (float(o[4]) - o[6]) % 360, 'corr', o[6])
print('  check in the JLC preview:', sorted(o[0] for o in out if any(re.search(p, o[5]) for p in CHECK)))
