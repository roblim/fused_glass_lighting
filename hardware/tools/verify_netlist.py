#!/usr/bin/env python3
"""Check a KiCad-exported netlist against hand-written design intent.

usage: verify_netlist.py <netlist.net> <expected_module> <schematic.kicad_sch> <project_dir>

1. Connectivity: every expected net exists with exactly the expected pins, and
   KiCad has no other multi-pin nets.
2. Unconnected pins: exactly the expected no-connects; nothing else floats.
3. Electrical rules KiCad 7's CLI can't run (no `erc` command before KiCad 8):
   power inputs driven, no two outputs on one net, no single-pin labelled nets.
4. Footprints: every footprint exists, and its pads match the symbol's pins.
5. BOM fields: every fitted, placeable part has LCSC and MPN; DNP flags as intended.
"""
import importlib
import os
import re
import sys

FP_DIR = next((p for p in (
    os.environ.get("KICAD_FOOTPRINT_DIR", ""),
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints",
    "/usr/share/kicad/footprints") if p and os.path.isdir(p)), "/usr/share/kicad/footprints")


def sexp_blocks(text, head):
    out, i = [], 0
    while True:
        i = text.find("(" + head, i)
        if i < 0:
            return out
        d, j = 0, i
        while True:
            c = text[j]
            if c == '"':
                j += 1
                while text[j] != '"':
                    j += 2 if text[j] == "\\" else 1
            elif c == "(":
                d += 1
            elif c == ")":
                d -= 1
                if d == 0:
                    break
            j += 1
        out.append(text[i:j + 1])
        i = j + 1


