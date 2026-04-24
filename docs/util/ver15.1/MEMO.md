# ver15.1 MEMO

## 実装メモ

### ROUGH_PLAN の `--category util` フラグについて

`ROUGH_PLAN.md` §後続 `/quick_impl` への引き継ぎメモ で示されたコマンド例 `python scripts/claude_loop.py --workflow scout --category util --max-loops 1` は、`--category` フラグが `claude_loop.py` に存在しないため実行時エラーになる。

カテゴリは `.claude/CURRENT_CATEGORY` ファイルで管理されており、すでに `util` に設定済みであったため、実際のコマンドは `python scripts/claude_loop.py --workflow scout --max-loops 1` で実行した。

**対応**: ROUGH_PLAN は計画ドキュメントのため修正不要。次バージョン以降の ROUGH_PLAN / handoff で同様の誤記が出ないよう、引き継ぎメモのコマンド例から `--category` フラグを省く慣習を採用すべき。ISSUES に起票するほどの重要度はないため、次の `/issue_scout` 起動時の自律探索に委ねる。

## scout 起票物のレビュー方針

scout が起票した 2 件は `raw / ai` のまま保持。次回 `/issue_plan` の ISSUE レビューフェーズで通常処理する（ROUGH_PLAN §引き継ぎメモの通り）。

- `medium/imple-plan-four-file-yaml-sync-check.md`: PHASE7.1 §2 着手前に `ready / ai` 昇格を検討する価値あり（YAML 追加が確実なため）
- `low/readme-workflow-yaml-table-missing-scout.md`: 既存 `scripts-readme-usage-boundary-clarification.md` との合流消化が合理的

## 後続バージョンへの引き継ぎ

- **PHASE7.1 §2（路線 B）**: `QUESTIONS/` + `question` workflow 新設。scout の挙動を確認済みのため着手可能。ver15.2 で `/issue_plan` → 適切なワークフロー選択。
- **`issue-review-rewrite-verification.md`**: `app` / `infra` カテゴリ起動まで継続持ち越し。
