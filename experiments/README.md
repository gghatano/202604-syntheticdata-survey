# Experiments

Shared scaffolding and three MST implementation subprojects for the synthetic-data comparison study (see `docs/spec.md`, v0.2).

## Layout

```
experiments/
  shared/           # common interface, preprocessing, evaluation, configs, orchestrator
  mst_smartnoise/   # smartnoise-synth runner
  mst_private_pgm/  # tmlt.private_pgm runner
  mst_dpmm/         # dpmm runner
```

Each `mst_*` subdir is an isolated `uv` project (per spec §6.3). The `shared/` tree is imported by runners via `PYTHONPATH`.

## Rerun (per spec §6.3)

From repo root, for each implementation subproject:

```bash
cd experiments/mst_smartnoise && uv sync && uv run python src/runner.py --epsilon 1.0 --seed 0 --output /tmp/out.json
cd experiments/mst_private_pgm && uv sync && uv run python src/runner.py --epsilon 1.0 --seed 0 --output /tmp/out.json
cd experiments/mst_dpmm      && uv sync && uv run python src/runner.py --epsilon 1.0 --seed 0 --output /tmp/out.json
```

## Orchestrate all runs

```bash
python experiments/shared/src/run_all.py \
  --base experiments/shared/configs/experiment_base.yaml \
  --epsilons experiments/shared/configs/epsilon_grid.yaml
```

Add `--dry-run` to emit stub rows without invoking runners. Outputs land in `results/` (summary.csv, per-metric csvs, failures.csv, raw/*.json).

## Visualize

```bash
python experiments/shared/src/visualize.py --summary results/summary.csv --out-dir results/plots
```

Runs on dummy data if `summary.csv` is missing, so the plot pipeline can be exercised immediately.

## Data

See `experiments/shared/data/README.md` for how to place the Adult CSV.
