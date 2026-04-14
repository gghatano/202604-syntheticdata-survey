# MST 3 実装 比較実験レポート (初回)

- 文書: docs/report.md  版: 0.1  実験実施日: 2026-04-14
- 仕様: [`docs/spec.md`](spec.md) v0.2
- タスク定義: [`docs/tasks/`](tasks/)

## 1. 実験概要

Python で利用可能な 3 種の MST ベース合成データ実装を、同一データ・同一前処理・同一条件で比較し、有用性・安全性・性能・実装容易性を評価した。

| ID | ライブラリ | 位置づけ | 内部実装 |
|---|---|---|---|
| A | `smartnoise-synth` 0.3.7 | 実務向けラッパ (OpenDP) | Private-PGM の MST を呼び出し |
| B | `private-pgm` (ryan112358, `mechanisms/mst.py` @ `e9ea5fc`) | 研究用リファレンス | 直接 mbi + カスタム MST |
| C | `dpmm` 0.1.9 (`dpmm.pipelines.mst.MSTPipeline`) | 研究/探索向けライブラリ | 独自実装 (内部 mbi) |

**実装名**は以降 `smartnoise` / `private_pgm` / `dpmm` と略記する。

### 1.1 データ

- UCI Adult (14 属性 + label `income`)
- 完全な 32,561 行からランダム 5,000 行サブサンプル (`adult_5k.csv`, seed=42) を使用
- 前処理は [`experiments/shared/src/preprocessing.py`](../experiments/shared/src/preprocessing.py) を 3 実装共通で適用
  - `fnlwgt` 削除
  - 数値列 5 本をビニング (age=10, education-num=5, capital-gain=5, capital-loss=5, hours-per-week=10)
  - `native-country` を Top-10 + `OTHER` に圧縮
  - 全列を整数エンコード
  - 前処理後のドメインサイズ合計: **95**

### 1.2 条件グリッド

- 実装: 3
- epsilon: **{0.3, 1.0, 3.0}** (spec §8.1 の 5 水準から中央 3 点を選択。fit コストを抑えるため縮小)
- seed: **{0, 1}** (spec §8.3 の 5 回から縮小)
- 生成件数: 元データと同数 (5000)
- delta: 1e-9
- 合計 runs: **18 / 18 成功 (失敗 0)**

### 1.3 環境

- Python 3.11 / uv 0.9
- 実装ごとに独立 venv (`experiments/mst_*/`) を `uv sync` で構築
- smartnoise は `smartnoise-synth` 単体では動かず、`private-pgm` の過去コミット・`disjoint-set`・`jax<0.5` を追加依存として pin 必要だった（§6 を参照）

## 2. 結果サマリ

### 2.1 平均値 (2 seed 平均)

