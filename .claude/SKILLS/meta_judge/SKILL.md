---
name: meta_judge
disable-model-invocation: true
user-invocable: true
---

# Claude Code の使い方が有効かどうかを判定してください

以下の項目について、上手な構成・プロンプトになっているか確認して、改善点を提案してください。
必要に応じて、以下のようなClaude Codeの機能が利用できないか検討してみてください。
- SKILL
- Instructions
- MCP
- CLAUDE.md
- Hooks
- Subagents

## 1. 実装ワークフロー

`.claude\SKILLS` 配下のSKILLを使って順番に実装している
現在までに出来ているバージョンを見て、出来を評価して（たくさんのバージョンがある場合は、最新のバージョンを中心に見ればよい。昔のバージョンは現在と異なるフローで実装されている可能性があるため）

1. `/split_plan` — マスタープラン or ISSUESから、今回取り組むべきタスクの抽出・計画
2. `/imple_plan` — 計画に基づく実装
3. `/wrap_up` — MEMOに基づく細かい改善・整理
4. `/write_current` — ドキュメントの更新
5. `/retrospective` — 振り返りと次バージョンへの改善点整理
