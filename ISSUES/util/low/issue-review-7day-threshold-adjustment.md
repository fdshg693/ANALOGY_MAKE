---
status: raw
assigned: ai
priority: low
reviewed_at: "2026-04-25"
---

# issue-review-7day-threshold-adjustment

## 概要

`issue_review` SKILL §1.5 の ready/ai 長期持ち越し検出閾値（現行 7 日）が過鈍の可能性があるため、5 日への短縮を検討する。

## 背景

- ver16.5 で §1.5 を導入。算出根拠は「1 minor ≒ 1〜2 日 → 5 版 ≒ 5〜10 日 → 中央値 7 日」
- ver16.6 / ver16.7 / ver16.8 の 3 版連続で §1.5 が未発火（ready/ai ISSUE が 7 日に達しなかった）
- 観察 ISSUE `issue-review-7day-threshold-observation` の完了条件「2 版経過後も未発火 → 閾値調整の後続 ISSUE 起票」に到達したため本 ISSUE を起票

## 未発火の原因分析

- ver16.6〜ver16.8 を通じて ready/ai ISSUE の `reviewed_at` 最古は 2 日（`issue-review-rewrite-verification`）。7 日閾値には到達しなかった
- ready/ai ISSUE が `review/ai` → `ready/ai` に昇格してからの経過日数が短い（バージョンアップが相対的に速かった可能性）
- 一方で `deferred-resume-twice-verification` / `issue-review-rewrite-verification` が medium でありながら外部待ちにより 3〜4 版据え置き中。7 日閾値さえ下げれば発火したはず

## 対応方針

1. `issue_review/SKILL.md` §1.5 の閾値を `7 日` → `5 日` に変更
2. 変更後、次版以降の `/issue_plan` → ROUGH_PLAN.md で §1.5 発火の有無を確認
3. 5 日でも未発火が 2 版以上続く場合は閾値ロジック自体（日数ベース vs 版数ベース）の再考を別 ISSUE で検討

## 影響範囲

- `.claude/skills/issue_review/SKILL.md` §1.5 の閾値記述（1 箇所）のみ
- `.claude/skills/issue_plan/SKILL.md` の同期更新（§1.5 閾値を参照している記述があれば）

## 完了条件

- §1.5 閾値を 5 日に変更し、次版以降で発火観察が開始される
- または観察の結果「5 日でも過鈍」と判断し、さらなる引き下げ or ロジック変更を別 ISSUE で起票

## 参照

- `docs/util/ver16.5/IMPLEMENT.md` §F-1 — 閾値算出根拠
- `docs/util/ver16.7/PLAN_HANDOFF.md` §1.5 予測 vs 実績の整合性記録 — F-1 閾値調整 ISSUE 起票の期限到達の明記
- `ISSUES/util/low/done/issue-review-7day-threshold-observation.md` — 完了した観察 ISSUE
