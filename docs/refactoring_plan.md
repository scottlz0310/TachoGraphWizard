# モジュール肥大化リファクタリング計画

## 1. 概要

### 1.1 リファクタリングの目的

本計画は、TachoGraphWizardプロジェクトにおける肥大化したモジュールを適切なサイズに分割し、保守性とテスト容易性を向上させることを目的とする。

### 1.2 目標指標

#### 定量的目標
- **行数**: 各モジュール300行以下を目安（厳密な制限ではない）
- **依存性**: I/O境界を明確化し、モジュール間の依存を最小化
- **循環依存**: ゼロを維持
- **テストカバレッジ**: 重要ロジックの分岐カバレッジを向上

#### 定性的目標
- 安定した公開API（呼び出し側の変更を最小化）
- テスト容易性（純粋関数化、I/O境界の明確化）
- 単一責任原則の遵守

---

## 2. 現状分析

### 2.1 モジュールサイズ一覧（行数降順）

| モジュール | 行数 | 状態 | 優先度 |
|-----------|------|------|--------|
| `core/image_splitter.py` | 778 | ⚠️ 要リファクタリング | 中 |
| `ui/text_inserter_dialog.py` | 753 | ⚠️ 要リファクタリング | 高 |
| `core/background_remover.py` | 702 | ⚠️ 要リファクタリング | 低 |
| `core/template_exporter.py` | 370 | 許容範囲 | - |
| `tachograph_wizard.py` | 343 | 許容範囲 | - |
| `procedures/wizard_procedure.py` | 272 | 許容範囲 | - |
| `core/pdb_runner.py` | 264 | 許容範囲 | - |
| その他 | <250 | OK | - |

---

## 3. モジュール分割計画

### 3.1 text_inserter_dialog.py (753行) - Phase 1

#### 3.1.1 現状の構造

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

#### 3.1.2 分割案

| 新モジュール | 責務 | 推定行数 | 依存性 |
|-------------|------|---------|--------|
| `ui/settings_manager.py` | 設定の永続化（読み書き） | ~150行 | pathlib, json |
| `core/filename_generator.py` | ファイル名生成ロジック | ~50行 | 純粋関数 |
| `ui/text_inserter_dialog.py` | ダイアログUI・イベント制御 | ~450行 | settings_manager, filename_generator |

#### 3.1.3 移動対象の詳細

**settings_manager.py（新規作成）**
```python
# 公開API
- get_settings_path() -> Path
- load_setting(key: str, default: Any) -> Any
- save_setting(key: str, value: Any) -> None

# 内部実装
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

**filename_generator.py（新規作成）**
```python
# 公開API
- generate_filename(row: dict, fields: list[str], extension: str) -> str

# 移動対象
- _generate_filename_from_row() ロジック部分
```

---

### 3.2 image_splitter.py (778行) - Phase 2

#### 3.2.1 現状の構造

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

#### 3.2.2 分割案

| 新モジュール | 責務 | 推定行数 | 依存性 |
|-------------|------|---------|--------|
| `core/image_analysis.py` | 画像分析（Otsu、コンポーネント検出） | ~200行 | GIMP API |
| `core/image_operations.py` | 画像操作（複製、クロップ、マスク） | ~200行 | GIMP API |
| `core/image_splitter.py` | 分割ロジック調整（公開API） | ~300行 | image_analysis, image_operations |

#### 3.2.3 移動対象の詳細

**image_analysis.py（新規作成）**
```python
# データクラス
- Component (旧_Component)

# 公開API
- get_image_dpi(image) -> float
- otsu_threshold(drawable) -> int
- find_components(drawable, threshold: int) -> list[Component]

# 内部実装
- _analysis_scale()
- _get_analysis_drawable()
- _buffer_get_bytes()
```

**image_operations.py（新規作成）**
```python
# 公開API
- duplicate_image(image) -> Image
- crop_image(image, x: int, y: int, width: int, height: int) -> Image
- apply_component_mask(drawable, component: Component) -> None

