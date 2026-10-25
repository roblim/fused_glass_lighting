#!/usr/bin/env python3
"""Attach the manufacturer 3D models in fgl_g2/3dmodels/ to the G2 board, and bring the
Degson port footprints on the board in line with fgl.pretty (outline fix of 2026-10-24).

Idempotent: replaces every (model ...) block of the listed footprints.

KiCad conventions used for the transforms (model frame = footprint frame with Y up, Z up
from the board's top surface; rotations are clockwise-positive and applied X, Y, Z, then
the offset in mm):

  J1  USB-C       LCSC C165948 model, front at -Y: turn 180, shift so the shell legs and
                  pegs land on the footprint's holes.
  F1  PTC fuse    LCSC C269137 model, already centred with the pads along X.
  J9/J10 sockets  LCSC C27985232 (Hong Cheng HC-PM254-5.0H-1x7PZ): pins along X, centred.
  J3  socket      1x5 derived from the 1x7 model (tools/trim_socket_1x5.py; LCSC's own 1x5
                  model is 8.5 mm tall, but the part is 5.0 mm). Pins at x = -7.62 ... 2.54.
  J3  + module    Hi-Link's HLK-LD2410S STEP: J2 pins at x = 18.476, y = 8.219 + 2.54(k-1),
                  header plastic underside at z = -3.8, pin tips at z = -9.8 (6.0 mm
                  pins). Antenna side up, pin k in socket pin k. Height: the socket's
                  contacts end 1.0 mm above the board (LCSC model), so 6.0 mm pins bottom
                  out there and the plastic sits at z = 7.0, 2 mm above the socket top.
                  That is what the 3D view shows; see g2_decisions.md D15.
  J5-J8 ports     Degson STEP (via the footprint, same transform as gen_g2_footprints.py).
  J9  + XIAO      XIAO ESP32C3 board and headers on J9/J10 (see XIAO below).
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "kicad", "fgl_g2", "fgl_g2.kicad_pcb")
D = "${KIPRJMOD}/3dmodels/"

PIN_FLOOR = 1.0   # z of the socket contact bottom (C27985232 model): deepest a pin tip can go
SOCKET7 = (D + "HC-PM254-5.0H-1x7PZ_LCSC_C27985232.step", (0, -7.62, 0), (0, 0, 90))
MODELS = {
    "J1": [(D + "USB_C_HRO_TYPE-C-31-M-12_LCSC_C165948.step", (0, -1.045, 0), (0, 0, 180))],
    "F1": [(D + "Fuse_SMD1812B150TF_LCSC_C269137.step", (0, 0, 0), (0, 0, 0))],
    "J9": [SOCKET7],
    "J10": [SOCKET7],
    "J3": [(D + "HC-PM254-5.0H-1x5PZ_from_1x7.step", (0, -7.62, 0), (0, 0, 90)),
           (D + "HLK-LD2410S.step", (18.476, 8.219, PIN_FLOOR + 9.8), (0, 0, 180))],
}
DEGSON = (D + "Degson_DG250-3.5-03P-11-00A_Z_H.stp", (1.7, 3.7, 5.75), (180, 0, -90))
for r in ("J5", "J6", "J7", "J8"):
    MODELS[r] = [DEGSON]

# XIAO ESP32C3 on J9/J10, sitting on its pre-soldered headers.
#  - Board: 3dmodels/XIAO_ESP32C3.step, Maurice Pannard's model on GrabCAD (the one Seeed's
#    wiki links; drawn from Seeed's DXF, SoC shield corrected from Seeed's drawing). It is
#    Y-up with the USB-C on +X; castellations at x = -5.88 + 2.54 i, pin rows at z = 1.509 and
#    -13.731, PCB 0..1 mm in y. Pin 1 (D0) is at the USB end of the z = -13.731 row. Mapped
#    by a least-squares fit of all 14 pins to the J9/J10 pads (residual 0): X +90 (KiCad -90),
#    then Z 90 CCW (KiCad -90), offset (13.731, -9.36).
#  - Headers: no model ships the pre-soldered headers, so KiCad's stock 1x7 2.54 mm header is
#    used, upside down: 3 mm tails up through the XIAO, 2.5 mm plastic under it, 6 mm pins down.
#  - Height: 6 mm pins bottom out on the socket contacts at z = PIN_FLOOR, so the header plastic
#    sits at z = 7.0 and the XIAO PCB underside at z = 9.5.
XIAO_Z = PIN_FLOOR + 6.0 + 2.5
HEADER7 = ("${KICAD9_3DMODEL_DIR}/Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x07_P2.54mm_Vertical.step",
           (0, 0, XIAO_Z), (0, 180, 0))
MODELS["J9"] = [SOCKET7, HEADER7, (D + "XIAO_ESP32C3.step", (13.731, -9.36, XIAO_Z), (-90, 0, -90))]
MODELS["J10"] = [SOCKET7, HEADER7]

# Degson outline on the board: old -> new numbers (see gen_g2_footprints.py)
DEGSON_GFX = [
    ("(start -3.32 -9.27)\n\t\t\t(end 8.92 -9.27)", "(start -1.92 -9.27)\n\t\t\t(end 10.32 -9.27)"),
    ("(start -3.32 2.47)\n\t\t\t(end -3.32 -9.27)", "(start -1.92 2.47)\n\t\t\t(end -1.92 -9.27)"),
    ("(start 8.92 -9.27)\n\t\t\t(end 8.92 2.47)", "(start 10.32 -9.27)\n\t\t\t(end 10.32 2.47)"),
    ("(start 8.92 2.47)\n\t\t\t(end -3.32 2.47)", "(start 10.32 2.47)\n\t\t\t(end -1.92 2.47)"),
    ("(start -3.7 -9.65)\n\t\t\t(end 9.3 5.25)", "(start -2.3 -10.15)\n\t\t\t(end 10.7 2.85)"),
    ("(start -3.2 -9.15)\n\t\t\t(end 8.8 2.35)", "(start -1.8 -9.65)\n\t\t\t(end 10.2 2.35)"),
]


def fmt(v):
    return ("%.4f" % v).rstrip("0").rstrip(".") if v != int(v) else str(int(v))


def model_block(path, off, rot):
    return ('\t\t(model "%s"\n\t\t\t(offset\n\t\t\t\t(xyz %s)\n\t\t\t)\n\t\t\t(scale\n\t\t\t\t(xyz 1 1 1)\n'
            '\t\t\t)\n\t\t\t(rotate\n\t\t\t\t(xyz %s)\n\t\t\t)\n\t\t)\n'
            % (path, " ".join(fmt(v) for v in off), " ".join(fmt(v) for v in rot)))


def main():
    t = open(PCB).read()
    starts = [m.start() for m in re.finditer(r"\n\t\(footprint ", t)]
    out, last = [], 0
    done = set()
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else _block_end(t, s)
        blk = t[s:e]
        ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
        if ref in MODELS:
            blk = re.sub(r'\t\t\(model "[^"]*"\n(?:\t\t\t.*\n)*?\t\t\)\n', "", blk)
            if ref in ("J5", "J6", "J7", "J8"):
                for a, b in DEGSON_GFX:
                    blk = blk.replace(a, b)
                for a, b in DEGSON_GFX:
                    assert b in blk, (ref, b)
            add = "".join(model_block(*m) for m in MODELS[ref])
            k = blk.rindex("\t\t(embedded_fonts")
            blk = blk[:k] + add + blk[k:]
            done.add(ref)
        out.append(t[last:s]); out.append(blk); last = e
    out.append(t[last:])
    missing = set(MODELS) - done
    if missing:
        sys.exit("footprints not found: %s" % sorted(missing))
    open(PCB, "w").write("".join(out))
    print("models set on", ", ".join(sorted(done)))


def _block_end(t, s):
    depth = 0
    i = t.index("(", s)
    while True:
        c = t[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        elif c == '"':
            i = t.index('"', i + 1)
            while t[i - 1] == "\\":
                i = t.index('"', i + 1)
        i += 1


if __name__ == "__main__":
    main()
