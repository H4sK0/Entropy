
#!/usr/bin/env python3
"""Compute information content for individual units (unigrams).

Ulazni CSV: rezultat collect_unigram_counts.py:
    gram,count

Izlazni CSV:
    gram,count,prob,info_bits

gdje je:
    prob = count / sum(count)
    info_bits = -log2(prob)
"""
import argparse
import csv
import math
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(
        description="Compute information content for individual unigrams."
    )
    ap.add_argument("--input", required=True, type=Path,
                    help="Ulazni CSV (gram,count)")
    ap.add_argument("--output", required=True, type=Path,
                    help="Izlazni CSV (gram,count,prob,info_bits)")
    args = ap.parse_args()

    # Prvo učitaj sve u memoriju
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

    if total == 0:
        raise SystemExit("Ukupan zbroj frekvencija je 0, nema podataka.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as fout:
        w = csv.writer(fout)
        w.writerow(["gram","count","prob","info_bits"])
        for g, c in grams:
            p = c / total
            if p > 0.0:
                info = -math.log2(p)
            else:
                info = 0.0
            w.writerow([g, c, f"{p:.12g}", f"{info:.10f}"])

if __name__ == "__main__":
    main()
