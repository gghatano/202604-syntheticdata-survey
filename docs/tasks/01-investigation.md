# T01 実装調査 / API 差分整理

## 目的
3 実装 (smartnoise-synth / tmlt.private_pgm / dpmm) の最小実行経路・必須引数・ドメイン指定方法・前処理要件を整理し、共通 I/F 設計 (T02) の入力とする。

## 成果物
- `docs/tasks/notes/01_api_matrix.md`
  - API 差分表（fit/sample/domain/epsilon/seed/対応データ型）
  - 最小実行サンプル（各 3 行程度）
  - 前処理要件（エンコード要否、欠損処理、カテゴリ列宣言）
  - 既知の制約・バージョン要件

## 作業
1. 各パッケージの README / ドキュメントから最小実行例を抽出
2. MST 呼び出しに必要な引数・ドメイン指定形式を確認
3. smartnoise が内部で Private-PGM を使う点を明記
4. Python 3.11 / 依存衝突情報を記録

## 完了条件
- API 差分表が埋まっている
- 共通 I/F 定義（T02）の入力として使える粒度である