# 内部実装
- (必要に応じて内部関数を定義)
```

---

### 3.3 background_remover.py (702行) - Phase 3

#### 3.3.1 現状の構造

```
BackgroundRemover (静的メソッドのみのクラス)
  - color_to_alpha (~100行) - 現在未使用？
  - despeckle (~50行)
  - auto_cleanup_and_crop (~100行)
  - remove_garbage_keep_largest_island (~470行) - 巨大！
  - add_center_guides (~40行)
  - process_background (~30行)
```

#### 3.3.2 分割案

| 新モジュール | 責務 | 推定行数 | 依存�� |
|-------------|------|---------|--------|
| `core/island_detector.py` | 連結成分検出・最大島抽出 | ~300行 | numpy/GIMP |
| `core/image_cleanup.py` | ノイズ除去・クリーンアップ | ~150行 | GIMP API |
| `core/background_remover.py` | 背景除去の統合API | ~250行 | island_detector, image_cleanup |

#### 3.3.3 移動対象の詳細

**island_detector.py（新規作成）**
```python
# 公開API
- find_largest_island(drawable, threshold: int) -> Island
- remove_small_islands(drawable, min_size: int) -> None

# 移動対象（内部ロジック）
- remove_garbage_keep_largest_island() の分割
  - 連結成分ラベリング
  - 最大島の検出
  - マスク生成
```

**image_cleanup.py（新規作成）**
```python
# 公開API
- despeckle(drawable, radius: int) -> None
- auto_cleanup_and_crop(image) -> tuple[int, int, int, int]
- add_center_guides(image) -> None

# 移動対象
- despeckle()
- auto_cleanup_and_crop()
- add_center_guides()
```

---

## 4. 実装計画

### 4.1 フェーズ構成

各フェーズは以下の手順で進める：

1. **事前準備**: Characterization testの作成（現状の動作を固定）
2. **公開APIの設計**: 新モジュールのインターフェース定義
3. **モジュール作成**: 新ファイルの作成とコードの移動
4. **テスト実行**: 自動テスト + 手動テスト
5. **コードレビュー**: 品質確認とフィードバック

### 4.2 Phase 1: 設定管理の分離（低リスク）

**目的**: UI層からビジネスロジックを分離

**期間**: 1-2日

**手順**:
1. `ui/settings_manager.py` と `core/filename_generator.py` を作成
2. 公開APIを定義（型ヒント含む）
3. text_inserter_dialog.py から関数を移動
4. インポートパスを更新
5. テスト実行
   - `uv run pre-commit run --all-files`
   - `uv run pytest`
   - GIMP環境での手動テスト（設定保存・読み込み）

**リスク**: 低（I/O操作のみ、外部依存少ない）

### 4.3 Phase 2: 画像分析の分離（中リスク）

**目的**: 画像処理ロジックの責務分離

**期間**: 2-3日

**手順**:
1. `core/image_analysis.py` と `core/image_operations.py` を作成
2. 公開APIを定義
3. Characterization testを追加（画像メトリクスのゴールデンマスター）
4. image_splitter.py から関数を移動
5. 内部呼び出しを新モジュール経由に変更
6. テスト実行
   - 自動テスト（メトリクス比較）
   - GIMP環境での手動テスト（分割結果の目視確認）

**リスク**: 中（GIMP API依存、画像処理の正確性検証が必要）

### 4.4 Phase 3: 背景除去の分離（高リスク）

**目的**: 巨大関数の分割と責務の明確化

**期間**: 3-5日

**手順**:
1. `core/island_detector.py` と `core/image_cleanup.py` を作成
2. 公開APIを定義
3. Characterization testを追加（ピクセル単位の比較または近似メトリクス）
4. 巨大な `remove_garbage_keep_largest_island` を段階的に分割
   - まず内部で小関数に分割
   - 次に新モジュールに移動
5. テスト実行
   - 画像差分テスト（PSNR/SSIM許容範囲）
   - GIMP環境での手動テスト（背景除去結果の確認）

**リスク**: 高（470行の巨大関数、アルゴリズムの複雑性）

---

## 5. テスト戦略

### 5.1 Characterization Test

**目的**: リファクタリング前後で動作が変わらないことを保証

**手法**:
- 現状の出力を「正解」として記録
- リファクタリング後に同じ入力で同じ出力が得られることを確認

### 5.2 画像処理のテスト

#### ゴールデンマスター方式
- 期待される画像を保存
- テスト時に生成画像と比較

#### メトリクス方式（推奨）
- ピクセル完全一致が困難な場合
- PSNR（Peak Signal-to-Noise Ratio）
- SSIM（Structural Similarity Index）
- 二値化後の一致率

#### テスト対象
| テスト項目 | 手法 | 許容範囲 |
|-----------|------|---------|
| 画像分割位置 | ピクセル座標比較 | ±2px |
| 背景除去結果 | PSNR/SSIM | PSNR>30dB |
| ノイズ除去 | 二値化後の一致率 | >98% |

### 5.3 テスト実行タイミング

- **各コミット前**: `uv run pre-commit run --all-files`
- **各フェーズ完了後**: `uv run pytest` + GIMP手動テスト
- **最終確認**: 全フェーズ完了後の統合テスト

---

## 6. 実装上の注意事項

### 6.1 共通ガイドライン

- **公開APIの設計優先**: コードを移動する前にインターフェースを確定
- **型ヒントの徹底**: すべての公開関数に型アノテーションを付与
- **純粋関数化**: 可能な限り副作用を排除し、テスト容易性を向上
- **小さなコミット**: 機能単位で細かくコミットし、問題発生時のロールバックを容易に

### 6.2 モジュール間依存の管理

- **循環依存の禁止**: 依存グラフは常にDAG（有向非巡回グラフ）を維持
- **依存方向の原則**:
  - `ui` → `core`（UI層がコア層を使用）
  - `core` ↛ `ui`（コア層はUIを知らない）

### 6.3 `_debug_log` 関数の扱い

以下のいずれかの方針を選択：

**A. 共通ユーティリティ化**
```python
# core/logging_util.py を作成
def debug_log(message: str) -> None:
    """統一されたデバッグログ出力"""
    ...
