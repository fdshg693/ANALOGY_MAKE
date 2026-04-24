# ver15.1 CHANGES

ver15.0 からの変更差分。

## 概要

`issue_scout`（`--workflow scout`）の初回 smoke test を実施し、`issue-scout-noise-risk.md`（R1/R2 観察追跡 ISSUE）をクローズした。コード変更なし。

## 変更内容

### ISSUES

- `ISSUES/util/medium/issue-scout-noise-risk.md` → `ISSUES/util/done/issue-scout-noise-risk.md`（クローズ）
  - 3 軸評価（上限遵守 / 重複検出 / frontmatter 完全性）すべてクリア

### ISSUES（scout 起票 — 次回 `/issue_plan` でレビュー）

scout smoke test の副産物として 2 件が新規起票（本バージョンでは `raw / ai` 保持、次回 `/issue_plan` でレビュー）:

- `ISSUES/util/medium/imple-plan-four-file-yaml-sync-check.md`（新規）
- `ISSUES/util/low/readme-workflow-yaml-table-missing-scout.md`（新規）

### docs

- `docs/util/ver15.1/` 新設（本ファイル含む）

## smoke test 観察結果

| 観察軸 | 結果 | 詳細 |
|---|---|---|
| 上限遵守（0〜3 件） | ✓ | 2 件起票 |
| 重複検出 | ✓ | スキップ 0 件・起票内容は既存と非重複 |
| frontmatter 完全性 | ✓ | 全件 `status:raw` / `assigned:ai` / `priority` / `reviewed_at` 揃い |

scout は「形骸的起票をしない」判断を適切に行い、第 3 候補（SKILL パス大文字小文字ブレ / model 調整候補）を自律的にゼロに留めた。ノイズ率・重複検出ヒューリスティックともに想定内の挙動を確認。
