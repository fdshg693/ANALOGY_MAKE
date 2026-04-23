# MEMO: util ver9.1

## 実装完了事項

- `scripts/claude_loop.py`: `_find_latest_rough_plan` にオプション引数 `mtime_threshold: float | None` を追加
- `scripts/claude_loop.py`: `_rough_plan_candidates(cwd)` ヘルパー（候補列挙を DRY に共有）
- `scripts/claude_loop.py`: `_version_key(path)` ヘルパー（自然順バージョンソート、ver10.0 > ver9.1 を正しく判定）
- `scripts/claude_loop.py`: `_run_auto` でフェーズ 1 開始前に `mtime_threshold` を記録し、フェーズ 2 の `_find_latest_rough_plan` に渡すよう変更
- `tests/test_claude_loop.py`: 閾値テスト 4 件追加（`test_threshold_excludes_pre_existing_files`, `test_threshold_no_new_files_raises`, `test_threshold_multiple_new_files_highest_version_wins`, `test_version_key_natural_sort`）
- `tests/test_claude_loop.py`: `TestAutoWorkflowIntegration._run_main_auto` で `claude_loop._find_latest_rough_plan` をパッチ（phase 1 はモックのため実ファイル作成なし → 統合テストがフェーズ 2 ディスパッチ検証に集中できるよう分離）
- `ISSUES/util/done/issue-plan-split-plan-handoff-verification.md` へ移動 + status: done に更新

## ROUGH_PLAN との乖離

なし。実装方針は ISSUE 本文の「対応方針 1（閾値記録方式）」に完全に従った。

`mtime_threshold = None` 時の旧挙動は保持（後方互換）。

## 残課題・メモ

- `TestAutoWorkflowIntegration` は `_find_latest_rough_plan` をパッチすることで閾値ロジックのテストを分離している。`_run_auto` 全体の E2E テスト（実際にファイルを書く subprocess mock）は YAGNI により追加していない
- `npx nuxi typecheck` は vue-router volar 関連の MODULE_NOT_FOUND クラッシュが発生するが、今回の変更（Python のみ）とは無関係。既知問題として CLAUDE.md に記載済み
