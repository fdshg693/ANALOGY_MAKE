# Hooks 設定: インストール後の残タスク

## 関連
- `ISSUES/util/high/HOOKS設定.md`（親課題）

## タスク一覧

### 1. 動作確認
- 手動モードで AskUserQuestion のパーミッションダイアログが表示されること
- 手動モードでファイル編集が自動許可されること
- 自動化モード（`-p` フラグ）で `.claude` 配下のファイル編集が成功すること

### 2. クリーンアップ
- `_staged_hooks/` ディレクトリの削除
- `REQUESTS/AI/hooks_install_request.md` のクローズ（削除）

## 前提条件
`bash _staged_hooks/install.sh` の実行が完了していること
