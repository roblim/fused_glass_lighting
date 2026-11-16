"""Check a laid-out .kicad_pcb against the hand-written design intent (g2_expected.py).

Every pad's net on the board must match the expected net (pads not listed must be unconnected),
and every expected footprint must be on the board. Usage: verify_pcb.py board.kicad_pcb g2_expected
"""
import importlib, re, sys, collections

def pads(path):
    t = open(path).read()
    out = {}
    for fp in re.split(r'\n\t\(footprint ', t)[1:]:
        m = re.search(r'\(property "Reference" "([^"]+)"', fp)
        ref = m.group(1)
        for pm in re.finditer(r'\(pad "([^"]*)" [^\n]*\n(.*?)\n\t\t\)', fp, re.S):
            num, body = pm.group(1), pm.group(2)
            nm = re.search(r'\(net \d+ "([^"]*)"\)', body)
            if num:
                out.setdefault(f'{ref}.{num}', set()).add(nm.group(1) if nm else '')
    return out

board, modname = sys.argv[1], sys.argv[2]
sys.path.insert(0, __file__.rsplit('/', 1)[0])
E = importlib.import_module(modname)
exp = {}
for net, pins in E.NETS.items():
    for p in pins:
        exp[p] = net
got = pads(board)
bad = []
for pin, nets in got.items():
    nets = {n.lstrip('/') for n in nets}
    want = exp.get(pin, '')
    if nets != {want}:
        bad.append((pin, sorted(nets), want))
refs_board = {p.split('.')[0] for p in got}
refs_exp = {p.split('.')[0] for p in exp} - set(getattr(E, 'NOT_ON_BOARD', ()))
missing_pins = sorted(p for p in exp if p.split('.')[0] in refs_exp and p not in got)
print(f'{len(got)} pads on {len(refs_board)} footprints checked against {len(E.NETS)} expected nets')
print('missing footprints:', sorted(refs_exp - refs_board) or 'none')
print('expected pins not on the board:', missing_pins or 'none')
for b in bad:
    print('MISMATCH', b)
print('PASS' if not bad and not missing_pins and refs_exp <= refs_board else 'FAIL')
sys.exit(0 if not bad else 1)
