# ver6.1 は quick ワークフロー候補

`/split_plan` の小規模タスク判定により、ver6.1（`parse-frontmatter-shared-util.md` 対応）は quick ワークフロー（`/quick_plan` → `/quick_impl` → `/quick_doc`）の条件を満たします。

## 判定

- 変更対象ファイル: 3 つ（`scripts/issue_status.py` / `scripts/claude_loop_lib/feedbacks.py` / 新規 `scripts/claude_loop_lib/frontmatter.py`）
- 追加行: 50 行未満の見込み
- 既存ファイル修正 + 新規 1 ファイル（同一ディレクトリ配下）

## 提案

AUTO 実行モードのため判断を中断できず、本ワークフロー（full）のまま `ROUGH_PLAN.md` → `IMPLEMENT.md`（簡潔版）→ review の順で続行しています。

次回同様のマイナー ISSUE を消化する際は、以下のコマンドで quick 版を明示的に起動できます:

```bash
python scripts/claude_loop.py -w scripts/claude_loop_quick.yaml
```

## 対応不要な場合

本リクエストは情報提供のみです。ユーザー対応不要であれば、ver6.1 完了後に本ファイルを削除してください。
