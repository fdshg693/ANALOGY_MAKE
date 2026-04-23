# CURRENT_tests: util ver15.0 — テスト構成

ver15.0 で `test_workflow.py` に 2 件・`test_validation.py` に 1 件を追加。合計 **236 件**（全 PASS）。

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
| `test_workflow.py` | 397 | `TestResolveCommandConfigRejectsAutoArgs` / `TestResolveDefaults` / `TestGetStepsModelEffort` / `TestGetStepsContinue` / `TestResolveWorkflowValue` / `TestResolveDefaultsOverrideKeys` / `TestGetStepsOverrideKeys` / `TestYamlSyncOverrideKeys` / `TestOverrideInheritanceMatrix` | `claude_loop_lib/workflow.py` |
| `test_issues.py` | 63 | `TestExtractStatusAssigned` | `claude_loop_lib/issues.py` |
| `test_claude_loop_cli.py` | 305 | `TestParseArgsLoggingOptions` / `TestRejectsAutoFlag` / `TestParseArgsNotifyOption` / `TestParseArgsAutoCommitBefore` / `TestParseArgsWorkflow` / `TestValidateAutoArgs` / `TestReadWorkflowKind` / `TestFindLatestRoughPlan` / `TestComputeRemainingBudget` | `scripts/claude_loop.py` CLI 層 |
| `test_claude_loop_integration.py` | — | `TestYamlIntegration` / `TestRunStepsSessionTracking` / `TestAutoWorkflowIntegration` / `TestStartupValidationIntegration` / `TestFeedbackInvariant` | `scripts/claude_loop.py` 統合テスト |
| `test_validation.py` | 419 | `TestValidateCategory` / `TestValidateSingleYamlShape` / `TestValidateDefaultsSection` / `TestValidateStepSchema` / `TestValidateOverrideWhitelist` / `TestValidateStepReferences` / `TestValidateStartupAggregation` / `TestValidateStartupExistingYamls` / `TestValidateRejectsLegacyKeys` | `claude_loop_lib/validation.py` |
| `test_issue_worklist.py` | 203 | `TestIssueWorklist` | `scripts/issue_worklist.py` |

## ver15.0 でのテスト変更

### `test_workflow.py`（385 行 → 397 行）

**追加**（2 件）:
1. `SCOUT_YAML_FILENAME` を import 一覧に追加
2. `TestResolveWorkflowValue.test_resolve_scout_returns_scout_yaml_path` — `resolve_workflow_value("scout", yaml_dir)` が `yaml_dir / SCOUT_YAML_FILENAME` を返すことを検証
3. `TestYamlSyncOverrideKeys.test_scout_yaml_uses_only_allowed_keys` — `load_workflow(SCOUT_YAML_FILENAME パス)` を呼び、step / defaults キーが `ALLOWED_STEP_KEYS` / `ALLOWED_DEFAULTS_KEYS` に収まることを assert

### `test_validation.py`（413 行 → 419 行）

**追加**（1 件）:
1. `TestValidateStartupExistingYamls.test_scout_yaml_passes` — `_make_args(workflow="scout")` で `validate_startup(YAML_DIR / SCOUT_YAML_FILENAME, args, YAML_DIR, PROJECT_ROOT)` が例外なく完走することを assert（`workflow.py` から `SCOUT_YAML_FILENAME` を直接 import）

## 検証結果（ver15.0 完了時点）

| コマンド | 結果 |
|---|---|
| `python -m unittest discover -s scripts/tests -t .` | 236/236 PASS |
| `python scripts/claude_loop.py --workflow scout --dry-run` | validation + resolve 完走、exit 0 |
| `pnpm exec vitest --run` | 変更なし（Python / Markdown / YAML のみの変更のため） |
