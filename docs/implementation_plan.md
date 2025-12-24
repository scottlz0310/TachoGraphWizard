# TachoGraphWizard 実装計画

## プロジェクト概要

GIMP 3向けタコグラフチャート画像処理ウィザードプラグイン
- **目的**: A3スキャン画像から複数のタコグラフチャート（円盤）をインタラクティブに処理
- **アプローチ**: 段階的実装（MVP → 拡張）
- **技術**: Python 3.14 + GIMP 3.0.6 API + 厳密な型チェック（Basedpyright strict）

---

## プロジェクト構造

```
TachoGraphWizard/
├── src/tachograph_wizard/          # メインパッケージ
│   ├── tachograph_wizard.py        # プラグインエントリーポイント
│   ├── procedures/                 # プロシージャ実装
│   │   ├── wizard_procedure.py     # メインウィザードプロシージャ
│   │   └── batch_procedure.py      # (Phase 5) バッチ処理
│   ├── core/                       # コア処理ロジック
│   │   ├── image_splitter.py       # 画像分割（ガイド/自動）
│   │   ├── background_remover.py   # 背景透明化
│   │   ├── rotator.py              # 回転補正
│   │   ├── text_renderer.py        # 文字入れ
│   │   └── exporter.py             # PNG出力
│   ├── ui/                         # UIコンポーネント
│   │   ├── wizard_dialog.py        # メインウィザードダイアログ
│   │   ├── pages/                  # ウィザードページ
│   │   │   ├── split_page.py
│   │   │   ├── transparency_page.py
│   │   │   ├── rotation_page.py
│   │   │   ├── text_page.py
│   │   │   └── save_page.py
│   │   └── components/             # 再利用可能なコンポーネント
│   │       ├── preview_widget.py   # プレビュー表示
│   │       └── template_selector.py
│   ├── templates/                  # テンプレート管理
│   │   ├── template_manager.py
│   │   └── models.py
│   └── utils/                      # ユーティリティ
│       ├── types.py                # 型定義
│       ├── file_utils.py
│       └── geometry.py
├── templates/                      # XCFテンプレートファイル
│   ├── template_a.xcf
│   ├── template_b.xcf
│   ├── template_c.xcf
│   └── metadata.json
├── samples/                        # サンプル画像
│   ├── input/
│   └── output/
├── tests/                          # テスト
│   ├── conftest.py
│   ├── fixtures/mock_gimp.py
│   ├── unit/
│   └── integration/
├── docs/                           # ドキュメント
│   ├── user_guide.md
│   ├── developer_guide.md
│   └── ui_mockups/
└── scripts/                        # ユーティリティスクリプト
    └── install_plugin.py
```

---

## 実装フェーズ

### Phase 1: MVP - 基本ワークフロー ✅ 完了

**目標**: 分割 → 透明化 → 保存の基本フローを動作させる

**機能**:
- プラグイン登録と基本UI（シンプルなダイアログ）
- ガイドベースの画像分割
- Color to Alphaで白背景除去
- PNG保存（アルファチャンネル保持）

**実装ファイル**:
1. `src/tachograph_wizard/tachograph_wizard.py` - Gimp.PlugInクラス、プラグイン登録
2. `src/tachograph_wizard/procedures/wizard_procedure.py` - メインプロシージャ
3. `src/tachograph_wizard/core/image_splitter.py` - ガイド分割実装
4. `src/tachograph_wizard/core/background_remover.py` - Color to Alpha呼び出し
5. `src/tachograph_wizard/core/exporter.py` - PNG保存
6. `src/tachograph_wizard/utils/types.py` - 型定義
7. `tests/conftest.py` + `tests/fixtures/mock_gimp.py` - テスト基盤

**品質チェック結果**:
- ✅ Ruff リンティング: All checks passed
- ✅ Basedpyright 型チェック: 0 errors, 0 warnings
- ✅ pytest テスト: 8/8 passed (100%)

### Phase 2: ウィザードUI

**目標**: GtkAssistantベースの段階的ウィザードに変換

