# 再実行手順

本実験 (`docs/report.md`) を再現するための手順。詳細は [`docs/report.md` §6](report.md#6-再実行手順) を参照。

## 前提

- Python 3.11 と `uv` がインストール済み
- リポジトリ root: `/home/hatano/works/20260419-syntheticdata`
- ネットワーク到達 (UCI / PyPI / GitHub)

## 1. データ取得

```bash
mkdir -p experiments/shared/data/raw
curl -sL https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data \
  -o experiments/shared/data/raw/adult.data
python3 -c "
import pandas as pd
cols=['age','workclass','fnlwgt','education','education-num','marital-status','occupation','relationship','race','sex','capital-gain','capital-loss','hours-per-week','native-country','income']
df=pd.read_csv('experiments/shared/data/raw/adult.data',header=None,names=cols,skipinitialspace=True,na_values=['?'])
df.to_csv('experiments/shared/data/raw/adult.csv',index=False)
df.sample(5000,random_state=42).reset_index(drop=True).to_csv('experiments/shared/data/raw/adult_5k.csv',index=False)
"
```

## 2. 環境構築

```bash
# smartnoise-synth (deps を pin)
(cd experiments/mst_smartnoise && uv sync --python 3.11)

# private-pgm (mbi + MST 関数を追加取得)
(cd experiments/mst_private_pgm && uv sync --python 3.11 && \
 uv pip install "git+https://github.com/ryan112358/private-pgm.git@e9ea5fcac62e2c5b92ae97f7afe2648c04432564" disjoint-set "jax<0.5" "jaxlib<0.5")
curl -sL https://raw.githubusercontent.com/ryan112358/private-pgm/e9ea5fcac62e2c5b92ae97f7afe2648c04432564/mechanisms/mst.py \
  -o experiments/mst_private_pgm/src/mst.py
curl -sL https://raw.githubusercontent.com/ryan112358/private-pgm/e9ea5fcac62e2c5b92ae97f7afe2648c04432564/mechanisms/cdp2adp.py \
  -o experiments/mst_private_pgm/src/cdp2adp.py

# dpmm
(cd experiments/mst_dpmm && uv sync --python 3.11)
```

## 3. グリッド実行 (3 実装並列)

```bash
./run_grid.sh experiments/mst_smartnoise  > /tmp/grid_smartnoise.log 2>&1 &
./run_grid.sh experiments/mst_private_pgm > /tmp/grid_privpgm.log    2>&1 &
./run_grid.sh experiments/mst_dpmm        > /tmp/grid_dpmm.log       2>&1 &
wait
```

グリッド: epsilon ∈ {0.3, 1.0, 3.0} × seed ∈ {0, 1} = 6 runs/impl × 3 impls = 18 runs。
所要時間: fit ~4 min/run、3 並列で wall-clock ~25 min。

## 4. 集計・可視化

```bash
python3 experiments/shared/src/aggregate.py
python3 experiments/shared/src/visualize.py --results-dir results
```

出力:

- `results/summary.csv` — 主要指標の 1 行 / run
- `results/utility_metrics.csv` — TVD / JS / 下流タスク / 多様性
- `results/privacy_metrics.csv` — DCR / NNDR / exact match / MIA
- `results/performance_metrics.csv` — fit/sample 時間、ピークメモリ
- `results/plots/*.png` — 10 枚

## 5. トラブルシュート

- `ModuleNotFoundError: mbi` → 手順 2 の private-pgm git pin を忘れている
- `AssertionError: data must contain domain attributes` (smartnoise) → pandas が 2.x になっている。`pandas<2` pin を確認
- `AttributeError: module 'numpy.dtypes' has no attribute 'StringDType'` → jax 0.9.x が入っている。`jax<0.5` pin を確認
- smartnoise `Please install mbi with: pip install ...` → 手順 2 の uv pip install 追加が実行されていない
