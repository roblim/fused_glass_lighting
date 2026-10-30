"""Copy the Reference property position/layer of the given parts from one board to another.

usage: apply_refs.py placed.kicad_pcb target.kicad_pcb REF [REF ...]
`placed` is refspots.py's output (re-serialised); the target keeps KiCad's own formatting,
and only the lines of each Reference property's position, layer and hide flag change.
"""
import re, sys

src, dst, refs = sys.argv[1], sys.argv[2], sys.argv[3:]
placed = open(src).read()
text = open(dst).read()

PROP = r'(\t\t\(property "Reference" "{ref}"\n)(\t\t\t\(at [^)]*\)\n)(\t\t\t\(layer "[^"]+"\)\n)(\t\t\t\(hide yes\)\n)?'
for ref in refs:
    m = re.search(PROP.format(ref=re.escape(ref)), placed)
    assert m, ref
    at, layer = m.group(2), m.group(3)
    assert m.group(4) is None and '"F.SilkS"' in layer, ref
    text, n = re.subn(PROP.format(ref=re.escape(ref)), lambda k: k.group(1) + at + layer, text)
    assert n == 1, (ref, n)
    print(ref, at.strip(), layer.strip())
open(dst, 'w').write(text)
