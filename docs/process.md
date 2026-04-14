# 実験プロセスガイド

実験 01 (MST 3 実装比較) で実際に通ったワークフローを再利用可能な形に整理したもの。次の実験 (PrivBayes / AIM / 別データセットなど) ではこのガイドに沿って進める。

## 全体フロー

```
spec.md (仕様)
   ↓
docs/tasks/ (タスク分解)
   ↓
┌─────────────────────────────┐
│ shared 基盤 (T02/T03/T05)    │ ← 既存を流用できれば差分追加のみ
│  interface / preprocessing   │
│  evaluation / aggregate      │
│  visualize / baseline        │
└─────────────────────────────┘
   ↓
experiments/<impl>/ per 実装 (T04)
   wrapper.py + runner.py + pyproject.toml
   ↓
uv sync + smoke test (1 run per impl)
   ↓
run_grid.sh (T06)   ← 3 impl 並列実行
   ↓
aggregate.py (T06)  ← results/*.csv 集計
   ↓
visualize.py (T07)  ← results/plots/*.png 生成
   ↓
独立レビュー (研究観点 + エンジニア観点)
   ↓
report.md (T08) ← テンプレ docs/templates/report_template.md
   ↓
feature ブランチで PR
```

---

## フェーズ 1: 仕様読解とタスク分解

**入力**: `docs/spec.md` (または追補)
**出力**: `docs/tasks/` (または `docs/tasks_<nn>/`) の 8 タスク分解

### やること
1. spec の評価観点・指標・受入基準を洗い出す
2. 既存 `docs/tasks/` との差分を特定 (既存を流用できる範囲を決める)
3. 新規タスクごとに `NN-<name>.md` を作成。各ファイルには以下を必ず含める:
   - 目的 (1 行)
   - 成果物 (ファイルパス)
   - 完了条件 (チェック可能な形)
   - 依存 (他タスク ID)

### よくある落とし穴
- spec が「評価指標」を挙げていても「計算方法」は書いてないことが多い。**T05 の段階で計算式と参照実装を 1 行で固定する**
- 前処理の「ドメイン定義」が実装差になる (spec §21.1 が最大の警告)。**T03 で前処理済み DF とドメイン辞書を共通化する**

---

## フェーズ 2: shared 基盤の準備

**場所**: `experiments/shared/`
**既存実装**: interface/preprocessing/evaluation/aggregate/visualize は実験 01 で揃っているため、**次実験では差分追加のみ** が原則。

### 共通インターフェース (`experiments/shared/src/interface.py`)
```python
@dataclass
class FitConfig:
    epsilon: float
    domain: dict[str, int] = field(default_factory=dict)
    categorical_columns: list[str] = field(default_factory=list)
    delta: float = 1e-9
    seed: int = 0
    timeout_sec: int = 1800

@dataclass
class FitResult:
    elapsed_sec: float = 0.0
    peak_memory_mb: float = 0.0
    model_info: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

class BaseSynthesizer(ABC):
    def fit(self, df, config) -> FitResult: ...
    def sample(self, n, seed) -> pd.DataFrame: ...
    def get_metadata(self) -> dict: ...
```

### 共通前処理 (`experiments/shared/src/preprocessing.py`)
- `preprocess(df, rules)` が **`(df_int, domain, encoders)`** を返す
- ルールは YAML で管理: `experiments/shared/configs/preprocessing.yaml`
- 新データセットを足すときは YAML に 1 エントリ追加するだけ

### 評価モジュール (`experiments/shared/evaluation/`)
- `utility.py`: TVD / JS / bivariate TVD / MI diff / downstream task / diversity
- `privacy.py`: DCR / NNDR / exact match / NN-MIA / attribute inference
- `performance.py`: fit/sample 時間・メモリの集計
- `usability.py`: 半定性スコアの入出力

