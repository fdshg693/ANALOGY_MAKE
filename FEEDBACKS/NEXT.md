FEEDBACKS\NEXT.md
`test-issue-worklist-limit-omitted-returns-all.md` を消化して

1. **スコープ**: ISSUE 本文に従い、`limit` パラメータ省略時の挙動を「全件返す」ことを確定する仕様として固める。関数シグネチャ・テスト期待値の片側に合わせる単体作業
2. **変更対象想定**: `scripts/claude_loop_lib/issues.py`（`issue_worklist` 関数の `limit` 既定値ハンドリング）+ `scripts/tests/test_issue_worklist.py`（`test_limit_omitted_returns_all` の期待値）
3. **ver12.0 validation との相互作用**: `validate_startup()` 自体は `issue_worklist` を呼ばないため、validation regression 懸念なし。既存 `TestValidateStartupExistingYamls` は引き続き通過することを確認