# T07 可視化

## 目的
spec §16 の必須図・推奨図を matplotlib で生成し、スライド転記可能な PNG を `results/plots/` に出力する。

## 成果物
- `experiments/shared/src/visualize.py`
- `results/plots/` 配下の PNG

### 必須図
1. `utility_vs_epsilon.png` — 実装別 × epsilon の有用性推移
2. `privacy_vs_epsilon.png` — 同 安全性推移
3. `fit_time.png` — fit 時間比較 (box or bar)
4. `sample_time.png` — sample 時間比較
5. `utility_vs_privacy.png` — 散布図 (優劣ではなく適材適所)
6. `usability_table.png` — 実装容易性スコア表
7. `radar_overall.png` — 総合レーダーチャート

### 推奨図
- `univariate_error_heatmap.png`
- `bivariate_error_heatmap.png`
- `mia_roc.png`
- `exact_match_bar.png`
- `errors_summary.png`

## 完了条件
- ダミー CSV から全図が生成できる
- DPI 150 以上、フォント日本語対応 (IPA or fallback)
