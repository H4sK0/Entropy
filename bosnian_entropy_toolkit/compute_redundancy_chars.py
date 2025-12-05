
#!/usr/bin/env python3
"""Compute redundancy and predictability for character-based entropy stats.

Pretpostavka: ulaz je entropy_chars_stats.csv (mode == "chars").
Računa:
    h(n) = H(n)/n
    C = log2(|A|)
    redundancy = 1 - h(n)/C
    predictability = redundancy  (isti izraz, druga interpretacija)

|A| (efektivna veličina alfabeta) prosljeđuje se preko --alphabet-size.
"""
import argparse
import csv
import math

def main():
    ap = argparse.ArgumentParser(
        description="Compute redundancy and predictability for character-based entropy stats."
    )
    ap.add_argument("--input", required=True,
                    help="Ulazni CSV (entropy_chars_stats.csv)")
    ap.add_argument("--output", required=True,
                    help="Izlazni CSV sa redundancijom")
    ap.add_argument("--alphabet-size", type=int, required=True,
                    help="Efektivna veličina alfabeta |A| (npr. 32, 40...)")
    args = ap.parse_args()

    C = math.log2(args.alphabet_size)

    with open(args.input, "r", encoding="utf-8", newline="") as fin,              open(args.output, "w", encoding="utf-8", newline="") as fout:

        reader = csv.DictReader(fin)
        base_fields = reader.fieldnames or []
        fieldnames = list(base_fields) + [
            "entropy_per_char", "redundancy", "predictability"
        ]
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            if row.get("mode") != "chars":
                # Preskoči ako nije chars
                continue
            try:
                n = int(row["n"])
                Hn = float(row["entropy_bits"])
            except (KeyError, ValueError):
                continue
            h_n = Hn / n if n > 0 else 0.0
            R = 1.0 - (h_n / C) if C > 0 else 0.0
            P = R

            row_out = dict(row)
            row_out["entropy_per_char"] = f"{h_n:.10f}"
            row_out["redundancy"] = f"{R:.10f}"
            row_out["predictability"] = f"{P:.10f}"
            writer.writerow(row_out)

if __name__ == "__main__":
    main()