### 差分を加えるとき
- **新指標**: まず `evaluation/*.py` に純関数で追加 → `aggregate.py` に組み込む → `visualize.py` にプロット追加 の順
- **`FitConfig`/`FitResult` の拡張**: 新フィールドは **デフォルト値必須**。既存 runner を壊さない
- **前処理ルール破壊的変更**: 別関数にするか、YAML に `version` キーを付けて切替

---

## フェーズ 3: 実装ごとの Runner 作成

**場所**: `experiments/<algo>_<library>/`
**雛形**: 実験 01 の `experiments/mst_smartnoise/`, `mst_private_pgm/`, `mst_dpmm/` を参照

### 最小構成
```
experiments/<algo>_<library>/
├── pyproject.toml     # uv の依存定義 (override-dependencies で pin)
├── README.md          # セットアップと注意点
├── src/
│   ├── wrapper.py     # BaseSynthesizer を継承した薄ラッパ
│   └── runner.py      # CLI (--data --preprocessing-config --epsilon --seed --n-synth --out --dataset)
└── results/
    └── .gitkeep
```

### wrapper.py の契約
- `fit(df_preprocessed, config)` は **整数エンコード済み DF とドメイン辞書** を受け取る
- ライブラリ固有の内部前処理は全て無効化する (例: `snsynth: preprocessor_eps=0.0`, `dpmm: disable_processing=True`)
- `tracemalloc.start()` → `time.perf_counter()` で計測、`FitResult` に詰めて返す

### runner.py の契約
- CLI 引数は 3 実装で統一 (`experiments/mst_*/src/runner.py` を参照)
- 出力は `<out>/synth_<tag>.csv` と `<out>/run_<tag>.json`
- JSON には `impl, epsilon, seed, elapsed_fit, elapsed_sample, peak_mem_mb, n_synth, status, error?, traceback?` を含める
- **例外は catch して status=failed で JSON に書き、exit 0** (オーケストレータを止めない)

---

## フェーズ 4: 環境構築と Smoke Test

### 環境構築
```bash
cd experiments/<algo>_<library>
uv sync --python 3.11
```

### 依存衝突が出たら
1. **pyyaml 5.4.1 ビルド失敗** → `pyproject.toml` の `[tool.uv].override-dependencies` に `"pyyaml>=6"` を追加
2. **numpy / pandas のバージョン衝突** → 同じ override で `numpy<2`, `pandas<2` を pin
3. **上流が削除された API を参照** (snsynth ← mbi の例) → コミット SHA で過去版を pin: `"<pkg> @ git+<url>@<sha>"`
4. **jax 新版が numpy>=2 を要求** → `jax<0.5`, `jaxlib<0.5` を pin

### Smoke Test
```bash
uv run python src/runner.py \
  --data ../shared/data/raw/<dataset>_5k.csv \
  --preprocessing-config ../shared/configs/preprocessing.yaml \
  --epsilon 1.0 --seed 0 --n-synth 2000 --out results
cat results/run_*.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['status'], d.get('error','')[:200])"
```
**status が `ok` になるまで次フェーズに進まない**。traceback を JSON で受け取れるので、デバッグしやすい。

---

## フェーズ 5: グリッド実行

### run_grid.sh
```bash
#!/usr/bin/env bash
set -e
IMPL_DIR="$1"
DATA=../shared/data/raw/<dataset>_5k.csv
CFG=../shared/configs/preprocessing.yaml
OUT=results
N_SYNTH=5000
cd "$IMPL_DIR"
for EPS in 0.3 1.0 3.0; do
  for SEED in 0 1; do
    uv run --python 3.11 python src/runner.py \
      --data "$DATA" --preprocessing-config "$CFG" \
      --epsilon "$EPS" --seed "$SEED" --n-synth "$N_SYNTH" --out "$OUT"
  done
done
```

### 3 実装並列実行
```bash
./run_grid.sh experiments/<algo>_A > /tmp/grid_A.log 2>&1 &
./run_grid.sh experiments/<algo>_B > /tmp/grid_B.log 2>&1 &
./run_grid.sh experiments/<algo>_C > /tmp/grid_C.log 2>&1 &
wait
```

