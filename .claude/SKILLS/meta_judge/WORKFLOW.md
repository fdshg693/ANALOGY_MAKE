# ワークフロー詳細

## 1. 実装ワークフロー

`.claude\SKILLS` 配下のSKILLを使って順番に実装している
現在までに出来ているバージョンを見て、出来を評価して（たくさんのバージョンがある場合は、最新のバージョンを中心に見ればよい。昔のバージョンは現在と異なるフローで実装されている可能性があるため）

1. `/split_plan` — マスタープラン or ISSUESから、今回取り組むべきタスクの抽出・計画
2. `/imple_plan` — 計画に基づく実装
3. `/wrap_up` — MEMOに基づく細かい改善・整理
4. `/write_current` — ドキュメントの更新
5. `/retrospective` — 振り返りと次バージョンへの改善点整理

## 2. 軽量ワークフロー（quick）

小規模タスク向けの 3 ステップワークフロー。`claude_loop_quick.yaml` で定義。

1. `/quick_plan` — ISSUE 選定 + 簡潔な計画（ROUGH_PLAN.md のみ）
2. `/quick_impl` — 実装 + MEMO対応 + typecheck + コミット
3. `/quick_doc` — CHANGES.md 作成 + CLAUDE.md 更新確認 + ISSUES 整理 + コミット

### ワークフロー選択ガイドライン

| 条件 | 推奨 |
|---|---|
| MASTER_PLAN の新項目着手 | full |
| アーキテクチャ変更・新規ライブラリ導入 | full |
| 変更ファイル 4 つ以上 | full |
| ISSUES/high の対応（複雑） | full |
| ISSUES の 1 件対応（単純） | quick |
| バグ修正（原因特定済み） | quick |
| 既存機能の微調整 | quick |
| ドキュメント・テスト追加 | quick |
| 変更ファイル 3 つ以下 | quick |
