---
workflow: quick
---

# ver16.4 IMPLEMENT — `extract_model_name` 最大 cost モデル返却に修正

## 修正対象

### `scripts/claude_loop_lib/costs.py::extract_model_name`（L149-168）

**変更前**: `modelUsage` dict の最初の key をループで返す実装。Python dict の挿入順に依存するため、CLI が haiku を先に挿入すると実コストが opus でも haiku が「代表 model」として返されるバグがあった。

**変更後**: `max()` + ラムダで `costUSD` 最大の key を返す実装。

```python
def _cost(entry: Any) -> float:
    if isinstance(entry, dict):
        v = entry.get("costUSD")
        if isinstance(v, (int, float)):
            return float(v)
    return 0.0

return max(model_usage, key=lambda k: _cost(model_usage[k]))
```

docstring を「最高 costUSD の key を返す」に更新し、エッジケース挙動（欠落→0扱い、同値→先頭、空→None）を明記。

### `scripts/tests/test_costs.py::TestExtractModelName`

| テスト | 対応 |
|---|---|
| `test_picks_first_model_key` | 削除（→ `test_returns_max_cost_model` に差し替え）|
| `test_returns_none_when_absent` | 維持（`{}` → `None`）|
| `test_returns_max_cost_model` | **新規**（2 model、haiku vs opus、最大 cost 側を返す）|
| `test_single_key_returned` | **新規**（SAMPLE_RESULT_SUCCESS の単一 key → `"claude-opus-4-7"`）|
| `test_missing_cost_usd_treated_as_zero` | **新規**（costUSD 欠落 entry は 0 扱い、正値 entry が勝つ）|
| `test_empty_model_usage_returns_none` | **新規**（`{"modelUsage": {}}` → `None`）|

TestExtractModelName は 2 テスト → 5 テストに増加。全体テスト数: 142 → 145。

## 実行結果

`pnpm test` 実行結果: **145 passed / 0 failed**（全テスト PASS）。

`npx nuxi typecheck` は本修正が Python ファイルのみの変更であるため不適用（TypeScript 変更なし）。
