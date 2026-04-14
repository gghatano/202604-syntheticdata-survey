# T05 共通評価モジュール

## 目的
合成データに対し spec §10〜§13 の評価指標を横並びで算出する。

## 成果物 (分岐 T05a/b/c/d)

### T05a utility.py
- 単変量 TVD / JS Divergence
- 二変量平均・最大 TVD
- 相互情報量差分 / Cramér's V 差分
- 下流タスク評価（sklearn LogisticRegression / RandomForest）
- 多様性（ユニーク率, 希少カテゴリ再現率, カバレッジ）

### T05b privacy.py
- DCR / NNDR
- 完全一致件数・率
- 最近傍ベース簡易 MIA (ROC-AUC, advantage)
- 属性推定ベースライン比較

### T05c performance.py
- fit/sample 時間、ピークメモリ、失敗率集計

### T05d usability.py
- 1〜5 点採点フォーマット（YAML 入力 → CSV 出力）

## 共通
- 入力: `df_real`, `df_synth`, `domain`, `task_spec`
- 出力: `dict` または `pd.DataFrame`
- `experiments/shared/evaluation/__init__.py` で公開

## 完了条件
- 各関数が dummy DF で smoke test 通過
- 出力カラムが `results/*.csv` テンプレと整合
