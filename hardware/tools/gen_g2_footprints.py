#!/usr/bin/env python3
"""Write the Rev G2 project footprint into kicad/fgl_g2/fgl.pretty (KiCad 7 format; KiCad 9 reads it).

(The XIAO sockets J9/J10 use KiCad's PinSocket_1x07_P2.54mm_Vertical; place them per Seeed's
XIAO-ESP32-C3-DIP geometry: rows 15.24 mm apart, pin 1 at the USB-C end. xiao() below draws
that outline for reference only and is not written.)

TerminalBlock_Degson_DG250-3.5-03P
    Degson DG250-3.5-03P-11-00A(H) push-in terminal block, 3 poles, 3.5 mm pitch.
    From Degson's drawing DG250-3.5-XXP-1Y-00A&Z(H).dxf (downloaded 2026-10-23):
    one pin per pole, staggered: odd poles in row A, even poles in row B, rows 5.0 mm apart;
    recommended hole 1.2 mm; body length 3.5 x N + 1.5 mm; body edge 2.35 mm beyond row A,
    depth 12 mm, wire entry on the row-B side (-Y here).
    Checked 2026-10-24 against Degson's STEP DG250-3.5-03P-11-00A&Z(H).stp: with the wire
    entry toward -Y, pin 1 is 1.8 mm and the last pin 3.2 mm from the body ends. (Until
    2026-10-24 this outline was mirrored: 3.2 mm at pin 1. The pads were always right.)
    3D model: Degson's STEP, in ../kicad/fgl_g2/3dmodels/.
"""
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "kicad", "fgl_g2", "fgl.pretty")
NS = uuid.UUID("0c7e4a51-2d8b-4e7a-9f0e-6a1b3c5d7e90")
_n = [0]


def u():
    _n[0] += 1
    return str(uuid.uuid5(NS, str(_n[0])))


def line(x1, y1, x2, y2, layer, w=0.12):
    return ('  (fp_line (start %g %g) (end %g %g) (stroke (width %g) (type solid)) (layer "%s") (tstamp %s))\n'
            % (x1, y1, x2, y2, w, layer, u()))


def rect(x1, y1, x2, y2, layer, w=0.05):
    return ('  (fp_rect (start %g %g) (end %g %g) (stroke (width %g) (type solid)) (fill none) (layer "%s") (tstamp %s))\n'
            % (x1, y1, x2, y2, w, layer, u()))


def text(kind, s, x, y, layer, size=1.0, thick=0.15):
    head = 'fp_text %s "%s"' % (kind, s)
    return ('  (%s (at %g %g) (layer "%s") (effects (font (size %g %g) (thickness %g))) (tstamp %s))\n'
            % (head, x, y, layer, size, size, thick, u()))


def pad(num, x, y, drill, size, square=False):
    shape = "rect" if square else "circle"
    return ('  (pad "%s" thru_hole %s (at %g %g) (size %g %g) (drill %g) (layers "*.Cu" "*.Mask") (tstamp %s))\n'
            % (num, shape, x, y, size, size, drill, u()))


def xiao():
    s = ('(footprint "XIAO_ESP32C3_Socketed" (version 20221018) (generator pcbnew)\n  (layer "F.Cu")\n'
         '  (descr "Seeed XIAO ESP32C3 in two 1x7 2.54 mm female sockets (low-profile, 5 mm). Pin positions from '
         'Seeed OPL_Kicad_Library XIAO-ESP32-C3-DIP (commit b0035c5, CC BY-SA 4.0). Pin 1 (D0) at the USB-C end.")\n'
         '  (tags "XIAO ESP32C3 socket")\n  (attr through_hole)\n')
    s += text("reference", "REF**", 0, -10.2, "F.SilkS")
    s += text("value", "XIAO_ESP32C3_Socketed", 0, 0, "F.Fab")
    s += text("user", "USB-C", 13.4, 0, "F.SilkS", 0.8, 0.12)
    # module outline (17.8 x 21 mm board, USB-C overhang at +x)
    s += line(-10.45, -8.9, 10.55, -8.9, "F.SilkS") + line(10.55, -8.9, 10.55, 8.9, "F.SilkS")
    s += line(10.55, 8.9, -10.45, 8.9, "F.SilkS") + line(-10.45, 8.9, -10.45, -8.9, "F.SilkS")
    s += line(10.55, -4.5, 12.05, -4.5, "F.SilkS") + line(12.05, -4.5, 12.05, 4.5, "F.SilkS")
    s += line(12.05, 4.5, 10.55, 4.5, "F.SilkS")
    s += rect(-10.45, -8.9, 10.55, 8.9, "F.Fab", 0.1)
    s += rect(-10.95, -9.4, 12.55, 9.4, "F.CrtYd")
    for k in range(7):          # pins 1-7: y = -7.62, x from +7.62 down; pins 8-14: y = +7.62, x from -7.62 up
        s += pad(str(k + 1), 7.62 - 2.54 * k, -7.62, 1.0, 1.7, square=(k == 0))
    for k in range(7):
        s += pad(str(k + 8), -7.62 + 2.54 * k, 7.62, 1.0, 1.7)
    return s + ")\n"


