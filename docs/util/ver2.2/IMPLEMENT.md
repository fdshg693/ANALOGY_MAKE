# IMPLEMENT: util ver2.2

小規模タスクのため簡潔に記述する。事前リファクタリング不要。

## 変更対象ファイル

| ファイル | 変更内容 |
|---|---|
| `scripts/claude_loop.py` | 未コミット変更検出 + 自動コミット機能の追加 |
| `tests/test_claude_loop.py` | 上記のテスト追加 |

## 実装内容

### 1. 新規関数（`scripts/claude_loop.py`）

#### `check_uncommitted_changes(cwd: Path) -> bool`

- `git status --porcelain` を実行し、出力があれば `True` を返す
- git が存在しない / リポジトリでない場合は `False` を返す（`get_head_commit()` と同じパターン）

#### `auto_commit_changes(cwd: Path) -> str | None`

- `git add -A` → `git commit -m "auto-commit before workflow"` を `check=True` で実行
- 成功時は `get_head_commit(cwd)` で新しいコミットハッシュを返す
- 失敗時（`subprocess.CalledProcessError` / `FileNotFoundError`）は `None` を返す

### 2. CLI フラグ追加（`parse_args()`）

`--auto-commit-before` を `store_true` で追加。ヘルプ: `"Automatically commit uncommitted changes before starting the workflow"`

### 3. `main()` への組み込み

`cwd` の解決後（L374-376）、ステップイテレータ構築前に以下のロジックを挿入:

```
1. check_uncommitted_changes(cwd) を呼び出す
2. 未コミット変更あり + --auto-commit-before:
   - auto_commit_changes(cwd) を実行
   - 成功: "Auto-committed uncommitted changes: {hash}" を stdout に出力
   - 失敗: "WARNING: Auto-commit failed. Proceeding with uncommitted changes." を stderr に出力
3. 未コミット変更あり + フラグなし:
   - "WARNING: Uncommitted changes detected. Consider committing before running the workflow." を stderr に出力
4. 未コミット変更なし / dry-run 時: 何もしない
```

チェック結果は `main()` で stdout/stderr に即時出力する。加えて、結果を文字列として保持し `_run_steps()` に `uncommitted_status: str | None` パラメータで渡す。`_run_steps()` はワークフローヘッダー内で `Uncommitted: {status}` 行としてログに記録する（`uncommitted_status` が `None` でない場合のみ）。

`uncommitted_status` の値:
- `"auto-committed ({hash})"` — 自動コミット成功時
- `"auto-commit failed, proceeding with uncommitted changes"` — 自動コミット失敗時
- `"uncommitted changes detected (no --auto-commit-before)"` — フラグなしで変更あり時
- `None` — 変更なし / dry-run 時（ヘッダーに行を追加しない）

### 4. テスト（`tests/test_claude_loop.py`）

| テストクラス | テスト内容 |
|---|---|
| `TestCheckUncommittedChanges` | (1) 変更あり→True、(2) 変更なし→False、(3) git未検出→False |
| `TestAutoCommitChanges` | (1) 成功→ハッシュ返却、(2) git add失敗→None、(3) git commit失敗→None |
| `TestParseArgsAutoCommitBefore` | (1) デフォルトFalse、(2) フラグ指定でTrue |

## dry-run 時の挙動

`--dry-run` 時は未コミット変更チェック自体をスキップする。dry-run は「コマンド確認のみ」が目的であり、副作用のあるチェックやコミットを行うべきでない。
