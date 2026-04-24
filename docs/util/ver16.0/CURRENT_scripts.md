# CURRENT_scripts: util ver16.0 — Python スクリプトと YAML ワークフロー定義

`scripts/` 配下のユーティリティスクリプト・YAML ワークフロー定義・Python テスト。ver16.0 では `claude_loop_lib/workflow.py` に `WORKFLOW_YAML_FILES` レジストリ・`AUTO_TARGET_YAMLS` 定数・`RESEARCH_YAML_FILENAME` を追加。`claude_loop_research.yaml` を新規作成。`claude_loop.py` の `_read_workflow_kind` を 3 値対応・`_run_auto` を dict 駆動に変更。テスト 4 件追加し計 280 件。

ver15.2 以降の主な追加: `questions.py` / `question_status.py` / `question_worklist.py`（ver15.2）、`notify.py` RunSummary + 永続通知（ver15.4）、`logging_utils.py write_stderr`（ver15.5）。

## ファイル一覧

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/scripts/get_latest_version.sh` | 43 | バージョン番号算出。`latest` / `major` / `next-minor` / `next-major` の 4 モード |
| `scripts/claude_loop.py` | 698 | エントリポイント。`--workflow auto` 3 分岐・各種ヘルパ。ver16.0 で `_run_auto` を `WORKFLOW_YAML_FILES` dict 駆動に変更 |
| `scripts/claude_loop_lib/__init__.py` | 0 | パッケージ初期化（空） |
| `scripts/claude_loop_lib/workflow.py` | 203 | YAML 読み込み・バリデーション・値リゾルバ。`WORKFLOW_YAML_FILES` dict レジストリ（ver16.0）・`AUTO_TARGET_YAMLS`（ver16.0）・`RESEARCH_YAML_FILENAME`（ver16.0）を含む |
| `scripts/claude_loop_lib/validation.py` | 345 | 起動前 validation。`AUTO_TARGET_YAMLS` 駆動で auto 候補 4 YAML を検証（ver16.0） |
| `scripts/claude_loop_lib/commands.py` | 76 | コマンド構築・ステップイテレータ |
| `scripts/claude_loop_lib/feedbacks.py` | 61 | フィードバックファイルのロード・消費 |
| `scripts/claude_loop_lib/frontmatter.py` | 42 | 共通 `parse_frontmatter(text) -> (dict|None, str)` 実装 |
| `scripts/claude_loop_lib/issues.py` | 53 | ISSUE frontmatter の共通ヘルパ（`VALID_STATUS` / `VALID_ASSIGNED` / `VALID_COMBOS` / `extract_status_assigned`） |
| `scripts/claude_loop_lib/questions.py` | — | ver15.2 新規。Question frontmatter 共通ヘルパ（`issues.py` 並列。`review` ステータス不在が主な差分） |
| `scripts/claude_loop_lib/logging_utils.py` | 57 | TeeWriter・ログパス生成・ステップヘッダ表示・duration フォーマット。ver15.5 で `write_stderr(line: str)` を追加 |
| `scripts/claude_loop_lib/git_utils.py` | 40 | git HEAD 取得・未コミット検出・自動コミット |
| `scripts/claude_loop_lib/notify.py` | — | Windows toast 通知・beep フォールバック。ver15.4 で `RunSummary` クラス追加・toast XML を `scenario='reminder'` に変更。ver15.5 で `_notify_beep` を `write_stderr` に寄せた |
| `scripts/claude_loop.yaml` | 43 | フルワークフロー定義（6 ステップ）。NOTE コメントは 6 ファイル sync 対象（ver16.0） |
| `scripts/claude_loop_quick.yaml` | 32 | 軽量ワークフロー定義（3 ステップ）。NOTE コメントは 6 ファイル sync 対象 |
| `scripts/claude_loop_issue_plan.yaml` | 22 | `/issue_plan` 単独実行用 YAML。NOTE コメントは 6 ファイル sync 対象 |
| `scripts/claude_loop_scout.yaml` | 23 | ver15.0 新規。`/issue_scout` 単独実行用 YAML。NOTE コメントは 6 ファイル sync 対象 |
| `scripts/claude_loop_question.yaml` | — | ver15.2 新規。`/question_research` 単独実行用 YAML。NOTE コメントは 6 ファイル sync 対象 |
| `scripts/claude_loop_research.yaml` | — | **ver16.0 新規。** `/research_context` / `/experiment_test` を挟んだ 8 ステップ research workflow。NOTE コメントは 6 ファイル sync 対象 |
| `scripts/claude_sync.py` | 58 | `.claude/` ⇔ `.claude_sync/` 同期 |
| `scripts/issue_status.py` | 93 | ISSUE の `status × assigned` 分布を表示 |
| `scripts/issue_worklist.py` | 163 | `--limit N` 付き ISSUE 絞り込み。デフォルト `--status ready,review` |
| `scripts/question_status.py` | — | ver15.2 新規。QUESTION の `status × assigned` 分布を表示 |
| `scripts/question_worklist.py` | — | ver15.2 新規。`--limit N` 付き Question 絞り込み。デフォルト `--status ready` |
| `scripts/README.md` | — | 概要・ファイル一覧・クイックスタート。ver16.0 で research workflow 節追加・auto 対象 YAML を「4 本」に更新 |
| `scripts/USAGE.md` | — | CLI オプション一覧・YAML 仕様詳細・ログ読解。ver16.0 で research workflow 節追加・同期契約を 6 ファイル表記に更新 |

## workflow.py モジュールの重要定数（ver16.0 現況）

```python
FULL_YAML_FILENAME = "claude_loop.yaml"
QUICK_YAML_FILENAME = "claude_loop_quick.yaml"
ISSUE_PLAN_YAML_FILENAME = "claude_loop_issue_plan.yaml"
SCOUT_YAML_FILENAME = "claude_loop_scout.yaml"
QUESTION_YAML_FILENAME = "claude_loop_question.yaml"
RESEARCH_YAML_FILENAME = "claude_loop_research.yaml"  # ver16.0 追加

