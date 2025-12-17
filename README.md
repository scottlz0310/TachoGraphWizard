# TachoGraphWizard: タコグラフチャート画像処理ウィザード for GIMP 3

## プロジェクト概要
A3スキャン画像に含まれる複数のタコグラフチャート（円盤状記録紙）を、**ブラックボックス化せず**インタラクティブに確認しながら処理するためのGIMP 3向けワークフローです。

### 主な機能
- スキャン画像の**分割**（ガイド分割／自動検出）
- 背景の**ゴミ取り＋透明化（Color to Alpha）**
- 円盤の**回転補正（Correctiveモード対応）**
- **文字入れ**（運転手名・機械名・車番、複数テンプレート対応）
- **PNG（アルファ付き）**で保存

---

## 要件定義
- **入力**：PDFまたはJPEG（A3スキャン、最大6枚の円盤）
- **出力**：アルファチャンネル付きPNG
- **操作性**：逐次確認型（プレビュー＋OK／やり直し／スキップ）
- **非機能要件**：Windows 11 / GIMP 3.0.6対応、OSSライセンス（MIT推奨）

---

## 技術スタック
- **基盤**：GIMP 3.0.6（Windows 11）
- **プラグイン**：Python 3 + GIMP API（Gimp/GimpUi）
- **補助ツール**：Slice Using Guides、Divide Scanned Images、Batcher（GIMP 3対応）

---

## 処理フロー
1. **分割**：ガイド分割（Slice Using Guides）または自動分割（Divide Scanned Images）
2. **背景透明化**：Color to Alphaで白背景を透過
3. **回転補正**：Correctiveモードで目視＋数値入力orマウスドラッグ 補助線活用
4. **文字入れ**：テンプレート選択＋入力フォーム
5. **保存**：命名規則（例：YYYYMMDD_車番_運転手.png）でPNG出力

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
