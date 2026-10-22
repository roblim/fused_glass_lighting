#!/usr/bin/env python3
"""Generate the Rev G1 controller schematic (KiCad 7 format).

RETIRED 2026-10-15: the schematic was upgraded and saved in KiCad 9.0.7 and is now
the source of truth. This script refuses to overwrite it unless run with --force.
Kept as the record of how G1 was first drawn.

Design intent and the reasoning for every value are in docs/design_review.md.
The connections are checked independently by verify_netlist.py against
g1_expected.py, which is written by hand and does not import this file.
"""
import os
import sys

import kgen
import symlib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "kicad", "fgl_g1")
PROJ = "fgl_g1"

R0603 = "Resistor_SMD:R_0603_1608Metric"
R1206 = "Resistor_SMD:R_1206_3216Metric"
R2512 = "Resistor_SMD:R_2512_6332Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
SMA = "Diode_SMD:D_SMA"


def lcsc(code, mpn, mfr):
    return {"LCSC": code, "MPN": mpn, "Manufacturer": mfr}


# Verified on lcsc.com / jlcpcb.com on 2026-10-15 (see docs/design_review.md, BOM section)
P = {
    "5k1":  (R0603, lcsc("C23186", "0603WAF5101T5E", "UNI-ROYAL")),
    "10k":  (R0603, lcsc("C25804", "0603WAF1002T5E", "UNI-ROYAL")),
    "2k2":  (R0603, lcsc("C4190", "0603WAF2201T5E", "UNI-ROYAL")),
    "47k":  (R0603, lcsc("C25819", "0603WAF4702T5E", "UNI-ROYAL")),
    "1k":   (R0603, lcsc("C21190", "0603WAF1001T5E", "UNI-ROYAL")),
    "100k": (R0603, lcsc("C25803", "0603WAF1003T5E", "UNI-ROYAL")),
    "100R": (R0603, lcsc("C22775", "0603WAF1000T5E", "UNI-ROYAL")),
    "0R33": (R1206, lcsc("C25337", "1206W4F330LT5E", "UNI-ROYAL")),
    "33R":  (R2512, lcsc("C53728", "25121WF330JT4E", "UNI-ROYAL")),
    "10u":  (C0805, lcsc("C15850", "CL21A106KAYNNNE", "Samsung")),
    "100n": (C0603, lcsc("C14663", "CC0603KRX7R9BB104", "YAGEO")),
    "1u":   (C0603, lcsc("C15849", "CL10A105KB8NNNC", "Samsung")),
    "SS14": (SMA, lcsc("C2480", "SS14", "MDD")),
}


def R(s, ref, val, x, y, a, b, rot=0, **kw):
    fp, f = P[val]
    s.place("Device:R_Small", ref, kw.pop("label", val), x, y, {"1": a, "2": b}, rot=rot,
            footprint=fp, fields=f, **kw)


def C(s, ref, val, x, y, a, b, rot=0, **kw):
    fp, f = P[val]
    s.place("Device:C_Small", ref, kw.pop("label", val), x, y, {"1": a, "2": b}, rot=rot,
            footprint=fp, fields=f, **kw)


