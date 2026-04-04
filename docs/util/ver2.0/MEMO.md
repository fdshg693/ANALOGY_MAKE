# MEMO: util ver2.0

## 計画との乖離

なし。IMPLEMENT.md の計画通りに実装した。

## 実装メモ

### ワークフロー名の取得

ログヘッダーの `Workflow:` 行では、ワークフロー名を `log_path.stem.split('_', 2)[-1]` で取得している。
ログファイル名が `20260404_143000_claude_loop.log` の場合、`claude_loop` が抽出される。
`_run_steps()` は `args.workflow` を直接受け取らないため、log_path から逆算する方式を採用した。
より直接的にするなら `workflow_name` を引数に追加する方法もあるが、現状で正しく動作するため据え置き。

### Python テストの追加

既存の Python テストファイルがなかったため、`tests/test_claude_loop.py` を新規作成した。
`unittest` を使用（pytest 未インストールのため）。`python -m unittest` で実行可能。

### 更新が必要そうなドキュメント

- `docs/util/ver2.0/CURRENT.md`: 今回のログ機能追加に伴うファイル構成・関数一覧の更新が必要

## wrap_up 対応結果

| # | 項目 | 対応 | 詳細 |
|---|---|---|---|
| 1 | ワークフロー名の取得 | ⏭️ 対応不要 | 設計判断の記録であり、コードは正しく動作している。ISSUES 登録不要（MEMO に記録済みで十分） |
| 2 | Python テストの追加 | ⏭️ 対応不要 | テスト基盤整備の情報メモ。テストは実装済み・動作確認済み |
| 3 | CURRENT.md の更新 | ✅ 対応完了 | `docs/util/ver2.0/CURRENT.md` を新規作成。ver2.0 で追加されたログ機能（TeeWriter, create_log_path, get_head_commit 等）、テストファイル構成、ログフォーマット仕様を反映 |
