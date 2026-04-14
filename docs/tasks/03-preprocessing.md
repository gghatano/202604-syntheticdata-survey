# T03 共通前処理 & ドメイン定義

## 目的
比較バイアスの最大要因である前処理差を排除するため、3 実装に同一の前処理済みデータとドメイン辞書を渡せるようにする。

## 成果物
- `experiments/shared/src/preprocessing.py`
  - `load_raw(name) -> pd.DataFrame`
  - `preprocess(df, rules) -> (df_processed, domain)`
  - 連続値ビニング / 欠損カテゴリ化 / 整数エンコード / 高カーディナリティ列 Top-K 圧縮
- `experiments/shared/configs/preprocessing.yaml`
  - 列型、ビン数、欠損処理方針
- `experiments/shared/src/split.py`
  - train / holdout 分割 (seed 固定)
- `experiments/shared/data/README.md` にデータ入手方法

## 推奨データセット候補
- UCI Adult (列数14, カテゴリ中心, 分類ラベル有)
- UCI Mushroom
- 既存の社内検証表 (あれば)

初期は **Adult** をデフォルトとする。

## 完了条件
- サンプル DataFrame に対して preprocess が domain 辞書と整数エンコード後 DF を返す
- doctest or 簡易 unit test
