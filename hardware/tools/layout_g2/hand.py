"""Hand-routed copper for fgl_g2: USB-C input escapes, power switch, +5V spine, SEPIC power
stage, controller pin escapes, filament-port chain and the LED_RTN bus.

Every coordinate is taken from pad positions, so moving a part keeps the routing honest.
The maze router (build.py) connects whatever is left.
"""

BUS = 1.0      # +5V spine, LED_RTN bus, port chain
PWR = 0.8
SIG = 0.25
VIA = (0.6, 0.3)
PVIA = (0.8, 0.4)

SPINE_Y = 15.8     # +5V spine, between the port bodies and L1
RTN_Y = 12.6       # LED_RTN bus under the port row


class HR:
    def __init__(self, b):
        self.b = b
        self.tracks = []   # (net, layer, w, [(x,y),...])
        self.vias = []     # (net, x, y, size, drill)

    def P(self, ref, num):
        p = self.b.pad(ref, num)
        return round(p['cx'], 3), round(p['cy'], 3)

    def t(self, net, pts, w, layer='F.Cu'):
        self.tracks.append((net, layer, w, [tuple(map(float, p)) for p in pts]))

    def v(self, net, x, y, sz=VIA):
        self.vias.append((net, float(x), float(y), sz[0], sz[1]))


