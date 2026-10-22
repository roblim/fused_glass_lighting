"""Rev G1 design intent, written by hand from docs/design_review.md.

Independent of gen_g1.py on purpose: verify_netlist.py compares this against
the netlist KiCad itself exports from the schematic. A change to the circuit
must be made in both places, which is the point.

Format: net name -> set of "REF.PIN". Pin numbers are footprint pad numbers.
"""

NETS = {
    # USB-C input (J1 = HRO TYPE-C-31-M-12, pads per KiCad footprint)
    "VBUS_IN": {"J1.A4", "J1.A9", "J1.B4", "J1.B9", "F1.1"},
    "CC1": {"J1.A5", "R1.1"},
    "CC2": {"J1.B5", "R2.1"},
    "+5V": {"F1.2", "C1.1", "D1.1",                       # D1 K (TVS, DNP)
            "U2.5", "U3.5", "C2.1", "C3.1", "C4.1", "C5.1",  # AL8860 VIN + caps
            "R3.1", "R4.1",                               # sense resistors, VIN side
            "D2.1", "D3.1",                               # catch diode cathodes
            "D4.2",                                       # XIAO feed diode anode
            "R12.1", "TP1.1"},
    "GND": {"J1.A1", "J1.A12", "J1.B1", "J1.B12", "J1.S1", "R1.2", "R2.2", "D1.2", "C1.2",
            "U2.2", "U3.2", "C2.2", "C3.2", "C4.2", "C5.2",
            "U1.13", "C8.2", "C9.2", "J2.3", "C6.2", "J3.2", "R7.2",
            "R9.2", "C7.2", "Q1.2", "R11.2", "TP2.1"},
    # Channel 1: AL8860 pin 1 SW, 2 GND, 3 CTRL, 4 SET, 5 VIN
    "LED1_A": {"R3.2", "U2.4", "J4.1"},
    "LED1_K": {"J4.2", "L1.1"},
    "SW1": {"L1.2", "U2.1", "D2.2"},
    # Channel 2
    "LED2_A": {"R4.2", "U3.4", "J5.1"},
    "LED2_K": {"J5.2", "L2.1"},
    "SW2": {"L2.2", "U3.1", "D3.2"},
    # Dimming
    "DIM_PWM": {"U1.3", "R8.1"},
    "DIM_CTRL": {"R8.2", "R9.1", "C7.1", "U2.3", "U3.3", "TP3.1"},
    # MCU supply: XIAO pad 14 = 5V, 12 = 3V3, 13 = GND
    "XIAO_5V": {"D4.1", "U1.14"},
    "+3V3": {"U1.12", "C8.1", "C9.1", "R5.1", "J3.1", "TP4.1"},
    # Pot
    "POT_HI": {"R5.2", "J2.1"},
    "POT_W": {"J2.2", "R6.1"},
    "ADC_POT": {"R6.2", "C6.1", "U1.2"},
    # Radar: J3 1 3V3, 2 GND, 3 OT1/TX, 4 RX, 5 OT2
    "UART_RX": {"J3.3", "U1.6"},          # radar TX -> XIAO D5/GPIO7
    "UART_TX": {"J3.4", "U1.5"},          # XIAO D4/GPIO6 -> radar RX
    "RADAR_OT2": {"J3.5", "U1.4", "R7.1", "TP5.1"},
    # Keep-alive: AO3400A 1 G, 2 S, 3 D
    "KA_DRV": {"U1.11", "R10.1"},
    "KA_G": {"R10.2", "R11.1", "Q1.1"},
    "KA_D": {"R12.2", "Q1.3"},
}

# Pins deliberately unconnected (no-connect flag expected)
NO_CONNECT = {"J1.A6", "J1.B6", "J1.A7", "J1.B7", "J1.A8", "J1.B8",
              "U1.1", "U1.7", "U1.8", "U1.9", "U1.10"}

# Parts not fitted by default
DNP = {"D1"}

# Physical expectations checked against symbol/footprint data
FOOTPRINT_PADS = {
    "U2": "Package_TO_SOT_SMD:TSOT-23-5", "U3": "Package_TO_SOT_SMD:TSOT-23-5",
    "Q1": "Package_TO_SOT_SMD:SOT-23",
}
