# mst_private_pgm

MST runner backed by `tmlt.private_pgm`.

## Setup

```bash
cd experiments/mst_private_pgm
uv init --python 3.11
uv add tmlt.private_pgm pandas scikit-learn matplotlib psutil memory-profiler pyyaml
```

## Run

```bash
uv run python src/runner.py \
  --data ../shared/data/processed/train.csv \
  --preprocessing-config ../shared/configs/preprocessing.yaml \
  --epsilon 1.0 \
  --seed 0 \
  --n-synth 10000 \
  --out results/
```

Outputs `synth_*.csv` and `run_*.json` into `--out`.
