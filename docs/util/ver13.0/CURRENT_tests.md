# CURRENT_tests: util ver13.0 — テスト構成

ver13.0 で `test_commands.py` / `test_workflow.py` / `test_validation.py` / `test_claude_loop_cli.py` を更新。合計 **231 件**（全 PASS）。

## テスト実行コマンド

```bash
# 全件実行（推奨）
python -m unittest discover -s scripts/tests -t .

# 個別ファイル指定
python -m unittest scripts.tests.test_validation

# Vitest（フロントエンド）
pnpm exec vitest --run
```

## `scripts/tests/` の構成

| ファイル | 行数 | 含むテストクラス | テスト対象モジュール |
|---|---|---|---|
| `__init__.py` | 0 | — | パッケージ初期化（空） |
| `_bootstrap.py` | 8 | — | `sys.path` への `scripts/` 追加（重複ガード付き）。全テストファイルが `from . import _bootstrap` で参照 |
| `test_logging_utils.py` | 94 | `TestCreateLogPath` / `TestFormatDuration` | `claude_loop_lib/logging_utils.py` |
| `test_git_utils.py` | 117 | `TestGetHeadCommit` / `TestCheckUncommittedChanges` / `TestAutoCommitChanges` | `claude_loop_lib/git_utils.py` |
| `test_notify.py` | 36 | `TestNotifyCompletion` | `claude_loop_lib/notify.py` |
| `test_frontmatter.py` | 44 | `TestParseFrontmatter` | `claude_loop_lib/frontmatter.py` |
| `test_feedbacks.py` | 168 | `TestParseFeedbackFrontmatter` / `TestLoadFeedbacks` / `TestConsumeFeedbacks` | `claude_loop_lib/feedbacks.py` |
| `test_commands.py` | 341 | `TestBuildCommandWithLogFilePath` / `TestBuildCommandWithFeedbacks` / `TestBuildCommandWithModelEffort` / `TestBuildCommandWithSession` / `TestBuildCommandWithSystemPrompt` / `TestBuildCommandWithAppendSystemPrompt` / `TestBuildCommandAlwaysInjectsUnattendedPrompt` | `claude_loop_lib/commands.py` |
| `test_workflow.py` | 385 | `TestResolveCommandConfigRejectsAutoArgs` / `TestResolveDefaults` / `TestGetStepsModelEffort` / `TestGetStepsContinue` / `TestResolveWorkflowValue` / `TestResolveDefaultsOverrideKeys` / `TestGetStepsOverrideKeys` / `TestYamlSyncOverrideKeys` / `TestOverrideInheritanceMatrix` | `claude_loop_lib/workflow.py` |
| `test_issues.py` | 63 | `TestExtractStatusAssigned` | `claude_loop_lib/issues.py` |
| `test_claude_loop_cli.py` | 305 | `TestParseArgsLoggingOptions` / `TestRejectsAutoFlag` / `TestParseArgsNotifyOption` / `TestParseArgsAutoCommitBefore` / `TestParseArgsWorkflow` / `TestValidateAutoArgs` / `TestReadWorkflowKind` / `TestFindLatestRoughPlan` / `TestComputeRemainingBudget` | `scripts/claude_loop.py` CLI 層 |
| `test_claude_loop_integration.py` | — | `TestYamlIntegration` / `TestRunStepsSessionTracking` / `TestAutoWorkflowIntegration` / `TestStartupValidationIntegration` | `scripts/claude_loop.py` 統合テスト |
| `test_validation.py` | 413 | `TestValidateCategory` / `TestValidateSingleYamlShape` / `TestValidateDefaultsSection` / `TestValidateStepSchema` / `TestValidateOverrideWhitelist` / `TestValidateStepReferences` / `TestValidateStartupAggregation` / `TestValidateStartupExistingYamls` / `TestValidateRejectsLegacyKeys` | `claude_loop_lib/validation.py` |
| `test_issue_worklist.py` | 203 | `TestIssueWorklist` | `scripts/issue_worklist.py` |

## ver13.0 でのテスト変更

### `test_commands.py` — 削除・更新・追加

**削除**:
- `TestBuildCommandWithMode`（`auto_mode` 引数消滅）
- `TestBuildCommandWithAppendSystemPrompt.test_appends_after_auto_mode`（`auto_mode=True` 引数消滅）

**更新**:
- `TestBuildCommandWithLogFilePath.test_without_log_file_path`: `"--append-system-prompt" not in cmd` → `"--append-system-prompt" in cmd`（常時注入のため）
- `TestBuildCommandWithLogFilePath.test_empty_string_log_file_path_does_not_add_args`: テスト名 `test_empty_string_log_file_path_omits_log_line_but_still_injects_unattended` にリネーム・同上反転
- `TestBuildCommandWithFeedbacks.test_no_feedbacks`: `assert "--append-system-prompt" not in cmd` → feedback 行が無い（unattended prompt は含まれる）ことを確認するアサーションに変更
- `TestBuildCommandWithAppendSystemPrompt` の複数テスト: `assert self._asp_value(cmd) == "my-append"` のような等号比較を `"my-append" in value` の含有比較に変更（unattended prompt が prefix に常時付くため）
- `TestBuildCommandWithAppendSystemPrompt.test_step_overrides_defaults_append`: `"A"` / `"B"` 値を `STEP_VAL` / `DEFAULT_VAL` ユニーク識別子にリネーム（unattended prompt 中の "A" との誤マッチ回避）
- `TestOverrideInheritanceMatrix` の 4 テスト: `append_system_prompt` キーに専用ヘルパ `_assert_contains()` を導入して key ごとに比較ロジックを切替え
- `TestBuildCommandWithAppendSystemPrompt.test_full_combination_order`: `auto_mode=True` 引数を削除・`"AUTO (unattended)"` → `"unattended"` の文言マッチに更新

**追加**:
- `TestBuildCommandAlwaysInjectsUnattendedPrompt`: minimal ケースで `"unattended"` が含まれ、`"AUTO"` 文字列（旧）が含まれないことを確認

### `test_workflow.py` — 削除・追加

**削除**:
- `TestResolveMode`（`resolve_mode()` 関数自体が消滅）
- `TestResolveCommandConfigAutoArgs`（`auto_args` 戻り値消滅）
- `from claude_loop_lib.workflow import resolve_mode` の import

**追加**:
- `TestResolveCommandConfigRejectsAutoArgs`: `{"command": {"auto_args": [...]}}` を渡すと `SystemExit` になることを検証

### `test_validation.py` — 追加

**追加**（ver13.0 新規クラス）:
- `TestValidateRejectsLegacyKeys` — 4 ケース:
  1. `mode:` キーを持つ YAML → 専用エラー文言で拒否
  2. `command.auto_args` キーを持つ YAML → 専用エラー文言で拒否
  3. 未知 top-level キーを持つ YAML → 汎用エラーで拒否
  4. 未知 command キーを持つ YAML → 汎用エラーで拒否

### `test_claude_loop_cli.py` — 削除・追加

**削除**:
- `TestParseArgsAutoOption`（`--auto` argparse 削除）

**追加**:
- `TestRejectsAutoFlag`: `_parse(["--auto"])` が `SystemExit` を発生させることを検証（argparse 標準挙動の確認）

## 検証結果（ver13.0 完了時点）

| コマンド | 結果 |
|---|---|
| `python -m unittest discover -s scripts/tests -t .` | 231/231 PASS |
| `pnpm exec vitest --run` | 変更なし（Python 変更のみのため） |
