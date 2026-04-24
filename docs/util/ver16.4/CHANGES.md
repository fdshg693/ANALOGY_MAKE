---
workflow: quick
---

# ver16.4 CHANGES — ver16.3 からの変更差分

## コード変更

### `scripts/claude_loop_lib/costs.py`

- `extract_model_name`（L149-168）: `modelUsage` の先頭 key を返す実装 → `costUSD` 最大の key を返す実装に変更
- docstring 更新: 「first key」から「最高 costUSD の key」に修正、エッジケース挙動（空/欠落/非数値→0扱い、同値→先頭）を明記
- **影響**: sidecar `model` フィールドが「実コストの大半を占めた model」を指すようになる。呼び出し元の戻り値型（`str | None`）は不変

### `scripts/tests/test_costs.py`

- `TestExtractModelName::test_picks_first_model_key` → `test_returns_max_cost_model` に名前・内容とも差し替え
- 追加テスト 3 本: `test_single_key_returned` / `test_missing_cost_usd_treated_as_zero` / `test_empty_model_usage_returns_none`
- テスト数: 142 → 145（+3）

## ISSUE 状態変化

| ISSUE | 変化 |
|---|---|
| `ISSUES/util/low/costs-representative-model-by-max-cost.md` | ready/ai → **done** |
| `ISSUES/util/low/issue-review-long-carryover-redemotion.md` | raw/ai → **ready/ai**（issue_plan フェーズで昇格、本版では着手せず） |

issue_plan フェーズでの ISSUE 状態サマリ（ver16.3 → ver16.4 開始時）: ready/ai=3→5, raw/ai=3→2。

## ドキュメント追加

- `docs/util/ver16.4/ROUGH_PLAN.md`
- `docs/util/ver16.4/PLAN_HANDOFF.md`
- `docs/util/ver16.4/IMPLEMENT.md`
- `docs/util/ver16.4/MEMO.md`
- `docs/util/ver16.4/CHANGES.md`（本ファイル）
