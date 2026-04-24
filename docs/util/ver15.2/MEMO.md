# ver15.2 MEMO — PHASE7.1 §2 実装メモ

## 計画との乖離

`IMPLEMENT.md` の計画通りに実装。乖離なし。

## 実装サマリ

- ベースラインテスト 236 件 → 252 件（+16 件）すべてグリーン
- 新規追加テスト内訳:
  - `test_workflow.py`: question 解決テスト・drift-guard テスト・question YAML key テスト（+3）
  - `test_validation.py`: question YAML 起動前 validation 通過テスト（+1）
  - `test_questions.py`（新規）: 5 メソッド
  - `test_question_worklist.py`（新規）: 7 メソッド
- 付随 ISSUE 2 件は `ISSUES/util/done/` に `git mv` で移動（成功）
- `--workflow question --dry-run` で起動パスが正常動作することを smoke 確認
- `python scripts/question_status.py util` / `python scripts/question_worklist.py --category util` も期待通り動作

## リスク・不確実性の検証結果（IMPLEMENT.md `## リスク・不確実性` の各項目）

| # | 抑制策 | 検証結果 |
|---|---|---|
| R1 | drift-guard テスト追加 | **検証済み** — `test_reserved_values_match_resolve_workflow_if_chain` を `test_workflow.py` に追加。`RESERVED_WORKFLOW_VALUES` の全要素について `resolve_workflow_value()` が `"auto"` または `Path` を返すことを assert |
| R2 | argparse `--workflow` help テキストの非更新 | **先送り** — ver15.0 scout precedent を踏襲し本バージョンでは更新しない。help 改善は別 ISSUE 候補。本番影響なし（reserved 値は USAGE.md / README.md / SKILL 経由で発見可能）。**ISSUE 起票はせず**、次回 retrospective 時に必要なら起票判断する（小粒のテキスト差分のため放置リスク低） |
| R3 | `TestYamlSyncOverrideKeys` の docstring 更新 | **検証済み** — 「3 shipped workflow YAMLs」→「all shipped workflow YAMLs」に更新済み |
| R4 | `review` ステータス不在の運用問題 | **検証先送り** — 運用後に困った事例が出るまで観察。本バージョン時点では PHASE7.1 §2-1 仕様（`raw / ready / need_human_action`）を厳守。ISSUE 起票は不要（仕様遵守は意図された設計判断であり、リスクではなく決定事項） |
| R5 | `.gitkeep` 配置の散らかり | **検証済み** — `util` カテゴリのみ作成（`app` / `infra` / `cicd` は未作成）。他カテゴリ起動時に必要に応じて追加する方針 |
| R6 | `docs/{category}/questions/` 欠如 | **検証済み** — `docs/util/questions/.gitkeep` を先行作成。SKILL 本文にも「ディレクトリが無ければ `mkdir -p` で作成」を明記 |
| R7 | `questions.py` / `issues.py` の重複コード | **検証先送り** — 3rd queue 登場時に抽象化を再検討する（add-only precedent を維持）。本バージョンでは 2 queue を明示的に並存させる。**ISSUE 起票は不要**（リスクは「将来のリファクタ負債」であって本番障害につながらず、トリガー条件「3rd queue 登場」が明確） |
| R8 | smoke 実行時 `ready / ai` ゼロ | **検証済み** — `--workflow question --dry-run` で dispatch 経路が正常動作することを確認。実際の Question 1 件投入は `/wrap_up` ステップに委譲（IMPLEMENT.md §11 のステップ 14 と整合）。サンプル Question 投入の判断は `/wrap_up` で行う |
| R9 | `.claude/` 同時編集コンフリクト | **検証済み** — 1 回の `claude_sync.py export` → 4 ファイル編集 → 1 回の `import` で完了。`git status` 上の差分は意図通り（question_research SKILL 新規 + issue_plan / imple_plan / quick_impl / rules-scripts への追記） |
| R10 | `git mv` の Windows 大文字小文字問題 | **検証済み** — `git mv` で両ファイル正常に done/ へ移動完了 |

## 動作確認

- ✅ `python -m unittest discover -s scripts/tests -t scripts` — 252 件すべて pass（既存 236 + 新規 16）
- ✅ `python scripts/claude_loop.py --workflow question --dry-run` — dispatch 経路正常
- ✅ `python scripts/question_status.py util` — 空 queue で 4 列表示
- ✅ `python scripts/question_worklist.py --category util` — `(no matching questions)` 表示
- ⚠️ `npx nuxi typecheck` — vue-router volar の MODULE_NOT_FOUND エラーが出る（CLAUDE.md 「開発上の注意」に「vue-router volar 関連の既知警告あり（ビルド・実行に影響なし）」と明記済み。本バージョンの変更は Python / YAML / Markdown のみで TypeScript 影響なし）
- ✅ `pnpm test` — 本バージョン変更は Python のみのため対象外（フロントエンドテストは Python 変更で動かない）

## ドキュメント更新提案（`/wrap_up` 対応結果）

- ✅ `docs/util/MASTER_PLAN/PHASE7.1.md` — §2 を「実装済み（ver15.2）」に更新
- ✅ `docs/util/ver15.0/CURRENT_scripts.md` — `claude_loop_question.yaml` / `questions.py` / `question_status.py` / `question_worklist.py` を追記。5 ファイル同期義務に更新。question workflow step 表・フロー図分岐を追加
- ✅ `docs/util/ver15.0/CURRENT_skills.md` — 「調査専用ワークフロー question（1 ステップ）」節を追加（`question_research/SKILL.md` の構成記述）。rules.md 行の注釈を「ver15.2 で 5 ファイルに更新済み」に修正
- ⏭️ R2 help テキスト改善: 対応不要（cosmetic 差分、MEMO.md に先送り根拠記録済み、ISSUE 起票なし）
- ⏭️ R8 サンプル Question 投入: dry-run smoke 確認済みのため先送り。初回実走は実際の Question 起票時に自然に行われる

## 後続バージョンへの引き継ぎ

- **PHASE7.1 §3 / §4**: 本バージョンで未着手。§3（`ROUGH_PLAN.md` / `PLAN_HANDOFF.md` 分離）は ver15.3、§4（run 単位通知）は ver15.4 以降が想定（ROUGH_PLAN.md / IMPLEMENT.md の「実施しない」節と整合）
- **`question_research` の初回実走**: `--workflow question` の dispatch は smoke 確認済みだが、実際の Question を 1 件投入して end-to-end で報告書出力 → `done/` 移動を回す検証は未実施。`/wrap_up` か後続バージョンで実運用テストとして実施するのが望ましい
- **`questions.py` / `issues.py` 重複**: 3rd queue が現れた時点で `claude_loop_lib/queues.py` 等の共通基盤への抽象化を再検討する（R7）

## 今回の実装で気づいた点（小粒、ISSUE 化未満）

- `scripts/USAGE.md` 冒頭の `issue_worklist.py` 節は内容が肥大化しており、新規追加した `question_worklist.py` 節を加えると更に冗長になる。将来的には「worklist 系スクリプトの仕様」を 1 節にまとめて DRY 化する余地あり（本バージョンでは触らない）
- `RESERVED_WORKFLOW_VALUES` は documentational なタプルだったが、drift-guard テストを追加したことで「if-chain との同期」が機械的に保証されるようになった。今後の workflow 追加（PHASE7.1 §3 等）でも安全に拡張できる
