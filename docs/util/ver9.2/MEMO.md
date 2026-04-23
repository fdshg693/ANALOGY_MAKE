# MEMO: util ver9.2

## 実装完了

- `scripts/issue_worklist.py`: `--limit N` オプション追加（デフォルト `None` = 全件）
- `tests/test_claude_loop.py`: `--limit` 関連テスト 5 件追加（`TestIssueWorklist` クラスに追記）
- `.claude/skills/issue_plan/SKILL.md` (+ `.claude_sync/`): コンテキスト行を `--limit 20` 付きに更新

## ROUGH_PLAN との乖離

なし。計画通り実装完了。

## 備考

- `format_json()` に `total/truncated/limit` フィールドを追加したが、`--limit` 未指定時は省略（後方互換）
- `format_text()` は `total > limit` 時のみ末尾に `(showing first N of M issues)` 行を追加
- `collect()` は変更なし（スライスは `main()` で実施）
- テストはすべて既存 `TestIssueWorklist` クラスへの追記で対応（新規ファイル不要）
