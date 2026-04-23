# ワークフロー詳細

## 1. 実装ワークフロー

`.claude\SKILLS` 配下のSKILLを使って順番に実装している
現在までに出来ているバージョンを見て、出来を評価して（たくさんのバージョンがある場合は、最新のバージョンを中心に見ればよい。昔のバージョンは現在と異なるフローで実装されている可能性があるため）

1. `/issue_plan` — 現状把握 + ISSUE レビュー + ISSUE/MASTER_PLAN 選定 + ROUGH_PLAN.md 作成 + workflow 判定
2. `/split_plan` — ROUGH_PLAN.md を起点に REFACTOR.md / IMPLEMENT.md 作成 + plan_review_agent で review
3. `/imple_plan` — 計画に基づく実装
4. `/wrap_up` — MEMOに基づく細かい改善・整理
5. `/write_current` — ドキュメントの更新
6. `/retrospective` — 振り返りと次バージョンへの改善点整理

## 2. 軽量ワークフロー（quick）

小規模タスク向けの 3 ステップワークフロー。`claude_loop_quick.yaml` で定義。

1. `/issue_plan` — 現状把握 + ISSUE レビュー + ISSUE 選定 + ROUGH_PLAN.md 作成（workflow=quick で frontmatter を付ける）
2. `/quick_impl` — 実装 + MEMO対応 + typecheck + コミット
3. `/quick_doc` — CHANGES.md 作成 + CLAUDE.md 更新確認 + ISSUES 整理 + コミット

### ワークフロー選択ガイドライン

| 条件 | 推奨 |
|---|---|
| MASTER_PLAN の新項目着手 | full |
| アーキテクチャ変更・新規ライブラリ導入 | full |
| 変更ファイル 4 つ以上（※） | full |
| ISSUES/high の対応（複雑） | full |
| ISSUES の 1 件対応（単純） | quick |
| バグ修正（原因特定済み） | quick |
| 既存機能の微調整 | quick |
| ドキュメント・テスト追加 | quick |
| 変更ファイル 3 つ以下 | quick |

※ ただし、全ファイルがテキスト編集のみ（SKILL 文言修正・ドキュメント更新等）で、各ファイルの変更が数行程度の場合は quick を推奨

### モデル・エフォートの指定

`claude_loop.yaml` / `claude_loop_quick.yaml` には各ステップのモデル（`model`）と推論エフォート（`effort`）を指定できる。トップレベルの `defaults:` で全ステップ共通値を定義し、各ステップで必要に応じて上書きする。省略時は CLI デフォルトが使用される（従来挙動）。

### 保守上の注意

- `claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` の `command` / `mode` / `defaults` セクションは同一内容で維持する（いずれかを変更した場合は必ず 3 ファイル全てを同期すること）
- 両ワークフローの 1 ステップ目は `/issue_plan` で共通。ROUGH_PLAN.md 冒頭の `workflow: full | quick` / `source: issues | master_plan` で後続分岐の材料が残る（`--workflow auto` 分岐ロジックは ver9.0 で実装済み）
- `--workflow auto`（新デフォルト）は `claude_loop_issue_plan.yaml` で `/issue_plan` を先行実行し、出力された最新 `ROUGH_PLAN.md` の frontmatter `workflow:` に応じて `claude_loop.yaml` / `claude_loop_quick.yaml` の `steps[1:]` を実行する。`workflow:` 未記載・不正値時は `full` にフォールバックして警告を出す
