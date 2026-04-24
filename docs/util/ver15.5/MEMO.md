# ver15.5 MEMO

## 実装メモ

### 案1 vs 案2 の選択（auto-loop-count-semantics）

PLAN_HANDOFF §A の通り、`RunStats.merge` の呼び出し元が `_run_auto` 内のみであることを確認し、案1（`_run_auto` 内でphase1を `merge` せず手動集計）を採用。`completed_loops` のみ除外し、`completed_steps` と `failed_step` は手動で転写。`workflow_label` は後続で上書きされるため転写不要。

### `_notify_beep` の print 行数

ISSUE・PLAN_HANDOFF は「4 行」と記載していたが、実際のファイルでは5行（`\a` + separator×2 + title + message）。全行 `write_stderr` に置換した。

### テスト追加の判断

- `test_notify.py`: `_notify_beep` をモック経由でのみテストしていた既存テストとは分離し、`TestNotifyBeep` クラスを新設。stdout に出力されないことも確認。
- `test_claude_loop_integration.py`: `notify_completion` をパッチして `RunSummary` を捕捉する方式を採用（`--no-notify` を外すことで実現）。`_find_latest_rough_plan` もパッチ済みのため、phase1でRough Planが生成されない統合テスト環境でも正常動作。

## 未対応項目

なし（本バージョンスコープはすべて解消済み）。
