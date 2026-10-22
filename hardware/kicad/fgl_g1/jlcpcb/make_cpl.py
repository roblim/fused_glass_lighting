"""KiCad position CSV -> JLCPCB CPL, with JLC rotation corrections.

Corrections from matthewlai/JLCKicadTools cpl_rotations_db.csv (the table the
kicad-jlcpcb-tools plugin downloads), checked 2026-10-22. Always confirm in
JLCPCB's placement preview before paying.
"""
import csv, re, sys
CORR = [(r'^TSOT-23', 180), (r'^SOT-23', -90), (r'^USB_C_Receptacle_HRO_TYPE-C-31-M-12', 180)]
bom = {}
for row in csv.DictReader(open('../bom_jlcpcb.csv')):
    for d in row['Designator'].split(','):
        bom[d.strip()] = row
out = []
skipped = []
for r in csv.DictReader(open('fgl_g1-pos-kicad.csv')):
    ref = r['Ref']
    if ref not in bom:
        skipped.append(ref); continue
    rot = float(r['Rot'])
    corr = next((c for p, c in CORR if re.search(p, r['Package'])), 0)
    jrot = (rot + corr) % 360
    out.append([ref, f"{float(r['PosX']):.4f}mm", f"{float(r['PosY']):.4f}mm", 'Top', f"{jrot:g}", r['Package'], corr])
w = csv.writer(open('fgl_g1-cpl-jlcpcb.csv', 'w', newline=''))
w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
for o in out:
    w.writerow(o[:5])
missing = sorted(set(bom) - {o[0] for o in out})
print('CPL rows', len(out), '| in pos but not JLC BOM (hand/DNP):', skipped, '| in BOM but missing from CPL:', missing)
for o in out:
    if o[6]: print('  corrected', o[0], o[5], 'kicad', o[4], 'corr', o[6])
