# mst_smartnoise

MST runner backed by [smartnoise-synth](https://docs.smartnoise.org/synth/synthesizers/mst.html).
Internally uses Private-PGM.

## Setup

```bash
cd experiments/mst_smartnoise
uv init --python 3.11      # only if pyproject.toml not yet committed
uv add smartnoise-synth pandas scikit-learn matplotlib psutil memory-profiler pyyaml
uv sync
```

## Run

```bash
uv run python src/runner.py \
  --data ../shared/data/processed/adult.csv \
  --preprocessing-config ../shared/configs/preprocessing.yaml \
  --epsilon 1.0 \
  --seed 0 \
  --n-synth 30000 \
  --out results/
```

Outputs:
- `results/synth_mst_smartnoise_<eps>_<seed>.csv`
- `results/run_mst_smartnoise_<eps>_<seed>.json`

On failure the run JSON is still written with `status="failed"` and the exit code is 0
so the orchestrator loop continues.

## Caveats

- `snsynth` MST expects `categorical_columns` to be listed explicitly; we pass all columns
  since the shared preprocessor integer-encodes every column.
- `preprocessor_eps=0.0` disables snsynth's internal budget for domain inference because
  our shared preprocessor already produces a clean integer-encoded frame with a known domain.
- snsynth's `.sample()` returns a `DataFrame` (or ndarray in older versions); the wrapper
  normalizes to the original column order.
