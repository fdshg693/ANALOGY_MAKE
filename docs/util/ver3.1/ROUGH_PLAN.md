# ROUGH_PLAN: util ver3.1

## 対応する ISSUE

- `ISSUES/util/medium/ログ一部エラー.md`

## 変更対象ファイル

1. `scripts/claude_loop.py` — コマンド文字列のログ出力修正
2. `tests/test_claude_loop.py` — 修正に対応するテスト更新

## 変更方針

### 原因

`_run_steps()` 内の `command_str = " ".join(command)`（489 行目付近）が、スペースを含む引数をクォートせずに結合している。
これにより、ログの `$ {command_str}` 行で auto_args の `--append-system-prompt` の値（長文システムプロンプト）と、`build_command()` が追加する 2 つ目の `--append-system-prompt`（ログパス）の境界が判別できない。

### 修正内容

- `" ".join(command)` を `shlex.join(command)` に変更する（Python 3.8+ で利用可能）
- `shlex.join()` はスペースや特殊文字を含む引数を自動的にシェルクォートするため、ログ出力でコマンドの構造が明確になる

### テスト方針

- 既存テストの `command_str` を検証している箇所があれば、クォート付き出力に合わせて更新
- `shlex.join()` 自体は標準ライブラリ関数のため、追加のユニットテストは不要
