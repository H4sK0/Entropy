
#!/usr/bin/env python3
"""Compute basic Zipf data from unigram counts.

Ulazni CSV: gram,count  (iz collect_unigram_counts.py)
Izlazni CSV:
    rank,gram,count,rel_freq

Ovaj izlaz se može koristiti za Zipf graf (log(rank) vs log(freq)).
"""
import argparse
import csv
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(
        description="Compute Zipf rank/frequency table from unigram counts."
    )
    ap.add_argument("--input", required=True, type=Path,
                    help="Ulazni CSV (gram,count)")
    ap.add_argument("--output", required=True, type=Path,
                    help="Izlazni CSV (rank,gram,count,rel_freq)")
    args = ap.parse_args()

    grams = []
    total = 0
    with args.input.open("r", encoding="utf-8", newline="") as fin:
        reader = csv.DictReader(fin)
        if reader.fieldnames is None or "gram" not in reader.fieldnames or "count" not in reader.fieldnames:
            raise SystemExit("Ulazni CSV mora imati kolone 'gram' i 'count'.")
        for row in reader:
            try:
                c = int(row["count"])
            except ValueError:
                continue
            g = row["gram"]
            grams.append((g, c))
            total += c

    grams.sort(key=lambda x: x[1], reverse=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as fout:
        w = csv.writer(fout)
        w.writerow(["rank","gram","count","rel_freq"])
        rank = 1
        for g, c in grams:
            rel = c / total if total > 0 else 0.0
            w.writerow([rank, g, c, f"{rel:.12g}"])
            rank += 1

if __name__ == "__main__":
    main()
