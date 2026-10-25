#!/bin/sh
# Export, check and document the KiCad projects.
#
#   G2:    current board. Exports its netlist and PDF, runs ERC (KiCad 8+), verifies the netlist
#          and the PCB pad nets against g2_expected.py, runs DRC and rewrites the BOMs. It never regenerates G2: once the
#          schematic is saved in KiCad 9 that file is the master (see hardware/README.md).
#   G1:    superseded 2026-10-23, frozen; same checks against g1_expected.py.
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

check() {   # check <project> <expected module> <make_bom expected arg or empty>
  P="$T/../kicad/$1"
  "$KICAD_CLI" sch export netlist -o "$P/$1.net" "$P/$1.kicad_sch" >/dev/null
  "$KICAD_CLI" sch export pdf -o "$P/$1.pdf" "$P/$1.kicad_sch" >/dev/null
  if "$KICAD_CLI" sch --help 2>/dev/null | grep -q " erc"; then
    "$KICAD_CLI" sch erc --severity-all -o "$P/ERC.rpt" "$P/$1.kicad_sch" >/dev/null || true
    tail -1 "$P/ERC.rpt"
  else
    echo "ERC skipped: this kicad-cli has no erc command (KiCad 8 or later needed)"
  fi
  python3 verify_netlist.py "$P/$1.net" "$2" "$P/$1.kicad_sch" "$P" | tee "$P/verification.txt"
  python3 make_bom.py "$P/$1.net" "$P" $3
}

check fgl_g2 g2_expected g2_expected
# G2 board: pad nets against the same design intent, then DRC (KiCad 9; zones must already be filled)
G2="$T/../kicad/fgl_g2"
python3 verify_pcb.py "$G2/fgl_g2.kicad_pcb" g2_expected | tee -a "$G2/verification.txt"
if "$KICAD_CLI" pcb --help 2>/dev/null | grep -q " drc"; then
  "$KICAD_CLI" pcb drc --severity-all --schematic-parity -o "$G2/DRC.rpt" "$G2/fgl_g2.kicad_pcb" >/dev/null || true
  grep "^\*\* Found" "$G2/DRC.rpt"
fi
check fgl_g1 g1_expected ""

python3 gen_rev_f.py
F="$T/../kicad/fgl_rev_f"
"$KICAD_CLI" sch export netlist -o "$F/fgl_rev_f.net" "$F/fgl_rev_f.kicad_sch" >/dev/null
"$KICAD_CLI" sch export pdf -o "$F/fgl_rev_f.pdf" "$F/fgl_rev_f.kicad_sch" >/dev/null
python3 verify_netlist.py "$F/fgl_rev_f.net" rev_f_expected "$F/fgl_rev_f.kicad_sch" "$F" | tee "$F/verification.txt"
