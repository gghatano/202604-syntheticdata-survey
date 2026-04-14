#!/usr/bin/env bash
set -e
# Usage: run_grid.sh <impl_dir>
# Runs MST on Adult 5k subsample across eps × seed grid.
IMPL_DIR="$1"
DATA=../shared/data/raw/adult_5k.csv
CFG=../shared/configs/preprocessing.yaml
OUT=results
N_SYNTH=5000

cd "$IMPL_DIR"
mkdir -p "$OUT"
for EPS in 0.3 1.0 3.0; do
  for SEED in 0 1; do
    echo "[$(basename $IMPL_DIR)] eps=$EPS seed=$SEED"
    uv run --python 3.11 python src/runner.py \
      --data "$DATA" --preprocessing-config "$CFG" \
      --epsilon "$EPS" --seed "$SEED" --n-synth "$N_SYNTH" --out "$OUT" \
      2>&1 | tail -3
  done
done
echo "[$(basename $IMPL_DIR)] done"
