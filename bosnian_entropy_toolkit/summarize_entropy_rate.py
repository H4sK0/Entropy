
#!/usr/bin/env python3
"""Summarize asymptotic entropy rate using largest n per (file,genre,mode).

Ulaz: entropy_*_stats.csv
Izlaz: po jedan red za svaku kombinaciju (file, genre, mode) sa:
    n_max, entropy_bits (H(n_max)), entropy_per_unit = H(n_max)/n_max
"""
import argparse
import csv
from collections import defaultdict

def main():
    ap = argparse.ArgumentParser(
        description="Summarize asymptotic entropy rate using largest n per (file,genre,mode)."
    )
    ap.add_argument("--input", required=True,
                    help="Ulazni CSV (entropy_*_stats.csv)")
    ap.add_argument("--output", required=True,
                    help="Izlazni CSV sa jednim redom po (file,genre,mode)")
    args = ap.parse_args()

    groups = defaultdict(list)
    with open(args.input, "r", encoding="utf-8", newline="") as fin:
        reader = csv.DictReader(fin)
        for row in reader:
            try:
                key = (row["file"], row["genre"], row["mode"])
            except KeyError:
                continue
            try:
                row_n = int(row["n"])
                row_H = float(row["entropy_bits"])
            except (KeyError, ValueError):
                continue
            row["n"] = row_n
            row["entropy_bits"] = row_H
            groups[key].append(row)

    with open(args.output, "w", encoding="utf-8", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerow(["file","genre","mode","n_max","entropy_bits","entropy_per_unit"])
        for (file_, genre, mode), rows in groups.items():
            rows.sort(key=lambda r: r["n"])
            last = rows[-1]
            n_max = last["n"]
            Hn = last["entropy_bits"]
            h_n = Hn / n_max if n_max > 0 else 0.0
            writer.writerow([
                file_, genre, mode,
                n_max,
                f"{Hn:.10f}",
                f"{h_n:.10f}",
            ])

if __name__ == "__main__":
    main()
