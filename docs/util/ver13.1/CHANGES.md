# ver13.1 CHANGES — ver13.0 からの変更差分

## 変更ファイル一覧

| ファイル | 変更種別 | 概要 |
|---|---|---|
| `scripts/tests/test_claude_loop_integration.py` | M | `TestFeedbackInvariant` クラスを追加（81行） |

## 変更内容の詳細

### `scripts/tests/test_claude_loop_integration.py` — FEEDBACK 異常終了温存の integration テスト追加

`_run_steps()` 内の不変条件「ステップ非ゼロ exit 時は `consume_feedbacks` を呼ばず `FEEDBACKS/` 直下にファイルを残す」を CI で自動検証するために `TestFeedbackInvariant` クラスを追加した。

**追加したテストメソッド**:

- `test_feedback_preserved_on_step_failure`: step が非ゼロ exit のとき `FEEDBACKS/dummy-feedback.md` が温存され `FEEDBACKS/done/` が空のままであることを assert
- `test_feedback_consumed_on_step_success`: step が正常終了のとき `FEEDBACKS/done/dummy-feedback.md` に移動されることを assert（対照ケース）

**実装方針**:

- `subprocess.run` のみモックして exit code を制御し、`consume_feedbacks` 内の `shutil.move` は実際に動かす（実ファイル移動を観測することで invariant を確実に検証）
- `tempfile.TemporaryDirectory` + `--cwd` で cwd を分離し、ver12.0 RETROSPECTIVE §2-2-b 教訓の cwd 依存問題を回避
- 単体 YAML を `cwd / "test-workflow.yaml"` に書き出し絶対パスで渡すことで、実際の `claude_loop.yaml` / `claude_loop_quick.yaml` への依存をゼロにする
- `TestAutoWorkflowIntegration._run_main_auto` と同じパッチセットを適用（`subprocess.run` / `check_uncommitted_changes` / `shutil.which` / `validate_startup` / `print`）

**テスト結果**: 233 tests OK（既存 231 + 新規 2）

## API変更

なし（テスト追加のみ）。

## 技術的判断

- **`shutil.move` はモックしない**: `consume_feedbacks` の実装が `shutil.move` を使うことを知りつつ、あえてモックせず実ファイル操作を観測する。モックすると invariant（ファイルが実際に残るかどうか）を検証できなくなるため
- **例外 / Ctrl-C 経路は今回スコープ外**: 両者とも `consume_feedbacks` に到達せずに関数を抜ける点は非ゼロ exit と同じであり、今回の非ゼロ exit ケースがカバーする invariant の本質と等価。将来必要なら別 ISSUE 化
