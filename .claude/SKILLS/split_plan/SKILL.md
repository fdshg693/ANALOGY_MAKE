---
name: split_plan
disable-model-invocation: true
user-invocable: true
---

## コンテキスト

- カテゴリ: !`cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app`
- 最新バージョン番号: !`bash .claude/scripts/get_latest_version.sh`
- 次のマイナーバージョン番号: !`bash .claude/scripts/get_latest_version.sh next-minor`

## 役割

ワークフロー後半の共通ステップ。`/issue_plan` が作成した `ROUGH_PLAN.md` と `PLAN_HANDOFF.md` を起点に、実装詳細の `REFACTOR.md` / `IMPLEMENT.md` を作成し、`plan_review_agent` で review を行う。

- 現状把握・ISSUE レビュー・`ROUGH_PLAN.md` と `PLAN_HANDOFF.md` 作成は `/issue_plan` の責務であり、本 SKILL では扱わない
- ワークフロー内で plan_review_agent を起動するのは本 SKILL のみ
- ROUGH_PLAN.md frontmatter の `workflow` 値が `quick` の場合、本 SKILL は呼ばれない想定（両 YAML は `/issue_plan → 後続` の設計で、quick には `/split_plan` が含まれない）

## ステップ1: 実装計画の作成と承認

`/issue_plan` が作成した `ROUGH_PLAN.md`（スコープ定義）と `PLAN_HANDOFF.md`（選定理由・除外理由・関連 ISSUE パス・後続 step への注意点）を読み、対象タスクを固定する（`docs/{カテゴリ}/ver{次のバージョン番号}/ROUGH_PLAN.md` と `PLAN_HANDOFF.md`）。`PLAN_HANDOFF.md` が存在しない場合（`/issue_plan` が handoff 情報ゼロと判定し省略したケース）は `ROUGH_PLAN.md` のみで進めてよい。

ROUGH_PLAN.md frontmatter に `workflow: full` が記録されていることを確認する。`quick` になっている場合は本ステップは実行されるべきでないため、`logs/workflow/` にエラー記録しつつ `ISSUES/{カテゴリ}/high/split-plan-consistency-error-ver{X.Y}.md` を作成（frontmatter: `status: need_human_action` / `assigned: human`）して終了する。

1. 承認された `ROUGH_PLAN.md` に基づいて、実装計画を作成する
  - **既存ファイルの事前確認**: 変更対象の既存ファイル（ソースコード、設定ファイル、`.gitignore` 等）は、計画に含める前に現在の内容を読んで確認すること。既に対応済みの設定や存在する機能を重複して計画に含めることを防ぐ
   - `REFACTOR.md` — 機能追加・変更への障害を減らすためのリファクタリングの洗い出し。リファクタリングが必要な場合のみファイルを作成する。不要な場合は `ROUGH_PLAN.md` に「事前リファクタリング不要」と理由を1行記載すれば十分（ファイル作成不要）
   - `IMPLEMENT.md` — タスクの実装案の作成。新規ライブラリや未使用APIを扱う場合は、「## リスク・不確実性」セクションを設け、型定義の不備・ドキュメント不足・実行時挙動の不確実性を洗い出すこと
     - 可能な限り実装の詳細に踏み込むこと

2. **plan_review_agentサブエージェントを起動して、実装計画を説明して、承認を得ること**（ここで実装詳細を確定する）

## ステップ2: Git にコミットする
- 作成したドキュメント（`IMPLEMENT.md`、必要なら `REFACTOR.md`）をコミットする
- コミットメッセージ例: `docs(ver{バージョン番号}): split_plan完了`
- **プッシュは不要**（後続ステップでまとめてプッシュする）
