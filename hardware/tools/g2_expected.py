"""Rev G2 design intent, written by hand from docs/g2_decisions.md.

Independent of gen_g2.py on purpose: verify_netlist.py compares this against the netlist
KiCad itself exports from the schematic. A change to the circuit must be made in both
places, which is the point.

Format: net name -> set of "REF.PIN". Pin numbers are footprint pad numbers.
"""

NETS = {
    # ---- USB-C input, fuse, power switch (J1 = HRO TYPE-C-31-M-12)
    "VBUS_IN": {"J1.A4", "J1.A9", "J1.B4", "J1.B9", "F1.1"},
    "VBUS_F": {"F1.2", "D1.1", "Q2.2", "R13.1", "C16.1"},  # D1 K (TVS, DNP); Q2 = AO3401A, 2 = S
    "Q2_G": {"Q2.1", "R13.2", "R14.1", "C16.2"},           # C16 + R14 (10 k): ~1 ms gate ramp, soft start
    "SW_N": {"R14.2", "R1.2", "R2.2", "J2.4"},           # pot switch pulls this to GND = ON
    "CC1": {"J1.A5", "R1.1"},
    "CC2": {"J1.B5", "R2.1"},
    "+5V": {"Q2.3", "C1.1", "U2.3", "C2.1", "C3.1", "L1.1", "D4.2", "R12.1", "TP1.1"},
    "GND": {"J1.A1", "J1.A12", "J1.B1", "J1.B12", "J1.S1", "D1.2", "C1.2",
            "C2.2", "C3.2", "L2.2", "C5.2", "C6.2", "R16.2", "R18.2", "C7.2", "C8.2", "C9.2", "R19.2",
            "U2.7", "U2.12", "U2.13", "U2.14", "U2.15",
            "R20.2", "JP1.2", "JP2.1",
            "J10.6", "C10.2", "C11.2",
            "J2.1", "C12.2", "C13.2", "C14.2", "J3.2", "J4.2", "R7.2",
            "R25.2", "C15.2", "Q1.2", "R11.2", "TP2.1"},
    # ---- SEPIC (TPS61500: 1,2 SW  3 VIN  4 EN  5 SS  6 DIMC  7 AGND  8 COMP  9 FB  10 FREQ  11 OVP  12-14 PGND  15 pad)
    "SW": {"U2.1", "U2.2", "L1.2", "C4.1"},
    "SEP_B": {"C4.2", "L2.1", "D5.2"},                   # D5 = SS36, 2 = A
    "VOUT": {"D5.1", "C5.1", "C6.1", "R15.1", "R24.1", "J5.1", "TP6.1"},
    "OVP": {"R15.2", "R16.1", "U2.11"},
    "DRV_EN": {"R17.2", "R18.1", "U2.4"},
    "DIMC": {"U2.6", "C7.1"},
    "SS": {"U2.5", "C8.1"},
    "COMP": {"U2.8", "C9.1"},
    "FREQ": {"U2.10", "R19.1"},
    # ---- filament string: J5..J8 pads 1 +, 2 NEXT, 3 END
    "STR2": {"J5.2", "J6.1"},
    "STR3": {"J6.2", "J7.1"},
    "STR4": {"J7.2", "J8.1"},
    "LED_RTN": {"J5.3", "J6.3", "J7.3", "J8.2", "J8.3", "U2.9", "R20.1", "R21.1", "TP3.1"},
    # JP1 = 1x3 2.54 mm header + shunt: 1-2 adds R21 (488 mA, ISEL stays high via R23);
    # 2-3 grounds ISEL (244 mA). One shunt can't make the unsafe combination.
    "RS2_B": {"R21.2", "JP1.1"},
    "ISEL": {"JP1.3", "R22.2", "R23.2"},
    # ---- MCU: sockets J9 (XIAO pins 1-7) / J10 (XIAO pins 8-14). U1, the module itself, is drawn
    #      with the same nets but marked "not on board", and KiCad leaves its pins out of the netlist.
    "ISEL_IO": {"J9.7", "R22.1"},
    "DIM_PWM": {"J10.1", "R17.1"},
    "ADC_POT": {"J9.2", "R6.2", "C12.1"},
    "VSENSE": {"J9.3", "R24.2", "R25.1", "C15.1"},
    "RADAR_OT2": {"J9.4", "R28.2", "R7.1", "TP5.1"},
    "UART_TX": {"J9.5", "R26.1"},              # XIAO D4 -> R26 -> radar RX
    "UART_RX": {"J9.6", "R27.2"},              # radar OT1/TX -> R27 -> XIAO D5
    "RADAR_RX": {"R26.2", "J3.4", "J4.4"},
    "RADAR_TX": {"R27.1", "J3.3", "J4.3"},
    "RADAR_OT2_C": {"R28.1", "J3.5", "J4.5"},
    "KA_DRV": {"J10.4", "R10.1"},
    # JP2 = 1x3 header + shunt: 1-2 grounds RADAR_MODE (manual: radar ignored); 2-3 parks the shunt.
    # The firmware enables GPIO8's internal pull-up, so no shunt = radar mode. D8 is a strapping pin, but only
    # matters in download mode (then it must be high: move the shunt off 1-2 before holding BOOT).
    "RADAR_MODE": {"J10.2", "JP2.2"},
    "+3V3": {"J10.5", "C10.1", "C11.1", "R23.1", "R5.1", "FB1.1", "TP4.1"},
    "XIAO_5V": {"D4.1", "J10.7"},
    # ---- pot + switch (J2, numbered like the pot: 1 CCW + switch common, 2 W, 3 CW, 4 SW), radar supply
    "POT_HI": {"R5.2", "J2.3"},
    "POT_W": {"J2.2", "R6.1"},
    "RADAR_3V3": {"FB1.2", "C13.1", "C14.1", "J3.1", "J4.1"},
    # ---- keep-alive: AO3400A 1 G, 2 S, 3 D
    "KA_G": {"R10.2", "R11.1", "Q1.1"},
    "KA_D": {"R12.2", "Q1.3"},
}

