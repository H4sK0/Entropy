
#!/usr/bin/env python3
"""Compute conditional entropy H(n|n-1) from entropy stats CSV.

Ulazni CSV: entropy_*_stats.csv (iz ent.py)
Izlazni CSV: dodaje kolonu conditional_entropy = H(n) - H(n-1),
računato unutar svake grupe (file, genre, mode).
"""
import argparse
import csv
from collections import defaultdict

def main():
    ap = argparse.ArgumentParser(
        description="Compute conditional entropy H(n|n-1) from entropy stats CSV."
    )
    ap.add_argument("--input", required=True,
                    help="Ulazni CSV (entropy_*_stats.csv)")
    ap.add_argument("--output", required=True,
                    help="Izlazni CSV sa conditional_entropy kolonom")
    args = ap.parse_args()

    groups = defaultdict(list)
    with open(args.input, "r", encoding="utf-8", newline="") as fin:
        reader = csv.DictReader(fin)
        base_fields = reader.fieldnames or []
        for row in reader:
            try:
                key = (row["file"], row["genre"], row["mode"])
            except KeyError:
                continue
            try:
                row["n"] = int(row["n"])
                row["entropy_bits"] = float(row["entropy_bits"])
            except (KeyError, ValueError):
                continue
            groups[key].append(row)

    out_fields = list(base_fields) + ["conditional_entropy"]
    with open(args.output, "w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=out_fields)
        writer.writeheader()

        for key, rows in groups.items():
            rows.sort(key=lambda r: r["n"])
            prev_H = None
            for row in rows:
                n = row["n"]
                Hn = row["entropy_bits"]
                if prev_H is None:
                    cond = ""
                else:
                    cond = Hn - prev_H
                row_out = dict(row)
                row_out["n"] = str(n)
                row_out["entropy_bits"] = f"{Hn:.10f}"
                if cond == "":
                    row_out["conditional_entropy"] = ""
                else:
                    row_out["conditional_entropy"] = f"{cond:.10f}"
                writer.writerow(row_out)
                prev_H = Hn

if __name__ == "__main__":
    main()
