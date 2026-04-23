# CURRENT_tests: util ver12.0 — テスト構成

ver12.0 で `scripts/tests/test_validation.py`（37 ケース）を新規追加し、`test_claude_loop_integration.py` に smoke test 1 ケースを追加。合計 **230 件**（229 pass + 1 pre-existing fail）。

## テスト実行コマンド

```bash
# 全件実行（推奨）
python -m unittest discover -s scripts/tests -t .

# 個別ファイル指定
python -m unittest scripts.tests.test_validation

# 個別クラス指定
python -m unittest scripts.tests.test_validation.TestValidateStartupExistingYamls

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
| `test_commands.py` | 319 | `TestBuildCommandWithLogFilePath` / `TestBuildCommandWithMode` / `TestBuildCommandWithFeedbacks` / `TestBuildCommandWithModelEffort` / `TestBuildCommandWithSession` / `TestBuildCommandWithSystemPrompt` / `TestBuildCommandWithAppendSystemPrompt` | `claude_loop_lib/commands.py` |
| `test_workflow.py` | 378 | `TestResolveMode` / `TestResolveCommandConfigAutoArgs` / `TestResolveDefaults` / `TestGetStepsModelEffort` / `TestGetStepsContinue` / `TestResolveWorkflowValue` / `TestResolveDefaultsOverrideKeys` / `TestGetStepsOverrideKeys` / `TestYamlSyncOverrideKeys` / `TestOverrideInheritanceMatrix` | `claude_loop_lib/workflow.py` |
| `test_issues.py` | 63 | `TestExtractStatusAssigned` | `claude_loop_lib/issues.py` |
| `test_claude_loop_cli.py` | 305 | `TestParseArgsLoggingOptions` / `TestParseArgsAutoOption` / `TestParseArgsNotifyOption` / `TestParseArgsAutoCommitBefore` / `TestParseArgsWorkflow` / `TestValidateAutoArgs` / `TestReadWorkflowKind` / `TestFindLatestRoughPlan` / `TestComputeRemainingBudget` | `scripts/claude_loop.py` CLI 層 |
| `test_claude_loop_integration.py` | — | `TestYamlIntegration` / `TestRunStepsSessionTracking` / `TestAutoWorkflowIntegration` / `TestStartupValidationIntegration`（ver12.0 追加） | `scripts/claude_loop.py` 統合テスト |
| `test_validation.py` | — | `TestValidateCategory` / `TestValidateSingleYamlShape` / `TestValidateDefaultsSection` / `TestValidateStepSchema` / `TestValidateOverrideWhitelist` / `TestValidateStepReferences` / `TestValidateStartupAggregation` / `TestValidateStartupExistingYamls` | `claude_loop_lib/validation.py` |
| `test_issue_worklist.py` | 203 | `TestIssueWorklist` | `scripts/issue_worklist.py` |

## `test_validation.py` の構成（ver12.0 新規）

| クラス | ケース数 | カバレッジ |
|---|---|---|
| `TestValidateCategory` | 5 | CURRENT_CATEGORY 欠如 / 空 / 不正文字 / docs dir 欠如 / 正常 |
| `TestValidateSingleYamlShape` | 6 | ファイル欠如 / parse 失敗 / 非 dict / defaults 非 dict / steps 非 list / 正常 |
| `TestValidateDefaultsSection` | — | defaults 検証独立クラス（計画外に切り出し） |
| `TestValidateStepSchema` | 8 | prompt 欠如 / prompt 非 str / unknown key / override 型不正 / continue 型不正 / name 非 str / 複数違反の集約 / 正常 |
| `TestValidateOverrideWhitelist` | 4 | 未知 model（warning） / 未知 effort（warning） / 既知 model / 既知 effort |
| `TestValidateStepReferences` | 4 | 存在しない SKILL / 存在する SKILL / `/` 非始まり prompt / `/foo extra arg` の先頭トークン lookup |
| `TestValidateStartupAggregation` | 5 | 3 YAML 正常 / 1 YAML parse 失敗（他継続） / step 違反の並列収集 / warning のみで非 SystemExit / error で exit code 2 |
| `TestValidateStartupExistingYamls` | 4 | 実ファイル 3 本（`claude_loop.yaml` / `_quick.yaml` / `_issue_plan.yaml`）を validate → violations ゼロ（regression guard） |

**実装上の注意**: `shutil.which` は大半のケースで `unittest.mock.patch` で mock。`TestValidateStartupExistingYamls` のみ実ファイルと実 PATH を使用するため、`claude` CLI が PATH になければ fail する（`claude_loop.py` 実行可能環境前提のため実害なし）。

## `test_claude_loop_integration.py` への追加（ver12.0）

`TestStartupValidationIntegration` クラス（1 ケース）を追加。`main()` 相当フローをモックし、`validate_startup()` が SystemExit する場合に `_execute_yaml()` が呼ばれないことを assert する。

既存 `TestRunMainAuto` は tmp_dir を cwd として使用しており `.claude/skills/` が存在しないため validation が先行 error になる問題を、`validate_startup` を patch で no-op 化して回避した（validation の振る舞いではなく phase1/phase2 分岐を検証する意図のため）。

## 検証結果（ver12.0 完了時点）

| コマンド | 結果 |
|---|---|
| `python -m unittest scripts.tests.test_validation -v` | 37/37 PASS |
| `python -m unittest discover -s scripts/tests -t .` | 229/230 PASS（1 fail は pre-existing） |
| `pnpm exec vitest --run` | 変更なし（Python 変更のみのため） |

## pre-existing fail

- `TestIssueWorklist.test_limit_omitted_returns_all`: ver12.0 前から失敗状態。`ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md` で追跡中。本バージョンのスコープ外。
