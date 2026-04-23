---
status: raw
assigned: ai
priority: low
---
# `system_prompt` 利用時の Claude Code 既定挙動消失リスク

## 概要

ver10.0 で workflow YAML の step / defaults に `system_prompt` キーを追加した。
この値は `--system-prompt` フラグとして渡され、Claude Code のデフォルト system prompt を **完全置換** するため、CLAUDE.md 自動読込みなど Claude Code の既定挙動が失われる可能性がある。

## 本番発生時の兆候

- `system_prompt` を指定した step で CLAUDE.md のルールが効いていない挙動（指示無視、メモリ不参照など）が観察される
- `--system-prompt` を渡した場合、Claude Code が CLAUDE.md を読み込まずに実行する

## 対応方針

1. **予防策（実装済み）**: `scripts/README.md` §「override 可能なキー」に「通常は `append_system_prompt` を使うこと」の注記を追加済み
2. **発生時の対応**: YAML の `system_prompt` を `append_system_prompt` に置き換えるか削除する
3. **ver10.0 では実値投入なし**（既存 3 本 YAML に `system_prompt` を書いていない）ため、利用者が能動的に書いた場合のみ顕在化する

## 影響範囲

- `scripts/claude_loop_lib/commands.py` の `build_command()` が生成する `--system-prompt` フラグ
- 利用者が YAML に `system_prompt` を明示指定した step のみ

## 由来

- `docs/util/ver10.0/IMPLEMENT.md` §5-4（リスク・不確実性 5-4）
- `docs/util/ver10.0/MEMO.md` で「検証先送り」と記録、`ISSUES/util/low/` に追加済み（wrap_up 対応）
