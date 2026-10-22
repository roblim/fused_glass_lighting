#!/bin/sh
# Export, check and document both KiCad projects.
#
#   G1:    the KiCad 9 schematic is the source of truth (since 2026-10-15). This exports
#          its netlist and PDF, runs ERC where kicad-cli supports it (KiCad 8+), verifies the
#          netlist against g1_expected.py and rewrites the BOMs. It never regenerates G1.
#   Rev F: documentation only; regenerated from gen_rev_f.py, then verified.
#
# kicad-cli: KiCad.app on macOS if present, otherwise kicad-cli on PATH. Override with KICAD_CLI.
set -e
T="$(cd "$(dirname "$0")" && pwd)"
cd "$T"
MAC_CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
if [ -z "$KICAD_CLI" ]; then
  if [ -x "$MAC_CLI" ]; then KICAD_CLI="$MAC_CLI"; else KICAD_CLI=kicad-cli; fi
fi

G="$T/../kicad/fgl_g1"
"$KICAD_CLI" sch export netlist -o "$G/fgl_g1.net" "$G/fgl_g1.kicad_sch" >/dev/null
"$KICAD_CLI" sch export pdf -o "$G/fgl_g1.pdf" "$G/fgl_g1.kicad_sch" >/dev/null
if "$KICAD_CLI" sch --help 2>/dev/null | grep -q " erc"; then
  "$KICAD_CLI" sch erc --severity-all -o "$G/ERC.rpt" "$G/fgl_g1.kicad_sch" >/dev/null || true
  tail -1 "$G/ERC.rpt"
else
  echo "ERC skipped: this kicad-cli has no erc command (KiCad 8 or later needed)"
fi
python3 verify_netlist.py "$G/fgl_g1.net" g1_expected "$G/fgl_g1.kicad_sch" "$G" | tee "$G/verification.txt"
python3 make_bom.py "$G/fgl_g1.net" "$G"

python3 gen_rev_f.py
F="$T/../kicad/fgl_rev_f"
"$KICAD_CLI" sch export netlist -o "$F/fgl_rev_f.net" "$F/fgl_rev_f.kicad_sch" >/dev/null
"$KICAD_CLI" sch export pdf -o "$F/fgl_rev_f.pdf" "$F/fgl_rev_f.kicad_sch" >/dev/null
python3 verify_netlist.py "$F/fgl_rev_f.net" rev_f_expected "$F/fgl_rev_f.kicad_sch" "$F" | tee "$F/verification.txt"
