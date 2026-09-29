#!/usr/bin/env python3
"""Jensen–Shannon divergencija/distanca između žanrova (unigrami riječi ili karaktera).

Ulaz: više fajlova, jedan po žanru. Svaki fajl je ILI
  - CSV sa kolonama gram,count (izlaz collect_unigram_counts.py), ILI
  - sirovi tekst (.txt / .txt.gz) — tada se tokenizuje identično ent.py.

    JSD(P,Q) = H(M) - (H(P)+H(Q))/2,   M = (P+Q)/2      [bits, 0..1]
    JS distanca = sqrt(JSD)                               [metrika, 0..1]

Izlaz: dugi format CSV
    genre_a,genre_b,jsd_bits,js_distance
(+ opcionalno --wide: kvadratna matrica js_distance za heatmap / pgfplots matrix plot)

Primjer:
    python compute_jsd_genres.py --mode words --lowercase \
        --inputs data/by_genre_97mb/*.txt \
        --output out/metrics/heat_jsd_words_97mb.csv \
        --wide out/metrics/heat_jsd_words_97mb_matrix.csv

Napomena: --top K ograničava na K najčešćih tipova svakog žanra (unija); preostala
masa se sabira u jedan tip "<OTHER>", tako da raspodjele ostaju normalizovane.
"""
import argparse
import csv
import math
from collections import Counter
from itertools import combinations
from pathlib import Path

from tokenize_common import is_letter, open_text, tokenize_words


def genre_name(path: Path) -> str:
    name = path.name
    for suf in (".gz", ".csv", ".txt"):
        if name.endswith(suf):
            name = name[: -len(suf)]
    return name.replace("bosnian_corpus_", "")


def load_counts(path: Path, mode: str, lowercase: bool, letters_only: bool) -> Counter:
    cnt = Counter()
    name = str(path)
    if name.endswith(".csv") or name.endswith(".csv.gz"):
        with open_text(path) as f:
            r = csv.DictReader(f)
            for row in r:
                try:
                    c = int(row["count"])
                except (KeyError, ValueError):
                    continue
                g = row["gram"]
                if lowercase:
                    g = g.lower()
                if letters_only and not all(is_letter(ch) for ch in g):
                    continue
                cnt[g] += c
        return cnt
    with open_text(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if lowercase:
                line = line.lower()
            if mode == "words":
                cnt.update(tokenize_words(line))
            else:
                if letters_only:
                    cnt.update(ch for ch in line if is_letter(ch))
                else:
                    cnt.update(line)
    return cnt


def entropy_bits(probs):
    return -sum(p * math.log2(p) for p in probs if p > 0)


def jsd(P: Counter, Q: Counter) -> float:
    tp, tq = sum(P.values()), sum(Q.values())
    h_p = entropy_bits(c / tp for c in P.values())
    h_q = entropy_bits(c / tq for c in Q.values())
    keys = set(P) | set(Q)
    h_m = entropy_bits(0.5 * (P.get(k, 0) / tp + Q.get(k, 0) / tq) for k in keys)
    return max(0.0, h_m - 0.5 * (h_p + h_q))


def apply_top(counts, top):
    keep = set()
    for c in counts.values():
        keep.update(g for g, _ in c.most_common(top))
    out = {}
    for name, c in counts.items():
        nc = Counter({g: v for g, v in c.items() if g in keep})
        other = sum(c.values()) - sum(nc.values())
        if other > 0:
            nc["<OTHER>"] = other
        out[name] = nc
    return out


def main():
    ap = argparse.ArgumentParser(description="Jensen–Shannon divergence between genres.")
    ap.add_argument("--inputs", required=True, type=Path, nargs="+")
    ap.add_argument("--mode", choices=["words", "chars"], default="words")
    ap.add_argument("--lowercase", action="store_true")
    ap.add_argument("--letters-only", action="store_true",
                    help="(chars) samo slova; (gram,count CSV) samo gramovi od slova")
    ap.add_argument("--top", type=int, default=0, help="0 = svi tipovi")
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--wide", type=Path, help="Opcioni CSV sa kvadratnom matricom js_distance")
    args = ap.parse_args()

    counts = {}
    for p in args.inputs:
        counts[genre_name(p)] = load_counts(p, args.mode, args.lowercase, args.letters_only)
        print(f"  {genre_name(p)}: T={sum(counts[genre_name(p)].values())}, V={len(counts[genre_name(p)])}")
    if args.top > 0:
        counts = apply_top(counts, args.top)

    names = sorted(counts)
    D = {}
    for a, b in combinations(names, 2):
        d = jsd(counts[a], counts[b])
        D[(a, b)] = D[(b, a)] = d
    for a in names:
        D[(a, a)] = 0.0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as fo:
        w = csv.writer(fo)
        w.writerow(["genre_a", "genre_b", "jsd_bits", "js_distance"])
        for a in names:
            for b in names:
                w.writerow([a, b, f"{D[(a, b)]:.10f}", f"{math.sqrt(D[(a, b)]):.10f}"])
    if args.wide:
        args.wide.parent.mkdir(parents=True, exist_ok=True)
        with args.wide.open("w", encoding="utf-8", newline="") as fo:
            w = csv.writer(fo)
            w.writerow(["genre"] + names)
            for a in names:
                w.writerow([a] + [f"{math.sqrt(D[(a, b)]):.8f}" for b in names])


if __name__ == "__main__":
    main()
