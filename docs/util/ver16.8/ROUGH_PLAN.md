---
workflow: quick
source: issues
---

# ver16.8 ROUGH_PLAN — `issue_review` SKILL に raw/ai 長期停滞検出ルート（§1.6）を追加

## 位置づけ

minor 版。ver16.5 で導入した §1.5「ready/ai 長期持ち越し検出」と同型のルートを `raw/ai` ISSUE にも拡張し、triage されないまま放置されている raw/ai ISSUE を `/issue_plan` 出力の第 4 ブロックとして可視化する。併せて、観察用 ISSUE `issue-review-7day-threshold-observation` が「2 版経過後も未発火」の完了条件に到達したため、閾値調整検討用の後続 ISSUE を起票し、観察 ISSUE 自体を `done/` へ移動する。

## バージョン種別

**マイナー（ver16.8）**。変更範囲は `.claude/skills/issue_review/SKILL.md` と `.claude/skills/issue_plan/SKILL.md`（同期更新）、および `ISSUES/util/low/` 配下の 1 件 `done/` 移動 + 1 件新規起票のみ。アーキテクチャ変更・新規外部依存・破壊的変更いずれもなし。メジャー昇格条件に該当しない。

## ワークフロー選択

**`quick`**。根拠:

- 選定 ISSUE に `status: review` を含まず（`full` 強制条件に該当せず）、util カテゴリの `review/ai` は 0 件
- MASTER_PLAN 新項目 / アーキ変更 / 新規外部ライブラリ導入のいずれにも該当しない
- 変更対象は 2 SKILL ファイル（同期更新で合計 ~50〜70 行規模）+ ISSUE ファイル 2 件（1 件 `done/` 移動、1 件新規作成）。3 ファイル以下・100 行以下の quick 閾値にほぼ収まる
- `research` 必要 4 条件のいずれも該当しない（外部仕様確認不要、実験不要、長時間検証不要、隔離環境不要）

## 着手対象 / スコープ

### 実施する

1. **`issue_review` SKILL に §1.6 を新設**（`.claude/skills/issue_review/SKILL.md`）
   - `status: raw` かつ `assigned: ai` の ISSUE のうち、`reviewed_at` が本日との差分で **14 日以上**のものを「triage 推奨」として新ブロックに列挙
   - frontmatter 書き換えは行わない（§1.5 と同じく報告のみ）
   - 閾値 14 日は SKILL 内既定値。根拠は「raw/ai は `review/ai` よりも triage に長期間要する可能性を含むため、§1.5（7 日）の 2 倍を暫定初期値とする」
2. **`issue_review` SKILL §5 に第 4 ブロック「## triage 推奨 raw/ai ISSUE」を追加**
   - 該当あり版 / 該当なし版の両テンプレを §1.5 と揃えた書式で提供
3. **`issue_plan` SKILL を同期更新**（`.claude/skills/issue_plan/SKILL.md`）
   - 「準備」節の ISSUE レビューフェーズ記載に第 4 ブロック要件を追加（「(c) raw/ai 長期停滞検出」列の追記）
   - ROUGH_PLAN 本文冒頭の見出し列に `## triage 推奨 raw/ai ISSUE` を追加
4. **F-1 閾値観察の完了処理**
   - `ISSUES/util/low/issue-review-7day-threshold-observation.md` を `ISSUES/util/low/done/` に移動（「2 版経過後も未発火 → 後続 ISSUE 起票」の完了条件に到達）
   - `ISSUES/util/low/issue-review-7day-threshold-adjustment.md` を新規起票（`status: raw`, `assigned: ai`, `priority: low`, `reviewed_at: "2026-04-25"`）。内容: 7 日閾値の過鈍判定根拠（ver16.6/16.7 連続未発火）+ 5 日への短縮案 + 次回発火観察の記載
5. **§1.6 の動作確認**（本版 scope 内）: 本版完了時点の util raw/ai 2 件は `reviewed_at: "2026-04-24"` で本日（2026-04-25）との差分は 1 日のため、初回は「該当なし」枠が出力される想定。**実際に 1 件でも列挙される発火観察は後続版持ち越し**

