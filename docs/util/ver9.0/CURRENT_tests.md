# CURRENT_tests: util ver9.0 — テスト構成

`tests/test_claude_loop.py` は `scripts/claude_loop.py` と `scripts/claude_loop_lib/` のユニットテスト。`unittest` を使用。ver9.0 で `--workflow auto` 関連の 7 クラス・32 ケースを追加し、合計 35 クラス・151 ケースになった。

## ver9.0 での検証結果

- `python -m unittest tests.test_claude_loop`: **151 件 全パス**（ver8.0 から +32 件）
- `pnpm test`: **15 ファイル / 177 件 全パス**（vitest + unittest 合計）
- `npx nuxi typecheck`: 既知の vue-router volar 警告のみ（ビルド・実行に影響なし）

## ver9.0 で追加されたテストクラス

| テストクラス | テスト対象 |
|---|---|
| `TestResolveWorkflowValue` | `resolve_workflow_value()`: `"auto"` → sentinel 文字列、`"full"` / `"quick"` → yaml_dir 以下の Path、パス直指定 → `Path(value)`、`"AUTO"` 等の大文字はパス扱い |
| `TestParseArgsWorkflow` | `parse_args()` の `--workflow`: デフォルト `"auto"`、`-w full` / `-w custom.yaml` の受け取り |
| `TestValidateAutoArgs` | `validate_auto_args()`: `auto + --start 1` は OK、`auto + --start 2` は `SystemExit` |
| `TestReadWorkflowKind` | `_read_workflow_kind()`: `quick` / `full` の正常系、frontmatter なし→`full` フォールバック、`workflow` キーなし→`full`、不正値→`full`（全ケースで stderr 警告チェック） |
| `TestFindLatestRoughPlan` | `_find_latest_rough_plan()`: 1 ファイル・最新 mtime 判定・ファイルなし→`SystemExit`・`CURRENT_CATEGORY` ファイル使用・未設定時 `app` フォールバック |
| `TestComputeRemainingBudget` | `_compute_remaining_budget()`: `max_step_runs` 未設定→None、設定時は `max(max_step_runs - completed, 0)` |
| `TestAutoWorkflowIntegration` | `_run_auto()` の統合テスト: `workflow: full` / `quick` での 2 段実行確認、phase 1 失敗時の早期終了、不正 frontmatter → full フォールバック、`--dry-run` での phase2 スキップ、`--no-log` 対応 |

### `TestAutoWorkflowIntegration` のパッチ構成

`subprocess.run` と `uuid.uuid4` をモック（`TestRunStepsSessionTracking` と同じ手法）。`_find_latest_rough_plan` と `_read_workflow_kind` をモックして ROUGH_PLAN.md の frontmatter を任意に制御する。Windows (cp932) の stdout エンコードエラーを回避するため `builtins.print` もパッチする（D4 として MEMO に記録済み）。

## 既存テストクラス一覧（ver8.0 から変更なし）

