"""Hand-routed copper: buck cells, input path, +5V bus, keep-alive, GND vias near power parts.

Every coordinate is derived from pad positions so moving a part keeps the routing honest.
"""
from place import JY, X1, X2

PWR = 0.8      # high-current traces (filament current, +5V)
BUS = 1.0      # +5V bus
SIG = 0.3      # Kelvin sense
GNDW = 0.5
VIA = (0.6, 0.3)
PVIA = (0.8, 0.4)  # power vias


class HR:
    def __init__(self, b):
        self.b = b
        self.tracks = []   # (net, layer, w, [(x,y),...])
        self.vias = []     # (net, x, y, size, drill)

    def P(self, ref, num):
        p = self.b.pad(ref, num)
        return p['cx'], p['cy']

    def t(self, net, pts, w, layer='F.Cu'):
        self.tracks.append((net, layer, w, [tuple(map(float, p)) for p in pts]))

    def v(self, net, x, y, sz=VIA):
        self.vias.append((net, float(x), float(y), sz[0], sz[1]))


def cell(h, X, J, R, U, L, Cd, D, Cb, n):
    """n: channel number (1/2)."""
    A, K, SW = f'/LED{n}_A', f'/LED{n}_K', f'/SW{n}'
    P = h.P
    jx1, jy1 = P(J, '1'); jx2, jy2 = P(J, '2')
    r1x, r1y = P(R, '1'); r2x, r2y = P(R, '2')
    vin = P(U, '5'); setp = P(U, '4'); usw = P(U, '1'); ugnd = P(U, '2')
    l1 = P(L, '1'); l2 = P(L, '2')
    dk = P(D, '1'); da = P(D, '2')
    cbp = P(Cb, '1'); cbn = P(Cb, '2')
    cdp = P(Cd, '1'); cdn = P(Cd, '2')

    # LED anode: sense resistor -> connector pin 1 (filament current)
    h.t(A, [(r2x, r2y), (r2x, r2y - 1.2), (jx1, jy1)], PWR)
    # Kelvin sense: separate thin traces from each resistor pad to the IC
    h.t(A, [(r2x - 0.25, r2y + 0.6), (setp[0], setp[1] - 0.4), setp], SIG)
    h.t('+5V', [(r1x + 0.25, r1y + 0.6), (vin[0], vin[1] - 0.4), vin], SIG)
    # LED cathode: connector pin 2 -> inductor pad 1
    h.t(K, [(jx2, jy2), (jx2, jy2 + 0.9), (l1[0] + 2.6, l1[1] - 0.3), (l1[0] + 1.5, l1[1])], PWR)
    # +5V feed into the sense resistor through a via (the LED path encloses it)
    fv = (X - 2.9, JY + 4.55)
    h.v('+5V', *fv, PVIA)
    h.t('+5V', [fv, (r1x - 0.1, r1y + 0.2)], PWR)
    h.t('+5V', [fv, cdp], 0.4)
    h.t('+5V', [cdp, (vin[0] - 0.2, cdp[1]), (vin[0], vin[1])], SIG)
    # B.Cu stub under the inductor to the +5V spine on the left of the cell
    sp = (X - 11.5, JY + 4.55)
    h.t('+5V', [fv, sp], PWR, 'B.Cu')
    h.v('+5V', *sp, PVIA)
    h.t('+5V', [sp, (sp[0], 24.0)], PWR)
    # 100n GND
    gv = (cdn[0], cdn[1] + 1.15)
    h.v('GND', *gv)
    h.t('GND', [cdn, gv], GNDW)
    # switch node: inductor pad 2 -> diode anode -> IC SW pin
    h.t(SW, [(l2[0] + 2.4, l2[1] + 0.45), (da[0] - 0.5, da[1] - 0.9)], PWR)
    h.t(SW, [usw, (usw[0], da[1] - 0.6)], 0.6)
    # IC GND -> via -> right of the diode -> 10u GND (direct return for the hot loop)
    g1 = (ugnd[0] + 0.3, ugnd[1] + 1.6)
    h.v('GND', *g1)
    h.t('GND', [ugnd, (ugnd[0], ugnd[1] + 0.6), g1], 0.4)
    g2 = (cbn[0] + 1.35, cbn[1])
    h.v('GND', *g2)
    h.t('GND', [g1, (g1[0], cbn[1] - 1.5), g2, cbn], 0.6)
    # diode cathode -> 10u +5V -> bus
    h.t('+5V', [dk, (dk[0] + 0.5, dk[1] + 0.9), (cbp[0], cbp[1] - 0.7), cbp], PWR)
    h.t('+5V', [cbp, (cbp[0], 24.0)], PWR)