### 実施しない

- **raw/ai 2 件（`rules-paths-frontmatter-autoload-verification` / `scripts-readme-usage-boundary-clarification`）の直接 triage**: §1.6 で検出可能になった後、次版以降で human / AI 判断により triage。本版は「検出ルート整備」まで
- **`deferred-resume-twice-verification`（medium, ready/ai）**: ver16.7 で harness 整備済み。人手実測待ちで AI 能動前進余地ゼロ
- **`issue-review-rewrite-verification`（medium, ready/ai）**: 他カテゴリ（`app` / `infra`）で `review/ai` が発生する外部契機待ち。util カテゴリ内ではトリガー不可
- **`toast-persistence-verification`（low, ready/ai）**: Windows 実機目視必須で AI 単独消化不能
- **PHASE9.0 骨子作成**: MASTER_PLAN ガイドライン 1 に従い既存 `ready/ai` 消化優先（ただし medium 2 件が AI 能動前進不可のため、本版は meta 改善で補完）
- **§1.5 閾値の実変更**: F-1 閾値調整 ISSUE として起票までで、実変更は後続版以降
- **raw/ai 閾値（14 日）の運用観察結果に基づく調整**: §1.6 新設直後のため、観察は後続版以降

## 想定成果物

- `docs/util/ver16.8/ROUGH_PLAN.md`（本ファイル）
- `docs/util/ver16.8/PLAN_HANDOFF.md`
- `docs/util/ver16.8/IMPLEMENT.md`（`/quick_impl` 生成、~40 行規模）
- `docs/util/ver16.8/CHANGES.md`（`/write_current`）
- `docs/util/ver16.8/MEMO.md`（`/wrap_up`、任意）
- `.claude/skills/issue_review/SKILL.md`（§1.6 追加 + §5 第 4 ブロック追加、~30 行増）
- `.claude/skills/issue_plan/SKILL.md`（同期更新、~5 行増）
- `ISSUES/util/low/done/issue-review-7day-threshold-observation.md`（`done/` 移動）
- `ISSUES/util/low/issue-review-7day-threshold-adjustment.md`（新規、~30 行）

## 事前リファクタリング要否

**不要**。§1.5 の既存書式を §1.6 でほぼコピー利用するのみで、既存ロジック・責務分離の見直しは発生しない。SKILL 同期更新 1 箇所は既に §131-137 で明文化済み（「呼び出し元との同期」節）、ルールも未変更。

---

## ISSUE レビュー結果

- `review/ai` → `ready/ai` に遷移: 0 件（対象ファイルなし）
- `review/ai` → `need_human_action/human` に遷移: 0 件
- 追記した `## AI からの依頼`: 0 件

## ISSUE 状態サマリ

| status / assigned | 件数 |
|---|---|
| ready / ai | 4 |
| review / ai | 0 |
| need_human_action / human | 0 |
| raw / human | 0 |
| raw / ai | 2 |

内訳:

- **ready / ai (4)**: `issue-review-rewrite-verification` (medium), `deferred-resume-twice-verification` (medium), `toast-persistence-verification` (low), `issue-review-7day-threshold-observation` (low)
- **raw / ai (2)**: `rules-paths-frontmatter-autoload-verification`, `scripts-readme-usage-boundary-clarification`

（上記分布は本版スコープで `issue-review-7day-threshold-observation` を `done/` 移動後、`ready/ai` = 3 件に減り、新規 `issue-review-7day-threshold-adjustment` が raw/ai に入り合計 `raw/ai` = 3 件になる想定）

## 選定理由・除外理由

### 選定: `issue_review` SKILL §1.6 新設（meta 改善）+ F-1 閾値観察の完了処理

選定根拠:

