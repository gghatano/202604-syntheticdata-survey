# Synthetic Data 比較実験リポジトリ

差分プライバシー付き表形式合成データ手法を、同一条件下で横並び比較するための実験基盤と結果を蓄積するリポジトリ。各実験は独立した `uv` 環境で走らせ、共通の前処理・評価・可視化モジュールで揃えて比較する。

---

## 1. 実験一覧

**完了した実験** のみここに記載する。未実施・計画中の実験は [GitHub Issues (label: experiment)](https://github.com/gghatano/202604-syntheticdata-survey/issues?q=is%3Aissue+label%3Aexperiment) で管理している。

| # | 実験名 | ステータス | 対象 | レポート | データ |
|---|---|---|---|---|---|
| 01 | MST 3 実装比較 (初回) | ✅ 完了 (2026-04-14) | smartnoise-synth / ryan112358 private-pgm / dpmm | [`docs/report.md`](docs/report.md) | UCI Adult 5k subsample, eps ∈ {0.3, 1.0, 3.0}, seed ∈ {0,1} |

### 候補実験 (Issue で管理)

| Issue | 実験名 | 優先度の目安 |
|---|---|---|
| [#4](https://github.com/gghatano/202604-syntheticdata-survey/issues/4) | exp02: epsilon 両端追加 + フル Adult 32k 再実験 | 後回し可 (01 の結論再確認になる可能性) |
| [#5](https://github.com/gghatano/202604-syntheticdata-survey/issues/5) | exp03: PrivBayes / AIM を加えた 3 アルゴリズム比較 | **推奨: 高** (共通基盤の旨味が最大) |
| [#6](https://github.com/gghatano/202604-syntheticdata-survey/issues/6) | exp04: 別データセット (Mushroom/Bank/Credit) での横展開 | 中 (exp03 後に推奨) |

新しい実験アイデアは Issue を立てて `experiment` ラベルを付ける。着手時に該当 Issue を "in progress" にし、完了したら実験一覧の表に行を追加して Issue を close する。

新しい実験を追加する際は、[§4 新規実験の受け入れ方針](#4-新規実験の受け入れ方針) と以下のドキュメント群を参照する:

- [`docs/process.md`](docs/process.md) — 実験の全体フロー (spec → tasks → 実装 → グリッド → 集計 → レビュー → report → PR)
- [`docs/templates/kickoff_checklist.md`](docs/templates/kickoff_checklist.md) — 新規実験キックオフ時のチェックリスト
- [`docs/templates/report_template.md`](docs/templates/report_template.md) — レポート雛形
- [`docs/review.md`](docs/review.md) — 7 観点の独立レビューエージェント (`.claude/agents/review-*`) の運用手順
- [`docs/spec.md`](docs/spec.md) — 比較実験の仕様書 v0.2

---

## 2. ディレクトリ構成

```text
.
├── README.md              ← このファイル (実験索引)
├── .claude/
│   └── agents/            レビューエージェント定義 (7 観点)
│       ├── review-experiment-execution.md
│       ├── review-interpretation.md
│       ├── review-experiment-management.md
│       ├── review-config-management.md
│       ├── review-documentation.md
│       ├── review-test-quality.md
│       └── review-uiux-quality.md
├── docs/
│   ├── spec.md            仕様書 v0.2 (比較方針・評価指標・受入基準)
│   ├── process.md         実験の全体フロー (spec→tasks→実装→グリッド→レビュー→report)
│   ├── review.md          レビューエージェントの運用手順
│   ├── templates/
│   │   ├── report_template.md       レポート雛形
│   │   └── kickoff_checklist.md     新規実験キックオフ時のチェックリスト
│   ├── tasks/             spec を 8 タスクに分解したタスク定義
│   │   ├── README.md      タスク一覧と依存グラフ
│   │   ├── 01-investigation.md       T01 実装調査
│   │   ├── 02-common-interface.md    T02 共通 I/F 設計
│   │   ├── 03-preprocessing.md       T03 共通前処理
│   │   ├── 04-runners.md             T04 3 実装 Runner
│   │   ├── 05-evaluation.md          T05 共通評価モジュール
│   │   ├── 06-experiment-execution.md T06 実験実行・ログ収集
│   │   ├── 07-visualization.md       T07 可視化
│   │   └── 08-report.md              T08 考察・レポート
│   ├── report.md          実験 01 のレポート (考察・用途別推奨)
│   └── rerun.md           実験 01 の再実行手順
│
├── experiments/
│   ├── README.md          実験ディレクトリ全体のメモ
│   ├── shared/            ← 3 実装で共通のコード (横展開の土台)
│   │   ├── configs/
│   │   │   ├── experiment_base.yaml    実験グリッドの基底設定
│   │   │   ├── epsilon_grid.yaml       epsilon 候補
│   │   │   └── preprocessing.yaml      データセット別の前処理ルール
│   │   ├── data/
│   │   │   └── README.md               データセット入手方法
│   │   ├── src/
│   │   │   ├── interface.py            BaseSynthesizer / FitConfig / FitResult
│   │   │   ├── preprocessing.py        共通前処理 (ビニング・top-K・整数エンコード)
│   │   │   ├── run_all.py              (参考実装、実運用は run_grid.sh を使用)
│   │   │   ├── aggregate.py            per-run JSON → results/*.csv 集計
│   │   │   ├── visualize.py            results/plots/*.png 生成
│   │   │   └── baseline.py             real↔real baseline 計算 (安全性指標の解釈基準)
│   │   └── evaluation/
│   │       ├── utility.py              TVD / JS / MI / 下流タスク / 多様性
│   │       ├── privacy.py              DCR / NNDR / exact match / NN-MIA / 属性推定
│   │       ├── performance.py          時間・メモリ集計
│   │       └── usability.py            半定性スコア入出力
│   │
│   ├── mst_smartnoise/    ← 実装 A: smartnoise-synth
│   │   ├── pyproject.toml              uv 依存定義 (mbi/jax/pandas pin あり)
│   │   ├── README.md                   セットアップと注意点
│   │   ├── src/{wrapper.py, runner.py}
│   │   └── results/run_*.json          per-run メタ
│   ├── mst_private_pgm/   ← 実装 B: ryan112358 private-pgm の MST を手動取得
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/{wrapper.py, runner.py, mst.py, cdp2adp.py}
│   └── mst_dpmm/          ← 実装 C: dpmm.pipelines.mst.MSTPipeline
│       ├── pyproject.toml
│       ├── README.md
│       └── src/{wrapper.py, runner.py}
│
├── results/               ← 実験横断の集計 CSV と可視化 PNG
│   ├── summary.csv                主要指標 1 行/run
│   ├── utility_metrics.csv        有用性指標詳細
│   ├── privacy_metrics.csv        安全性指標詳細
│   ├── performance_metrics.csv    時間・メモリ・失敗状況
│   └── plots/                     必須図 10 枚 (§3 参照)
│
└── run_grid.sh            3 実装 × epsilon × seed を回す最小オーケストレータ
```

---

## 3. 実験 01 の成果物の場所

| 知りたいこと | 見るファイル |
|---|---|
| 実験の設計思想と比較観点 | [`docs/spec.md`](docs/spec.md) §3〜§13 |
| 実装差分の比較・用途別推奨 | [`docs/report.md`](docs/report.md) §2〜§4 |
| 結論 (PoC / 研究 / 継続基盤 の推奨) | [`docs/report.md`](docs/report.md) §4 |
| どこがバイアス要因か | [`docs/report.md`](docs/report.md) §5 |
| 再実行コマンド | [`docs/rerun.md`](docs/rerun.md) |
| 指標生値 (1 行/run) | `results/summary.csv` |
| 有用性詳細 (TVD/JS/MI/下流タスク) | `results/utility_metrics.csv` |
| 安全性詳細 (DCR/exact/MIA) | `results/privacy_metrics.csv` |
| 時間・メモリ | `results/performance_metrics.csv` |
| 可視化 (必須 10 枚) | `results/plots/*.png` — `utility_vs_epsilon` / `bivariate_vs_epsilon` / `privacy_dcr_vs_epsilon` / `privacy_mia_vs_epsilon` / `fit_time` / `sample_time` / `peak_memory` / `utility_vs_privacy` / `radar_overall` / `downstream_acc` |
| 各 run の生ログ | `experiments/mst_*/results/run_*.json` (ビニングされた synth_*.csv は `.gitignore`) |
| 共通 I/F と前処理の実装 | `experiments/shared/src/{interface,preprocessing}.py` |
| 評価指標の実装 | `experiments/shared/evaluation/{utility,privacy,performance,usability}.py` |

---

## 4. 新規実験の受け入れ方針

追加実験を走らせる際は、**原則として既存の共通基盤を壊さず差分だけを足す**。

### 4.1 命名と配置

- 新しい合成アルゴリズムを足す場合: `experiments/<algo>_<library>/` を作る (例: `experiments/aim_dpmm/`)。
- 同じアルゴリズムで条件だけ変える場合 (例: eps 両端追加・フルデータ再実験): 実験 ID をコミットメッセージと `docs/report_<nn>.md` に書き、`run_grid.sh` を複製または `--config` 引数を足す。
- 別データセットで同じアルゴリズムを比較: `experiments/shared/configs/preprocessing.yaml` に新規エントリを追加し、`run_grid.sh` の `--dataset` 引数で切替。

### 4.2 共通基盤を更新するとき

- `experiments/shared/src/interface.py` の `FitConfig`/`FitResult` に新フィールドを足すときはデフォルト値必須（既存 3 runner を壊さない）
- 評価指標を増やすときは `evaluation/*.py` にまず純関数で追加 → `aggregate.py` に組み込む → `visualize.py` にプロットを追加 の順
- `preprocessing.py` のルールを壊す変更は全実験の再計算が必要になるため、明示的に別関数にするか、YAML の `version` キーで切替

### 4.3 レポート

- 実験ごとに `docs/report_<nn>_<shortname>.md` を作成し、本 README の実験一覧に行を追加する (`docs/report.md` は実験 01 専用として残す)
- テンプレートは [`docs/templates/report_template.md`](docs/templates/report_template.md) を使う
- 再実行手順は `docs/rerun.md` に追記するか、規模が大きければ `docs/rerun_<nn>.md` に分離

### 4.4 レビュー

- report 執筆後・PR 作成前に 7 観点の独立レビューエージェントを起動する (詳細 [`docs/review.md`](docs/review.md))
- 観点: 実験実行 / 結果解釈 / 実験管理 / 構成管理 / ドキュメント / テスト品質 / UI-UX 品質
- すべて `.claude/agents/review-*.md` に定義済みで、Task ツールから `subagent_type=review-<name>` で並列起動可能

### 4.5 結果ファイル

- `results/` 直下は「最新実験の集計」と位置づけ、実験ごとのアーカイブは `results/archive/<YYYYMMDD>_<nn>/` にコピーしてから新しい実験を流す
- プロット PNG も同じポリシー

---

## 5. クイックスタート (実験 01 の再実行)

[`docs/rerun.md`](docs/rerun.md) を参照。概略:

```bash
# 1. データ取得 (UCI Adult → 5k subsample)
# 2. 3 実装の環境構築 (uv sync + 追加 pin)
# 3. ./run_grid.sh を 3 実装並列で実行
# 4. python3 experiments/shared/src/aggregate.py
# 5. python3 experiments/shared/src/visualize.py --results-dir results
```

所要時間: wall-clock 約 25 分 (fit が 4 分/run × 6 runs/impl、3 impl 並列)。
