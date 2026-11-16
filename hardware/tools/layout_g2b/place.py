"""Placement for fgl_g2, 90 x 60 mm relayout (D19). Board-local mm, origin top-left, y down.

Same flow as the 74 x 58 layout (layout_g2/place.py), spread out for rework:
  - the four ports are horizontal-entry push-in blocks (JILN JL212R) along the top edge, release
    buttons flush with the edge, 15 mm apart so a finger fits between them;
  - USB-C J1 on the right edge -> F1 -> Q2 -> +5V spine (y = SPINE_Y) -> L1 / U2;
  - XIAO bottom-left (its USB-C at the left edge), radar bottom-right, pot and radar-cable
    connectors on the bottom edge; M3 holes in the four corners.
Small parts keep at least ~1 mm between courtyards; parts under the plug-in XIAO and radar are
reachable by unplugging the module.
"""
W, H = 90.0, 60.0

# ---- ports: JL212R footprint origin = '+' pin, front row; buttons 5.1 mm in front of it
PTIP = 0.3                              # board y of the button fronts
PY = PTIP + 5.1                         # front pin row; rear row at PY + 7
PX = [12.0, 27.0, 42.0, 57.0]           # '+' pin x of J5..J8 (15 mm pitch)

XC = (13.5, 42.0)                       # XIAO module centre
UX, UY = 45.0, 28.5                     # TPS61500 centre
J3X, J3Y = 70.2, 56.4                   # radar socket pin 1

PLACE = {
    'J5': (PX[0], PY, 0), 'J6': (PX[1], PY, 0), 'J7': (PX[2], PY, 0), 'J8': (PX[3], PY, 0),
    'H1': (3.5, 3.5, 0), 'H2': (W - 3.5, 3.5, 0), 'H3': (3.5, H - 3.5, 0), 'H4': (W - 3.5, H - 3.5, 0),

    # ---- SEPIC power stage (same arrangement as layout_g2, a little more room)
    'U2': (UX, UY, 270),
    'L1': (UX + 8.6, 25.0, 180),          # pad 2 (SW) left, pad 1 (+5V) right
    'C3': (UX + 1.9, 22.4, 0),            # 100n at VIN
    'C2': (UX + 15.0, 24.2, 270),         # 10u SEPIC input
    # switching loop U2 SW -> C4 -> D5 -> C5/C6 -> GND -> U2, tightened after Flux's layout review
    # (2026-10-28): C4 lies under L1, D5 stands below C4's SEP_B end, C5/C6 sit beside D5's
    # cathode with their GND over the solid B.Cu ground under U2
    'C4': (50.4, 30.9, 0),            # coupling: pad 1 SW (left, from L1's SW pad), pad 2 SEP_B (right)
    'L2': (58.4, 36.0, 0),            # pad 1 SEP_B left, pad 2 GND right
    'D5': (51.9, 36.3, 90),           # pad 2 A = SEP_B (top, under C4), pad 1 K = VOUT (bottom)
    'C5': (47.4, 39.0, 180),          # 10u output: pad 1 VOUT right (to D5 K), pad 2 GND left
    'C6': (47.4, 41.7, 180),
    'TP6': (UX - 9.4, 40.0, 0),           # VOUT

    # ---- controller small parts: EN / SS / DIMC above, COMP / FREQ / OVP below
    'R17': (39.6, 20.0, 0),           # DIM_PWM -> EN
    'R18': (42.9, 20.4, 90),          # EN pull-down
    'C8': (39.9, 23.0, 180),          # SS
    'C7': (39.6, 25.4, 180),          # DIMC
    'C9': (40.8, 34.8, 270),          # COMP
    'R19': (43.4, 34.8, 270),         # FREQ
    'R16': (45.9, 34.8, 270),         # OVP -> GND
    'R15': (48.4, 34.8, 90),          # VOUT -> OVP (pad 1 bottom)

    # ---- current sense, current jumper, LED_RTN test point
    'R20': (22.0, 19.6, 270),             # 0.82R LED_RTN -> GND
    'R21': (25.4, 19.6, 270),             # 0.82R LED_RTN -> RS2_B
    'JP1': (29.0, 24.8, 270),             # pin 1 right
    'TP3': (18.0, 19.6, 0),               # LED_RTN

    # ---- input: USB-C on the right edge, fuse, soft-start P-FET switch
    'J1': (W - 3.2, 20.0, 90),
    'F1': (78.6, 20.0, 270),              # pad 1 VBUS_IN top, pad 2 VBUS_F bottom
    'Q2': (73.6, 21.6, 90),               # G bottom-left, S bottom-right, D top
    'C16': (73.6, 27.8, 180),              # Q2 gate-source soft start
    'R13': (73.6, 25.4, 180),             # VBUS_F -> G
    'R14': (73.6, 30.2, 0),               # G -> SW_N
    'D1': (78.4, 26.8, 0),                # TVS (DNP)
    'R1': (83.4, 30.0, 270),
    'R2': (86.2, 30.0, 270),
    'C1': (68.4, 22.0, 270),              # 10u on +5V after the switch
    'TP1': (67.6, 26.4, 0),               # +5V

    # ---- keep-alive load
    'R12': (74.6, 34.0, 0),
    'Q1': (81.4, 34.6, 0),
    'R10': (81.4, 38.0, 0),
    'R11': (85.6, 34.6, 90),

    # ---- MCU sockets and support parts
    'J9': (XC[0] - 7.62, XC[1] + 7.62, 90),     # XIAO pins 1-7 along +x
    'J10': (XC[0] + 7.62, XC[1] - 7.62, 270),   # XIAO pins 8-14 along -x
    'D4': (6.4, 29.6, 0),
    'C10': (12.4, 29.6, 0),
    'C11': (12.4, 26.2, 0),
    'TP4': (16.4, 25.6, 0),               # 3V3
    'JP2': (23.0, 29.8, 270),             # pin 1 right
    'R29': (20.46, 25.6, 270),            # RADAR_MODE pull-up: pad 1 (+3V3) top, pad 2 down to JP2 pin 2
    'R22': (21.6, 42.4, 90),              # ISEL_IO -> ISEL (under the XIAO)
    'R23': (19.2, 42.4, 90),
    'R24': (9.0, 42.4, 90),               # VOUT -> VSENSE
    'R25': (6.6, 42.4, 90),
    'C15': (4.2, 42.4, 90),
    'R6': (11.4, 42.4, 90),               # POT_W -> ADC
    'C12': (13.8, 42.4, 90),
    'R5': (16.6, 42.4, 90),               # 3V3 -> POT_HI
    'TP2': (34.6, 47.0, 0),               # GND

    # ---- pot and radar-cable connectors on the bottom edge (openings face the edge)
    'J2': (27.0, 53.2, 0),
    'J4': (39.4, 53.2, 0),

    # ---- radar socket (module over the bottom-right) and its parts
    'J3': (J3X, J3Y, 90),                 # pins 1..5 along +x
    'R26': (66.0, 45.0, 0), 'R27': (66.0, 47.4, 0), 'R28': (66.0, 49.8, 0),
    'R7': (70.6, 49.8, 0),
    'FB1': (70.6, 45.0, 0),
    'C13': (75.4, 45.0, 0),
    'C14': (75.4, 47.8, 0),
    'TP5': (58.6, 50.6, 0),               # RADAR_OT2, clear of the module
}
