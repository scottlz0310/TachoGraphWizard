# Phase 2: Tachograph Text Inserter プラグイン実装計画

## 概要

新しいプラグイン「Tachograph Text Inserter」を作成し、処理済みのタコグラフ画像にテキストを配置する機能を提供します。

## 目標

- CSVファイルから車両情報を読み込み
- テンプレートに基づいてテキストを自動配置
- 解像度が変わっても正しく配置できる比率管理
- フォント・スタイルの柔軟な設定

## アーキテクチャ設計

### プラグイン構成

```
src/tachograph_wizard/
├── tachograph_wizard.py          # メインエントリーポイント（既存を拡張）
├── procedures/
│   ├── wizard_procedure.py       # 既存の画像処理プラグイン
│   └── text_inserter_procedure.py # 新規: テキスト挿入プラグイン
├── core/
│   ├── template_manager.py       # 新規: テンプレート管理
│   ├── text_renderer.py          # 新規: テキストレンダリング
│   └── csv_parser.py             # 新規: CSV読み込み
├── templates/
│   ├── __init__.py
│   ├── models.py                 # 新規: データモデル定義
│   └── default_templates/        # 新規: デフォルトテンプレート
│       └── standard.yaml
└── ui/
    └── text_inserter_dialog.py   # 新規: UI実装
```

## データモデル設計

### テンプレート構造（YAML形式）

```yaml
# templates/default_templates/standard.yaml
name: "Standard Tachograph Template"
version: "1.0"
description: "標準的なタコグラフ記録用テンプレート"

# 画像サイズの基準（ピクセル）
# テンプレート作成時の画像サイズ
reference_width: 1000
reference_height: 1000

# テキストフィールド定義
fields:
  vehicle_type:
    # 位置は画像サイズに対する比率（0.0～1.0）
    position:
      x_ratio: 0.1      # 左端から10%の位置
      y_ratio: 0.05     # 上端から5%の位置

    # フォント設定
    font:
      family: "Arial"
      size_ratio: 0.03  # 画像の短辺に対する比率
      color: "#000000"  # 黒
      bold: false
      italic: false

    # 配置設定
    align: "left"       # left, center, right
    vertical_align: "top"  # top, middle, bottom

    # オプション設定
    visible: true
    required: false     # 必須フィールドかどうか

  vehicle_no:
    position:
      x_ratio: 0.5
      y_ratio: 0.05
    font:
      family: "Arial"
      size_ratio: 0.04
      color: "#000000"
      bold: true
      italic: false
    align: "center"
    vertical_align: "top"
    visible: true
    required: true

  driver:
    position:
      x_ratio: 0.1
      y_ratio: 0.15
    font:
      family: "Arial"
      size_ratio: 0.025
      color: "#000000"
      bold: false
      italic: false
    align: "left"
    vertical_align: "top"
    visible: true
    required: false

  date_year:
    position:
      x_ratio: 0.7
      y_ratio: 0.05
    font:
      family: "Arial"
      size_ratio: 0.03
      color: "#000000"
      bold: false
      italic: false
    align: "right"
    vertical_align: "top"
    visible: true
    required: false

  date_month:
    position:
      x_ratio: 0.8
      y_ratio: 0.05
    font:
      family: "Arial"
      size_ratio: 0.03
      color: "#000000"
      bold: false
      italic: false
    align: "right"
    vertical_align: "top"
    visible: true
    required: false

  date_day:
    position:
      x_ratio: 0.9
      y_ratio: 0.05
    font:
      family: "Arial"
      size_ratio: 0.03
      color: "#000000"
      bold: false
      italic: false
    align: "right"
    vertical_align: "top"
    visible: true
    required: false
```

### CSV形式仕様

```csv
vehicle_type,vehicle_no,driver,date_year,date_month,date_day
普通車,123-45,山田太郎,2025,12,25
トラック,678-90,佐藤花子,2025,12,26
,999-99,鈴木次郎,2025,12,27
```

#### CSV仕様詳細

- **エンコーディング**: UTF-8（BOM付き推奨）
- **ヘッダー行**: 必須（フィールド名はテンプレートと一致）
- **必須列**: `vehicle_type`, `vehicle_no`, `driver`（車両マスタ）
- **空欄**: 空文字列として扱う（該当フィールドは非表示）
- **1行**: 1枚の画像に対応
- **日付**: `date_year`/`date_month`/`date_day` または `date` が存在する場合はその値を使用。存在しない場合はUIで選択した日付を全行に適用する。

