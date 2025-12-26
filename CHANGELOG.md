# CHANGELOG

このドキュメントは現行仕様の要約と変更履歴を記載します。

## [0.1.1] - 2025-12-26
### 変更
- CI/CDのPyPI publishジョブを削除
- GitHub Release作成の権限を`contents: write`に更新

## [0.1.0] - 2025-12-26
### 追加
- Tachograph Chart Wizard
  - ガイド分割による円盤の切り分け
  - 背景除去（Color to Alpha）
  - PNG保存
- Tachograph Text Inserter
  - JSONテンプレート読み込み（位置比率・フォント設定）
  - 車両マスタCSV読み込み（`vehicle_type`, `vehicle_no`, `driver`）
  - 日付はUI選択で補完（前回値があれば優先、無ければ当日）
  - CSVに `date`/`date_year` 等があればその値を優先
  - 行選択プレビューとテキスト挿入
  - カスタムテンプレートフォルダの読み込み（設定に保存）
- Tachograph Template Exporter
  - テキストレイヤーからJSONテンプレートを出力
  - フォントサイズ単位がptの場合、DPIからpx換算
- 設定保存
  - `%APPDATA%\tachograph_wizard\settings.json` に前回日付とテンプレートフォルダを保存
- ドキュメント
  - `docs/phase2_implementation.md`
  - `docs/version_upgrade_plan.md`

### 既知の制約
- 切り分けはガイド分割が前提（自動切り分けは次期版で検討）
- 文字入れは別ダイアログ（Text Inserter）で実行
