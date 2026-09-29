# Entropija i energija bosanskog jezika — Entropy Toolkit + materijali rada

[English](README.md) · **Bosanski**

Reproducibilna, informaciono–teorijska analiza bosanskog jezika na **6,18 GB očišćenog korpusa** (Bosnian Corpus v1.0), uključujući **blok–entropiju n-grama**, **uslovnu entropiju / aproksimaciju entropijske stope**, **Zipf/Heaps**, **Onicescu energiju**, **Rényi-2**, **Shannonovu entropiju**, **Gini–Simpson**, **HHI**, te **poređenja po žanrovima** (uravnoteženo ~97 MB po žanru).

**GitHub repozitorij:** https://github.com/H4sK0/Entropy  
**Rad, revidirana engleska verzija (Zenodo DOI):** [10.5281/zenodo.20804511](https://doi.org/10.5281/zenodo.20804511)  
**Rad, prva verzija (Zenodo DOI):** [10.5281/zenodo.17970788](https://doi.org/10.5281/zenodo.17970788)  
**Korpus (Zenodo DOI):** [10.5281/zenodo.17757098](https://doi.org/10.5281/zenodo.17757098)

---

## Šta ovaj repozitorij sadrži

Ovaj repozitorij obezbjeđuje:

- Deterministički pipeline za računanje:
  - Entropija na nivou karaktera (do **n = 8**)
  - Entropija na nivou riječi (do **n = 5**)
  - Uslovne entropije i aproksimacije entropijske stope
  - Unigram koncentracionih metrika (“familija energije”)
  - Zipfove raspodjele (riječi + slova)
  - (Opcionalno) fitovanje Heapsovog zakona
  - Jensen–Shannon distance između žanrova (word–unigrami)

- CSV izlaze formatirane za:
  - LaTeX tabele i PGFPlots grafikone
  - Dalju analizu u Pythonu/R

---

## Zenodo artefakti

### Rad — aktuelna verzija (revidirana, engleski)
- **DOI:** [10.5281/zenodo.20804511](https://doi.org/10.5281/zenodo.20804511)  
- Proširena i revidirana verzija rada na engleskom jeziku. **Ovu verziju citirati.**

### Rad — prva verzija
- **DOI:** [10.5281/zenodo.17970788](https://doi.org/10.5281/zenodo.17970788)  
- Originalna verzija; zadržana radi historije. Rad referencira korpus + pipeline i sadrži uputstva za reproducibilnost.

### Skup podataka (Bosnian Corpus v1.0)
- **DOI:** [10.5281/zenodo.17757098](https://doi.org/10.5281/zenodo.17757098)  
- Očišćen tekst pogodan za entropiju/NLP istraživanja (globalno + po žanrovima).

---


## Struktura repozitorija

```
ent.py                                  # map/reduce brojanje n-grama -> dovoljne statistike
run_reduce_chars_parallel.sh            # paralelni reduce za chars n=1..8
entropy_chars_stats.csv                 # objavljeni rezultati, globalno (chars, n=1..8)
entropy_words_stats.csv                 # objavljeni rezultati, globalno (words, n=1..5)
entropy_chars_genres_97mb.csv           # po žanrovima (~97 MB/žanr)
entropy_words_genres_97mb.csv
bosnian_entropy_toolkit/
  tokenize_common.py                    # tokenizacija identična ent.py
  compute_conditional_entropy.py        # H(n) - H(n-1)
  compute_block_entropy_series.py       # H(n), H(n)/n, ΔH, Δ²H
  compute_entropy_rate.py               # H(n)/n (blok-stopa)
  summarize_entropy_rate.py             # blok- i uslovna stopa + dijagnostika uzorkovanja
  compute_energy_metrics.py             # Onicescu E, Rényi-2, Gini–Simpson, HHI, Hillovi brojevi
  compute_redundancy_chars.py           # redundansa 1 - h/log2|A|
  collect_unigram_counts.py             # gram,count iz map part fajlova
  compute_zipf_from_unigrams.py         # rank/frekvencija
  compute_information_per_unit.py       # -log2 p po jedinici
  compute_jsd_genres.py                 # Jensen–Shannon između žanrova
  make_heaps_snapshots.py               # (N, V) tačke rasta vokabulara
  fit_heaps_law.py                      # V(N) = k N^β
```

Sve skripte koriste samo Python standardnu biblioteku (Python ≥ 3.8); `requirements.txt` je prazan.

---

## Brzi start

```bash
git clone https://github.com/H4sK0/Entropy.git
cd Entropy
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1
TK=bosnian_entropy_toolkit
```

Korpus sa Zenoda raspakuj u `data/`, npr.:

```
data/clean/bosnian_corpus_all.txt
data/by_genre_97mb/bosnian_corpus_{ads_promo,forum_chat,info_howto,legal_admin,literature,mix,news,opinion}.txt
```

---

## 1) Brojanje n-grama (map → reduce)

Tačne postavke kojima su dobijeni objavljeni `entropy_*_stats.csv` (default opcije):

```bash
# Karakteri, n = 1..8
python3 ent.py map    --input data/clean/bosnian_corpus_all.txt --mode chars \
                      --n 1 2 3 4 5 6 7 8 --out-dir parts_chars
./run_reduce_chars_parallel.sh parts_chars entropy_chars_stats.csv bosnian_corpus_all.txt all
#   (ili serijski:)
# python3 ent.py reduce --parts-dir parts_chars --mode chars --n 1 2 3 4 5 6 7 8 \
#                       --out entropy_chars_stats.csv --tag-file bosnian_corpus_all.txt --tag-genre all

# Riječi, n = 1..5
python3 ent.py map    --input data/clean/bosnian_corpus_all.txt --mode words \
                      --n 1 2 3 4 5 --out-dir parts_words
python3 ent.py reduce --parts-dir parts_words --mode words --n 1 2 3 4 5 \
                      --out entropy_words_stats.csv --tag-file bosnian_corpus_all.txt --tag-genre all
```

Za žanrove isto, jedan `map`/`reduce` par po fajlu sa `--tag-genre <žanr>`, pa spoji CSV-ove.

**Opcije `map` faze** (sve nove opcije su opt-in; default = objavljeni rezultati):

| opcija | značenje |
|---|---|
| `--lowercase` | sve u mala slova prije brojanja |
| `--skip-whitespace` | (chars) izbaci razmake |
| `--line-sep ' '` | (chars) prelom reda zamijeni razmakom. Default `''` spaja linije bez razmaka, pa zadnja riječ linije i prva riječ sljedeće daju vještačke n-grame |
| `--reset-context line` | n-grami ne prelaze granicu linije/dokumenta (default `file`) |
| `--letters-only` | (chars) alfabet = slova + razmak; sve ostalo → razmak. Preporučeno za redundansu i poređenje sa drugim jezicima |
| `--buckets`, `--flush-keys`, `--compress`, `--hash` | performanse; ne utiču na rezultat |

---

## 2) Izvedene mjere iz `entropy_*_stats.csv`

```bash
# Uslovna entropija H(n)-H(n-1) i serija blok-entropije
python3 $TK/compute_conditional_entropy.py  --input entropy_chars_stats.csv --output out/cond_chars.csv
python3 $TK/compute_block_entropy_series.py --input entropy_chars_stats.csv --output out/block_chars.csv

# Entropijska stopa: blok (H/n) i uslovna + dijagnostika uzorkovanja
python3 $TK/summarize_entropy_rate.py --input entropy_words_stats.csv --output out/rate_words.csv

# Energija / koncentracija (Onicescu, Rényi-2, Gini–Simpson, HHI)
python3 $TK/compute_energy_metrics.py --input entropy_words_stats.csv --output out/energy_words.csv
python3 $TK/compute_energy_metrics.py --input entropy_words_genres_97mb.csv --output out/energy_words_genres.csv

# Redundansa: |A| mora odgovarati inventaru nad kojim je računat H.
# entropy_chars_letters_stats.csv = map/reduce sa --letters-only --lowercase (|A| = 30 slova + razmak = 31)
python3 $TK/compute_redundancy_chars.py --input entropy_chars_letters_stats.csv \
        --output out/redundancy_chars.csv --alphabet-size 31 --rate conditional
```

Formule u `compute_energy_metrics.py` (iz dovoljnih statistika, bez ponovnog čitanja korpusa):

- Onicescu energija E = Σ p² = Σ c² / T²
- Rényi-2 H₂ = −log₂ E
- Gini–Simpson G = 1 − E
- normalizovani HHI = (E − 1/V) / (1 − 1/V)
- Shannon H₁ = log₂ T − Σ c log₂ c / T; Rényi-½ = 2 log₂ Σ √p

Stare kolone `E1_*`, `E05_*`, `E2_*` su zadržane radi kompatibilnosti (`--no-legacy` ih uklanja). **`E2_per_token` = Σc²/T nije Onicescu energija.**

---

## 3) Unigrami, Zipf, informacija po jedinici

```bash
python3 $TK/collect_unigram_counts.py --parts-dir parts_words --mode words --output out/unigrams_words.csv
python3 $TK/collect_unigram_counts.py --parts-dir parts_chars --mode chars --output out/unigrams_letters.csv \
        --letters-only --lowercase
python3 $TK/compute_zipf_from_unigrams.py   --input out/unigrams_words.csv --output out/zipf_words.csv
python3 $TK/compute_information_per_unit.py --input out/unigrams_words.csv --output out/info_words.csv
```

---

## 4) Heapsov zakon

Heaps se fituje na **rast jednog korpusa** (N od ~10³ do punog korpusa), ne na n-grame različitog reda niti na žanrove iste veličine. Skripta to sada provjerava i odbija fit ako je max(N)/min(N) < 10.

```bash
python3 $TK/make_heaps_snapshots.py --input data/clean/bosnian_corpus_all.txt \
        --output out/heaps_points_words.csv
python3 $TK/fit_heaps_law.py --input out/heaps_points_words.csv --mode words --output out/heaps_fit.csv
```

Ako je `map` rađen sa `--lowercase`, dodaj `--lowercase` i u `make_heaps_snapshots.py`.

---

## 5) Jensen–Shannon između žanrova

```bash
python3 $TK/compute_jsd_genres.py --mode words --inputs data/by_genre_97mb/*.txt \
        --output out/heat_jsd_words_97mb.csv --wide out/heat_jsd_words_97mb_matrix.csv
# ili iz gram,count fajlova (collect_unigram_counts.py po žanru):
python3 $TK/compute_jsd_genres.py --inputs out/unigrams_*.csv --output out/jsd.csv
```

Izlaz: `jsd_bits` (0–1) i `js_distance = sqrt(JSD)`, koja je prava metrika.

---

## Metodološke napomene (važno za tumačenje)

1. **Procjenitelj.** Sve entropije su MLE (plug-in) procjene i sistematski su pristrasne naniže, i to jače što je V/T veće.
2. **Zasićenje riječnih n-grama.** U globalnom korpusu je za riječi V/T = 0,47 (n=3), 0,74 (n=4) i 0,86 (n=5), a H(5) = 29,34 bita je blizu maksimuma log₂T = 29,81. Pad uslovne entropije za n ≥ 3 (5,06 → 2,10 → 0,68 bita) zato je posljedica konačnog uzorka, a ne jezički plato. `summarize_entropy_rate.py` to označava kolonama `saturation`, `types_per_token` i `reliable`.
3. **Definicija stope.** H(n)/n (blok) i H(n) − H(n−1) (uslovna) konvergiraju ka istoj stopi, ali različitom brzinom. Kod karaktera za n=8: 2,98 naspram 1,86 bita/znak. U radu treba navesti koja je korištena.
4. **Inventar karaktera.** Globalni chars unigrami imaju 2932 tipa (sva Unicode interpunkcija, cifre, strana slova). Za redundansu i poređenje s drugim jezicima koristi `--letters-only` i navedi |A|.
5. **Granice linija.** Default `map` spaja linije bez separatora i pušta n-grame preko granica dokumenata; vidi `--line-sep` i `--reset-context`.

### Referentne vrijednosti (unigrami, iz objavljenih CSV-ova)

| | T | V | H₁ [bit] | Onicescu E | H₂ [bit] | Gini–Simpson |
|---|---|---|---|---|---|---|
| karakteri | 5 013 889 571 | 2 932 | 4,4572 | 0,058339 | 4,0994 | 0,941661 |
| riječi | 938 196 277 | 5 035 194 | 12,6769 | 0,0052504 | 7,5733 | 0,994750 |

---

## Reproducibilnost i integritet

- Koristi isti release korpusa i ista pravila čišćenja/tokenizacije.
- Default opcije `ent.py` daju bit-identične rezultate kao verzija kojom su napravljeni objavljeni CSV-ovi.
- Kada koristiš Zenodo arhive, provjeri SHA-256 hash-sumove.

## Kako citirati

Citirati revidiranu englesku verziju rada, DOI [10.5281/zenodo.20804511](https://doi.org/10.5281/zenodo.20804511), i korpus, DOI [10.5281/zenodo.17757098](https://doi.org/10.5281/zenodo.17757098). Dugme „Cite this repository" na GitHubu koristi `CITATION.cff`.

## Izmjene (v1.1)

- `compute_energy_metrics.py`: dodani Onicescu E = Σc²/T², Rényi-2, Gini–Simpson, normalizovani HHI, Rényi-½, Hillovi brojevi
- `fit_heaps_law.py`: filtrira mode/n, odbija degenerisan raspon N, ispisuje SE i R²
- `summarize_entropy_rate.py`: uslovna stopa + dijagnostika zasićenja
- `compute_redundancy_chars.py`: uslovna stopa (default), uklonjena duplirana kolona `predictability`
- nove skripte: `compute_jsd_genres.py`, `make_heaps_snapshots.py`, `tokenize_common.py`
- `ent.py`: opt-in opcije `--line-sep`, `--reset-context`, `--letters-only` (default ponašanje nepromijenjeno)
- `collect_unigram_counts.py`: `--letters-only`, `--lowercase`
- `run_reduce_chars_parallel.sh`: ispravna bash skripta (ranije zalijepljena terminal sesija)
- README: komande usklađene sa stvarnim argumentima skripti; dodan engleski README (README.md) i DOI revidirane verzije rada
