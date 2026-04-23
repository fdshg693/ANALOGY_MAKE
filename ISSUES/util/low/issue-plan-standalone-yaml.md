---
status: ready
assigned: ai
priority: low
reviewed_at: "2026-04-23"
---
# `/issue_plan` 単独実行用 YAML の新設

## 概要

ver8.0 で `/issue_plan` SKILL を新設したが、単独実行用 YAML（`scripts/claude_loop_issue_plan.yaml`）は作成していない。このため `/issue_plan` の動作確認は `claude_loop.yaml` / `claude_loop_quick.yaml` を 1 ステップ目で中断する形（`--max-step-runs 1` など）でしか行えない。

MASTER_PLAN PHASE6.0 §3 で予定されている作業の一部。

## 本番発生時の兆候

- `/issue_plan` の振る舞い調整・検証がフルワークフロー起動を伴ってしか行えず、開発フィードバックが遅い
- `/issue_plan` を単独で反復実行したいケース（ISSUE レビューのみを定期的に走らせる等）で YAML を自作する必要がある

## 対応方針

1. `scripts/claude_loop_issue_plan.yaml` を新規作成（1 ステップ構成: `/issue_plan` のみ）
2. `defaults` / `command` セクションは `claude_loop.yaml` と同期
3. `scripts/README.md` にクイックスタート例を追記

## 影響範囲

- `scripts/claude_loop_issue_plan.yaml`（新規）
- `scripts/README.md`（使用例追記）

## 出典

`docs/util/ver8.0/IMPLEMENT.md` §9 R6 / §11（ver8.1 以降スコープ）
