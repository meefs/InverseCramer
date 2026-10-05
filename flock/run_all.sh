#!/usr/bin/env bash
# Whole Flock pipeline on one machine. Usage: flock/run_all.sh [builddir] [shards]
set -euo pipefail
B=${1:-build/flock}; N=${2:-$(nproc)}
SECONDS=0; stamp() { echo "$1 ${SECONDS}s" | tee -a "$B/timings.txt"; }
mkdir -p "$B"; : > "$B/timings.txt"
python -m flock.still "$B";                    stamp still+qa
python -m flock.animate "$B" sheet;            stamp cues+sheet
for i in $(seq 0 $((N-1))); do python -m flock.animate "$B" "$i" "$N" & done
python -m flock.score "$B" &
wait;                                          stamp frames+score
python -m flock.assemble "$B";                 stamp assemble
python -m flock.html "$B";                     stamp html
