---
workflow: quick
source: issues
---

# ver16.6 PLAN_HANDOFF

## 関連 ISSUE / 関連ファイル

### 関連 ISSUE

- `ISSUES/util/low/issue-review-llm-date-calc-observation.md` — F-3 主眼、本版で消化予定
- `ISSUES/util/low/issue-review-7day-threshold-observation.md` — F-1 観察継続、本版は未発火で追加アクションなし

### 関連ファイル（参照のみ、本版は編集なし）

- `.claude/skills/issue_review/SKILL.md` — §1.5 / §5 第 3 ブロック仕様の一次資料（ver16.5 で追補済、本版は touch なし）
- `.claude/skills/issue_plan/SKILL.md` — §1.5 呼び出し側の運用手順（本版は touch なし）
- `docs/util/ver16.6/ROUGH_PLAN.md` — `## 再判定推奨 ISSUE` ブロックが書式検証対象そのもの

## 後続 step への注意点

### /quick_impl

- 唯一の実装操作: `git mv ISSUES/util/low/issue-review-llm-date-calc-observation.md ISSUES/util/low/done/`
- コード / SKILL / テスト / YAML いずれも編集なし。Python / Node の実行も不要
- 事前確認: 本 ROUGH_PLAN.md の `## 再判定推奨 ISSUE` ブロックが SKILL.md §5 の「該当ゼロ版」テンプレート（見出し ＋「該当なし〜」1 行）と一致していること。書式崩れを発見した場合は移動せず、代わりに `SKILL.md §1.5 / §5 に計算例 inline 追記` の後続 ISSUE を `ISSUES/util/low/` に新規起票すること（F-3 ISSUE 本文の「書式崩れ / 見出し欠落の場合」分岐に一致）
- `imple_plan effort 下げ試行`（ver16.5 handoff §2）は本版対象外: `/quick_impl` ルートは `/imple_plan` step を経由しないため試行機会なし。ver16.7 以降で `full` ワークフローかつ実装量小ケースが出た際に再試行

### /write_current

- CHANGES.md のみ作成（minor）
- 必須記載: (a) F-3 ISSUE 消化、(b) §1.5 ルートの初回実走書式確認完了、(c) コード / SKILL 変更ゼロ
- 前版 ver16.5 との差分は「ISSUES/util/low/done/ に 1 件追加」のみ

### /wrap_up

- F-3 完了条件: 本 ROUGH_PLAN.md の §再判定推奨 ISSUE が書式テンプレート準拠 → 充足済として扱い、F-3 ISSUE を done/ へ移動する判定の最終確定
- F-1（閾値妥当性）: 本版未発火のため追加アクションなし。次版 handoff で継続観察項目として引き継ぐ
- 観察 ISSUE の新規起票基準: ver16.5 wrap_up で F-1/F-3 起票した運用サンプル 1 件目が本版で消化された。2 サンプル目（次の SKILL 追補を伴う minor 版）を待ってから SKILL 文言化を判断する

### §1.5 予測 vs 実績の整合性記録（ver16.5 handoff §3 要請）

- **予測**（ver16.5 RETROSPECTIVE §3.5）: ready/ai 5 件すべて `reviewed_at < 7 日` → §1.5 出力「該当なし」
- **実績**（本 ROUGH_PLAN §再判定推奨 ISSUE）: 該当ゼロ、列挙 ISSUE 0 件、「該当なし」1 行出力
- **整合判定**: 予測通り。§1.5 判定ルートの初回実走は書式レベル・計数レベルともに想定動作を確認

### raw/ai 2 件の停滞観察

- `rules-paths-frontmatter-autoload-verification` / `scripts-readme-usage-boundary-clarification` は ver16.3 から本版まで計 4 ループ（ver16.3 / 16.4 / 16.5 / 16.6）据え置き
- ver16.5 handoff では「3 ループ連続停滞（ver16.7 到達時点）で昇格ルート整備検討」とあるが、本版で既に 4 ループ目。ver16.7 の `/issue_plan` 時点で「`raw/ai` 長期停滞向け review 昇格ルート」を ver16.5 §1.5 と同型の meta 改善として起案する優先度を一段上げてよい
