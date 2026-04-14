# MST 3 実装 比較実験レポート (初回)

- 文書: docs/report.md  版: 0.2  実験実施日: 2026-04-14
- 仕様: [`docs/spec.md`](spec.md) v0.2
- タスク定義: [`docs/tasks/`](tasks/)

---

## 0. エグゼクティブサマリ

差分プライバシー (DP) 付き表形式合成データのアルゴリズム **MST (Maximum Spanning Tree)** を実装した Python パッケージ 3 種を、同一データ・同一前処理・同一評価指標で比較した。

**結論 (一行)**: 前処理を揃えれば 3 実装の有用性・安全性はほぼ同等で、**差が出るのは導入コストと API の使い勝手**。用途別には PoC なら `dpmm`、研究改造なら `ryan112358/private-pgm`、継続比較基盤なら `dpmm` を推奨する。

### 主要数値 (eps=1.0 の 2 seed 平均)

| impl | TVD uni | TVD biv | exact match | MIA AUC | fit (s) | sample (s) | 導入手間 |
|---|---:|---:|---:|---:|---:|---:|---|
| smartnoise | 0.015 | 0.061 | 14% | 0.506 | 244 | 0.07 | **重** (mbi/jax を手動 pin) |
| private_pgm | 0.017 | 0.067 | 14% | 0.508 | 238 | 0.001 | 中 (`mst.py` を手動取得) |
| dpmm | 0.015 | 0.064 | 14% | 0.500 | 297 | 0.04 | **軽** (`pip install dpmm` のみ) |

※ 実データ holdout↔train の **exact match ベースライン自体が 21%** (Adult をビニングした粗い格子の必然)。synth の 7–17% はこれより低い ≒「元データをコピーしているのではなく、同じセルに複数人が居る」ことの反映。詳細は §3.2。

### 一枚だけ見るなら
`results/plots/utility_vs_privacy.png` — 横軸 univariate TVD (小さい=有用)、縦軸 DCR (大きい=安全)。3 実装が 1 つの曲線上にほぼ重なる。

---

## 1. 背景と実験設計

### 1.1 MST とは

**MST (Maximum Spanning Tree)** は、DP 付き表形式合成データ生成アルゴリズムの 1 つ。2018 NIST Differential Privacy Synthetic Data Competition の優勝手法を一般化したもので、大まかには以下の手順:

1. 各列 (および列ペア) の **marginal** をノイズ付きで測定する (ガウス/ラプラスメカニズム)
2. 列ペア間の相互情報量を DP 推定し、**属性ペアの重み付きグラフ**を作る
3. そのグラフの **最大全域木 (Maximum Spanning Tree)** を選び、木に乗ったクリーク (ペア) だけを保持する
4. 選んだ marginal 群を graphical model (Private-PGM) に渡して整合的な確率分布に推定
5. その分布から合成レコードをサンプリング

特徴:

