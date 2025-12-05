
#!/usr/bin/env python3
"""Compute energy-like measures from entropy stats CSV.

Ulaz: entropy_*_stats.csv (chars ili words).
Koristi sum_c_log2c, sum_c_sqrt, sum_c2 i num_tokens da izračuna:
    E1_sum_c_log2c, E05_sum_c_sqrt, E2_sum_c2
    E1_per_token, E05_per_token, E2_per_token
"""
import argparse
import csv

def main():
    ap = argparse.ArgumentParser(
        description="Compute energy-like measures from entropy stats CSV."
    )
    ap.add_argument("--input", required=True,
                    help="Ulazni CSV (entropy_*_stats.csv)")
    ap.add_argument("--output", required=True,
                    help="Izlazni CSV sa energijskim mjerama")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8", newline="") as fin,              open(args.output, "w", encoding="utf-8", newline="") as fout:

        reader = csv.DictReader(fin)
        base_fields = reader.fieldnames or []
        fieldnames = list(base_fields) + [
            "E1_sum_c_log2c",
            "E05_sum_c_sqrt",
            "E2_sum_c2",
            "E1_per_token",
            "E05_per_token",
            "E2_per_token",
        ]
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            try:
                T = float(row["num_tokens"])
                S1 = float(row["sum_c_log2c"])
                S05 = float(row["sum_c_sqrt"])
                S2 = float(row["sum_c2"])
            except (KeyError, ValueError):
                continue

            E1 = S1
            E05 = S05
            E2 = S2

            if T > 0:
                E1_pt = E1 / T
                E05_pt = E05 / T
                E2_pt = E2 / T
            else:
                E1_pt = E05_pt = E2_pt = 0.0

            row_out = dict(row)
            row_out["E1_sum_c_log2c"] = f"{E1:.10f}"
            row_out["E05_sum_c_sqrt"] = f"{E05:.10f}"
            row_out["E2_sum_c2"] = f"{E2:.10f}"
            row_out["E1_per_token"] = f"{E1_pt:.10f}"
            row_out["E05_per_token"] = f"{E05_pt:.10f}"
            row_out["E2_per_token"] = f"{E2_pt:.10f}"
            writer.writerow(row_out)

if __name__ == "__main__":
    main()
