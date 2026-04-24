# ver15.1 CHANGES

ver15.0 からの変更差分。`issue_scout` 初回 smoke test 実施・`issue-scout-noise-risk.md` クローズ。コード変更なし。

## 変更ファイル一覧

| ファイル | 種別 | 概要 |
|---|---|---|
| `FEEDBACKS/handoff_ver15.0_to_next.md` | 移動 → `done/` | ver15.0 handoff を消費（路線 A 完了）|
| `ISSUES/util/medium/issue-scout-noise-risk.md` | 移動 → `done/` | R1/R2 観察 ISSUE クローズ（3 軸全クリア）|
| `ISSUES/util/medium/imple-plan-four-file-yaml-sync-check.md` | 新規 | scout 起票: `/imple_plan` への YAML 同期チェック追記提案 |
| `ISSUES/util/low/readme-workflow-yaml-table-missing-scout.md` | 新規 | scout 起票: README ファイル一覧に scout YAML が未掲載 |
| `docs/util/ver15.1/ROUGH_PLAN.md` | 新規 | バージョン計画（`/issue_plan` 成果物）|
| `docs/util/ver15.1/CHANGES.md` | 新規 | 本ファイル |
| `docs/util/ver15.1/MEMO.md` | 新規 | 実装メモ・引き継ぎ |

## 変更内容の詳細

### scout smoke test 実施・R1/R2 リスク観察クローズ

`python scripts/claude_loop.py --workflow scout --max-loops 1` を実行し、`/issue_scout` SKILL の初回観察を実施。

**3 軸評価結果**:

| 観察軸 | 結果 | 詳細 |
|---|---|---|
| 上限遵守（0〜3 件） | ✓ | 2 件起票 |
| 重複検出 | ✓ | スキップ 0 件・内容も既存 ISSUE と非重複 |
| frontmatter 完全性 | ✓ | 全件 `status:raw` / `assigned:ai` / `priority` / `reviewed_at` 揃い |

scout は「形骸的起票をしない」判断を適切に行い、第 3 候補（SKILL パス大文字小文字ブレ / model 調整）を自律的にゼロに留めた。ノイズ率・重複検出ヒューリスティックともに想定内の挙動を確認。

### ISSUES 状態変化

- `issue-scout-noise-risk.md` を `done/` 化（R1/R2 リスク観察クローズ）
- scout 起票 2 件を `raw / ai` 保持（次回 `/issue_plan` でレビュー）
