---
workflow: full
source: issues
---

# ver16.5 CHANGES — `issue_review` SKILL に `ready/ai` 長期持ち越し再判定ルートを追加

ver16.4 からの変更差分を記録する。コードベース（Python / TypeScript）への変更はなく、SKILL 仕様書 2 本と ISSUES 関連ファイルのみを対象とした仕様書変更。

## 変更ファイル一覧

| 操作 | ファイル | 概要 |
|---|---|---|
| M | `.claude/SKILLS/issue_review/SKILL.md` | 長期持ち越し再判定ルート追加（§1.5 / §3 / §5 / description） |
| M | `.claude/SKILLS/issue_plan/SKILL.md` | ISSUE レビューフェーズ記述を (a)/(b) 2 系統に再構成 |
| M | `ISSUES/README.md` | §ライフサイクル節に「長期持ち越し再判定」サブセクション追加 |
| R | `ISSUES/util/low/issue-review-long-carryover-redemotion.md` → `done/` | 消化 ISSUE の done/ 移動 |
| A | `ISSUES/util/low/issue-review-7day-threshold-observation.md` | wrap_up: 閾値妥当性観察 ISSUE 起票 |
| A | `ISSUES/util/low/issue-review-llm-date-calc-observation.md` | wrap_up: LLM 日付計算確認 ISSUE 起票 |
| R | `FEEDBACKS/handoff_ver16.3_to_next.md` → `FEEDBACKS/done/` | FEEDBACK 消費済み（done/ 移動） |

## 変更内容の詳細

### `.claude/SKILLS/issue_review/SKILL.md` — 長期持ち越し再判定ルート追加

4 箇所を追補:

**A-1. description 更新**  
`ready/ai 長期持ち越し ISSUE を再判定推奨として一覧する` を末尾に付加し、SKILL の責務をより正確に表現。

**A-2. §1.5「長期持ち越し ready/ai の検出」追加**  
§1 スキャン末尾に新節を挿入。`status: ready` かつ `assigned: ai` のファイルを並行走査し、`reviewed_at` が本日から 7 日以上前のものを「再判定推奨」として検出する。`reviewed_at` 欠落 ISSUE は false positive 防止のため対象外。frontmatter 書き換えなし（サマリ報告への列挙のみ）。

**A-3. §3 書き換えガードへの第 6 項目追加**  
「長期持ち越し ISSUE の frontmatter は書き換えない」を明示し、§1.5 の検出行為と frontmatter 変更が区別できるように整理。

**A-4. §5「再判定推奨 ISSUE」第 3 ブロック追加**  
既存 2 ブロック（`## ISSUE レビュー結果` / `## ISSUE 状態サマリ`）の後に、`## 再判定推奨 ISSUE` ブロック書式を追加。該当あり・該当なしの 2 テンプレートを例示。候補理由 A（実機検証要 → 降格検討）/ B（前提待ち → 維持検討）をテンプレート固定文として常備する（判別自動化はしない）。

### `.claude/SKILLS/issue_plan/SKILL.md` — ISSUE レビューフェーズ記述同期

「準備」節の ISSUE レビューフェーズ説明文を (a)/(b) 2 系統で再構成:
- (a) 従来の `review/ai` 走査・振り分け・frontmatter 書き換え
- (b) `ready/ai` 長期持ち越し検出（frontmatter 書き換えなし）

ROUGH_PLAN.md への出力ブロックも 2 本 → 3 本（第 3 ブロック `## 再判定推奨 ISSUE` を追加）に拡張。呼び出し元との同期原則に従い `issue_review` SKILL の変更と整合。

### `ISSUES/README.md` — 長期持ち越し再判定フロー追記

§ライフサイクル節末尾（`issue_scout` サブセクションの直後）に「長期持ち越し再判定（ver16.5 追加）」を追加。検出条件・挙動・想定される対応（降格 / 維持 / 再判断）の 3 点と、詳細仕様の参照先（`issue_review/SKILL.md §1.5 / §5`）を記載。

## 技術的判断

### 測定指標: `reviewed_at` 日付差分方式を採用

「N バージョン以上前」の代理指標として、`reviewed_at` と本日日付の差分（日数）を採用。根拠:
- 新規 frontmatter フィールド不要（既存 ISSUE 全件に即適用）
- SKILL.md 内の自然言語手順で完結し、Python スクリプト変更なし
- `reviewed_at` は `ready/ai` 昇格後は更新されない（`review/ai` に戻して再判定するまで固定）ため、「`ready/ai` 滞留日数」の代理として機能する

不採用候補:
- `carryover_count` 追加: frontmatter の侵襲的変更が発生するため不採用
- git log 初出日: リネーム履歴・空白挙動の不確実性と「ファイル年齢」と「滞留時間」の概念混同リスクで不採用

### 閾値: 7 日

ver14〜ver16 の version bump 実績（1 minor ≒ 1〜2 日サイクル、5 バージョン ≒ 5〜10 日）の中央値から 7 日を既定値とした。SKILL.md 内の 1 箇所に定数を集約し、運用観察結果次第で後続版で調整可能とする設計。

### ISSUE §AI からの依頼セクション: done/ 移動時は保持

消化 ISSUE（`issue-review-long-carryover-redemotion.md`）の done/ 移動時、本文末尾の `## AI からの依頼` セクションを保持（削除しない）。根拠: done/ 配下の先行 ISSUE に同セクションを持つものが観察されず慣行確立済みとは言えないため、情報損失回避を優先。

### 今後の観察課題（後続版）

- **F-1 閾値妥当性**: 本日（2026-04-25）時点で util ready/ai 4 件の `reviewed_at` はすべて 7 日以内のため初回発火未確認。ver16.6〜16.7 の `/issue_plan` 実行で発火を観察する
- **F-3 LLM 日付計算確認**: 次版 `/issue_plan` の ROUGH_PLAN.md に `## 再判定推奨 ISSUE` が正しい書式で出力されるか目視確認する
