# mst_dpmm

MST runner using the `dpmm` library.

Per spec section 4.3, `dpmm` requires Python 3.10 or 3.11. This project pins `>=3.11,<3.12`.

## Setup

```bash
cd experiments/mst_dpmm
uv init --python 3.11
uv add dpmm pandas scikit-learn matplotlib psutil memory-profiler pyyaml
```

## Run

```bash
uv run python src/runner.py \
  --data path/to/data.csv \
  --preprocessing-config path/to/preprocess.yaml \
  --epsilon 1.0 \
  --seed 0 \
  --n-synth 10000 \
  --out results/
```

Outputs `synth_<tag>.csv` and `run_<tag>.json` under `--out`.
