# CURRENT_tests: util ver8.0 — テスト構成

`tests/test_claude_loop.py` は `scripts/claude_loop.py` と `scripts/claude_loop_lib/` のユニットテスト。`unittest` を使用。ver8.0 でのワークフロー YAML 変更（`/issue_plan` 追加・`/quick_plan` 削除）後も既存テスト全件がパスしていることを確認済み。テストクラス・テストケース数は ver7.0 から変化なし（28 テストクラス・119 テストケース）。`pnpm test` では vitest（app カテゴリ）と unittest の合計 145 テストが全パス。

## ver8.0 での検証結果

- `python -m unittest tests.test_claude_loop`: **119 件 全パス**
- `pnpm test`: **15 ファイル / 145 件 全パス**
- `npx nuxi typecheck`: 既知の vue-router volar 警告のみ（ビルド・実行に影響なし）

YAML の `steps:` 構造に対してハードコードされた期待値は存在せず、`split_plan` は feedbacks の step 名例として登場するのみで破綻しなかった。

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
python -m unittest tests.test_claude_loop.TestIssueWorklist  # クラス単位
pnpm test                                           # vitest + unittest 両方実行
```

## テスト方針

- `TestIssueWorklist`: `tempfile.TemporaryDirectory` で一時 `ISSUES/` ツリーを組み、`issue_worklist.REPO_ROOT` / `ISSUES_DIR` をモンキーパッチする方式
- stderr の warning 検証: `io.StringIO` を `sys.stderr` に差し替えて文字列で assert する標準手法
- `issue_status.py` のユニットテストは未追加（外部挙動の同一性は `TestExtractStatusAssigned` + 手動スモークで保証）
- YAML の `steps:` 構造に対するハードコード期待値なし（SKILL 名追加・削除でテストが壊れない設計）
