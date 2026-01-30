# トラブルシューティングガイド

GIMP 3 Python API開発で遭遇した問題と解決策をまとめたガイドです。

---

## 🔍 デバッグの基本戦略

### 1. 公式ドキュメントを参照する

GIMP 3はAPIが大きく変更されており、古い情報が役に立たないことが多いです。**必ず公式ドキュメントを参照してください**。

**主要なリソース：**
- **GIMP 3 API Reference**: https://www.gimp.org/docs/python-fu.html
- **GObject Introspection (gi.repository)**: https://gi.readthedocs.io/
- **GIMP Developer Resources**: https://developer.gimp.org/
- **GIMP GitLab Issues**: https://gitlab.gnome.org/GNOME/gimp/-/issues
  - 既知の問題やバグレポートを検索できる

**検索のコツ：**
```
# 良い検索クエリの例
"GIMP 3 select_ellipse python"
"GIMP 3.0 Python-Fu API"
"gi.repository.Gimp Selection"

# 避けるべき検索
"GIMP python-fu" (GIMP 2の情報が混ざる)
"pdb.gimp_*" (古いPDB形式の情報)
```

### 2. Python-Fuコンソールで検証する

**重要**: コードを書く前に、必ずPython-Fuコンソールで動作確認してください。

#### Python-Fuコンソールの起動方法

1. GIMPを起動
2. メニューから **Filters > Python-Fu > Console** を選択
3. インタラクティブなPythonシェルが開く

#### 基本的な使い方

```python
# 現在開いている画像を取得
image = Gimp.get_images()[0]
print(f"Image size: {image.get_width()}x{image.get_height()}")

# レイヤーを取得
layers = image.get_layers()
layer = layers[0]
print(f"Layer name: {layer.get_name()}")

# 楕円選択を試す
image.select_ellipse(
    Gimp.ChannelOps.REPLACE,
    100, 100,  # x, y
    200, 200,  # width, height
)

# 選択範囲を確認
has_selection = Gimp.Selection.is_empty(image)
print(f"Has selection: {not has_selection}")
```

#### デバッグTips

**タブ補完を活用する:**
```python
# オブジェクトのメソッドを調べる
image.  # ここでTabキーを押すと利用可能なメソッド一覧が表示される
Gimp.Selection.  # 同様にTabで補完
```

**型を確認する:**
```python
# オブジェクトの型を確認
print(type(image))
# <class 'gi.repository.Gimp.Image'>

# 列挙型の値を確認
print(Gimp.ChannelOps.REPLACE)
# <enum GIMP_CHANNEL_OP_REPLACE of type Gimp.ChannelOps>
```

**エラーを確認する:**
```python
# エラーが出たら、詳細を確認
try:
    image.select_ellipse(...)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
```

### 3. 最小再現コードで検証する

問題が起きたら、最小限のコードで再現できるか確認します。

```python
# ❌ 複雑すぎて原因特定が困難
def complex_function():
    # 100行のコード
    ...

# ✅ 最小再現コード
image = Gimp.get_images()[0]
image.select_ellipse(Gimp.ChannelOps.REPLACE, 0, 0, 100, 100)
# → これで動作確認できる
```

---

## 🐛 よくある問題と解決策

### 1. 楕円選択が作成されない

#### 症状
```python
image.select_ellipse(Gimp.ChannelOps.REPLACE, x, y, w, h)
# 選択範囲が作成されない、またはエラーが出る
```

#### 原因と解決策

**原因1: 幅・高さが0以下**
```python
# ❌ 動かない
ellipse_w = width - padding * 2  # パディングが大きすぎて負の値
image.select_ellipse(op, x, y, ellipse_w, ellipse_h)

# ✅ 動く
ellipse_w = max(1, width - padding * 2)
ellipse_h = max(1, height - padding * 2)
image.select_ellipse(op, x, y, ellipse_w, ellipse_h)
```

**原因2: アンチエイリアス/フェザー設定が未設定**
```python
# ✅ コンテキスト設定を忘れずに
Gimp.context_push()
try:
    Gimp.context_set_antialias(True)
    Gimp.context_set_feather(False)
    image.select_ellipse(...)
finally:
    Gimp.context_pop()
```

**原因3: 画像がロックされている**
```python
# レイヤーのロック状態を確認
if layer.get_lock_content():
    layer.set_lock_content(False)
```

