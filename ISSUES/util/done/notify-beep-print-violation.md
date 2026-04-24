---
status: done
assigned: ai
priority: low
reviewed_at: 2026-04-24
---

# `_notify_beep` の `print()` 直接使用（scripts.md §5 違反）

## 概要

`scripts/claude_loop_lib/notify.py::_notify_beep` は `print("\a")` / `print(f"...")` を直接呼んでおり、`.claude/rules/scripts.md` §5「`print()` を直接使わず `logging_utils` 経由を使う」に違反している。

ver15.4 で `notify_completion` の API を `RunSummary` ベースに変更した際、fallback 経路の出力レイヤ書き換えはスコープ過大として意図的に持ち越した。

## 背景・制約

`_notify_beep` は `TeeWriter` コンテキスト外（通知はワークフロー終了後に発火）で呼ばれるため、現行の `logging_utils.TeeWriter.write_line` はそのまま使えない。差し替えには「TeeWriter コンテキストなしでも使える stderr 出力ヘルパ」を `logging_utils` に追加する前提作業が必要。

## 対応方針

1. `logging_utils.py` に `write_stderr(line: str)` 等の軽量ヘルパを追加（`print(line, file=sys.stderr)` ラッパーで十分）
2. `_notify_beep` の `print(...)` を `write_stderr(...)` 経由に差し替え
3. テストは既存 `test_notify.py` の fallback テストで beep 出力先が stderr になることを確認

## 影響範囲

- `scripts/claude_loop_lib/notify.py::_notify_beep`（4 行）
- `scripts/claude_loop_lib/logging_utils.py`（ヘルパ追加）
- `scripts/tests/test_notify.py`（fallback テストのアサート修正が必要な場合）

## 関連

- `.claude/rules/scripts.md` §5
- `docs/util/ver15.4/MEMO.md` §後続バージョンへの申し送り
