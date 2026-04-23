# CURRENT_tests: util ver14.0 — テスト構成

ver14.0 で `test_claude_loop_integration.py` に `TestFeedbackInvariant` クラスを追加。合計 **233 件**（全 PASS）。

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
| `test_claude_loop_integration.py` | — | `TestYamlIntegration` / `TestRunStepsSessionTracking` / `TestAutoWorkflowIntegration` / `TestStartupValidationIntegration` / `TestFeedbackInvariant` | `scripts/claude_loop.py` 統合テスト |
| `test_validation.py` | 413 | `TestValidateCategory` / `TestValidateSingleYamlShape` / `TestValidateDefaultsSection` / `TestValidateStepSchema` / `TestValidateOverrideWhitelist` / `TestValidateStepReferences` / `TestValidateStartupAggregation` / `TestValidateStartupExistingYamls` / `TestValidateRejectsLegacyKeys` | `claude_loop_lib/validation.py` |
| `test_issue_worklist.py` | 203 | `TestIssueWorklist` | `scripts/issue_worklist.py` |

## ver14.0 でのテスト変更

### `test_claude_loop_integration.py` — 追加

**追加**（ver14.0 新規クラス）:
- `TestFeedbackInvariant` — 2 ケース:
  1. `test_feedback_preserved_on_step_failure`: step が非ゼロ終了した場合、`FEEDBACKS/dummy-feedback.md` が `FEEDBACKS/` に残り `FEEDBACKS/done/` が空であることを検証（FEEDBACK 温存 invariant）
  2. `test_feedback_consumed_on_step_success`: step が正常終了（returncode=0）した場合、`FEEDBACKS/dummy-feedback.md` が `FEEDBACKS/done/` に移動することを検証

ver13.1 で `TestFeedbackInvariant` 追加済みと IMPLEMENT.md に記載されていたが、実際には ver14.0 での追加（`test_claude_loop_integration.py` は ver13.1 で件数確認済の 231 件に `TestFeedbackInvariant` 2 件が加わって 233 件となった）。

## 検証結果（ver14.0 完了時点）

| コマンド | 結果 |
|---|---|
| `python -m unittest discover -s scripts/tests -t .` | 233/233 PASS |
| `pnpm exec vitest --run` | 変更なし（Python / Markdown のみの変更のため） |
