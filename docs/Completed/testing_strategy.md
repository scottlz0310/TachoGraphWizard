# テスト戦略ドキュメント

## 現状分析（v1.0.0時点）

### カバレッジサマリー
- **全体カバレッジ**: 8% (2,707行中2,479行が未カバー)
- **テスト数**: 18テスト
- **テスト実行時間**: 0.45秒

### カバレッジ内訳

#### ✅ 高カバレッジ（テスト済み）
| ファイル | カバレッジ | 状態 |
|---------|-----------|------|
| `templates/models.py` | 100% | データクラス定義 |
| `core/exporter.py` | 86% | ファイル名生成、PNG保存 |
| `core/template_manager.py` | 77% | テンプレート読み込み |
| `core/csv_parser.py` | 74% | CSV解析、ヘッダー検証 |

#### ❌ 未カバー（テスト未実装）
| ファイル | 行数 | 重要度 | テスト難易度 |
|---------|------|--------|------------|
| `core/image_splitter.py` | 514 | 🔴 高 | 🔴 高（GIMP API依存） |
| `core/background_remover.py` | 365 | 🔴 高 | 🔴 高（GIMP API依存） |
| `core/template_exporter.py` | 312 | 🟡 中 | 🔴 高（GIMP API依存） |
| `ui/text_inserter_dialog.py` | 398 | 🟡 中 | 🔴 高（GTK UI） |
| `wizard_procedure.py` | 197 | 🔴 高 | 🔴 高（GIMP+GTK） |
| `ui/template_exporter_dialog.py` | 150 | 🟡 中 | 🔴 高（GTK UI） |
| `core/text_renderer.py` | 148 | 🟡 中 | 🔴 高（GIMP API依存） |
| `core/pdb_runner.py` | 172 | 🟢 低 | 🟡 中（PDB互換レイヤー） |

---

## テスト実装が困難な理由

### 1. GIMP API依存
ほとんどのコア機能がGIMP 3のPython API（`Gimp.Image`, `Gimp.Layer`, `Gimp.Selection`など）に依存しているため、以下の課題があります：

- **GObject Introspection**: 型情報が不完全でモックが困難
- **状態管理**: GIMP内部の画像状態、レイヤースタック、選択状態などの再現が必要
- **ネイティブバイナリ**: C/C++で実装されたGIMPコアとの連携

### 2. GTK UI依存
UIコンポーネントがGTK 3に依存しているため：

- **イベントループ**: GTKメインループのモックが必要
- **ウィジェット階層**: 複雑なウィジェットツリーの構築
- **ユーザーインタラクション**: ボタンクリック、スピナー操作などのシミュレーション

### 3. 統合的な処理フロー
各機能が相互に依存しており、単体テストよりも統合テストが適している場合が多い。

---

## テスト戦略

### フェーズ1: ユーティリティ層の完全カバレッジ（優先度：高）

#### 対象ファイル
- ✅ `csv_parser.py` (74% → 100%)
- ✅ `exporter.py` (86% → 100%)
- ✅ `template_manager.py` (77% → 100%)

#### 実装内容
1. **csv_parser.py**
   - エッジケース: 空のCSV、不正な文字エンコーディング
   - エラーケース: 必須カラム欠損のバリエーション

2. **exporter.py**
   - ファイル名サニタイズの全パターン
   - ディレクトリ作成エラーのハンドリング
   - PNG保存のモック（GIMP APIを使わない部分のみ）

3. **template_manager.py**
   - 不正なJSON形式のエラーハンドリング
   - テンプレートキャッシュの動作確認

#### 見積もり工数
- 2-3時間（追加テスト10-15ケース）

---

### フェーズ2: コア機能のモックベーステスト（優先度：中）

#### 対象ファイル
- `image_splitter.py` (0% → 30-40%)
- `background_remover.py` (0% → 30-40%)

#### モック戦略

##### 必要なGIMP APIモック
```python
# tests/mocks/gimp_mocks.py
class MockGimpImage:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.layers = []
        self._selection = None

    def select_ellipse(self, op, x, y, w, h):
        self._selection = ('ellipse', op, x, y, w, h)

    def insert_layer(self, layer, parent, position):
        self.layers.insert(position, layer)

    # ... 他のメソッド

class MockGimpLayer:
    def __init__(self, image, name, width, height):
        self.image = image
        self.name = name
        self.width = width
        self.height = height

    def edit_clear(self):
        # 選択範囲のクリアをシミュレート
        pass
```

#### テスト方針
1. **アルゴリズムロジックのテスト**
   - しきい値計算の正確性
   - 境界ボックス検出のロジック
   - パディング計算

2. **モックを使った統合テスト**
   - モック画像での分割処理
   - 楕円選択パラメータの検証
   - エラーハンドリング

#### 実装の課題
- Geglバッファのモックが必要（ピクセルデータアクセス）
- NumPy配列でのピクセルデータ代替を検討
- 実画像を使った手動E2Eテストとの併用が現実的

#### 見積もり工数
- 8-12時間（モックフレームワーク構築 + テスト実装）

---

### フェーズ3: UI統合テスト（優先度：低）

#### 対象ファイル
- `wizard_procedure.py`
- `ui/text_inserter_dialog.py`
- `ui/template_exporter_dialog.py`

#### テスト方針
**推奨アプローチ**: 自動テストではなく手動テストチェックリストを整備

