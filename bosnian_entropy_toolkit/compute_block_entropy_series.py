
#!/usr/bin/env python3
"""Compute block entropy series and finite differences (higher-structure view).

Ulaz: entropy_*_stats.csv
Izlaz: CSV sa:
    file,genre,mode,n,Hn,Hn_over_n,delta_H,delta2_H

gdje je:
    Hn        = entropy_bits
    Hn_over_n = H(n)/n
    delta_H   = H(n) - H(n-1)
    delta2_H  = (H(n) - H(n-1)) - (H(n-1) - H(n-2))

Ovo daje pregled rasta blok-entropije i zakrivljenosti (informacija o višim strukturama).
"""
import argparse
import csv
from collections import defaultdict

def main():
    ap = argparse.ArgumentParser(
        description="Compute block entropy series and finite differences."
    )
    ap.add_argument("--input", required=True,
                    help="Ulazni CSV (entropy_*_stats.csv)")
    ap.add_argument("--output", required=True,
                    help="Izlazni CSV za seriju H(n)")
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
                n = int(row["n"])
                Hn = float(row["entropy_bits"])
            except (KeyError, ValueError):
                continue
            row["n"] = n
            row["entropy_bits"] = Hn
            groups[key].append(row)

    with open(args.output, "w", encoding="utf-8", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerow([
            "file","genre","mode","n",
            "Hn","Hn_over_n","delta_H","delta2_H"
        ])
        for (file_, genre, mode), rows in groups.items():
            rows.sort(key=lambda r: r["n"])
            prev_H = None
            prev_delta = None
            for row in rows:
                n = row["n"]
                Hn = row["entropy_bits"]
                Hn_over_n = Hn / n if n > 0 else 0.0
                if prev_H is None:
                    delta_H = ""
                    delta2_H = ""
                else:
                    delta_H = Hn - prev_H
                    if prev_delta is None:
                        delta2_H = ""
                    else:
                        delta2_H = delta_H - prev_delta
                writer.writerow([
                    file_, genre, mode, n,
                    f"{Hn:.10f}",
                    f"{Hn_over_n:.10f}",
                    "" if delta_H == "" else f"{delta_H:.10f}",
                    "" if delta2_H == "" else f"{delta2_H:.10f}",
                ])
                if prev_H is None:
                    prev_H = Hn
                    prev_delta = None
                else:
                    prev_delta = (Hn - prev_H)
                    prev_H = Hn

if __name__ == "__main__":
    main()
