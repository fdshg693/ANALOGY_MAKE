# ver15.2 CHANGES

ver15.1 からの変更差分。PHASE7.1 §2（`QUESTIONS/` queue + `question_research` workflow + 周辺ツール）を add-only で実装。付随 ISSUE 2 件を消化。

## 変更ファイル一覧

### 新規追加

| ファイル | 概要 |
|---|---|
| `QUESTIONS/README.md` | Question の frontmatter 仕様・ライフサイクル・報告書配置・`ISSUES/` との境界を定義 |
| `QUESTIONS/util/{high,medium,low,done}/.gitkeep` | ディレクトリ骨格 |
| `docs/util/questions/.gitkeep` | 調査報告書の出力先（先行作成、R6 抑制策） |
| `scripts/claude_loop_question.yaml` | 調査専用 workflow 定義（1 ステップ、opus / high）|
| `scripts/claude_loop_lib/questions.py` | Question frontmatter 共通ヘルパ（`issues.py` 並列、`review` 不在）|
| `scripts/question_status.py` | 分布表示（`issue_status.py` 並列）|
| `scripts/question_worklist.py` | 着手候補抽出（`issue_worklist.py` 並列、既定 `--status ready`）|
| `.claude/skills/question_research/SKILL.md` | 調査専用 SKILL（5 セクション報告書 / 後処理ルール）|
| `scripts/tests/test_questions.py` | `extract_status_assigned` のテスト 5 件 |
| `scripts/tests/test_question_worklist.py` | `question_worklist.py` のテスト 7 件 |
| `docs/util/ver15.2/IMPLEMENT.md` | 実装計画（`/split_plan` 成果物）|
| `docs/util/ver15.2/MEMO.md` | 実装メモ・リスク検証結果 |
| `docs/util/ver15.2/CHANGES.md` | 本ファイル |

### 変更

| ファイル | 概要 |
|---|---|
| `scripts/claude_loop_lib/workflow.py` | `QUESTION_YAML_FILENAME` 追加・`RESERVED_WORKFLOW_VALUES` に `"question"` 追加・`resolve_workflow_value` に分岐追加 |
| `scripts/claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` / `claude_loop_scout.yaml` | NOTE コメントの相互参照に `claude_loop_question.yaml` を追加（5 ファイル同期契約）|
| `.claude/rules/scripts.md` | §3 の「4 ファイル」→「5 ファイル」更新・§4 に `questions.py` 共通定数の参照を追記 |
| `.claude/skills/issue_plan/SKILL.md` | 「`QUESTIONS/` は本 SKILL の対象外」を明記（最小追記）|
| `.claude/skills/imple_plan/SKILL.md` | 「ワークフロー YAML 同期チェック」を実装品質ガイドラインに追記（付随 ISSUE 10a 消化）|
| `.claude/skills/quick_impl/SKILL.md` | 同上、quick 経路用の短縮版を追記 |
| `scripts/README.md` | ファイル一覧に `claude_loop_scout.yaml`（付随 ISSUE 10b 消化）と `claude_loop_question.yaml` を追加・`question_status.py` / `question_worklist.py` 行を追加・`questions.py` モジュール行を追加・「question（調査専用）」節を追加 |
| `scripts/USAGE.md` | 4 ファイル同期契約を 5 ファイルに更新・サンプル YAML に question を追加・`QUESTIONS/` と `ISSUES/` の境界節を追記 |
| `scripts/tests/test_workflow.py` | `QUESTION_YAML_FILENAME` import 追加・question 解決テスト・drift-guard テスト・question YAML key テスト追加・`TestYamlSyncOverrideKeys` docstring を「all shipped workflow YAMLs」に更新 |
| `scripts/tests/test_validation.py` | `test_question_yaml_passes` 追加（scout と同型）|

### 移動（ISSUE 完了）

