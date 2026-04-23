# ver12.1 MEMO

## 計画からの乖離

乖離なし。ROUGH_PLAN の「`scripts/issue_worklist.py` の `main()` 内で `total = len(items)` を `if limit is not None:` ブロック内に移動する」方針を 3 行の変更で実現。

## 変更内容

`scripts/issue_worklist.py` の `main()` 関数:

```python
# 変更前
total = len(items)
limit: int | None = args.limit
if limit is not None:
    items = items[:limit]

# 変更後
limit: int | None = args.limit
total: int | None = None
if limit is not None:
    total = len(items)
    items = items[:limit]
```

これにより `format_json()` へ渡す `total` が `--limit` 省略時は `None` となり、`if total is not None:` ガードが正しく機能する。

## テスト結果

- `test_limit_omitted_returns_all`: **OK**（pre-existing 失敗が解消）
- `TestIssueWorklist` 全 13 ケース: OK
- `TestValidation` / `TestValidateStartupExistingYamls` / `TestAutoWorkflowIntegration` など 65 ケース: OK（regression なし）

## FEEDBACKS/NEXT.md の処理

`FEEDBACKS/NEXT.md` は `claude_loop.py` が正常完了後に `FEEDBACKS/done/` へ移動する想定のため、このステップでは移動しない。
