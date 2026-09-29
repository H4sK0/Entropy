#!/usr/bin/env python3
"""Redundancy for character-based entropy stats.

Ulaz: entropy_chars_stats.csv (redovi sa mode == "chars").

    C          = log2(|A|)                          (maksimalna entropija alfabeta)
    h_block(n) = H(n)/n
    h_cond(n)  = H(n) - H(n-1)                      (n = 1: H(1))
    redundancy = 1 - h(n)/C                         (h prema --rate, default: conditional)

|A| se zadaje sa --alphabet-size. Mora odgovarati inventaru nad kojim je računat H:
ako ulazni stats uključuju sve Unicode znakove (npr. 2932 tipa), a |A| = 30, redundansa
nije interpretabilna. Preporuka: računati redundansu nad letters-only brojanjem
(ent.py map --letters-only) i navesti |A| eksplicitno u radu.

Po defaultu se koristi conditional (brže konvergira); --rate block daje staru definiciju.
"""
import argparse
import csv
import math
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser(description="Character redundancy from entropy stats.")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--alphabet-size", type=int, required=True,
                    help="Efektivna veličina alfabeta |A| (npr. 30 za bosansku latinicu)")
    ap.add_argument("--rate", choices=["conditional", "block"], default="conditional")
    args = ap.parse_args()

    C = math.log2(args.alphabet_size)
    groups = defaultdict(list)
    with open(args.input, "r", encoding="utf-8", newline="") as fin:
        reader = csv.DictReader(fin)
        base_fields = reader.fieldnames or []
        for row in reader:
            if row.get("mode") != "chars":
                continue
            try:
                row["_n"] = int(row["n"])
                row["_H"] = float(row["entropy_bits"])
            except (KeyError, ValueError):
                continue
            groups[(row["file"], row["genre"])].append(row)

    fields = list(base_fields) + ["alphabet_size", "max_entropy_bits",
                                  "h_block", "h_conditional", "rate_used", "redundancy"]
    with open(args.output, "w", encoding="utf-8", newline="") as fout:
        w = csv.DictWriter(fout, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for rows in groups.values():
            rows.sort(key=lambda r: r["_n"])
            byn = {r["_n"]: r["_H"] for r in rows}
            for r in rows:
                n, H = r["_n"], r["_H"]
                hb = H / n
                hc = H - byn[n - 1] if (n - 1) in byn else (H if n == 1 else float("nan"))
                h = hc if args.rate == "conditional" else hb
                out = {k: v for k, v in r.items() if not k.startswith("_")}
                out.update({
                    "alphabet_size": args.alphabet_size,
                    "max_entropy_bits": f"{C:.10f}",
                    "h_block": f"{hb:.10f}",
                    "h_conditional": "" if math.isnan(hc) else f"{hc:.10f}",
                    "rate_used": args.rate,
                    "redundancy": "" if math.isnan(h) else f"{1.0 - h / C:.10f}",
                })
                w.writerow(out)


if __name__ == "__main__":
    main()
