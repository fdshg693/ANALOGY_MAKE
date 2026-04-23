# ver13.1 MEMO — 実装メモ

## 計画からの乖離

なし。ROUGH_PLAN の方針通りに実装完了。

- `scripts/tests/test_claude_loop_integration.py` に `TestFeedbackInvariant` クラスを追加
- テストメソッド 2 件（failure / success 対照）
- ヘルパ 2 件（`_setup_cwd` / `_run_with_returncode`）
- 計 81 行追加（ROUGH_PLAN 見込み 50〜80 行に収まる）
- プロダクションコードへの変更なし

## 実装の要点

- `feedbacks_dir = cwd / "FEEDBACKS"` は `_run_steps()` が実 cwd から決定するため、`tempfile.TemporaryDirectory` ＋ `--cwd` で完全に分離できる
- `consume_feedbacks` の `shutil.move` はモックしていない（実ファイル移動を観測してこそ invariant 検証になる）。`subprocess.run` のみモックして exit code を制御
- `TestAutoWorkflowIntegration._run_main_auto` と同じパッチセット（`subprocess.run` / `check_uncommitted_changes` / `shutil.which` / `validate_startup` / `print`）を適用
- 単体 YAML は `cwd / "test-workflow.yaml"` に書き出し、`--workflow <絶対パス>` で渡す（"full"/"quick"/"auto" を避けて実 YAML ファイルへの依存をゼロにする）

## テスト実行結果

- 新規テスト: 2/2 OK
- 全テストスイート: 233 tests OK（既存 231 + 新規 2）

## ISSUE 状態更新（要対応）

`ISSUES/util/medium/feedback-abnormal-exit-integration-test.md` を `done` に更新する必要あり（quick_doc ステップで実施予定）。
