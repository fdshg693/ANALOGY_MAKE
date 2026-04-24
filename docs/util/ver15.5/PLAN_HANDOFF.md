---
workflow: quick
source: issues
---

# ver15.5 PLAN_HANDOFF — `/quick_impl` 向け引き継ぎ

## 関連 ISSUE / 関連ファイル

### 着手 ISSUE（実施対象）

- `ISSUES/util/low/notify-beep-print-violation.md`
- `ISSUES/util/low/auto-loop-count-semantics.md`

### 関連ファイル（編集予定）

- `scripts/claude_loop_lib/logging_utils.py` — stderr 出力ヘルパを新設（例: `write_stderr(line: str) -> None` を `print(line, file=sys.stderr)` のラッパとして追加）
- `scripts/claude_loop_lib/notify.py` — `_notify_beep` 内の `print("\a")` および `print(f"...")` 4 行を新ヘルパ経由に置換。`from claude_loop_lib.logging_utils import write_stderr` を追加
- `scripts/claude_loop.py` — `_run_auto`（line 314 周辺）で phase1 の `RunStats` 合算時に `completed_loops` を除外。`completed_steps` は両 phase 合算のまま維持
- `scripts/tests/test_notify.py` — fallback 経路のテストで出力先が stderr であることを `capsys.readouterr().err` でアサート
- `scripts/tests/test_claude_loop_integration.py` — `--workflow auto --max-loops 1` 実行時に `loops_completed == 1`（= phase2 の loop 数のみ）であることをアサート

### 参照ファイル（編集対象外、判断材料）

- `.claude/rules/scripts.md` §5（`print()` 直接使用禁止規約の一次資料）
- `docs/util/ver15.4/MEMO.md` §後続バージョンへの申し送り（先送り 2 件の詳細記録）
- `docs/util/ver15.4/IMPLEMENT.md` §通知改修の R1〜R3（fallback 3 段構造の前提）
- `scripts/claude_loop_lib/notify.py::RunSummary.message()`（loop 数表示の出力点）

## 後続 step への注意点

### A. `_run_auto` 合算実装の選択肢

ISSUE 本文に 2 案が示されている。`/quick_impl` 側で最終決定すること:

- **案1（推奨）**: `_run_auto` 内で `combined.completed_loops += phase2_stats.completed_loops` のように直接記述し、phase1 を加算対象から外す。`completed_steps` は両 phase 加算を維持。
- **案2**: `RunStats.merge` に `exclude_loops=True` オプションを追加し、phase1 合算時のみ loops を加えない。

案1 は `_run_auto` 内に局所化されるが `RunStats.merge` ヘルパを使わない例外パターンを生む。案2 は API が肥大化するが対称性が保てる。**現状 `RunStats.merge` の呼び出し元が `_run_auto` の 1 箇所のみ**であれば案1 を推奨（不要な抽象化を避けるため）。`/quick_impl` の「現状の再確認」節で `merge` の呼び出し回数を確認した上で確定すること。

### B. `_notify_beep` の TeeWriter コンテキスト外問題

`_notify_beep` は workflow 終了後の通知失敗時 fallback で呼ばれるため、`TeeWriter` インスタンスが scope 外にある。stderr ヘルパは TeeWriter 非依存にすること（モジュールレベル関数 + `import sys` のみで完結する形）。`logging_utils.py` 既存の `TeeWriter.write_line` と混同しないよう、関数名は明確に分けること（例: `write_stderr` / `print_stderr`）。

### C. テスト方針

- `test_notify.py` の fallback テストは現行 stdout を見ているはず。stderr に変わる前後でアサート差分を最小に抑えること
- `test_claude_loop_integration.py` の auto モードテストは現行で loop 数アサートが無い可能性が高い。新規アサート追加で済むか、既存値を補正する必要があるかは `/quick_impl` で実コード確認すること

### D. ver15.4 の R1（toast 永続表示の実機検証）は本バージョンスコープ外

`toast-persistence-verification.md` は ROUGH_PLAN で明示的に除外している。`/quick_impl` で `notify.py` を触るタイミングで「ついで対応」として手を入れないこと。本 ISSUE は別経路（開発者対面セッション）で消化する方針。

### E. quick ワークフロー省略判断のトラッキング材料

`plan-handoff-omission-tracking.md`（観察 ISSUE）の観察対象として、本ループは「PLAN_HANDOFF.md 省略しない判断」を選択した（quick だが後続 step への判断材料が複数あるため省略不可）。retrospective でこの判断を 1 ケースとして記録すること。
