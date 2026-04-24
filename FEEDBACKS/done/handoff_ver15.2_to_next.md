---
step: issue_plan
---

## 背景

ver15.2 で PHASE7.1 §2（`QUESTIONS/` queue + `question_research` workflow）を add-only で完了。PHASE7.1 は §1 / §2 実装済・§3 / §4 未着手。util カテゴリの `ready / ai` ISSUE は `issue-review-rewrite-verification.md` 1 件のみで、これは `app` / `infra` カテゴリ起動時でないと消化できない（ver6.0 以来の持ち越し）。

## 次ループで試すこと

- **次バージョンは ver15.3（マイナー）、PHASE7.1 §3（`ROUGH_PLAN.md` / `PLAN_HANDOFF.md` の役割分離）に着手する想定で `/issue_plan` を回す**。
- §3 は既存 SKILL 3 本（`.claude/skills/issue_plan/SKILL.md` / `split_plan/SKILL.md` / `quick_impl/SKILL.md`）と `.claude/plans/VERSION_FLOW.md` の改訂を伴う破壊性中〜高の変更。ROUGH_PLAN.md 段階で以下を明示すること:
  - 既存 `ROUGH_PLAN.md` 記述のうち「スコープ定義」に残すもの / 新設 `PLAN_HANDOFF.md` に逃がすもの の仕分け方針
  - 既存 SKILL 本文で `ROUGH_PLAN.md` を主入力として読んでいる箇所の棚卸し（影響範囲の先出し）
  - ver15.0 / ver15.1 / ver15.2 の ROUGH_PLAN.md フォーマット変更をどこまで遡って一貫化するか（過去 docs は触らない方針で揃えるのが add-only 原則と整合）
- §2 で追加した `RESERVED_WORKFLOW_VALUES` drift-guard テストの設計は §3 で新 workflow が増えた場合もそのまま活きる（安心材料）。

## 保留事項

- **`issue-review-rewrite-verification.md`**: 引き続き util 単体消化不能のため持ち越し。`app` / `infra` 起動時に消化判断する（ver15.3 ROUGH_PLAN でも同じ理由で除外して問題ない）。
- **ver14.0 観察持越し 2 件**（`rules-paths-frontmatter-autoload-verification.md` / `scripts-readme-usage-boundary-clarification.md`）: 運用中に問題が顕在化するまで観察継続。ver15.3 スコープには入れない。
- **PHASE7.1 §4（run 単位通知）**: §3 と同時着手しない。ver15.4 以降で単独扱い。
- **`questions.py` / `issues.py` 重複**: 3rd queue が登場するまで共通基盤化は先送り（R7 トリガー条件、ver15.3 スコープ外）。
- **workflow YAML model / effort 調整**: ver15.2 時点で実行した各 step の品質は良好。「次 1 ループで試す具体的調整」には該当せず、本 handoff では触らない。
