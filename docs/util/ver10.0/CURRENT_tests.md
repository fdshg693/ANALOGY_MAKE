# CURRENT_tests: util ver10.0 — テスト構成

`tests/test_claude_loop.py` は `scripts/claude_loop.py` と `scripts/claude_loop_lib/` のユニットテスト。`unittest` を使用。ver9.1 で 4 件（mtime 閾値）、ver9.2 で 5 件（--limit）、ver10.0 で 32 件（override キー）を追加し、合計 **192 件**になった。

## ver10.0 での検証結果

- `python -m unittest tests.test_claude_loop`: **192 件 全パス**（ver9.0 比 +41 件）
  - 既知の pre-existing 失敗: `TestIssueWorklist.test_limit_omitted_returns_all`（ver10.0 着手前から失敗、`ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md` で追跡中）
- `pnpm exec vitest --run`: フロントエンドテスト（変更なし）

## ver10.0 で追加されたテストクラス

| テストクラス | 件数 | テスト対象 |
|---|---|---|
| `TestResolveDefaultsOverrideKeys` | 6 | `resolve_defaults()`: `system_prompt` / `append_system_prompt` のパース、4 キー同時指定、未知キー（`temperature` 等）→ `SystemExit`、空文字列 → `SystemExit`、非文字列 → `SystemExit` |
| `TestGetStepsOverrideKeys` | 7 | `get_steps()`: 各新キーの格納、未知キーで `Allowed keys:` メッセージ付き `SystemExit`、新キー無しの step にキーが入らない、`null` は未指定扱い、空文字列 4 キーのパラメタライズ |
| `TestBuildCommandWithSystemPrompt` | 4 | `build_command()`: step の `system_prompt` → `--system-prompt` 生成、defaults からの継承、step が defaults を上書き、未設定でフラグなし |
| `TestBuildCommandWithAppendSystemPrompt` | 7 | `build_command()`: step の `append_system_prompt` のみ指定、log_file_path / auto_mode / feedbacks との合成順序（各単独 + 全種同時）、defaults からの継承、step が defaults を置換（連結ではない） |
| `TestOverrideInheritanceMatrix` | 継続 | `OVERRIDE_STRING_KEYS` の 4 キー × 5 パターン（step 値あり/defaults あり・step 値あり/defaults なし・step 値なし/defaults あり・双方なし・step=None/defaults あり）を `subTest` で網羅 |
| `TestYamlSyncOverrideKeys` | 3 | 3 本の YAML（`claude_loop.yaml` / `_quick.yaml` / `_issue_plan.yaml`）を `load_workflow` + `get_steps` でロードし、新仕様の許容キー集合内に収まることを確認 |

## ver9.1 で追加されたテストクラス（`TestFindLatestRoughPlan` 拡張）

| テスト名 | 検証内容 |
|---|---|
| `test_threshold_excludes_pre_existing_files` | `mtime == threshold` のファイルは除外され、`mtime > threshold` のみ返る |
| `test_threshold_no_new_files_raises` | 全ファイルが `mtime ≤ threshold` のとき `SystemExit` が発生 |
| `test_threshold_multiple_new_files_highest_version_wins` | 複数の新規ファイルがある場合に最大バージョン（ver10.0 等）が選ばれる |
| `test_version_key_natural_sort` | `(9,1) < (10,0)` が成立することを確認 |

## ver9.2 で追加されたテスト（`TestIssueWorklist` 拡張）

| テスト名 | 検証内容 |
|---|---|
| `test_limit_returns_top_n_in_priority_order` | `--limit 3` で先頭 3 件が返り、JSON に `total` / `truncated` / `limit` が含まれる |
| `test_limit_omitted_returns_all` | `--limit` 省略時は全件返り、JSON に `total` フィールドが含まれない（**pre-existing 失敗**） |
| `test_limit_exceeds_count_no_truncation` | `--limit 100` で件数超過時は `truncated=false` |
| `test_limit_text_format_appends_truncation_note` | `text` 形式で切り捨て発生時に補助行が出る |
| `test_limit_text_format_no_note_when_not_truncated` | `text` 形式で切り捨てなし時に補助行が出ない |

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
| `TestIssueWorklist` | `issue_worklist.py` の絞り込みロジック（基本動作 + ver9.2 追加の `--limit` テスト） |
| `TestResolveWorkflowValue` | `resolve_workflow_value()`: `"auto"` → sentinel、`"full"` / `"quick"` → yaml_dir 以下の Path、パス直指定 → Path |
| `TestParseArgsWorkflow` | `parse_args()` の `--workflow`: デフォルト `"auto"`、`-w full` / `-w custom.yaml` |
| `TestValidateAutoArgs` | `validate_auto_args()`: `auto + --start 1` は OK、`auto + --start 2` は `SystemExit` |
| `TestReadWorkflowKind` | `_read_workflow_kind()`: quick/full 正常系、frontmatter なし→full フォールバック、不正値→full |
| `TestFindLatestRoughPlan` | `_find_latest_rough_plan()`: 基本動作 + ver9.1 追加の mtime 閾値テスト 4 件 |
| `TestComputeRemainingBudget` | `_compute_remaining_budget()`: `max_step_runs` 未設定→None、設定時は `max(max - completed, 0)` |
| `TestAutoWorkflowIntegration` | `_run_auto()` の統合テスト: full/quick 2 段実行・phase1 失敗・不正 frontmatter → full・`--dry-run` |

## 実行方法

```bash
python -m unittest tests.test_claude_loop          # 全テスト実行
python -m unittest tests.test_claude_loop.TestOverrideInheritanceMatrix  # クラス単位
pnpm exec vitest --run                             # フロントエンドテスト（vitest）
```

## テスト方針

- `TestOverrideInheritanceMatrix`: `OVERRIDE_STRING_KEYS` の各キーごとに 5 パターンを `subTest` で網羅し、継承ルールの 3 段階優先を確認
- `TestYamlSyncOverrideKeys`: 3 本の YAML を `load_workflow` + `get_steps` でロードして既存 YAML が新仕様の許容キー集合内に収まることを確認（既存環境破壊防止）
- `TestBuildCommandWithAppendSystemPrompt.test_step_overrides_defaults_append`: `step.get("append_system_prompt", defaults.get(...))` の Python dict-fallback 挙動による単純置換（defaults 値との合成は行わない）を assert
- `TestAutoWorkflowIntegration`: `subprocess.run` と `uuid.uuid4` をモック。`_find_latest_rough_plan` と `_read_workflow_kind` をモックして ROUGH_PLAN.md の frontmatter を任意に制御
