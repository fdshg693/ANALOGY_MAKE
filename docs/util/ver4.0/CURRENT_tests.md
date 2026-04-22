# CURRENT_tests: util ver4.0 — テスト構成

`tests/test_claude_loop.py`（741 行）は `scripts/claude_loop.py` のユニットテスト。`unittest` を使用、22 テストクラス・89 テストケース。

## テストクラス一覧

| テストクラス | 行 | テスト対象 |
|---|---|---|
| `TestCreateLogPath` | 26 | `create_log_path()`: ファイル名形式、ディレクトリ配置、stem 抽出、ディレクトリ作成 |
| `TestGetHeadCommit` | 71 | `get_head_commit()`: 正常取得、非ゼロ終了、git 未インストール、空白トリム |
| `TestFormatDuration` | 109 | `format_duration()`: 秒・分・時のフォーマット、境界値、小数点切り捨て |
| `TestBuildCommandWithLogFilePath` | 144 | `build_command()` のログパス引数: None 時、指定時、引数順序、空文字列 |
| `TestParseArgsLoggingOptions` | 184 | `--no-log` / `--log-dir` のデフォルト・指定・共存 |
| `TestNotifyCompletion` | 213 | `notify_completion()`: toast 成功、beep フォールバック、シングルクォートエスケープ |
| `TestResolveMode` | 236 | `resolve_mode()`: デフォルト、YAML `auto=true`、CLI `--auto` オーバーライド |
| `TestBuildCommandWithMode` | 249 | `build_command()` の auto_mode: AUTO プロンプト注入、非 AUTO 時プロンプトなし、ログ＋モードの単一プロンプト結合 |
| `TestParseArgsAutoOption` | 271 | `--auto` フラグのデフォルト・指定 |
| `TestParseArgsNotifyOption` | 287 | `--no-notify` フラグのデフォルト・指定 |
| `TestResolveCommandConfigAutoArgs` | 303 | `resolve_command_config()` の `auto_args` 抽出・デフォルト空リスト |
| `TestCheckUncommittedChanges` | 317 | `check_uncommitted_changes()`: 変更あり、変更なし、git 未検出 |
| `TestAutoCommitChanges` | 345 | `auto_commit_changes()`: 成功→ハッシュ返却、`git add` 失敗→None、`git commit` 失敗→None |
| `TestParseArgsAutoCommitBefore` | 379 | `--auto-commit-before` フラグのデフォルト・指定 |
| `TestParseFeedbackFrontmatter` | 395 | フィードバック frontmatter 解析: 文字列/リスト/未指定（キャッチオール）/無効 YAML/空 body |
| `TestLoadFeedbacks` | 435 | `load_feedbacks()`: マッチ/不一致/キャッチオール/ソート順/`done/` 除外 |
| `TestConsumeFeedbacks` | 496 | `consume_feedbacks()`: 正常移動/ディレクトリ自動作成/空リスト/同名上書き |
| `TestBuildCommandWithFeedbacks` | 546 | `build_command(feedbacks=...)`: 注入/複数 FB の `---` 区切り/なしの場合 |
| `TestResolveDefaults` | 579 | **ver4.0 新規**。`resolve_defaults()`: `defaults` キー無→空 dict、両方指定、片方のみ、非マッピング→`SystemExit`、空文字列→`SystemExit` |
| `TestBuildCommandWithModelEffort` | 607 | **ver4.0 新規**。`build_command(defaults=...)`: defaults/step ともに未設定で引数なし、defaults 継承、step による上書き、step のみ指定、`--model`/`--effort` が `--append-system-prompt` より前に配置、`defaults=None` が空 dict 相当 |
| `TestGetStepsModelEffort` | 661 | **ver4.0 新規**。`get_steps()` の model/effort 受け取り: キー無なら dict に含まれない、両方指定、片方のみ、`None` は未指定扱い、空文字列→`SystemExit`、非文字列→`SystemExit` |
| `TestYamlIntegration` | 700 | **ver4.0 新規**。`load_workflow` → `get_steps` + `resolve_defaults` → `build_command` の統合フローで、defaults 継承とステップ上書きが期待通り cmd に反映されることを検証 |

## 実行方法

```bash
python -m unittest tests.test_claude_loop   # 全テスト実行
python -m unittest tests.test_claude_loop.TestResolveDefaults  # クラス単位実行
pytest tests/test_claude_loop.py -q        # pytest 経由でも実行可能
```

## 補助インポート

テストファイルは `unittest`・`subprocess` モック用の `unittest.mock`・一時ディレクトリ用の `tempfile`・`shutil`・`pathlib.Path` に加え、`scripts/claude_loop.py` から以下をインポート:

- `create_log_path` / `get_head_commit` / `format_duration` / `build_command` / `print_step_header` / `parse_args`
- `notify_completion` / `_notify_toast` / `_notify_beep` / `resolve_mode` / `resolve_command_config`
- `check_uncommitted_changes` / `auto_commit_changes`
- `parse_feedback_frontmatter` / `load_feedbacks` / `consume_feedbacks`
- `resolve_defaults` / `get_steps` / `load_workflow`（ver4.0 で追加）