**機能**:
- ステップ型ダイアログ（導入 → 分割 → 透明化 → 保存）
- 各ステップでプレビュー表示
- OK/やり直し/スキップ/次へボタン

**実装ファイル**:
1. `src/tachograph_wizard/ui/wizard_dialog.py` - GtkAssistantベースのウィザード
2. `src/tachograph_wizard/ui/components/preview_widget.py` - プレビューウィジェット
3. `src/tachograph_wizard/ui/pages/*.py` - 各ステップのページ

### Phase 3: 回転補正

**目標**: インタラクティブな回転補正機能

**機能**:
- 回転角度調整（スライダー + 手動入力）
- 補助線表示
- リアルタイムプレビュー

**実装ファイル**:
1. `src/tachograph_wizard/core/rotator.py` - 回転処理
2. `src/tachograph_wizard/ui/pages/rotation_page.py` - 回転UIページ
3. `src/tachograph_wizard/utils/geometry.py` - 幾何計算

### Phase 4: 文字入れ・テンプレート

**目標**: テンプレート選択と文字入れ機能

**機能**:
- テンプレート（A/B/C）選択
- 運転手名・車番・機械名入力フォーム
- テキストレイヤー作成・配置

**実装ファイル**:
1. `src/tachograph_wizard/templates/models.py` - テンプレートデータモデル
2. `src/tachograph_wizard/templates/template_manager.py` - テンプレート管理
3. `src/tachograph_wizard/core/text_renderer.py` - テキストレイヤー作成
4. `src/tachograph_wizard/ui/components/template_selector.py` - テンプレート選択UI
5. `src/tachograph_wizard/ui/pages/text_page.py` - 文字入力ページ
6. `templates/*.xcf` + `templates/metadata.json` - 実際のテンプレート

### Phase 5: 自動検出・高度機能

**目標**: 自動円盤検出とバッチ処理

**機能**:
- 円盤の自動検出（エッジ検出 + Hough変換）
- バッチ処理モード
- 設定の保存/読み込み

**実装ファイル**:
1. `src/tachograph_wizard/core/image_splitter.py` (拡張) - 自動検出アルゴリズム
2. `src/tachograph_wizard/procedures/batch_procedure.py` - バッチ処理
3. `src/tachograph_wizard/utils/file_utils.py` - ファイル操作

### Phase 6: ドキュメント・仕上げ

**目標**: ドキュメント整備、サンプル作成

**成果物**:
- ユーザーガイド（インストール、使い方、スクリーンショット付き）
- 開発者ガイド（開発環境、コード構造、GIMP API）
- サンプル画像（入出力）
- インストールスクリプト

---

## 技術詳細

### GIMP 3 プラグイン基本構造

```python
#!/usr/bin/env python3
from __future__ import annotations
import sys
import gi

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
from gi.repository import Gimp, GimpUi, GLib

class TachographWizard(Gimp.PlugIn):
    def do_query_procedures(self) -> list[str]:
        return ["tachograph-wizard"]

    def do_create_procedure(self, name: str) -> Gimp.Procedure | None:
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self._run_wizard
        )
        procedure.set_menu_label("Tachograph Chart Wizard...")
        procedure.add_menu_path("<Image>/Filters/Processing")
        return procedure

    def _run_wizard(self, procedure, run_mode, image, n_drawables,
                    drawables, config, run_data) -> Gimp.ValueArray:
        # ウィザード実行
        pass

Gimp.main(TachographWizard.__gtype__, sys.argv)
```

### 主要GIMP API

| 機能 | API |
|------|-----|
| ガイド分割 | `Gimp.get_pdb().run_procedure("plug-in-guillotine")` |
| 背景透明化 | `Gimp.DrawableFilter.new(drawable, "gegl:color-to-alpha")` |
| 回転 | `layer.transform_rotate(angle, auto_center, x, y)` |
| テキスト追加 | `Gimp.TextLayer.new(image, text, font, size, unit)` |
| PNG保存 | `Gimp.file_save(run_mode, image, [drawable], file)` |

