(.venv) halida@MacBookPro bosnian_corpus % cat > run_reduce_chars_parallel.sh << 'EOF'
#!/bin/zsh
PARTS_DIR="./parts_chars"
BUCKETS=64
TAG_FILE="bosnian_corpus_all.txt"
TAG_GENRE="all"

# 1) Paralelno pokreni 8 reduce procesa, po jedan za svaki n
for N in 1 2 3 4 5 6 7 8; do
  echo "Pokrećem reduce za n=$N ..."
  python3 ent.py reduce \
    --parts-dir "$PARTS_DIR" \
    --mode chars \
    --n $N \
    --buckets $BUCKETS \
    --out "./entropy_chars_n${N}.csv" \
    --tag-file "$TAG_FILE" \
    --tag-genre "$TAG_GENRE" &
done

# 2) Sačekaj da svi završe
wait

echo "Spajam rezultate u jedan CSV..."

# 3) Uzmi header iz prvog, ostale dodaj bez headera
head -n 1 entropy_chars_n1.csv > entropy_chars_stats.csv
for N in 1 2 3 4 5 6 7 8; do
  tail -n +2 "entropy_chars_n${N}.csv" >> entropy_chars_stats.csv
done

echo "Gotovo: entropy_chars_stats.csv"
EOF
