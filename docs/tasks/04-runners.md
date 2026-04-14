# T04 3 実装 Runner 実装

## 目的
T02 で定義した共通 I/F を、3 ライブラリそれぞれに適用する wrapper/runner を作る。

## 成果物 (分岐 T04a/b/c)

### T04a smartnoise
- `experiments/mst_smartnoise/src/wrapper.py`
- `experiments/mst_smartnoise/src/runner.py`
- `experiments/mst_smartnoise/pyproject.toml`

### T04b tmlt.private_pgm
- `experiments/mst_private_pgm/src/wrapper.py`
- `experiments/mst_private_pgm/src/runner.py`
- `experiments/mst_private_pgm/pyproject.toml`

### T04c dpmm
- `experiments/mst_dpmm/src/wrapper.py`
- `experiments/mst_dpmm/src/runner.py`
- `experiments/mst_dpmm/pyproject.toml`

## 共通
- `runner.py` は CLI: `python runner.py --config CONFIG_YAML --epsilon E --seed S --out OUT_DIR`
- 失敗時は例外を catch して JSON に error 情報を残す
- fit / sample 時間、ピークメモリを `results/run_<ts>.json` に出力

## 完了条件
- 雛形がインポートエラー無しで書けている（ライブラリ未インストールでも構文は通る: ランタイムで ImportError を出す設計）
- `uv add` 手順が pyproject コメントに記載されている
