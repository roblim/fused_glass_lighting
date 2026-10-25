#!/usr/bin/env python3
"""Write bom.csv (grouped, every part) and bom_jlcpcb.csv (JLCPCB assembly upload)
from a KiCad-exported netlist.

usage: make_bom.py <netlist.net> <out_dir> [expected_module]

With an expected module (e.g. g2_expected), its HAND set says which parts are not
fitted by JLCPCB, its NO_LCSC set lists PCB-only items left out, and its BOM_EXTRA rows
are added as written (loose parts, the plug-in XIAO); a part listed there is not also
listed from the netlist.

JLCPCB list = SMD parts with an LCSC number, fitted. Left out: U1 (XIAO, hand-
soldered), the through-hole JST connectors J2-J5 (hand-soldered or JLCPCB
standard PCBA), test points, holes and DNP parts.
"""
import csv
import os
import re
import sys

from verify_netlist import parse_netlist

HAND = {"U1", "J2", "J3", "J4", "J5"}


def natural(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def main(netfile, outdir, expected=None):
    hand, skip = HAND, set()
    if expected:
        import importlib
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        E = importlib.import_module(expected)
        hand, skip = set(getattr(E, "HAND", HAND)), set(getattr(E, "NO_LCSC", ()))
    comps, _ = parse_netlist(netfile)
    extra = [list(r) for r in getattr(E, "BOM_EXTRA", [])] if expected else []
    # parts that BOM_EXTRA describes itself (e.g. U1, the XIAO, which the schematic
    # also carries as an off-board symbol) are listed once, from BOM_EXTRA
    covered = {ref.strip() for r in extra for ref in str(r[1]).split(",")}
    t = open(netfile).read()
    values = dict(re.findall(r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]*)"\)', t)) or \
        {r: c.get("value", "") for r, c in comps.items()}
    groups = {}
    for ref, c in comps.items():
        if ref.startswith(("TP", "H")) or ref in skip or ref in covered:
            continue
        f = c["fields"]
        key = (values.get(ref, ""), c["fp"], f.get("MPN", ""), f.get("LCSC", ""), c["dnp"])
        groups.setdefault(key, []).append(ref)
    rows = []
    for (val, fp, mpn, lcsc, dnp), refs in groups.items():
        refs.sort(key=natural)
        mfr = comps[refs[0]]["fields"].get("Manufacturer", "")
        how = "DNP" if dnp else ("hand" if set(refs) & hand else "JLCPCB")
        rows.append([len(refs), ",".join(refs), val, fp.split(":")[-1], mpn, mfr, lcsc, how])
    rows += extra
    rows.sort(key=lambda r: natural(r[1].split(",")[0]))
    with open(os.path.join(outdir, "bom.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Qty", "References", "Value", "Footprint", "MPN", "Manufacturer", "LCSC", "Assembly"])
        w.writerows(rows)
    with open(os.path.join(outdir, "bom_jlcpcb.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for r in rows:
            if r[7] == "JLCPCB":
                w.writerow([r[2], r[1], r[3], r[6]])
    n_j = sum(r[0] for r in rows if r[7] == "JLCPCB")
    print("bom.csv: %d lines; bom_jlcpcb.csv: %d placements" % (len(rows), n_j))


if __name__ == "__main__":
    main(*sys.argv[1:4])
