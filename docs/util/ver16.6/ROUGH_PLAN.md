---
workflow: quick
source: issues
---

# ver16.6 ROUGH_PLAN — `issue_review` §1.5 LLM 日付計算動作確認（F-3 消化）

## 位置づけ

minor 版。ver16.5 で `issue_review` SKILL §1.5 / §5 第 3 ブロックとして追加した「`ready/ai` 長期持ち越し ISSUE の再判定推奨ルート」の **初回実走**ループ。本 `/issue_plan` の出力そのものが検証対象となる自己言及的な構造で、F-3 観察 ISSUE の完了条件（「正しい書式で出力が確認できれば done/ へ移動」）を本ループで満たす。

## バージョン種別

**マイナー（ver16.6）**。コード変更ゼロ、SKILL / YAML 変更なし、ISSUE 消化 1 件（観察系）、アーキテクチャ / 新規外部依存 / 破壊的変更いずれもなし。メジャー昇格条件に該当しない。

## ワークフロー選択

**`quick`**。根拠:

- 選定 ISSUE は `ready/ai` のみ（`review` を含まず、`full` 強制条件に該当せず）
- 実装は F-3 ISSUE ファイル 1 本を `ISSUES/util/low/done/` に `git mv` するのみ。編集ゼロ・ファイル数 1・行数 0
- 外部仕様確認 / 実験 / 長時間検証いずれも不要（`research` 条件に該当せず）

## 着手対象 / スコープ

### 実施する

1. 本 ROUGH_PLAN.md に `## 再判定推奨 ISSUE` ブロックを SKILL.md §5 テンプレート準拠の書式（該当ゼロ版「該当なし」1 行）で出力する
2. F-3 ISSUE `ISSUES/util/low/issue-review-llm-date-calc-observation.md` の完了条件を本 ROUGH_PLAN 生成時点の書式により判定（見出し存在 / テンプレート一致 / 該当ゼロ時の 1 行出力）
3. `/quick_impl` 段階で `git mv ISSUES/util/low/issue-review-llm-date-calc-observation.md ISSUES/util/low/done/`（書式 OK 前提）

### 実施しない

- **F-1 閾値妥当性観察**（`issue-review-7day-threshold-observation`）: 本版時点で §1.5 対象 ISSUE ゼロ、自然な時間経過待ち。最早発火予測 2026-04-30 以降
- **`raw/ai` 2 件の triage**（`rules-paths-frontmatter-autoload-verification` / `scripts-readme-usage-boundary-clarification`）: ver16.3 以降据え置き継続。3 ループ連続停滞となる ver16.7 到達時点で昇格ルート整備を検討
- **`deferred-resume-twice-verification`**（medium, ready/ai）: research workflow 必要、本版 quick と方針不整合
- **`toast-persistence-verification`**（low, ready/ai）: Windows 実機目視必須で AI 単独消化不能
- **`issue-review-rewrite-verification`**（medium, ready/ai）: 他カテゴリでの `review/ai` ISSUE 発生が前提、観察機会なし
- **PHASE9.0 骨子作成**: PHASE8.0 完走済だが、既存 ready/ai が 5 件あり MASTER_PLAN ガイドライン 1（既存 ISSUES 消化優先）に従い次 PHASE 着手は見送り
- **`imple_plan` effort 下げ試行**: 本版は `/quick_impl` ルート（`/split_plan` → `/imple_plan` を通らない）のため handoff §2 の対象外

## 想定成果物

- `docs/util/ver16.6/ROUGH_PLAN.md`（本ファイル）
- `docs/util/ver16.6/PLAN_HANDOFF.md`
- `docs/util/ver16.6/IMPLEMENT.md`（`/quick_impl` 生成、~10 行規模）
- `docs/util/ver16.6/CHANGES.md`（`/write_current`）
- `docs/util/ver16.6/MEMO.md`（`/wrap_up`、任意）
- `docs/util/ver16.6/RETROSPECTIVE.md`
- `ISSUES/util/low/done/issue-review-llm-date-calc-observation.md`（F-3 移動）

## 事前リファクタリング要否

**不要**。コード変更ゼロ、SKILL 変更ゼロ。

---

## ISSUE レビュー結果

- `review/ai` → `ready/ai` に遷移: 0 件（対象ファイルなし）
- `review/ai` → `need_human_action/human` に遷移: 0 件
- 追記した `## AI からの依頼`: 0 件

## ISSUE 状態サマリ

| status / assigned | 件数 |
|---|---|
| ready / ai | 5 |
| review / ai | 0 |
| need_human_action / human | 0 |
| raw / human | 0 |
| raw / ai | 2 |

内訳:

- **ready / ai (5)**: `issue-review-rewrite-verification`, `deferred-resume-twice-verification`, `toast-persistence-verification`, `issue-review-7day-threshold-observation`, `issue-review-llm-date-calc-observation`
- **raw / ai (2)**: `rules-paths-frontmatter-autoload-verification`, `scripts-readme-usage-boundary-clarification`

## 選定理由・除外理由

### 選定: `issue-review-llm-date-calc-observation`（F-3、low）

- 検証対象が **次版 `/issue_plan` 出力そのもの**という自己言及構造で、本ループ単体で完結可能な唯一の ready/ai ISSUE
- 完了条件が「書式目視 → done/ 移動」と明快、所要時間最小で quick 志向と整合

### 除外 ISSUE

| ISSUE | 除外理由 |
|---|---|
| `issue-review-rewrite-verification` (medium) | 他カテゴリで `review/ai` ISSUE が発生しない限り観察機会ゼロ |
| `deferred-resume-twice-verification` (medium) | research workflow が必要（`experiments/` 実測） |
| `toast-persistence-verification` (low) | Windows 実機目視必須（AI 単独消化不能） |
| `issue-review-7day-threshold-observation` (low) | 本版時点で §1.5 発火対象ゼロ、自然な時間経過待ち |
| `rules-paths-frontmatter-autoload-verification` (raw/ai) | triage 据え置き、ver16.7 到達時点で昇格ルート検討 |
| `scripts-readme-usage-boundary-clarification` (raw/ai) | 同上 |

---

## 再判定推奨 ISSUE

該当なし（`ready/ai` で 7 日以上停滞している ISSUE はない）。

※ 参考（本日 2026-04-25 時点の ready/ai 5 件の `reviewed_at` 経過日数）:

- `issue-review-rewrite-verification` — reviewed_at: 2026-04-23（2 日経過）
- `deferred-resume-twice-verification` — reviewed_at: 2026-04-24（1 日経過）
- `toast-persistence-verification` — reviewed_at: 2026-04-24（1 日経過）
- `issue-review-7day-threshold-observation` — reviewed_at: 2026-04-25（0 日経過）
- `issue-review-llm-date-calc-observation` — reviewed_at: 2026-04-25（0 日経過）

初回発火予測: `issue-review-rewrite-verification` が 2026-04-30 以降で閾値 7 日に到達（途中で `review/ai` に差し戻されなければ）。F-1 観察継続。
