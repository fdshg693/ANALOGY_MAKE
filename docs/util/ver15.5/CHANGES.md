# ver15.5 CHANGES（vs ver15.4）

## 変更ファイル

### `scripts/claude_loop_lib/logging_utils.py`
- `import sys` を追加
- `write_stderr(line: str) -> None` を新設（`print(line, file=sys.stderr)` ラッパー）

### `scripts/claude_loop_lib/notify.py`
- `write_stderr` をインポートに追加
- `_notify_beep` の `print(...)` 5行を `write_stderr(...)` に置換（stdout → stderr）

### `scripts/claude_loop.py`
- `_run_auto` の phase1 `RunStats` 合算を `combined.merge(phase1_stats)` から手動集計に変更
  - `completed_loops` を除外（phase1 のループカウントは通知本文に含めない）
  - `completed_steps` と `failed_step` は引き続き集計

### `scripts/tests/test_notify.py`
- `_notify_beep` インポートを追加
- `TestNotifyBeep` クラスを新設（stderr出力確認・stdout非出力確認）

### `scripts/tests/test_claude_loop_integration.py`
- `TestAutoLoopCountSemantics` クラスを新設
  - auto モードで `loops_completed` が phase2 のみを反映することをアサート

## 解消した ISSUE

- `ISSUES/util/low/notify-beep-print-violation.md` → `status: done`
- `ISSUES/util/low/auto-loop-count-semantics.md` → `status: done`