```

**B. 各モジュールでローカル定義**
```python
# 各モジュール内で独自実装
def _debug_log(message: str) -> None:
    """モジュール固有のログ出力"""
    ...
```

**推奨**: オプションAで統一的なログ管理を実現

### 6.4 インポートパスの変更管理

- **影響範囲の確認**: 移動する関数/クラスの参照箇所をすべてリストアップ
- **段階的移行**:
  1. 新モジュールに実装を追加
  2. 旧モジュールで新モジュールをインポートし、互換性維持
  3. 呼び出し側を徐々に更新
  4. 旧モジュールの互換レイヤーを削除

---

## 7. 成功基準と期待される効果

### 7.1 定量的成功基準

- [ ] すべてのターゲットモジュールが300行以下
- [ ] テストカバレッジ: 新規コア関数の80%以上
- [ ] 循環依存: ゼロ
- [ ] 既存機能の動作: すべてのテストがパス

### 7.2 定性的成功基準

- [ ] 各モジュールが明確な単一責任を持つ
- [ ] 新規開発者がコードを理解しやすい
- [ ] 機能追加時の変更範囲が明確

### 7.3 期待される効果

#### 短期的効果
- コードレビューの効率化（変更範囲が小さく明確）
- バグ修正の迅速化（影響範囲の特定が容易）

#### 長期的効果
- 新機能開発の加速（既存コードの理解が容易）
- テストコードの充実（テスタブルな設計）
- 技術的負債の削減（保守コストの低減��

---

## 8. リスク管理

### 8.1 想定リスクと対策

| リスク | 発生確率 | 影響度 | 対策 |
|--------|---------|--------|------|
| リファクタリングによるバグ混入 | 中 | 高 | Characterization testの充実 |
| GIMP API依存による互換性問題 | 低 | 高 | 各フェーズで手動テスト実施 |
| 工数超過 | 中 | 中 | フェーズごとに進捗確認、必要に応じて範囲調整 |
| パフォーマンス劣化 | 低 | 中 | ベンチマークテストの実施 |

### 8.2 ロールバック計画

- 各フェーズは独立したブランチで実施
- 問題発生時は該当フェーズのブランチを破棄し、前フェーズに戻る
- mainブランチへのマージは全テストパス後のみ

---

## 9. 今後の展開

### 9.1 追加検討事項

- `core/template_exporter.py` (370行) の分割必要性を評価
- 共通データクラスの整理（複数モジュールで使用される型定義）
- ドキュメント整備（APIドキュメント、アーキテクチャ図）

### 9.2 継続的改善

- 定期的なモジュールサイズレビュー（月次）
- 新規コードへのサイズ制限ガイドラインの適用
- リファクタリング知見の共有（チーム内ドキュメント化）

---

## 10. 参考資料

- [Python コーディング規約（PEP 8）](https://peps.python.org/pep-0008/)
- [Clean Code by Robert C. Martin](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
- [Working Effectively with Legacy Code by Michael Feathers](https://www.oreilly.com/library/view/working-effectively-with/0131177052/)

---

## 11. 進捗管理

### 11.1 フェーズ別進捗状況

| フェーズ | 状態 | 開始日 | 完了日 | 担当者 | 備考 |
|---------|------|--------|--------|--------|------|
| Phase 1: 設定管理の分離 | ✅ 完了 | 2026-01-29 | 2026-01-29 | - | settings_manager.py, filename_generator.py 作成完了 |
| Phase 2: 画像分析の分離 | ✅ 完了 | 2026-01-29 | 2026-01-29 | - | image_analysis.py, image_operations.py 作成完了 |
| Phase 3: 背景除去の分離 | ⏳ 未着手 | - | - | - | - |

### 11.2 実施履歴

| 日付 | 内容 | 関連PR/Issue |
|------|------|-------------|
| 2026-01-29 | Phase 1 完了: settings_manager.py (約240行), filename_generator.py (約55行) の作成 | PR #38 |
| 2026-01-29 | Phase 1 検証: 全テスト (85件) パス、コード品質チェック完了 | PR #38 |
| 2026-01-29 | Phase 2 完了: image_analysis.py (264行), image_operations.py (265行) の作成 | PR #40 |
| 2026-01-29 | Phase 2 検証: 全テスト (103件) パス、コード品質チェック完了 | PR #40 |

### 11.3 Phase 1 完了サマリー

#### 作成されたモジュール

**src/tachograph_wizard/ui/settings_manager.py (約240行)**
- 設定ファイルの読み書き機能を提供
- JSON形式での永続化
- 型ヒント完備
- 公開API: `load_*()`, `save_*()`, `parse_date_string()`

**src/tachograph_wizard/core/filename_generator.py (約55行)**
- ファイル名生成ロジックの分離と副作用の最小化
  - 日付未指定時は実行時の `datetime.date.today()` を使用するため純粋関数ではないが、日付を引数で指定可能とすることでテスト容易性を高めた
- 公開API: `generate_filename()`

#### 品質指標

- ✅ テスト: 全85件パス (filename_generator: 11件, settings関連: 20件含む)
- ✅ コードカバレッジ: filename_generator 100%, settings_manager 71%
- ✅ コードフォーマット: ruff format チェック完了
- ✅ Lint: ruff check クリーン
- ✅ 型チェック: basedpyright エラー0件
- ✅ 循環依存: ゼロ

#### 残課題

- text_inserter_dialog.py の行数が802行 (目標450行に対して未達)
  - 原因: UI作成・イベントハンドラ部分が多い
  - 対応: Phase 2以降で UI コンポーネントの分離を検討

### 11.4 次回アクション

- [ ] Phase 1 の最終レビュー完了
- [ ] Phase 2 の着手判断と計画策定
- [ ] text_inserter_dialog.py のさらなる分割検討