### 2. 列挙型（Enum）の値が見つからない

#### 症状
```python
AttributeError: type object 'Gimp.ImageType' has no attribute 'GRAY'
```

#### 原因
GIMP 3では列挙型の名前が変更されています。

#### 解決策

**Python-Fuコンソールで利用可能な値を確認：**
```python
# 列挙型の値を一覧表示
import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

# ImageType → ImageBaseType
print([x for x in dir(Gimp.ImageBaseType) if not x.startswith('_')])
# ['GRAY', 'INDEXED', 'RGB']

# ChannelOps
print([x for x in dir(Gimp.ChannelOps) if not x.startswith('_')])
# ['ADD', 'INTERSECT', 'REPLACE', 'SUBTRACT']
```

**よくある間違い：**
```python
# ❌ GIMP 2の古いコード
Gimp.ImageType.GRAY

# ✅ GIMP 3の正しいコード
Gimp.ImageBaseType.GRAY
```

### 3. PDB（Procedural Database）の呼び出しエラー

#### 症状
```python
AttributeError: 'Pdb' object has no attribute 'gimp_selection_invert'
```

#### 原因
GIMP 3ではOOPスタイルのメソッド呼び出しが推奨されます。

#### 解決策

**PDBプロシージャ → OOPメソッドへの変換表：**

| GIMP 2 (PDB) | GIMP 3 (OOP) |
|--------------|--------------|
| `pdb.gimp_selection_none(image)` | `Gimp.Selection.none(image)` |
| `pdb.gimp_selection_invert(image)` | `Gimp.Selection.invert(image)` |
| `pdb.gimp_selection_is_empty(image)` | `Gimp.Selection.is_empty(image)` |
| `pdb.gimp_edit_clear(layer)` | `layer.edit_clear()` |
| `pdb.gimp_image_select_ellipse(...)` | `image.select_ellipse(...)` |
| `pdb.gimp_layer_resize_to_image_size(layer)` | `layer.resize_to_image_size()` |

**Python-Fuコンソールで確認する方法：**
```python
# オブジェクトのメソッドを探す
image = Gimp.get_images()[0]
[m for m in dir(image) if 'select' in m.lower()]
# ['select_color', 'select_contiguous_color', 'select_ellipse', 'select_item', ...]

# Selectionクラスのメソッドを探す
[m for m in dir(Gimp.Selection) if not m.startswith('_')]
# ['all', 'border', 'bounds', 'feather', 'flood', 'grow', 'invert', 'is_empty', 'none', ...]
```

### 4. Geglバッファアクセスの問題

#### 症状
```python
buffer = layer.get_buffer()
data = buffer.get_data()  # エラーまたは空のデータ
```

#### 原因
GIMP 3のGeglバッファアクセスはPython APIで直接サポートされていない場合があります。

#### 解決策

**代替アプローチ1: Gegl.Buffer.linear_from_data()を使用**
```python
from gi.repository import Gegl

# バッファからデータを取得
buffer = layer.get_buffer()
pixel_rgn = buffer.get_property('pixel-rgn')
# ... 複雑な処理が必要
```

**代替アプローチ2: ピクセルアクセスを避ける**
```python
# ✅ ピクセルレベルのアクセスを避け、GIMP APIを使う
# 楕円選択で背景除去 → ピクセル操作不要
image.select_ellipse(...)
Gimp.Selection.invert(image)
layer.edit_clear()
```

### 5. `drawable.edit_clear()`が効かない

#### 症状
```python
layer.edit_clear()  # 何も起きない
```

#### 原因と解決策

**原因1: 選択範囲がない**
```python
# 選択範囲があるか確認
has_selection = not Gimp.Selection.is_empty(image)
print(f"Has selection: {has_selection}")

if has_selection:
    layer.edit_clear()
```

**原因2: レイヤーにアルファチャンネルがない**
```python
# アルファチャンネルを追加
if not layer.has_alpha():
    layer.add_alpha()

layer.edit_clear()
```

**原因3: アンドゥグループ内で実行していない**
```python
# アンドゥグループで囲む（推奨）
image.undo_group_start()
try:
    layer.edit_clear()
finally:
    image.undo_group_end()
```

### 6. インポートエラー

#### 症状
```python
ModuleNotFoundError: No module named 'gi.repository.Gimp'
```

#### 原因
GIMPの外でPythonスクリプトを実行している。

#### 解決策

