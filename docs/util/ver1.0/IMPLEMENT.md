# IMPLEMENT: Hooks 設定の修正

## 概要

`ROUGH_PLAN.md` の 3 つの問題に対する実装計画。

## 変更対象ファイル

| ファイル | 操作 | 内容 |
|---|---|---|
| `.claude/hooks/permission_handler.py` | 新規作成 | PermissionRequest フック処理スクリプト |
| `.claude/settings.local.json` | 変更 | フックコマンドの外部スクリプト化 + permissions.allow 追加 |

## 実装手順

### ステップ 1: フック処理スクリプトの作成（問題 1 + 問題 3）

`.claude/hooks/permission_handler.py` を新規作成する。

**言語選定**: Python を使用する。理由:
- JSON パースが標準ライブラリで確実にできる（`jq` 不要）
- Windows 環境で bash スクリプトより動作が安定する
- プロジェクト内で既に Python を使用している（`scripts/claude_loop.py`）

**スクリプトのロジック**:

```python
#!/usr/bin/env python3
"""PermissionRequest hook handler.

Auto-allows all permission requests except AskUserQuestion.
AskUserQuestion は自動許可せず、通常のパーミッションダイアログを表示させる。
"""
import json
import sys


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # JSON パース失敗時は何もせず終了（通常のダイアログを表示）
        sys.exit(0)

    tool_name = data.get("tool_name", "")

    # AskUserQuestion は自動許可しない → ユーザーが回答できるようにする
    if tool_name == "AskUserQuestion":
        sys.exit(0)

    # それ以外のツールは自動許可
    result = {
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {
                "behavior": "allow"
            }
        }
    }
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
```

**動作の説明**:
- stdin から JSON を読み取り、`tool_name` を確認
- `AskUserQuestion` の場合: exit 0 で JSON を出力しない → Claude Code は通常のパーミッションダイアログを表示する
- それ以外の場合: `{"behavior": "allow"}` を出力 → Claude Code は自動的に許可する

### ステップ 2: settings.local.json の更新（問題 2 + 問題 3）

#### 2a: フックコマンドの外部スクリプト化

`hooks.PermissionRequest` のインラインコマンドを外部スクリプト呼び出しに変更する。

**変更前**:
```json
"hooks": {
    "PermissionRequest": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "echo '{\"hookSpecificOutput\": {\"hookEventName\": \"PermissionRequest\", \"decision\": {\"behavior\": \"allow\"}}}'"
          }
        ]
      }
    ]
  }
```

**変更後**:
```json
"hooks": {
    "PermissionRequest": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/permission_handler.py\""
          }
        ]
      }
    ]
  }
```

**`$CLAUDE_PROJECT_DIR` のフォールバック**: Windows 環境でこの環境変数が展開されない場合は、絶対パスに切り替える:
```json
"command": "python \"C:/CodeRoot/ANALOGY_MAKE/.claude/hooks/permission_handler.py\""
```

#### 2b: permissions.allow への `.claude` 編集許可の追加（問題 2）

**根本原因の特定**:

公式ドキュメントから以下が判明した:

> `bypassPermissions` モード（`--dangerously-skip-permissions`）は `.git`, `.claude`, `.vscode`, `.idea`, `.husky` ディレクトリへの書き込み時に確認プロンプトを表示する。ただし `.claude/commands`, `.claude/agents`, `.claude/skills` は例外で確認不要。

つまり `--dangerously-skip-permissions` を使用しても、`.claude/hooks/` や `.claude/settings.local.json` への書き込みは確認が必要。非対話モード（`-p`）ではこの確認に応答できないため、書き込みが失敗する。

**解決策**: `permissions.allow` に明示的なエントリを追加する。

Edit/Write の permission ルールは gitignore 仕様に準拠する（[公式ドキュメント](https://code.claude.com/docs/en/permissions)）:
- `/path` — プロジェクトルートからの相対パス
- `**` — ディレクトリを再帰的にマッチ

**追加するエントリ**:
```json
"permissions": {
    "allow": [
      ...既存エントリ...
      "Edit(/.claude/**)",
      "Write(/.claude/**)"
    ]
  }
```

**注意**: `permissions.allow` の `allow` ルールは、`bypassPermissions` モードの保護ディレクトリ制限をオーバーライドできるかどうかは公式ドキュメントで明示されていない。オーバーライドできない場合の代替案:
- `PreToolUse` フックを使用する（`PreToolUse` フックは `-p` モードでも発火し、`--dangerously-skip-permissions` でも発火する）
- `PreToolUse` フックで `permissionDecision: "allow"` を返すことで、保護ディレクトリ制限を回避できる可能性がある

### ステップ 3: 動作確認

以下のシナリオで動作確認を行う:

1. **手動モードで AskUserQuestion**: Claude Code を手動実行し、AI に質問を促す → パーミッションダイアログが表示されること
2. **手動モードで Edit/Write**: Claude Code を手動実行し、ファイル編集 → 自動許可されること
3. **自動化モードで `.claude` 編集**: 以下の手順で確認
   a. `claude_loop.py --dry-run` で引数を確認
   b. 手動で `claude -p "Edit .claude/test.txt with content 'test'" --dangerously-skip-permissions` を実行し、`.claude` 配下のファイル編集が成功するか確認
   c. 失敗した場合: `PreToolUse` フックへの切り替えを検討（代替案参照）

## リスク・不確実性

### `permissions.allow` が `bypassPermissions` の保護を上書きできるか

`bypassPermissions` モードの `.claude` ディレクトリ保護は、通常の deny/ask/allow ルールとは別の仕組みである可能性がある。`permissions.allow` のエントリがこの保護を上書きできるかは実装時に確認が必要。

**対処**: ステップ 3c で確認。上書きできない場合は `PreToolUse` フックで対応する。`PreToolUse` フックは全モード（`-p` 含む）で発火し、`--dangerously-skip-permissions` でも発火するため、確実な代替手段となる。

### Windows 環境でのフックスクリプト実行

Claude Code が Windows 上でフックコマンドを実行する際のシェルが不明（cmd.exe / PowerShell / Git Bash）。`python` コマンドのパス解決や `$CLAUDE_PROJECT_DIR` 環境変数の展開が正しく動作するか確認が必要。

**対処**: 実装後に `/hooks` ブラウザで設定を確認し、手動テストで動作を検証する。
- `$CLAUDE_PROJECT_DIR` が展開されない場合 → 絶対パスに切り替え（ステップ 2a のフォールバック参照）
- `python` が見つからない場合 → `python3` やフルパスに変更