### 所要時間の見積もり
- 実験 01 実績: fit ~240s/run × 6 runs/impl × 3 並列 = wall-clock ~25 min
- 新しいアルゴリズムでは **まず 1 impl × 1 条件で実時間を計測** してから倍率を決める

---

## フェーズ 6: 集計

```bash
python3 experiments/shared/src/aggregate.py
```

**出力** (デフォルト `results/`):
- `summary.csv` — 1 行 / run、主要指標のみ
- `utility_metrics.csv` — 有用性指標詳細
- `privacy_metrics.csv` — 安全性指標詳細
- `performance_metrics.csv` — 時間・メモリ・失敗状況

`aggregate.py` は `experiments/mst_*/results/{run,synth}_*.json|csv` を読み込む。実装ディレクトリ名が変わる場合は冒頭の `IMPLS = [...]` を差し替える。

---

## フェーズ 7: 可視化

```bash
python3 experiments/shared/src/visualize.py --results-dir results
```

必須図 10 枚を生成 (`results/plots/`):
- `utility_vs_epsilon.png`
- `bivariate_vs_epsilon.png`
- `privacy_dcr_vs_epsilon.png`
- `privacy_mia_vs_epsilon.png`
- `fit_time.png`
- `sample_time.png`
- `peak_memory.png`
- `utility_vs_privacy.png`
- `radar_overall.png`
- `downstream_acc.png`

**新しい指標を足したら** `visualize.py` に `_line` / `_bar` / `_scatter` の呼び出しを追加する。

---

## フェーズ 8: 独立レビュー

report を書く **前** に、研究観点とエンジニア観点から独立にレビューを受ける。実験 01 では Claude の general-purpose agent を 1 本呼んで以下のプロンプトで回した:

```
You are doing an independent review of {REPORT_PATH} from two angles combined:

(a) A {DOMAIN} researcher: does the report make claims that are
    technically imprecise or unsupported? Are there standard metrics or
    caveats missing that a reviewer would flag?

(b) A research engineer who will rerun this in 3 months: is there
    anything that would make reproduction hard, or that hides important
    context (versions, seeds, randomness, data provenance, edge cases,
    error handling)?

Deliverables — reply in Japanese, under 400 words, as a bullet list
grouped by: 研究観点 / エンジニア観点、各指摘に「すぐ直せる / 次の実験で対応」を付ける。
```

返ってきた指摘を report に反映する。

---

## フェーズ 9: レポート執筆

**テンプレ**: [`docs/templates/report_template.md`](templates/report_template.md) をコピーして `docs/report_<nn>_<shortname>.md` として編集。

**必須節**:
- §0 エグゼクティブサマリ (1 行結論 + 主要数値表 + 代表図)
- §1 背景・設計 (手法説明 / データ / 前処理意図 / 条件 / 環境 / 上流バグ)
- §2 評価方法 (観点→指標→意味→方向)
- §3 結果 (平均 ± SD)
- §4 観点別考察
- §5 用途別推奨
- §6 比較バイアスと注意点
- §7 追加実験案
- §8 再実行手順

---

## フェーズ 10: PR

**main 直コミットは hook で禁止**。必ず feature ブランチから PR:

```bash
git checkout -b feat/exp<nn>-<shortname>
git add <files>
git commit -m "exp<nn>: ..."
git push -u origin feat/exp<nn>-<shortname>
# GitHub UI で PR 作成 (出力される URL を参照)
```

---

## チートシート: 新実験を始めるときに見るファイル

1. [`docs/templates/kickoff_checklist.md`](templates/kickoff_checklist.md) — 手順チェックリスト
2. [`docs/templates/report_template.md`](templates/report_template.md) — レポート雛形
3. [`docs/process.md`](process.md) — 本ドキュメント (このファイル)
4. [`README.md`](../README.md) §4 — 新規実験の受け入れ方針
5. [`docs/report.md`](report.md) — 実験 01 の完成例
