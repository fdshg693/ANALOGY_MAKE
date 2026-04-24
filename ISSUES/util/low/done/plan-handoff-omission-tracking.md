---
status: ready
assigned: ai
priority: low
reviewed_at: 2026-04-24
---

# PLAN_HANDOFF.md 省略の乱発追跡

## 概要

ver15.3 で導入した `PLAN_HANDOFF.md` には「handoff 情報が全てゼロの場合のみ省略可」という抜け道がある。quick workflow では冗長に感じられる可能性が PHASE7.1.md §3 リスク節で指摘されており、運用者が省略乱発すると `/split_plan` / `/quick_impl` での情報引き継ぎが形骸化する恐れがある。

## 本番発生時の兆候

- quick バージョンで `PLAN_HANDOFF.md` が常に省略されている（`ROUGH_PLAN.md` 末尾に「省略（handoff 情報なし）」宣言のみ）
- 省略宣言はあるが実際には「関連 ISSUE パス」や「後続 step への注意点」が `ROUGH_PLAN.md` 本文にも不在
- `/quick_impl` が ROUGH_PLAN.md だけでは判断が付かず retry / 誤実装が発生

## 対応方針

1. ver15.4〜15.6 の 3 バージョンほど運用し、省略頻度を RETROSPECTIVE で記録
2. quick バージョンで常に省略されるようなら、`issue_plan/SKILL.md` の省略条件を再検討（例: quick でも「関連 ISSUE パス」1 節は必須化）
3. full バージョンで省略された事例が出たら、省略判断の適切性を個別レビュー

## 影響範囲

- 後続 step の情報引き継ぎ品質
- quick workflow の実運用コスト（過度に必須化すると冗長化、緩すぎると引き継ぎ不全）

## 関連

- `docs/util/ver15.3/IMPLEMENT.md` §9 リスク表 6 行目
- `docs/util/MASTER_PLAN/PHASE7.1.md` §3 リスク節「quick タスクで冗長に見える」
- `.claude/skills/issue_plan/SKILL.md` `## PLAN_HANDOFF.md の省略条件`
