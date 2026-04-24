---
status: done
assigned: ai
priority: low
reviewed_at: 2026-04-24
---

# `--workflow auto` の loop カウント意味論（通知本文が過大表示される）

## 概要

`_run_auto` は phase1（`claude_loop_issue_plan.yaml` の 1 step）と phase2（full/quick）の `RunStats` を単純合算している。phase1 は 1 step・1 YAML なので `absolute_index == total_steps` 判定が成立し、「1 loop 完了」としてカウントされる。

`--max-loops 1` で `auto` を 1 回実行しても、通知本文に「2 loops」と表示される可能性があり、ユーザーが混乱しやすい。

## 再現条件

```bash
python scripts/claude_loop.py --workflow auto --max-loops 1
```

通知本文が `auto(full) / 2 loops / 7 steps / Xm Ys` のように phase1 の 1 loop が加算された状態になる（期待値は `1 loop / 6 steps`）。

## 対応方針

`_run_auto` 内で phase1 の `RunStats.completed_loops` を合算対象から除外し、`auto` 実行時は phase2 の loop 数のみを `combined.completed_loops` とする。

実装例:
```python
combined.completed_loops += phase2_stats.completed_loops  # phase1 は除外
combined.completed_steps += phase1_stats.completed_steps + phase2_stats.completed_steps
```

または `RunStats.merge` に `exclude_loops=True` オプションを追加して phase1 合算時だけ loops を加えない。

## 影響範囲

- `scripts/claude_loop.py::_run_auto`（RunStats 合算ロジック）
- `scripts/tests/test_claude_loop_integration.py`（auto テストで loop 数アサート追加が必要）
- 通知本文の表示値のみ変わり、exit code / step 数 / duration には影響なし

## 関連

- `docs/util/ver15.4/MEMO.md` §後続バージョンへの申し送り「auto モードの loop カウント意味論」
- `scripts/claude_loop_lib/notify.py::RunSummary.message()`