def build(b):
    h = HR(b)
    P, t, v = h.P, h.t, h.v

    # ---------------- USB-C input ----------------
    vt = P('J1', 'A9')      # VBUS pair at the top (A9/B4 share a pad position)
    vb = P('J1', 'A4')      # VBUS pair at the bottom (A4/B9)
    f1 = P('F1', '1'); f2 = P('F1', '2')
    x_v = 65.2
    t('VBUS_IN', [vt, (65.6, vt[1])], 0.6)
    t('VBUS_IN', [(65.6, vt[1]), (f1[0], vt[1])], PWR)
    t('VBUS_IN', [vb, (x_v, vb[1])], 0.6)
    v('VBUS_IN', x_v, vt[1], PVIA)
    v('VBUS_IN', x_v, vb[1], PVIA)
    t('VBUS_IN', [(x_v, vt[1]), (x_v, vb[1])], PWR, 'B.Cu')
    # CC escapes: out under the fuse body to vias, then the router takes them down on B.Cu
    c1 = P('J1', 'A5'); c2 = P('J1', 'B5')
    t('CC1', [c1, (65.7, c1[1]), (65.3, 17.8), (64.2, 17.8)], SIG)
    v('CC1', 64.2, 17.8)
    t('CC2', [c2, (65.8, c2[1]), (65.4, 16.2), (63.4, 16.2)], SIG)
    v('CC2', 63.4, 16.2)

    # ---------------- fuse -> P-FET -> +5V ----------------
    qs = P('Q2', '2'); qd = P('Q2', '3'); qg = P('Q2', '1')
    t('VBUS_F', [f2, (qs[0] + 0.6, f2[1]), qs], PWR)
    r13a = P('R13', '1'); r13b = P('R13', '2')
    t('VBUS_F', [qs, (qs[0], r13a[1] - 0.8), r13a], 0.5)
    t('Q2_G', [qg, (qg[0], r13b[1] - 0.8), r13b], 0.4)
    r14a = P('R14', '1')
    t('Q2_G', [r13b, r14a], 0.4)

    # +5V spine
    c3p = P('C3', '1')
    t('+5V', [qd, (qd[0], SPINE_Y)], 0.6)
    t('+5V', [(qd[0], SPINE_Y), (c3p[0], SPINE_Y), c3p], BUS)
    for ref in ('C1', 'C2'):
        p = P(ref, '1')
        t('+5V', [(p[0], SPINE_Y), p], PWR)
    l1a = P('L1', '1')
    t('+5V', [(l1a[0], SPINE_Y), (l1a[0], l1a[1] - 2.5)], BUS)
    # C3 -> VIN pin
    vin = P('U2', '3')
    t('+5V', [c3p, (vin[0], vin[1] - 1.2), vin], 0.3)

    # ---------------- SEPIC power stage ----------------
    sw1 = P('U2', '1'); sw2 = P('U2', '2')
    l1b = P('L1', '2')
    t('SW', [sw2, sw1], 0.4)
    t('SW', [sw1, (l1b[0], sw1[1])], PWR)
    c4a = P('C4', '1'); c4b = P('C4', '2')
    t('SW', [(l1b[0], l1b[1] + 2.5), c4a], BUS)
    l2a = P('L2', '1'); d5a = P('D5', '2'); d5k = P('D5', '1')
    t('SEP_B', [c4b, (c4b[0], l2a[1]), l2a], BUS)
    t('SEP_B', [(c4b[0], l2a[1]), d5a], BUS)
    c5 = P('C5', '1'); c6 = P('C6', '1')
    t('VOUT', [d5k, c5], BUS)
    t('VOUT', [c5, c6], PWR)
    r15v = P('R15', '1')
    t('VOUT', [r15v, (r15v[0] - 1.0, r15v[1] + 1.0), (d5k[0] + 0.3, r15v[1] + 1.0), (d5k[0], d5k[1] - 0.5)], 0.4)

    # controller GND pins onto the exposed pad
    for n, dy in (('7', +1.4), ('12', -1.4), ('13', -1.4), ('14', -1.4)):
        p = P('U2', n)
        t('GND', [p, (p[0], p[1] + dy)], 0.3)

    # EN / SS / DIMC staircase (rightmost pin climbs highest)
    en = P('U2', '4'); r18 = P('R18', '1'); r17 = P('R17', '2')
    t('DRV_EN', [en, (en[0], r18[1]), r18, r17], SIG)
    ss = P('U2', '5'); c8 = P('C8', '1')
    t('SS', [ss, (ss[0], c8[1]), c8], SIG)
    dm = P('U2', '6'); c7 = P('C7', '1')
    t('DIMC', [dm, (dm[0], 19.9), (c7[0] + 0.7, 19.9), c7], SIG)
    # COMP / FB / FREQ / OVP below
    cp = P('U2', '8'); c9 = P('C9', '1')
    t('COMP', [cp, (cp[0], cp[1] + 1.05), c9], SIG)
    fq = P('U2', '10'); r19 = P('R19', '1')
    t('FREQ', [fq, (fq[0], fq[1] + 1.15), r19], SIG)
    ov = P('U2', '11'); r16 = P('R16', '1'); r15o = P('R15', '2')
    t('OVP', [ov, (ov[0], ov[1] + 1.05), (r16[0] - 0.45, r16[1]), r15o], SIG)
    fb = P('U2', '9')
    fbv = (fb[0] - 0.3, fb[1] + 1.75)       # via clear of R19 pad 1; FB continues on B.Cu
    t('LED_RTN', [fb, fbv], SIG)
    v('LED_RTN', *fbv)

    # ---------------- filament ports ----------------
    for a, k, net in (('J5', 'J6', 'STR2'), ('J6', 'J7', 'STR3'), ('J7', 'J8', 'STR4')):
        n = P(a, '2'); p1 = P(k, '1')
        t(net, [n, (p1[0] - 2.5, n[1]), (p1[0], n[1] + 2.5), p1], BUS)
    j82 = P('J8', '2'); j83 = P('J8', '3')
    t('LED_RTN', [j82, (j83[0] - 2.0, j82[1]), (j83[0], j82[1] + 2.0), j83], BUS)
    ends = [P(j, '3') for j in ('J5', 'J6', 'J7', 'J8')]
    for e in ends:
        t('LED_RTN', [e, (e[0], RTN_Y)], BUS)
    t('LED_RTN', [(ends[0][0], RTN_Y), (ends[-1][0], RTN_Y)], BUS)
    # bus -> the two sense resistors
    r20 = P('R20', '1'); r21 = P('R21', '1')
    xm = round((r20[0] + r21[0]) / 2, 3)
    t('LED_RTN', [(xm, RTN_Y), (xm, r20[1])], BUS)
    t('LED_RTN', [r20, r21], BUS)
    # 500 mA leg: R21 -> JP1 pad 1
    t('RS2_B', [P('R21', '2'), P('JP1', '1')], PWR)
    return h
