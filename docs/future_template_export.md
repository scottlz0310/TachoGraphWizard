# テンプレートエクスポート機能（将来実装）

## 概要
GIMP上で手動調整したテキストレイヤーの設定を読み取り、テンプレートJSONとしてエクスポートする機能。

## ユーザーワークフロー

1. **初期テキスト挿入**
   - 既存のテンプレート（例：standard）を使用してテキスト挿入
   - または空のテンプレートから開始

2. **GIMP上で手動調整**
   - テキストレイヤーの位置を移動
   - フォントサイズを変更
   - フォント種類を変更
   - テキスト色を変更
   - レイヤー名でフィールド名を識別

3. **テンプレートエクスポート**
   - プラグインメニューから「Export Template」を実行
   - 画像内のテキストレイヤーを自動検出
   - 各レイヤーの設定を読み取る
   - 位置を比率に変換（解像度非依存）
   - 新しいテンプレートJSONとして保存

4. **次回からの使用**
   - エクスポートしたテンプレートが自動的にリストに追加される
   - 「Select Template」で選択可能になる

## 実装要件

### 必要な情報の読み取り

**テキストレイヤーから取得:**
- レイヤー名 → フィールド名（"Text: field_name" パターン）
- テキスト内容 → サンプル（optional）
- 位置（x, y） → 画像サイズで割って比率に変換
- フォントサイズ → 画像の短辺で割って比率に変換
- フォント種類 → `layer.get_font()` または text layer APIs
- テキスト色 → `layer.get_color()` または text layer APIs
- 配置情報 → レイヤーの境界ボックスと位置から推測

### API調査項目
- `Gimp.TextLayer` の利用可能なメソッド
- フォント情報の取得方法
- テキスト色の取得方法
- テキスト配置（align, vertical_align）の取得/推測方法

### UI設計

**ダイアログ:**
1. 検出されたテキストレイヤーのリスト表示
2. 各フィールドの設定プレビュー
3. テンプレート名入力
4. 保存先選択（デフォルト: `templates/default_templates/`）
5. 「Export」ボタン

### 技術的課題

1. **配置の推測**
   - レイヤーの境界ボックスと実際の位置から、left/center/right と top/middle/bottom を推測
   - または、ユーザーに手動選択させる

2. **フォント名の互換性**
   - システムフォント名を適切に保存
   - 異なる環境でのフォールバック対応

3. **既存テンプレートとの競合**
   - 同名テンプレートの上書き確認
   - バージョン管理

## 実装フェーズ

### Phase 1: 基本情報の読み取り
- テキストレイヤーの検出
- 位置、サイズの取得と変換
- 基本的なJSON生成

### Phase 2: フォント情報の取得
- フォント種類、サイズ、色の読み取り
- GIMP 3 APIの調査と実装

### Phase 3: UI実装
- エクスポートダイアログの作成
- プレビュー機能
- テンプレート保存機能

### Phase 4: 高度な機能
- 配置の自動推測
- テンプレートの検証
- エラーハンドリング

## 関連ファイル

- 新規作成: `src/tachograph_wizard/procedures/template_exporter_procedure.py`
- 新規作成: `src/tachograph_wizard/ui/template_exporter_dialog.py`
- 新規作成: `src/tachograph_wizard/core/template_exporter.py`
- 更新: `src/tachograph_wizard/tachograph_wizard.py` (プロシージャ登録)

## 参考リンク

- GIMP 3 Python API: TextLayer
- GIMP 3 PDB: text-layer-get-* procedures
