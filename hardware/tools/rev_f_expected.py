"""Rev F prototype as built, written by hand from Rob's description (2026-10-14)
and the Oct 6 point-to-point wiring table. Independent of gen_rev_f.py."""

NETS = {
    "+5V": {"M1.1", "D1.2", "M2.1", "M3.1", "C1.1", "C2.1", "R7.1"},
    "GND": {"M1.2", "U1.13", "M2.2", "M3.2", "C1.2", "C2.2", "R3.2", "RV1.3", "C5.2",
            "M4.2", "C3.2", "C4.2", "Q1.1", "R6.2"},
    "XIAO_5V": {"D1.1", "U1.14"},
    "+3V3": {"U1.12", "R4.1", "M4.1", "C3.1", "C4.1"},
    "CE_PWM": {"U1.3", "M2.3", "M3.3", "R3.1"},
    "L1_P": {"M2.4", "R1.1"},
    "FIL1_A": {"R1.2", "LED1.2"},
    "L1_N": {"LED1.1", "M2.5"},
    "L2_P": {"M3.4", "R2.1"},
    "FIL2_A": {"R2.2", "LED2.2"},
    "L2_N": {"LED2.1", "M3.5"},
    "POT_HI": {"R4.2", "RV1.1"},
    "ADC_POT": {"RV1.2", "C5.1", "U1.2"},
    "UART_RX": {"M4.3", "U1.6"},
    "UART_TX": {"M4.4", "U1.5"},
    "RADAR_OT2": {"M4.5", "U1.4"},
    "KA_DRV": {"U1.11", "R5.1"},
    "KA_G": {"R5.2", "R6.1", "Q1.2"},
    "KA_D": {"R7.2", "Q1.3"},
}
NO_CONNECT = {"U1.1", "U1.7", "U1.8", "U1.9", "U1.10"}
DNP = set()
CHECK_FOOTPRINTS = False
