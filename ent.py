#!/usr/bin/env python3
import argparse, csv, gzip, hashlib, math, re, zlib
from collections import Counter, deque
from pathlib import Path
from typing import Iterable, List

WORD_RE = re.compile(r"[A-Za-zÀ-ž0-9]+(?:[-’'][A-Za-zÀ-ž0-9]+)*")
NON_LETTER_RUN = re.compile(r"[\W\d_]+")

# NAPOMENA O REPRODUCIBILNOSTI
# Default postavke (line_sep="", reset_context="file", bez --letters-only) su IDENTIČNE
# verziji kojom su dobijeni objavljeni entropy_*_stats.csv. Nove opcije su opt-in.

def open_maybe_gzip(path: Path, mode="rt"):
    if str(path).endswith(".gz"):
        return gzip.open(path, mode, encoding="utf-8", errors="ignore")
    return open(path, mode, encoding="utf-8", errors="ignore")

def iter_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
    else:
        for p in root.rglob("*"):
            if p.is_file():
                yield p

def tokenize_words(line: str) -> List[str]:
    return WORD_RE.findall(line)

def bucket_id(key_str: str, buckets: int, hash_kind: str) -> int:
    if hash_kind == "adler32":
        return zlib.adler32(key_str.encode("utf-8")) % buckets
    # fallback: blake2b (sporije, ali stabilno)
    h = hashlib.blake2b(key_str.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(h, "little") % buckets

def map_stage(input_path: Path, mode: str, ns, out_dir: Path,
              buckets: int, flush_keys: int, lowercase: bool,
              skip_whitespace: bool, compress: str, compress_level: int,
              hash_kind: str, line_sep: str = "", reset_context: str = "file",
              letters_only: bool = False):
    out_dir.mkdir(parents=True, exist_ok=True)
    counters = {n: [Counter() for _ in range(buckets)] for n in ns}
    total_keys = 0
    part_id = 0
    # kontekst za prelaz preko linija
    if mode == "words":
        ctx = {n: deque(maxlen=n-1) for n in ns if n > 1}
    else:
        ctx = {n: "" for n in ns if n > 1}

    def _dump_counter(fn: Path, cnt: Counter):
        if compress == "gzip":
            with gzip.open(fn.with_suffix(fn.suffix + ".gz"), "wt", encoding="utf-8", newline="", compresslevel=compress_level) as f:
                w = csv.writer(f)
                for g, c in cnt.items():
                    w.writerow([g, c])
        else:
            with open(fn, "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                for g, c in cnt.items():
                    w.writerow([g, c])

    def flush_all():
        nonlocal part_id, total_keys
        for n in ns:
            for b in range(buckets):
                cnt = counters[n][b]
                if not cnt:
                    continue
                base = out_dir / f"{mode}_n{n:02d}_b{b:04d}_part{part_id:05d}.csv"
                _dump_counter(base, cnt)
                cnt.clear()
        total_keys = 0
        part_id += 1

    def _reset_ctx():
        if mode == "words":
            return {n: deque(maxlen=n-1) for n in ns if n > 1}
        return {n: "" for n in ns if n > 1}

    for file in iter_files(input_path):
        with open_maybe_gzip(file, "rt") as f:
            for raw in f:
                line = raw.rstrip("\n")
                if lowercase:
                    line = line.lower()
                if mode == "chars":
                    if letters_only:
                        # alfabet = slova + jedan razmak; sve ostalo -> razmak,
                        # nizovi razmaka se sažimaju, kraj linije = razmak
                        line = NON_LETTER_RUN.sub(" ", line).strip()
                        line = (line + " ") if line else ""
                    elif line_sep:
                        line = line + line_sep

                if mode == "words":
                    toks = tokenize_words(line)

                    # unigrams
                    if 1 in ns:
                        for t in toks:
                            b = bucket_id(t, buckets, hash_kind)
                            counters[1][b][t] += 1
                            total_keys += 1

                    # n>1 n-grami: broji (ctx + t), pa tek onda d.append(t)
                    for t in toks:
                        for n in ns:
                            if n == 1:
                                continue
                            d = ctx[n]
                            if len(d) == n - 1:
                                gram = " ".join(list(d) + [t])
                                b = bucket_id(gram, buckets, hash_kind)
                                counters[n][b][gram] += 1
                                total_keys += 1
                            d.append(t)

                else:
                    s = line
                    # unigrams
                    if 1 in ns:
                        for ch in s:
                            if skip_whitespace and ch.isspace():
                                continue
                            b = bucket_id(ch, buckets, hash_kind)
                            counters[1][b][ch] += 1
                            total_keys += 1
                    # n>1
                    for n in ns:
                        if n == 1:
                            continue
                        carry = ctx[n]
                        buf = carry + s
                        if skip_whitespace:
                            # briši čiste whitespace (opciono)
                            buf = "".join(ch for ch in buf if not ch.isspace())
                        L = len(buf)
                        if L >= n:
                            for i in range(L - n + 1):
                                g = buf[i:i+n]
                                b = bucket_id(g, buckets, hash_kind)
                                counters[n][b][g] += 1
                                total_keys += 1
                        ctx[n] = buf[-(n-1):] if L >= n-1 else buf

                if reset_context == "line":
                    ctx = _reset_ctx()

                if total_keys >= flush_keys:
                    flush_all()

        # reset konteksta po fajlu
        if mode == "words":
            ctx = {n: deque(maxlen=n-1) for n in ns if n > 1}
        else:
            ctx = {n: "" for n in ns if n > 1}

    flush_all()

def _log2(x: float) -> float:
    return math.log(x, 2) if x > 0 else float("-inf")

def reduce_to_stats(parts_dir: Path, mode: str, ns, buckets: int,
                    out_csv: Path, tag_file: str, tag_genre: str):
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for n in ns:
        T = 0            # num_ngrams
        V = 0            # num_types
        c_max = 0
        S1  = 0.0        # ∑ c log2 c
        S05 = 0.0        # ∑ c^0.5
        S2  = 0.0        # ∑ c^2

        for b in range(buckets):
            agg = Counter()
            # traži i .csv.gz i .csv
            patt_gz = f"{mode}_n{n:02d}_b{b:04d}_part*.csv.gz"
            patt_pl = f"{mode}_n{n:02d}_b{b:04d}_part*.csv"
            files = sorted(list(parts_dir.glob(patt_gz)) + [p for p in parts_dir.glob(patt_pl) if not str(p).endswith(".gz")])
            if not files:
                continue

            for fn in files:
                if str(fn).endswith(".gz"):
                    f = gzip.open(fn, "rt", encoding="utf-8", newline="")
                else:
                    f = open(fn, "r", encoding="utf-8", newline="")
                with f:
                    r = csv.reader(f)
                    for gram, c in r:
                        agg[gram] += int(c)

            if agg:
                V += len(agg)
                for c in agg.values():
                    T += c
                    if c > c_max: c_max = c
                    S1  += c * _log2(c)
                    S05 += c ** 0.5
                    S2  += c ** 2
                agg.clear()

        H1 = (_log2(T) - (S1 / T)) if T > 0 else 0.0
        rows.append([
            tag_file, tag_genre, mode, n,
            T, V, H1, S1, S05, S2, c_max
        ])

    cols = ["file","genre","mode","n",
            "num_tokens","num_types","entropy_bits",
            "sum_c_log2c","sum_c_sqrt","sum_c2","c_max"]

    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)

def main():
    ap = argparse.ArgumentParser("Fast MapReduce Entropy – sufficient stats")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_map = sub.add_parser("map", help="Count n-grams into bucketed parts")
    ap_map.add_argument("--input", required=True, type=Path)
    ap_map.add_argument("--mode", choices=["chars","words"], required=True)
    ap_map.add_argument("--n", nargs="+", type=int, required=True)
    ap_map.add_argument("--out-dir", required=True, type=Path)
    ap_map.add_argument("--buckets", type=int, default=64)
    ap_map.add_argument("--flush-keys", type=int, default=10_000_000)
    ap_map.add_argument("--lowercase", action="store_true")
    ap_map.add_argument("--skip-whitespace", action="store_true",
                        help="(chars mode) preskoči whitespace pri brojanju")
    ap_map.add_argument("--compress", choices=["gzip","none"], default="gzip")
    ap_map.add_argument("--compress-level", type=int, default=1)
    ap_map.add_argument("--hash", choices=["adler32","blake2b"], default="adler32")
    ap_map.add_argument("--line-sep", default="",
                        help="(chars) znak koji zamjenjuje prelom reda; default '' = linije se "
                             "spajaju bez razmaka (kao u objavljenim rezultatima). Preporuka: ' '")
    ap_map.add_argument("--reset-context", choices=["file","line"], default="file",
                        help="Da li n-grami smiju prelaziti granicu linije (file, default) ili ne (line)")
    ap_map.add_argument("--letters-only", action="store_true",
                        help="(chars) alfabet = slova + razmak; sve ne-slovo -> razmak")

    ap_red = sub.add_parser("reduce", help="Aggregate parts into sufficient stats CSV")
    ap_red.add_argument("--parts-dir", required=True, type=Path)
    ap_red.add_argument("--mode", choices=["chars","words"], required=True)
    ap_red.add_argument("--n", nargs="+", type=int, required=True)
    ap_red.add_argument("--buckets", type=int, default=64)
    ap_red.add_argument("--out", required=True, type=Path)
    ap_red.add_argument("--tag-file", default="")
    ap_red.add_argument("--tag-genre", default="")

    args = ap.parse_args()
    ns = sorted(set(int(x) for x in getattr(args, "n", [])))

    if args.cmd == "map":
        map_stage(args.input, args.mode, ns, args.out_dir,
                  args.buckets, args.flush_keys, args.lowercase,
                  args.skip_whitespace, args.compress, args.compress_level,
                  args.hash, args.line_sep, args.reset_context, args.letters_only)
    else:
        reduce_to_stats(args.parts_dir, args.mode, ns, args.buckets,
                        args.out, args.tag_file, args.tag_genre)

if __name__ == "__main__":
    main()
