#!/usr/bin/env python3
"""Write a PADS-PCB ASCII netlist from a KiCad netlist (XML or s-expression).

usage: make_pads_netlist.py <netlist.net> <out.asc>

For tools that read PADS-PCB rather than KiCad netlists (Pinscope, for example).
The layout follows KiCad's own PADS exporter (eeschema File > Export > Netlist > PADS):
*PADS-PCB*, a *PART* section (reference, footprint), a *NET* section with one *SIGNAL*
per net listing REF.PIN nodes, then *END*. Spaces in names become underscores.
Nets with a single node (unconnected pins, including the intentional no-connects) are
left out: in a PADS netlist an unlisted pin is an unconnected pin.
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_netlist import parse_netlist


def natural(s):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', s)]


def main(src, dst):
    comps, nets = parse_netlist(src)
    out = ['*PADS-PCB*', '*PART*']
    for ref in sorted(comps, key=natural):
        fp = (comps[ref]['fp'] or comps[ref].get('value', '') or 'NOFOOTPRINT').strip().replace(' ', '_')
        out.append(f'{ref:<16} {fp}')
    out += ['', '*NET*']
    kept = skipped = 0
    for name in sorted(nets, key=natural):
        nodes = sorted({(r, p) for r, p, _ in nets[name]}, key=lambda n: (natural(n[0]), natural(n[1])))
        if len(nodes) < 2:
            skipped += 1
            continue
        kept += 1
        out.append('*SIGNAL* ' + name.replace(' ', '_'))
        toks = [f'{r}.{p}' for r, p in nodes]
        for i in range(0, len(toks), 8):        # PADS readers expect modest line lengths
            out.append(' '.join(toks[i:i + 8]))
    out.append('*END*')
    with open(dst, 'w') as f:
        f.write('\n'.join(out) + '\n')
    print(f'{dst}: {len(comps)} parts, {kept} nets ({skipped} single-pin nets left out)')


if __name__ == '__main__':
    main(*sys.argv[1:3])