理由：
- GTKのモックが非常に複雑
- GIMPプラグインとしての実行環境が必要
- ROI（投資対効果）が低い

#### 手動テストチェックリスト作成
`docs/manual_test_checklist.md` を作成し、以下を文書化：
1. ウィザードの各ステップの動作確認
2. パディング調整の動作確認
3. エラーメッセージの表示確認
4. CSV読み込みとプレビュー
5. テンプレート選択と適用

#### 見積もり工数
- チェックリスト作成: 2時間
- 自動テスト実装: 20時間以上（非推奨）

---

## 推奨テスト戦略

### 短期（次回リリースまで）
1. ✅ **フェーズ1を完了**: ユーティリティ層を100%カバレッジに
   - カバレッジを8% → 15-20%に改善
   - 低コスト・高効果

2. ✅ **手動テストチェックリスト作成**
   - リリース前の品質保証を形式化
   - 再現性のある動作確認

### 中期（v1.1-v1.2）
3. **フェーズ2のモック構築**
   - `image_splitter.py`の一部をテスト可能に
   - アルゴリズムロジックの正確性を保証

4. **E2Eテスト環境の検討**
   - GIMP 3をヘッドレスモードで起動
   - サンプル画像を使った自動処理テスト
   - GitHub Actions上での実行可能性を調査

### 長期（v2.0以降）
5. **統合テストフレームワークの構築**
   - GIMP APIモック層の完全実装
   - ピクセルレベルの検証
   - パフォーマンステスト

---

## テストデータ戦略

### 既存のテストデータ
- `tests/fixtures/sample_data.csv`: CSV読み込みテスト用
- `examples/sample_data.csv`: ユーザー向けサンプル

### 追加が必要なテストデータ
1. **画像データ**
   - 最小サンプル画像（100x100px、単一円盤）
   - マルチ円盤サンプル（A3スキャン風、低解像度）
   - エッジケース画像：
     - 歪んだ円盤
     - ノイズが多い画像
     - 低コントラスト画像

2. **テンプレートデータ**
   - 不正なJSONテンプレート
   - 必須フィールド欠損テンプレート
   - 異常な座標値を持つテンプレート

3. **CSVデータ**
   - 異常系CSVのバリエーション（既存テストで一部カバー済み）

### データ配置
```
tests/
├── fixtures/
│   ├── images/
│   │   ├── single_disc_100x100.xcf
│   │   ├── multi_disc_low_res.xcf
│   │   ├── distorted_disc.xcf
│   │   └── noisy_image.xcf
│   ├── templates/
│   │   ├── invalid_json.json
│   │   ├── missing_fields.json
│   │   └── invalid_coordinates.json
│   └── csv/
│       ├── empty.csv
│       ├── missing_columns.csv
│       └── malformed_utf8.csv
```

---

## CI/CD統合

### 現状のCI設定（`.github/workflows/ci-cd.yml`）
```yaml
- name: Run tests
  run: |
    uv run pytest tests/ --cov="src" --cov-report=xml --cov-report=term-missing

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v5
  with:
    file: ./coverage.xml
```

### 推奨される改善
1. **カバレッジ閾値の設定**
   ```yaml
   - name: Check coverage threshold
     run: |
       uv run coverage report --fail-under=20  # 段階的に引き上げ
   ```

2. **カバレッジバッジの追加**
   README.mdにCodecovバッジを追加：
   ```markdown
   [![codecov](https://codecov.io/gh/scottlz0310/TachoGraphWizard/branch/main/graph/badge.svg)](https://codecov.io/gh/scottlz0310/TachoGraphWizard)
   ```

3. **PR時のカバレッジ差分レポート**
   Codecovは自動的にPRコメントでカバレッジ変化を報告

---

## 技術的な制約と考慮事項

### GIMP APIのテスタビリティ
- **制約**: GObject Introspectionベースのため、完全なモックは困難
- **対策**: インターフェース層を導入し、GIMP依存を抽象化
  ```python
  # 例: core/image_operations.py
  class ImageOperations(Protocol):
      def select_ellipse(self, x, y, w, h) -> None: ...
      def invert_selection(self) -> None: ...
      def clear_selection(self) -> None: ...

  class GimpImageOperations(ImageOperations):
      # 実装

  class MockImageOperations(ImageOperations):
      # テスト用モック実装
  ```

### パフォーマンステスト
現状では不要だが、将来的に大量画像処理が必要になった場合：
- ベンチマークテストの追加
- メモリ使用量の監視
- 処理時間の回帰テスト

---

## まとめ

### 現状の評価
- ✅ ユーティリティ層は一定のテストカバレッジあり
- ❌ コア機能（画像処理）のテストが不足
- ❌ UI層のテストが完全に欠落

### 推奨アクション
1. **即座に実施**: フェーズ1（ユーティリティ層100%カバレッジ）
2. **次回リリース前**: 手動テストチェックリスト作成
3. **v1.1以降**: モックフレームワーク構築、コア機能の部分テスト化

### 現実的な目標設定
- **v1.0.0**: 8% カバレッジ（現状）
- **v1.0.1**: 20% カバレッジ（フェーズ1完了）
- **v1.1.0**: 35-40% カバレッジ（フェーズ2部分実装）
- **v2.0.0**: 60%+ カバレッジ（統合テスト整備）

### 重要な認識
GIMP プラグインという特性上、**100%の自動テストカバレッジは現実的ではない**。手動テストとの組み合わせが最も効果的なアプローチとなる。
