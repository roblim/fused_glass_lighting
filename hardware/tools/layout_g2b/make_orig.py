"""Make the unplaced input board for the 90 x 60 mm relayout (D19) from the D18 board.

Keeps every footprint as it is on the D18 board (properties, 3D models, U2's enlarged thermal vias,
fab text), drops all copper, zones and board graphics, and applies the D19 schematic changes:
  - J5..J8: JILN JL212R-35003B01 horizontal push-in ports (fgl.pretty footprint);
  - C16: 0402 -> 0603;
  - R29: new 10 k pull-up, +3V3 (pad 1) -> RADAR_MODE (pad 2), cloned from R23.
Net names lose their leading '/' (the layout scripts use bare names; emit.py puts them back).
usage: make_orig.py d18.kicad_pcb fgl.pretty orig.kicad_pcb
"""
import sys, uuid, copy, re
from sx import parse, ser, find, find1, Sym

src, lib, dst = sys.argv[1:4]
T = parse(open(src).read())
U = lambda: str(uuid.uuid4())
DROP = {'segment', 'via', 'zone', 'gr_line', 'gr_arc', 'gr_text', 'gr_rect', 'gr_poly', 'gr_circle', 'group', 'dimension'}
T[:] = [i for i in T if not (isinstance(i, list) and i and i[0] in DROP)]


def bare(n):
    return n[1:] if n.startswith('/') else n


def walk(x):
    if isinstance(x, list):
        if len(x) == 3 and x[0] == 'net' and isinstance(x[2], str) and not isinstance(x[2], Sym):
            x[2] = bare(x[2])
        for i in x:
            walk(i)


walk(T)
nets = {n[2]: int(n[1]) for n in find(T, 'net')}
fps = {[p[2] for p in find(f, 'property') if p[1] == 'Reference'][0]: f for f in find(T, 'footprint')}


def newuuids(x):
    if isinstance(x, list):
        if len(x) == 2 and x[0] in ('uuid', 'tstamp') and isinstance(x[1], str):
            x[0] = Sym('uuid'); x[1] = U()
        for i in x:
            newuuids(i)


def set_prop(fp, name, val):
    for p in find(fp, 'property'):
        if p[1] == name:
            p[2] = val; return
    raise KeyError(name)


def pad_nets(fp):
    out = {}
    for p in find(fp, 'pad'):
        n = find1(p, 'net')
        if n:
            out[p[1]] = (int(n[1]), n[2])
    return out


# ---- J5..J8 -> JL212R
mod = parse(open(lib + '/TerminalBlock_JILN_JL212R-3.5-03P_Horizontal.kicad_mod').read())
newuuids(mod)
body = [i for i in mod if isinstance(i, list) and i[0] in ('fp_line', 'fp_rect', 'pad', 'model')
        or (isinstance(i, list) and i[0] == 'fp_text' and i[1] == 'user')]
for ref in ('J5', 'J6', 'J7', 'J8'):
    fp = fps[ref]
    nn = pad_nets(fp)
    keep = [i for i in fp if not (isinstance(i, list) and i[0] in ('fp_line', 'fp_rect', 'fp_text', 'pad', 'model', 'fp_circle', 'fp_poly', 'fp_arc'))]
    keep[1] = 'fgl:TerminalBlock_JILN_JL212R-3.5-03P_Horizontal'
    for i in keep:
        if isinstance(i, list) and i[0] == 'descr':
            i[1] = find1(mod, 'descr')[1]
        if isinstance(i, list) and i[0] == 'tags':
            i[1] = find1(mod, 'tags')[1]
    new = copy.deepcopy(body)
    newuuids(new)
    for it in new:
        if it[0] == 'pad':
            n = nn[it[1]]
            k = [j for j, x in enumerate(it) if isinstance(x, list) and x[0] == 'uuid'][0]
            it.insert(k, [Sym('net'), n[0], n[1]])
    # embedded_fonts must stay before model in KiCad 9's order; put the new items before it
    k = [j for j, x in enumerate(keep) if isinstance(x, list) and x[0] == 'embedded_fonts']
    k = k[0] if k else len(keep)
    fp[:] = keep[:k] + new + keep[k:]
    # model goes last
    m = [x for x in fp if isinstance(x, list) and x[0] == 'model']
    fp[:] = [x for x in fp if not (isinstance(x, list) and x[0] == 'model')] + m

# ---- C16 -> 0603 (clone C11's 0603 footprint)
nn = pad_nets(fps['C16'])
c = copy.deepcopy(fps['C11'])
newuuids(c)
set_prop(c, 'Reference', 'C16'); set_prop(c, 'Value', '100n 50V')
for p in find(c, 'pad'):
    n = find1(p, 'net'); n[1], n[2] = nn[p[1]]
T[T.index(fps['C16'])] = c
fps['C16'] = c

# ---- R29 (clone R23)
r = copy.deepcopy(fps['R23'])
newuuids(r)
set_prop(r, 'Reference', 'R29'); set_prop(r, 'Value', '10k')
for p in find(r, 'pad'):
    name = '+3V3' if p[1] == '1' else 'RADAR_MODE'
    n = find1(p, 'net'); n[1], n[2] = nets[name], name
T.insert(T.index(fps['R23']) + 1, r)

open(dst, 'w').write(ser(T) + '\n')
print('footprints', len(find(T, 'footprint')), 'nets', len(nets))
