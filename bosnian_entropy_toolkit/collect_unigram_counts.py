
#!/usr/bin/env python3
"""Collect unigram counts (n=1) iz parts_* direktorija u jedan CSV.

Ovo je pomoćna skripta za:
  - informacijski sadržaj pojedinačnih jedinica
  - Zipf-ovu distribuciju
  - Heaps-ov zakon (ako imaš više podkorpusa)

Pretpostavlja izlaz ent.py map faze:
  fajlovi oblika: {mode}_n01_b####_part#####.csv[.gz]

Izlaz: CSV sa kolonama:
  gram,count

PAŽNJA: za ogromne korpuse broj unigrama može biti vrlo velik.
Koristi ovo prvenstveno za:
  - chars, n=1
  - words, n=1
"""
import argparse
import csv
import gzip
from collections import Counter
from pathlib import Path

def open_maybe_gzip(path: Path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return open(path, "r", encoding="utf-8", newline="")

def main():
    ap = argparse.ArgumentParser(
        description="Collect unigram counts (n=1) iz parts_* direktorija u jedan CSV."
    )
    ap.add_argument("--parts-dir", required=True, type=Path,
                    help="Direktorij sa part fajlovima (npr. ./parts_chars ili ./parts_words)")
    ap.add_argument("--mode", required=True, choices=["chars","words"],
                    help="Mode (chars ili words), mora odgovarati prefiksu fajlova")
    ap.add_argument("--output", required=True, type=Path,
                    help="Izlazni CSV sa kolonama gram,count")
    args = ap.parse_args()

    parts_dir = args.parts_dir
    mode = args.mode

    # Uzimamo samo n=1 part fajlove
    patterns = [
        f"{mode}_n01_b????_part*.csv.gz",
        f"{mode}_n01_b????_part*.csv",
    ]
    files = []
    for pat in patterns:
        files.extend(parts_dir.glob(pat))

    if not files:
        raise SystemExit(f"Nema fajlova za {mode} n=1 u {parts_dir}")

    agg = Counter()
    for fn in sorted(files):
        with open_maybe_gzip(fn) as f:
            r = csv.reader(f)
            for row in r:
                if len(row) != 2:
                    continue
                gram, c = row
                try:
                    c = int(c)
                except ValueError:
                    continue
                agg[gram] += c

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as fout:
        w = csv.writer(fout)
        w.writerow(["gram","count"])
        for gram, c in agg.most_common():
            w.writerow([gram, c])

if __name__ == "__main__":
    main()