| ファイル | 移動先 |
|---|---|
| `ISSUES/util/medium/imple-plan-four-file-yaml-sync-check.md` | `ISSUES/util/done/` |
| `ISSUES/util/low/readme-workflow-yaml-table-missing-scout.md` | `ISSUES/util/done/` |

## 変更内容の詳細

### PHASE7.1 §2: `QUESTIONS/` queue と `question_research` workflow の新設

`--workflow question` で `scripts/claude_loop_question.yaml` を起動できる新エントリポイントを追加。`auto` / `full` / `quick` / `scout` の挙動は不変（add-only）。

**Question ライフサイクル**:

1. `QUESTIONS/{cat}/{priority}/*.md` に `status: ready` / `assigned: ai` の Question を投入
2. `python scripts/claude_loop.py --workflow question --category {cat}` を起動
3. `question_research` SKILL が最上位優先度の `ready / ai` を 1 件選定
4. コードベース・docs・既存 ISSUE を調査して `docs/{cat}/questions/{slug}.md` に固定 5 セクションの報告書を出力
5. 結論確定 → `QUESTIONS/{cat}/done/` へ移動（実装課題が出た場合は `ISSUES/` に新規起票）
6. 結論未確定 → `need_human_action / human` に書き換え（`done/` 移動はしない）

**`auto` 非混入**: `question` workflow は `--workflow auto` の対象外。`QUESTIONS/` も `question_research` 専属で他 workflow からは走査されない。

### 付随 ISSUE 2 件の合流消化

- `imple-plan-four-file-yaml-sync-check.md` (medium): §2 で 5 ファイル目 YAML を追加するタイミングで `.claude/skills/imple_plan/SKILL.md` / `quick_impl/SKILL.md` に「ワークフロー YAML 同期チェック」を追記し、本バージョン中に rule / docs を 5 ファイル表記に同期。`done/` へ移動
- `readme-workflow-yaml-table-missing-scout.md` (low): `scripts/README.md` のファイル一覧テーブル編集と同タイミングで scout 行を追加。`done/` へ移動

### drift-guard テスト追加（R1 抑制策）

`test_workflow.py::TestResolveWorkflowValue::test_reserved_values_match_resolve_workflow_if_chain` を追加。`RESERVED_WORKFLOW_VALUES` の各要素について `resolve_workflow_value()` が `"auto"` または `Path` を返すことを assert する。将来 reserved 値を追加して `resolve_workflow_value` の if-chain 更新を忘れた場合、テストが失敗してドリフトを早期検知できる。

## テスト結果

`python -m unittest discover -s scripts/tests -t scripts` — **252 件すべて pass**（既存 236 + 新規 16）

- `scripts/tests/test_workflow.py`: +3 件（question 解決 / drift-guard / question YAML keys）
- `scripts/tests/test_validation.py`: +1 件（question YAML 起動前 validation）
- `scripts/tests/test_questions.py`: +5 件（新規）
- `scripts/tests/test_question_worklist.py`: +7 件（新規）

## 影響範囲

- **既存 workflow（auto / full / quick / scout）への影響**: なし。add-only 構造で `claude_loop.py` の `_run_selected()` 一般経路を共有
- **既存テスト 236 件**: 全件 pass（回帰なし）
- **`ISSUES/` queue**: 不変。`QUESTIONS/` は完全に独立した新 queue
- **dispatch smoke**: `python scripts/claude_loop.py --workflow question --dry-run` で起動パス正常動作

## 関連ドキュメント

- `docs/util/ver15.2/ROUGH_PLAN.md` — バージョン計画
- `docs/util/ver15.2/IMPLEMENT.md` — 実装計画 / 成果物一覧 / リスク表
- `docs/util/ver15.2/MEMO.md` — リスク検証結果 / 引き継ぎ
- `docs/util/MASTER_PLAN/PHASE7.1.md` — §2 一次資料（進捗表更新は `/wrap_up` / `/write_current` で実施）
- `QUESTIONS/README.md` — Question 運用ガイド
- `.claude/skills/question_research/SKILL.md` — 調査 SKILL 仕様
