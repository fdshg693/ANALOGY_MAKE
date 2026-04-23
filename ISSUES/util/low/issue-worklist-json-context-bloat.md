---
status: done
assigned: ai
priority: low
reviewed_at: "2026-04-23"
---
# `issue_worklist.py --format json` の出力肥大化時の件数制限対応

## 概要

`/issue_plan` の SKILL コンテキスト先頭で `!` バックティック展開により `python scripts/issue_worklist.py --format json` を実行する。カテゴリによっては `ready / review` の ISSUE が多数あり、トークンを消費して想定外のコンテキスト肥大化を招く可能性がある。

ver8.0 時点では util カテゴリで 1 件、app カテゴリで 6 件程度のため問題ないが、将来的に ISSUE が積み上がった場合の対策として `--limit` オプションの追加を検討する。

## 本番発生時の兆候

- `/issue_plan` 実行時のプロンプト長が想定外に膨らむ
- ISSUE 選定時に AI が全件走査できず、優先度の低い ISSUE が拾われる
- `logs/workflow/*.log` でステップ開始前のコンテキストサイズが急増

## 対応方針

1. `scripts/issue_worklist.py` に `--limit N` オプション（デフォルト 20 件程度）を追加
2. `--limit` 省略時は現行動作（全件）を維持
3. `/issue_plan` SKILL のコンテキスト行を `issue_worklist.py --format json --limit 20` に更新
4. priority 順（high → medium → low）で上位から切り出すため `issue_worklist.py` のソート順を保証

## 影響範囲

- `scripts/issue_worklist.py`
- `scripts/claude_loop_lib/issues.py`（共通ヘルパ側の変更が必要か要確認）
- `.claude/skills/issue_plan/SKILL.md` のコンテキスト行
- `tests/test_claude_loop.py` の `--limit` 分岐テスト追加

## 出典

`docs/util/ver8.0/IMPLEMENT.md` §9 R5（検証先送り）
