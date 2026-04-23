# util MASTER_PLAN

`scripts`配下のPythonスクリプトおよび、それによって駆動される`.claude\SKILLS\meta_judge\WORKFLOW.md`のワークフローの履歴・計画を記録するドキュメントです。

- `./MASTER_PLAN/PHASE1.0.md` — **実装済み**（SKILL チェーン 5 ステップ・Python 自動化スクリプト・カテゴリ分離・サブエージェント連携）
- `./MASTER_PLAN/PHASE2.0.md` — **実装済み**（ver2.0 でログ永続化・ログパス共有・CLI オプションを実装。ver2.1 で完了通知・自動実行モード設定ファイル化を実装。ver2.2 で未コミット変更検出・`--auto-commit-before` フラグを実装し全項目完了）
- `./MASTER_PLAN/PHASE3.0.md` — **実装済み**（ver3.0 で軽量ワークフロー `quick` の導入・ワークフロー種別の拡張を実装。quick_plan / quick_impl / quick_doc の 3 SKILL と `claude_loop_quick.yaml` を追加）
- `./MASTER_PLAN/PHASE4.0.md` — **実装済み**（ver4.0 でステップごとの `--model` / `--effort` 指定を実装。top-level `defaults:` と各ステップでの上書きをサポート。ver4.1 で `scripts/README.md` 新規作成・`claude_loop.py` のモジュール分割（`claude_loop_lib/` 6モジュール）を実装。ver5.0 でセッション継続（`continue: true` / `-r` / `--session-id`）を実装し全項目完了）
- `./MASTER_PLAN/PHASE5.0.md` — **未実装**（ISSUE ステータス管理: frontmatter で `raw` / `review` / `ready` / `need_info` を管理。`/split_plan` / `/quick_plan` 冒頭で `review` を詳細化し、`ready` のみを着手対象とする）
- `./MASTER_PLAN/PHASE6.0.md` — **未実装**（`/split_plan` 前半を `/issue_plan` として分離し、`scripts/issue_worklist.py` で自分向け `ready` / `review` ISSUE を取得。`--workflow auto` をデフォルト化し、前半ステップで `quick` / `full` を自動選択）
