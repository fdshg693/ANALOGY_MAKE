---
status: ready
assigned: ai
priority: low
reviewed_at: "2026-04-23"
---
# `--workflow auto` の ROUGH_PLAN.md 同定を mtime 依存から明示判定に強化

## 概要

ver9.0 で導入された `--workflow auto` のフェーズ 2 は、`docs/{category}/ver*/ROUGH_PLAN.md` の中から最新 `st_mtime` のファイルを「今回フェーズ 1 で書かれたもの」として同定している (`scripts/claude_loop.py::_find_latest_rough_plan`)。

通常運用では成立するが、以下のケースで誤同定が起こり得る:

- 人間が過去バージョンの ROUGH_PLAN.md を `touch` / 再保存した直後に auto 実行した場合
- フェーズ 1 が極めて短時間で終わり、mtime 秒解像度内で既存ファイルと衝突した場合
- ファイルシステムの mtime 解像度が粗い環境（FAT32 等）で auto 実行した場合

## 本番発生時の兆候

- `auto: phase2 = <kind> (<yaml>.yaml)` で表示される `kind` が直近 ROUGH_PLAN.md の frontmatter と一致しない
- フェーズ 2 で想定外のワークフロー（full のはずが quick、あるいは逆）が起動する
- `/issue_plan` の ROUGH_PLAN.md が作られたはずの新バージョンフォルダと異なる場所が読み取られる

## 対応方針

1. `_run_auto()` でフェーズ 1 開始前に `max(p.stat().st_mtime for p in candidates)` を記録
2. フェーズ 2 側では「記録した閾値を超える mtime を持つファイル」のみを候補化
3. 候補が複数あれば最新バージョン（`ver` 番号でソート）を優先
4. 候補 0 件なら `SystemExit` で明示的に失敗させる

または、`/issue_plan` SKILL 側に作成した ROUGH_PLAN.md のパスを `REQUESTS/AI/.auto_phase1_result` のようなサイドチャネルに書かせ、フェーズ 2 がそれを読む形も検討可能（SKILL 改修が必要）。

## 影響範囲

- `scripts/claude_loop.py::_find_latest_rough_plan` / `_run_auto`
- `tests/test_claude_loop.py::TestFindLatestRoughPlan` / `TestAutoWorkflowIntegration`

## 出典

`docs/util/ver9.0/IMPLEMENT.md` §10 R1（検証先送り）
