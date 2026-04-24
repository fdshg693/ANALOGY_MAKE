---
workflow: full
source: issues
---

# ver16.3 CHANGES — cost tracking 初回実機突合 準備 + 長期持ち越し ready/ai 再判定手順 ISSUE 起票

## 変更ファイル一覧

### 追加

| ファイル | 概要 |
|---|---|
| `ISSUES/util/low/issue-review-long-carryover-redemotion.md` | 新規 ISSUE: `ready/ai` 長期持ち越しを検出・再判定するルートを `issue_review` SKILL に追加する設計提案 |
| `docs/util/ver16.3/ROUGH_PLAN.md` | ver16.3 課題選定計画（issue_plan step 成果物） |
| `docs/util/ver16.3/PLAN_HANDOFF.md` | 後続 step 向け引き継ぎ（issue_plan step 成果物） |
| `docs/util/ver16.3/IMPLEMENT.md` | 実装計画（split_plan step 成果物）。§A cost tracking 突合観点チェックリスト・§B ISSUE 起票手順を記載 |
| `docs/util/ver16.3/MEMO.md` | 実装メモ・wrap_up 結果（imple_plan/wrap_up step 成果物） |

### 移動

| 元パス | 移動先 | 概要 |
|---|---|---|
| `FEEDBACKS/handoff_ver16.2_to_next.md` | `FEEDBACKS/done/handoff_ver16.2_to_next.md` | ver16.3 issue_plan で消費完了、`done/` へ移動 |

## 変更内容の詳細

### §A. cost tracking 初回実機突合の準備（観察・評価系、実装変更なし）

ver16.2 で実装した PHASE8.0 §3（`costs.py` / `logs/workflow/*.costs.json` sidecar）の初回本番突合を `/retrospective §3.5 相当` に委ねる準備を行った。

- `IMPLEMENT.md §A` に突合観点チェックリスト（A-1〜A-6）を固定：`modelUsage` key 名確認（A-1）・`total_cost_usd` と `cost_source` 分布（A-2）・`status="unavailable"` 発生率（A-3）・deferred 発火時の kind 別 record（A-4）・live stdout サイレント化の実害度（A-5）・top-level key の突合（A-6）
- 本 step 実行時に `/issue_plan` sidecar（`20260424_231449_claude_loop_issue_plan.costs.json`）を先行観察し、先行所見 4 点を `IMPLEMENT.md §A` の「初期観察」欄に記録（正式判定は `/retrospective` 担当）
- 本 ver16.3 では **実装変更なし**。突合で「実装 bug / 仕様乖離の兆候」が発見された場合のみ次版以降で対応する方針を `IMPLEMENT.md §A` に明示

### §B. 長期持ち越し ready/ai 再判定手順の ISSUE 起票（実装系）

`ready / ai` のまま 5 バージョン以上着手されない ISSUE を検出・降格する「長期持ち越し再判定ルート」を `issue_review` SKILL に追加する設計提案を ISSUE として書き起こした。

- 作成 ISSUE: `ISSUES/util/low/issue-review-long-carryover-redemotion.md`（`status: raw`, `assigned: ai`, `priority: low`）
- 設計提案の 3 要素:
  1. **スキャン対象拡張**: `status: ready / ai` かつ `reviewed_at` が N バージョン以上前を検出対象に追加
  2. **しきい値 2 段階**: 5 バージョン連続 = 要再判定警告、10 バージョン連続 = 強制降格
  3. **判定ルート**: 実機検証を要するなら `need_human_action / human` へ降格、AI 消化可能なら `ready / ai` 維持 + `## AI からの依頼` にヒント追加
- 影響ファイル（将来版で実装時): `.claude/skills/issue_review/SKILL.md` / `.claude/skills/issue_plan/SKILL.md` / `ISSUES/README.md`
- **本版では SKILL 実装変更なし**。次回 `/issue_plan` で `review / ai` 経由 `ready / ai` に昇格後、別版で拡張実装する

### MASTER_PLAN.md 更新

PHASE8.0 のサマリ行を「§1・§2 実装済み」から「**実装済み**（全 3 節完了）」に修正。ver16.2 で §3 token/cost 計測を実装済みだったが、ver16.2 の `write_current` で更新漏れとなっていた分を本版で補完。

## 技術的判断

### REFACTOR.md 非作成

本版は「新規 ISSUE 1 件追加」のみで既存ファイルへの変更なし。事前リファクタリング対象が存在しないため、REFACTOR.md の作成を省略（`ROUGH_PLAN.md` に根拠明記）。

### §A を `/retrospective` に集約する判断

cost tracking の突合観点は `/write_current`（本 step）ではなく `/retrospective` が全 sidecar 出揃い後に実施する設計とした。理由: 本版でコード変更なし・CHANGES.md に観察途中の暫定値を記載することによる混乱防止。`IMPLEMENT.md §A` チェックリストが `/retrospective` の起点として機能する。

### フィードバック消費

`FEEDBACKS/handoff_ver16.2_to_next.md` を消費完了として `done/` に移動。ver16.3 の issue_plan step で handoff 記載事項（§A cost tracking 突合・§B ISSUE 起票）を着手スコープに取り込んだことで、フィードバック内容の消化完了と判断。
