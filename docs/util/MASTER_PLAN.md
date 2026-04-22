# util MASTER_PLAN

`scripts`配下のPythonスクリプトおよび、それによって駆動される`.claude\SKILLS\meta_judge\WORKFLOW.md`のワークフローの履歴・計画を記録するドキュメントです。

- `./MASTER_PLAN/PHASE1.0.md` — **実装済み**（SKILL チェーン 5 ステップ・Python 自動化スクリプト・カテゴリ分離・サブエージェント連携）
- `./MASTER_PLAN/PHASE2.0.md` — **実装済み**（ver2.0 でログ永続化・ログパス共有・CLI オプションを実装。ver2.1 で完了通知・自動実行モード設定ファイル化を実装。ver2.2 で未コミット変更検出・`--auto-commit-before` フラグを実装し全項目完了）
- `./MASTER_PLAN/PHASE3.0.md` — **実装済み**（ver3.0 で軽量ワークフロー `quick` の導入・ワークフロー種別の拡張を実装。quick_plan / quick_impl / quick_doc の 3 SKILL と `claude_loop_quick.yaml` を追加）
- `./MASTER_PLAN/PHASE4.0.md` — **未実装**（ワークフロー柔軟化: ステップごとの `--model` / `--effort` 指定とセッション継続 `-r` を YAML で制御。top-level `defaults:` で共通値を定義し、各ステップで上書き）
- `./MASTER_PLAN/PHASE5.0.md` — **未実装**（ISSUE ステータス管理: frontmatter で `raw` / `review` / `ready` / `need_info` を管理。`/split_plan` / `/quick_plan` 冒頭で `review` を詳細化し、`ready` のみを着手対象とする）
