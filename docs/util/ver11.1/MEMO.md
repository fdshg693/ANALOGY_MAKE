# ver11.1 MEMO

## 乖離・判断事項

### S1: 物理ファイル移動なし（論理分離のみ）

ROUGH_PLAN の判断基準「決め手に欠ける場合は移動しない」を適用。
`.claude/rules/claude_edit.md` / `CLAUDE.md` / `scripts/README.md` 等の参照が `scripts/claude_sync.py` / `scripts/issue_status.py` 等をハードコードしており、物理移動すると更新コストが高い。
README のファイル一覧を「ワークフロー実行 / ISSUES 管理ツール / 補助ツール」の 3 グループに分けることで論理的分離を実現した。

### S3: ログ読解観点は USAGE.md のログフォーマット節に追記

概要（手動再開・エラー特定・セッション汚染）は README の「## ログの見方」に短く掲載し、詳細は USAGE.md の「### ログの読み方（トラブルシュート）」に記載。

## テスト結果

- `python -m unittest discover -s scripts/tests -t .`: 192 tests, 1 FAIL（`test_limit_omitted_returns_all` — pre-existing 失敗、ver11.0 末と同一）
- CLI 4 コマンドすべて `--help` レベルで正常起動を確認

## 今後の課題（ISSUES への転記不要）

- `test_limit_omitted_returns_all` は ver11.2 で単独処理予定（ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md）
