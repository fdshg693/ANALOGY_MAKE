---
status: ready
assigned: ai
reviewed_at: "2026-04-25"
---

# issue-review-llm-date-calc-observation

## 概要

ver16.5 で `issue_review` SKILL §1.5 / §5 に追加した「`reviewed_at` と本日日付の差分計算（7 日以上で再判定推奨）」を LLM が確実に実行できるか、次版 `/issue_plan` の出力で確認する。

## 背景

- SKILL.md の自然言語指示だけで LLM に日付差分を計算させる方式を採用（scripts/ 側のロジック追加なし）
- コンテキストに「今日の日付: !`date +%Y-%m-%d`」相当の絶対日付が既に存在（SKILL.md L17）するため確定的に判定できると想定
- IMPLEMENT.md §F-3 に「次版 `/issue_plan` の ROUGH_PLAN.md で書式を目視確認」と明記

## 検証内容

次版（ver16.6 相当）の `/issue_plan` 実行後に ROUGH_PLAN.md を確認:

1. 「## 再判定推奨 ISSUE」見出しが **存在する** か（ブロック自体が省略されていないか）
2. 書式が SKILL.md §5 のテンプレートと一致しているか（該当なし の場合も見出し＋ 1 行が出力されているか）
3. 7 日以上経過 ISSUE がある場合、正しくパスと日付差が列挙されているか

## 完了条件

- 正しい書式で出力が確認できれば `done/` へ移動
- 書式崩れ / 見出し欠落の場合 → SKILL.md §1.5 / §5 に計算例を inline で追記する後続 ISSUE を起票
