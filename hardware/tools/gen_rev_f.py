#!/usr/bin/env python3
"""Generate the Rev F prototype schematic, as built (documentation only).

Rev F is hand-wired on one full-size ElectroCookie board from modules, so the
parts have no footprints. Built from Rob's description of 2026-10-14 plus the
Oct 6 wiring table (docs/archive/hardware_rev_f.md). Items he did not confirm
are marked on the sheet. Checked by verify_netlist.py against rev_f_expected.py.
"""
import os

import kgen
import symlib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "kicad", "fgl_rev_f")
PROJ = "fgl_rev_f"


def build():
    os.makedirs(OUT, exist_ok=True)
    symlib.write(os.path.join(OUT, "fgl.kicad_sym"),
                 which=("xiao", "ld1500sb", "pd_trigger", "ld2410s"))
    lib = kgen.Library(extra={"fgl": os.path.join(OUT, "fgl.kicad_sym")})
    s = kgen.Schematic(PROJ, "Fused Glass Lighting prototype (as built)", "F", "2026-10-15", "Rob Lim",
                       comments=("Hand-wired on one full-size ElectroCookie board. Documentation of the build, not a PCB.",
                                 "2 x LD1500SB (CN5711 linear) modules, current set by on-board trimmer, 4.7 R 2 W ballast",
                                 "Superseded for production by Rev G1 (fgl_g1)"), lib=lib)

    def R(ref, val, x, y, a, b, rot=0, **kw):
        s.place("Device:R_Small", ref, val, x, y, {"1": a, "2": b}, rot=rot, **kw)

    def C(ref, val, x, y, a, b, sym="Device:C_Small", **kw):
        s.place(sym, ref, val, x, y, {"1": a, "2": b}, **kw)

    # ------------------------------------------------------------ power entry
    s.box(12.7, 22.86, 132.08, 96.52, "1  POWER ENTRY")
    s.place("fgl:PD_Trigger_Module", "M1", "AITRIP PD trigger", 35.56, 50.8, {"OUT+": "+5V", "OUT-": "GND"},
            ref_at=(44.45, 45.72), val_at=(44.45, 48.26))
    s.pwr_flag("GND", 50.8, 60.96)
    s.place("Device:D_Schottky", "D1", "1N5819", 91.44, 50.8, {"K": "XIAO_5V", "A": "+5V"}, rot=180,
            ref_at=(88.9, 45.72), val_at=(88.9, 55.88))
    s.pwr_flag("XIAO_5V", 109.22, 35.56)
    s.text("Bank USB-C -> PD trigger, set to 5 V and button-locked.\n"
           "Verified to keep the B0DQPD24ZD bank awake on its own.\n"
           "No fuse anywhere (see design review P1).\n"
           "1N5819 feeds the XIAO's 5V pin and blocks back-feed\n"
           "when the XIAO's own USB-C is plugged in for flashing.",
           15.24, 78.74, 1.1)

    # ------------------------------------------------------------ MCU
    s.box(12.7, 104.14, 132.08, 190.5, "2  MCU: XIAO ESP32C3")
    s.place("fgl:XIAO_ESP32C3", "U1", "XIAO ESP32C3", 68.58, 147.32,
            {"1": "NC", "2": "ADC_POT", "3": "CE_PWM", "4": "RADAR_OT2", "5": "UART_TX",
             "6": "UART_RX", "7": "NC", "8": "NC", "9": "NC", "10": "NC", "11": "KA_DRV",
             "12": "+3V3", "13": "GND", "14": "XIAO_5V"}, ref_at=(73.66, 129.54), val_at=(73.66, 162.56))
    s.text("Firmware: src/main.c (a631148). D2 = 1 kHz PWM, 13-bit, XTAL clock.\n"
           "ADC_RAW_AT_MAX = 2950 measured on this unit.", 15.24, 177.8, 1.1)

    # ------------------------------------------------------------ drivers
    def channel(n, y0, M, Rb, LED, Cin):
        s.box(142.24, y0, 297.18, y0 + 63.5, "%d  FILAMENT %d: LD1500SB (CN5711 LINEAR SINK)" % (n + 2, n))
        s.place("fgl:LD1500SB_Module", M, "LD1500SB", 185.42, y0 + 30.48,
                {"IN+": "+5V", "IN-": "GND", "EN": "CE_PWM", "L+": "L%d_P" % n, "L-": "L%d_N" % n},
                ref_at=(194.31, y0 + 21.59), val_at=(194.31, y0 + 40.64))
        s.place("Device:R", Rb, "4.7R 2W", 220.98, y0 + 27.94, {"1": "L%d_P" % n, "2": "FIL%d_A" % n}, rot=90,
                ref_at=(218.44, y0 + 22.86), val_at=(218.44, y0 + 33.02))
        s.place("Device:LED", LED, "Filament %d (30 cm)" % n, 248.92, y0 + 27.94,
                {"A": "FIL%d_A" % n, "K": "L%d_N" % n}, rot=180, ref_at=(246.38, y0 + 21.59),
                val_at=(246.38, y0 + 34.29))
        C(Cin, "10u", 160.02, y0 + 49.53, "+5V", "GND", sym="Device:C_Polarized_Small")
        s.text("Trimmer on the module (1 k + 47 k) set to ~300 mA, measured, not recorded.\n"
               "L+ is IN+ inside the module: the filament's + lead is the 5 V rail.\n"
               "Ballast position (above or below the filament) not confirmed; either works.",
               185.42, y0 + 50.8, 1.0)

    channel(1, 22.86, "M2", "R1", "LED1", "C1")
    channel(2, 93.98, "M3", "R2", "LED2", "C2")
    R("R3", "10k (confirm)", 152.4, 175.26, "CE_PWM", "GND")
    s.text("R3: CE pull-down from the Oct 6 wiring table. Not in the\n"
           "Oct 14 description - confirm it is fitted (review P2).", 158.75, 167.64, 1.0)

    # ------------------------------------------------------------ pot + radar
    s.box(12.7, 198.12, 142.24, 281.94, "5  BRIGHTNESS TRIMMER AND RADAR")
    R("R4", "4.7k", 30.48, 215.9, "+3V3", "=POT_HI")
    s.place("Device:R_Potentiometer_Trim", "RV1", "10k trimmer", 30.48, 227.33,
            {"1": "POT_HI", "2": "ADC_POT", "3": "GND"}, ref_at=(35.56, 222.25), val_at=(35.56, 233.68))
    C("C5", "100n", 50.8, 246.38, "ADC_POT", "GND")
    s.place("fgl:HLK-LD2410S", "M4", "HLK-LD2410S", 116.84, 236.22,
            {"3V3": "+3V3", "GND": "GND", "OT1/TX": "UART_RX", "RX": "UART_TX", "OT2": "RADAR_OT2"},
            ref_at=(119.38, 226.06), val_at=(119.38, 246.38))
    C("C3", "10u", 76.2, 220.98, "+3V3", "GND", sym="Device:C_Polarized_Small")
    C("C4", "100n", 86.36, 220.98, "+3V3", "GND")
    s.text("Wiper tops out at 2.25 V (4.7 k above the 10 k trimmer).", 15.24, 266.7, 1.0)

    # ------------------------------------------------------------ keep-alive
    s.box(152.4, 198.12, 297.18, 281.94, "6  BANK KEEP-ALIVE")
    R("R7", "33R 2W", 213.36, 215.9, "+5V", "=KA_D")
    s.place("Transistor_FET:2N7000", "Q1", "2N7000", 210.82, 228.6, {"G": "KA_G", "S": "GND", "D": "KA_D"},
            ref_at=(215.9, 226.06), val_at=(215.9, 231.14))
    R("R5", "100R", 185.42, 228.6, "KA_DRV", "KA_G", rot=90, ref_at=(182.88, 223.52), val_at=(182.88, 233.68))
    R("R6", "100k", 195.58, 241.3, "KA_G", "GND")
    s.text("152 mA nominal (~115 mA at a 3.3 V gate), 200 ms every 10 s\n"
           "while the lamp is dark. 2N7000 flat face: S G D.", 154.94, 262.89, 1.0)

    s.write(os.path.join(OUT, PROJ + ".kicad_sch"))
    kgen.write_project(OUT, PROJ, sym_libs=[("fgl", "fgl.kicad_sym", "Project symbols")])
    return s


if __name__ == "__main__":
    s = build()
    print("wrote", PROJ, len(s.parts), "parts")
