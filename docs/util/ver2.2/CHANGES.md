# ver2.2 CHANGES

PHASE2.0 の最終残タスク（未コミット変更検出・`--auto-commit-before` フラグ）を実装。加えて、不要なインタラクティブモードの削除を実施。本バージョンにより PHASE2.0 は全項目完了。

## 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---|---|---|
| `scripts/claude_loop.py` | 変更 | 未コミット変更検出・自動コミット機能の追加、インタラクティブモードの削除（541→575行, +34行） |
| `tests/test_claude_loop.py` | 変更 | 新テストクラス3個追加、インタラクティブモード関連テストの削除・更新（334→391行, +57行） |
| `.claude/SKILLS/split_plan/SKILL.md` | 変更 | split_plan 完了後の Git コミットステップを追加 |
| `.claude/SKILLS/write_current/SKILL.md` | 変更 | write_current 完了後の Git コミットステップを追加 |

## 変更内容の詳細

### 1. 未コミット変更検出・自動コミット（`scripts/claude_loop.py`）

ワークフロー開始前に作業ディレクトリの状態をチェックし、未コミット変更がある場合に警告または自動コミットを行う機能を追加。

#### 新規関数

- **`check_uncommitted_changes(cwd: Path) -> bool`**: `git status --porcelain` を実行し、出力があれば `True` を返す。git 未検出時は `False`
- **`auto_commit_changes(cwd: Path) -> str | None`**: `git add -A` → `git commit -m "auto-commit before workflow"` を実行。成功時はコミットハッシュ、失敗時は `None`

#### CLI フラグ追加

- **`--auto-commit-before`**（`store_true`）: ワークフロー開始前に未コミット変更を自動コミット

#### `main()` への組み込み

`cwd` 解決後、ステップイテレータ構築前に以下のロジックを実行:
1. `check_uncommitted_changes(cwd)` でチェック
2. 変更あり + `--auto-commit-before`: 自動コミット実行（成功/失敗をそれぞれ stdout/stderr に出力）
3. 変更あり + フラグなし: stderr に警告出力
4. `--dry-run` 時: チェック自体をスキップ

チェック結果は `uncommitted_status` 文字列として `_run_steps()` に渡され、ワークフローヘッダー内に `Uncommitted: {status}` 行として記録される。

### 2. インタラクティブモードの削除（`scripts/claude_loop.py`）

ユーザー判断により、不要なインタラクティブモード関連のコードを削除。

- **`--interactive` CLI フラグの削除**: `--auto` との排他グループを解消し、`--auto` を単独の `store_true` フラグに変更
- **`resolve_mode()` の簡素化**: `cli_interactive` パラメータを削除（2引数 → 1引数に）
- **`build_command()` の INTERACTIVE プロンプト削除**: 非AUTO時の `"Workflow execution mode: INTERACTIVE..."` システムプロンプト注入を削除。非AUTO時は `--append-system-prompt` を付与しない（ログパスがある場合を除く）

### 3. テスト変更（`tests/test_claude_loop.py`）

#### 新規テストクラス

| テストクラス | テスト数 | 対象 |
|---|---|---|
| `TestCheckUncommittedChanges` | 3 | 変更あり→True、変更なし→False、git未検出→False |
| `TestAutoCommitChanges` | 3 | 成功→ハッシュ返却、git add失敗→None、git commit失敗→None |
| `TestParseArgsAutoCommitBefore` | 2 | デフォルトFalse、フラグ指定でTrue |

#### 既存テスト更新

- **`TestBuildCommandWithLogFilePath`**: INTERACTIVE プロンプト関連のアサーションを削除。ログパスなし時は `--append-system-prompt` が付与されないことを検証
- **`TestResolveMode`**: `cli_interactive` パラメータの削除に対応。`test_cli_interactive_overrides_yaml` を削除
- **`TestBuildCommandWithMode`**: `test_interactive_mode_includes_interactive_prompt` → `test_non_auto_mode_has_no_mode_prompt` にリネーム・内容変更
- **`TestParseArgsModeOptions`** → **`TestParseArgsAutoOption`** にリネーム: `--interactive` 関連テスト3件を削除

### 4. SKILL ファイルへのコミットステップ追加

ver2.1 のレトロスペクティブ改善提案に基づき、split_plan と write_current の各 SKILL にワークフロー成果物の Git コミットステップを追加。

- **`.claude/SKILLS/split_plan/SKILL.md`**: 「ステップ3: Git にコミットする」を追加（`docs(ver{バージョン番号}): split_plan完了` 形式）
- **`.claude/SKILLS/write_current/SKILL.md`**: 「Git にコミットする」セクションを追加（`docs(ver{バージョン番号}): write_current完了` 形式）

## 技術的判断

- **`--interactive` フラグの削除**: ワークフローは基本的にAUTOモードで実行されるため、明示的なINTERACTIVEモード切替は不要と判断。非AUTOモードがデフォルトの挙動として残る
- **`--dry-run` 時の未コミットチェックスキップ**: dry-run は「コマンド確認のみ」が目的であり、副作用のあるチェックやコミットを行うべきでないため
- **SKILL へのコミットステップ追加**: ワークフロー各ステップの成果物を即座にコミットすることで、コミット粒度の改善と後続ステップでの差分追跡を容易にする
