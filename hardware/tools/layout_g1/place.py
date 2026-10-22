"""Placement for fgl_g1 (board-local mm, origin top-left, y down). Board 66 x 44 mm."""
W, H = 66.0, 44.0
JY = 6.4                     # filament connector pin row
X1, X2 = 14.5, 30.5          # channel 1 / channel 2 connector pin-1 x


def cell(X, J, R, U, L, Cd, D, Cb):
    """One AL8860 buck cell anchored on the filament connector's pin 1."""
    return {
        J: (X, JY, 180),            # opening faces the top edge
        R: (X, JY + 3.6, 0),        # sense: pad1 +5V left, pad2 LED_A right
        U: (X, JY + 7.2, 90),       # VIN/SET up (Kelvin to R), SW/GND/CTRL down
        L: (X - 7.0, JY + 5.3, 270),  # pad1 LED_K top, pad2 SW bottom
        Cd: (X - 2.75, JY + 6.6, 270),  # 100n at VIN: +5V top, GND bottom
        D: (X - 3.5, JY + 11.8, 0),   # K (+5V) left, A (SW) right under U.SW
        Cb: (X - 3.5, JY + 14.8, 0),  # 10u: +5V left, GND right
    }


PLACE = {}
PLACE.update(cell(X1, 'J4', 'R3', 'U2', 'L1', 'C4', 'D2', 'C2'))
PLACE.update(cell(X2, 'J5', 'R4', 'U3', 'L2', 'C5', 'D3', 'C3'))
PLACE.update({
    # mounting holes
    'H1': (3.5, 3.5, 0), 'H2': (62.5, 3.5, 0), 'H3': (3.5, 40.5, 0), 'H4': (62.5, 40.5, 0),
    # XIAO: USB-C at the top edge (module edge on the board edge, plug overhangs)
    'U1': (40.0, 21.0, 0),
    # input
    'J1': (3.5, 31.5, 270),        # mouth faces the left edge
    'F1': (10.8, 27.4, 90),        # pad1 VBUS_IN bottom, pad2 +5V top
    'R1': (13.0, 30.6, 0),
    'R2': (13.0, 32.9, 0),
    'C1': (14.0, 26.0, 0),
    'D1': (14.3, 28.4, 0),
    # keep-alive
    'R10': (62.6, 28.6, 0),        # pad1 KA_DRV left, pad2 KA_G right
    'Q1': (62.0, 25.0, 180),       # D left (to R12), G/S right
    'R11': (64.8, 25.0, 90),       # pad1 KA_G bottom, pad2 GND top
    'R12': (56.0, 25.0, 0),        # pad1 +5V left, pad2 KA_D right
    # XIAO feed diode
    'D4': (47.5, 25.8, 180),       # A (+5V) left, K (XIAO_5V) right
    # dimming RC and ADC filter, beside the XIAO's signal column
    'R8': (37.0, 7.96, 180),       # pad1 DIM_PWM right, pad2 DIM_CTRL left
    'R9': (35.4, 11.0, 270),
    'C7': (37.0, 11.0, 270),
    'C6': (37.4, 5.42, 180),       # pad1 ADC right, pad2 GND left
    # pot
    'J2': (24.5, 37.75, 0),        # opening faces the bottom edge
    'R5': (24.5, 33.6, 270),       # pad1 3V3 top, pad2 POT_HI bottom
    'R6': (26.5, 33.6, 90),        # pad1 POT_W bottom, pad2 ADC top
    # radar
    'J3': (34.7, 37.75, 0),        # signal pins directly under the XIAO signal column
    'C8': (35.7, 32.6, 0),
    'C9': (35.7, 34.6, 0),
    'R7': (44.5, 33.0, 0),
    # test points
    'TP1': (6.0, 21.3, 0),         # +5V
    'TP2': (17.2, 32.6, 0),        # GND
    'TP3': (35.4, 14.6, 0),        # DIM_CTRL
    'TP4': (31.6, 32.2, 0),        # 3V3
    'TP5': (47.5, 33.0, 0),        # RADAR_OT2
})
