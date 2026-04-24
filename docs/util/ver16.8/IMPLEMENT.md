---
workflow: quick
source: issues
---

# ver16.8 IMPLEMENT

## 実装対象

ROUGH_PLAN §1〜4 の全 5 タスク。

## 変更ファイル一覧

| ファイル | 変更種別 | 内容 |
|---|---|---|
| `.claude/skills/issue_review/SKILL.md` | 編集 | §1.6 追加 + §5 第 4 ブロック追加 + §3 注記更新 + frontmatter description 更新 |
| `.claude/skills/issue_plan/SKILL.md` | 編集 | 「準備」節 ISSUE レビューフェーズに (c) を追加、4 ブロック列挙に更新 |
| `ISSUES/util/low/done/issue-review-7day-threshold-observation.md` | git mv | `done/` へ移動（完了記録を本文末尾に追記済み） |
| `ISSUES/util/low/issue-review-7day-threshold-adjustment.md` | 新規作成 | 7 日閾値→5 日短縮検討 ISSUE（raw/ai, low, reviewed_at: 2026-04-25） |

## §1.6 実装詳細

§1.5（ready/ai 長期持ち越し検出）の構造を踏襲し、以下を差分として実装:

- 対象 status: `raw`（§1.5 は `ready`）
- 閾値: 14 日（§1.5 の 2 倍）
- 出力ブロック: §5 第 4 ブロック「## triage 推奨 raw/ai ISSUE」
- `reviewed_at` 意味論: ISSUE 登録時または前回レビュー時の日付が固定される

## §5 第 4 ブロック仕様

- 該当あり: path / reviewed_at / 経過日数 + 候補理由 A（review/ai 昇格候補）/ 候補理由 B（raw/ai 継続）
- 該当なし: `該当なし（raw/ai で 14 日以上 triage されていない ISSUE はない）。` の 1 行

## §1.6 初回動作確認（本版実装完了時点の予測）

本版完了時点での raw/ai 内訳（reviewed_at が 2026-04-24 or 2026-04-25 のため 14 日閾値未到達）:

- `rules-paths-frontmatter-autoload-verification` — 1 日経過
- `scripts-readme-usage-boundary-clarification` — 1 日経過
- `issue-review-7day-threshold-adjustment`（本版新規）— 0 日経過

次版以降で「triage 推奨 raw/ai ISSUE: 該当なし」が「該当あり」に変わることを 2026-05-08 以降に確認予定。
