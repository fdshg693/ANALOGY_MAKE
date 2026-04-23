# CURRENT_tests: util ver11.0 — テスト構成

ver11.0 で `tests/test_claude_loop.py`（1881 行・41 クラス）を `scripts/tests/` 配下の 11 ファイルに分割完了。Python テストとアプリ本体の Vitest テストが物理的に分離された。テスト件数・アサーション内容は保全され、合計 **192 件**（pre-existing fail 1 件含む）のまま。

## テスト実行コマンド

```bash
# 全件実行（推奨）
python -m unittest discover -s scripts/tests -t .

# 個別ファイル指定
python -m unittest scripts.tests.test_commands

# 個別クラス指定
python -m unittest scripts.tests.test_workflow.TestOverrideInheritanceMatrix

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
| `test_claude_loop_integration.py` | 287 | `TestYamlIntegration` / `TestRunStepsSessionTracking` / `TestAutoWorkflowIntegration` | `scripts/claude_loop.py` 統合テスト |
| `test_issue_worklist.py` | 203 | `TestIssueWorklist` | `scripts/issue_worklist.py` |

## `_bootstrap.py` の実装

```python
"""sys.path setup for scripts/tests/ — imported for side effect only."""
from __future__ import annotations
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent  # scripts/
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
```

各テストファイルは import ブロック冒頭で `from . import _bootstrap  # noqa: F401` を実行してから `claude_loop` / `claude_loop_lib` を import する。

## 検証結果（ver11.0 完了時点）

- `python -m unittest discover -s scripts/tests -t .`: **192 件収集、191 pass + 1 fail**
  - fail: `TestIssueWorklist.test_limit_omitted_returns_all`（pre-existing fail）
- `pnpm exec vitest --run`: 15 ファイル・145 件 pass（変更なし）
- `scripts/__init__.py` は不要（Python 3.13 の implicit namespace package で `discover -t .` が動作）

## pre-existing fail

- `TestIssueWorklist.test_limit_omitted_returns_all`: ver11.0 前から失敗状態。`ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md` で追跡中。本バージョンはテスト構造変更のみなので修正対象外。

## ver10.0 からの変更点

| 変更 | 内容 |
|---|---|
| 削除 | `tests/test_claude_loop.py` (1881 行・41 クラス) |
| 新設 | `scripts/tests/` ディレクトリ（13 ファイル） |
| 変更 | `scripts/README.md` のテスト実行コマンドを `python -m unittest discover -s scripts/tests -t .` に更新 |
| `TestYamlSyncOverrideKeys._yaml_path` | ファイル位置変更（`tests/` → `scripts/tests/`）に伴い `parent.parent.parent / "scripts" / name` に調整（1 階層深くなった） |