# workflow 値 → YAML ファイル名（"auto" は sentinel のため含めない）
WORKFLOW_YAML_FILES: dict[str, str] = {
    "full": FULL_YAML_FILENAME,
    "quick": QUICK_YAML_FILENAME,
    "research": RESEARCH_YAML_FILENAME,  # ver16.0 追加
    "scout": SCOUT_YAML_FILENAME,
    "question": QUESTION_YAML_FILENAME,
}

RESERVED_WORKFLOW_VALUES: tuple[str, ...] = ("auto",) + tuple(WORKFLOW_YAML_FILES)
# = ("auto", "full", "quick", "research", "scout", "question")

# auto モードで起動前検証・phase2 候補となる YAML
AUTO_TARGET_YAMLS: tuple[str, ...] = (
    ISSUE_PLAN_YAML_FILENAME,
    FULL_YAML_FILENAME,
    QUICK_YAML_FILENAME,
    RESEARCH_YAML_FILENAME,  # ver16.0 追加
)
```

`scout` / `question` は `AUTO_TARGET_YAMLS` に含まれない（auto 非対象）。

## YAML ワークフロー定義

### 6 ファイル同期義務

`claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_research.yaml` / `claude_loop_issue_plan.yaml` / `claude_loop_scout.yaml` / `claude_loop_question.yaml` の `command` / `defaults` セクションは 6 ファイル間で常に同一内容を維持する（ver16.0 で 5 ファイル → 6 ファイル同期に拡張）。

### `scripts/claude_loop.yaml`（full）のステップ別設定

| ステップ | model | effort | continue |
|---|---|---|---|
| issue_plan | opus | high | false |
| split_plan | opus | high | false |
| imple_plan | opus | high | false |
| wrap_up | sonnet（defaults） | medium（defaults） | true |
| write_current | sonnet（defaults） | low | false |
| retrospective | opus | medium（defaults） | false |

### `scripts/claude_loop_quick.yaml`（quick）のステップ別設定

| ステップ | model | effort | continue |
|---|---|---|---|
| issue_plan | opus | high | false |
| quick_impl | sonnet（defaults） | high | true |
| quick_doc | sonnet（defaults） | low | true |

### `scripts/claude_loop_research.yaml`（research）のステップ別設定（**ver16.0 新規**）

| ステップ | model | effort | continue |
|---|---|---|---|
| issue_plan | opus | high | false |
| split_plan | opus | high | false |
| research_context | opus | high | false |
| experiment_test | opus | high | false |
| imple_plan | opus | high | false |
| wrap_up | sonnet（defaults） | medium（defaults） | true |
| write_current | sonnet（defaults） | medium（defaults） | false |
| retrospective | opus | medium（defaults） | false |

`/research_context` / `/experiment_test` は `continue: false`（session 分離。外部 API 呼び出しが主で session 継続に依存しない）。

### `scripts/claude_loop_scout.yaml`（scout）のステップ別設定

| ステップ | model | effort | continue |
|---|---|---|---|
| issue_scout | opus | high | false |

### `scripts/claude_loop_question.yaml`（question）のステップ別設定

| ステップ | model | effort | continue |
|---|---|---|---|
| question_research | opus | high | false |

## `scripts/claude_loop.py` の主要構成

### `main()` のフロー

```
parse_args()  ← try ブロック外（--help / 引数ミスで通知が出ないように）
validate_auto_args()  ← try ブロック外
try:
  signal.signal(SIGTERM, _sigterm_to_keyboard_interrupt)
  resolve_workflow_value() → resolved ("auto" | Path)
    ├─ "auto" → "auto"（sentinel）
    ├─ "full"     → scripts/claude_loop.yaml
    ├─ "quick"    → scripts/claude_loop_quick.yaml
    ├─ "research" → scripts/claude_loop_research.yaml  ← ver16.0 追加
    ├─ "scout"    → scripts/claude_loop_scout.yaml
    ├─ "question" → scripts/claude_loop_question.yaml
    └─ other      → Path(value).expanduser()
  _resolve_uncommitted_status()
  validate_startup()
  exit_code, stats = _run_selected()
    ├─ resolved == "auto" → _run_auto()
    └─ resolved は Path   → _execute_yaml()
