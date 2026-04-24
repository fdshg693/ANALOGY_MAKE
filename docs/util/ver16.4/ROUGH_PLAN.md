---
workflow: quick
source: issues
---

# ver16.4 ROUGH_PLAN — costs.py `extract_model_name` を「最大 cost の model」ベースに修正

ver16.3 RETROSPECTIVE §3.5 A-6 で発見した cost tracking の軽微バグ（sidecar `model` フィールドが primary model を指さず、先頭 key に依存して sub-tool の haiku を拾う問題）を解消する minor 版。handoff で示された「起票 → review → ready の流れを踏む」方針に従い、本 `/issue_plan` の review フェーズで新規 ISSUE 2 件を `ready / ai` に昇格させた上で、`costs-representative-model-by-max-cost` を ver16.4 の単一主眼として選定する。

## ISSUE 状態サマリ

| status / assigned | 件数 |
|---|---|
| ready / ai | 5 |
| review / ai | 0 |
| need_human_action / human | 0 |
| raw / human | 0 |
| raw / ai | 2 |

出典: `python scripts/issue_status.py util`（本 review フェーズ適用後の状態）。直前（ver16.3 時点）は `ready/ai=3, raw/ai=3`。本 review で `raw/ai` から 1 件 (`issue-review-long-carryover-redemotion`) が `ready/ai` に昇格、本版新規作成の `costs-representative-model-by-max-cost` が `review/ai` を経て `ready/ai` に昇格、合計 +2 件。

## ISSUE レビュー結果

- ready/ai に遷移: 2（`ISSUES/util/low/costs-representative-model-by-max-cost.md` / `ISSUES/util/low/issue-review-long-carryover-redemotion.md`）
- need_human_action/human に遷移: 0
- 追記した `## AI からの依頼`: 0（両件とも具体性条件を満たすため降格理由が無い）

選定理由・除外理由の詳細は `PLAN_HANDOFF.md` に記載。

## バージョン種別の判定

**マイナー（ver16.4）**。根拠:

- MASTER_PLAN 新項目（PHASE9.0 骨子）には着手しない（ver16.3 RETROSPECTIVE §3 と handoff で「時期尚早」と判定済み）
- アーキテクチャ変更・新規外部ライブラリ導入・破壊的変更いずれも無し
- 実装スコープは「既存関数 1 個の挙動修正 + 既存テスト更新」で完結

## ワークフロー選択

**`quick`（3 step）**。根拠:

- 選定 ISSUE は本 review 通過後すべて `ready / ai`（`review` 持ち越しなし）
- 変更対象は `scripts/claude_loop_lib/costs.py` 本体（1 関数 + docstring）と `scripts/tests/test_costs.py`（2 テスト修正 + 2〜3 テスト追加）の 2 ファイル、合計 30 行以下の見込み。quick 閾値「3 ファイル以下・100 行以下」を明確に下回る
- `research` 4 条件（外部仕様確認 / 実装方式実験 / 長時間検証 / 隔離環境試行）はいずれも該当しない。仕様は ver16.2 RESEARCH.md および ver16.3 RETROSPECTIVE §3.5 で確定済、実装方式も「`max(modelUsage.items(), key=…)`」で機械的に決まる
- `full` を選ぶ余地: 本版は `/retrospective` step を含まないため、次 run で発火観察が必要な項目（後述）は handoff 経由で ver16.5 以降に委ねる

## 着手スコープ

### 主眼: `extract_model_name` を「最大 cost の model」ベースに修正

対象 ISSUE: `ISSUES/util/low/costs-representative-model-by-max-cost.md`

実施内容の骨子:

- `scripts/claude_loop_lib/costs.py::extract_model_name`（現状 L149-156）を、`modelUsage` 内の各 entry の `costUSD` を参照し最大値の key を返す実装に変更する
- `modelUsage` の entry が空 / 非 dict / `costUSD` 欠落 / 全 entry 0 等のエッジケースでの挙動を関数 docstring に明文化する（`str | None` という戻り値仕様自体は不変）
- 既存テスト `scripts/tests/test_costs.py::TestExtractModelName::test_picks_first_model_key` を「最大 cost の model を返す」趣旨に名前ごと差し替え、エッジケース 2〜3 本を追加する

本版では**提供機能の変更**として、sidecar JSON および log 1 行サマリに記録される `model` フィールドが「当該 step で実コストの大半を占めた model」を指すようになる。retrospective で「どの step でどの model を使ったか」を sidecar から素早く把握する運用が初めて成立する。

### やらないこと（本版スコープ外）

- `modelUsage` を重み付きスコア（トークン数 × 単価等）で多次元評価する高度化 — `costUSD` 単独で十分
- `model` フィールドを `primary_model` / `all_models` に分割するなどの schema 変更 — 本 ISSUE のスコープ外
- `total_cost_usd` フォールバック経路（`cost_source: "fallback_price_book"`）の振る舞い見直し — ver16.3 で `cli` 100% 確認済み、未発動のため据え置き
- もう 1 件の ready/ai に昇格させた `issue-review-long-carryover-redemotion` の SKILL 拡張実装 — SKILL 本体書き換えを伴うため本版と並行せず将来版（ver16.5 以降）に委ねる
- ver16.3 から持ち越しの長期据え置き 3 件（`deferred-resume-twice-verification` / `issue-review-rewrite-verification` / `toast-persistence-verification`）の個別消化
- PHASE9.0 骨子作成
- `experiment_test` / `imple_plan` の effort / model 調整（sample 不足、据え置き）

## 成果物（想定）

- `docs/util/ver16.4/ROUGH_PLAN.md` — 本ファイル
- `docs/util/ver16.4/PLAN_HANDOFF.md` — quick-tier（2 節）
- `docs/util/ver16.4/IMPLEMENT.md` — `/quick_impl` step で生成。実装詳細（修正対象行・テスト更新方針）を記録
- `docs/util/ver16.4/MEMO.md` — `/quick_impl` step の実装メモ・残課題（quick では wrap_up 相当を含む）
- `docs/util/ver16.4/CHANGES.md` — 前版 (ver16.3) からの変更差分（`costs.py` 挙動変更、ISSUE 2 件 ready/ai 昇格、新規 ISSUE 1 件追加）
- `ISSUES/util/low/costs-representative-model-by-max-cost.md` — 本 `/issue_plan` で新規作成済（`ready/ai`）
- `ISSUES/util/low/issue-review-long-carryover-redemotion.md` — 本 `/issue_plan` で `raw/ai → ready/ai` に昇格済（frontmatter のみ変更）

`RESEARCH.md` / `EXPERIMENT.md` / `CURRENT.md` / `REFACTOR.md` / `RETROSPECTIVE.md` は `quick` workflow につき生成しない。

## 事前リファクタリング要否

**不要**。`extract_model_name` は単一関数・内部仕様が局所的で、修正前に分離しておくべき責務の重複は見当たらない。呼び出し元（`build_step_cost` 経由の sidecar 書き出し）も戻り値の型（`str | None`）が不変のため影響を受けない。
