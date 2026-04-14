# 新規実験 キックオフチェックリスト

新しい実験 (別アルゴリズム/別データセット/追加条件) を始めるときの短いチェックリスト。詳細は [`docs/process.md`](../process.md) を参照。

## Before code: 準備

- [ ] この実験の **目的 1 行** を書けるか (報告時の結論の型)
- [ ] 既存の `docs/spec.md` で足りるか、追補が必要か
- [ ] 実験 ID (次の nn) を決めた
- [ ] 結果を格納するディレクトリ命名を決めた
  - 新アルゴリズム: `experiments/<algo>_<library>/`
  - 同アルゴで条件違い: `experiments/<existing>/` を流用 + `run_grid_<nn>.sh`
  - 新データセット: `experiments/shared/configs/preprocessing.yaml` に 1 エントリ追加
- [ ] **既存 shared 基盤で不足する指標・前処理を列挙**した
- [ ] 計算コスト見積もり (1 run あたり / グリッド合計 / 並列度)

## タスク分解

- [ ] `docs/tasks/` (または `docs/tasks_<nn>/`) に新タスクを追加
- [ ] 各タスクに成果物パスと完了条件を書いた
- [ ] 既存タスクを流用する部分を明示

## shared 基盤の差分

- [ ] `FitConfig`/`FitResult` に新フィールド必要か (あれば **デフォルト値を必須に**)
- [ ] 新指標を `evaluation/*.py` に純関数で追加
- [ ] `aggregate.py` の集計出力カラムを拡張
- [ ] `visualize.py` の plot 追加
- [ ] `preprocessing.yaml` のデータセットエントリ

## Runner 実装

- [ ] `wrapper.py` が `BaseSynthesizer` を継承
- [ ] ライブラリ内部前処理を**無効化**している (比較公平性の最重要要件)
- [ ] `tracemalloc.start()` → 計測 → `FitResult` に詰める
- [ ] `runner.py` の CLI 引数が既存 3 runner と揃っている
- [ ] 例外は catch して JSON に status=failed で書き、exit 0

## 環境構築

- [ ] `pyproject.toml` に依存追加
- [ ] `uv sync --python 3.11` 成功
- [ ] 依存衝突 (pyyaml / numpy / pandas / jax 等) は `override-dependencies` で pin
- [ ] 上流バグ/vendoring があれば `src/` 内に commit SHA 付きで取得

## Smoke test

- [ ] 1 run で status=ok の JSON が出る
- [ ] synth CSV が期待列数で出力される
- [ ] fit 時間の実測値をメモ (グリッド計算コスト見積もりのため)

## グリッド実行

- [ ] `run_grid.sh` を作成 or 流用
- [ ] 3 並列 or 直列を決定 (CPU 競合ノイズ vs 時間)
- [ ] 開始前に results/ を退避 (または新しい実験 ID のディレクトリに出力)

## 集計・可視化

- [ ] `aggregate.py` 実行 → `results/*.csv`
- [ ] `visualize.py` 実行 → `results/plots/*.png`
- [ ] `results/archive/<YYYYMMDD>_<nn>/` に前実験をコピー (混ぜない)

## レビュー

report を書く**前**に、以下のレビューを受ける (`.claude/agents/` に整備済み):

- [ ] `review-experiment-execution` — 実験条件・実行・再現性
- [ ] `review-interpretation` — 結果解釈の妥当性
- [ ] `review-experiment-management` — 実験管理・命名・ID 追跡
- [ ] `review-config-management` — 設定ファイル・pin・版管理
- [ ] `review-documentation` — ドキュメント構造と可読性
- [ ] `review-test-quality` — テスト/smoke test/失敗時のハンドリング
- [ ] `review-uiux-quality` — CLI/プロット/表の UX (該当する場合)

起動例:
```
Task (subagent_type=review-experiment-execution): "Review docs/report_<nn>.md from the experimental-execution angle"
```
詳細は [`docs/review.md`](../review.md)

## レポート

- [ ] `docs/templates/report_template.md` をコピー → `docs/report_<nn>_<name>.md`
- [ ] §0 エグゼクティブサマリ埋め済み (1 行結論・主要数値・代表図)
- [ ] §2 評価方法で指標の**意味**を書いた (ただ列挙ではなく)
- [ ] §6 バイアス節で抜け漏れチェックリストを真に満たしている
- [ ] レビューエージェントの指摘を反映 (すぐ直せる分)

## PR

- [ ] feature ブランチ (`feat/exp<nn>-<name>`) を切る
- [ ] `main` 直コミットは hook で禁止されている点を確認
- [ ] コミットメッセージに実験 ID と主要変更点
- [ ] `README.md` §1 の実験一覧表に新しい行を追加
- [ ] `git push -u origin <branch>` → PR 作成
