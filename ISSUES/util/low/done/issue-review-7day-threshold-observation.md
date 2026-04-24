---
status: ready
assigned: ai
reviewed_at: "2026-04-25"
---

# issue-review-7day-threshold-observation

## 概要

ver16.5 で `issue_review` SKILL に導入した「`reviewed_at` が 7 日以上前の `ready/ai` ISSUE を再判定推奨として検出する」ルートの閾値（7 日）妥当性を観察する。

## 背景

- 実装日（2026-04-25）時点で util カテゴリ ready/ai 4 件すべてが 7 日以内（最古 2026-04-23）のため、初回発火未確認
- 7 日閾値は ver14〜ver16 の version bump 実績（1 minor ≒ 1〜2 日）から「5 バージョン ≒ 5〜10 日 → 中央値 7 日」と算出
- IMPLEMENT.md §F-1 に「後続 2 版（ver16.6, ver16.7）で経過観察」と明記

## 検証内容

後続版の `/issue_plan` → ROUGH_PLAN.md で以下を確認する:

1. 「## 再判定推奨 ISSUE」ブロックに **該当なし** が出続ける場合 → 閾値が過鈍（長すぎる）可能性。5 日への引き下げを検討
2. 「## 再判定推奨 ISSUE」に頻繁に ISSUE が列挙される場合 → 閾値が過敏（短すぎる）可能性。10〜14 日への引き上げを検討
3. 初回発火（7 日以上経過 ISSUE が列挙される）が確認できた場合 → 動作確認完了。本 ISSUE を `done/` へ移動

## 完了条件

- 初回発火が確認されれば `done/` へ移動
- 2 版（ver16.7 相当）経過後も未発火 → 閾値調整の後続 ISSUE を起票

## 完了記録（ver16.8）

ver16.6 / ver16.7 / ver16.8（3 版）を経て §1.5 が一度も発火しなかった（ready/ai ISSUE の `reviewed_at` が 7 日に到達せず）。完了条件「2 版経過後も未発火 → 後続 ISSUE 起票」に到達。`issue-review-7day-threshold-adjustment.md` を新規起票した上で本 ISSUE を `done/` へ移動。
