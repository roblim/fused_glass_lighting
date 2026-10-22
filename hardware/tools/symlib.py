"""Project symbol library (fgl.kicad_sym): parts KiCad's libraries don't have."""


def _pin(etype, x, y, ang, name, num, length=2.54):
    return ('(pin %s line (at %s %s %d) (length %s) (name "%s" (effects (font (size 1.27 1.27)))) '
            '(number "%s" (effects (font (size 1.27 1.27)))))' % (etype, x, y, ang, length, name, num))


def _sym(name, ref, value, body, pins, fp="", ds="", desc="", hide_pin_numbers=False):
    pn = " (pin_numbers hide)" if hide_pin_numbers else ""
    return ('(symbol "%s"%s (pin_names (offset 1.016)) (in_bom yes) (on_board yes)\n'
            '  (property "Reference" "%s" (at 0 0 0) (effects (font (size 1.27 1.27))))\n'
            '  (property "Value" "%s" (at 0 0 0) (effects (font (size 1.27 1.27))))\n'
            '  (property "Footprint" "%s" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
            '  (property "Datasheet" "%s" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
            '  (property "ki_description" "%s" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
            '  (symbol "%s_0_1" %s)\n'
            '  (symbol "%s_1_1" %s)\n)'
            % (name, pn, ref, value, fp, ds, desc, name, body, name, " ".join(pins)))


def _rect(x1, y1, x2, y2):
    return ('(rectangle (start %s %s) (end %s %s) (stroke (width 0.254) (type default)) '
            '(fill (type background)))' % (x1, y1, x2, y2))


def xiao():
    left = [("1", "D0 GPIO2"), ("2", "D1 GPIO3 A1"), ("3", "D2 GPIO4 A2"), ("4", "D3 GPIO5"),
            ("5", "D4 GPIO6"), ("6", "D5 GPIO7"), ("7", "D6 GPIO21 TX")]
    right = [("8", "D7 GPIO20 RX"), ("9", "D8 GPIO8"), ("10", "D9 GPIO9 BOOT"), ("11", "D10 GPIO10")]
    pins = [_pin("bidirectional", -22.86, 7.62 - 2.54 * k, 0, n, p) for k, (p, n) in enumerate(left)]
    pins += [_pin("bidirectional", 22.86, 7.62 - 2.54 * k, 180, n, p) for k, (p, n) in enumerate(right)]
    pins += [_pin("power_in", -2.54, 13.97, 270, "5V", "14"),
             _pin("power_out", 2.54, 13.97, 270, "3V3", "12"),
             _pin("power_in", 0, -12.7, 90, "GND", "13")]
    return _sym("XIAO_ESP32C3", "U", "XIAO_ESP32C3", _rect(-20.32, 11.43, 20.32, -10.16), pins,
                fp="fgl:XIAO_ESP32C3_Castellated",
                ds="https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/",
                desc="Seeed Studio XIAO ESP32C3. Pin numbers follow Seeed's footprint (1-14).")


def ld1500sb():
    pins = [_pin("power_in", -2.54, 10.16, 270, "IN+", "1"),
            _pin("power_in", -2.54, -10.16, 90, "IN-", "2"),
            _pin("input", -10.16, 0, 0, "EN", "3"),
            _pin("power_out", 10.16, 2.54, 180, "L+", "4"),
            _pin("passive", 10.16, -2.54, 180, "L-", "5")]
    return _sym("LD1500SB_Module", "M", "LD1500SB", _rect(-7.62, 7.62, 7.62, -7.62), pins,
                ds="https://www.amazon.com/dp/B0F1K97V61",
                desc="LD1500SB CC LED driver module: CN5711 linear sink, 1k + 47k trimmer sets current. L+ is IN+.")


def pd_trigger():
    pins = [_pin("power_out", 0, 10.16, 270, "OUT+", "1"),
            _pin("passive", 0, -10.16, 90, "OUT-", "2")]
    return _sym("PD_Trigger_Module", "M", "PD trigger", _rect(-7.62, 7.62, 7.62, -7.62), pins,
                ds="https://www.amazon.com/dp/B0D7CFSCP6",
                desc="AITRIP USB-C PD trigger module, set to 5 V and button-locked")


def ld2410s():
    pins = [_pin("power_in", 2.54, 10.16, 270, "3V3", "1"),
            _pin("power_in", 2.54, -10.16, 90, "GND", "2"),
            _pin("output", -10.16, 0, 0, "OT1/TX", "3"),
            _pin("input", -10.16, -2.54, 0, "RX", "4"),
            _pin("output", -10.16, -5.08, 0, "OT2", "5")]
    return _sym("HLK-LD2410S", "M", "HLK-LD2410S", _rect(-7.62, 7.62, 7.62, -7.62), pins,
                ds="https://www.tinytronics.nl/product_files/006002_HLK-LD2410S%20serial%20communication%20protocol-V1.00.pdf",
                desc="Hi-Link LD2410S 24 GHz presence radar, 3.0-3.6 V. J2 header: 3V3 GND OT1/TX RX OT2")


def conn_radar():
    """5-pin JST-PH to the LD2410S, 1:1 with its header. Power pins drawn top/bottom."""
    pins = [_pin("passive", 5.08, 7.62, 270, "3V3", "1"),
            _pin("passive", 5.08, -7.62, 90, "GND", "2"),
            _pin("passive", -7.62, 2.54, 0, "OT1/TX", "3"),
            _pin("passive", -7.62, 0, 0, "RX", "4"),
            _pin("passive", -7.62, -2.54, 0, "OT2", "5")]
    return _sym("Conn_LD2410S", "J", "LD2410S", _rect(-5.08, 5.08, 7.62, -5.08), pins,
                fp="Connector_JST:JST_PH_S5B-PH-K_1x05_P2.00mm_Horizontal",
                desc="5-pin header to the HLK-LD2410S: 1 3V3, 2 GND, 3 OT1/TX, 4 RX, 5 OT2")


def conn_pot():
    pins = [_pin("passive", -7.62, 2.54, 0, "CW", "1"),
            _pin("passive", -7.62, 0, 0, "W", "2"),
            _pin("passive", 2.54, -7.62, 90, "CCW", "3")]
    return _sym("Conn_Pot", "J", "POT", _rect(-5.08, 5.08, 5.08, -5.08), pins,
                fp="Connector_JST:JST_PH_S3B-PH-K_1x03_P2.00mm_Horizontal",
                desc="3-pin header to the brightness pot: 1 CW end, 2 wiper, 3 CCW end")


def write(path, which=("xiao", "ld1500sb", "pd_trigger", "ld2410s")):
    fns = dict(xiao=xiao, ld1500sb=ld1500sb, pd_trigger=pd_trigger, ld2410s=ld2410s,
               conn_radar=conn_radar, conn_pot=conn_pot)
    body = "\n".join(fns[w]() for w in which)
    open(path, "w").write('(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)\n%s\n)\n' % body)
