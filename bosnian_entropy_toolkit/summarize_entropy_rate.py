#!/usr/bin/env python3
"""Summarize entropy-rate estimates per (file, genre, mode) + dijagnostika uzorkovanja.

Ulaz: entropy_*_stats.csv
Izlaz: jedan red po (file, genre, mode) i po n (ili samo n_max uz --only-max):

    n, entropy_bits (H(n)),
    block_rate        = H(n)/n              (gornja granica; sporo konvergira)
    conditional_rate  = H(n) - H(n-1)       (bolja procjena h; za n=1 prazno)
    log2_tokens       = log2(T)             (maksimalna moguća MLE entropija)
    saturation        = H(n) / log2(T)      (blizu 1 -> n-grami su uglavnom hapaksi)
    types_per_token   = V/T
    reliable          = 1 ako types_per_token < --max-vt (default 0.1), inače 0

Entropijska stopa h = lim H(n)-H(n-1) = lim H(n)/n; conditional_rate konvergira brže.
Kada je reliable = 0, MLE sistematski PODCJENJUJE H(n), pa conditional_rate pada
vještački — to NIJE jezički plato nego posljedica konačnog uzorka.
"""
import argparse
import csv
import math
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser(description="Summarize entropy rate with sampling diagnostics.")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--only-max", action="store_true", help="Samo red za najveći n")
    ap.add_argument("--max-vt", type=float, default=0.1,
                    help="Prag V/T iznad kojeg se procjena označava kao nepouzdana")
    args = ap.parse_args()

    groups = defaultdict(list)
    with open(args.input, "r", encoding="utf-8", newline="") as fin:
        for row in csv.DictReader(fin):
            try:
                key = (row["file"], row["genre"], row["mode"])
                rec = (int(row["n"]), float(row["entropy_bits"]),
                       float(row["num_tokens"]), float(row["num_types"]))
            except (KeyError, ValueError):
                continue
            groups[key].append(rec)

    with open(args.output, "w", encoding="utf-8", newline="") as fout:
        w = csv.writer(fout)
        w.writerow(["file", "genre", "mode", "n", "entropy_bits", "block_rate",
                    "conditional_rate", "log2_tokens", "saturation",
                    "types_per_token", "reliable"])
        for (file_, genre, mode), recs in groups.items():
            recs.sort()
            byn = {r[0]: r for r in recs}
            sel = [recs[-1]] if args.only_max else recs
            for n, H, T, V in sel:
                prev = byn.get(n - 1)
                cond = "" if prev is None else f"{H - prev[1]:.10f}"
                l2t = math.log2(T) if T > 0 else float("nan")
                vt = V / T if T > 0 else float("nan")
                w.writerow([file_, genre, mode, n, f"{H:.10f}",
                            f"{H / n:.10f}", cond, f"{l2t:.6f}",
                            f"{H / l2t:.6f}", f"{vt:.6f}",
                            1 if vt < args.max_vt else 0])


if __name__ == "__main__":
    main()