def parse_netlist(path):
    t = open(path).read()
    comps = {}
    for c in sexp_blocks(t, "comp (ref"):
        ref = re.search(r'\(ref "([^"]+)"\)', c).group(1)
        fp = re.search(r'\(footprint "([^"]*)"\)', c)
        fields = dict(re.findall(r'\(field \(name "([^"]+)"\)\s*"((?:[^"\\]|\\.)*)"\)', c))
        comps[ref] = dict(fp=fp.group(1) if fp else "", fields=fields,
                          dnp='(property (name "dnp")' in c)
    nets = {}
    for n in sexp_blocks(t, "net (code"):
        name = re.search(r'\(name "([^"]*)"\)', n).group(1)
        nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)(?: \(pinfunction "[^"]*"\))? \(pintype "([^"]+)"\)', n)
        nets[name] = [(r, p, ty) for r, p, ty in nodes]
    return comps, nets


def footprint_pads(fp, project_dir):
    lib, name = fp.split(":")
    path = os.path.join(project_dir, lib + ".pretty", name + ".kicad_mod") if lib == "fgl" \
        else os.path.join(FP_DIR, lib + ".pretty", name + ".kicad_mod")
    if not os.path.exists(path):
        return None
    pads = set(re.findall(r'\(pad "?([^" ]*)"? ', open(path).read()))
    return pads


def main(netfile, expected_mod, schfile, project_dir):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    E = importlib.import_module(expected_mod)
    comps, nets = parse_netlist(netfile)
    errors, notes = [], []

    pin_net = {}
    multi = {}
    for name, nodes in nets.items():
        clean = name.lstrip("/")
        for r, p, ty in nodes:
            pin_net[r + "." + p] = clean
        if not name.startswith("unconnected-") and not name.startswith("Net-("):
            multi[clean] = nodes
        elif name.startswith("Net-("):
            multi[clean] = nodes

    # 1. connectivity
    for net, want in E.NETS.items():
        got = {r + "." + p for r, p, _ in multi.get(net, [])}
        if not got:
            errors.append("missing net %s" % net)
            continue
        if got != want:
            if want - got:
                errors.append("%s: missing %s" % (net, sorted(want - got)))
            if got - want:
                errors.append("%s: unexpected %s" % (net, sorted(got - want)))
    for net in multi:
        if net not in E.NETS:
            errors.append("unexpected net %s: %s" % (net, multi[net]))

    # 2. unconnected pins
    floating = {r + "." + p for name, nodes in nets.items() if name.startswith("unconnected-")
                for r, p, _ in nodes}
    if floating != E.NO_CONNECT:
        if floating - E.NO_CONNECT:
            errors.append("pins left unconnected: %s" % sorted(floating - E.NO_CONNECT))
        if E.NO_CONNECT - floating:
            errors.append("expected no-connects that are connected: %s" % sorted(E.NO_CONNECT - floating))
    # Collapse whitespace so the same regexes read KiCad 7 (one line per item) and KiCad 9 (indented) files
    sch = re.sub(r"\s+", " ", open(schfile).read())
    n_nc = sch.count("(no_connect ")
    if n_nc != len(E.NO_CONNECT):
        errors.append("schematic has %d no-connect flags, expected %d" % (n_nc, len(E.NO_CONNECT)))

    # 3. electrical rules
    # KiCad drops PWR_FLAGs from the netlist. Each flag's stub ends 2.54 mm below it
    # in a net label or a power symbol, so recover the flagged nets geometrically.
    ends = {}
    for m in re.finditer(r'\(label "([^"]+)" \(at ([-\d.]+) ([-\d.]+)', sch):
        ends[(round(float(m.group(2)), 2), round(float(m.group(3)), 2))] = m.group(1)
    for blk in sexp_blocks(sch, 'symbol (lib_id "power:'):
        m = re.match(r'\(symbol \(lib_id "power:([^"]+)"\) \(at ([-\d.]+) ([-\d.]+)', blk)
        if m and m.group(1) != "PWR_FLAG":
            ends[(round(float(m.group(2)), 2), round(float(m.group(3)), 2))] = m.group(1)
    flag_nets = set()
    for blk in sexp_blocks(sch, 'symbol (lib_id "power:PWR_FLAG")'):
        m = re.match(r'\(symbol \(lib_id "power:PWR_FLAG"\) \(at ([-\d.]+) ([-\d.]+)', blk)
        key = (round(float(m.group(1)), 2), round(float(m.group(2)) + 2.54, 2))
        if key in ends:
            flag_nets.add(ends[key])
        else:
            errors.append("PWR_FLAG at %s has no net" % (key,))
    for net, nodes in multi.items():
        types = [ty for _, _, ty in nodes]
        if "power_in" in types and "power_out" not in types and net not in flag_nets:
            errors.append("%s: power input pins with no power source or PWR_FLAG" % net)
        drivers = [r + "." + p for r, p, ty in nodes if ty in ("output", "power_out")]
        if len(drivers) > 1:
            errors.append("%s: multiple drivers %s" % (net, drivers))
        if len(nodes) < 2:
            errors.append("%s: single-pin net" % net)

    # 4. footprints vs pins
    pins_by_ref = {}
    for key in pin_net:
        r, p = key.split(".", 1)
        pins_by_ref.setdefault(r, set()).add(p)
    for r, p in (k.split(".", 1) for k in floating):
        pins_by_ref.setdefault(r, set()).add(p)
    check_fp = getattr(E, "CHECK_FOOTPRINTS", True)
    for ref, c in sorted(comps.items()) if check_fp else []:
        if not c["fp"]:
            errors.append("%s has no footprint" % ref)
            continue
        pads = footprint_pads(c["fp"], project_dir)
        if pads is None:
            errors.append("%s footprint not found: %s" % (ref, c["fp"]))
            continue
        pads.discard("")
        pins = pins_by_ref.get(ref, set())
        if pins - pads:
            errors.append("%s: symbol pins with no pad %s" % (ref, sorted(pins - pads)))
        if pads - pins:
            errors.append("%s: pads with no symbol pin %s" % (ref, sorted(pads - pins)))
    for ref, fp in getattr(E, "FOOTPRINT_PADS", {}).items():
        if comps.get(ref, {}).get("fp") != fp:
            errors.append("%s footprint %s, expected %s" % (ref, comps.get(ref, {}).get("fp"), fp))

    # 5. BOM fields and DNP
    for ref, c in sorted(comps.items()) if check_fp else []:
        if ref.startswith(("TP", "H")):
            continue
        f = c["fields"]
        if ref == "U1":
            if not f.get("MPN"):
                errors.append("U1 has no MPN")
            continue
        if not f.get("LCSC") or not f.get("MPN"):
            errors.append("%s missing LCSC/MPN" % ref)
    dnp_sch = set()
    for blk in sexp_blocks(sch, "symbol (lib_id"):
        if "(dnp yes)" in blk:
            m = re.search(r'\(property "Reference" "([^"]+)"', blk)
            dnp_sch.add(m.group(1))
    if dnp_sch != E.DNP:
        errors.append("DNP set %s, expected %s" % (sorted(dnp_sch), sorted(E.DNP)))

    nets_n = len(E.NETS)
    pins_n = sum(len(v) for v in E.NETS.values())
    if errors:
        print("FAIL")
        for e in errors:
            print("  -", e)
        return 1
    print("PASS: %d nets, %d connections, %d no-connects, %d parts; %s"
          % (nets_n, pins_n, len(E.NO_CONNECT), len(comps),
             "footprints and BOM fields OK" if check_fp else "footprint/BOM checks not applicable"))
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