- **カテゴリ (離散) 列に強い**。数値列はビニングしてから流す前提
- 列ペアまでの依存関係を保存する。3 次以上の相関は (木が持てるだけ) 限定的
- ε-DP を厳密に満たす ( zCDP → (ε,δ)-DP 変換を使用)
- 実装は [Private-PGM (ryan112358)](https://github.com/ryan112358/private-pgm) の `mechanisms/mst.py` がリファレンス

本実験の比較対象 3 実装は、いずれもこのアルゴリズムの **MST 部分を呼び出す API ラッパ**である:

| ID | ライブラリ | バージョン | 位置づけ | MST の実体 |
|---|---|---|---|---|
| A | `smartnoise-synth` | 0.3.7 | 実務向けラッパ (OpenDP) | Private-PGM の MST を呼び出し |
| B | `private-pgm` (ryan112358) | `mechanisms/mst.py` @ `e9ea5fc` | 研究用リファレンス | 直接 mbi + カスタム MST |
| C | `dpmm` | 0.1.9 (`dpmm.pipelines.mst.MSTPipeline`) | 研究/探索向けライブラリ | 独自実装 (内部に mbi を同梱) |

以降の略称: `smartnoise` / `private_pgm` / `dpmm`。

### 1.2 データ

- **UCI Adult** (14 属性 + 2 値ラベル `income`)
- 32,561 行のフル版からランダム 5,000 行の **サブサンプル** を `random_state=42` で抽出し `adult_5k.csv` として保存。以降の実験はこれで統一。
- train / holdout 分割: holdout 20% (`random_state=42`, 実験実行時の seed とは別軸)。

### 1.3 前処理 (3 実装で共通)

前処理の違いが比較バイアスの最大要因 (spec §21.1) になるため、[`experiments/shared/src/preprocessing.py`](../experiments/shared/src/preprocessing.py) で **3 実装に同じ整数エンコード済み DF を渡す**。各ステップの意図:

| ステップ | 対象 | 意図 |
|---|---|---|
| `fnlwgt` 削除 | 連続値の人口ウェイト列 | 分類器の特徴量ではなく集計用の重み。ビン化しても意味が無く、カーディナリティを増やすだけ |
| 数値列ビニング (age=10, education-num=5, capital-gain=5, capital-loss=5, hours-per-week=10) | 連続値 5 本 | **MST はカテゴリ専用**。連続値は離散化しないと domain を定義できない。bin 数は有用性とドメインサイズのトレードオフで経験的に設定 |
| `native-country` を Top-10 + `OTHER` | 高カーディナリティカテゴリ (41 カテゴリ) | **カーディナリティが大きいとノイズが marginal を支配する** (DP 誤差がセル数に応じて広がる)。稀カテゴリを OTHER に畳む |
| 欠損値 → `"__NA__"` → 整数コード | 全列 | 欠損を別カテゴリとして陽に扱う。MST は NaN を受け付けない |
| 全列の整数エンコード | 全列 | mbi の `Dataset` / `Domain` が整数インデックス前提 |

**ドメインサイズ**: 各列のカテゴリ (ビン) 数のこと。MST の内部では「各列が 0..k-1 の整数を取る」と扱うため、列ごとの k を宣言する必要がある。これを辞書で集めたものを *domain* と呼ぶ。本実験の domain 合計 (Σ k_i) は **95**、全組み合わせ (Π k_i) は約 **3×10⁹**。全組み合わせの大きさはメモリ消費量の上限に関わる。

### 1.4 実験条件

- **実装**: 3 種 (smartnoise / private_pgm / dpmm)
- **epsilon**: 3 値 {0.3, 1.0, 3.0}
- **乱数 seed**: 2 値 {0, 1}
- → **実験回数 = 3 × 3 × 2 = 18 runs**
- 生成件数: 元データと同じ 5,000 行
- delta: 1e-9 (1/n² のオーダー。n=5000 に対して十分保守的。spec §7.2 の推奨と整合)
- タイムアウト: fit 30 分 / sample 10 分 (仕様どおり、実際は超過なし)
- **全 18 runs 成功、失敗 0**

spec §8.1 の 5 水準 (0.1, 0.3, 1.0, 3.0, 10.0) と §8.3 の 5 seed からは縮小している。初回の spec 検証と共通基盤の立ち上げを優先した。拡張実験案は §7 を参照。

### 1.5 実行環境

- **Python**: 3.11.14 / **uv**: 0.9.7
- 実装ごとに独立 venv (`experiments/mst_*/.venv`)
- 実行マシン: WSL2 Linux 5.15 on 24 コア相当 (タスク同時実行数 3)
- **並列度**: 3 実装を並行実行 (`run_grid.sh` × 3)。同マシン上で同時走行しているため fit 時間の絶対値比較は ±10% 程度の CPU 競合ノイズを含む。相対順位 (dpmm が他 2 より ~25% 遅い) は再現性あり。

**実測バージョン pin** (`uv.lock` と `uv pip freeze` より、主要):

| impl | numpy | pandas | jax | mbi | その他 |
|---|---|---|---|---|---|
| smartnoise | 1.26.4 | 1.5.3 | 0.4.38 | 1.1.0 @ e9ea5fc | smartnoise-synth 0.3.7, torch 1.13.1 |
| private_pgm | 1.26.4 | 1.5.3 | 0.4.38 | 1.1.0 @ e9ea5fc | tmlt.private_pgm 0.1.1a2 (未使用), disjoint-set 0.9.0 |
| dpmm | 1.26.4 | 2.1.0 | — | (同梱) | dpmm 0.1.9, opendp 0.12.1 |

### 1.6 なぜ smartnoise に過去コミットの private-pgm が必要なのか

これは **公式パッケージ単体では smartnoise MST が動かない** ことを反映しており、本実験で判明した実運用上の落とし穴である。

事情:

1. `smartnoise-synth` 0.3.7 の `snsynth/mst/mst.py` 冒頭で `from mbi import FactoredInference, Dataset, Domain` を実行している
2. しかし `mbi` は PyPI に **公開されておらず**、ryan112358 の [private-pgm リポジトリ](https://github.com/ryan112358/private-pgm) から `pip install git+...` で入れる必要がある
3. 現在 (2026-04 時点) の private-pgm `main` は大規模リファクタ後で、`mbi` トップレベルから `FactoredInference` / `Dataset` / `Domain` が **削除** されている (jax ベースの新 API に移行)
4. しかも新 API は `jax>=0.5` / `numpy>=2.0` を要求するが、snsql (smartnoise の別依存) は `numpy<2` でしか動かない

→ `smartnoise-synth` は **snsynth 自身のコードコメントで `tree/e9ea5fcac62e2c5b92ae97f7afe2648c04432564`** という特定コミットを参照している ([`snsynth/mst/mst.py` L17](https://github.com/opendp/smartnoise-sdk/blob/main/synth/snsynth/mst/mst.py))。このコミットの `mbi` がまさに snsynth が期待する旧 API を持つ。

**したがって本実験では**:

```bash
uv pip install "git+https://github.com/ryan112358/private-pgm.git@e9ea5fcac62e2c5b92ae97f7afe2648c04432564" \
               disjoint-set "jax<0.5" "jaxlib<0.5"
```

を smartnoise 環境に追加で流している。これは smartnoise 側のバグというよりは **上流 private-pgm の破壊的変更に snsynth がまだ追随していない** ことによる一時的な不整合。実装容易性スコア (§3.4) で反映。

---

## 2. 評価方法

本実験の「良さ」を 1 つの数字では決めず、**4 観点 × 複数指標** で横並びに見る (spec §9)。各観点で「何を測りたいか」と「指標の意味」を整理する。

### 2.1 観点と指標の対応

| 観点 | 測りたいこと | 指標 | 指標の意味 | 方向 |
|---|---|---|---|---|
| **有用性 (単変量)** | 各列の周辺分布が再現できているか | **univariate TVD** | 実 vs synth の確率質量関数の L1 距離の 1/2。0=完全一致、1=完全乖離 | 小=良 |
| 有用性 (単変量) | 同上 (情報量ベース) | **Jensen–Shannon** | 対称化 KL。0=一致、log2=完全乖離 | 小=良 |
| **有用性 (二変量)** | 列ペアの相関が保存されているか | **bivariate TVD mean / max** | 全 C(14,2)=91 ペアのクロス集計 TVD の平均と最悪ケース | 小=良 |
| 有用性 (相関構造) | 依存グラフの形が残っているか | **mutual information diff** | 実 vs synth の列ペア MI 行列の絶対差 | 小=良 |
| **有用性 (実用)** | 実タスクでモデルが学習できるか | **downstream accuracy / macro F1** | synth で学習→**実** holdout で評価。実データ学習ベースラインとの差が「有用性の伸びしろ」 | 大=良 |
| 有用性 (カバレッジ) | 合成データが元の多様性を持つか | **unique_rate / duplicate_rate / coverage** | 合成レコードのユニーク率と、実データ行の被覆率 | 大=良 |
| **安全性 (近接)** | 合成レコードが特定個人に近すぎないか | **DCR (hamming)** | 合成レコード → 最近接の実レコードまでの距離。大きい=個体に似ていない | 大=安全 |
| 安全性 (近接) | 1 位と 2 位の近さの比 | **NNDR** | 最近接距離 / 2 位距離。1 に近い=近傍が密集、小さい=特定個体に張り付いている | 大=安全 |
| **安全性 (一致)** | 元データそのものをコピーしていないか | **exact match rate** | 完全同一レコードの割合。ただし粗いビニング下では実データ自身の holdout↔train でも大きな値になる点に注意 | 小=安全 (baselineと比較) |
| **安全性 (攻撃)** | 攻撃者が「この人は訓練データに居たか」を当てられるか | **nearest-neighbor MIA ROC-AUC** | 合成データ中の最近傍距離をスコアに、train/holdout を 2 クラス分類。**0.5=完全に安全、1.0=完全漏洩** | 0.5 に近いほど安全 |
| 安全性 (攻撃) | 同上の advantage 表現 | **MIA advantage** | 2×(AUC − 0.5)。0=完全安全 | 0 に近いほど安全 |
| **処理性能** | 学習時間 | **fit elapsed (s)** | runner プロセス内での fit 呼び出しの壁時計時間 | 小=良 |
| 処理性能 | 生成時間 | **sample elapsed (s)** | 同 sample 呼び出し | 小=良 |
| 処理性能 | メモリ | **tracemalloc peak (MB)** | fit 中の Python ヒープ最大値。**numpy のネイティブメモリは含まない** ため絶対値ではなく桁感を見る指標 | 小=良 |
| **実装容易性** | 使い勝手 | 半定性スコア 5 点満点 × 5 項目 | 導入難易度・API・ドメイン指定・ドキュメント・エラー追跡 | 大=良 |

### 2.2 MST で特に重要なペア

MST はアルゴリズム上 **列ペアの依存関係 (2 次相関) を優先保存する** 手法のため、**bivariate TVD** と **mutual information diff** の差が有用性評価の本丸となる。単変量 TVD は前提条件 (周辺分布が合っていなければペアも合わない) にすぎない。

### 2.3 採用しなかった指標と理由 (初回)

- **k-匿名性 / l-多様性**: DP とは設計思想が異なり、MST は DP で保証しているため重複計測
- **shadow model MIA**: 攻撃者コストが大きく、初回では NN-MIA のみ。§7 で追加予定
- **PR-AUC** (下流): 本データセットは 24% / 76% のクラス不均衡があり本来追加すべき。**次実験で対応**

### 2.4 現実の基準値 (real↔real ベースライン)

粗いビニング後の Adult データは、実データ自身の中でも高い重複率を持つ。synth の安全性指標を解釈する際はこの基準と比較する。

| 指標 | real↔real 値 | 計算対象 | 意味 |
|---|---:|---|---|
| exact match rate | **0.21** (210/1000) | holdout の各行が train に存在する率 | 合成データの exact match が 0.21 未満なら「実データの自己一致より安全」 |
| train internal duplicate | **0.12** | train 内で重複する行の割合 | 自分自身の内部重複率 |
| DCR mean (hamming) | **0.092** | holdout→train の最近傍距離 | 合成データの DCR がこれ以上なら「自分に似ている実データより遠い」 |

これらの baseline は次節の解釈に直接使う。

---

## 3. 結果

### 3.1 平均値と標準偏差 (2 seed)

| impl | eps | TVD uni | TVD biv | DCR | MIA AUC | fit (s) |
|---|---:|---:|---:|---:|---:|---:|
| smartnoise | 0.3 | 0.044 ±0.0001 | 0.111 ±0.002 | 0.129 ±0.004 | 0.503 ±0.000 | 249.5 ±0.7 |
| smartnoise | 1.0 | 0.015 ±0.001 | 0.061 ±0.003 | 0.108 ±0.000 | 0.506 ±0.005 | 243.5 ±1.3 |
| smartnoise | 3.0 | 0.004 ±0.000 | 0.043 ±0.000 | 0.105 ±0.000 | 0.502 ±0.002 | 244.2 ±0.2 |
| private_pgm | 0.3 | 0.045 ±0.002 | 0.115 ±0.006 | 0.131 ±0.005 | 0.503 ±0.008 | 240.5 ±2.7 |
| private_pgm | 1.0 | 0.017 ±0.002 | 0.067 ±0.003 | 0.113 ±0.000 | 0.508 ±0.004 | 237.7 ±0.1 |
| private_pgm | 3.0 | 0.006 ±0.001 | 0.044 ±0.002 | 0.105 ±0.000 | 0.508 ±0.002 | 234.8 ±1.4 |
| dpmm | 0.3 | 0.041 ±0.004 | 0.116 ±0.010 | 0.133 ±0.001 | 0.510 ±0.007 | 302.0 ±3.3 |
| dpmm | 1.0 | 0.015 ±0.000 | 0.064 ±0.001 | 0.112 ±0.003 | 0.500 ±0.003 | 297.0 ±2.5 |
| dpmm | 3.0 | 0.005 ±0.001 | 0.044 ±0.002 | 0.106 ±0.000 | 0.508 ±0.007 | 302.2 ±1.6 |

※ n=2 の SD はあくまで参考。本来 seed ≥5 で検定すべきところ (§7 で対応)。

### 3.2 下流タスク (holdout `income` 分類, Logistic Regression)

実データ学習ベースライン: **accuracy = 0.836** (LR)。このギャップが「DP によるユーティリティロス」。

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

macro F1 が accuracy より 0.15〜0.25 低いのはクラス不均衡 (income 1:3) のため。**次実験では PR-AUC を追加**。

### 3.3 メモリ (tracemalloc ピーク)

| impl | fit peak (MB) |
|---|---:|
| smartnoise | 50.0 |
| private_pgm | 4.7 |
| dpmm | 2.9 |

tracemalloc は Python allocator 経由のみを追跡し、numpy 大域配列は含まない。計測開始は runner 内 `fit()` 直前 (`wrapper.py` の `tracemalloc.start()` 以降)。smartnoise の 50 MB は `snsql/snsynth` のインポート時に作られる Python オブジェクト (SQL AST、メタデータ辞書など) を反映。**MST 本体のメモリ差ではない**。

---

## 4. 観点別考察

### 4.1 有用性

- 単変量 TVD・二変量 TVD・下流 accuracy のいずれも、**3 実装の差は seed 内分散と同程度** (eps=1.0 で TVD uni 差 ≤0.002、SD 0.001)。これは 3 実装がいずれも「同じ MST アルゴリズムを同じドメインで呼んでいる」ことと整合する。
- 期待どおり epsilon 増加で TVD 単調減少 (0.044 → 0.015 → 0.005)。下流 accuracy の改善は 0.74 → 0.76 と微細で、eps=3.0 でも実データ baseline (0.836) から 0.08 低い。
- **MST は 2 次相関までしか保存しない**ため、3 次以上の交互作用に依存する分類タスクでは有用性の天井がある。PrivBayes / AIM との比較でこの限界が可視化されるはず。

### 4.2 安全性

- **MIA ROC-AUC は全条件で 0.50–0.51** (advantage ≤0.019)。ただし seed=2 では 95%CI を引けないため「漏洩が無い」ではなく「簡易 NN-MIA では検出できない」と読む。また AUC の Wilson CI を次実験で出す。
- **DCR (hamming) は 0.10–0.13** で、real↔real ベースライン **0.092** より大きい。つまり「合成レコード最近傍の実レコードは、実データ自身の最近傍より **遠い**」 ≒ 個体同定の観点では安全側。
- **exact match rate 0.07–0.17** は一見大きいが、real↔real の **0.21** を下回る。これは「合成データが元データより自己複製していない」ことを意味し、**粗いビニングで格子が埋まる Adult の特性が主因**であって MST の問題ではない。実運用では exact match だけ見ると誤読しやすいので DCR / baseline と併読する必要がある。
- epsilon 増加で DCR が減る (0.133 → 0.105) のは「有用性向上により元分布に近づいた結果、最近傍距離も縮む」という副作用。個体単位の接近ではないが、**eps が十分大きい領域では安全性と有用性のトレードオフが顕在化する**。eps 両端を含めた次実験で曲線を描きたい。

### 4.3 処理性能

- fit 時間: **private_pgm ≈ smartnoise (~240 s) < dpmm (~300 s)** で一貫 (CPU 競合ノイズ ±10% 込み)。
  - dpmm の +60s は `MSTPipeline` が `disable_processing=True` でも内部でドメイン検証・compress 判定・`n_jobs` 調整を行う分のオーバーヘッド。
  - smartnoise は snsql/snsynth のインポート・変換を経由するが `preprocessor_eps=0.0` により本体は private-pgm の MST 直呼びとほぼ同じ。
- sample 時間: **private_pgm が 1 ms と突出**。これは本実験の wrapper が **fit 時点で 1 つの synthetic DF を生成して貯め込み、`sample(n)` は numpy の再抽出のみ** という実装にしているため。他 2 実装は毎回モデルから生成する。**公平比較ではない**ことを明記し、§5 のバイアス節にも記載。
- 安定性: 18/18 成功。タイムアウト・例外ゼロ。OOM なし。

### 4.4 実装容易性 (導入・API・ドキュメント・デバッグ)

| 項目 | smartnoise | private_pgm | dpmm |
|---|---:|---:|---:|
| pip/uv 導入 | 2 (依存 pin と追加 git install が必要) | 3 (`mechanisms/mst.py` を手動取得する必要がある) | 5 (`pip install dpmm` だけで MST を呼べた) |
| API の直感性 | 4 (`Synthesizer.create("mst", ...)`) | 2 (raw mbi、MST 関数はリポジトリの `mechanisms/` に埋まっている) | 4 (`MSTPipeline.fit/generate`) |
| ドメイン指定 | 3 (snsynth が自動推定、無効化に `preprocessor_eps=0.0`) | 5 (`Domain` に明示) | 4 (dict で渡す) |
| ドキュメント | 3 (OpenDP docs は最低限) | 2 (README のみ、コミット参照必要) | 2 (PyPI README のみ) |
| エラー追跡 | 2 (snsynth/mbi/jax の多層スタック) | 4 (ほぼ素の numpy + mbi) | 3 (パイプライン内部で epsilon 分配が隠れる) |
| **合計 (25 点満点)** | **14** | **16** | **18** |

### 4.5 将来拡張性

- **dpmm**: `MSTPipeline` と同形の `AIMPipeline` / `PrivBayesPipeline` を提供しているため、spec の次ステップ (PrivBayes / AIM 比較) への拡張コストが最小。
- **private_pgm**: raw mbi を直接触るため、内部アルゴリズムの改造 (クリーク選択、ノイズ配分など) が最もやりやすい。研究用途向け。
- **smartnoise**: ラッパとして固定化され、内部を触るには上流フォークが必要。代わりに `ctgan`, `mwem`, `aim`, `dpctgan` など他手法を **同じ `Synthesizer.create(...)` API で横比較** できるのが利点。

---

## 5. 用途別推奨

spec §22 のフォーマット:

| 用途 | 推奨 | 理由 | 見送り点 |
|---|---|---|---|
| **短期 PoC** (動くものを最短で) | **dpmm** | `pip install dpmm` → `MSTPipeline.fit/generate` の 5 行で動く。前処理とドメイン推定まで面倒を見る | fit が他より ~25% 遅い。内部パラメータがブラックボックス寄り |
| **研究・理解・改造** | **private_pgm (ryan112358)** | mbi を直接触れて MST の実装を読める。fit が最速クラス。ノイズ配分や clique 選択を直接書き換えられる | MST 関数は PyPI パッケージに含まれず `mechanisms/mst.py` を手動取得する必要がある |
| **継続比較基盤** (今後 PrivBayes/AIM を足す) | **dpmm** (次点: smartnoise) | 同形 API で複数アルゴリズムを追加できるのが dpmm 最大の強み。smartnoise は MST 以外 (ctgan 等) と横並べしたい場合に有効 | dpmm は API 安定性がまだ流動的。version pin 必須 |

---

## 6. 比較バイアスと注意点

1. **3 実装の有用性差がほぼゼロな主因は前処理の固定**: 同じ整数エンコード DF とドメイン辞書を渡し、各ライブラリの内部前処理を無効化した (`smartnoise: preprocessor_eps=0.0`, `dpmm: disable_processing=True`)。「各ライブラリをデフォルトで使ったときの性能」は別問題で、§4.4 で拾っている。
2. **smartnoise の追加 pin 問題**: `pip install smartnoise-synth` 単体では MST が動かない (§1.6 参照)。上流依存が壊れている期間の実情を反映して導入スコアを減点した。この問題は上流が追従すれば消える可能性がある。
3. **epsilon グリッド縮小** (0.1, 10.0 を外した): 有用性崩壊領域と安全性低下領域の両端を見ていない。トレードオフ曲線を描くには再実験が必要。
4. **seed=2 は統計的に不十分**: SD は参考値。特に downstream F1 のような分散の大きい指標では seed ≥5 で再測が必要。
5. **データは 5k subsample**: 有用性は一般に n が大きいほど改善する (同じ ε 予算でノイズの影響が希釈される) ため、絶対値を 32k に外挿しないこと。fit 時間は比例しないことを smoke test で確認 (32k でも ~250s)。
6. **sample 時間の公平性**: private_pgm wrapper は fit 時点で synthetic DF を貯め `sample(n)` は numpy 再抽出にしているため ~1 ms に見える。他 2 実装はモデルから都度生成。DP 的には問題ないが **「sample 速度の比較」としては公平でない**。
7. **NN-MIA が弱い**: MIA AUC が 0.5 付近なのは「MST が安全」というより「simple NN-MIA の攻撃力不足」の可能性あり。shadow model MIA / holdout-based MIA の追加が必要。
8. **exact match / DCR の解釈は real↔real baseline (§2.4) に対する相対で読むこと**。絶対値だけでは「21% ならヤバい」と誤読する。
9. **並列実行による CPU 競合**: 3 実装を同時並行で fit しているため、fit 時間の絶対値は ±10% の測定ノイズを含む。相対順位は再現性あり。順位が近い実装 (smartnoise vs private_pgm) の差は有意でない可能性がある。
10. **tracemalloc は numpy ネイティブメモリを見ていない**: 本実験の 2.9–50 MB という値は Python ヒープのみ。実際の RSS ピークはこの 5〜20 倍程度と推定。次実験では psutil の RSS 測定を併用する。
11. **vendored 外部ファイル**: `experiments/mst_private_pgm/src/{mst.py, cdp2adp.py}` は ryan112358 リポジトリから curl 取得したもの。上流が消えたり force-push されたら再現不能になる。コミット SHA で pin 済みだが、**repo 内に vendor として常駐しているため自己完結している**。将来的には SHA256 を README に記載して改竄検出できるようにするのが望ましい。

---

## 7. 追加実験案 (優先順)

1. **epsilon 両端** (0.1, 10.0) 追加 → 有用性崩壊と安全性低下のカーブを描く
2. **seed を 5 に戻す** → SD バンドと Wilson CI / ペア t 検定を出す
3. **PR-AUC / Balanced Accuracy 追加** → クラス不均衡に頑健な評価
4. **shadow model MIA** → NN-MIA が弱い仮説の検証
5. **PrivBayes / AIM 追加** (dpmm の同形 API を活用) → MST の 2 次相関限界を可視化
6. **フル 32k Adult** → subsample の外挿誤差の確認
7. **別データセット** (Mushroom, Bank, Credit) → Adult 依存性の切り離し
8. **属性推定攻撃** → `income` を伏せて他列から推定、ベースラインとの差分
9. **psutil RSS 計測の併用** → tracemalloc の値と実 RSS の乖離を確認

---

## 8. 再実行手順

[`docs/rerun.md`](rerun.md) に分離。概略:

```bash
# 1. データ取得
bash scripts/fetch_adult.sh   # (UCI curl + pandas で adult.csv/adult_5k.csv 生成)

# 2. 環境構築 (3 実装)
(cd experiments/mst_smartnoise && uv sync --python 3.11)
(cd experiments/mst_private_pgm && uv sync --python 3.11)
(cd experiments/mst_dpmm && uv sync --python 3.11)

# 3. 18 runs (3 impl 並列)
./run_grid.sh experiments/mst_smartnoise  &
./run_grid.sh experiments/mst_private_pgm &
./run_grid.sh experiments/mst_dpmm        &
wait

# 4. 集計・可視化
python3 experiments/shared/src/aggregate.py
python3 experiments/shared/src/visualize.py --results-dir results
```

所要時間: wall-clock 約 25 分 (fit 4 分/run × 6 runs/impl × 3 impl 並列)。
