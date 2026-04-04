# MEMO: util ver2.1

## 実装メモ

- 計画との乖離なし。IMPLEMENT.md の実装順序・設計通りに実装完了。

## 残課題・気づき

- `_notify_toast()` は Windows 専用実装。macOS/Linux 対応は現時点でスコープ外（デプロイ先は Azure Linux だが、`claude_loop.py` は開発マシン上で実行するためWindows前提で問題なし）。
- `_run_steps()` 内の `workflow_start` と `main()` 内の `workflow_start` が二重に存在する。`_run_steps()` 内のものはログ出力用（Duration 行）、`main()` 内のものは通知用。機能的に正しいが、将来リファクタリングで一本化を検討してもよい。

## wrap_up 対応結果

- ⏭️ **`_notify_toast()` Windows専用**: 対応不要 — `claude_loop.py` は開発マシン（Windows）上で実行するツールであり、クロスプラットフォーム対応は不要。フォールバック (`_notify_beep`) も実装済み。
- ⏭️ **`workflow_start` 二重定義**: 対応不要 — `_run_steps()` 内（ログ Duration 用）と `main()` 内（通知 Duration 用）で目的が異なり、機能的に正しい。計測タイミングの微差は実用上問題なし。低優先度のリファクタリング候補だが ISSUES 登録不要。
- ✅ **品質チェック**: typecheck 通過（vue-router volar 警告は既知）、未使用 import/変数なし。
