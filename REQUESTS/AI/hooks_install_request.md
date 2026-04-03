# Hooks 設定ファイルのインストール依頼

## 状況

`.claude/` ディレクトリは保護されているため、AI から直接ファイルを書き込めませんでした。
ステージングディレクトリ `_staged_hooks/` にファイルを準備しました。

## インストール方法

以下のコマンドを実行してください:

```bash
bash _staged_hooks/install.sh
```

## 変更内容

### 1. `.claude/hooks/permission_handler.py`（新規作成）
- AskUserQuestion 以外の全ツールを自動許可する Python スクリプト
- AskUserQuestion は自動許可せず、通常のパーミッションダイアログを表示

### 2. `.claude/settings.local.json`（更新）
- `hooks.PermissionRequest`: インライン echo → 外部 Python スクリプト呼び出しに変更
- `permissions.allow`: `Edit(/.claude/**)` と `Write(/.claude/**)` を追加（自動化モードでの .claude 編集対応）

## インストール後の確認

1. Claude Code を手動起動して、質問を促す操作をする → AskUserQuestion のパーミッションダイアログが表示されるか
2. ファイル編集操作 → 自動許可されるか

## 注意事項

- `$CLAUDE_PROJECT_DIR` 環境変数が Windows で展開されない場合、`settings.local.json` の hook command を絶対パスに変更してください:
  ```
  "command": "python \"C:/CodeRoot/ANALOGY_MAKE/.claude/hooks/permission_handler.py\""
  ```
- インストール後、`_staged_hooks/` ディレクトリは削除して構いません