# Degson's STEP has the pins up (+Z) and the wire entry on +X: flip it over (X 180), turn it so the
# entry faces -Y on the PCB (Z -90 in KiCad's clockwise-positive convention), then put pin 1 on the origin.
MODEL_DEGSON = ('  (model "${KIPRJMOD}/3dmodels/Degson_DG250-3.5-03P-11-00A_Z_H.stp"\n'
                '    (offset (xyz 1.7 3.7 5.75)) (scale (xyz 1 1 1)) (rotate (xyz 180 0 -90)))\n')


def degson(n=3):
    pitch, row = 3.5, 5.0
    x0, x1 = -1.8, pitch * (n - 1) + 3.2          # body ends (Degson STEP)
    ya, yb = 2.35, 2.35 - 12.0                    # body edges: row A at y=0, row B at y=-5;
                                                  # wire entry face at yb
    s = ('(footprint "TerminalBlock_Degson_DG250-3.5-%02dP" (version 20221018) (generator pcbnew)\n  (layer "F.Cu")\n'
         '  (descr "Degson DG250-3.5-%02dP-11-00A(H) push-in PCB terminal block, %d poles, 3.5 mm pitch, staggered pins '
         '(rows 5.0 mm apart), 1.2 mm holes. From Degson drawing DG250-3.5-XXP-1Y-00A&Z(H). '
         'Legends: 1 + (string in), 2 NEXT (to next port), 3 END (string return).")\n'
         '  (tags "terminal block push-in Degson DG250 3.5mm")\n  (attr through_hole)\n') % (n, n, n)
    s += text("reference", "REF**", (x0 + x1) / 2, yb - 1.2, "F.SilkS")
    s += text("value", "DG250-3.5-%02dP" % n, (x0 + x1) / 2, -2.5, "F.Fab")
    s += rect(x0, yb, x1, ya, "F.Fab", 0.1)
    ys = yb + 0.38                                # silk front line kept 0.5 mm off the board edge
    s += line(x0 - 0.12, ys, x1 + 0.12, ys, "F.SilkS") + line(x1 + 0.12, ys, x1 + 0.12, ya + 0.12, "F.SilkS")
    s += line(x1 + 0.12, ya + 0.12, x0 - 0.12, ya + 0.12, "F.SilkS") + line(x0 - 0.12, ya + 0.12, x0 - 0.12, ys, "F.SilkS")
    s += rect(x0 - 0.5, yb - 0.5, x1 + 0.5, ya + 0.5, "F.CrtYd")
    legends = ["+", "NEXT", "END"] if n == 3 else [str(i + 1) for i in range(n)]
    for i in range(n):
        x, y = pitch * i, 0 if i % 2 == 0 else -row
        s += pad(str(i + 1), x, y, 1.2, 2.0, square=(i == 0))
        s += text("user", legends[i], x, ya + 1.45, "F.SilkS", 1.2 if legends[i] in "+" else 0.9, 0.18)
    s += MODEL_DEGSON
    return s + ")\n"


def main():
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "TerminalBlock_Degson_DG250-3.5-03P.kicad_mod"), "w").write(degson(3))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
