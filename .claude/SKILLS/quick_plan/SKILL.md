---
name: quick_plan
description: 軽量ワークフロー用の計画ステップ（マイナーバージョンのみ）
disable-model-invocation: true
user-invocable: true
---

## コンテキスト

- カテゴリ: !`cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app`
- 最新バージョン番号: !`bash .claude/scripts/get_latest_version.sh`
- 次のマイナーバージョン番号: !`bash .claude/scripts/get_latest_version.sh next-minor`

## 準備

現在のコード状況を把握するために、以下を参照してください:

1. 最新バージョンの `CURRENT.md` があれば参照する（メジャーバージョンの `CURRENT.md` を起点に、以降のマイナーバージョンの `CHANGES.md` も確認する）。`CURRENT.md` が分割されている場合（`CURRENT_{トピック名}.md` へのリンクを含む場合）は、今回のタスクに関連する詳細ファイルのみを読む
2. `ISSUES/{カテゴリ}` フォルダ配下の `high`・`medium` 課題を確認する
3. 直前バージョンの `RETROSPECTIVE.md` が存在する場合は確認し、未実施の改善提案がないか確認する
4. `docs/{カテゴリ}/MASTER_PLAN.md` の全フェーズが「実装済み」の場合は、ISSUES 対応に集中する。ISSUES もない場合はユーザーに次の方向性を確認する
5. **ISSUE レビューフェーズ**: `ISSUES/{カテゴリ}/{high,medium,low}/*.md` を走査し、`status: review` かつ `assigned: ai` の ISSUE を 1 件ずつ `ready / ai` または `need_human_action / human` に振り分ける。判定基準・書き換え手順・`## AI からの依頼` 追記の書式は `.claude/skills/issue_review/SKILL.md` を一次資料とする。レビュー結果サマリと状態分布を ROUGH_PLAN 冒頭に `## ISSUE レビュー結果` / `## ISSUE 状態サマリ` の見出しで残す

## 計画

### バージョン種別

quick ワークフローは **マイナーバージョンのみ** を対象とする。
以下の条件に該当する場合はメジャーバージョンが必要なため、ユーザーに報告してフルワークフロー（`/split_plan`）への切り替えを推奨すること:

- MASTER_PLAN の新項目に着手する
- アーキテクチャの変更を伴う
- 新規の外部ライブラリ・サービスを導入する
- 破壊的変更を伴うリファクタリング

### ROUGH_PLAN.md の作成

`docs/{カテゴリ}/ver{次のマイナーバージョン番号}/` フォルダを作成し、`ROUGH_PLAN.md` を作成する:

- **対応する ISSUE**（1〜2 件）
  - `ISSUES/{カテゴリ}/` から `status: ready` かつ `assigned: ai` の ISSUE を優先度順（high → medium → low）で抽出する。`review` / `need_human_action` / `raw` は着手対象外
  - ユーザーから明示的な指示がある場合はそちらに従う
- **変更対象ファイル**（3 つ以下の見込み）
- **変更方針**（5〜10 行程度の簡潔な記述）
  - 実装方針も簡潔に含める（IMPLEMENT.md を作成しないため）

**注意**: plan_review_agent は起動しない（軽量ワークフローでは省略）

## Git にコミットする
- コミットメッセージ: `docs(ver{バージョン番号}): quick_plan完了`
- **プッシュは不要**