def build(force=False):
    target = os.path.join(OUT, PROJ + ".kicad_sch")
    if os.path.exists(target) and "(version 20230121)" not in open(target).read(200) and not force:
        sys.exit("fgl_g1.kicad_sch has been saved by a newer KiCad and is now the source of truth.\n"
                 "Regenerating would overwrite those edits. Use --force only to start over.")
    os.makedirs(OUT, exist_ok=True)
    symlib.write(os.path.join(OUT, "fgl.kicad_sym"), which=("xiao", "conn_radar", "conn_pot"))
    lib = kgen.Library(extra={"fgl": os.path.join(OUT, "fgl.kicad_sym")})
    s = kgen.Schematic(PROJ, "Fused Glass Lighting controller", "G1", "2026-10-15", "Rob Lim",
                       comments=("2 x 30 cm 3 V filaments at 303 mA, AL8860 buck, 5 V USB-C input (no PD)",
                                 "XIAO ESP32C3, HLK-LD2410S radar, brightness pot, power-bank keep-alive",
                                 "Design review: docs/design_review.md"), lib=lib)

    # ------------------------------------------------------------ 1 USB-C input
    s.box(12.7, 22.86, 147.32, 109.22, "1  USB-C INPUT: 5 V SINK, NO PD")
    s.place("Connector:USB_C_Receptacle_USB2.0_16P", "J1", "USB-C (from bank)", 38.1, 60.96,
            {"VBUS": "VBUS_IN", "CC1": "CC1", "CC2": "CC2", "A6": "NC", "B6": "NC", "A7": "NC",
             "B7": "NC", "SBU1": "NC", "SBU2": "NC", "GND": "GND", "SHIELD": "GND"},
            footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
            fields=lcsc("C165948", "TYPE-C-31-M-12", "Korean Hroparts Elec"),
            ref_at=(30.48, 33.02), val_at=(30.48, 35.56))
    R(s, "R1", "5k1", 73.66, 69.85, "CC1", "GND", label="5.1k 1%")
    R(s, "R2", "5k1", 88.9, 69.85, "CC2", "GND", label="5.1k 1%")
    s.place("Device:Polyfuse_Small", "F1", "0.75A hold", 101.6, 45.72, {"1": "VBUS_IN", "2": "+5V"},
            rot=90, footprint="Fuse:Fuse_1206_3216Metric",
            fields=lcsc("C99563", "1206L075THYR", "Littelfuse"), ref_at=(99.06, 40.64), val_at=(99.06, 50.8))
    s.place("Device:D_Zener_Small", "D1", "SMF6.0A", 124.46, 58.42, {"K": "+5V", "A": "GND"}, rot=270,
            footprint="Diode_SMD:D_SOD-123F", dnp=True,
            fields=lcsc("C178260", "SMF6.0A", "Jingdao"), ref_at=(127, 57.15), val_at=(127, 60.96))
    C(s, "C1", "10u", 137.16, 58.42, "+5V", "GND", label="10u 25V")
    s.pwr_flag("VBUS_IN", 91.44, 30.48)
    s.pwr_flag("+5V", 114.3, 30.48)
    s.pwr_flag("GND", 50.8, 93.98)
    s.text("Rd = 5.1 k on CC1 and CC2 (separate resistors): the bank supplies 5 V.\n"
           "No PD negotiation, so no part here can ever see more than 5.5 V from a\n"
           "compliant source. Works with USB-C banks and with USB-A to C cables.\n"
           "F1: 0.75 A hold / 1.5 A trip. Normal max 0.42 A lit; keep-alive pulses\n"
           "only run when the lamp draws < 120 mA. D1 DNP: fit only if a hot-plug\n"
           "test shows > 6.5 V on +5V (its leakage would cost idle current).",
           58.42, 81.28, 1.1)

    # ------------------------------------------------------------ 2/3 LED channels
    def channel(n, y0, U, Rs, L, D, J, Cb, Cd):
        s.box(157.48, y0, 302.26, y0 + 80.01, "%d  FILAMENT %d: AL8860 BUCK, 0.1 V / 0.33 R = 303 mA" % (n + 1, n))
        A, K, SW = "LED%d_A" % n, "LED%d_K" % n, "SW%d" % n
        s.place("Driver_LED:AL8860WT", U, "AL8860WT-7", 200.66, y0 + 41.91,
                {"VIN": "+5V", "GND": "GND", "CTRL": "DIM_CTRL", "SET": A, "SW": SW},
                footprint="Package_TO_SOT_SMD:TSOT-23-5",
                fields=lcsc("C125330", "AL8860WT-7", "Diodes Inc"),
                ref_at=(203.2, y0 + 30.48), val_at=(203.2, y0 + 53.34))
        C(s, Cb, "10u", 172.72, y0 + 25.4, "+5V", "GND", label="10u 25V")
        C(s, Cd, "100n", 187.96, y0 + 25.4, "+5V", "GND")
        R(s, Rs, "0R33", 236.22, y0 + 25.4, "+5V", A, label="0.33R 1%")
        s.place("Connector_Generic:Conn_01x02", J, "FILAMENT %d" % n, 284.48, y0 + 39.37,
                {"1": A, "2": K}, footprint="Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",
                fields=lcsc("C173752", "S2B-PH-K-S(LF)(SN)", "JST"),
                ref_at=(287.02, y0 + 38.1), val_at=(287.02, y0 + 43.18))
        s.place("Device:L", L, "47uH", 254.0, y0 + 59.69, {"1": K, "2": SW}, rot=90,
                footprint="Inductor_SMD:L_Sunlord_SWPA6045S",
                fields=lcsc("C36414", "SWPA6045S470MT", "Sunlord"),
                ref_at=(251.46, y0 + 55.88), val_at=(251.46, y0 + 64.77))
        s.place("Device:D_Schottky_Small", D, "SS14", 236.22, y0 + 69.85, {"K": "+5V", "A": SW},
                rot=270, footprint=SMA, fields=P["SS14"][1],
                ref_at=(238.76, y0 + 68.58), val_at=(238.76, y0 + 71.12))
        s.text("Loop: +5V -> %s -> filament -> %s -> SW; %s returns to +5V.\n"
               "Filament + is NOT ground-referenced. Never tie a lead to GND or the frame.\n"
               "Layout: tight VIN cap / Rs / L / D loop; Kelvin-route Rs to VIN and SET."
               % (Rs, L, D), 160.02, y0 + 66.04, 1.0)

    channel(1, 22.86, "U2", "R3", "L1", "D2", "J4", "C2", "C4")
    channel(2, 105.41, "U3", "R4", "L2", "D3", "J5", "C3", "C5")

    # ------------------------------------------------------------ 4 MCU
    s.box(12.7, 115.57, 147.32, 196.85, "4  MCU: SEEED XIAO ESP32C3 (hand-soldered)")
    s.place("fgl:XIAO_ESP32C3", "U1", "XIAO ESP32C3", 63.5, 160.02,
            {"1": "NC", "2": "ADC_POT", "3": "DIM_PWM", "4": "RADAR_OT2", "5": "UART_TX",
             "6": "UART_RX", "7": "NC", "8": "NC", "9": "NC", "10": "NC", "11": "KA_DRV",
             "12": "+3V3", "13": "GND", "14": "XIAO_5V"},
            footprint="fgl:XIAO_ESP32C3_Castellated",
            fields={"MPN": "113991054", "Manufacturer": "Seeed Studio", "LCSC": "",
                    "Note": "Hand-solder; not placed by JLCPCB"},
            ref_at=(68.58, 142.24), val_at=(68.58, 175.26))
    s.place("Device:D_Schottky_Small", "D4", "SS14", 48.26, 132.08, {"K": "XIAO_5V", "A": "+5V"},
            rot=180, footprint=SMA, fields=P["SS14"][1], ref_at=(46.99, 127.0), val_at=(46.99, 136.65))
    s.pwr_flag("XIAO_5V", 33.02, 124.46)
    s.text("D4 lets the board feed the XIAO's 5V pin (Seeed requires a diode)\n"
           "and blocks back-feed when the XIAO's own USB-C is plugged in.\n"
           "Strapping pins D0/D8/D9 and UART0 D6/D7 are left unconnected.\n"
           "Footprint has only the 14 edge pads: the underside pads\n"
           "(VBAT, EN, JTAG) are omitted so nothing can short to them.",
           88.9, 180.34, 1.0)
    C(s, "C8", "10u", 116.84, 130.81, "+3V3", "GND", label="10u 25V")
    C(s, "C9", "100n", 132.08, 130.81, "+3V3", "GND")

    # ------------------------------------------------------------ 5 pot + radar
    s.box(12.7, 203.2, 147.32, 284.48, "5  BRIGHTNESS POT AND RADAR")
    R(s, "R5", "47k", 30.48, 220.98, "+3V3", "POT_HI", label="47k 1%")
    s.place("fgl:Conn_Pot", "J2", "POT 100k lin", 30.48, 246.38,
            {"1": "POT_HI", "2": "POT_W", "3": "GND"},
            footprint="Connector_JST:JST_PH_S3B-PH-K_1x03_P2.00mm_Horizontal",
            fields=lcsc("C157929", "S3B-PH-K-S(LF)(SN)", "JST"),
            ref_at=(36.83, 241.3), val_at=(36.83, 255.27))
    R(s, "R6", "1k", 55.88, 246.38, "POT_W", "ADC_POT", rot=90, ref_at=(53.34, 241.3), val_at=(53.34, 251.46))
    C(s, "C6", "100n", 71.12, 256.54, "ADC_POT", "GND")
    s.place("fgl:Conn_LD2410S", "J3", "LD2410S", 132.08, 243.84,
            {"1": "+3V3", "2": "GND", "3": "UART_RX", "4": "UART_TX", "5": "RADAR_OT2"},
            footprint="Connector_JST:JST_PH_S5B-PH-K_1x05_P2.00mm_Horizontal",
            fields=lcsc("C157923", "S5B-PH-K-S(LF)(SN)", "JST"),
            ref_at=(142.24, 241.3), val_at=(142.24, 246.38))
    R(s, "R7", "100k", 99.06, 261.62, "RADAR_OT2", "GND")
    s.text("Pot: 100 k linear across 47 k + pot -> wiper 0-2.24 V\n"
           "(inside the C3's linear ADC range). 22 uA standing.\n"
           "R6 + C6: ESD and sampling filter if a panel knob is used.\n"
           "J3 is 1:1 with the LD2410S header: 1 3V3, 2 GND,\n"
           "3 OT1/TX, 4 RX, 5 OT2. R7 holds the wake pin low\n"
           "if the radar is unplugged.", 15.24, 264.16, 1.0)

    # ------------------------------------------------------------ 6 dimming
    s.box(157.48, 190.5, 233.68, 284.48, "6  DIMMING (both CTRL pins)")
    R(s, "R8", "2k2", 177.8, 210.82, "DIM_PWM", "DIM_CTRL", rot=90, label="2.2k 1%",
      ref_at=(175.26, 205.74), val_at=(175.26, 215.9))
    R(s, "R9", "10k", 195.58, 223.52, "DIM_CTRL", "GND", label="10k 1%")
    C(s, "C7", "1u", 210.82, 223.52, "DIM_CTRL", "GND")
    s.text("Analog (default): 19.5 kHz PWM -> RC -> DC on CTRL.\n"
           "V_CTRL = 2.70 V x duty. AL8860: 0.3-2.5 V = 0-100 %,\n"
           "< 0.2 V off, > 2.5 V clamps at 100 %.\n"
           "Flicker-free; ripple ~19 mV p-p; tau 1.8 ms.\n"
           "PWM fallback: leave C7 off, PWM <= 500 Hz.\n"
           "R9 holds CTRL at 0 V while D2 floats (reset,\n"
           "flashing, panic, light sleep) -> filaments dark.", 160.02, 238.76, 1.0)

    # ------------------------------------------------------------ 7 keep-alive
    s.box(236.22, 190.5, 297.18, 284.48, "7  BANK KEEP-ALIVE")
    R(s, "R12", "33R", 284.48, 215.9, "+5V", "=KA_D", label="33R 1W 2512")
    s.place("Transistor_FET:AO3400A", "Q1", "AO3400A", 281.94, 228.6, {"G": "KA_G", "S": "GND", "D": "KA_D"},
            footprint="Package_TO_SOT_SMD:SOT-23", fields=lcsc("C20917", "AO3400A", "AOS"),
            ref_at=(285.75, 226.06), val_at=(285.75, 231.14))
    R(s, "R10", "100R", 256.54, 228.6, "KA_DRV", "KA_G", rot=90, ref_at=(254.0, 223.52), val_at=(254.0, 233.68))
    R(s, "R11", "100k", 266.7, 238.76, "KA_G", "GND")
    s.text("152 mA for 200 ms every 10 s (3 mA avg)\n"
           "whenever the load is below ~120 mA:\n"
           "dark, or dimmed below ~25 %.\n"
           "Q1/R10/R11/R12 may be DNP for a bank\n"
           "proven to stay on without it.", 238.76, 254.0, 1.0)

    # ------------------------------------------------------------ notes, TPs, holes
    s.box(307.34, 22.86, 406.4, 116.84, "NOTES")
    s.text(
        "Power: one 5 V rail from the bank. Lit 2.06 W (411 mA),\n"
        "idle ~1.1 mA + 3 mA keep-alive (model: power_model.py).\n\n"
        "Pins (XIAO):\n"
        "  D1 GPIO3  ADC_POT    ADC1_CH3\n"
        "  D2 GPIO4  DIM_PWM    LEDC 19.5 kHz, 11-bit\n"
        "  D3 GPIO5  RADAR_OT2  light-sleep wake, high = present\n"
        "  D4 GPIO6  UART_TX -> radar RX (115200 8N1)\n"
        "  D5 GPIO7  UART_RX <- radar OT1/TX\n"
        "  D10 GPIO10 KA_DRV    keep-alive gate\n\n"
        "Connectors (JST-PH 2.0, through-hole, hand-soldered):\n"
        "  J2 pot, J3 radar, J4/J5 filaments (pin 1 = +, anode)\n\n"
        "Test on the first board (design_review.md, section 6):\n"
        "  TP3 < 0.2 V with the XIAO held in reset\n"
        "  each filament 303 mA +/- 5 % at full brightness\n"
        "  AL8860, L, R12 < 60 C after 45 min in the frame\n\n"
        "DNP: D1. JLCPCB places everything except U1 and J2-J5.",
        309.88, 29.21, 1.1)
    for i, (net, x) in enumerate([("+5V", 320.04), ("GND", 335.28), ("DIM_CTRL", 350.52),
                                  ("+3V3", 365.76), ("RADAR_OT2", 381.0)]):
        s.place("Connector:TestPoint", "TP%d" % (i + 1), net, x, 142.24, {"1": net},
                footprint="TestPoint:TestPoint_Pad_D1.5mm", ref_at=(x + 1.27, 137.16),
                val_at=(x + 1.27, 139.7), hide_value=True)
    s.text("Test points: TP1 +5V  TP2 GND  TP3 DIM_CTRL  TP4 +3V3  TP5 RADAR_OT2", 309.88, 127.0, 1.0)
    for i in range(4):
        s.place("Mechanical:MountingHole", "H%d" % (i + 1), "M3", 320.04 + 15.24 * i, 175.26, {},
                footprint="MountingHole:MountingHole_3.2mm_M3", hide_value=True,
                ref_at=(318.77 + 15.24 * i, 170.18))
    s.text("H1-H4: M3, place to suit the frame", 309.88, 182.88, 1.0)

    s.write(os.path.join(OUT, PROJ + ".kicad_sch"))
    kgen.write_project(OUT, PROJ, sym_libs=[("fgl", "fgl.kicad_sym", "Project symbols")],
                       fp_libs=[("fgl", "fgl.pretty", "Project footprints")])
    return s


if __name__ == "__main__":
    s = build(force="--force" in sys.argv)
    print("wrote", PROJ, len(s.parts), "parts")
