# CURRENT_skills: util ver12.0 — SKILL ファイル・サブエージェント

ver12.0 では SKILL 本体の変更はなし。内容は ver11.0 と同一。詳細は [ver11.0/CURRENT_skills.md](../ver11.0/CURRENT_skills.md) を参照。

## フルワークフロー（6 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `issue_plan/SKILL.md` | 101 | ステップ 1: 現状把握・ISSUE レビュー・ISSUE/MASTER_PLAN 選定・ROUGH_PLAN.md 作成・workflow 判定。`issue_worklist.py --limit 20` で ISSUE 一覧を取得 |
| `split_plan/SKILL.md` | 38 | ステップ 2: REFACTOR/IMPLEMENT 作成 + plan_review_agent での review のみ |
| `imple_plan/SKILL.md` | 81 | ステップ 3: 実装。CURRENT.md + 計画ドキュメントに基づきコード実装。MEMO.md を出力。検証先送りリスクは `ISSUES/` に独立ファイルを作成 |
| `wrap_up/SKILL.md` | 46 | ステップ 4: 残課題対応。MEMO.md の項目を ✅完了 / ⏭️不要 / 📋先送り に分類し、ISSUES 整理 |
| `write_current/SKILL.md` | 83 | ステップ 5: ドキュメント更新。メジャー版は CURRENT.md、マイナー版は CHANGES.md を作成。150 行超の場合は `CURRENT_{トピック名}.md` に分割 |
| `retrospective/SKILL.md` | 76 | ステップ 6: 振り返り。§3 冒頭で `issue_worklist.py` を呼び出し次バージョン推奨の材料を収集 |

## 軽量ワークフロー quick（3 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `issue_plan/SKILL.md` | 101 | ステップ 1: quick でも同じ前半ステップを使用 |
| `quick_impl/SKILL.md` | 43 | ステップ 2: 実装 + MEMO 対応を統合 |
| `quick_doc/SKILL.md` | 55 | ステップ 3: CHANGES.md 作成 + CLAUDE.md 更新確認 + ISSUES 整理 + コミット＆プッシュ |

## ISSUE レビュー仕様書

| ファイル | 行数 | 役割 |
|---|---|---|
| `issue_review/SKILL.md` | 99 | ISSUE レビューフェーズの一次資料。`/issue_plan` が参照し、スキャン → 個別レビュー → 書き換えガード → サマリ報告 の手順を定義。**直接起動しない** |

## メタ評価・ワークフロー文書

| ファイル | 行数 | 役割 |
|---|---|---|
| `meta_judge/SKILL.md` | 18 | メタ評価。ワークフロー全体の有効性を評価する手動実行専用 SKILL |
| `meta_judge/WORKFLOW.md` | 48 | 保守上の注意（3 ファイル同期義務・`--workflow auto` 実装済み）を定義 |

## サブエージェント

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/agents/plan_review_agent.md` | 17 | 計画レビュー専用エージェント。Sonnet モデル、Read/Glob/Grep のみ使用。`/split_plan` で利用（quick ワークフローでは使用しない） |
