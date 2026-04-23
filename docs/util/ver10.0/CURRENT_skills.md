# CURRENT_skills: util ver10.0 — SKILL ファイル・サブエージェント

`.claude/skills/` 配下の SKILL ファイルと、サブエージェントの構成。ver10.0 での SKILL 本体の変更はなし（ver9.2 で `issue_plan/SKILL.md` の `issue_worklist.py` 呼び出しに `--limit 20` が追加済み）。

## フルワークフロー（6 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `issue_plan/SKILL.md` | 101 | ステップ 1: 現状把握・ISSUE レビュー・ISSUE/MASTER_PLAN 選定・ROUGH_PLAN.md 作成・workflow 判定。**ver9.2 で** `issue_worklist.py --limit 20` に変更 |
| `split_plan/SKILL.md` | 38 | ステップ 2: REFACTOR/IMPLEMENT 作成 + plan_review_agent での review のみ |
| `imple_plan/SKILL.md` | 81 | ステップ 3: 実装。CURRENT.md + 計画ドキュメントに基づきコード実装。MEMO.md を出力。検証先送りリスクは `ISSUES/` に独立ファイルを作成 |
| `wrap_up/SKILL.md` | 46 | ステップ 4: 残課題対応。MEMO.md の項目を ✅完了 / ⏭️不要 / 📋先送り に分類し、ISSUES 整理 |
| `write_current/SKILL.md` | 83 | ステップ 5: ドキュメント更新。メジャー版は CURRENT.md、マイナー版は CHANGES.md を作成。150 行超の場合は `CURRENT_{topic}.md` に分割 |
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
| `issue_review/SKILL.md` | 99 | ISSUE レビューフェーズの**一次資料**。`/issue_plan` が参照し、スキャン → 個別レビュー → 書き換えガード → サマリ報告 の手順を定義。**直接起動しない** |

### issue_review の処理フロー

1. **スキャン**: `ISSUES/{カテゴリ}/{high,medium,low}/*.md` を走査し frontmatter を読む
2. **レビュー対象抽出**: `status: review` かつ `assigned: ai` のファイルを選出
3. **個別レビュー**: 各ファイルを Read → 判定 → Edit（frontmatter ブロック丸ごと置換）
   - 記述が具体的（再現手順/期待動作/影響範囲の 2 点以上）→ `ready / ai`
   - 人間対応必要 / 記述が粗すぎる → `need_human_action / human` + `## AI からの依頼` 追記
4. **サマリ報告**: `## ISSUE レビュー結果` / `## ISSUE 状態サマリ` を ROUGH_PLAN 冒頭に残す

## `/issue_plan` SKILL の構成

### 主な処理

- `CURRENT.md` / 直前 `RETROSPECTIVE.md` / `MASTER_PLAN.md` を参照して現状把握
- ISSUE レビューフェーズ（`issue_review/SKILL.md` の手順をインライン展開）
- `status: ready` / `assigned: ai` の ISSUE 優先選定（high → medium → low）
- `ready/ai` が無い場合のみ MASTER_PLAN 次項目に着手
- `docs/{カテゴリ}/ver{次バージョン}/ROUGH_PLAN.md` を作成
- ROUGH_PLAN.md 冒頭 frontmatter に `workflow: quick | full` と `source: issues | master_plan` を記録

### ワークフロー選択ルール

| 条件 | 決定 |
|---|---|
| 選定 ISSUE に `status: review` が 1 件でも含まれる | **必ず full** |
| MASTER_PLAN 新項目 / アーキテクチャ変更 / 新規ライブラリ導入を含む | **必ず full** |
| 全 `ready` で変更対象が 3 ファイル以下かつ 100 行以下の見込み | quick |
| 判断に迷う場合 | 安全側で full |

### ROUGH_PLAN.md の frontmatter 形式

```yaml
---
workflow: full   # または quick
source: issues   # または master_plan
---
```

## `/split_plan` SKILL の現在の構成

前半責務（現状把握・ISSUE 選定・ROUGH_PLAN.md 作成）は `/issue_plan` に移管済み。現在は以下のみ担当:

1. `/issue_plan` が作成した `ROUGH_PLAN.md` を読み対象タスクを固定
2. ROUGH_PLAN.md frontmatter の `workflow: full` を確認
3. REFACTOR.md / IMPLEMENT.md を作成
4. plan_review_agent を起動して実装計画を review（**ワークフロー内で唯一 review を行うステップ**）
5. コミット

## メタ評価・ワークフロー文書

| ファイル | 行数 | 役割 |
|---|---|---|
| `meta_judge/SKILL.md` | 18 | メタ評価。ワークフロー全体の有効性を評価する手動実行専用 SKILL |
| `meta_judge/WORKFLOW.md` | 48 | 保守上の注意（3 ファイル同期義務・`--workflow auto` 実装済み）を定義 |

## サブエージェント

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/agents/plan_review_agent.md` | 17 | 計画レビュー専用エージェント。Sonnet モデル、Read/Glob/Grep のみ使用。`/split_plan` で利用（quick ワークフローでは使用しない） |

## 各 SKILL ファイルで保持すべき主要な振る舞い

- **全ステップ共通**: `.claude/CURRENT_CATEGORY` を参照して現在のカテゴリに対応するパスを取得
- **issue_plan**: ISSUE レビューフェーズ後、`ready/ai` ISSUE を優先度順で拾い上げ。`ready/ai` が無い場合のみ MASTER_PLAN の次項目に進む。ROUGH_PLAN.md に `workflow` / `source` frontmatter を記録する。`issue_worklist.py --format json --limit 20` で ISSUE 一覧を取得
- **split_plan**: ROUGH_PLAN.md の `workflow: full` を確認してから実装計画を作成。ワークフロー内で唯一 plan_review_agent を起動する
- **imple_plan**: 検証先送りリスクは MEMO 内注記に加え `ISSUES/` に独立ファイルを作成して追跡
- **write_current**: CURRENT.md 分割基準（150 行超）、命名規則（`CURRENT_{トピック名}.md`）を遵守
- **retrospective**: SKILL 自体の改善を即時適用する自己改善ループを含む。§3 で `issue_worklist.py` を呼んで次バージョン推奨の材料を収集する
