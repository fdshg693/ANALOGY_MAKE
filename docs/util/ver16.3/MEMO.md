# ver16.3 MEMO — /imple_plan 実施メモ

## 実装結果

IMPLEMENT.md §B に基づき新規 ISSUE を 1 件作成した。§A（cost tracking 初回突合）は本 step のスコープ外（`/retrospective` 担当）のため本 step では観察のみ。

### 作成ファイル

- `ISSUES/util/low/issue-review-long-carryover-redemotion.md`
  - frontmatter: `status: raw`, `assigned: ai`, `priority: low`, `reviewed_at: "2026-04-24"`
  - 本文 5 節（`## 概要` / `## 背景（ver16.3 handoff 経由）` / `## 対応方針（設計提案）` / `## 影響範囲` / `## 関連資料`）— PLAN_HANDOFF.md §「`/split_plan`」の節立て指定どおり
  - 設計要素 3 点（スキャン対象拡張 / しきい値 2 段階 / 判定ルート）を `## 対応方針（設計提案）` 配下のサブ節として記述

### 動作確認

1. `python scripts/issue_status.py util` 実行結果: `util/low raw/ai=3`（作成前 2 件 → 作成後 3 件）。新規 ISSUE が想定どおり `raw/ai` として集計されることを確認
2. `npx nuxi typecheck` 実行結果: exit 0。CLAUDE.md 既知の vue-router volar 警告（`Cannot find module '@vue/language-core'`）のみで、型エラーは無し
3. `pnpm test` は未実行（IMPLEMENT.md §B 手順 4 の「322 tests は触らない」および PLAN_HANDOFF.md §「`/imple_plan`」の「実行確認はスキップしてよい」に従う。ISSUE 追加のみで scripts/ には変更なし）

### 計画との乖離

なし。IMPLEMENT.md §B 実装手順どおりに進行。§C の「REFACTOR.md 作成しない」判断も維持（事前リファクタリング不要）。

## リスク・不確実性（IMPLEMENT.md にセクションなし）

IMPLEMENT.md に `## リスク・不確実性` セクションが存在しないため、本節での検証・先送り記録は発生しない（/imple_plan SKILL §動作確認 4 の条件非該当）。なお本版の §A（cost tracking 観察）は `/retrospective` 側で扱う性質であり、ここでのリスク扱いではない。

## 残課題・更新提案

- **本 ISSUE の昇格タイミング**: 作成した `issue-review-long-carryover-redemotion` は `status: raw / ai` のため、次回 util カテゴリで `/issue_plan` が走る際のレビューフェーズで `review / ai` 経由 `ready / ai` に昇格させる想定。ver16.4 で扱う候補
- **SKILL 拡張版のスコープ試算**: 本 ISSUE が `ready / ai` に昇格後、`issue_review` SKILL 本体の拡張実装はおそらく minor 1 版で完結するが、`issue_plan` 側インライン展開部の同期更新が必要になるため 2〜3 ファイル編集になる見込み
- **`/retrospective` への申し送り**: §A の cost tracking 突合観点チェックリスト（A-1〜A-6）は IMPLEMENT.md §A に固定済み。`/retrospective` 着手時は IMPLEMENT.md §A のチェックリストを起点に `logs/workflow/*.costs.json` を走査する運用を想定。CHANGES.md / RETROSPECTIVE.md 側でも参照リンクを張るのが望ましい
