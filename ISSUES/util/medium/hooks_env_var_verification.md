# Hooks 設定: インストール後の検証事項

## 関連
- `ISSUES/util/high/HOOKS設定.md`（親課題）
- `docs/util/ver1.0/IMPLEMENT.md`（実装計画）

## 検証項目

### 1. `$CLAUDE_PROJECT_DIR` 環境変数の展開
- `settings.local.json` の hook command で `$CLAUDE_PROJECT_DIR` を使用している
- Windows 環境でこの変数が正しく展開されるか未確認
- **展開されない場合の対処**: 絶対パス `C:/CodeRoot/ANALOGY_MAKE/.claude/hooks/permission_handler.py` に変更

### 2. `permissions.allow` による `.claude` 保護の上書き
- `Edit(/.claude/**)` / `Write(/.claude/**)` が `bypassPermissions` モードの保護を上書きできるか未確認
- **上書きできない場合の対処**: `PreToolUse` フックでの対応を検討（IMPLEMENT.md ステップ 3c 参照）

## 前提条件
`bash _staged_hooks/install.sh` の実行が完了していること
