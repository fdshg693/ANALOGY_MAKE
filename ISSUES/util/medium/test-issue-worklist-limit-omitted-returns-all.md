---
status: raw
assigned: ai
priority: medium
origin: pre-existing
---
# TestIssueWorklist.test_limit_omitted_returns_all が失敗（pre-existing）

## 概要

`tests/test_claude_loop.py` の `TestIssueWorklist.test_limit_omitted_returns_all` が
ver10.0 以前から失敗している（git stash 状態でも再現確認済み）。
テストスイートに既知の失敗が混在するとリグレッションの検出精度が低下するため修正が必要。

## 失敗内容

```
FAIL: test_limit_omitted_returns_all (tests.test_claude_loop.TestIssueWorklist)
AssertionError: assert "total" not in payload
```

`--limit` を省略した場合に `payload` に `total` キーが含まれないことを期待しているが、
実際には含まれている。

## 調査方針

1. `issue_worklist.py` の `--limit` 省略時の出力フォーマットを確認
2. テスト側が意図している仕様（`total` キーなし）と実装側の仕様（`total` キーあり）のどちらが正しいかを確認
3. 仕様に合わせてテストまたは実装を修正

## 影響範囲

- `tests/test_claude_loop.py` の `TestIssueWorklist` クラス
- `scripts/issue_worklist.py` の JSON 出力フォーマット（変更が必要な場合）

## 由来

- `docs/util/ver10.0/MEMO.md` §既知の問題 に記録済み（ver10.0 での修正はスコープ外）
- `python -m unittest tests.test_claude_loop` 実行時に常に 1 件失敗として報告される
