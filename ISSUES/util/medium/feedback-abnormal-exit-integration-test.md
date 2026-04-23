---
status: ready
assigned: ai
priority: medium
reviewed_at: "2026-04-23"
---

# FEEDBACK 異常終了時の温存挙動を integration テストで検証する

## 概要

`scripts/claude_loop.py:570` 付近の不変条件「ステップ非ゼロ exit / 例外 / Ctrl-C 時は `consume_feedbacks` を呼ばず、FEEDBACK ファイルは `FEEDBACKS/` 直下に残す」を、現状は README / USAGE / docstring での明文化のみで担保している。コード側で invariant が壊れても CI で気付けないため、integration テストを追加したい。

## 背景（ver13.0 PHASE7.0 §4 で先送り）

- ver13.0 の IMPLEMENT.md §2-2 で、この検証を「単体テスト化には subprocess / TeeWriter / 一時 cwd 組立が必要で ver12.0 RETROSPECTIVE §2-2-b の cwd 依存問題を再発させやすい」と判断し、本バージョンでは追加しない方針にした
- MEMO.md 6-4 で「先送り」として記録、ISSUE 化で埋もれ防止

## 本番発生時の兆候

- ユーザー報告例: 「ワークフローが途中で失敗したのに、再実行したら同じフィードバックが適用されない／片方だけ消えた」
- ログ上の判断材料:
  - ステップ failure 時の log (`logs/workflow/*.log`) の `--- end (exit: <non-zero>, ...)` 直後
  - `git log --all -- "FEEDBACKS/done/**"` で想定外の時刻に移動履歴があれば invariant 破れの疑い

## 対応方針

1. `scripts/tests/test_claude_loop_integration.py` 配下に、以下を検証するテストを追加する:
   - step を `sh -c "exit 1"` 相当に差し替えた軽量 YAML を一時ディレクトリに生成
   - 事前に `FEEDBACKS/` にダミーフィードバックを置く
   - `claude_loop.py` を subprocess で起動し、非ゼロ exit を確認
   - テスト後に `FEEDBACKS/` 直下にダミーが残り、`FEEDBACKS/done/` が作成されていない／または空であることを assert
2. 既存 integration テスト（`test_claude_loop_integration.py`）で確立されているテンポラリ cwd パターンを流用し、cwd 依存を再発させない
3. 正常終了時の consume 挙動との対照テストもペアで用意する

## 影響範囲

- 検証対象コード: `scripts/claude_loop.py:_run_steps()` 内の `exit_code != 0` 分岐と `consume_feedbacks` 呼び出し位置（現行 L570 付近）
- テスト追加のみで、プロダクションコードには手を入れない想定