| テストクラス | テスト対象 |
|---|---|
| `TestCreateLogPath` | `create_log_path()`: ファイル名形式、ディレクトリ配置、stem 抽出、ディレクトリ作成 |
| `TestGetHeadCommit` | `get_head_commit()`: 正常取得、非ゼロ終了、git 未インストール、空白トリム |
| `TestFormatDuration` | `format_duration()`: 秒・分・時のフォーマット、境界値、小数点切り捨て |
| `TestBuildCommandWithLogFilePath` | `build_command()` のログパス引数: None 時、指定時、引数順序、空文字列 |
| `TestParseArgsLoggingOptions` | `--no-log` / `--log-dir` のデフォルト・指定・共存 |
| `TestNotifyCompletion` | `notify_completion()`: toast 成功、beep フォールバック、シングルクォートエスケープ |
| `TestResolveMode` | `resolve_mode()`: デフォルト、YAML `auto=true`、CLI `--auto` オーバーライド |
| `TestBuildCommandWithMode` | `build_command()` の auto_mode: AUTO プロンプト注入、非 AUTO 時プロンプトなし |
| `TestParseArgsAutoOption` | `--auto` フラグのデフォルト・指定 |
| `TestParseArgsNotifyOption` | `--no-notify` フラグのデフォルト・指定 |
| `TestResolveCommandConfigAutoArgs` | `resolve_command_config()` の `auto_args` 抽出・デフォルト空リスト |
| `TestCheckUncommittedChanges` | `check_uncommitted_changes()`: 変更あり、変更なし、git 未検出 |
| `TestAutoCommitChanges` | `auto_commit_changes()`: 成功→ハッシュ返却、`git add` 失敗→None、`git commit` 失敗→None |
| `TestParseArgsAutoCommitBefore` | `--auto-commit-before` フラグのデフォルト・指定 |
| `TestParseFeedbackFrontmatter` | フィードバック frontmatter 解析: 文字列/リスト/未指定（キャッチオール）/無効 YAML/空 body |
| `TestLoadFeedbacks` | `load_feedbacks()`: マッチ/不一致/キャッチオール/ソート順/`done/` 除外 |
| `TestConsumeFeedbacks` | `consume_feedbacks()`: 正常移動/ディレクトリ自動作成/空リスト/同名上書き |
| `TestBuildCommandWithFeedbacks` | `build_command(feedbacks=...)`: 注入/複数 FB の `---` 区切り/なしの場合 |
| `TestResolveDefaults` | `resolve_defaults()`: `defaults` キー無→空 dict、両方指定、片方のみ、非マッピング→`SystemExit` |
| `TestBuildCommandWithModelEffort` | `build_command(defaults=...)`: defaults/step ともに未設定で引数なし、defaults 継承、step による上書き |
| `TestGetStepsModelEffort` | `get_steps()` の model/effort 受け取り: キー無なら dict に含まれない、空文字列→`SystemExit` |
| `TestYamlIntegration` | `load_workflow` → `get_steps` + `resolve_defaults` → `build_command` の統合フロー |
| `TestBuildCommandWithSession` | `build_command(session_id=..., resume=...)`: `resume=True` で `-r` フラグ、session_id=None で両フラグなし |
| `TestGetStepsContinue` | `get_steps()` の `continue` 受け取り: 省略→False、true/false 正規化、非 bool→`SystemExit` |
| `TestRunStepsSessionTracking` | `_run_steps()` のセッション ID 管理: `continue=false` で新規 UUID、`continue=true` で引き継ぎ |
| `TestParseFrontmatter` | `parse_frontmatter()`: 正常系/先頭`---`なし/閉じ`---`なし/YAML不正/dict以外 |
| `TestExtractStatusAssigned` | `extract_status_assigned()`: frontmatter なし→`raw/human`フォールバック、正常 frontmatter で 4-tuple 返却、無効 combo で stderr 警告 |
| `TestIssueWorklist` | `issue_worklist.py` の絞り込みロジック: ready/ai 2 件ヒット・human フィルタ除外・frontmatter なし除外・JSON 出力パース・status 単一指定・priority ミスマッチ警告・`collect()` 空 dir・text フォーマット 0 件 |

## 実行方法

```bash
python -m unittest tests.test_claude_loop          # 全テスト実行
python -m unittest tests.test_claude_loop.TestAutoWorkflowIntegration  # クラス単位
pnpm test                                           # vitest + unittest 両方実行
```

## テスト方針

- `TestAutoWorkflowIntegration`: `@patch("claude_loop.subprocess.run")` + `@patch("claude_loop.uuid.uuid4")` + `@patch("claude_loop._find_latest_rough_plan")` + `@patch("claude_loop._read_workflow_kind")` のパッチ構成。`tempfile.TemporaryDirectory` で一時ディレクトリを生成して YAML ファイルを配置
- `TestIssueWorklist`: `tempfile.TemporaryDirectory` で一時 `ISSUES/` ツリーを組み、`issue_worklist.REPO_ROOT` / `ISSUES_DIR` をモンキーパッチする方式
- stderr の warning 検証: `io.StringIO` を `sys.stderr` に差し替えて文字列で assert する標準手法
- `issue_status.py` のユニットテストは未追加（外部挙動の同一性は `TestExtractStatusAssigned` + 手動スモークで保証）
- YAML の `steps:` 構造に対するハードコード期待値なし（SKILL 名追加・削除でテストが壊れない設計）
