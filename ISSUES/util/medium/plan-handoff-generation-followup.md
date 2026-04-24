---
status: ready
assigned: ai
priority: medium
reviewed_at: 2026-04-24
---

# PLAN_HANDOFF.md 生成追跡（ver15.3 先送りリスク）

## 概要

ver15.3（PHASE7.1 §3）で新設した `PLAN_HANDOFF.md` が、次回以降の `/issue_plan` で実際に生成されるかを実地確認する必要がある。SKILL 改訂直後は「新ルールを読み落として忘れる」リスクが最も高い。

## 本番発生時の兆候

- ver15.4 以降の `docs/{category}/ver{X.Y}/` に `PLAN_HANDOFF.md` が欠落
- `ROUGH_PLAN.md` 末尾に「PLAN_HANDOFF.md 省略（handoff 情報なし）」の正当省略宣言もない
- `/split_plan` / `/quick_impl` で `PLAN_HANDOFF.md` が存在しないまま後続 step が進行

## 対応方針

1. ver15.4 以降の最初の `/issue_plan` 実行結果を観察
2. 生成されていれば本 ISSUE を `done/` へ移動
3. 生成されず、かつ省略宣言もなければ `.claude/skills/issue_plan/SKILL.md` の指示文を強化（例: コミット節で `PLAN_HANDOFF.md` 存在を必須化）
4. 運用を 2〜3 バージョン観察した上で、`validation.py` に静的チェック追加を検討（別 ISSUE で追跡）

## 影響範囲

- 後続 `/split_plan` / `/quick_impl` の情報引き継ぎ（handoff なしでも動くが、判断材料が欠落する）
- RETROSPECTIVE で仕分け方針の妥当性検証が困難になる

## 関連

- `docs/util/ver15.3/IMPLEMENT.md` §9 リスク表 1 行目
- `docs/util/ver15.3/MEMO.md` リスク検証結果
- `.claude/skills/issue_plan/SKILL.md`（改訂箇所）
