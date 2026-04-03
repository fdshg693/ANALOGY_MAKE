# MEMO: util ver2.1

## 実装メモ

- 計画との乖離なし。IMPLEMENT.md の実装順序・設計通りに実装完了。

## 残課題・気づき

- `_notify_toast()` は Windows 専用実装。macOS/Linux 対応は現時点でスコープ外（デプロイ先は Azure Linux だが、`claude_loop.py` は開発マシン上で実行するためWindows前提で問題なし）。
- `_run_steps()` 内の `workflow_start` と `main()` 内の `workflow_start` が二重に存在する。`_run_steps()` 内のものはログ出力用（Duration 行）、`main()` 内のものは通知用。機能的に正しいが、将来リファクタリングで一本化を検討してもよい。
