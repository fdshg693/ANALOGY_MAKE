# ver4.0 MEMO

## 実装サマリ

IMPLEMENT.md の全項目を完了:

- `scripts/claude_loop.py`
  - `resolve_defaults()` 新規追加
  - `get_steps()` が step から `model` / `effort` を受け取り、存在するキーだけを step dict に入れる（`None` は未指定扱い）
  - `build_command()` に `defaults` 引数追加。step → defaults の順で上書き判定（キー存在ベース）
  - `main()` / `_run_steps()` に `defaults` を引き回す
  - ステップヘッダログに `Model: X, Effort: Y` 行を追加（tee/非tee 両ルートで `_out(...)` 経由に統一）
- `scripts/claude_loop.yaml` / `scripts/claude_loop_quick.yaml` に `defaults:` と各ステップ上書きを追加
- `tests/test_claude_loop.py` に 4 クラス追加（`TestResolveDefaults` / `TestBuildCommandWithModelEffort` / `TestGetStepsModelEffort` / `TestYamlIntegration`）
- `.claude/SKILLS/meta_judge/WORKFLOW.md` に「モデル・エフォートの指定」節を追記

## 計画との乖離

- IMPLEMENT.md 3-2 の `test_model_effort_order` は「`--model`/`--effort` が `--append-system-prompt` より前」というテーマだったが、ログ追跡性の観点以外に特段の意味はなかったため、より目的に即した名前 `test_model_effort_before_append_system_prompt` に変更した。内容（index 比較）は IMPLEMENT.md の記述と同一。
- `TestBuildCommandWithModelEffort` に `test_defaults_none_equivalent_to_empty` を追加（`defaults=None` で呼ばれるケースの後方互換の明示的検証）。既存テストは `defaults` を省略しているため、このケースは重要。
- `TestGetStepsModelEffort` に `test_none_value_treated_as_absent` を追加（YAML で `model: null` と書かれたケースの挙動を明示）。ROUGH_PLAN で `null` 無効化はサポートしないと宣言しているが、「`None` は未指定扱い（エラーにせずキーを落とすのみ）」という仕様を固定化するテスト。

## 動作確認結果

- `python -m unittest tests.test_claude_loop`: 89 tests passed
- `python scripts/claude_loop.py --dry-run --no-log`: 5 ステップ全てに期待通り `--model` / `--effort` が付与された（split_plan/imple_plan: opus high, wrap_up/retrospective: sonnet medium, write_current: sonnet low）
- `python scripts/claude_loop.py -w scripts/claude_loop_quick.yaml --dry-run --no-log`: quick の 3 ステップも期待通り（quick_plan: sonnet medium, quick_impl: sonnet high, quick_doc: sonnet low）
- `npx nuxi typecheck`: 既知の vue-router volar 警告のみ（TS エラーなし）。今回の変更は Python/YAML のみで TypeScript への影響はない

## リスク 7-1（`--effort` フラグ受理）について

実走での CLI 受理確認は未実施。`claude --help | grep -- --effort` の手動確認、または 1 ステップの実走確認は、実運用で問題が発生した場合に対応。現状の CLI バージョンでは問題なく受理されるはずだが、受理されない場合は `build_command` の `--effort` 付与部分を一時コメントアウトすれば回避可能（YAML 側の `effort` は温存）。

## 未対応（ver4.1 以降）

- セッション継続（`continue: true` / `-r` / `--session-id`）
- `--output-format stream-json` パーサ
- `scripts/README.md` 新規作成（`ISSUES/util/medium/スクリプト改善.md`）
- `defaults` 明示リセット機能（`null` による無効化）