#### 日付入力の運用方針

- Text Inserter はチャート紙1枚につき1回の実行とする
- 日付はダイアログで選択し、CSVには基本的に含めない（冗長化の回避）
- 日付初期値は「前回選択値があればそれ／なければ当日」
- 選択日付はテンプレートの `date_year`/`date_month`/`date_day` に展開して適用する
- 前回日付はプラグイン設定に保存して次回の初期値として利用する

## モジュール設計

### 1. `csv_parser.py` - CSV読み込み

```python
class CSVParser:
    @staticmethod
    def parse(file_path: Path) -> list[dict[str, str]]:
        """CSVファイルを読み込み、辞書のリストとして返す"""

    @staticmethod
    def validate_headers(headers: list[str], template_fields: list[str]) -> bool:
        """CSVヘッダーがテンプレートフィールドと一致するか検証"""
```

### 2. `template_manager.py` - テンプレート管理

```python
class TemplateManager:
    def load_template(self, template_path: Path) -> Template:
        """YAMLからテンプレートを読み込み"""

    def list_templates(self) -> list[str]:
        """利用可能なテンプレート一覧を取得"""

    def get_default_template(self) -> Template:
        """デフォルトテンプレートを取得"""
```

### 3. `text_renderer.py` - テキストレンダリング

```python
class TextRenderer:
    def __init__(self, image: Gimp.Image, template: Template):
        """初期化"""

    def render_text(self, field_name: str, text: str) -> Gimp.Layer:
        """テキストレイヤーを作成して配置"""
        # 1. 画像サイズを取得
        # 2. テンプレートの比率から実際のピクセル位置を計算
        # 3. フォントサイズを画像サイズから計算
        # 4. GIMPのテキストレイヤーを作成
        # 5. 位置を設定

    def render_all(self, data: dict[str, str]) -> list[Gimp.Layer]:
        """すべてのフィールドをレンダリング"""
```

### 4. `text_inserter_dialog.py` - UI実装

```python
class TextInserterDialog(GimpUi.Dialog):
    """テキスト挿入プラグインのUIダイアログ"""

    def __init__(self, image: Gimp.Image):
        # UI要素:
        # - テンプレート選択コンボボックス
        # - CSVファイル選択ボタン
        # - プレビュー領域（オプション）
        # - 実行ボタン

    def on_load_csv_clicked(self):
        """CSV読み込みボタンクリック時の処理"""

    def on_insert_text_clicked(self):
        """テキスト挿入ボタンクリック時の処理"""
```

### 5. `text_inserter_procedure.py` - プロシージャ実装

```python
def run_text_inserter_dialog(image: Gimp.Image, drawable: Gimp.Drawable | None) -> bool:
    """テキスト挿入ダイアログを実行"""
```

## 実装順序

### Phase 2.1: 基盤実装（最小機能）
1. データモデル定義（`templates/models.py`）
2. YAMLテンプレートローダー（`template_manager.py`）
3. デフォルトテンプレート作成（`standard.yaml`）
4. テキストレンダリング基礎（`text_renderer.py`）

### Phase 2.2: CSV統合
1. CSV読み込み機能（`csv_parser.py`）
2. CSV検証機能
3. バッチ処理機能（複数行のCSVを複数画像に適用）

### Phase 2.3: UI実装
1. シンプルなダイアログUI
2. テンプレート選択機能
3. CSVファイル選択機能
4. プレビュー機能（オプション）

### Phase 2.4: プラグイン統合
1. 新しいプロシージャの登録（`tachograph_wizard.py`）
2. メニューエントリの追加
3. 統合テスト

## プラグインメニュー構成

```
Filters > Processing >
  ├─ Tachograph Chart Wizard...        # 既存: 画像処理プラグイン
  └─ Tachograph Text Inserter...       # 新規: テキスト挿入プラグイン
```

## 依存関係

- Python 3.12+
- GIMP 3.0 Python-Fu API
- PyYAML（テンプレート読み込み用）

## 今後の拡張性

- テンプレートエディタUI（GUI上でテンプレート編集）
- JSON形式のテンプレートサポート
- プレビュー機能の強化
- 複数画像への一括適用
- カスタムフォントのサポート拡張
