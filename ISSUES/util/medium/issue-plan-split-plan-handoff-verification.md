---
status: ready
assigned: ai
priority: medium
reviewed_at: "2026-04-23"
---
# `/issue_plan` → `/split_plan` の新規セッション運用での情報引き継ぎ検証

## 概要

ver8.0 で `/issue_plan` → `/split_plan` 間を新規セッション（`continue: false` 相当）で運用する方針に切り替えた。`/split_plan` が ROUGH_PLAN.md だけから IMPLEMENT.md を起こせるかは、実運用でのみ検証可能。

## 本番発生時の兆候

- `/split_plan` ステップで「ROUGH_PLAN.md の記述だけでは対象ファイルや背景が不明」といった `REQUESTS/AI/` の追記
- IMPLEMENT.md の内容が ROUGH_PLAN.md から大きく逸脱（前段の判断経緯を失って別方針に走る）
- plan_review_agent の指摘で「ROUGH_PLAN との不整合」が繰り返し挙がる

## 対応方針

1. 実ワークフロー数回（ver8.1 / ver8.2 あたり）で `/split_plan` の IMPLEMENT.md 起こしを観察
2. 不足が顕在化した場合の対処候補:
   - `/issue_plan` の ROUGH_PLAN.md テンプレートに「判断経緯」「関連ファイル一覧」セクションを必須化する
   - `/split_plan` 側で `continue: true` に切り替え、`/issue_plan` のセッション文脈を引き継ぐ
3. 検証完了後に本 ISSUE を `done/` へ移動

## 影響範囲

- `scripts/claude_loop.yaml` の `split_plan` ステップ定義（`continue` フラグ）
- `.claude/skills/issue_plan/SKILL.md` の ROUGH_PLAN.md 作成ガイド
- `.claude/skills/split_plan/SKILL.md` の「ステップ1」冒頭

## 出典

`docs/util/ver8.0/IMPLEMENT.md` §9 R2（検証先送り）

## ver9.0 実走での観察結果（半検証済）

ver9.0 ワークフローで以下を確認した:

- `/issue_plan` が作成した ROUGH_PLAN.md（190 行）には、関連ファイル一覧・判断経緯（選定理由・除外理由）・前提リスク引用・事前リファクタリング判断がすべて格納されていた
- 後続 `/split_plan` はこの ROUGH_PLAN.md 単体から IMPLEMENT.md（564 行）を生成可能で、他ファイル参照は最小限で済んだ

ただしこの観察は `claude_loop.yaml` を 1 プロセスで通した際のものであり、`continue: true` のセッション継続効果と重畳している可能性がある。**完全に独立した新規セッション**（`--max-step-runs 1` で停止 → 別プロセスで `--start 2` 再起動）での検証は未実施。ver9.1 以降で自然発生する停止・再開サイクルを利用して追検証する。

詳細は `docs/util/ver9.0/RETROSPECTIVE.md` §2-2 参照。