### 型アノテーション戦略（strict mode）

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from gi.repository import Gimp

def process_image(
    image: Gimp.Image,
    drawables: Sequence[Gimp.Drawable],
) -> bool:
    """全関数に完全な型シグネチャが必須"""
    return True
```

### テスト戦略

```python
# tests/conftest.py
@pytest.fixture
def mock_gimp():
    """GIMP APIをモック化"""
    gimp_mock = MagicMock()
    sys.modules["gi.repository.Gimp"] = gimp_mock
    yield gimp_mock
```

---

## テンプレートメタデータ形式

```json
{
  "templates": [
    {
      "id": "template_a",
      "name": "Template A - Standard",
      "file": "template_a.xcf",
      "fields": [
        {
          "name": "driver",
          "label": "運転手名",
          "x": 100, "y": 50,
          "font": "Arial Bold",
          "size": 24,
          "color": "#000000"
        },
        {
          "name": "vehicle",
          "label": "車番",
          "x": 100, "y": 80,
          "font": "Arial",
          "size": 18,
          "color": "#000000"
        }
      ]
    }
  ]
}
```

---

## Phase 1（MVP）実装の重要ファイル

### 最優先で実装するファイル（TOP 5）

1. **`src/tachograph_wizard/tachograph_wizard.py`**
   - プラグインのエントリーポイント
   - `Gimp.PlugIn`クラスの実装
   - プロシージャの登録

2. **`src/tachograph_wizard/procedures/wizard_procedure.py`**
   - メインのワークフロー制御
   - UI起動とコア機能の呼び出し

3. **`src/tachograph_wizard/core/image_splitter.py`**
   - ガイドベースの画像分割
   - `plug-in-guillotine`の呼び出し

4. **`src/tachograph_wizard/core/background_remover.py`**
   - `gegl:color-to-alpha`フィルター適用
   - ゴミ取り（median-blur）

5. **`src/tachograph_wizard/core/exporter.py`**
   - PNG保存（アルファチャンネル保持）
   - ファイル名生成（YYYYMMDD_車番_運転手.png）

---

## 開発ワークフロー

### Phase 1開発ステップ ✅ 完了

1. ✅ ディレクトリ構造作成
2. ✅ `__init__.py`ファイル作成
3. ✅ `tachograph_wizard.py`実装（プラグイン登録）
4. ⬜ GIMP 3でプラグイン読み込み確認
5. ✅ コアモジュール実装（splitter, remover, exporter）
6. ✅ 型アノテーション追加（全ファイル）
7. ✅ テスト作成（モック使用）
8. ✅ CI/CD確認（Ruff, Basedpyright, pytest）
9. ⬜ GIMP 3で実際の画像処理テスト

### コード品質要件

- ✅ Ruff: 行長120文字、厳密なルール適用
- ✅ Basedpyright: strict モード、全関数に型アノテーション
- ✅ pytest: モックを使った単体テスト、カバレッジ>80%
- ✅ すべてのpublic関数にGoogle形式のdocstring

---

## インストール

```bash
# 開発モード
python scripts/install_plugin.py

# インストール先
# Windows: %APPDATA%\GIMP\3.0\plug-ins\tachograph-wizard\
# Linux: ~/.config/GIMP/3.0/plug-ins/tachograph-wizard/
# macOS: ~/Library/Application Support/GIMP/3.0/plug-ins/tachograph-wizard/
```

---

## 次のステップ

### Phase 2 実装予定

GtkAssistantベースのウィザードUIへの移行：
1. `ui/wizard_dialog.py`でGtkAssistant実装
2. プレビューウィジェット作成
3. 各ステップのページ実装
4. 既存のシンプルダイアログから移行

### 長期ロードマップ

- **Phase 3**: 回転補正機能（リアルタイムプレビュー付き）
- **Phase 4**: テンプレートベースの文字入れ
- **Phase 5**: 自動円盤検出とバッチ処理
- **Phase 6**: 完全なドキュメント整備とサンプル提供