**GIMP内で実行する必要がある:**
- GIMPプラグインとして実行
- Python-Fuコンソールで実行

**GIMP外でテストする場合（モック）:**
```python
# tests/mocks/gimp_mocks.py
try:
    from gi.repository import Gimp
except ImportError:
    # テスト環境用のモック
    class Gimp:
        class Image:
            pass
        class Layer:
            pass
```

---

## 📚 デバッグのベストプラクティス

### 1. 段階的に実装する

```python
# ❌ 一度に全部実装
def complex_background_removal():
    # 100行のコード
    ...

# ✅ 段階的に実装・検証
def step1_create_selection():
    image.select_ellipse(...)
    # Python-Fuコンソールで確認

def step2_invert_selection():
    Gimp.Selection.invert(image)
    # Python-Fuコンソールで確認

def step3_clear_background():
    layer.edit_clear()
    # Python-Fuコンソールで確認
```

### 2. ログ出力を活用する

```python
def _debug_log(msg: str) -> None:
    """デバッグログ（GIMP Error Console に表示）"""
    print(f"[DEBUG] {msg}")

# 使用例
_debug_log(f"Image size: {width}x{height}")
_debug_log(f"Ellipse params: ({x}, {y}, {w}, {h})")
```

### 3. エラーハンドリングを追加する

```python
try:
    image.select_ellipse(op, x, y, w, h)
except Exception as e:
    _debug_log(f"Failed to create ellipse selection: {e}")
    _debug_log(f"Parameters: op={op}, x={x}, y={y}, w={w}, h={h}")
    raise
```

### 4. コンテキスト管理を徹底する

```python
# ✅ 必ずcontext_push/popで囲む
Gimp.context_push()
try:
    # 設定変更
    Gimp.context_set_antialias(True)
    # 処理
    image.select_ellipse(...)
finally:
    # 必ず元に戻す
    Gimp.context_pop()
```

---

## 🔗 参考リソース

### 公式ドキュメント
- [GIMP 3 Developer Resources](https://developer.gimp.org/)
- [GObject Introspection Documentation](https://gi.readthedocs.io/)
- [PyGObject API Reference](https://lazka.github.io/pgi-docs/)

### コミュニティ
- [GIMP GitLab Issues](https://gitlab.gnome.org/GNOME/gimp/-/issues)
- [GIMP Forum - Scripting Questions](https://www.gimp-forum.net/)
- [Stack Overflow - gimp tag](https://stackoverflow.com/questions/tagged/gimp)

### 内部ドキュメント
- `docs/decisions/001-ellipse-based-background-removal.md` - 設計判断の記録
- `CHANGELOG.md` - 変更履歴
- `docs/testing_strategy.md` - テスト戦略

---

## 💡 よくある質問

### Q: GIMP 2のコードをGIMP 3に移植したい

**A:** 以下の手順で移植してください：

1. PDB呼び出し → OOPメソッドに変換
2. 列挙型の名前を確認（`ImageType` → `ImageBaseType`など）
3. Python-Fuコンソールで動作確認
4. 公式ドキュメントで最新のAPI仕様を確認

### Q: Python-Fuコンソールで試したコードがプラグインで動かない

**A:** 以下を確認してください：

1. コンテキスト設定（`Gimp.context_push/pop`）
2. アンドゥグループ（`image.undo_group_start/end`）
3. エラーハンドリング
4. ログ出力でパラメータを確認

### Q: どのメソッドが使えるか分からない

**A:** Python-Fuコンソールで調べてください：

```python
# オブジェクトのメソッド一覧
dir(image)

# メソッドのヘルプ
help(image.select_ellipse)

# 列挙型の値
dir(Gimp.ChannelOps)
```

---

## 🛠️ 開発環境のセットアップ

### Python-Fuコンソールの設定

**ログを見やすくする:**
1. Filters > Python-Fu > Console を開く
2. **Settings** タブで以下を設定：
   - Font size: 12pt（見やすいサイズに）
   - Save output: チェック（ログを保存）
   - Output directory: `C:\temp\gimp-python-fu\`（任意）

### GIMP Error Consoleの活用

1. Windows > Dockable Dialogs > Error Console
2. `print()`の出力がここに表示される
3. デバッグログとして活用

---

このガイドは、実際の開発で遭遇した問題と解決策をまとめたものです。新しい問題が見つかったら、随時追加してください。
