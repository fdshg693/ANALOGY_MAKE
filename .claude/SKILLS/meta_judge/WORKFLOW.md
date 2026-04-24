# ワークフロー詳細

## 1. 実装ワークフロー

`.claude\SKILLS` 配下のSKILLを使って順番に実装している
現在までに出来ているバージョンを見て、出来を評価して（たくさんのバージョンがある場合は、最新のバージョンを中心に見ればよい。昔のバージョンは現在と異なるフローで実装されている可能性があるため）

1. `/issue_plan` — 現状把握 + ISSUE レビュー + ISSUE/MASTER_PLAN 選定 + ROUGH_PLAN.md と PLAN_HANDOFF.md 作成 + workflow 判定
2. `/split_plan` — ROUGH_PLAN.md と PLAN_HANDOFF.md を起点に REFACTOR.md / IMPLEMENT.md 作成 + plan_review_agent で review
3. `/imple_plan` — 計画に基づく実装
4. `/wrap_up` — MEMOに基づく細かい改善・整理
5. `/write_current` — ドキュメントの更新
6. `/retrospective` — 振り返りと次バージョンへの改善点整理

## 2. 軽量ワークフロー（quick）

小規模タスク向けの 3 ステップワークフロー。`claude_loop_quick.yaml` で定義。

1. `/issue_plan` — 現状把握 + ISSUE レビュー + ISSUE 選定 + ROUGH_PLAN.md と（必要なら）PLAN_HANDOFF.md 作成（workflow=quick で frontmatter を付ける）
2. `/quick_impl` — 実装 + MEMO対応 + typecheck + コミット
3. `/quick_doc` — CHANGES.md 作成 + CLAUDE.md 更新確認 + ISSUES 整理 + コミット

## 3. 調査・実験ワークフロー（research）

`claude_loop_research.yaml` で定義する 8 step ワークフロー。実装前に調査・実験を正式 step として挟む。

1. `/issue_plan` — 現状把握 + ISSUE レビュー + ISSUE / MASTER_PLAN 選定 + ROUGH_PLAN.md 作成（`workflow: research` frontmatter）
2. `/split_plan` — REFACTOR.md / IMPLEMENT.md 作成 + plan_review_agent で review
3. `/research_context` — 外部調査（公式 docs・類似事例）結果を `RESEARCH.md` に出力
4. `/experiment_test` — `experiments/` 配下で仮説検証し `EXPERIMENT.md` に出力
5. `/imple_plan` — `RESEARCH.md` / `EXPERIMENT.md` の確定事項を反映した実装
6. `/wrap_up` — MEMO対応・細かい改善
7. `/write_current` — ドキュメント更新
8. `/retrospective` — 振り返り

### 選択条件（いずれか 1 つを満たす）

- 外部仕様・公式 docs の確認が主要成果に影響する
- 実装方式を実験で絞り込む必要がある
- 1 step で 5 分以上を要する実測系の長時間検証が事前に必要
- 軽い隔離環境（`experiments/` 配下）での試行が前提

### `question` workflow との違い

| 観点 | `question` (`QUESTIONS/`) | `research` (`docs/{cat}/ver{X.Y}/RESEARCH.md`) |
|---|---|---|
| (a) 最終成果物 | 報告書のみ（`docs/{cat}/questions/{slug}.md`） | **コード変更**（`RESEARCH.md` は中間成果物） |
| (b) 入力キュー | `QUESTIONS/{cat}/{priority}/` | `ISSUES/{cat}/{priority}/` または MASTER_PLAN |
| (c) workflow | 調査→報告書で終了（実装に進まない） | 調査→実験→実装→retrospective まで 8 step 完走 |

### ワークフロー選択ガイドライン

| 条件 | 推奨 |
|---|---|
| MASTER_PLAN の新項目着手（調査・実験が必要な場合） | research |
| MASTER_PLAN の新項目着手（調査不要な場合） | full |
| アーキテクチャ変更・新規ライブラリ導入（外部仕様確認が主要成果に影響） | research |
| アーキテクチャ変更・新規ライブラリ導入（上記以外） | full |
| 変更ファイル 4 つ以上（※） | full |
| ISSUES/high の対応（複雑） | full |
| ISSUES の 1 件対応（単純） | quick |
| バグ修正（原因特定済み） | quick |
| 既存機能の微調整 | quick |
| ドキュメント・テスト追加 | quick |
| 変更ファイル 3 つ以下 | quick |

※ ただし、全ファイルがテキスト編集のみ（SKILL 文言修正・ドキュメント更新等）で、各ファイルの変更が数行程度の場合は quick を推奨

### モデル・エフォートの指定

`claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_research.yaml` には各ステップのモデル（`model`）と推論エフォート（`effort`）を指定できる。トップレベルの `defaults:` で全ステップ共通値を定義し、各ステップで必要に応じて上書きする。省略時は CLI デフォルトが使用される（従来挙動）。

なお、`/retrospective` が書き出した `FEEDBACKS/handoff_ver*_to_next.md` は次ループの `/issue_plan` で 1 回だけ消費され、prompt / model 調整の具体案を次ループに引き継ぐ経路として機能する（詳細は `.claude/skills/retrospective/SKILL.md` §3.5 / §4.5）。

### 保守上の注意

- `claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_research.yaml` / `claude_loop_issue_plan.yaml` / `claude_loop_scout.yaml` / `claude_loop_question.yaml` の `command` / `defaults` セクションは同一内容で維持する（いずれかを変更した場合は必ず 6 ファイル全てを同期すること）
- 3 ワークフローの 1 ステップ目は `/issue_plan` で共通。ROUGH_PLAN.md 冒頭の `workflow: full | quick | research` / `source: issues | master_plan` で後続分岐の材料が残る。`workflow:` / `source:` の one source of truth は `ROUGH_PLAN.md` 側に保ち、`PLAN_HANDOFF.md` 側は同値を冗長保持する
- `--workflow auto`（新デフォルト）は `claude_loop_issue_plan.yaml` で `/issue_plan` を先行実行し、出力された最新 `ROUGH_PLAN.md` の frontmatter `workflow:` に応じて `claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_research.yaml` の `steps[1:]` を実行する。`workflow:` 未記載・不正値時は `full` にフォールバックして警告を出す
