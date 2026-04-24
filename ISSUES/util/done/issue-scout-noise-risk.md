---
status: raw
assigned: ai
priority: medium
reviewed_at: "2026-04-24"
---

# issue_scout 初回 run のノイズ率・重複検出閾値の観察

## 概要

ver15.0 で `/issue_scout`（`--workflow scout`）を新設した際に、以下 2 点の検証を初回 smoke test まで先送りした。本 ISSUE は先送りリスクが MEMO.md 内に埋もれないようにするためのトレースポイント。

1. **ノイズ率**（IMPLEMENT.md §リスク R1）: `issue_scout` の判定粒度が粗いと価値の低い `raw / ai` が増え、`ISSUES/` がノイズ源化する
2. **重複検出閾値**（IMPLEMENT.md §リスク R2）: SKILL 内ヒューリスティック（タイトル正規化完全一致 + 本文冒頭 50 文字 Jaccard ≥ 0.5）の閾値が過検出/取りこぼしどちらに偏るか未検証

## 本番発生時の兆候

- `python scripts/issue_status.py util` の `raw / ai` 件数が 1 run あたり 3 件の上限近くに張り付く
- `/issue_plan` 冒頭の ISSUE レビューフェーズで「実質重複」な ISSUE が頻出する
- 逆に、既存 ISSUE と明らかに類似する候補まで起票されている／類似しない候補がスキップされている

## 対応方針

初回 `issue_scout` run（`/wrap_up` smoke test か手動 `python scripts/claude_loop.py --workflow scout --category util --max-loops 1`）の結果を見て以下を判断:

- 起票された ISSUE と既存 `ISSUES/util/` および `ISSUES/util/done/` を目視 diff
- 過検出なら Jaccard 閾値を 0.4 程度まで下げる or タイトル正規化を substring まで緩める
- 取りこぼしなら閾値を 0.6 程度まで上げる or 本文冒頭の比較対象を 100 文字に広げる
- ノイズ率が高い場合は SKILL.md の「価値観点 3 軸」を再定義 or 件数上限を 2 件に引き下げ

## 影響範囲

- `.claude/skills/issue_scout/SKILL.md`（ヒューリスティック定義）
- `ISSUES/util/` の分布シグナル/ノイズ比
- `/issue_plan` のレビュー負荷

## 参照

- `docs/util/ver15.0/IMPLEMENT.md` §リスク・不確実性 R1, R2
- `docs/util/ver15.0/MEMO.md` §リスク検証結果 R1, R2
