#!/usr/bin/env python3
"""Power and runtime model for the fused-glass filament lamp.

Every input is listed in INPUTS with where it came from. Nothing here is
measured; the bring-up tests in docs/design_review.md replace these numbers
with measurements. Run:  python3 power_model.py
"""

# ---------------------------------------------------------------- inputs
INPUTS = dict(
    # Filament (jojofuny 30 cm 3 V). Vf at 300 mA is NOT measured yet (test T2).
    VF=2.80,            # V at 300 mA, Rev B estimate
    # AL8860 (Diodes datasheet): VSENSE 100 mV typ (96-104), ripple 0.40*ILED,
    # RSW 0.3 ohm (inductor equation note), Iq 0.55 mA, shutdown 50 uA typ.
    RS=0.33, VSENSE=0.100, RSW=0.30, IQ_DRV=0.55e-3, ISD_DRV=50e-6,
    # SWPA6045S470MT: 47 uH, DCR 0.20 ohm (LCSC C36414)
    L=47e-6, RL=0.20,
    # SS14 catch diode, VF at ~0.3 A (datasheet curve, ~0.38 V)
    VD=0.38,
    # Switching loss estimate per transition: 0.5*V*I*t, t ~ 20 ns each edge
    T_EDGE=20e-9,
    # Input path: PTC 1206L075 0.09 ohm + J1 + traces 0.03 ohm
    R_IN=0.12,
    # XIAO ESP32C3 lit (80-160 MHz, radios off) ~20 mA at 3.3 V via its LDO
    I_XIAO_ON=20e-3,
    # Light sleep: ESP32-C3 ~130 uA + XIAO LDO Iq; Seeed quotes 44 uA deep sleep
    I_XIAO_SLEEP=0.20e-3,
    # Wake every 10 s for the 200 ms keep-alive pulse, CPU awake at ~15 mA
    I_WAKE=15e-3, T_WAKE=0.200, T_PERIOD=10.0,
    # LD2410S average (vendor: 0.1-0.45 mA depending on report rate)
    I_RADAR=0.45e-3,
    # Pot divider: G1 47k + 100k = 22 uA; Rev F 4.7k + 10k = 0.22 mA
    I_POT_G1=3.3/147e3, I_POT_F=3.3/14.7e3,
    # Keep-alive: 33 ohm at 5 V, 200 ms every 10 s
    R_KA=33.0, KA_DUTY=0.02,
    # XIAO charge LED with no battery: UNKNOWN, 0 or a few mA (test T8)
    I_CHG_LED=0.0,
    # Bank: nominal cell 3.7 V; usable fraction after boost losses and cutoff
    V_CELL=3.7, BANK_EFF=0.85,
    # Rev F (as built): CN5711 linear sink, current set ~300 mA by trimmer
    I_F_CH=0.300,
    # ---- Rev G2: TPS61500 SEPIC, series string (docs/g2_decisions.md)
    # SEPIC efficiency: TI SLVA904 sizes at 80 % and assumes 85 % for loop calcs; 84 % is
    # used here, flat. Replace with the bring-up measurement.
    EFF_SEPIC=0.84,
    IQ_TPS=2.0e-3,          # TPS61500 operating quiescent (estimate), shutdown 2 uA max
    ISD_TPS=2e-6,
    # Filament forward voltage per type at the drive current (Adafruit / DFRobot tables)
    VF_12V_150=10.9, VF_12V_244=11.2, VF_3V_150=2.72, VF_3V_244=2.80,
    # G2 standing currents while ON: Q2 gate pull-up R13 (5 V / 101 k), EN pull-down only when lit
    I_R13=5.0 / 101e3, I_EN_PD=3.3 / 101e3,
    # Pot divider stays 47 k + 100 k
)
for k, v in INPUTS.items():
    globals()[k] = v