except KeyboardInterrupt:
  result = "interrupted"; exit_code = 130
except SystemExit as e:
  記録して再 raise
finally:
  if not args.no_notify and not args.dry_run:
    notify_completion(RunSummary(...))
```

### `_run_auto()` の phase2 YAML 選択（ver16.0 変更後）

```python
# phase2_kind は _read_workflow_kind() により "quick" / "full" / "research" のいずれか
phase2_yaml = yaml_dir / WORKFLOW_YAML_FILES[phase2_kind]
```

`WORKFLOW_YAML_FILES` dict 駆動のため、将来 workflow 値が増えても分岐追加不要。

### 完了通知（ver15.4 実装）

`RunSummary` クラス（`notify.py`）が run 単位の通知本文を組み立て:

- 成功: `claude_loop / 2 loops / 12 steps / 14m 32s`
- 失敗: `failed at imple_plan (exit 1) / claude_loop / 1 loop / 3 steps / 4m 11s`
- 中断: `interrupted (SIGINT) at write_current / claude_loop / 1 loop / 5 steps / 7m 02s`

Windows toast は `scenario='reminder' duration='long'` XML + dismiss アクション構成。`reminder → long → beep` の 3 段フォールバック。beep fallback は `write_stderr`（stderr 出力、ver15.5）。

`_run_auto()` の `loops_completed` は phase2 のみを反映（phase1 は除外、ver15.5 修正）。

## `scripts/tests/` の構成

| ファイル | 行数 | 含むテストクラス |
|---|---|---|
| `__init__.py` | 0 | — |
| `_bootstrap.py` | 8 | — |
| `test_logging_utils.py` | 94 | `TestCreateLogPath` / `TestFormatDuration` |
| `test_git_utils.py` | 117 | `TestGetHeadCommit` / `TestCheckUncommittedChanges` / `TestAutoCommitChanges` |
| `test_notify.py` | 176 | `TestNotifyCompletion` / `TestRunSummary` / `TestNotifyBeep`（ver15.4〜15.5 で大幅追加） |
| `test_frontmatter.py` | 44 | `TestParseFrontmatter` |
| `test_feedbacks.py` | 168 | `TestParseFeedbackFrontmatter` / `TestLoadFeedbacks` / `TestConsumeFeedbacks` |
| `test_commands.py` | 341 | `TestBuildCommand*`（7 クラス） |
| `test_workflow.py` | 424 | `TestResolveCommandConfigRejectsAutoArgs` / `TestResolveDefaults` / `TestGetSteps*` / `TestResolveWorkflowValue` / `TestYamlSyncOverrideKeys` / `TestOverrideInheritanceMatrix`（ver16.0 で research 解決テスト・all-registered-values テスト追加） |
| `test_issues.py` | 63 | `TestExtractStatusAssigned` |
| `test_questions.py` | 91 | `TestExtractStatusAssigned`（questions 版） |
| `test_issue_worklist.py` | 203 | `TestIssueWorklist` |
| `test_question_worklist.py` | 134 | `TestQuestionWorklist` |
| `test_claude_loop_cli.py` | 501 | `TestParseArgs*` / `TestValidateAutoArgs` / `TestReadWorkflowKind` / `TestFindLatestRoughPlan` / `TestComputeRemainingBudget` / `TestMainNotifyRunSummary` / `TestSigtermHandler` / `TestWorkflowLabelFallback`（ver16.0 で `--workflow research` テスト追加） |
| `test_claude_loop_integration.py` | 461 | `TestYamlIntegration` / `TestRunStepsSessionTracking` / `TestAutoWorkflowIntegration` / `TestStartupValidationIntegration` / `TestFeedbackInvariant` / `TestAutoLoopCountSemantics`（ver16.0 で research auto 経路 end-to-end テスト追加） |
| `test_validation.py` | 425 | `TestValidateCategory` / `TestValidateSingleYamlShape` / `TestValidateDefaultsSection` / `TestValidateStepSchema` / `TestValidateOverrideWhitelist` / `TestValidateStepReferences` / `TestValidateStartupAggregation` / `TestValidateStartupExistingYamls` / `TestValidateRejectsLegacyKeys` |

**合計: 280 件 PASS**（ver15.0 236 件 → ver15.2 +16 → ver15.4 +25 前後 → ver15.5 +2 → ver16.0 +4）

## validation.py モジュール（ver16.0 現況）

### 公開 API

- `validate_startup(resolved, args, yaml_dir, cwd) -> None` — 唯一の公開関数。SystemExit(2) を副作用として投げる
- `Violation` dataclass / `KNOWN_MODELS` / `KNOWN_EFFORTS` / `ALLOWED_TOPLEVEL_KEYS` / `ALLOWED_COMMAND_KEYS` もテスト import 用に公開

### auto モード時の検証対象 YAML（ver16.0 変更後）

`AUTO_TARGET_YAMLS`（`workflow.py` 定義）駆動:

```python
# 起動時に 4 ファイルすべてのスキーマ不備を一括検出
(ISSUE_PLAN_YAML_FILENAME, FULL_YAML_FILENAME, QUICK_YAML_FILENAME, RESEARCH_YAML_FILENAME)
```

ver15.0 以前の 3 ファイル → ver16.0 で 4 ファイルに拡大。

### 検証項目と重大度

| # | 検証項目 | 重大度 |
|---|---|---|
| ① | `.claude/CURRENT_CATEGORY` の存在・中身（空文字・パス区切り文字を含む無効名）、`docs/{category}/` の存在 | error（ファイル未存在は warning + `app` フォールバック） |
| ② | YAML ファイルの存在・parse 成功・top-level が mapping であること | error |
| ② | top-level に `mode:` キーがある場合は専用エラー（ver13.0 廃止） | error |
| ② | top-level に未知キーがある場合は汎用エラー | error |
| ③ | `command.executable` が `shutil.which` で解決できること | error |
| ④ | `defaults` / `steps[]` のキー集合が `ALLOWED_DEFAULTS_KEYS` / `ALLOWED_STEP_KEYS` に収まること | error |
| ④ | override キー（`model` / `effort` / `system_prompt` / `append_system_prompt`）が非空 string であること | error |
| ④ | `continue` が bool であること | error |
| ④ | `model` 値が `KNOWN_MODELS = {"opus", "sonnet", "haiku"}` に含まれること | **warning** |
| ④ | `effort` 値が `KNOWN_EFFORTS = {"low", "medium", "high", "xhigh", "max"}` に含まれること | **warning** |
| ⑤ | `step.prompt` が `/` 始まりの場合、`.claude/skills/<name>/SKILL.md` が存在すること | error |
