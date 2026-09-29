#!/usr/bin/env bash
# Paralelni reduce za karakterske n-grame (n = 1..8), jedan proces po n,
# pa spajanje u jedan entropy_chars_stats.csv.
#
# Upotreba:
#   ./run_reduce_chars_parallel.sh [PARTS_DIR] [OUT_CSV] [TAG_FILE] [TAG_GENRE]
# Primjer:
#   ./run_reduce_chars_parallel.sh ./parts_chars ./entropy_chars_stats.csv bosnian_corpus_all.txt all
#
# PAŽNJA: svaki reduce drži jedan bucket u RAM-u; za n = 7, 8 to može biti nekoliko GB
# po procesu. Ako nemaš dovoljno memorije, smanji paralelizam (MAX_JOBS=2 ./run_...).
set -euo pipefail

PARTS_DIR="${1:-./parts_chars}"
OUT_CSV="${2:-./entropy_chars_stats.csv}"
TAG_FILE="${3:-bosnian_corpus_all.txt}"
TAG_GENRE="${4:-all}"
BUCKETS="${BUCKETS:-64}"
MAX_JOBS="${MAX_JOBS:-8}"
NS="${NS:-1 2 3 4 5 6 7 8}"
PY="${PYTHON:-python3}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

for N in $NS; do
  while [ "$(jobs -rp | wc -l)" -ge "$MAX_JOBS" ]; do sleep 1; done
  echo "reduce n=$N ..."
  "$PY" "$SCRIPT_DIR/ent.py" reduce \
    --parts-dir "$PARTS_DIR" --mode chars --n "$N" --buckets "$BUCKETS" \
    --out "$TMP_DIR/n${N}.csv" --tag-file "$TAG_FILE" --tag-genre "$TAG_GENRE" &
done
wait

first=1
for N in $NS; do
  if [ $first -eq 1 ]; then cat "$TMP_DIR/n${N}.csv" > "$OUT_CSV"; first=0
  else tail -n +2 "$TMP_DIR/n${N}.csv" >> "$OUT_CSV"; fi
done
echo "Gotovo: $OUT_CSV"
