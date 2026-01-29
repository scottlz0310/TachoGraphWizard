# モジュール肥大化リファクタリング計画

## 現状分析

### モジュールサイズ一覧（行数降順）

| モジュール | 行数 | 状態 |
|-----------|------|------|
| `core/image_splitter.py` | 778 | ⚠️ 要リファクタリング |
| `ui/text_inserter_dialog.py` | 753 | ⚠️ 要リファクタリング |
| `core/background_remover.py` | 702 | ⚠️ 要リファクタリング |
| `core/template_exporter.py` | 370 | 許容範囲 |
| `tachograph_wizard.py` | 343 | 許容範囲 |
| `procedures/wizard_procedure.py` | 272 | 許容範囲 |
| `core/pdb_runner.py` | 264 | 許容範囲 |
| その他 | <250 | OK |

**目標**: 
- 各モジュールを300行以下に分割(必須ではなく目安)
- 安定した公開API（呼び出し側の変更が最小）
- テスト容易性（I/O境界の明確化、純粋関数化）

---

## 1. text_inserter_dialog.py (753行)

### 現状の構造

```
CsvDateError (例外クラス)
設定関連関数 (約140行)
  - _get_settings_path, _load_setting, _save_setting
  - _load_path_setting, _load_last_used_date, _save_last_used_date
  - _load_template_dir, _save_template_dir
  - _load_csv_path, _save_csv_path
  - _load_output_dir, _save_output_dir
  - _parse_date_string
  - _load_filename_fields, _save_filename_fields
  - _load_window_size, _save_window_size

TextInserterDialog (メインクラス、約600行)
  - UI作成メソッド群 (~250行)
  - イベントハンドラ群 (~200行)
  - ビジネスロジック (~150行)
```

### 分割案

| 新モジュール | 内容 | 推定行数 |
|-------------|------|---------|
| `ui/settings_manager.py` | 設定の読み書き関数すべて | ~150行 |
| `ui/text_inserter_dialog.py` | ダイアログ本体（UIとイベント） | ~450行 |
| `core/filename_generator.py` | ファイル名生成ロジック | ~50行 |

### 詳細

#### settings_manager.py（新規作成）
```python
# 移動対象
- _get_settings_path()
- _load_setting() / _save_setting()
- _load_path_setting()
- _load_last_used_date() / _save_last_used_date()
- _load_template_dir() / _save_template_dir()
- _load_csv_path() / _save_csv_path()
- _load_output_dir() / _save_output_dir()
- _load_filename_fields() / _save_filename_fields()
- _load_window_size() / _save_window_size()
- _parse_date_string()
```

#### filename_generator.py（新規作成）
```python
# 移動対象
- _generate_filename_from_row() ロジック部分
```

---

## 2. image_splitter.py (778行)

### 現状の構造

```
_Component (データクラス、~20行)
ImageSplitter (静的メソッドのみのクラス)
  - ユーティリティ (~150行)
    - _debug_log, _analysis_scale, _get_image_dpi
    - _get_analysis_drawable, _buffer_get_bytes
    - _otsu_threshold
  - コンポーネント検出 (~50行)
    - _find_components
  - 画像操作 (~200行)
    - _duplicate_image, _crop_image
    - _apply_component_mask
  - ガイド分割 (~270行)
    - split_by_guides
  - 自動検出分割 (~230行)
    - split_by_auto_detect
  - 結果取得 (~50行)
    - get_split_result
```

### 分割案

| 新モジュール | 内容 | 推定行数 |
|-------------|------|---------|
| `core/image_analysis.py` | 画像分析（Otsu、コンポーネント検出） | ~200行 |
| `core/image_operations.py` | 画像操作（複製、クロップ、マスク適用） | ~200行 |
| `core/image_splitter.py` | 分割ロジック本体 | ~300行 |

### 詳細

#### image_analysis.py（新規作成）
```python
# 移動対象
- _Component クラス
- _analysis_scale()
- _get_image_dpi()
- _get_analysis_drawable()
- _buffer_get_bytes()
- _otsu_threshold()
- _find_components()
```

#### image_operations.py（新規作成）
```python
# 移動対象
- _duplicate_image()
- _crop_image()
- _apply_component_mask()
```

---

## 3. background_remover.py (702行)

### 現状の構造

```
BackgroundRemover (静的メソッドのみのクラス)
  - color_to_alpha (~100行) - 現在未使用？
  - despeckle (~50行)
  - auto_cleanup_and_crop (~100行)
  - remove_garbage_keep_largest_island (~470行) - 巨大！
  - add_center_guides (~40行)
  - process_background (~30行)
```

### 分割案

| 新モジュール | 内容 | 推定行数 |
|-------------|------|---------|
| `core/island_detector.py` | 島検出・最大島抽出ロジック | ~300行 |
| `core/background_remover.py` | 背景除去の高レベルAPI | ~250行 |
| `core/image_cleanup.py` | クリーンアップ・ガイド追加 | ~150行 |

### 詳細

#### island_detector.py（新規作成）
```python
# 移動対象
- remove_garbage_keep_largest_island() の内部ロジック
  - 連結成分ラベリング
  - 最大島の検出
  - マスク生成
```

#### image_cleanup.py（新規作成）
```python
# 移動対象
- despeckle()
- auto_cleanup_and_crop()
- add_center_guides()
```

---

## 実装優先順位

### Phase 1: 設定管理の分離（低リスク）
1. `ui/settings_manager.py` を作成
2. text_inserter_dialog.py から設定関数を移動
3. テスト実行・動作確認

### Phase 2: 画像分析の分離（中リスク）
1. `core/image_analysis.py` を作成
2. image_splitter.py から分析関数を移動
3. テスト実行・動作確認

### Phase 3: 背景除去の分離（高リスク）
1. `core/island_detector.py` を作成
2. 巨大な `remove_garbage_keep_largest_island` を分割
3. テスト実行・動作確認

---

## 注意事項

- 各フェーズ完了後に `uv run pre-commit run --all-files` と `uv run pytest` を実行
- GIMP環境での手動テストも必要（特にPhase 2, 3）
- インポートパスの変更に注意（他モジュールからの参照を確認）
- `_debug_log` 関数は各モジュールでローカルに定義するか、共通ユーティリティに移動
- 純粋関数 + 小さなデータ構造に寄せるのを目指す（特に内部)
- test戦略
  - characterization test（現状の出力を固定するテスト）
  - 画像系なら golden master（期待画像 or 期待メトリクス）
  - ピクセル完全一致が難しければ、差分許容（PSNR/SSIM的な近似や、二値化後の一致率など）でも良い
- **各新モジュールの公開API（関数シグネチャ）**を先に決める
- フェーズごとに characterization test を追加してから移動
- 目標指標を「行数」だけでなく
  - 依存（I/Oの境界数）
  - 循環依存ゼロ
  - 重要ロジックの分岐カバレッジ

---

## 期待される効果

- 各モジュールが単一責任に近づく
- テストの書きやすさ向上
- コードの見通しが改善
- 将来の機能追加が容易に
