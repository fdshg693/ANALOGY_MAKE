---
workflow: quick
source: issues
---

# ver16.8 CHANGES

前バージョン ver16.7 からの変更差分。

## 変更ファイル一覧

| ファイル | 変更種別 | 概要 |
|---|---|---|
| `.claude/SKILLS/issue_review/SKILL.md` | 変更 | §1.6（raw/ai 長期停滞検出）追加、§5 第 4 ブロック追加、§3 注記更新、frontmatter description 更新 |
| `.claude/SKILLS/issue_plan/SKILL.md` | 変更 | 「準備」節 ISSUE レビューフェーズに (c) 追加、4 ブロック列挙に更新 |
| `ISSUES/util/low/done/issue-review-7day-threshold-observation.md` | 移動（rename） | `low/` → `low/done/` へ移動、完了記録を末尾に追記 |
| `ISSUES/util/low/issue-review-7day-threshold-adjustment.md` | 新規 | §1.5 閾値（7 日 → 5 日）短縮検討 ISSUE を起票（raw/ai, low） |
| `docs/util/ver16.8/IMPLEMENT.md` | 新規 | 実装記録 |
| `docs/util/ver16.8/ROUGH_PLAN.md` | 新規 | 計画書（issue_plan 生成） |
| `docs/util/ver16.8/PLAN_HANDOFF.md` | 新規 | 後続 step への引き継ぎ情報（issue_plan 生成） |

コード（`scripts/` / `server/` / `app/`）の変更はゼロ。

## 変更内容の詳細

### `issue_review/SKILL.md` への §1.6 追加

ver16.5 で導入した §1.5（ready/ai 長期持ち越し検出、7 日閾値）と同型のルートを `raw/ai` ISSUE にも拡張した。

- 対象: `status: raw` かつ `assigned: ai` のうち `reviewed_at` が **14 日以上**前の ISSUE
- 閾値 14 日の根拠: raw/ai は triage 判断そのものに時間がかかるため §1.5（7 日）の 2 倍を暫定初期値とした
- 出力: §5 第 4 ブロック「## triage 推奨 raw/ai ISSUE」として列挙（frontmatter 書き換えなし）
- `reviewed_at` 欠落 ISSUE は対象外（§1.5 と同じ扱い）

### `issue_review/SKILL.md` への §5 第 4 ブロック追加

§5 サマリ報告の出力テンプレートに第 4 ブロックを追加:

- 該当あり版: path / reviewed_at / 経過日数 + 候補理由 A（review/ai 昇格候補）/ 候補理由 B（raw/ai 継続 + 情報源追記）
- 該当なし版: `該当なし（raw/ai で 14 日以上 triage されていない ISSUE はない）。` の 1 行

### `issue_plan/SKILL.md` の同期更新

`issue_review/SKILL.md` 変更に合わせて呼び出し元を更新:

- 「準備」節 ISSUE レビューフェーズに「(c) raw/ai で reviewed_at が 14 日以上前の ISSUE を triage 推奨として検出する（frontmatter 書き換えなし）」を追加
- ROUGH_PLAN 冒頭 3 ブロック列挙を 4 ブロック（`## triage 推奨 raw/ai ISSUE` を追加）に更新

### F-1 閾値観察 ISSUE の完了処理

`issue-review-7day-threshold-observation`（ready/ai, low）:
- 完了条件「2 版経過後も §1.5 未発火 → 閾値調整 ISSUE 起票」に到達（ver16.6/16.7 連続未発火）
- 完了記録を本文末尾に追記し、`ISSUES/util/low/done/` に移動

### 後続 ISSUE の起票

`issue-review-7day-threshold-adjustment`（raw/ai, low, reviewed_at: 2026-04-25）:
- 7 日閾値が 3 版連続未発火（過鈍の可能性）のため、5 日への短縮案を検討する ISSUE を新規起票
- 対応方針: §1.5 閾値を 5 日に変更後、次版以降で発火観察を継続

## ISSUE 状態変化（ver16.7 → ver16.8）

| ISSUE | ver16.7 状態 | ver16.8 状態 |
|---|---|---|
| `issue-review-rewrite-verification` | ready/ai (medium) | ready/ai (medium)（不変） |
| `deferred-resume-twice-verification` | ready/ai (medium) | ready/ai (medium)（不変） |
| `toast-persistence-verification` | ready/ai (low) | ready/ai (low)（不変） |
| `issue-review-7day-threshold-observation` | ready/ai (low) | done/（移動） |
| `issue-review-7day-threshold-adjustment` | 未存在 | raw/ai (low)（新規起票） |
| `rules-paths-frontmatter-autoload-verification` | raw/ai (low) | raw/ai (low)（不変、§1.6 の将来検出対象） |
| `scripts-readme-usage-boundary-clarification` | raw/ai (low) | raw/ai (low)（不変、§1.6 の将来検出対象） |
