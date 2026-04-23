# CURRENT_tests: util ver5.0 — テスト構成

`tests/test_claude_loop.py` は `scripts/claude_loop.py` と `scripts/claude_loop_lib/` のユニットテスト。`unittest` を使用、25 テストクラス・103 テストケース（ver4.0: 22 クラス・89 ケース → ver5.0: +3 クラス・+14 ケース）。

## テストクラス一覧

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
| `TestResolveDefaults` | `resolve_defaults()`: `defaults` キー無→空 dict、両方指定、片方のみ、非マッピング→`SystemExit`、空文字列→`SystemExit` |
| `TestBuildCommandWithModelEffort` | `build_command(defaults=...)`: defaults/step ともに未設定で引数なし、defaults 継承、step による上書き |
| `TestGetStepsModelEffort` | `get_steps()` の model/effort 受け取り: キー無なら dict に含まれない、`None` は未指定扱い、空文字列→`SystemExit` |
| `TestYamlIntegration` | `load_workflow` → `get_steps` + `resolve_defaults` → `build_command` の統合フロー |
| `TestBuildCommandWithSession` | **ver5.0 新規**。`build_command(session_id=..., resume=...)`: `resume=True` で `-r` フラグ、`resume=False` で `--session-id` フラグ、session_id=None で両フラグなし、`--append-system-prompt` より前に配置 |
| `TestGetStepsContinue` | **ver5.0 新規**。`get_steps()` の `continue` 受け取り: 省略→False、true/false 正規化、非 bool→`SystemExit` |
| `TestRunStepsSessionTracking` | **ver5.0 新規**。`_run_steps()` のセッション ID 管理: `continue=false` で新規 UUID、`continue=true` で `-r` による引き継ぎ、`--start > 1` で continue 無効化・警告 |

## 実行方法

```bash
python -m unittest tests.test_claude_loop          # 全テスト実行
python -m unittest tests.test_claude_loop.TestBuildCommandWithSession  # クラス単位
pnpm test                                           # pnpm 経由（vitest + unittest 両方実行）
```

## 補助インポート

テストファイルは `unittest`・`unittest.mock`・`tempfile`・`shutil`・`pathlib.Path` + `uuid` に加え、`scripts/claude_loop.py` と `scripts/claude_loop_lib/` から以下をインポート:

- `create_log_path` / `get_head_commit` / `format_duration` / `build_command` / `print_step_header` / `parse_args`
- `notify_completion` / `_notify_toast` / `_notify_beep` / `resolve_mode` / `resolve_command_config`
- `check_uncommitted_changes` / `auto_commit_changes`
- `parse_feedback_frontmatter` / `load_feedbacks` / `consume_feedbacks`
- `resolve_defaults` / `get_steps` / `load_workflow`
- `_run_steps`（ver5.0 で `TestRunStepsSessionTracking` 向けに追加）
