# util MASTER_PLAN

**ワークフロー概要: `.claude\SKILLS\meta_judge\WORKFLOW.md`**
**ワークフロー自動化スクリプト: `scripts\README.md`参照**

`scripts`配下のPythonスクリプトおよび、それによって駆動される`.claude\SKILLS\meta_judge\WORKFLOW.md`のワークフローの履歴・計画を記録するドキュメントです。

- `./MASTER_PLAN/PHASE1.0.md` — **実装済み**（SKILL チェーン 5 ステップ・Python 自動化スクリプト・カテゴリ分離・サブエージェント連携）
- `./MASTER_PLAN/PHASE2.0.md` — **実装済み**（ver2.0 でログ永続化・ログパス共有・CLI オプションを実装。ver2.1 で完了通知・自動実行モード設定ファイル化を実装。ver2.2 で未コミット変更検出・`--auto-commit-before` フラグを実装し全項目完了）
- `./MASTER_PLAN/PHASE3.0.md` — **実装済み**（ver3.0 で軽量ワークフロー `quick` の導入・ワークフロー種別の拡張を実装。quick_plan / quick_impl / quick_doc の 3 SKILL と `claude_loop_quick.yaml` を追加）
- `./MASTER_PLAN/PHASE4.0.md` — **実装済み**（ver4.0 でステップごとの `--model` / `--effort` 指定を実装。top-level `defaults:` と各ステップでの上書きをサポート。ver4.1 で `scripts/README.md` 新規作成・`claude_loop.py` のモジュール分割（`claude_loop_lib/` 6モジュール）を実装。ver5.0 でセッション継続（`continue: true` / `-r` / `--session-id`）を実装し全項目完了）
- `./MASTER_PLAN/PHASE5.0.md` — **実装済み**（ver6.0 で ISSUE ステータス管理を実装。frontmatter で `raw` / `review` / `ready` / `need_human_action` / `assigned` を管理。`issue_review` SKILL を新設し `/split_plan` / `/quick_plan` 冒頭にインライン展開。`ready / ai` のみを着手対象とする選定ロジックに変更。`scripts/issue_status.py` で分布表示。`ISSUES/README.md` でフロントマター仕様を文書化）
- `./MASTER_PLAN/PHASE6.0.md` — **実装済み**（ver7.0 で §1 `issue_worklist.py` 新設・`claude_loop_lib/issues.py` 共通化 と §4 `/retrospective` での活用手順追記を実装。ver8.0 で §2 `/issue_plan` SKILL 新設・`/split_plan` 責務縮小・`/quick_plan` 削除を実装。ver9.0 で §3 `--workflow auto` を導入し全項目完了。詳細は `MASTER_PLAN/PHASE6.0.md` 参照）
- `./MASTER_PLAN/PHASE7.0.md` — **一部実装済み**（ver10.0 で §1 条件①②充足、ver12.0 で §1 条件③および §2 完了。ver13.0 で §3〜§5 完了。§6〜§8 は未着手。詳細は `MASTER_PLAN/PHASE7.0.md` 参照）