| impl | eps | TVD (uni) | TVD (biv) | DCR | MIA AUC | fit (s) | sample (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| smartnoise | 0.3 | 0.0438 | 0.1109 | 0.1292 | 0.503 | 249.5 | 0.059 |
| smartnoise | 1.0 | 0.0147 | 0.0607 | 0.1079 | 0.506 | 243.5 | 0.068 |
| smartnoise | 3.0 | 0.0045 | 0.0434 | 0.1047 | 0.502 | 244.2 | 0.065 |
| private_pgm | 0.3 | 0.0454 | 0.1151 | 0.1310 | 0.503 | 240.5 | 0.001 |
| private_pgm | 1.0 | 0.0165 | 0.0672 | 0.1132 | 0.508 | 237.7 | 0.001 |
| private_pgm | 3.0 | 0.0055 | 0.0437 | 0.1048 | 0.508 | 234.8 | 0.001 |
| dpmm | 0.3 | 0.0405 | 0.1160 | 0.1334 | 0.510 | 302.0 | 0.050 |
| dpmm | 1.0 | 0.0151 | 0.0635 | 0.1117 | 0.500 | 297.0 | 0.042 |
| dpmm | 3.0 | 0.0053 | 0.0437 | 0.1062 | 0.508 | 302.2 | 0.041 |

### 2.2 下流タスク (holdout `income` 分類)

- 実データ学習ベースライン: accuracy = **0.836** (Logistic Regression)

| impl | eps | acc (synth→real holdout) | macro F1 |
|---|---:|---:|---:|
| smartnoise | 0.3 | 0.748 | 0.551 |
| smartnoise | 1.0 | 0.749 | 0.576 |
| smartnoise | 3.0 | 0.759 | 0.552 |
| private_pgm | 0.3 | 0.750 | 0.572 |
| private_pgm | 1.0 | 0.730 | 0.566 |
| private_pgm | 3.0 | 0.765 | 0.574 |
| dpmm | 0.3 | 0.744 | 0.525 |
| dpmm | 1.0 | 0.754 | 0.538 |
| dpmm | 3.0 | 0.764 | 0.600 |

### 2.3 メモリ (tracemalloc ピーク)

| impl | fit peak (MB) |
|---|---:|
| smartnoise | 50.0 |
| private_pgm | 4.7 |
| dpmm | 2.9 |

※ `tracemalloc` は Python allocator 経由の割り当てのみを追跡する。NumPy/ネイティブ層の割り当てはカウントされないため絶対値ではなく「挙動の桁」として参照すること。smartnoise で値が大きいのは snsql/snsynth のインポート時 Python オブジェクト量が多いことを反映。

## 3. 観点別考察

### 3.1 有用性

- 単変量 TVD・二変量 TVD ともに **3 実装の差は誤差程度** (eps=1.0 で TVD_uni 0.015±0.001)。同じ MST アルゴリズムを異なる API から呼び出していることと整合する。
- 下流タスク精度も 3 実装で ±0.03 以内に収まり、**epsilon を揃えれば実装による有用性差は事実上無い**。
- 期待どおり epsilon 増加で TVD は単調減少 (0.044 → 0.015 → 0.005)。

### 3.2 安全性

- **MIA (最近傍ベース) の ROC-AUC は全条件で 0.50〜0.51**、advantage は 0〜0.019。MST はここでの簡易 MIA では情報漏洩をほぼ示さない。
- DCR (hamming) は epsilon 増加に伴いわずかに縮む (0.133 → 0.105) が、これは「有用性向上により元分布に近づく」ことの副作用であり、個体単位の近接ではない。
- exact match rate は eps=0.3 で 7〜8%、eps=3.0 で 15〜17% に達する (Adult はビニング後の格子が粗いため元データに偶発一致しやすい)。これは合成レコードが元の特定個人をコピーしたというより「同じ `(階級, 教育, …)` セルに複数人が居る」ことを意味するが、**実運用では exact match の意味解釈に注意が必要**。

### 3.3 処理性能

- fit 時間: **private_pgm ≈ smartnoise (~240s) < dpmm (~300s)** で一貫。
  - dpmm は `MSTPipeline` の wrapping overhead (前処理 disable 時も内部で辞書ドメイン検証・compress 判定) で ~60s 遅い。
  - smartnoise は snsql/snsynth のインポート・変換処理が入るが、`preprocessor_eps=0.0` により実質は private-pgm の MST を直呼びとほぼ同等。
- sample 時間: **private_pgm が圧倒的に速い (~1ms)**、smartnoise/dpmm は ~50ms。private_pgm 版 wrapper は fit 時点で synthetic df を貯めて `sample()` は numpy 再サンプリングのみのため差が大きい。
- 安定性: 18/18 成功、タイムアウト・例外ゼロ。

### 3.4 実装容易性

| 項目 | smartnoise | private_pgm | dpmm |
|---|---:|---:|---:|
| pip/uv 導入 | 2 (私費 pin と追加 git dep 必要) | 3 (tmlt.private_pgm は MST を含まず、元祖 private-pgm の過去コミットを手動で取得) | 5 (`pip install dpmm` だけで MST を呼べた) |
| API の直感性 | 4 (`Synthesizer.create("mst", ...)`) | 2 (raw mbi を触る、MST 関数はリポジトリの mechanisms に埋まっている) | 4 (`MSTPipeline.fit/generate`) |
| ドメイン指定 | 3 (snsynth が自動推定、無効化に `preprocessor_eps=0.0` が必要) | 5 (`Domain` に明示) | 4 (dict で渡す) |
| ドキュメント | 3 (OpenDP docs は最低限) | 2 (README のみ、コミット参照が必要) | 2 (PyPI README のみ) |
| エラー追跡 | 2 (snsynth/mbi/jax の多層スタック) | 4 (ほぼ素の numpy + mbi) | 3 (パイプライン内部で epsilon 分配が隠れている) |
| **合計 (25 点満点)** | **14** | **16** | **18** |

### 3.5 将来拡張性

- **dpmm** は `MSTPipeline` と同形の `AIMPipeline` / `PrivBayesPipeline` を提供しており、spec で予定されている PrivBayes / AIM への拡張コストが最小。
- **private_pgm** は raw mbi を直接使うため理論側の改造 (カスタムクリーク選択、ノイズ付与変更) が最もやりやすい。研究用途向け。
- **smartnoise** はラッパとして固定化されており、内部アルゴリズムに手を入れるには上流フォークが必要。代わりに他の合成手法 (ctgan, mwem 等) を同 API で試せる利点がある。

## 4. 用途別推奨

| 用途 | 推奨 | 理由 | 注意点 |
|---|---|---|---|
| **短期 PoC** (動くものを最短で) | **dpmm** | 素の `pip install dpmm` → `MSTPipeline.fit/generate` で 5 行。内部で前処理・ドメイン推定まで面倒を見る | fit で ~20% 遅い、ブラックボックス寄り |
| **研究・改造** | **private_pgm (ryan112358)** | mbi を直接触れて MST 実装を読める。fit が最速クラス | MST を呼ぶには mechanisms/mst.py を手動取得する必要がある（パッケージに含まれない）|
| **継続評価基盤** | **dpmm** (次点: smartnoise) | AIM/PrivBayes/MST が同形 API。比較軸を増やすコストが最小。smartnoise は CTGAN 等と横並び比較できるが MST に関しては依存 pin が重い | dpmm は API 安定性がまだ流動的。version ピンを必須に |

spec §22 のフォーマットに沿うと:

- **PoC 向け**: dpmm
- **研究・理解向け**: private_pgm (ryan112358)
- **継続比較基盤向け**: dpmm (近い将来複数アルゴリズムを追加するなら)／smartnoise (MST 以外のメカニズムと横比較するなら)

## 5. 比較バイアスと注意点

1. **3 実装の有用性差がほぼゼロ**な主因は、全実装で同じ前処理済み整数エンコード DF とドメイン辞書を渡し、内部前処理を全て無効化したこと (`smartnoise: preprocessor_eps=0.0`, `dpmm: disable_processing=True`)。spec §21.1 が警告する「ドメイン定義と前処理の違い」が比較結果を汚染しないようブロックした。**逆に言えば、各ライブラリを「デフォルトで使ったとき」の性能は別問題**であり、導入容易性評価 (§3.4) で拾っている。
2. smartnoise は snsynth 単体では `mbi` / `disjoint-set` が解決できず、`private-pgm` の過去コミット (`e9ea5fc`) を手動 pin する必要があった。これは上流 snsynth が古い mbi API を参照しているためで、**素直な `pip install smartnoise-synth` だけでは MST が動かない**。現時点 (2026-04) でのリアルな導入コストを反映して §3.4 の導入スコアに減点した。
3. epsilon グリッドを {0.3, 1.0, 3.0} に縮小したため、spec §8.1 が指定する 0.1 / 10.0 の両端を検証できていない。特に eps=0.1 ではユーティリティが崩壊する領域のはずで、安全性との実質トレードオフ曲線を論じるには再実験が必要。
4. seed 数を 2 に縮小したため、標準偏差はあるものの有意差検定には不十分。eps ごとの差分が大きい指標 (TVD) では十分、有意差検定が必要な指標 (downstream_f1) では seed を増やしたい。
5. サブサンプル 5k rows を使用。フルデータ (32k) では fit 時間が比例しないことを smoke test で確認 (~250s) しているが、高次相関保持は n が大きいほど改善する傾向があるため絶対値の外挿は注意。
6. MIA AUC が 0.5 付近なのは「MST が安全」というより「simple NN ベースの MIA が弱すぎる」可能性がある。spec §11.3 の別種 MIA (holdout 区別ベース) の追加を推奨。

## 6. 再実行手順

1. Adult データ取得:
   ```bash
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
2. 環境構築 (3 実装):
   ```bash
   (cd experiments/mst_smartnoise && uv sync --python 3.11)
   (cd experiments/mst_private_pgm && uv sync --python 3.11 && \
     uv pip install "git+https://github.com/ryan112358/private-pgm.git@e9ea5fcac62e2c5b92ae97f7afe2648c04432564" disjoint-set "jax<0.5" "jaxlib<0.5")
   (cd experiments/mst_dpmm && uv sync --python 3.11)
   curl -sL "https://raw.githubusercontent.com/ryan112358/private-pgm/e9ea5fcac62e2c5b92ae97f7afe2648c04432564/mechanisms/mst.py" -o experiments/mst_private_pgm/src/mst.py
   curl -sL "https://raw.githubusercontent.com/ryan112358/private-pgm/e9ea5fcac62e2c5b92ae97f7afe2648c04432564/mechanisms/cdp2adp.py" -o experiments/mst_private_pgm/src/cdp2adp.py
   ```
3. グリッド実行:
   ```bash
   ./run_grid.sh experiments/mst_smartnoise  &
   ./run_grid.sh experiments/mst_private_pgm &
   ./run_grid.sh experiments/mst_dpmm        &
   wait
   ```
4. 集計・可視化:
   ```bash
   python3 experiments/shared/src/aggregate.py
   python3 experiments/shared/src/visualize.py --results-dir results
   ```
5. 出力: `results/{summary,utility_metrics,privacy_metrics,performance_metrics}.csv` と `results/plots/*.png`

## 7. 追加実験案

1. **epsilon 両端** (0.1, 10.0) を追加し、有用性崩壊と安全性低下のカーブを描く
2. **seed 5 本**に戻し、標準偏差バンドと有意差検定を出す
3. **フル 32k Adult** で同条件を再実行し、サブサンプルとの差分を確認
4. **別 MIA** (holdout 区別ベース、shadow モデル型) を追加し、安全性の見立てをクロスチェック
5. **PrivBayes / AIM 比較**: dpmm の同形 API 上で 3 アルゴリズムを同じ枠組みで回す (dpmm を基盤にした場合の最大の旨味)
6. **属性推定攻撃**: `income` を伏せて他列から推定する典型シナリオ
7. **カテゴリ・カーディナリティの感度**: top_k 切り詰めを外した場合の結果比較
