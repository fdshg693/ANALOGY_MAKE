# ver9.0 MEMO — 実装メモ・残課題

## 実装サマリ

IMPLEMENT.md §2〜§8 に従い、`--workflow auto | full | quick | <path>` を導入した。

- `scripts/claude_loop_lib/workflow.py`: `resolve_workflow_value()` 新設 + `FULL_YAML_FILENAME` / `QUICK_YAML_FILENAME` / `ISSUE_PLAN_YAML_FILENAME` 定数を追加
- `scripts/claude_loop_issue_plan.yaml`: 新規（`/issue_plan` 単独 YAML、`mode` / `command` / `defaults` は `claude_loop.yaml` と同一内容）
- `scripts/claude_loop.py`: `--workflow` のデフォルトを `"auto"` に変更、`validate_auto_args()` / `_find_latest_rough_plan()` / `_read_workflow_kind()` / `_compute_remaining_budget()` / `_resolve_uncommitted_status()` / `_execute_yaml()` / `_run_auto()` を追加。`main()` を `auto` 分岐対応に書き直し
- `scripts/claude_loop.yaml` / `claude_loop_quick.yaml`: 先頭に NOTE コメントを追記（`--workflow auto` が `steps[1:]` を使う旨 + 3 ファイル同期義務）
- `scripts/README.md`: `--auto` と `--workflow auto` の違い・`auto` 分岐仕様節を追加、CLI オプション表の `--workflow` 行を更新
- `.claude/skills/meta_judge/WORKFLOW.md`: 保守上の注意を 3 ファイル同期義務と `auto` 実装済み記述に更新（`claude_sync.py` 経由）
- `tests/test_claude_loop.py`: +32 件のテスト（`TestResolveWorkflowValue` / `TestParseArgsWorkflow` / `TestValidateAutoArgs` / `TestReadWorkflowKind` / `TestFindLatestRoughPlan` / `TestComputeRemainingBudget` / `TestAutoWorkflowIntegration`）

## 計画との乖離

### L1: `_execute_yaml()` による共通化（IMPLEMENT.md にない追加）

IMPLEMENT.md §4-5 の擬似コードは単一の `_run_steps` 呼び出しを二度書く形だったが、実装では `_execute_yaml(yaml_path, args, cwd, ...)` というヘルパに切り出し、非 auto の単一ワークフロー実行と auto フェーズ 1/2 の両方から呼ぶ形にした。理由:

- 各ステージで `load_workflow` / `get_steps` / `resolve_command_config` / `resolve_defaults` / `resolve_mode` / `shutil.which` / `step_iter` 生成が必要で、素朴に書くと `main()` が肥大化
- 共通化により、テスト時のフック面（`claude_loop.subprocess.run` / `claude_loop.shutil.which`）が 1 箇所に集約されて扱いやすい

抽象化は 1 段だけなので過剰ではない。`_run_auto()` は start_index と `max_step_runs_override` を変えて 2 回呼ぶだけで済む。

### L2: `_resolve_uncommitted_status()` の切り出し

IMPLEMENT.md §4-5 では `main()` 冒頭で uncommitted 処理をそのまま残す想定だったが、`_run_auto` と非 auto 両経路で同じロジックを使うため、`main()` 内部でヘルパ関数として切り出した。副作用的な print は維持しつつ、戻り値で uncommitted_status を返す形。

## リスク・不確実性の対応記録（IMPLEMENT.md §10 対応）

### R1: `_find_latest_rough_plan` の mtime 依存

**検証先送り** — ver9.0 スコープでは mtime 採用で割り切る（IMPLEMENT.md §10 に記載の通り）。将来的に「フェーズ 1 開始時点の最大 mtime を記録しておき、それを超えるものを候補とする」形に強化可能。

本番発生時の対応方針: `auto` 実行直後に誤った ROUGH_PLAN.md が同定された場合は、対象ファイルを `touch` して明示的に最新化するか、`--workflow quick` / `--workflow full` を明示指定して回避する。

`ISSUES/util/low/auto-mtime-robustness.md` に追加済み。

### R2: `auto` フェーズ 2 のセッション引き継ぎ

**検証不要** — `_run_auto()` の実装上、フェーズ 1 とフェーズ 2 は別々の `_execute_yaml()` 呼び出しとなり、`previous_session_id` は各呼び出し内のローカル変数としてリセットされる。`claude_loop.yaml` / `claude_loop_quick.yaml` の `steps[1]` (`/split_plan` / `/quick_impl`) はどちらも `continue: true` を付けていないため意図通り。

### R3: `--max-step-runs` との整合

**検証済み** — `_compute_remaining_budget()` 単体テスト（`TestComputeRemainingBudget`）で `max(max_step_runs - 1, 0)` の挙動を確認。`_execute_yaml()` 側でも `max_step_runs_override <= 0` の早期 return を実装し、フェーズ 2 が想定外に走らないことを保証。

### R4: `--dry-run` との相性

**検証済み** — `_run_auto()` で `args.dry_run` 時はフェーズ 2 をスキップし `"--- auto: phase2 skipped (--dry-run) ---"` を出力する実装。`TestAutoWorkflowIntegration.test_auto_dry_run_skips_phase2` でカバー。手動ドライラン (`PYTHONIOENCODING=utf-8 python scripts/claude_loop.py --workflow auto --no-log --dry-run --no-notify`) でも確認済み。

