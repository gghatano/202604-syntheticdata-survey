# MST 3種比較実験 タスク一覧

`docs/spec.md` v0.2 に基づくタスク分解。Claude Code のチーム（並列エージェント）で対応する。

## フェーズと依存関係

```
T01 調査 ──┐
           ├─> T02 共通I/F ──> T04 各Runner ──┐
T03 前処理 ─┘                                  ├─> T06 実験実行 ──> T07 可視化 ──> T08 レポート
           └─> T05 評価指標 ─────────────────┘
```

## タスク一覧

| ID  | タイトル                  | ファイル                           | 並列可 | 依存       |
| --- | ------------------------- | ---------------------------------- | ------ | ---------- |
| T01 | 実装調査 / API 差分整理   | [01-investigation.md](01-investigation.md) | ○      | -          |
| T02 | 共通 I/F 設計             | [02-common-interface.md](02-common-interface.md) | -      | T01        |
| T03 | 共通前処理 & ドメイン定義 | [03-preprocessing.md](03-preprocessing.md) | ○      | -          |
| T04 | 3 実装 Runner 実装        | [04-runners.md](04-runners.md)     | ○ (3分岐) | T02, T03 |
| T05 | 共通評価モジュール        | [05-evaluation.md](05-evaluation.md) | ○ (4分岐) | T03      |
| T06 | 実験実行・ログ収集        | [06-experiment-execution.md](06-experiment-execution.md) | - | T04, T05 |
| T07 | 可視化                    | [07-visualization.md](07-visualization.md) | -   | T06       |
| T08 | 考察・レポート            | [08-report.md](08-report.md)       | -      | T07        |

## 初期実装スコープ（本セッションで進める範囲）

ネットワーク/パッケージインストールを伴わない以下をまず実装する:

- `experiments/` 配下のディレクトリ雛形
- `shared/configs/experiment_base.yaml`, `epsilon_grid.yaml`
- `shared/evaluation/{utility,privacy,performance,usability}.py` スタブ
- `shared/data/` 前処理スクリプト雛形
- 各 `runner.py` / `wrapper.py` の共通 I/F に沿った骨格
- `experiments/README.md` に再実行手順

`uv add` 等のネットワーク作業は手順ドキュメント化にとどめ、実行は利用者に委ねる。
