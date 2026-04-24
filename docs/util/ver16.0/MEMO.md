# ver16.0 MEMO — imple_plan 実装メモ

## 計画との乖離

乖離なし。`REFACTOR.md` Step 1〜2 と `IMPLEMENT.md` §2〜4 の構成に沿って実装した。

## `## リスク・不確実性` セクションの対応記録

`IMPLEMENT.md` §1 の各項目について以下の通り処理した:

### §1.1 新規ライブラリ / 未使用 API

- **該当なし** と計画で明記されており、本実装でも該当なし。検証不要。

### §1.2 型定義の不備 / ドキュメント不足の可能性

#### `_read_workflow_kind` の戻り値型変更

- **検証済み**: 呼び出し元は `scripts/claude_loop.py:_run_auto` の `phase2_kind` のみ。変更前の `QUICK_YAML_FILENAME if phase2_kind == "quick" else FULL_YAML_FILENAME` 分岐を `WORKFLOW_YAML_FILES[phase2_kind]` に置換したため、`"research"` 受け入れ時も KeyError 無し。`TestAutoWorkflowIntegration::test_auto_runs_issue_plan_then_research` が end-to-end で 8 step 呼び出しを確認（test 通過）。
- `test_auto_fallback_on_invalid_frontmatter` も既存通り pass（`banana` → `full` フォールバック維持）。

#### `--workflow auto` の dry-run 時の新ログ出力

- **検証済み**: `_run_auto` の `f"--- auto: phase2 = {phase2_kind} ({phase2_yaml.name}) ---"` は `phase2_kind` が `"research"` の場合も文字列として成立。format 修正不要。既存 dry-run テストは phase2 をスキップするため、"research" 文字列ログ自体は直接テストしていないが、format 文字列の `{str}` は常に成立する Python 標準挙動のため実害なし。

### §1.3 実行時挙動の不確実性

#### 8 step での `continue: true` 境界

- **検証済み**: `claude_loop_research.yaml` では `wrap_up` のみ `continue: true` を付与し、`/research_context` / `/experiment_test` は `continue: false`（session 分離、既存方針踏襲）。`_run_steps` のセッション継続ロジックは step 単位で `continue: true` のみを判定するため、追加修正不要。

#### `RESEARCH.md` / `EXPERIMENT.md` 不在時の `/imple_plan` 挙動

- **検証済み**: `.claude/skills/imple_plan/SKILL.md` 本文に「`RESEARCH.md` / `EXPERIMENT.md` は `workflow: full` / `quick` では存在しない。**存在しなくてもエラーにしない**（条件分岐で無視）」を明文化。SKILL テキスト指示のため、ランタイムの `FileNotFoundError` を避ける責任は `/imple_plan` 実行時の LLM に委譲。

#### `experiments/` 配下の既存スクリプト

- **検証済み**: 既存 4 本（`_shared.ts` / `01-basic-connection.ts` / `02-memory-management.ts` / `inspect-db.ts`）に変更なし。`experiments/README.md` を新規作成し、規約（コメントヘッダ・依存サブディレクトリ方針）を明文化。既存ファイルは規約未準拠だが破壊的変更は加えず、README の「既存ファイル」表に現状を記載。

## 結果サマリ

- REFACTOR: workflow.py / validation.py の workflow 値レジストリ化（1 commit）
- IMPLEMENT:
  - `scripts/claude_loop_research.yaml` 新規
  - `scripts/claude_loop_lib/workflow.py` に `RESEARCH_YAML_FILENAME` / `WORKFLOW_YAML_FILES["research"]` / `AUTO_TARGET_YAMLS` に 1 行追加
  - `scripts/claude_loop.py` の `_read_workflow_kind` / `_run_auto` / `--workflow` help を更新
  - `scripts/claude_loop*.yaml` の 5 ファイル NOTE コメントを 6 ファイル列挙に更新
  - `.claude/rules/scripts.md` / `scripts/README.md` / `scripts/USAGE.md` の同期契約記述を 5→6 に更新
  - `.claude/skills/research_context/SKILL.md` / `experiment_test/SKILL.md` 新規
  - `.claude/skills/issue_plan/SKILL.md` / `split_plan/SKILL.md` / `imple_plan/SKILL.md` / `meta_judge/WORKFLOW.md` を更新
  - `experiments/README.md` 新規
  - `scripts/tests/test_claude_loop_cli.py` / `test_workflow.py` / `test_claude_loop_integration.py` に 4 テスト追加
- Python テスト: 280 件 pass（REFACTOR 前 276 → +4）
- Vitest: 145 件 pass（影響なし）
- typecheck: vue-tsc の pre-existing MODULE_NOT_FOUND 警告のみ（CLAUDE.md 記載の既知警告、本変更とは無関係）

## 残課題 / 次バージョン候補

- `MASTER_PLAN/PHASE8.0.md` への「§1 実装済み」注記は `/wrap_up` / `/write_current` の責務範囲（本 SKILL スコープ外）
- `docs/util/ver16.0/CURRENT.md`（メジャー版必須）は `/write_current` が生成
- PHASE8.0 §1-2 完了条件チェックリスト（`IMPLEMENT.md` §6）は `/wrap_up` で各条件達成判定を行う
- ver16.1（PHASE8.0 §2 長時間コマンド deferred execution）/ ver16.2（PHASE8.0 §3 step 単位 token/cost 計測）は次メジャー以降

## ドキュメント更新提案

- `scripts/README.md` の「起動前 validation」節で `--workflow auto` 候補を「3 本」と記載していた箇所は「4 本」に更新済み（`claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_research.yaml` / `claude_loop_issue_plan.yaml`）
- `docs/util/ver15.x` の CURRENT.md / CHANGES.md には `research` workflow の記載が無いため、ver16.0 CURRENT.md で追補される前提

## 削除推奨

なし（本版は純粋に機能追加）。