def al8860(vin, iled=VSENSE / RS, vf=VF):
    """Operating point of one AL8860 channel from the datasheet equations."""
    di = 0.40 * iled
    ton = L * di / (vin - vf - iled * (RS + RL + RSW))
    toff = L * di / (vf + VD + iled * (RS + RL))
    f = 1 / (ton + toff)
    d = ton / (ton + toff)
    irms2 = iled**2 + di**2 / 12              # triangular ripple
    p_led = vf * iled
    p_rs = irms2 * RS
    p_rl = irms2 * RL
    p_sw = irms2 * RSW * d
    p_d = VD * iled * (1 - d)
    p_swt = 0.5 * vin * iled * 2 * T_EDGE * f   # on + off edges
    p_q = vin * IQ_DRV
    p_in = p_led + p_rs + p_rl + p_sw + p_d + p_swt + p_q
    return dict(vin=vin, i=iled, f=f, d=d, ton=ton, p_in=p_in, p_led=p_led,
                eff=p_led / p_in, loss=p_in - p_led,
                parts=dict(rs=p_rs, rl=p_rl, sw=p_sw, diode=p_d, swt=p_swt, q=p_q))

def bank_wh(mah):
    return mah / 1000 * V_CELL * BANK_EFF

def runtime(mah, p_on_w, p_idle_w, hours_on):
    day_wh = p_on_w * hours_on + p_idle_w * (24 - hours_on)
    return bank_wh(mah) / day_wh

def g1_lit(level=1.0, vin=5.0):
    """Input power with both channels at `level` (0-1) of 303 mA (analog dim)."""
    ch = al8860(vin, iled=level * VSENSE / RS) if level > 0 else None
    p = 2 * ch["p_in"] if ch else 2 * vin * ISD_DRV
    p += vin * (I_XIAO_ON + I_RADAR + I_POT_G1 + I_CHG_LED)
    i = p / vin
    p += i**2 * R_IN
    return p, p / vin

def g1_idle(keepalive=True, vin=5.0):
    i = (I_XIAO_SLEEP + I_WAKE * T_WAKE / T_PERIOD + I_RADAR + I_POT_G1
         + 2 * ISD_DRV + I_CHG_LED)
    if keepalive:
        i += vin / R_KA * KA_DUTY
    return vin * i, i

def revf_lit(duty=1.0, vin=5.0):
    i = 2 * I_F_CH * duty + I_XIAO_ON + I_RADAR + I_POT_F + I_CHG_LED
    return vin * i, i

def revf_idle(vin=5.0):
    i = (I_XIAO_SLEEP + I_WAKE * T_WAKE / T_PERIOD + I_RADAR + I_POT_F
         + I_CHG_LED + vin / R_KA * KA_DUTY)
    return vin * i, i

def g2_lit(v_string, i_led, vin=5.0):
    """Input power with the G2 SEPIC driving a string of v_string volts at i_led."""
    p = v_string * i_led / EFF_SEPIC + vin * IQ_TPS
    p += vin * (I_XIAO_ON + I_RADAR + I_POT_G1 + I_CHG_LED + I_R13 + I_EN_PD)
    i = p / vin
    p += i**2 * R_IN
    return p, p / vin


def g2_idle(keepalive=True, vin=5.0, wake=None):
    """Dark (switch ON, radar watching). wake=False drops the 10 s wake used only for the pulse."""
    wake = keepalive if wake is None else wake
    i = I_XIAO_SLEEP + I_RADAR + I_POT_G1 + ISD_TPS + I_CHG_LED + I_R13
    if wake:
        i += I_WAKE * T_WAKE / T_PERIOD
    if keepalive:
        i += vin / R_KA * KA_DUTY
    return vin * i, i


