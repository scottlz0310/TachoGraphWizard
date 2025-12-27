# CHANGELOG

このドキュメントは現行仕様の要約と変更履歴を記載します。

## [1.0.0] - 2025-12-27
### 追加
- **Split Padding設定**: 自動切り分け時の各円盤周囲の余白を調整可能（デフォルト20px）
- **Ellipse Padding設定**: 背景除去時の楕円選択の内側余白を調整可能（デフォルト20px）

### 変更
- **Auto Split正式版**: Beta表記を削除し、正式機能として提供
- **背景除去アルゴリズム**: しきい値ベースから楕円選択ベースに変更
  - GIMP 3の`image.select_ellipse()`、`Gimp.Selection.invert()`、`drawable.edit_clear()`を使用
  - より確実かつシンプルな背景除去を実現
- **UIの簡素化**: Step 2のThresholdスライダーを削除（不要になったため）

### 削除
- **Split Using Guidesボタン**: ガイドベースの切り分け機能を削除（MVP用の暫定機能のため）
- Threshold関連パラメータと複雑なアルゴリズム（Color to Alpha、島検出など）

### 修正
- GIMP 3 Python API互換性の向上
  - PDBプロシージャ呼び出しからOOPメソッド呼び出しへ移行
  - `Gimp.ImageType.GRAY`などの存在しない列挙値の使用を修正
- 楕円選択が正しく作成されない問題を解決

### 技術的改善
- `image_splitter.py`: `pad_px`パラメータを外部から設定可能に
- `background_remover.py`: `ellipse_padding`パラメータを追加し、柔軟な背景除去を実現
- コードの簡素化: 約200行のワークアラウンドコードを40行のシンプルな実装に置き換え

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