1. **medium ready/ai 2 件が AI 能動前進不可**: `deferred-resume-twice-verification` は ver16.7 で harness 整備済みで人手実測待ち、`issue-review-rewrite-verification` は他カテゴリでの `review/ai` 発生待ち。どちらも util 内の AI 作業では進まない（ver16.7 PLAN_HANDOFF §後続 step §raw/ai 2 件の停滞観察 に明記済み）
2. **ver16.7 handoff で明示的に優先度上げが指示されていた**: 「ver16.8 以降で meta 改善（raw/ai 長期停滞 → review 昇格ルート）優先度を一段上げる」「次に medium ready/ai が尽きた版で起案」。medium ready/ai は件数上 0 件ではないが、AI 視点で実質的に消化完了（全件外部待ち）のため、handoff 意図に沿う
3. **F-1 閾値観察完了条件への到達**: `issue-review-7day-threshold-observation` は「2 版（ver16.6 / ver16.7）経過後も未発火 → 後続 ISSUE 起票」が完了条件で、本版（ver16.8）にて 2 版経過の閾値に到達済み。done/ 移動と後続起票は本版で実行すべき保守作業
4. **変更規模が quick ワークフロー閾値に収まる**: SKILL 2 ファイル（§1.5 を template に §1.6 を追加、同期更新は 1 行変更）+ ISSUE ファイル 2 件操作のみ。3 ファイル・100 行以下に近い規模

### 除外 ISSUE / 判断

| ISSUE / 項目 | 除外理由 |
|---|---|
| `deferred-resume-twice-verification` (medium) | ver16.7 で harness 整備済、人手実測待ち（AI 能動前進余地ゼロ）|
| `issue-review-rewrite-verification` (medium) | 他カテゴリで `review/ai` 発生しない限り観察機会ゼロ（ver16.6/16.7 と同様 carryover）|
| `toast-persistence-verification` (low) | Windows 実機目視必須で AI 単独消化不能（carryover）|
| `rules-paths-frontmatter-autoload-verification` (raw/ai) | 本版の §1.6 はこの ISSUE を検出する側。直接 triage は後続版に持ち越し |
| `scripts-readme-usage-boundary-clarification` (raw/ai) | 同上。内容自体は triage 可能な具体性があるが、本版は検出ルート整備までで完結させる |
| PHASE9.0 骨子作成 | MASTER_PLAN ガイドライン 1（既存 ready/ai 消化優先 or meta 改善）に従い、PHASE 未着手は維持 |
| `issue_plan` effort 下げ試行 | 本版 quick のため対象外（ver16.5 handoff §2 / ver16.6 PLAN_HANDOFF 末尾の継続事項）。次に `full` 実装量小の版で handoff 再消費 |

---

## 再判定推奨 ISSUE

該当なし（`ready/ai` で 7 日以上停滞している ISSUE はない）。

※ 参考（本日 2026-04-25 時点の ready/ai 4 件の `reviewed_at` 経過日数）:

- `issue-review-rewrite-verification` — reviewed_at: 2026-04-23（2 日経過）
- `deferred-resume-twice-verification` — reviewed_at: 2026-04-24（1 日経過）
- `toast-persistence-verification` — reviewed_at: 2026-04-24（1 日経過）
- `issue-review-7day-threshold-observation` — reviewed_at: 2026-04-25（0 日経過、本版で `done/` 移動予定）

初回発火予測: `issue-review-rewrite-verification` が 2026-04-30 以降で閾値 7 日に到達（途中で `review/ai` に差し戻されなければ）。F-1 観察継続。

---

## §1.6 新設後の初回観察予測（本版参考記録）

本版の §1.6 実装完了時点での raw/ai 内訳:

- `rules-paths-frontmatter-autoload-verification` — reviewed_at: 2026-04-24（1 日経過）
- `scripts-readme-usage-boundary-clarification` — reviewed_at: 2026-04-24（1 日経過）
- `issue-review-7day-threshold-adjustment`（本版新規）— reviewed_at: 2026-04-25（0 日経過）

初回発火予測（14 日閾値）: 2026-05-08 以降（raw/ai 2 件の 14 日到達）。本版完了時点では「triage 推奨 raw/ai ISSUE: 該当なし」枠の出力のみを確認する。
