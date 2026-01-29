# Codex Agent Guide (日本語)

## 目的
GIMP 3向けのタコグラフチャート処理プラグイン（分割・背景除去・文字入れ・保存）を実装/運用するための作業メモです。

## 日本語使用
- AIとのやり取りは日本語で行います。
- コードコメントやドキュメントも日本語で記述します。

## セットアップ
- 依存関係: Python 3.12+ / GIMP 3.0.6
- 開発環境: `uv sync`

## 品質確保（必須）
コードを変更する際は、以下の全てのチェックが成功することを確認してください。

```bash
# フォーマットチェック
uv run ruff format --check .

# Lintチェック
uv run ruff check .

# 型チェック
uv run basedpyright

# テスト実行
uv run pytest tests/
```

または、一括で実行する場合:
```bash
uv run ruff format --check . && uv run ruff check . && uv run basedpyright && uv run pytest tests/
```

**注意**: PRをマージする前に、上記全てのチェックが成功することを確認してください。CIでも同様のチェックが実行されます。

## よく使うコマンド
- フォーマット: `uv run ruff format .`
- Lint: `uv run ruff check .`
- Lint（自動修正）: `uv run ruff check . --fix`
- 型チェック: `uv run basedpyright`
- テスト: `uv run pytest tests/`
- テスト（カバレッジ付き）: `uv run pytest tests/ --cov=src --cov-report=term-missing`

## プラグイン導入（Windows）
- GIMPプラグインディレクトリ: `%APPDATA%\GIMP\3.0\plug-ins`
- 例: `xcopy /E /I src\tachograph_wizard "C:\Users\<ユーザー名>\AppData\Roaming\GIMP\3.0\plug-ins\tachograph_wizard"`
- 注意: GIMP 3 は `plug-ins` 直下の `.py` を無視。サブディレクトリ配下で、ファイル名はディレクトリ名と一致させること。

## 主要ディレクトリ
- `src/tachograph_wizard/`: プラグイン本体
- `src/tachograph_wizard/ui/`: UIダイアログ
- `src/tachograph_wizard/core/`: CSV/テンプレート/レンダラ
- `src/tachograph_wizard/templates/default_templates/`: 標準テンプレート(JSON)
- `docs/`: 設計資料

## Text Inserter（文字入れ）
### CSV仕様（車両マスタ）
- 必須列: `vehicle_type`, `vehicle_no`, `driver`
- 日付列は任意:
  - `date_year`, `date_month`, `date_day` または `date`
  - 無い場合はUIで選択した日付を全行に適用

### 日付の運用
- 1枚のチャート紙につき1回実行
- UIで日付選択（前回値があればそれ／無ければ当日）
- 保存先: `%APPDATA%\tachograph_wizard\settings.json`
  - `text_inserter_last_date`

### テンプレート
- JSON形式で管理
- `font.size_ratio` は「画像短辺に対する比率」（px相当）
- カスタムテンプレートは任意フォルダからロード可能
  - UIでテンプレートフォルダを選択 → `Load Templates`
  - 保存先: `%APPDATA%\tachograph_wizard\settings.json`
    - `text_inserter_template_dir`

## Template Exporter（テンプレート書き出し）
- テキストレイヤーからJSONテンプレートを生成
- フォントサイズ単位が `pt` の場合は画像DPIからpx換算

## ログ
- 既定: `%TEMP%\tachograph_wizard.log`
  - 起動失敗やPDBエラーの確認に使用

## 参考ドキュメント
- `README.md`
- `docs/phase2_implementation.md`
