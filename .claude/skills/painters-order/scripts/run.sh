#!/usr/bin/env bash
# Painter's Order: tessellation SVG -> oscilloscope comma-pump chorale (film + soundtrack + web tile organ).
#
#   run.sh <tessellation.svg> <outdir> [shards]
#
# Environment (all optional):
#   PO_PREVIEW=1     analysis + soundtrack + contact sheet only (about a minute); skip the full film
#   PO_CYCLES=6      rounds of the comma pump (each sinks home by 81/80, about 21.5 cents; ~6.4 s each)
#   PO_CHORD_DUR=1.6 seconds per chord
#   PO_CREF=130.81   frequency of the opening C, in Hz
#   PO_TITLE / PO_SUBTITLE   text for the title card (and the organ page)
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
[ $# -ge 2 ] || { sed -n 2,13p "$0"; exit 2; }
export PO_SVG=$(realpath "$1") PYTHONPATH="$HERE${PYTHONPATH:+:$PYTHONPATH}"
B=$2; N=${3:-$(nproc)}
mkdir -p "$B/web"; : > "$B/timings.txt"
SECONDS=0; stamp() { echo "$1 ${SECONDS}s" | tee -a "$B/timings.txt"; }
python -m po_kit.tess | tee "$B/analysis.txt";        stamp analysis
python -m po_kit.audio "$B";                          stamp soundtrack
python -m po_kit.web "$B/score.json" "$B/web/organ_data.js"
cp "$HERE/../assets/organ.html" "$B/web/index.html";          stamp organ
python -m po_kit.film "$B" sheet;                     stamp sheet
if [ "${PO_PREVIEW:-0}" = 1 ]; then echo "preview done: $B/sheet.png, $B/score.wav, $B/web/index.html"; exit 0; fi
for i in $(seq 0 $((N-1))); do python -m po_kit.film "$B" "$i" "$N" & done
wait;                                                         stamp frames
python -m po_kit.assemble "$B";                       stamp film
