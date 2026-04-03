# MEMO: ver1.0 Hooks 設定の修正

## 計画との乖離

### `.claude/` ディレクトリへの書き込み制限
- **乖離内容**: IMPLEMENT.md では直接 `.claude/hooks/permission_handler.py` と `.claude/settings.local.json` を編集する計画だったが、Claude Code の保護ディレクトリ制限により AI から直接書き込みできなかった
- **対処**: ステージングディレクトリ `_staged_hooks/` にファイルを準備し、インストールスクリプト `install.sh` とリクエストファイル `REQUESTS/AI/hooks_install_request.md` を作成した
- **ユーザーアクション必要**: `bash _staged_hooks/install.sh` の実行が必要
- **wrap_up 対応**: ⏭️ 対応不要（記録事項。ステージング方式への変更は実施済み）

## 動作確認についての注記

### `$CLAUDE_PROJECT_DIR` 環境変数
- Windows 環境でこの環境変数が展開されるかは未確認
- 展開されない場合、`settings.local.json` の hook command を絶対パスに変更する必要あり（`REQUESTS/AI/hooks_install_request.md` に記載済み）
- **wrap_up 対応**: 📋 先送り — インストール実行後に検証が必要。`ISSUES/util/medium/hooks_env_var_verification.md` に起票済み

### `permissions.allow` による `.claude` 保護の上書き
- IMPLEMENT.md のリスク項目として記載されていた不確実性が残る
- `Edit(/.claude/**)` / `Write(/.claude/**)` が `bypassPermissions` モードの保護を上書きできるかは、インストール後に実環境で確認が必要
- 上書きできない場合は、`PreToolUse` フックでの対応を検討（IMPLEMENT.md ステップ 3c 参照）
- **wrap_up 対応**: 📋 先送り — インストール実行後に検証が必要。`ISSUES/util/medium/hooks_env_var_verification.md` に起票済み

## 残タスク

- インストールスクリプト実行後、`_staged_hooks/` ディレクトリの削除
- 動作確認（手動モード・自動化モード）の実施
- `REQUESTS/AI/hooks_install_request.md` のクローズ
- **wrap_up 対応**: 📋 先送り — 全てインストール実行後のタスク。`ISSUES/util/medium/hooks_post_install_tasks.md` に起票済み

## 削除推奨

- インストール完了後: `_staged_hooks/` ディレクトリ
- 動作確認完了後: `REQUESTS/AI/hooks_install_request.md`
- **wrap_up 対応**: 📋 先送り — 上記「残タスク」に含まれる
