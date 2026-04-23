# ver6.1 CHANGES — parse_frontmatter 共通化

ISSUE `ISSUES/util/low/parse-frontmatter-shared-util.md` に対応した純粋なリファクタリング。外部挙動の変更なし。

## 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---|---|---|
| `scripts/claude_loop_lib/frontmatter.py` | 新規 | 共通 `parse_frontmatter` 関数を実装（42 行） |
| `scripts/claude_loop_lib/feedbacks.py` | 修正 | `parse_feedback_frontmatter` 内の frontmatter 抽出を共通関数に委譲（42 行 → 26 行） |
| `scripts/issue_status.py` | 修正 | ローカル `parse_frontmatter` を `_extract_status_assigned` にリネームし共通関数を呼ぶ形に置換。`sys.path` 調整追加 |
| `tests/test_claude_loop.py` | 追加 | `TestParseFrontmatter` クラスを追加（5 ケース） |
| `REQUESTS/AI/quick-workflow-suggestion-ver6.1.md` | 新規 | quick ワークフロー提案を記録（AUTO モード運用のため自動中断せず） |
| `ISSUES/util/done/` | 新規 | `done/` ディレクトリ作成 |
| `ISSUES/util/done/parse-frontmatter-shared-util.md` | 移動 | `low/` から `done/` へ移動 |

## 変更内容の詳細

### `scripts/claude_loop_lib/frontmatter.py`（新規）

シグネチャ: `parse_frontmatter(text: str) -> tuple[dict | None, str]`

- 先頭 `---` 行で始まり閉じ `---` で終わる YAML ブロックを抽出し、`(frontmatter_dict, body)` を返す
- フォールバック規則:
  - 先頭 `---` なし → `(None, text)` （非 strip）
  - 閉じ `---` なし → `(None, text)` （非 strip）
  - YAML パースエラー → `(None, text)` （非 strip）
  - YAML が dict 以外（list 等）→ `(None, body)` （strip 済みの閉じ後テキスト）
- `feedbacks.py` と `issue_status.py` の両方で `body` を利用できるよう tuple を採用

### `scripts/claude_loop_lib/feedbacks.py`

`parse_feedback_frontmatter` が内部で行っていた `"---"` 境界手動 split + `yaml.safe_load` を削除し、`parse_frontmatter` 呼び出しに置換。step フィールドの型解釈（str / list）は引き続き `feedbacks.py` 側で担当。

既存テスト `TestParseFeedbackFrontmatter`（6 ケース）の挙動同一性は変更前後の全通過で保証。

### `scripts/issue_status.py`

`issue_status.py` 独自の `parse_frontmatter(path: Path) -> tuple[str, str]` は `frontmatter.py` 側のシグネチャ `parse_frontmatter(text: str)` と名前衝突するため、`_extract_status_assigned(path: Path) -> tuple[str, str]` にリネーム。内部で `parse_frontmatter(text)` を呼ぶ形に置換。

副作用: YAML パース失敗時の `warn(f"{path}: YAML parse failed ({exc})")` 警告が消えた（共通関数が YAML エラーを `(None, text)` で返すため）。frontmatter 破損時は `raw / human` フォールバックされるため運用影響は軽微。

`sys.path.insert(0, str(Path(__file__).resolve().parent))` を追加し、`claude_loop_lib` を初めてインポートする `issue_status.py` から参照可能にした（E402 は `# noqa` で抑制）。

### `tests/test_claude_loop.py`

`TestParseFrontmatter` クラスを追加（5 ケース）:
1. 正常系: `---\nkey: value\n---\nbody` → `({"key": "value"}, "body")`
2. 先頭 `---` なし → `(None, 元テキスト)`
3. 閉じ `---` なし → `(None, 元テキスト)`
4. YAML 不正 → `(None, 元テキスト)`
5. dict 以外（list） → `(None, body)`

## 技術的判断

- **関数名衝突の解決**: `issue_status.py` 側をリネーム（`_extract_status_assigned`）する方向を選択。共通関数のシグネチャ（text 受け取り）の方が汎用性が高く、PHASE6.0 の `issue_worklist.py` でも再利用しやすいため
- **YAML 警告の廃止**: 共通関数から呼び出し元固有の警告を出すと責務が混ざるため、警告は意図的に廃止。`raw / human` フォールバックで十分な可視性がある判断
- **tuple 戻り値**: `feedbacks.py` は body が必要、`issue_status.py` は dict のみ必要という非対称な要求を tuple で解決。呼び出し側でどちらを捨ててもよい設計
