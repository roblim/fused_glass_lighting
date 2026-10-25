#!/usr/bin/env python3
"""Rev G2 LED driver: TPS61500 SEPIC component checks (method from TI SLVA904, April 2018).

Run: python3 sepic_design.py
Prints the operating points that size the parts: switch peak current against the 3 A
minimum limit, switch and diode voltage, inductor currents, coupling-capacitor ripple and
the right-half-plane zero that bounds the loop crossover. Worst-case tolerances follow
SLVA904: inductance -20 %, frequency -20 %. Nothing here is measured; bring-up replaces it.
"""
import math

# ---- chosen values (schematic fgl_g2)
VFB = 0.200                 # TPS61500 FB regulation, 195-205 mV
RS1 = RS2 = 0.82            # R20, R21 (1 %, 1206)
L = 10e-6                   # L1 = L2, SWPA8040S100MT, Isat 4.1 A, DCR ~29 mOhm
F_SW = 1.17e6               # R19 = 82 k (datasheet: 80 k -> 1.2 MHz)
C_COUPLE = 10e-6            # C4, 10 uF 50 V X7R 1206; sits at VIN, so ~8 uF effective
OVP_R1, OVP_R2 = 120e3, 5.1e3
V_OVPREF = 1.229
VD = 0.50                   # SS36 at ~0.5 A
I_SW_LIM_MIN = 3.0          # A
V_SW_ABSMAX = 40.0
P_CAP = 5.0                 # firmware LED power cap, W
EFF = 0.85                  # SLVA904 uses 80 % for sizing and 85 % for the RHPZ
VIN_MIN, VIN_MAX = 4.5, 5.25


def point(vin, vout, iout, l_tol=0.8, f_tol=0.8):
    d = (vout + VD) / (vin + vout + VD)
    pout = vout * iout
    iin = pout / (EFF * vin)                 # = average L1 current
    di = vin * d / (L * l_tol * F_SW * f_tol)  # ripple in each inductor (uncoupled)
    isw_pk = iin + iout + di                 # IL1pk + IL2pk = Iin + Iout + 2 * di/2
    vsw = vin + vout + VD
    dvc = iout * d / (C_COUPLE * 0.8 * F_SW)
    rload = vout / iout
    f_rhpz = rload * (1 - d) ** 2 / (2 * math.pi * d * L)
    return dict(d=d, pout=pout, iin=iin, di=di, isw_pk=isw_pk, vsw=vsw, dvc=dvc, f_rhpz=f_rhpz)


def main():
    i1 = VFB / RS1
    i2 = VFB / (RS1 * RS2 / (RS1 + RS2))
    ovp = V_OVPREF * (1 + OVP_R1 / OVP_R2)
    print("I_max: %.0f mA (JP1 open), %.0f mA (JP1 bridged)" % (i1 * 1e3, i2 * 1e3))
    print("OVP: %.1f V; switch at OVP and %.2f V in: %.1f V (abs max %.0f V)"
          % (ovp, VIN_MAX, ovp + VD + VIN_MAX, V_SW_ABSMAX))
    print("Sense resistor dissipation: %.0f mW each" % (VFB * i1 * 1e3))
    print()
    print("%-34s %5s %6s %6s %6s %7s %6s %6s %8s" %
          ("case (VIN 4.5 V, L and f -20 %)", "D", "Pout", "Iin", "dI", "Isw_pk", "Vsw", "dVc", "f_RHPZ"))
    cases = [
        ("one 3 V filament, 244 mA", 2.75, i1),
        ("one 3 V filament, 488 mA", 2.95, i2),
        ("one 12 V 600 mm, 150 mA", 10.9, 0.150),
        ("one 12 V 600 mm, 244 mA", 11.2, i1),
        ("12 V 600 mm at the 5 W cap", 11.4, P_CAP / 11.4),
        ("4 x 3 V, 488 mA -> 5 W cap", 11.8, P_CAP / 11.8),
        ("~28 V string at the 5 W cap", 28.0, P_CAP / 28.0),
        ("30 V (OVP) string at 5 W", 30.0, P_CAP / 30.0),
    ]
    worst = 0
    for name, vout, iout in cases:
        r = point(VIN_MIN, vout, iout)
        worst = max(worst, r["isw_pk"])
        print("%-34s %5.2f %5.2fW %5.2fA %5.2fA %6.2fA %5.1fV %4.0fmV %6.0fkHz" %
              (name, r["d"], r["pout"], r["iin"], r["di"], r["isw_pk"], r["vsw"], r["dvc"] * 1e3,
               r["f_rhpz"] / 1e3))
    print()
    print("Worst switch peak %.2f A vs %.1f A minimum limit: margin %.0f %%"
          % (worst, I_SW_LIM_MIN, 100 * (1 - worst / I_SW_LIM_MIN)))
    low = min(point(VIN_MIN, v, i)["f_rhpz"] for _, v, i in cases)
    print("Lowest RHPZ %.0f kHz -> keep loop crossover below %.1f kHz (10x). SLVA904 measured 1.7 kHz"
          " at 5 V with 15 nF and 4.7 uH; G2 uses 100 nF and 10 uH, which lowers it further." % (low / 1e3, low / 1e4))
    print("Without the firmware cap (fault), a 30 V string at 488 mA asks for 14.6 W: the 3 A switch limit")
    print("and F1 (1.5 A hold / 3 A trip) limit it; nothing in the power path is rated below that.")


if __name__ == "__main__":
    main()
