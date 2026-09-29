#!/usr/bin/env python3
"""Fit Heaps' law V(N) = k * N^beta na osnovu (num_tokens, num_types).

Heaps ima smisla SAMO za unigrame (n = 1) istog moda, mjerene na podkorpusima RAZLIČITE
veličine (npr. snapshoti rasta: 1 %, 2 %, 5 %, 10 %, ... 100 % korpusa).
Zato skripta po defaultu filtrira `n == 1` i zahtijeva `--mode`.

Ulaz (jedan od):
  (a) entropy_*_stats.csv (ili više spojenih) sa kolonama mode, n, num_tokens, num_types
  (b) bilo koji CSV sa kolonama num_tokens, num_types (bez mode/n) -> koristi --no-filter

Skripta odbija fit ako je raspon N premali (default: max(N)/min(N) < 10), jer je nagib
tada numerički nestabilan (npr. 8 žanrova po ~97 MB daje gotovo isti N).

Za pravljenje snapshota rasta koristi make_heaps_snapshots.py.
"""
import argparse
import csv
import math
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(
        description="Fit Heaps' law V(N) = k * N^beta using (num_tokens, num_types)."
    )
    ap.add_argument("--input", required=True, type=Path, nargs="+",
                    help="Jedan ili više ulaznih CSV fajlova")
    ap.add_argument("--mode", choices=["chars", "words"], default="words",
                    help="Koji mode uzeti (default: words)")
    ap.add_argument("--n", type=int, default=1, help="Red n-grama (default: 1)")
    ap.add_argument("--no-filter", action="store_true",
                    help="Ne filtriraj po mode/n (ulaz već sadrži samo odgovarajuće redove)")
    ap.add_argument("--min-range", type=float, default=10.0,
                    help="Minimalan odnos max(N)/min(N) za fit (default: 10)")
    ap.add_argument("--output", type=Path,
                    help="Opcioni izlazni CSV sa logN, logV i predikcijama")
    args = ap.parse_args()

    rows, Ns, Vs = [], [], []
    headers = []
    for path in args.input:
        with path.open("r", encoding="utf-8", newline="") as fin:
            reader = csv.DictReader(fin)
            for h in reader.fieldnames or []:
                if h not in headers:
                    headers.append(h)
            for row in reader:
                if not args.no_filter:
                    if row.get("mode") != args.mode:
                        continue
                    try:
                        if int(row.get("n", "")) != args.n:
                            continue
                    except ValueError:
                        continue
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

    if len(Ns) < 3:
        raise SystemExit(f"Premalo tačaka za Heaps fit: {len(Ns)} (treba bar 3).")
    ratio = max(Ns) / min(Ns)
    if ratio < args.min_range:
        raise SystemExit(
            f"Raspon N je premali za pouzdan fit: max/min = {ratio:.3g} < {args.min_range}. "
            "Napravi snapshote rasta korpusa (make_heaps_snapshots.py)."
        )

    xs = [math.log(N) for N in Ns]
    ys = [math.log(V) for V in Vs]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    syy = sum((y - my) ** 2 for y in ys)
    beta = sxy / sxx
    a = my - beta * mx
    k = math.exp(a)
    r2 = (sxy * sxy) / (sxx * syy) if syy > 0 else 1.0
    resid = [y - (a + beta * x) for x, y in zip(xs, ys)]
    se_beta = math.sqrt(sum(e * e for e in resid) / (n - 2) / sxx) if n > 2 else float("nan")

    print("Heaps fit: V(N) = k * N^beta")
    print(f"  points = {n}   N range = {min(Ns):.4g} .. {max(Ns):.4g}")
    print(f"  k      = {k:.6g}")
    print(f"  beta   = {beta:.6g}  (SE {se_beta:.3g})")
    print(f"  R^2    = {r2:.6f}")
    if not (0.0 < beta < 1.0):
        print("  UPOZORENJE: beta van (0,1) — provjeri ulazne podatke.")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="") as fout:
            fieldnames = headers + ["log_num_tokens", "log_num_types", "heaps_V_pred"]
            writer = csv.DictWriter(fout, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row, N, V in zip(rows, Ns, Vs):
                out = dict(row)
                out["log_num_tokens"] = f"{math.log(N):.10f}"
                out["log_num_types"] = f"{math.log(V):.10f}"
                out["heaps_V_pred"] = f"{k * N ** beta:.4f}"
                writer.writerow(out)


if __name__ == "__main__":
    main()
