# T06 実験実行・ログ収集

## 目的
条件グリッド（impl × epsilon × seed）をループ実行し、結果を CSV に集約する。

## 成果物
- `experiments/shared/src/run_all.py`
  - 設定 YAML 読込
  - 3 runner を subprocess で呼ぶ（環境分離のため）
  - タイムアウト (fit 30分 / sample 10分)
  - 失敗時のリトライ無し、failure CSV へ記録
- `experiments/shared/configs/experiment_base.yaml`
- `experiments/shared/configs/epsilon_grid.yaml` (0.1, 0.3, 1.0, 3.0, 10.0)
- 出力:
  - `results/summary.csv`
  - `results/utility_metrics.csv`
  - `results/privacy_metrics.csv`
  - `results/performance_metrics.csv`
  - `results/failures.csv`

## 完了条件
- dry-run モードで stub runner を回せる
- 5 seed × 5 epsilon × 3 impl = 75 条件を記述可能
