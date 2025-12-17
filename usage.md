# 使用ガイド

このガイドでは、GIMP 3 で **Tachograph Wizard** プラグインをインストールして使用する方法について説明します。

## インストール

PythonベースのGIMP 3プラグインであるため、GIMPのプラグインディレクトリに配置する必要があります。

### 1. GIMPプラグインディレクトリの特定
GIMP 3のユーザープラグインディレクトリを探します。一般的な場所は以下の通りです：
- **Windows**: `%APPDATA%\GIMP\3.0\plug-ins`
- **Linux**: `~/.config/GIMP/3.0/plug-ins`
- **macOS**: `~/Library/Application Support/GIMP/3.0/plug-ins`

*注: 正確なパスはGIMPの`編集` > `環境設定` > `フォルダ` > `プラグイン`で確認できます。*

### 2. プラグインのインストール
GIMPが期待するディレクトリ構造に合わせるため、プラグインをインストールする必要があります：
`plug-ins/tachograph_wizard/__init__.py` および `plug-ins/tachograph_wizard/plugin.py`。

#### オプションA: コピー（最も簡単）
1. このリポジトリから `src/tachograph_wizard` ディレクトリをコピーします。
2. GIMPの `plug-ins` ディレクトリに貼り付けます。

#### オプションB: シンボリックリンク（開発用）
プラグインを開発している場合は、更新が即座に反映されるようシンボリックリンクを作成することをお勧めします。

**Windows (管理者権限のPowerShell):**
```powershell
New-Item -ItemType SymbolicLink -Path "$env:APPDATA\GIMP\3.0\plug-ins\tachograph_wizard" -Target "C:\path\to\repo\src\tachograph_wizard"
```

**Linux/macOS:**
```bash
ln -s /path/to/repo/src/tachograph_wizard ~/.config/GIMP/3.0/plug-ins/tachograph_wizard
```

### 3. インストール確認
1. GIMPを再起動します。
2. プラグインは自動的に読み込まれます。ターミナルからGIMPを起動した場合はターミナルの出力を確認するか、以下の手順でメニュー項目を探して正しく読み込まれたか確認できます。

## 使用方法

1. **画像を開く**: タコグラフチャートが含まれたA3用紙のスキャン画像をGIMPで開きます。
2. **ウィザードを起動**:
   - メニューから選択: **フィルター** > **Processing** > **Tachograph Chart Wizard...**
3. **ウィザードの手順に従う**:
   - 対話型ダイアログが、チャートの分割、クリーニング、回転、注釈付けをガイドします。

## トラブルシューティング

- **プラグインが表示されない場合**
  - **GIMP 3.0**（または互換性のあるリリース候補版/ベータ版）がインストールされていることを確認してください。このプラグインはGIMP 3で利用可能なGObject Introspectionを使用します。
  - `plug-ins`フォルダ内の`tachograph_wizard`フォルダに`plugin.py`が含まれていることを確認してください。
  - Linux/macOSでは、`plugin.py`に実行権限が付与されていることを確認してください（`chmod +x plugin.py`）。

- **"インタープリター 'python3' は無効です" というエラーが出る場合 (Windows)**
  GIMPがPythonを見つけられていません。`C:\Program Files\GIMP 3\lib\gimp\3.0\interpreters\pygimp.interp` をテキストエディタ（管理者権限）で開き、以下のようにPythonのフルパスを指定してください。

  **変更前:**
  ```ini
  python=pythonw.exe
  python3=pythonw.exe
  ```

  **変更後 (例: Pythonが標準的な場所にインストールされている場合):**
  ```ini
  python=C:\Users\あなたのユーザー名\AppData\Local\Programs\Python\Python312\pythonw.exe
  python3=C:\Users\あなたのユーザー名\AppData\Local\Programs\Python\Python312\pythonw.exe
  ```
  ※ `pythonw.exe` のパスは、お使いの環境に合わせて書き換えてください（`where pythonw` コマンドで確認できます）。

  **uvを使用している場合:**
  uvで管理されているPythonを使用する場合、バージョンリストからパスを確認できます。
  ```powershell
  uv python list --only-installed
  ```
  出力例:
  `cpython-3.12.11-windows-x86_64-none    C:\Users\User\AppData\Roaming\uv\python\cpython-3.12.11-windows-x86_64-none\python.exe`

  このパスの `python.exe` を `pythonw.exe` に置き換えて設定ファイルに記述してください。
  ```ini
  python=C:\Users\User\AppData\Roaming\uv\python\cpython-3.12.11-windows-x86_64-none\pythonw.exe
  python3=C:\Users\User\AppData\Roaming\uv\python\cpython-3.12.11-windows-x86_64-none\pythonw.exe
  ```
