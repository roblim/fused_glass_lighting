"""Placement for fgl_g2 (board-local mm, origin top-left, y down).

Flow, right to left: USB-C J1 (right edge) -> F1 -> Q2 (power switch) -> +5V bus along y~16 ->
L1 / U2 (SEPIC switch node) -> C4 -> D5 -> VOUT -> left side -> port J5 '+'.
The four filament ports run along the top edge; the LED_RTN bus sits under them.
XIAO (plugs into J9/J10) at the bottom-left, radar module (plugs into J3) over the bottom-right.
"""
W, H = 74.0, 58.0

# ---- filament ports along the top edge (Degson DG250-3.5-03P): pin 1 '+' and pin 3 'END'
#      on row A (y = PY), pin 2 'NEXT' on row B (y = PY - 5), wire entry toward the top edge
PY = 9.8
PX = [10.8, 24.3, 37.8, 51.3]          # pin-1 x of J5..J8 (13.5 mm pitch)

# ---- XIAO module centre (USB-C at the left board edge); J9 = XIAO pins 1-7, J10 = pins 8-14
XC = (13.5, 46.0)

# ---- SEPIC controller centre (rot 270: SW/VIN/EN/SS/DIMC/AGND along the top edge,
#      COMP/FB/FREQ/OVP/PGND along the bottom edge)
UX, UY = 40.0, 24.0

PLACE = {
    'J5': (PX[0], PY, 0), 'J6': (PX[1], PY, 0), 'J7': (PX[2], PY, 0), 'J8': (PX[3], PY, 0),
    'H1': (3.5, 3.5, 0), 'H2': (70.5, 3.5, 0), 'H3': (3.5, 27.0, 0), 'H4': (70.5, 30.0, 0),

    # ---- SEPIC power stage
    'U2': (UX, UY, 270),
    'L1': (UX + 8.0, 21.0, 180),          # pad 2 (SW) left, next to U2's SW pins; pad 1 (+5V) right
    'C3': (UX + 1.9, 18.6, 0),            # 100n above VIN: pad 1 (+5V) left, pad 2 (GND) right
    'C2': (53.6, 18.4, 270),              # 10u SEPIC input bulk (input current is continuous through L1)
    'C4': (UX + 5.0, 28.6, 270),          # coupling cap: pad 1 SW (top), pad 2 SEP_B (bottom)
    'L2': (UX + 10.8, 31.2, 0),           # pad 1 SEP_B left, pad 2 GND right
    'D5': (UX + 2.5, 33.0, 0),            # pad 1 K = VOUT (left), pad 2 A = SEP_B (right)
    'C5': (UX - 3.5, 33.0, 180),          # 10u output: pad 1 VOUT right, pad 2 GND left
    'C6': (UX - 3.5, 35.6, 180),
    'TP6': (UX - 7.6, 34.2, 0),           # VOUT

    # ---- controller small parts: EN / SS / DIMC above, COMP / FREQ / OVP below
    'R17': (UX - 4.4, 17.2, 0),           # DIM_PWM -> EN
    'R18': (UX - 2.0, 16.55, 90),           # EN pull-down
    'C8': (UX - 3.6, 18.8, 180),            # SS
    'C7': (UX - 4.3, 20.6, 180),            # DIMC
    'C9': (UX - 3.6, 29.5, 270),          # COMP
    'R19': (UX - 0.6, 29.5, 270),         # FREQ
    'R16': (UX + 1.2, 29.5, 270),         # OVP -> GND
    'R15': (UX + 3.0, 29.5, 90),          # VOUT -> OVP (pad 1 bottom, toward D5's cathode)

    # ---- current sense, 250/500 mA jumper, LED_RTN test point
    'R20': (UX - 13.5, 22.4, 270),         # 0.82R LED_RTN -> GND
    'R21': (UX - 10.8, 22.4, 270),         # 0.82R LED_RTN -> RS2_B
    'JP1': (UX - 10.8, 27.2, 270),
    'TP3': (UX - 15.6, 18.0, 0),          # LED_RTN

    # ---- input: USB-C on the right edge, fuse, P-FET power switch
    'J1': (70.8, 17.0, 90),
    'F1': (62.6, 17.0, 270),              # pad 1 VBUS_IN top, pad 2 VBUS_F bottom
    'Q2': (58.6, 18.6, 90),               # G bottom-left, S bottom-right, D top
    'D1': (62.4, 22.2, 0),                # TVS (DNP)
    'R13': (58.6, 22.4, 180),             # VBUS_F (pad 1, right) -> G (pad 2, left)
    'R14': (58.6, 24.2, 0),               # G -> SW_N
    'R1': (66.2, 24.4, 270),
    'R2': (68.0, 24.4, 270),
    'C1': (55.6, 18.4, 270),               # 10u bulk on +5V after the switch
    'TP1': (55.4, 22.6, 0),               # +5V

    # ---- keep-alive load
    'R12': (61.0, 28.6, 0),
    'Q1': (61.0, 32.6, 0),
    'R10': (57.4, 34.6, 0),
    'R11': (61.4, 35.4, 0),

    # ---- MCU sockets and support parts (low parts under the plug-in module are fine)
    'J9': (XC[0] - 7.62, XC[1] + 7.62, 90),     # XIAO pins 1-7 along +x
    'J10': (XC[0] + 7.62, XC[1] - 7.62, 270),   # XIAO pins 8-14 along -x
    'D4': (9.6, 34.4, 0),
    'C10': (14.9, 34.6, 0),
    'C11': (18.4, 34.6, 0),
    'TP4': (21.4, 34.4, 0),               # 3V3
    'R22': (21.2, 46.0, 90),              # ISEL_IO -> ISEL
    'R23': (19.0, 46.0, 90),
    'R24': (11.4, 46.0, 90),              # VOUT -> VSENSE
    'R25': (9.2, 46.0, 90),
    'C15': (7.0, 46.0, 90),
    'R6': (13.6, 46.0, 90),               # POT_W -> ADC
    'C12': (15.6, 46.0, 90),
    'R5': (17.2, 42.2, 90),               # 3V3 -> POT_HI
    'TP2': (33.6, 45.4, 0),               # GND

    # ---- pot and radar-cable connectors on the bottom edge (openings face the edge)
    'J2': (26.0, 51.2, 0),
    'J4': (37.5, 51.2, 0),

    # ---- radar socket (module plugs in over the bottom-right corner)
    'J3': (52.0, 54.6, 90),               # pins 1..5 along +x
    'R26': (52.6, 44.6, 0), 'R27': (52.6, 46.4, 0), 'R28': (52.6, 48.2, 0),
    'R7': (56.2, 48.2, 0),
    'TP5': (59.6, 48.4, 0),
    'FB1': (56.2, 44.6, 0),
    'C13': (59.8, 44.6, 0),
    'C14': (59.8, 46.4, 0),
}
