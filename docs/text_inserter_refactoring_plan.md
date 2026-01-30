# TextInserter 再リファクタリング計画

## 目的
- UI機能を削らずに、TextInserterDialogの責務密度と行数を下げる。
- 画面ロジックをUIから分離し、ユニットテスト可能にする。
- settingsアクセスを統合し、UI層の依存面積を縮小する。

## 非目的
- UI部品や操作項目の削除。
- 既存の外部呼び出し点や保存物フォーマットの変更。
- core層からui層への依存追加。

## 成功条件
- TextInserterDialogのUI構築コードが大幅に削減される（.ui化またはUIファクトリへの移管）。
- CSV→row_data→render/export のロジックがcore側のUseCaseに分離され、ユニットテストで検証可能。
- settingsアクセスがSettingsオブジェクト経由に集約され、列挙importが撤廃される。
- 既存のボタン/入力項目のUI機能が維持される。

## 依存関係
- Gtk.Builder（.ui）によるUIロード機構。
- 既存の `core/text_renderer.py`, `core/exporter.py`, `core/template_manager.py`。
- 既存の `ui/settings_manager.py`（ラップして段階導入）。

## リスク
- .uiのID/シグナル不整合でUIロードに失敗するリスク。
- フォント/レイアウト差異によるUI表示の変化。
- GIMP依存のE2Eテストが不安定になる可能性。

---

## 1) 変更方針（アーキテクチャ図を文章で）

- **UI定義**: `ui/text_inserter_dialog.ui` にWidget構築を移管し、Python側は `Gtk.Builder` でロード。
- **Dialog層**: `TextInserterDialog` は「UI初期値の反映・ユーザー入力の収集・UseCase呼び出し・表示更新」に限定。
- **UseCase層（core）**:
  - `TextInsertUseCase`: テンプレート選択 → row_data構築 → `TextRenderer` → layers返却。
  - `ExportUseCase`: row_data構築 → filename生成 → `Exporter.save_png` 実行。
  - `row_data` は `dict[str, str]` に固定し、日付解決・差し込みフィールド決定までをUseCase側で担当する。
- **Settings層（ui）**: `Settings` オブジェクトに統合し、`settings_manager` は互換ラッパとして段階導入。
- **依存方向**: `ui -> core` のみ。`core` は `ui` を参照しない。

---

## 2) 段階的な実施手順

### Phase 0: 下準備（移動なし）
- **内容**: 既存機能のスモークテスト基盤を整備、現状の挙動を固定。
- **完了条件**:
  - 既存ダイアログで「CSV読み込み → 挿入 → 保存」が通る。
  - 既存テストが全てパス。

### Phase 1: UseCase層の導入（移動のみ）
- **内容**: UIからロジックを移動し、UseCaseとして切り出し。
- **完了条件**:
  - TextInserterDialogはUseCaseを呼ぶだけになり、直接ロジックを持たない。
  - UseCaseのユニットテストが追加される。
  - 差分は「移動のみ」で、動作変更は行わない。

### Phase 2: Settingsオブジェクト導入（配線のみ）
- **内容**: `Settings` を導入し、`load_* / save_*` の列挙importを削減。
- **完了条件**:
  - TextInserterDialogのsettingsアクセスが `Settings` 経由に統一。
  - 旧APIは互換ラッパとして残存。
  - 差分は「配線のみ」で、動作変更は行わない。

### Phase 3: .ui化（移動のみ）
- **内容**: UI構築コードを `.ui` ファイルへ移管。
- **完了条件**:
  - Python側は `Gtk.Builder` でロードし、`get_object` と `connect_signals` のみ。
  - UIロード健全性テストが追加される。
  - 差分は「移動のみ」で、動作変更は行わない。

### Phase 4: ガード節/エラーハンドリング共通化（整理のみ）
- **内容**: `_require_*` と `_run_action` の導入で重複除去。
- **完了条件**:
  - ガード節の重複削減。
  - エラーハンドリングの一貫性が確保される。
  - 差分は「整理のみ」で、動作変更は行わない。

---

## 3) 新規ファイル案と責務

### UI
- `ui/text_inserter_dialog.ui`
  - UI構築（GtkBuilderでロードされるWidget定義）
  - どのセクションを.ui化するか:
    - Template選択セクション
    - CSVファイル選択セクション
    - Date選択カレンダー
    - Row選択とプレビュー
    - Saveセクション
  - シグナル設計ルール:
    - シグナルは少数の入口に集約し、個別Widgetのon_changed乱立を避ける。
  - 必須IDの固定（UIロード健全性テスト対象）:
    - template_dir_button
    - template_combo
    - csv_chooser
    - date_calendar
    - row_spinner
    - preview_text
    - output_folder_button
    - filename_preview_label
    - status_label

### core
- `core/text_insert_usecase.py`
  - 入力: image, template_path, row_data
  - 出力: 追加レイヤー一覧
  - 依存: TemplateManager, TextRenderer
  - row_data: dict[str, str]（日付解決・差し込みフィールド決定までUseCase内で完結）

- `core/export_usecase.py`
  - 入力: image, row_data, output_dir
  - 出力: 保存パス
  - 依存: Exporter, filename_generator
  - row_data: dict[str, str]

### ui
- `ui/settings.py`
  - Settingsオブジェクト（typed property）
  - 内部で `settings_manager` を利用

---

## 4) TextInserterDialog から外に出す候補一覧

- CSV読み込み
  - `CSVParser.parse` 呼び出しとrow数更新ロジック
- row_data構築
  - `_build_row_data`, `_resolve_date_from_row`
  - 日付解決・差し込みフィールド決定（UseCase側へ）
- Insert処理
  - template選択 → TemplateManager.load_template → TextRenderer
- Save処理
  - output_dir検証/作成 → filename生成 → Exporter.save_png
- エラーハンドリング共通化
  - `_run_action`, `_require_*`

---

## 5) リスクと回避策

### .ui ID/信号ミス
- **リスク**: builder.get_objectが失敗、signal接続漏れ
- **回避策**: UIロード健全性テストを追加（必須Widgetが取れるか確認）

### フォント差異
- **リスク**: .ui化でデフォルトフォントが異なる
- **回避策**: 現行UIのフォント/サイズを .ui に明示

### GIMP依存テストの不安定性
- **リスク**: CIでGIMPバッチ実行が不安定
- **回避策**: E2EテストはXvfb + GIMPバッチを前提にし、UseCase層はユニットテストで担保

---

## テスト戦略（最低限）

- **UIロード健全性テスト**（必須）
  - `text_inserter_dialog.ui` がロードできる
  - 必須Widgetが取得できる
  - signal接続が失敗しない

- **UseCaseユニットテスト**
  - CSV行 → row_data 変換
  - filename生成
  - Exporter.save_png呼び出し境界

- **E2Eテスト（将来）**
  - Xvfb + GIMPバッチで「テンプレ + 差し込み → PNG生成」
  - UI操作と保存結果を検証
