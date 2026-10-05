#!/usr/bin/env bash
# Whole Painter's Order pipeline on one machine. Usage: painters_order/run_all.sh [builddir] [shards]
set -euo pipefail
B=${1:-build/painters_order}; N=${2:-$(nproc)}
SECONDS=0; stamp() { echo "$1 ${SECONDS}s" | tee -a "$B/timings.txt"; }
mkdir -p "$B"; : > "$B/timings.txt"
python -m painters_order.audio "$B";                 stamp score
for i in $(seq 0 $((N-1))); do python -m painters_order.film "$B" "$i" "$N" & done
wait;                                                stamp frames
python -m painters_order.film "$B" sheet;            stamp sheet
python -m painters_order.assemble "$B";              stamp assemble
