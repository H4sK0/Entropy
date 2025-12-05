
#!/usr/bin/env python3
"""Fit Heaps' law V(N) = k * N^beta na osnovu (num_tokens, num_types).

Ulazni CSV: izlaz ent.py (entropy_*_stats.csv) ili bilo koji CSV koji ima:
    num_tokens, num_types

Skripta:
  - čita sve redove
  - filtrira one gdje su num_tokens > 0 i num_types > 0
  - radi linearni fit u log-log prostoru:
        log V = log k + beta * log N
  - ispisuje k i beta i opcionalno upisuje prošireni CSV sa log vrijednostima.

Napomena:
  Heaps ima smisla kad imaš više tačaka (npr. različiti žanrovi, podkorpusi,
  ili snapshoti rasta korpusa).
"""
import argparse
import csv
import math
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(
        description="Fit Heaps' law V(N) = k * N^beta using (num_tokens, num_types)."
    )
    ap.add_argument("--input", required=True, type=Path,
                    help="Ulazni CSV (entropy_*_stats.csv ili slično)")
    ap.add_argument("--output", required=False, type=Path,
                    help="Opcioni izlazni CSV sa logN, logV i predikcijama")
    args = ap.parse_args()

    Ns = []
    Vs = []
    rows = []

    with args.input.open("r", encoding="utf-8", newline="") as fin:
        reader = csv.DictReader(fin)
        headers = reader.fieldnames or []
        for row in reader:
            try:
                N = float(row["num_tokens"])
                V = float(row["num_types"])
            except (KeyError, ValueError):
                continue
            if N <= 0 or V <= 0:
                continue
            Ns.append(N)
            Vs.append(V)
            rows.append(row)

    if len(Ns) < 2:
        raise SystemExit("Premalo tačaka za Heaps fit (treba bar 2).")

    # Linearni fit: logV = a + b * logN
    xs = [math.log(N) for N in Ns]
    ys = [math.log(V) for V in Vs]

    n = len(xs)
    sx = sum(xs)
    sy = sum(ys)
    sxx = sum(x*x for x in xs)
    sxy = sum(x*y for x, y in zip(xs, ys))

    denom = n*sxx - sx*sx
    if denom == 0:
        raise SystemExit("Degenerisan skup tačaka (denominator=0).")

    b = (n*sxy - sx*sy) / denom
    a = (sy - b*sx) / n

    beta = b
    k = math.exp(a)

    print(f"Heaps fit: V(N) = k * N^beta")
    print(f"  k    = {k:.6g}")
    print(f"  beta = {beta:.6g}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="") as fout:
            fieldnames = (headers or []) + [
                "log_num_tokens","log_num_types","heaps_V_pred"
            ]
            writer = csv.DictWriter(fout, fieldnames=fieldnames)
            writer.writeheader()
            for row, N, V in zip(rows, Ns, Vs):
                logN = math.log(N)
                logV = math.log(V)
                V_pred = k * (N ** beta)
                row_out = dict(row)
                row_out["log_num_tokens"] = f"{logN:.10f}"
                row_out["log_num_types"] = f"{logV:.10f}"
                row_out["heaps_V_pred"] = f"{V_pred:.10f}"
                writer.writerow(row_out)

if __name__ == "__main__":
    main()
