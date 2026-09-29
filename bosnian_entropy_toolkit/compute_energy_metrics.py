#!/usr/bin/env python3
"""Compute distributional energy / concentration measures from entropy stats CSV.

Ulaz: entropy_*_stats.csv (izlaz `ent.py reduce`), sa kolonama
    num_tokens (T), num_types (V), entropy_bits, sum_c_log2c, sum_c_sqrt, sum_c2

Sve mjere se računaju egzaktno iz dovoljnih statistika (bez ponovnog čitanja korpusa):

    onicescu_energy  E   = sum p_i^2 = sum c_i^2 / T^2
    renyi2_bits      H2  = -log2(E)
    gini_simpson     G   = 1 - E
    hhi_normalized   HHI* = (E - 1/V) / (1 - 1/V)        (0 = uniformno, 1 = jedan tip)
    shannon_bits     H1  = log2(T) - sum c log2 c / T     (MLE / plug-in; = entropy_bits)
    renyi05_bits     H_1/2 = 2 * log2( sum sqrt(p_i) ) = 2 * log2( sum sqrt(c_i) / sqrt(T) )
    effective_types_H1 = 2^H1  (Hillov broj reda 1)
    effective_types_H2 = 1/E   (Hillov broj reda 2)

Stare kolone (E1_sum_c_log2c, E05_sum_c_sqrt, E2_sum_c2, *_per_token) zadržane su radi
kompatibilnosti sa ranijim izlazima. PAŽNJA: E2_per_token = sum c^2 / T NIJE Onicescu
energija; Onicescu energija je onicescu_energy = sum c^2 / T^2.

Sve vrijednosti su MLE (plug-in) procjene i za n-grame višeg reda (V/T blizu 1) su
pristrasne — vidi kolonu types_per_token.
"""
import argparse
import csv
import math


def main():
    ap = argparse.ArgumentParser(
        description="Compute Onicescu energy, Rényi-2, Gini–Simpson, HHI from entropy stats CSV."
    )
    ap.add_argument("--input", required=True, help="Ulazni CSV (entropy_*_stats.csv)")
    ap.add_argument("--output", required=True, help="Izlazni CSV sa energijskim mjerama")
    ap.add_argument("--no-legacy", action="store_true",
                    help="Ne ispisuj stare kolone E1_/E05_/E2_*")
    args = ap.parse_args()

    new_cols = [
        "onicescu_energy", "renyi2_bits", "gini_simpson", "hhi_normalized",
        "shannon_bits", "renyi05_bits", "effective_types_H1", "effective_types_H2",
        "types_per_token",
    ]
    legacy_cols = [
        "E1_sum_c_log2c", "E05_sum_c_sqrt", "E2_sum_c2",
        "E1_per_token", "E05_per_token", "E2_per_token",
    ]

    with open(args.input, "r", encoding="utf-8", newline="") as fin, \
         open(args.output, "w", encoding="utf-8", newline="") as fout:
        reader = csv.DictReader(fin)
        base_fields = reader.fieldnames or []
        fieldnames = list(base_fields) + new_cols + ([] if args.no_legacy else legacy_cols)
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            try:
                T = float(row["num_tokens"])
                V = float(row["num_types"])
                S1 = float(row["sum_c_log2c"])
                S05 = float(row["sum_c_sqrt"])
                S2 = float(row["sum_c2"])
            except (KeyError, ValueError):
                continue
            if T <= 0 or V <= 0:
                continue

            E = S2 / (T * T)
            H2 = -math.log2(E) if E > 0 else float("nan")
            G = 1.0 - E
            HHI = (E - 1.0 / V) / (1.0 - 1.0 / V) if V > 1 else 1.0
            H1 = math.log2(T) - S1 / T
            H05 = 2.0 * math.log2(S05 / math.sqrt(T)) if S05 > 0 else float("nan")

            out = dict(row)
            out.update({
                "onicescu_energy": f"{E:.12g}",
                "renyi2_bits": f"{H2:.10f}",
                "gini_simpson": f"{G:.12g}",
                "hhi_normalized": f"{HHI:.12g}",
                "shannon_bits": f"{H1:.10f}",
                "renyi05_bits": f"{H05:.10f}",
                "effective_types_H1": f"{2.0 ** H1:.6f}",
                "effective_types_H2": f"{1.0 / E:.6f}",
                "types_per_token": f"{V / T:.10f}",
            })
            if not args.no_legacy:
                out.update({
                    "E1_sum_c_log2c": f"{S1:.10f}",
                    "E05_sum_c_sqrt": f"{S05:.10f}",
                    "E2_sum_c2": f"{S2:.10f}",
                    "E1_per_token": f"{S1 / T:.10f}",
                    "E05_per_token": f"{S05 / T:.10f}",
                    "E2_per_token": f"{S2 / T:.10f}",
                })
            writer.writerow(out)


if __name__ == "__main__":
    main()
