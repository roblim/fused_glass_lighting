#!/usr/bin/env python3
"""Generate the Rev G2 controller schematic (KiCad 7 format; KiCad 9 opens and upgrades it).

G2 replaces G1's two AL8860 buck channels with one TPS61500 SEPIC (TI SLVA904) driving a
series string of filaments through four push-in ports. Decisions and reasoning:
docs/g2_decisions.md. Values: tools/sepic_design.py.

Like gen_g1.py, this script is the first draft. Once the schematic has been saved in
KiCad 9 it becomes the source of truth and this script refuses to overwrite it unless run
with --force. verify_netlist.py checks the result against g2_expected.py, written by hand.
"""
import os
import sys

import kgen
import symlib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "kicad", "fgl_g2")
PROJ = "fgl_g2"

R0603 = "Resistor_SMD:R_0603_1608Metric"
R1206 = "Resistor_SMD:R_1206_3216Metric"
R2512 = "Resistor_SMD:R_2512_6332Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
SMA = "Diode_SMD:D_SMA"


def lcsc(code, mpn, mfr):
    return {"LCSC": code, "MPN": mpn, "Manufacturer": mfr}


# Stock and price checked on lcsc.com / jlcpcb.com 2026-10-23 (docs/g2_decisions.md, BOM section)
P = {
    "5k1":  (R0603, lcsc("C23186", "0603WAF5101T5E", "UNI-ROYAL")),
    "10k":  (R0603, lcsc("C25804", "0603WAF1002T5E", "UNI-ROYAL")),
    "47k":  (R0603, lcsc("C25819", "0603WAF4702T5E", "UNI-ROYAL")),
    "1k":   (R0603, lcsc("C21190", "0603WAF1001T5E", "UNI-ROYAL")),
    "82k":  (R0603, lcsc("C23254", "0603WAF8202T5E", "UNI-ROYAL")),
    "100k": (R0603, lcsc("C25803", "0603WAF1003T5E", "UNI-ROYAL")),
    "120k": (R0603, lcsc("C25808", "0603WAF1203T5E", "UNI-ROYAL")),
    "100R": (R0603, lcsc("C22775", "0603WAF1000T5E", "UNI-ROYAL")),
    "0R82": (R1206, lcsc("C30568", "1206W4F820LT5E", "UNI-ROYAL")),
    "33R":  (R2512, lcsc("C53728", "25121WF330JT4E", "UNI-ROYAL")),
    "10u":  (C0805, lcsc("C15850", "CL21A106KAYNNNE", "Samsung")),
    "10u50": (C1206, lcsc("C13585", "CL31A106KBHNNNE", "Samsung")),
    "100n": (C0603, lcsc("C14663", "CC0603KRX7R9BB104", "YAGEO")),
    "1u":   (C0603, lcsc("C15849", "CL10A105KB8NNNC", "Samsung")),
    "SS14": (SMA, lcsc("C2480", "SS14", "MDD")),
    "SS36": (SMA, lcsc("C2903825", "SS36", "LGE")),
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
        sys.exit("fgl_g2.kicad_sch has been saved by a newer KiCad and is now the source of truth.\n"
                 "Regenerating would overwrite those edits. Use --force only to start over.")
    os.makedirs(OUT, exist_ok=True)
    symlib.write(os.path.join(OUT, "fgl.kicad_sym"),
                 which=("xiao", "conn_radar", "conn_potsw", "tps61500", "conn_port"))
    lib = kgen.Library(extra={"fgl": os.path.join(OUT, "fgl.kicad_sym")})
    s = kgen.Schematic(PROJ, "Fused Glass Lighting controller", "G2", "2026-10-23", "Rob Lim",
                       comments=("Series filament string, TPS61500 SEPIC (TI SLVA904), 244/488 mA, 5 V USB-C input (no PD)",
                                 "XIAO ESP32C3 (socketed), LD2410S radar (socket or pigtail), pot + power switch, keep-alive",
                                 "Decisions: docs/g2_decisions.md. Values: hardware/tools/sepic_design.py"), lib=lib)

    # ------------------------------------------------------------ 1 USB-C input + power switch
    s.box(12.7, 22.86, 147.32, 109.22, "1  USB-C INPUT, FUSE AND POWER SWITCH (5 V SINK, NO PD)")
    s.place("Connector:USB_C_Receptacle_USB2.0_16P", "J1", "USB-C (from bank)", 33.02, 60.96,
            {"VBUS": "VBUS_IN", "CC1": "CC1", "CC2": "CC2", "A6": "NC", "B6": "NC", "A7": "NC",
             "B7": "NC", "SBU1": "NC", "SBU2": "NC", "GND": "GND", "SHIELD": "GND"},
            footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
            fields=lcsc("C165948", "TYPE-C-31-M-12", "Korean Hroparts Elec"),
            ref_at=(25.4, 33.02), val_at=(25.4, 35.56))
    R(s, "R1", "5k1", 63.5, 69.85, "CC1", "SW_N", label="5.1k 1%")
    R(s, "R2", "5k1", 76.2, 69.85, "CC2", "SW_N", label="5.1k 1%")
    s.place("Device:Polyfuse_Small", "F1", "2A hold", 71.12, 40.64, {"1": "VBUS_IN", "2": "VBUS_F"},
            rot=90, footprint="Fuse:Fuse_1812_4532Metric",
            fields=lcsc("C269145", "SMD1812B200TF/16", "Brightking"), ref_at=(68.58, 35.56), val_at=(68.58, 45.72))
    s.place("Device:D_Zener_Small", "D1", "SMF6.0A", 88.9, 54.61, {"K": "VBUS_F", "A": "GND"}, rot=270,
            footprint="Diode_SMD:D_SOD-123F", dnp=True,
            fields=lcsc("C178260", "SMF6.0A", "Jingdao"), ref_at=(91.44, 53.34), val_at=(91.44, 57.15))
    s.place("Transistor_FET:AO3401A", "Q2", "AO3401A", 114.3, 43.18, {"G": "Q2_G", "S": "VBUS_F", "D": "+5V"},
            rot=90, footprint="Package_TO_SOT_SMD:SOT-23", fields=lcsc("C15127", "AO3401A", "AOS"),
            ref_at=(110.49, 35.56), val_at=(116.84, 35.56))
    R(s, "R13", "100k", 101.6, 60.96, "VBUS_F", "Q2_G", label="100k")
    R(s, "R14", "1k", 114.3, 74.93, "Q2_G", "SW_N", label="1k")
    C(s, "C1", "10u", 137.16, 60.96, "+5V", "GND", label="10u 25V")
    s.pwr_flag("VBUS_IN", 60.96, 27.94)
    s.pwr_flag("+5V", 132.08, 27.94)
    s.pwr_flag("GND", 45.72, 93.98)
    s.text("Power switch: the pot's switch (J2 pin 4) pulls SW_N to GND.\n"
           " ON:  Rd (R1/R2 5.1 k) reach GND, so a USB-C bank sees a sink attach and\n"
           "      turns VBUS on; Q2's gate goes low and Q2 connects VBUS_F to +5V.\n"
           " OFF: Rd float (bank sees nothing attached, sleeps) and R13 holds Q2 off,\n"
           "      which also cuts non-compliant banks and USB-A to C cables.\n"
           "The switch carries < 0.1 mA. R14 keeps cable ESD off Q2's gate.\n"
           "F1: 1.5 A hold / 3 A trip. Max normal draw 1.4 A (5 W LED cap).\n"
           "D1 DNP: fit only if a hot-plug test shows > 6.5 V on VBUS_F.",
           50.8, 82.55, 1.0)

    # ------------------------------------------------------------ 2 SEPIC
    s.box(157.48, 22.86, 302.26, 132.08, "2  LED DRIVER: TPS61500 SEPIC (TI SLVA904), REGULATES 0.2 V ON FB")
    s.place("fgl:TPS61500", "U2", "TPS61500PWPR", 205.74, 78.74,
            {"3": "+5V", "4": "DRV_EN", "6": "DIMC", "5": "SS", "8": "COMP", "10": "FREQ",
             "1": "SW", "2": "SW", "11": "OVP", "9": "LED_RTN",
             "7": "GND", "12": "GND", "13": "GND", "14": "GND", "15": "GND"},
            footprint="Package_SO:Texas_HTSSOP-14-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask3.155x3.255mm_ThermalVias",
            fields=lcsc("C71160", "TPS61500PWPR", "TI"), ref_at=(200.66, 63.5), val_at=(213.36, 100.33))
    C(s, "C2", "10u", 167.64, 40.64, "+5V", "GND", label="10u 25V")
    C(s, "C3", "100n", 180.34, 40.64, "+5V", "GND")
    s.place("Device:L", "L1", "10uH", 228.6, 40.64, {"1": "+5V", "2": "SW"}, rot=90,
            footprint="Inductor_SMD:L_Sunlord_SWPA8040S",
            fields=lcsc("C37429", "SWPA8040S100MT", "Sunlord"), ref_at=(226.06, 35.56), val_at=(226.06, 45.72))
    C(s, "C4", "10u50", 248.92, 53.34, "SW", "SEP_B", rot=90, label="10u 50V",
      ref_at=(246.38, 48.26), val_at=(246.38, 58.42))
    s.place("Device:L", "L2", "10uH", 264.16, 68.58, {"1": "SEP_B", "2": "GND"},
            footprint="Inductor_SMD:L_Sunlord_SWPA8040S",
            fields=lcsc("C37429", "SWPA8040S100MT", "Sunlord"), ref_at=(266.7, 66.04), val_at=(266.7, 71.12))
    s.place("Device:D_Schottky_Small", "D5", "SS36", 276.86, 45.72, {"A": "SEP_B", "K": "VOUT"},
            footprint=SMA, fields=P["SS36"][1], ref_at=(274.32, 40.64), val_at=(274.32, 50.8))
    C(s, "C5", "10u50", 292.1, 60.96, "VOUT", "GND", label="10u 50V")
    C(s, "C6", "100n", 292.1, 81.28, "VOUT", "GND")
    R(s, "R15", "120k", 251.46, 93.98, "VOUT", "OVP", label="120k 1%")
    R(s, "R16", "5k1", 251.46, 109.22, "OVP", "GND", label="5.1k 1%")
    R(s, "R17", "1k", 167.64, 63.5, "DIM_PWM", "DRV_EN", rot=90, ref_at=(165.1, 58.42), val_at=(165.1, 68.58))
    R(s, "R18", "100k", 175.26, 104.14, "DRV_EN", "GND")
    C(s, "C7", "1u", 182.88, 116.84, "DIMC", "GND")
    C(s, "C8", "100n", 195.58, 116.84, "SS", "GND")
    C(s, "C9", "100n", 208.28, 116.84, "COMP", "GND")
    R(s, "R19", "82k", 220.98, 116.84, "FREQ", "GND", label="82k 1%")

    # ------------------------------------------------------------ 3 filament ports
    s.box(157.48, 137.16, 302.26, 200.66, "3  FILAMENT PORTS: ONE SERIES STRING, PUSH-IN TERMINALS")
    ports = [("J5", "VOUT", "STR2", "LED_RTN"), ("J6", "STR2", "STR3", "LED_RTN"),
             ("J7", "STR3", "STR4", "LED_RTN"), ("J8", "STR4", "LED_RTN", "LED_RTN")]
    for i, (ref, a, b, c) in enumerate(ports):
        x = 185.42 + 30.48 * i
        s.place("fgl:Filament_Port", ref, "PORT %d" % (i + 1), x, 157.48, {"1": a, "2": b, "3": c},
                footprint="fgl:TerminalBlock_Degson_DG250-3.5-03P",
                fields=lcsc("C7588159", "DG250-3.5-03P-11-00A(H)", "DEGSON"),
                ref_at=(x - 2.54, 149.86), val_at=(x - 2.54, 165.1))
    s.text("Fill ports in order from PORT 1. Each filament: + wire -> its port's +, - wire -> NEXT,\n"
           "except the LAST filament, whose - wire goes to END. PORT 4's NEXT is also END.\n"
           "Mix 3 V and 12 V filaments freely; same current through all. Open string -> VOUT\n"
           "rises to OVP and firmware flags it (VSENSE). Silkscreen: + / NEXT / END on each port.",
           160.02, 172.72, 1.0)
    R(s, "R20", "0R82", 177.8, 190.5, "LED_RTN", "GND", label="0.82R 1%")
    R(s, "R21", "0R82", 195.58, 190.5, "LED_RTN", "RS2_B", label="0.82R 1%")
    s.place("Jumper:SolderJumper_3_Open", "JP1", "500mA", 220.98, 190.5,
            {"1": "RS2_B", "2": "GND", "3": "ISEL"},
            footprint="Jumper:SolderJumper-3_P1.3mm_Open_RoundedPad1.0x1.5mm",
            fields={"LCSC": "", "MPN": "solder jumper", "Manufacturer": "PCB"},
            ref_at=(218.44, 185.42), val_at=(226.06, 185.42))
    s.text("I_max = 0.2 V / Rs.\nJP1 open: R20 only, 244 mA.\nBridge ALL THREE pads of JP1:\n"
           "R21 in parallel (488 mA) and\nISEL to GND so the firmware knows.", 246.38, 184.15, 1.0)

    # ------------------------------------------------------------ 4 MCU
    s.box(12.7, 115.57, 147.32, 196.85, "4  MCU: SEEED XIAO ESP32C3 IN 5 mm SOCKETS (bought with pins)")
    # U1 is the module itself: in the schematic and BOM, not on the board. It plugs into J9/J10.
    xiao_pins = {1: "NC", 2: "ADC_POT", 3: "VSENSE", 4: "RADAR_OT2", 5: "UART_TX", 6: "UART_RX",
                 7: "ISEL_IO", 8: "DIM_PWM", 9: "NC", 10: "NC", 11: "KA_DRV", 12: "+3V3", 13: "GND",
                 14: "XIAO_5V"}
    s.place("fgl:XIAO_ESP32C3", "U1", "XIAO ESP32C3", 63.5, 160.02,
            {str(k): v for k, v in xiao_pins.items()}, footprint="", on_board=False,
            fields={"MPN": "102010633", "Manufacturer": "Seeed Studio",
                    "LCSC": "", "Note": "Plugs into J9/J10; not on the PCB"},
            ref_at=(68.58, 142.24), val_at=(68.58, 175.26))
    # The sockets carry the same nets. J9 pin k = XIAO pin k; J10 pin k = XIAO pin 7 + k.
    # Layout: Seeed XIAO-ESP32-C3-DIP geometry, rows 15.24 mm apart, pin 1 at the USB-C end.
    for ref, first, y in (("J9", 1, 147.32), ("J10", 8, 167.64)):
        nets = {str(k + 1): xiao_pins[first + k] for k in range(7)}
        nets = {k: ("NC" if v == "NC" else v) for k, v in nets.items()}
        s.place("Connector_Generic:Conn_01x07", ref, "XIAO socket %d-%d" % (first, first + 6), 127.0, y, nets,
                rot=0 if ref == "J9" else 90,
                footprint="Connector_PinSocket_2.54mm:PinSocket_1x07_P2.54mm_Vertical",
                fields=lcsc("C27985232", "HC-PM254-5.0H-1x7PZ", "Hong Cheng"),
                ref_at=(129.54, y - 10.16) if ref == "J9" else (106.68, y - 5.08),
                val_at=(129.54, y + 10.16) if ref == "J9" else (106.68, y - 2.54),
                stubs=None if ref == "J9" else {"5": 7.62, "7": 5.08})
    s.place("Device:D_Schottky_Small", "D4", "SS14", 48.26, 132.08, {"K": "XIAO_5V", "A": "+5V"},
            rot=180, footprint=SMA, fields=P["SS14"][1], ref_at=(46.99, 127.0), val_at=(46.99, 136.65))
    s.pwr_flag("XIAO_5V", 33.02, 124.46)
    R(s, "R22", "1k", 22.86, 182.88, "ISEL_IO", "ISEL", rot=90, ref_at=(20.32, 177.8), val_at=(20.32, 187.96))
    R(s, "R23", "100k", 38.1, 186.69, "+3V3", "ISEL")
    C(s, "C10", "10u", 99.06, 130.81, "+3V3", "GND", label="10u 25V")
    C(s, "C11", "100n", 111.76, 130.81, "+3V3", "GND")
    s.text("D4 feeds the XIAO's 5V pin and blocks back-feed from its own USB-C.\n"
           "D6 (GPIO21) is UART0 TX: it toggles during boot, so ISEL goes through R22.\n"
           "D7 (GPIO20, UART0 RX, input at boot) drives EN; R18 keeps it low until set.\n"
           "Strapping pins D0/D8/D9 unconnected. J9/J10: 5 mm low-profile sockets\n"
           "(JLCPCB fits them); the XIAO's USB-C faces the board edge.",
           50.8, 182.88, 1.0)

    # ------------------------------------------------------------ 5 pot + switch, radar
    s.box(12.7, 203.2, 147.32, 284.48, "5  POT + POWER SWITCH, RADAR (SOCKET OR PIGTAIL)")
    R(s, "R5", "47k", 25.4, 220.98, "+3V3", "POT_HI", label="47k 1%")
    s.place("fgl:Conn_PotSwitch", "J2", "POT 100k lin + SW", 33.02, 241.3,
            {"1": "GND", "2": "POT_W", "3": "POT_HI", "4": "SW_N"}, rot=90, stubs={"1": 7.62},
            footprint="Connector_JST:JST_PH_S4B-PH-K_1x04_P2.00mm_Horizontal",
            fields=lcsc("C157926", "S4B-PH-K-S(LF)(SN)", "JST"),
            ref_at=(40.64, 236.22), val_at=(40.64, 238.76))
    R(s, "R6", "1k", 55.88, 254.0, "POT_W", "ADC_POT", rot=90, ref_at=(53.34, 248.92), val_at=(53.34, 259.08))
    C(s, "C12", "100n", 68.58, 260.35, "ADC_POT", "GND")
    s.place("Device:FerriteBead_Small", "FB1", "600R@100MHz", 99.06, 220.98, {"1": "+3V3", "2": "RADAR_3V3"},
            rot=90, footprint="Inductor_SMD:L_0603_1608Metric",
            fields=lcsc("C1002", "GZ1608D601TF", "Sunlord"), ref_at=(96.52, 215.9), val_at=(96.52, 226.06))
    C(s, "C13", "10u", 114.3, 228.6, "RADAR_3V3", "GND", label="10u 25V")
    C(s, "C14", "100n", 127.0, 228.6, "RADAR_3V3", "GND")
    radar = {"1": "RADAR_3V3", "2": "GND", "3": "RADAR_TX", "4": "RADAR_RX", "5": "RADAR_OT2_C"}
    s.place("fgl:Conn_LD2410S", "J3", "LD2410S socket", 96.52, 251.46, radar,
            footprint="Connector_PinSocket_2.54mm:PinSocket_1x05_P2.54mm_Vertical",
            fields=lcsc("C27985230", "HC-PM254-5.0H-1x5PZ", "Hong Cheng"),
            ref_at=(104.14, 259.08), val_at=(104.14, 261.62))
    s.place("fgl:Conn_LD2410S", "J4", "LD2410S cable", 129.54, 251.46, radar,
            footprint="Connector_JST:JST_PH_S5B-PH-K_1x05_P2.00mm_Horizontal",
            fields=lcsc("C157923", "S5B-PH-K-S(LF)(SN)", "JST"),
            ref_at=(137.16, 259.08), val_at=(137.16, 261.62))
    R(s, "R7", "100k", 78.74, 269.24, "RADAR_OT2", "GND")
    s.text("J2: pot with built-in switch, off at the CCW stop. Numbered like the pot:\n"
           "1 CCW end + switch common (GND), 2 wiper, 3 CW end, 4 switch (SW_N). CW = brighter.\n"
           "Wiper 0-2.24 V (47 k + 100 k pot). R6/C12 ESD + sampling filter.\n"
           "J3 (radar plugs in directly) and J4 (radar on a cable) are in parallel,\n"
           "1:1 with the LD2410S header: 3V3, GND, OT1/TX, RX, OT2. Use one.\n"
           "FB1/C13/C14 keep switching noise off the radar supply.",
           15.24, 264.16, 1.0)

    # ------------------------------------------------------------ 6 string-voltage sense
    s.box(157.48, 205.74, 233.68, 284.48, "6  STRING VOLTAGE SENSE, RADAR LINE RESISTORS")
    R(s, "R26", "1k", 223.52, 223.52, "UART_TX", "RADAR_RX", rot=90, ref_at=(220.98, 218.44), val_at=(226.06, 218.44))
    R(s, "R27", "1k", 223.52, 233.68, "RADAR_TX", "UART_RX", rot=90, ref_at=(220.98, 228.6), val_at=(226.06, 228.6))
    R(s, "R28", "1k", 223.52, 243.84, "RADAR_OT2_C", "RADAR_OT2", rot=90, ref_at=(220.98, 238.76), val_at=(226.06, 238.76))
    R(s, "R24", "120k", 177.8, 223.52, "VOUT", "VSENSE", label="120k 1%")
    R(s, "R25", "10k", 177.8, 243.84, "VSENSE", "GND", label="10k 1%")
    C(s, "C15", "100n", 189.23, 243.84, "VSENSE", "GND")
    s.text("VSENSE = VOUT / 13: 30.2 V (OVP) -> 2.32 V, inside the C3's\n"
           "ADC range at 11 dB. Firmware uses it for:\n"
           " - P_LED = VOUT x I_set, capped at 5 W\n"
           " - open string (VOUT near OVP at low current)\n"
           " - shorted output (VOUT ~ 0 while lit)\n"
           " - what is connected (one 12 V ~ 11 V, 3 x 3 V ~ 8.4 V)\n"
           "0 uA when the driver is off (C4 blocks DC).\n"
           "R26-R28: 1 k series on the radar lines (ESD on the cable/socket).", 160.02, 256.54, 1.0)

    # ------------------------------------------------------------ 7 keep-alive
    s.box(236.22, 205.74, 297.18, 284.48, "7  BANK KEEP-ALIVE")
    R(s, "R12", "33R", 284.48, 223.52, "+5V", "=KA_D", label="33R 1W 2512")
    s.place("Transistor_FET:AO3400A", "Q1", "AO3400A", 281.94, 236.22, {"G": "KA_G", "S": "GND", "D": "KA_D"},
            footprint="Package_TO_SOT_SMD:SOT-23", fields=lcsc("C20917", "AO3400A", "AOS"),
            ref_at=(285.75, 233.68), val_at=(285.75, 238.76))
    R(s, "R10", "100R", 256.54, 236.22, "KA_DRV", "KA_G", rot=90, ref_at=(254.0, 231.14), val_at=(254.0, 241.3))
    R(s, "R11", "100k", 266.7, 246.38, "KA_G", "GND")
    s.text("152 mA for 200 ms every 10 s (3 mA avg)\n"
           "only while the board draws less than\n"
           "the bank's threshold. Firmware setting\n"
           "can turn it off; R12 DNP = hard off.", 238.76, 261.62, 1.0)

    # ------------------------------------------------------------ notes, TPs, holes
    s.box(307.34, 22.86, 406.4, 160.02, "NOTES")
    s.text(
        "Power: 5 V from the bank via Q2. LED power capped at 5 W in firmware\n"
        "(~1.4 A from the bank); 1.7 W lit at prototype brightness; idle ~4 mA\n"
        "with keep-alive, ~0.7 mA without (model: power_model.py).\n\n"
        "Pins (XIAO):\n"
        "  D1 GPIO3  ADC_POT    ADC1_CH3\n"
        "  D2 GPIO4  VSENSE     ADC1_CH4, VOUT / 13\n"
        "  D3 GPIO5  RADAR_OT2  wake, high = present\n"
        "  D4 GPIO6  UART_TX -> radar RX (115200 8N1)\n"
        "  D5 GPIO7  UART_RX <- radar OT1/TX\n"
        "  D6 GPIO21 ISEL_IO    low = 500 mA jumper (via R22)\n"
        "  D7 GPIO20 DIM_PWM    LEDC 19.5 kHz -> EN (analog dim)\n"
        "  D10 GPIO10 KA_DRV    keep-alive gate\n\n"
        "Assembly: JLCPCB fits everything incl. through-hole J2-J8 and the\n"
        "XIAO sockets; you plug in the XIAO and the radar. DNP: D1.\n\n"
        "Bring-up (docs/g2_decisions.md): SEPIC at the extremes (one 3 V\n"
        "filament at 244 mA; ~28 V string at the 5 W cap), filament\n"
        "temperature in the frame, bank wake via the switch.",
        309.88, 29.21, 1.1)
    s.text("SEPIC: +5V -> L1 -> SW (switch) ; C4 couples SW to SEP_B ; L2 SEP_B -> GND ;\n"
           "D5 SEP_B -> VOUT. Works for any string from one 3 V filament (~2.7 V) to ~28 V,\n"
           "and C4 blocks DC: no current path from the bank to the LEDs when U2 is off.\n"
           "f = 1.17 MHz (R19 82 k). OVP = 1.229 x (1 + 120k/5.1k) = 30.2 V; switch sees\n"
           "VIN + VOUT + VD < 36 V (40 V abs max). L1 = L2 = 10 uH, 4.1 A sat.\n"
           "Dimming: 19.5 kHz PWM on EN, filtered inside U2 by DIMC (C7) -> analog FB reference,\n"
           "I_LED = duty x I_max. EN low > 10 ms = shutdown (2 uA). R18 holds EN low at boot.\n"
           "COMP C9 100 nF. Lowest RHPZ 43 kHz (5 W into a 12 V string, 4.5 V in): keep crossover\n"
           "< 4.3 kHz. SLVA904 measured 1.7 kHz with 15 nF / 4.7 uH; 100 nF / 10 uH is lower still.\n"
           "Tune 15-470 nF on the bench. Checks: sepic_design.py (switch peak 2.2 A vs 3 A min).",
           309.88, 129.54, 1.0)
    for i, (net, x) in enumerate([("+5V", 320.04), ("GND", 332.74), ("LED_RTN", 345.44),
                                  ("+3V3", 358.14), ("RADAR_OT2", 370.84), ("VOUT", 383.54)]):
        s.place("Connector:TestPoint", "TP%d" % (i + 1), net, x, 182.88, {"1": net},
                footprint="TestPoint:TestPoint_Pad_D1.5mm", ref_at=(x + 1.27, 177.8),
                val_at=(x + 1.27, 180.34), hide_value=True)
    s.text("TP1 +5V  TP2 GND  TP3 LED_RTN (I = V / 0.82 R)  TP4 +3V3  TP5 RADAR_OT2  TP6 VOUT",
           309.88, 170.18, 1.0)
    for i in range(4):
        s.place("Mechanical:MountingHole", "H%d" % (i + 1), "M3", 320.04 + 15.24 * i, 213.36, {},
                footprint="MountingHole:MountingHole_3.2mm_M3", hide_value=True,
                ref_at=(318.77 + 15.24 * i, 208.28))
    s.text("H1-H4: M3, place to suit the frame", 309.88, 220.98, 1.0)

    s.write(os.path.join(OUT, PROJ + ".kicad_sch"))
    kgen.write_project(OUT, PROJ, sym_libs=[("fgl", "fgl.kicad_sym", "Project symbols")],
                       fp_libs=[("fgl", "fgl.pretty", "Project footprints")])
    return s


if __name__ == "__main__":
    s = build(force="--force" in sys.argv)
    print("wrote", PROJ, len(s.parts), "parts")
