# TextInserter 再リファクタリング作業チェックリスト

## 目的
- TextInserterDialog の責務密度を下げ、UI機能を維持したままテスト容易性と保守性を向上する。

## 非目的
- UI部品の削除や操作項目の削減。
- 既存の保存物フォーマット変更。
- core層からui層への依存追加。

## 成功条件
- UI構築が .ui へ移行（またはUI生成コードが大幅削減）される。
- UseCase層がユニットテスト可能となる。
- Settingsアクセスが単一APIに集約される。

## 依存関係
- Gtk.Builder（.ui）
- 既存の core 実装（TemplateManager / TextRenderer / Exporter / filename_generator）
- 既存の settings_manager（ラップ導入）

## リスク
- .uiのID/信号不整合
- フォント/レイアウト差異
- GIMP依存テストの不安定性

---

## Phase 0: 現状固定（準備）
- [x] 既存の手動動作確認（CSV→挿入→保存）
- [x] 既存の自動テストが全てパス

## Phase 1: UseCase層の導入（移動のみ）
- [x] core/text_insert_usecase.py を新規作成
- [x] core/export_usecase.py を新規作成
- [x] TextInserterDialog からロジックをUseCaseへ移動
- [x] UseCaseユニットテストを追加
- [x] 差分は「移動のみ」で、動作変更は行わない

## Phase 2: Settingsオブジェクト導入（配線のみ）
- [x] ui/settings.py を新規作成（Settingsオブジェクト）
- [x] TextInserterDialogのsettingsアクセスをSettings経由に統一
- [x] settings_managerの互換ラッパ維持
- [x] 差分は「配線のみ」で、動作変更は行わない

## Phase 3: UIの .ui 化（移動のみ）
- [x] ui/text_inserter_dialog.ui を新規作成
- [x] TextInserterDialog をGtk.Builderロード方式へ移行
- [x] UIロード健全性テストを追加
- [x] 必須IDリストを固定（template_dir_button / template_combo / csv_chooser / date_calendar / row_spinner / preview_text / output_folder_button / filename_preview_label / status_label）
- [x] 差分は「移動のみ」で、動作変更は行わない

## Phase 4: ガード節/エラーハンドリング共通化（整理のみ）
- [x] _require_* 系のプリチェック共通化
- [x] _run_action による例外処理集約
- [x] 既存UI機能を維持していることを確認
- [x] 差分は「整理のみ」で、動作変更は行わない

## 仕上げ
- [x] docs/text_inserter_refactoring_plan.md と整合確認
- [x] 全テスト実行（ruff/basedpyright/pytest）
- [x] リファクタリング前後の行数を比較
