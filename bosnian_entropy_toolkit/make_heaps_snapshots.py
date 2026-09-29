#!/usr/bin/env python3
"""Napravi (N, V) tačke rasta vokabulara za Heapsov zakon iz sirovog teksta.

Čita tekst sekvencijalno (tokenizacija identična ent.py) i bilježi broj tokena N i
broj različitih tipova V u logaritamski raspoređenim tačkama.

Izlaz (kompatibilan sa fit_heaps_law.py):
    file,genre,mode,n,num_tokens,num_types

Primjer:
    python make_heaps_snapshots.py --input data/clean/bosnian_corpus_all.txt \
        --output out/metrics/heaps_points_words.csv --lowercase
    python fit_heaps_law.py --input out/metrics/heaps_points_words.csv --mode words

Memorija: drži skup svih tipova (za ~5 M tipova reda veličine ~0,5–1 GB RAM).
"""
import argparse
import csv
import math
from pathlib import Path

from tokenize_common import open_text, tokenize_words


def main():
    ap = argparse.ArgumentParser(description="Heaps growth points (N, V) from raw text.")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--lowercase", action="store_true",
                    help="Mora odgovarati postavci korištenoj u ent.py map")
    ap.add_argument("--points-per-decade", type=int, default=10)
    ap.add_argument("--start", type=int, default=1000, help="Prva tačka (broj tokena)")
    ap.add_argument("--genre", default="")
    args = ap.parse_args()

    step = 10 ** (1.0 / args.points_per_decade)
    next_cp = float(args.start)
    seen = set()
    N = 0
    out = []
    with open_text(args.input) as f:
        for line in f:
            if args.lowercase:
                line = line.lower()
            for t in tokenize_words(line):
                N += 1
                seen.add(t)
                if N >= next_cp:
                    out.append((N, len(seen)))
                    while next_cp <= N:
                        next_cp *= step
    if not out or out[-1][0] != N:
        out.append((N, len(seen)))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as fo:
        w = csv.writer(fo)
        w.writerow(["file", "genre", "mode", "n", "num_tokens", "num_types"])
        for n_tok, v in out:
            w.writerow([args.input.name, args.genre, "words", 1, n_tok, v])
    print(f"{len(out)} tačaka, N={N}, V={len(seen)} -> {args.output}")


if __name__ == "__main__":
    main()
