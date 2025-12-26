# TachoGraphWizard: タコグラフチャート画像処理ウィザード for GIMP 3

## プロジェクト概要
A3スキャン画像に含まれる複数のタコグラフチャート（円盤状記録紙）を、**ブラックボックス化せず**インタラクティブに確認しながら処理するためのGIMP 3向けワークフローです。

### 主な機能
- スキャン画像の**分割**（ガイド分割／自動検出）
- 背景の**ゴミ取り＋透明化（Color to Alpha）**
- 円盤の**回転補正（Correctiveモード対応）**
- **文字入れ**（CSV読み込み対応、テンプレート管理、位置比率管理）
- **PNG（アルファ付き）**で保存

### 提供プラグイン
1. **Tachograph Chart Wizard** - 画像処理プラグイン（分割・背景透明化・保存）
2. **Tachograph Text Inserter** - テキスト挿入プラグイン（CSV・テンプレート対応）

---

## 要件定義
- **入力**：PDFまたはJPEG（A3スキャン、最大6枚の円盤）
- **出力**：アルファチャンネル付きPNG
- **操作性**：逐次確認型（プレビュー＋OK／やり直し／スキップ）
- **非機能要件**：Windows 11 / GIMP 3.0.6対応、OSSライセンス（MIT推奨）

---

## 技術スタック
- **基盤**：GIMP 3.0.6（Windows 11）
- **プラグイン**：Python 3.12+ + GIMP API（Gimp/GimpUi）
- **依存関係**：なし（標準ライブラリのみ使用）
- **補助ツール**：Slice Using Guides、Divide Scanned Images、Batcher（GIMP 3対応）

---

## インストール

### 前提条件
- GIMP 3.0以降がインストールされていること
- Python 3.12以降がインストールされていること

### 手順

1. **依存関係のインストール**
```bash
# プロジェクトディレクトリで実行
uv sync
```

2. **プラグインのインストール**
GIMP 3のプラグインディレクトリにシンボリックリンクまたはコピーを作成します。

**Windows**:
```bash
# GIMPのプラグインディレクトリを確認
# 通常: C:\Users\<ユーザー名>\AppData\Roaming\GIMP\3.0\plug-ins\

# プラグインディレクトリにコピー
xcopy /E /I src\tachograph_wizard "C:\Users\<ユーザー名>\AppData\Roaming\GIMP\3.0\plug-ins\tachograph_wizard"
```

3. **GIMPを再起動**

4. **プラグインの確認**
- メニューから **Filters > Processing** を開く
- **Tachograph Chart Wizard...** と **Tachograph Text Inserter...** が表示されることを確認

---

## 処理フロー
1. **分割**：ガイド分割（Slice Using Guides）または自動分割（Divide Scanned Images）
2. **背景透明化**：Color to Alphaで白背景を透過
3. **回転補正**：Correctiveモードで目視＋数値入力orマウスドラッグ 補助線活用
4. **文字入れ**：テンプレート選択＋日付選択＋CSV読み込み
5. **保存**：命名規則（例：YYYYMMDD_車番_運転手.png）でPNG出力

---

## 使い方

### Tachograph Text Inserter プラグイン

#### 1. CSVファイルの準備
`examples/sample_data.csv` を参考に、車両マスタCSVを作成します（必須列: `vehicle_type`, `vehicle_no`, `driver`）。

```csv
vehicle_type,vehicle_no,driver
普通車,123-45,山田太郎
トラック,678-90,佐藤花子
```

**重要**: CSVファイルはUTF-8エンコーディングで保存してください。
**日付**: CSVに `date` または `date_year/date_month/date_day` がある場合はその値を使用し、無い場合はUIで選択した日付を全行に適用します。

#### 2. プラグインの起動
1. GIMP 3で画像を開く
2. メニューから **Filters > Processing > Tachograph Text Inserter...** を選択

#### 3. テキスト挿入
1. **テンプレートフォルダ選択（任意）**: 「Template Folder」でカスタムテンプレートの場所を選び、「Load Templates」をクリック
2. **テンプレート選択**: ドロップダウンから使用するテンプレートを選択（デフォルト: standard）
3. **CSV読み込み**: 「Load CSV」ボタンをクリックして、CSVファイルを選択
4. **日付選択**: 前回選択値があればそれを初期値にし、無い場合は当日を設定
5. **行選択**: スピナーで挿入するデータ行を選択（プレビューで確認可能）
6. **テキスト挿入**: 「Insert Text」ボタンをクリックしてテキストレイヤーを作成

#### テンプレートのカスタマイズ
テンプレートは `src/tachograph_wizard/templates/default_templates/` に配置されています。
JSONファイルを編集して、テキストの位置、フォント、色などをカスタマイズできます。

詳細は `docs/phase2_implementation.md` を参照してください。

---

## UI設計（ウィザード型）
- ステップ型ダイアログ：分割 → 透明化 → 回転 → 文字入れ → 保存
- 各工程でプレビュー表示、操作ボタン（OK／やり直し／スキップ／次へ）

---

## リポジトリ構成
```
/README.md            # 本ドキュメント
/docs/                # UIモック・設計資料
/templates/           # XCFテンプレート（A/B/C）
/samples/             # 入出力サンプル（匿名化）
/LICENSE              # MIT推奨
```

---

## 公開運用
- GitHub Public（無料プラン）
- サンプル画像は匿名・低解像度化
- Issue/PRテンプレートで標準化

---

## ロードマップ
1. テンプレート設計（A/B/C）
2. 標準機能で運用開始（Slice Using Guides＋Color to Alpha）
3. ウィザードUIプロトタイプ開発
4. Batcher併用で定型工程を一括化
5. README・運用ガイド整備

---

## ライセンス
MIT License