def g2_report():
    gi, gii = g2_idle()
    gi0, gii0 = g2_idle(keepalive=False)
    print("\n== Rev G2 (SEPIC %.0f %%, flat estimate)" % (EFF_SEPIC * 100))
    print(" idle %.2f mA with keep-alive, %.2f mA without; switched off: 0" % (gii * 1e3, gii0 * 1e3))
    print(" %-40s %7s %7s %9s %9s %9s" % ("configuration", "LED W", "mA in", "20Ah 4h/d", "30Ah 4h/d", "20Ah cont"))
    for name, vs, i in [("one 12 V 600 mm @ 150 mA (= prototype)", VF_12V_150, 0.150),
                        ("one 12 V 600 mm @ 244 mA", VF_12V_244, 0.244),
                        ("2 x 3 V 300 mm @ 244 mA", 2 * VF_3V_244, 0.244),
                        ("4 x 3 V 300 mm @ 150 mA", 4 * VF_3V_150, 0.150),
                        ("4 x 3 V 300 mm @ 244 mA", 4 * VF_3V_244, 0.244),
                        ("5 W cap (500 mA setting)", 5.0 / 0.42, 0.42)]:
        p, ii = g2_lit(vs, i)
        print(" %-40s %7.2f %7.0f %8.1f d %8.1f d %7.1f h" % (name, vs * i, ii * 1e3, runtime(20000, p, gi, 4),
              runtime(30000, p, gi, 4), bank_wh(20000) / p))


if __name__ == "__main__":
    print("== AL8860 channel at 303 mA, VF = %.2f V" % VF)
    print(" VIN    f(kHz)  D     ton(us)  Pin(mW)  eff    losses rs/rl/sw/diode/swt/q (mW)")
    for vin in (4.5, 5.0, 5.25, 9.0):
        r = al8860(vin)
        pr = "/".join("%.0f" % (1e3 * x) for x in r["parts"].values())
        print(" %4.2f   %5.0f   %.2f  %5.2f    %6.0f   %.1f%%  %s"
              % (vin, r["f"] / 1e3, r["d"], r["ton"] * 1e6, r["p_in"] * 1e3,
                 100 * r["eff"], pr))
    print("\n== Load seen by the bank (keep-alive threshold check)")
    print(" level   G1 analog (mA)   Rev F PWM duty (mA)")
    for lv in (1.0, 0.5, 0.25, 0.10, 0.05):
        print(" %4.0f%%   %6.0f           %6.0f"
              % (100 * lv, g1_lit(lv)[1] * 1e3, revf_lit(lv)[1] * 1e3))
    pg, ig = g1_lit()
    pf, i_f = revf_lit()
    gi, gii = g1_idle()
    gi0, gii0 = g1_idle(keepalive=False)
    fi, fii = revf_idle()
    print("\n== Totals at 5 V")
    print(" G1   lit %.2f W (%.0f mA)   idle %.2f mA (%.2f mA without keep-alive)"
          % (pg, ig * 1e3, gii * 1e3, gii0 * 1e3))
    print(" RevF lit %.2f W (%.0f mA)   idle %.2f mA" % (pf, i_f * 1e3, fii * 1e3))
    print("\n== Runtime (bank %.0f%% usable at %.1f V)" % (BANK_EFF * 100, V_CELL))
    print(" bank     G1 cont.  G1 4h/day  G1 8h/day  RevF cont.  RevF 4h/day")
    for mah in (20000, 25000, 30000):
        print(" %5d    %5.1f h   %4.1f d     %4.1f d     %5.1f h     %4.1f d"
              % (mah, bank_wh(mah) / pg, runtime(mah, pg, gi, 4),
                 runtime(mah, pg, gi, 8), bank_wh(mah) / pf,
                 runtime(mah, pf, fi, 4)))
    g2_report()
    led = 2e-3
    INPUTS["I_CHG_LED"] = led; globals()["I_CHG_LED"] = led
    pg2, _ = g1_lit(); gi2, gii2 = g1_idle()
    print("\n== Sensitivity: XIAO charge LED drawing %.0f mA continuously" % (led * 1e3))
    print(" G1 idle %.2f mA; 20 Ah at 4 h/day: %.1f d (vs %.1f d)"
          % (gii2 * 1e3, runtime(20000, pg2, gi2, 4), runtime(20000, pg, gi, 4)))