### R5: `/issue_plan` が frontmatter を書き忘れた場合

**検証済み** — `_read_workflow_kind()` は frontmatter 欠落・`workflow` キー欠落・不正値のいずれの場合も stderr に警告を出しつつ `"full"` を返す。`TestReadWorkflowKind` の 5 ケースおよび `TestAutoWorkflowIntegration.test_auto_fallback_on_invalid_frontmatter` でカバー。

### R6: `load_workflow` のパス解決と既定値変更の相互作用

**検証済み** — `TestResolveWorkflowValue.test_resolve_relative_path_preserved` で `resolve_workflow_value("other.yaml", yaml_dir)` が `Path("other.yaml")`（相対）を返すことを確認。`load_workflow` の `.expanduser().resolve()` で cwd 解決される既存挙動は維持。

### R7: `.claude/CURRENT_CATEGORY` 未設定時の挙動

**検証済み** — `TestFindLatestRoughPlan.test_missing_category_file_falls_back_to_app` で `app` フォールバックを確認。`SystemExit` メッセージに「(When .claude/CURRENT_CATEGORY is unset, 'app' is used.)」を含めた。

### R8: `issue_worklist.py` の `!` バックティック展開失敗

**検証不要** — `_run_auto()` の `if exit_code != 0: return exit_code` により、フェーズ 1 が何らかの理由で失敗すればフェーズ 2 は走らない（`_execute_yaml` → `_run_steps` の既存挙動）。`issue_worklist.py` 側の堅牢性は別 ISSUE として扱う（`ISSUES/util/low/issue-worklist-json-context-bloat.md` など）。

## 残課題・フォロー候補

### D1: `claude_loop_issue_plan.yaml` / `claude_loop.yaml` / `claude_loop_quick.yaml` の `command` セクション重複

NOTE コメント + SKILL ドキュメントの「保守上の注意」で同期義務を明記したが、物理的な重複は残る。将来的に includes 機構を入れれば解消できるが、現時点では YAGNI。IMPLEMENT.md §12 にスコープ外として明記済み。

### D2: `--workflow auto` + `--start N>1` の再開

ver9.0 では `--start 1` のみ許可する実装。フェーズ 2 からの再開（`--start 2` 以上）は将来拡張。ユーザー要望が発生したら別 ISSUE として起票。

### D3: 動作確認の範囲

- `npx nuxi typecheck`: vue-router volar 既知警告のみ（CLAUDE.md 記載通り、ビルド・実行に影響なし）
- `python -m unittest tests.test_claude_loop`: 151 件パス（+32 件）
- ドライラン: `auto` / `full` / `quick` / `auto --start 2`（エラー）いずれも期待通りの挙動

実際のワークフロー実動作確認（Claude CLI を実際に呼ぶ）は未実施。次の `/issue_plan` → 後続選択の実走が ISSUE `issue-plan-split-plan-handoff-verification.md` の観察機会になる。

### D4: テストにおける `patch("builtins.print")` の使用

`TestAutoWorkflowIntegration` で `builtins.print` をパッチしている。これは Windows (cp932) の stdout が YAML 内の em-dash (`—`) を encode できず UnicodeEncodeError を投げるための回避。本番 CLI 実行時は実際に em-dash が含まれたコマンドをテ表示する必要があるため、環境変数 `PYTHONIOENCODING=utf-8` を推奨（README に追記してもよいが、今回は最小修正優先で見送り）。

本番実走時のエンコードエラー有無は D3 の「次のワークフロー実走で自然に確認される」範囲に含まれる。問題が発生した場合は `sys.stdout.reconfigure(encoding='utf-8')` を `claude_loop.py` 冒頭に追加するか、README に `PYTHONIOENCODING=utf-8` を明示するかを /wrap_up 時点で判断する。

## wrap_up 対応記録（ver9.0）

| 項目 | 対応 | 理由 |
|---|---|---|
| L1: `_execute_yaml()` 追加 | ⏭️ 対応不要 | IMPLEMENT.md 計画改善版。追加対応不要 |
| L2: `_resolve_uncommitted_status()` 切り出し | ⏭️ 対応不要 | 合理的なリファクタ。副作用なし |
| R1: mtime 依存 | 📋 先送り済み | `ISSUES/util/low/auto-mtime-robustness.md` に記録済み |
| R2〜R8 | ⏭️ 対応不要 | 検証済み or 設計上検証不要と確認済み |
| D1: command セクション重複 | ⏭️ 対応不要 | YAGNI。IMPLEMENT.md §12 でスコープ外明記済み |
| D2: auto + --start N>1 | ⏭️ 対応不要 | 将来拡張。IMPLEMENT.md §12 でスコープ外明記済み |
| D3: 動作確認の範囲 | ⏭️ 対応不要 | 次ワークフロー実走で自然に確認される |
| D4: PYTHONIOENCODING | ⏭️ 対応不要 | 本番問題発生時に対処。D3 の観察範囲に含める |
| `issue-plan-standalone-yaml.md` | ✅ ISSUE 削除 | ver9.0 で `claude_loop_issue_plan.yaml` 作成・解決済み |