NO_CONNECT = {"J1.A6", "J1.B6", "J1.A7", "J1.B7", "J1.A8", "J1.B8",
              "J9.1", "J10.3", "JP2.3"}       # JP2.3: shunt parking position

DNP = {"D1"}

NOT_ON_BOARD = {"U1"}          # the XIAO module: plugs into J9/J10; KiCad leaves it out of the netlist
OFF_BOARD_NO_CONNECTS = 2      # U1's own flags on D0, D9 (also flagged on J9.1, J10.3)
BOM_EXTRA = [[1, "U1", "XIAO ESP32C3", "(plugs into J9/J10)", "113991054, order with pre-soldered headers",
              "Seeed Studio", "", "hand"],
             [2, "JP1-shunt, JP2-shunt", "2.54 mm shunt for JP1 / JP2", "(loose part)", "2.54 (open top)", "BOOMELE", "C5305", "loose"]]
NO_LCSC = set()                # JP1/JP2 are fitted pin headers (the shunts are loose parts)
HAND = {"U1"}                  # everything else is fitted by JLCPCB

FOOTPRINT_PADS = {
    "U2": "Package_SO:Texas_HTSSOP-14-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask3.155x3.255mm_ThermalVias",
    "Q1": "Package_TO_SOT_SMD:SOT-23", "Q2": "Package_TO_SOT_SMD:SOT-23",
    "J5": "fgl:TerminalBlock_Degson_DG250-3.5-03P",
}

# Footprints that exist in KiCad 9 but not in older libraries; pads as listed by KiCad 9.0.7
# (get_footprint_info, 2026-10-23). Used only when the library file isn't found locally.
EXTERNAL_PADS = {
    "Package_SO:Texas_HTSSOP-14-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask3.155x3.255mm_ThermalVias":
        {str(n) for n in range(1, 16)},
}
