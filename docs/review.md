# レビュー運用ガイド

実験レポートやコード変更の品質を、**複数の観点の独立レビュアー**が並行でチェックする体制を `.claude/agents/` に組み込んである。このドキュメントは **どのエージェントを・いつ・どう呼ぶか** の運用手順書。

## 1. 用意されているレビューエージェント

`.claude/agents/` 配下の 7 種。いずれも Claude Code の sub-agent として起動する。

| Agent | 観点 | 主に見るファイル | いつ起動するか |
|---|---|---|---|
| `review-experiment-execution` | 実験の設計・実行・再現性 | `docs/report*.md`, `experiments/**/runner.py` | グリッド実行後、report 執筆前 |
| `review-interpretation` | 結果解釈・統計的扱い・主張の強さ | `docs/report*.md` §3〜§5 | report の結果/考察を書いた直後 |
| `review-experiment-management` | 実験管理・命名・ID 追跡・比較可能性 | `README.md`, `docs/report*.md`, `results/` | 新実験追加の前後 |
| `review-config-management` | 依存 pin・設定散在・再現環境 | `pyproject.toml`, `uv.lock`, `**/configs/*.yaml` | 環境追加・依存更新時 |
| `review-documentation` | 情報アーキテクチャ・可読性・リンク整合 | `docs/**`, `README.md` | ドキュメント編集後 |
| `review-test-quality` | smoke test・例外・観測性・境界条件 | `experiments/**/runner.py`, `**/wrapper.py`, `aggregate.py` | runner/wrapper 変更時 |
| `review-uiux-quality` | CLI / プロット / 表の UX | `visualize.py`, `runner.py`, `docs/report*.md` の表/図 | 可視化追加・CLI 変更時 |

すべて Sonnet で動作し、日本語で 400 語以内の構造化指摘を返す。感想文ではなく **ファイルパス:行番号での引用と具体的修正案** を出すよう指示済み。

## 2. 起動方法

### 2.1 個別起動 (特定の観点だけ見たい)

Claude Code の Task ツールで `subagent_type` を指定して起動する。

例:
```
Review docs/report.md with review-interpretation and return the structured bullet list.
```

Task ツール呼び出しでは `subagent_type: "review-interpretation"` を指定。プロンプトで対象ファイル・対象セクションを明記する。

### 2.2 まとめてレビュー (report/PR 完成直前)

新しい実験レポートを書き終えたら、**観点ごとに並列**で 7 エージェントを起動する。Claude Code の 1 回の応答で複数の Task 呼び出しを発行すると自動で並列実行される。

起動例 (レポート執筆者が Claude に依頼する場合):

```
experiment 02 のレポート docs/report_02_*.md ができたのでレビューしてください。
以下の 7 観点のエージェントを並列起動して、指摘を統合してください:
- review-experiment-execution
- review-interpretation
- review-experiment-management
- review-config-management
- review-documentation
- review-test-quality
- review-uiux-quality
```

Claude 側は 7 本の `Task(subagent_type=...)` を並列で発行し、返ってきた指摘を **観点ごとに分類して統合**して report 著者に渡す。著者は優先度 🔴 を全て、🟡 を可能な範囲で反映してから PR を作成する。

### 2.3 部分レビュー (差分だけ)

コード変更の直後に関連エージェントだけ呼ぶケース:

| 変更 | 呼ぶべきエージェント |
|---|---|
| runner.py / wrapper.py を編集 | review-test-quality + review-experiment-execution |
| pyproject.toml / uv.lock 変更 | review-config-management |
| visualize.py / プロット追加 | review-uiux-quality |
| docs/ を編集 | review-documentation |
| 新しい実験ディレクトリ追加 | review-experiment-management + review-config-management |
| report の結果節を書いた | review-interpretation + review-documentation |

## 3. 指摘への対応ポリシー

各エージェントは指摘に **🔴 すぐ直す / 🟡 次の実験で対応 / 🟢 Nice-to-have** の優先度を付ける。対応方針:

- **🔴**: 原則すべて PR 前に直す。直せない場合は report の §6 バイアス節に書いて明示する
- **🟡**: 次実験のタスク定義 (`docs/tasks/` または `docs/tasks_<nn>/`) に起票する
- **🟢**: バックログ (`docs/backlog.md` を作ってもよい) に積む

指摘と対応を PR 本文の「レビュー指摘への対応」節に書き残すと、次回の追試時に同じ議論を繰り返さずに済む。

## 4. エージェントのメンテナンス

- 新しい観点が必要になったら `.claude/agents/review-<name>.md` を追加する
- 既存エージェントが見落とす頻出ミスが出たら、そのエージェントの # 観点 セクションに項目を足す
- エージェントの指摘がノイズに感じる場合は `description` を狭めて起動頻度を絞る
- `model: sonnet` を `opus` に上げると鋭くなるが、コストとレイテンシが上がる

## 5. レビューを省いてよいケース

- typo 修正・コメント追加など意味的に中立な変更
- ドキュメント 1 行の軽微な修正
- **ただし** 実験結果の解釈や主張に関わる変更は必ず `review-interpretation` を通す

---

関連: [`docs/process.md`](process.md) フェーズ 8 から本ドキュメントを参照している。
