# Entropy and Energy of the Bosnian Language — Entropy Toolkit + Paper Materials

**English** · [Bosanski](README.bs.md)

A reproducible, information-theoretic analysis of the Bosnian language on a **6.18 GB cleaned corpus** (Bosnian Corpus v1.0). It covers **n-gram block entropy**, **conditional entropy / entropy-rate approximation**, **Zipf/Heaps**, **Onicescu energy**, **Rényi-2**, **Shannon entropy**, **Gini–Simpson**, **HHI**, and **genre comparisons** (balanced to ~97 MB per genre).

**GitHub repository:** https://github.com/H4sK0/Entropy  
**Paper, revised English version (Zenodo DOI):** [10.5281/zenodo.20804511](https://doi.org/10.5281/zenodo.20804511)  
**Paper, first version (Zenodo DOI):** [10.5281/zenodo.17970788](https://doi.org/10.5281/zenodo.17970788)  
**Corpus (Zenodo DOI):** [10.5281/zenodo.17757098](https://doi.org/10.5281/zenodo.17757098)

---

## What this repository contains

- A deterministic pipeline that computes:
  - character-level entropy (up to **n = 8**)
  - word-level entropy (up to **n = 5**)
  - conditional entropies and entropy-rate approximations
  - unigram concentration measures (the "energy family")
  - Zipf distributions (words and letters)
  - Heaps' law fits (optional)
  - Jensen–Shannon distances between genres (word unigrams)

- CSV outputs formatted for:
  - LaTeX tables and PGFPlots figures
  - further analysis in Python or R

---

## Zenodo records

### Paper — current version (revised, English)
- **DOI:** [10.5281/zenodo.20804511](https://doi.org/10.5281/zenodo.20804511)
- Extended and revised English version of the paper. **Please cite this version.**

### Paper — first version
- **DOI:** [10.5281/zenodo.17970788](https://doi.org/10.5281/zenodo.17970788)
- Original version, kept for the record. It references the corpus and pipeline and includes reproducibility instructions.

### Dataset (Bosnian Corpus v1.0)
- **DOI:** [10.5281/zenodo.17757098](https://doi.org/10.5281/zenodo.17757098)
- Cleaned text suitable for entropy and NLP research (global and per genre).

---

## Repository layout

```
ent.py                                  # map/reduce n-gram counting -> sufficient statistics
run_reduce_chars_parallel.sh            # parallel reduce for chars n=1..8
entropy_chars_stats.csv                 # published results, global (chars, n=1..8)
entropy_words_stats.csv                 # published results, global (words, n=1..5)
entropy_chars_genres_97mb.csv           # per genre (~97 MB/genre)
entropy_words_genres_97mb.csv
bosnian_entropy_toolkit/
  tokenize_common.py                    # tokenization identical to ent.py
  compute_conditional_entropy.py        # H(n) - H(n-1)
  compute_block_entropy_series.py       # H(n), H(n)/n, ΔH, Δ²H
  compute_entropy_rate.py               # H(n)/n (block rate)
  summarize_entropy_rate.py             # block and conditional rate + sampling diagnostics
  compute_energy_metrics.py             # Onicescu E, Rényi-2, Gini–Simpson, HHI, Hill numbers
  compute_redundancy_chars.py           # redundancy 1 - h/log2|A|
  collect_unigram_counts.py             # gram,count from map part files
  compute_zipf_from_unigrams.py         # rank/frequency table
  compute_information_per_unit.py       # -log2 p per unit
  compute_jsd_genres.py                 # Jensen–Shannon between genres
  make_heaps_snapshots.py               # (N, V) vocabulary-growth points
  fit_heaps_law.py                      # V(N) = k N^β
```

All scripts use only the Python standard library (Python ≥ 3.8); `requirements.txt` is intentionally empty.

---

## Quick start

```bash
git clone https://github.com/H4sK0/Entropy.git
cd Entropy
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1
TK=bosnian_entropy_toolkit
```

Unpack the corpus from Zenodo into `data/`, for example:

```
data/clean/bosnian_corpus_all.txt
data/by_genre_97mb/bosnian_corpus_{ads_promo,forum_chat,info_howto,legal_admin,literature,mix,news,opinion}.txt
```

---

## 1) N-gram counting (map → reduce)

These are the exact settings used to produce the published `entropy_*_stats.csv` files (default options):

```bash
# Characters, n = 1..8
python3 ent.py map    --input data/clean/bosnian_corpus_all.txt --mode chars \
                      --n 1 2 3 4 5 6 7 8 --out-dir parts_chars
./run_reduce_chars_parallel.sh parts_chars entropy_chars_stats.csv bosnian_corpus_all.txt all
#   (or serially:)
# python3 ent.py reduce --parts-dir parts_chars --mode chars --n 1 2 3 4 5 6 7 8 \
#                       --out entropy_chars_stats.csv --tag-file bosnian_corpus_all.txt --tag-genre all

# Words, n = 1..5
python3 ent.py map    --input data/clean/bosnian_corpus_all.txt --mode words \
                      --n 1 2 3 4 5 --out-dir parts_words
python3 ent.py reduce --parts-dir parts_words --mode words --n 1 2 3 4 5 \
                      --out entropy_words_stats.csv --tag-file bosnian_corpus_all.txt --tag-genre all
```

For genres, run one `map`/`reduce` pair per file with `--tag-genre <genre>`, then concatenate the CSVs.

**`map` options** (all new options are opt-in; the defaults reproduce the published results):

| option | meaning |
|---|---|
| `--lowercase` | lowercase everything before counting |
| `--skip-whitespace` | (chars) drop whitespace |
| `--line-sep ' '` | (chars) replace the line break with a space. The default `''` joins lines with no separator, so the last word of one line and the first word of the next form artificial n-grams |
| `--reset-context line` | n-grams do not cross line/document boundaries (default `file`) |
| `--letters-only` | (chars) alphabet = letters + space; everything else → space. Recommended for redundancy and cross-language comparison |
| `--buckets`, `--flush-keys`, `--compress`, `--hash` | performance only; they do not affect results |

---

## 2) Derived measures from `entropy_*_stats.csv`

```bash
# Conditional entropy H(n)-H(n-1) and the block-entropy series
python3 $TK/compute_conditional_entropy.py  --input entropy_chars_stats.csv --output out/cond_chars.csv
python3 $TK/compute_block_entropy_series.py --input entropy_chars_stats.csv --output out/block_chars.csv

# Entropy rate: block (H/n) and conditional, plus sampling diagnostics
python3 $TK/summarize_entropy_rate.py --input entropy_words_stats.csv --output out/rate_words.csv

# Energy / concentration (Onicescu, Rényi-2, Gini–Simpson, HHI)
python3 $TK/compute_energy_metrics.py --input entropy_words_stats.csv --output out/energy_words.csv
python3 $TK/compute_energy_metrics.py --input entropy_words_genres_97mb.csv --output out/energy_words_genres.csv

# Redundancy: |A| must match the inventory over which H was computed.
# entropy_chars_letters_stats.csv = map/reduce with --letters-only --lowercase (|A| = 30 letters + space = 31)
python3 $TK/compute_redundancy_chars.py --input entropy_chars_letters_stats.csv \
        --output out/redundancy_chars.csv --alphabet-size 31 --rate conditional
```

Formulas in `compute_energy_metrics.py` (computed from sufficient statistics, without re-reading the corpus):

- Onicescu energy E = Σ p² = Σ c² / T²
- Rényi-2 H₂ = −log₂ E
- Gini–Simpson G = 1 − E
- normalized HHI = (E − 1/V) / (1 − 1/V)
- Shannon H₁ = log₂ T − Σ c log₂ c / T; Rényi-½ = 2 log₂ Σ √p

The legacy columns `E1_*`, `E05_*`, `E2_*` are kept for backward compatibility (`--no-legacy` removes them). **`E2_per_token` = Σc²/T is not the Onicescu energy.**

---

## 3) Unigrams, Zipf, information per unit

```bash
python3 $TK/collect_unigram_counts.py --parts-dir parts_words --mode words --output out/unigrams_words.csv
python3 $TK/collect_unigram_counts.py --parts-dir parts_chars --mode chars --output out/unigrams_letters.csv \
        --letters-only --lowercase
python3 $TK/compute_zipf_from_unigrams.py   --input out/unigrams_words.csv --output out/zipf_words.csv
python3 $TK/compute_information_per_unit.py --input out/unigrams_words.csv --output out/info_words.csv
```

---

## 4) Heaps' law

Heaps' law is fitted to the **growth of a single corpus** (N from ~10³ up to the full corpus), not to n-grams of different orders and not to genres of equal size. The script now checks this and refuses to fit when max(N)/min(N) < 10.

```bash
python3 $TK/make_heaps_snapshots.py --input data/clean/bosnian_corpus_all.txt \
        --output out/heaps_points_words.csv
python3 $TK/fit_heaps_law.py --input out/heaps_points_words.csv --mode words --output out/heaps_fit.csv
```

If `map` was run with `--lowercase`, also pass `--lowercase` to `make_heaps_snapshots.py`.

---

## 5) Jensen–Shannon between genres

```bash
python3 $TK/compute_jsd_genres.py --mode words --inputs data/by_genre_97mb/*.txt \
        --output out/heat_jsd_words_97mb.csv --wide out/heat_jsd_words_97mb_matrix.csv
# or from gram,count files (collect_unigram_counts.py per genre):
python3 $TK/compute_jsd_genres.py --inputs out/unigrams_*.csv --output out/jsd.csv
```

Output: `jsd_bits` (0–1) and `js_distance = sqrt(JSD)`, which is a true metric.

---

## Methodological notes (important for interpretation)

1. **Estimator.** All entropies are MLE (plug-in) estimates. They are biased downward, and the bias grows with V/T.
2. **Saturation of word n-grams.** In the global corpus, V/T for words is 0.47 (n=3), 0.74 (n=4) and 0.86 (n=5), and H(5) = 29.34 bits is close to the maximum log₂T = 29.81. The drop in conditional entropy for n ≥ 3 (5.06 → 2.10 → 0.68 bits) is therefore a finite-sample effect, not a linguistic plateau. `summarize_entropy_rate.py` flags this in the `saturation`, `types_per_token` and `reliable` columns.
3. **Rate definition.** H(n)/n (block) and H(n) − H(n−1) (conditional) converge to the same rate, but at different speeds. For characters at n=8 they give 2.98 vs 1.86 bits/char. The paper should state which one is used.
4. **Character inventory.** The global character unigrams contain 2,932 types (all Unicode punctuation, digits, foreign letters). For redundancy and cross-language comparison, use `--letters-only` and report |A|.
5. **Line boundaries.** The default `map` joins lines with no separator and lets n-grams cross document boundaries; see `--line-sep` and `--reset-context`.

### Reference values (unigrams, from the published CSVs)

| | T | V | H₁ [bits] | Onicescu E | H₂ [bits] | Gini–Simpson |
|---|---|---|---|---|---|---|
| characters | 5,013,889,571 | 2,932 | 4.4572 | 0.058339 | 4.0994 | 0.941661 |
| words | 938,196,277 | 5,035,194 | 12.6769 | 0.0052504 | 7.5733 | 0.994750 |

---

## Reproducibility and integrity

- Use the same corpus release and the same cleaning/tokenization rules.
- The default `ent.py` options give bit-identical results to the version used to produce the published CSVs.
- When using the Zenodo archives, verify the SHA-256 checksums.

## How to cite

Please cite the revised English version of the paper, DOI [10.5281/zenodo.20804511](https://doi.org/10.5281/zenodo.20804511), and the corpus, DOI [10.5281/zenodo.17757098](https://doi.org/10.5281/zenodo.17757098). GitHub's "Cite this repository" button uses `CITATION.cff`.

## Changes (v1.1)

- `compute_energy_metrics.py`: added Onicescu E = Σc²/T², Rényi-2, Gini–Simpson, normalized HHI, Rényi-½, Hill numbers
- `fit_heaps_law.py`: filters by mode/n, rejects a degenerate N range, reports SE and R²
- `summarize_entropy_rate.py`: conditional rate + saturation diagnostics
- `compute_redundancy_chars.py`: conditional rate by default; removed the duplicate `predictability` column
- new scripts: `compute_jsd_genres.py`, `make_heaps_snapshots.py`, `tokenize_common.py`
- `ent.py`: opt-in options `--line-sep`, `--reset-context`, `--letters-only` (default behaviour unchanged)
- `collect_unigram_counts.py`: `--letters-only`, `--lowercase`
- `run_reduce_chars_parallel.sh`: a proper bash script (previously a pasted terminal session)
- README: commands match the scripts' actual arguments; English README added; DOI of the revised paper added
