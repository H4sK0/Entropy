
#!/usr/bin/env python3
"""Compute effective entropy rate h(n) = H(n)/n from entropy stats CSV.

Ulazni CSV treba da bude izlaz ent.py skripte (entropy_*_stats.csv) sa kolonama:
    file,genre,mode,n,num_tokens,num_types,entropy_bits,sum_c_log2c,sum_c_sqrt,sum_c2,c_max

Skripta dodaje kolonu:
    entropy_per_unit  (H(n)/n)
"""
import argparse
import csv

def main():
    ap = argparse.ArgumentParser(
        description="Compute effective entropy rate h(n) = H(n)/n from entropy stats CSV."
    )
    ap.add_argument("--input", required=True,
                    help="Ulazni CSV (npr. entropy_chars_stats.csv)")
    ap.add_argument("--output", required=True,
                    help="Izlazni CSV sa dodatnom kolonom entropy_per_unit")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8", newline="") as fin,              open(args.output, "w", encoding="utf-8", newline="") as fout:

        reader = csv.DictReader(fin)
        fieldnames = list(reader.fieldnames) + ["entropy_per_unit"]
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            try:
                n = int(row["n"])
                Hn = float(row["entropy_bits"])
            except (KeyError, ValueError):
                # Preskoči nevalidne redove
                continue
            h_n = Hn / n if n > 0 else 0.0
            row["entropy_per_unit"] = f"{h_n:.10f}"
            writer.writerow(row)

if __name__ == "__main__":
    main()