def build(b):
    h = HR(b)
    cell(h, X1, 'J4', 'R3', 'U2', 'L1', 'C4', 'D2', 'C2', 1)
    cell(h, X2, 'J5', 'R4', 'U3', 'L2', 'C5', 'D3', 'C3', 2)
    P = h.P

    # ---- +5V bus (left spine to the XIAO feed diode), then on to the keep-alive load ----
    d4a = P('D4', '2')
    h.t('+5V', [(X1 - 11.5, 24.0), (d4a[0], 24.0), (d4a[0], d4a[1])], BUS)
    r12p = P('R12', '1')
    h.t('+5V', [(d4a[0], 24.0), (d4a[0] + 1.1, 22.9), (r12p[0] - 1.0, 22.9), (r12p[0], 23.9), r12p], PWR)
    tp1 = P('TP1', '1')
    h.t('+5V', [tp1, (X1 - 11.5, tp1[1])], PWR)

    # ---- USB-C input ----
    vb1 = [p for p in b.pads('J1') if p['net'] == '/VBUS_IN']
    ys = sorted({round(p['cy'], 3) for p in vb1})
    jx = vb1[0]['cx']
    f1a = P('F1', '1'); f1b = P('F1', '2')
    vx = 9.3
    h.t('/VBUS_IN', [(jx, ys[0]), (vx, ys[0]), (f1a[0] - 0.4, ys[0]), (f1a[0] - 0.1, f1a[1] + 0.1)], 0.6)
    h.t('/VBUS_IN', [(jx, ys[1]), (vx, ys[1])], 0.6)
    h.v('/VBUS_IN', vx, ys[0]); h.v('/VBUS_IN', vx, ys[1])
    h.t('/VBUS_IN', [(vx, ys[0]), (vx, ys[1])], 0.6, 'B.Cu')
    for net, ref in (('/CC1', 'R1'), ('/CC2', 'R2')):
        cp = [p for p in b.pads('J1') if p['net'] == net][0]
        rp = P(ref, '1')
        h.t(net, [(cp['cx'], cp['cy']), (rp[0] - 1.0, cp['cy']), rp], 0.25)
        g = P(ref, '2')
        h.v('GND', g[0] + 1.15, g[1])
        h.t('GND', [g, (g[0] + 1.15, g[1])], GNDW)
    gp = sorted({round(p['cy'], 3) for p in b.pads('J1') if p['net'] == 'GND' and p['kind'] == 'smd'})
    h.v('GND', 9.4, gp[0] - 0.6); h.t('GND', [(jx, gp[0]), (jx + 0.9, gp[0]), (9.4, gp[0] - 0.6)], 0.4)
    h.v('GND', 9.4, gp[1] + 0.6); h.t('GND', [(jx, gp[1]), (jx + 0.9, gp[1]), (9.4, gp[1] + 0.6)], 0.4)
    # fuse -> bus, bulk cap, TVS
    h.t('+5V', [f1b, (f1b[0], 24.0)], BUS)
    c1p = P('C1', '1'); c1n = P('C1', '2')
    h.t('+5V', [c1p, (c1p[0], 24.0)], PWR)
    d1k = P('D1', '1'); d1a = P('D1', '2')
    h.t('+5V', [d1k, (d1k[0], d1k[1] - 1.0), (c1p[0], c1p[1] + 0.5), c1p], 0.6)
    gv = (16.35, 26.9)
    h.v('GND', *gv)
    h.t('GND', [c1n, (c1n[0] + 0.6, c1n[1] + 0.6), gv], GNDW)
    h.t('GND', [d1a, (d1a[0] + 0.35, d1a[1] - 0.6), gv], GNDW)

    # ---- keep-alive (bottom right) ----
    r12d = P('R12', '2')
    qg = P('Q1', '1'); qs = P('Q1', '2'); qd = P('Q1', '3')
    h.t('/KA_D', [qd, r12d], 0.6)
    r10g = P('R10', '2'); r11g = P('R11', '1'); r11n = P('R11', '2')
    h.t('/KA_G', [r10g, (r10g[0], qg[1] + 0.6), qg], 0.3)
    h.t('/KA_G', [r11g, (qg[0] + 0.7, r11g[1]), qg], 0.3)
    h.v('GND', r11n[0], r11n[1] - 1.3); h.t('GND', [r11n, (r11n[0], r11n[1] - 1.3)], GNDW)
    h.v('GND', qs[0], qs[1] - 1.35); h.t('GND', [qs, (qs[0], qs[1] - 1.35)], GNDW)

    # ---- XIAO pin escapes (no vias in the castellated pads) ----
    p14 = P('U1', '14'); p13 = P('U1', '13'); p12 = P('U1', '12')
    h.t('/XIAO_5V', [p14, (59.6, p14[1])], 0.5); h.v('/XIAO_5V', 59.6, p14[1])
    h.t('GND', [p13, (59.6, p13[1])], GNDW); h.v('GND', 59.6, p13[1])
    h.t('+3V3', [p12, (59.6, p12[1])], 0.4); h.v('+3V3', 59.6, p12[1])
    for num, net in (('4', '/RADAR_OT2'), ('5', '/UART_TX'), ('6', '/UART_RX')):
        q = P('U1', num)
        h.t(net, [q, (38.7, q[1])], 0.25); h.v(net, 38.7, q[1])
    # XIAO 5V: B.Cu under the module from the pin-14 via to the feed diode cathode
    d4k = P('D4', '1')
    kv = (d4k[0] + 2.1, d4k[1])
    h.t('/XIAO_5V', [(59.6, p14[1]), (54.0, p14[1] + 5.6), (54.0, 22.0), (kv[0], 22.0 + 54.0 - kv[0]), kv], 0.5, 'B.Cu')
    h.v('/XIAO_5V', *kv)
    h.t('/XIAO_5V', [kv, d4k], 0.5)
    # 3V3 trunk: B.Cu down the right strip, surfacing below the keep-alive
    tv = (60.4, 30.6)
    h.t('+3V3', [(59.6, p12[1]), (60.4, p12[1] + 0.8), tv], 0.4, 'B.Cu')
    h.v('+3V3', *tv)
    return h
