---
name: issue_plan
disable-model-invocation: true
user-invocable: true
---

## コンテキスト

- カテゴリ: !`cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app`
- 最新バージョン番号: !`bash .claude/scripts/get_latest_version.sh`
- 次のマイナーバージョン番号: !`bash .claude/scripts/get_latest_version.sh next-minor`
- 次のメジャーバージョン番号: !`bash .claude/scripts/get_latest_version.sh next-major`
- AI 向け ready/review ISSUE: !`python scripts/issue_worklist.py --format json --limit 20`

## 役割

ワークフロー先頭の共通ステップ。`/split_plan`・`/quick_plan` からプラン前半責務を切り出した位置づけ。

- 現状把握（`CURRENT.md` / 直前 `RETROSPECTIVE.md` / `MASTER_PLAN.md` を参照）
- ISSUE レビューフェーズ（`review / ai` → `ready / ai` or `need_human_action / human`）
- `status: ready` / `assigned: ai` の ISSUE 優先選定（優先度順 high → medium → low）
- MASTER_PLAN 新項目への着手判断（ready/ai が無い場合）
- `docs/{カテゴリ}/ver{次バージョン}/ROUGH_PLAN.md` を作成する
- ROUGH_PLAN.md 冒頭 frontmatter に `workflow: quick | full` と `source: issues | master_plan` を記録する
- **review は行わない**（plan_review_agent は起動しない）

## 準備

上記の最新バージョン番号に基づいて、現在の状況を把握して。

- 現状を把握して
  - 最新バージョンの `CURRENT.md` があれば参照する。`CURRENT.md` が分割されている場合（`CURRENT_{トピック名}.md` へのリンクを含む場合）は、今回のタスクに関連する詳細ファイルのみを読む。`CURRENT.md` がなければユーザーへの質問＋サブエージェントによる調査で把握する
  - `ISSUES/{カテゴリ}` フォルダ配下に優先度の高い課題があれば参照して、把握する（ `high`・`medium`・`low`フォルダに分かれている）
  - 直前バージョンの `RETROSPECTIVE.md` が存在する場合は確認し、未実施の改善提案がないか確認する
  - **retrospective からの FEEDBACK handoff**: `FEEDBACKS/handoff_ver*_to_next.md` が存在する場合、`--append-system-prompt` 経由で自動注入される。ROUGH_PLAN の判断材料として優先度高で参照する（retrospective が次ループ向けに意図的に書き出した補助線であり、感想ではなく次ステップに効く入力として扱う）。本 handoff は次ループで 1 回だけ消費され `FEEDBACKS/done/` に移動するため、恒久メモリではない
  - **ISSUE レビューフェーズ**: `ISSUES/{カテゴリ}/{high,medium,low}/*.md` を走査し、`status: review` かつ `assigned: ai` の ISSUE を 1 件ずつ Read → 判定 → frontmatter を `ready / ai` または `need_human_action / human` に書き換える。判定基準・書き換え手順・`## AI からの依頼` 追記の書式は `.claude/skills/issue_review/SKILL.md` を一次資料とする。レビュー結果サマリ（遷移件数・対象パス）と状態分布（`status × assigned` の 5 区分）を ROUGH_PLAN 本文冒頭に `## ISSUE レビュー結果` / `## ISSUE 状態サマリ` の見出しで残す

- 目標となるプランを把握して
  - ドキュメントが指定されていなければ、 `docs/{カテゴリ}/MASTER_PLAN.md` を参照して、目標となるプランを把握する
  - ドキュメントなしでユーザーの入力だけで進めてはならず、必ずドキュメントに落とし込んだ上で、ユーザーの承認を得ること
  - **MASTER_PLAN 全フェーズ完了時の判断ガイドライン**: `docs/{カテゴリ}/MASTER_PLAN/` 配下の全 PHASE が「実装済み」の場合、以下の優先順で方針を選択する:
    1. **既存 ISSUES の消化を優先**: `status: ready / ai` の ISSUE が 1 件以上あり、小粒対応で区切れる場合は、新 PHASE の骨子作成は行わず、ROUGH_PLAN のスコープを既存 ISSUE に限定する（`source: issues`）
    2. **新 PHASE の骨子作成を ROUGH_PLAN スコープに含める**: 既存 ISSUES が尽きている or 既存 ISSUES だけでは扱えないテーマが明確な場合のみ、新 `PHASE{N+1}.md` 骨子作成を ROUGH_PLAN のタスクとして取り上げる（`source: master_plan`）。この場合は必ず `workflow: full`
    3. **ユーザーに方向性を確認**: 上記で決め切れない場合は、AUTO モード下では `ISSUES/{カテゴリ}/medium/direction-check-ver{X.Y}.md` を作成（frontmatter: `status: need_human_action` / `assigned: human`）した上で、暫定的に既存 ISSUES 消化に倒す

## バージョン種別の判定

今回のタスクがメジャー・マイナーのどちらに該当するか判定する:

**メジャーバージョンアップ (X.0)** の条件（いずれか）:
- MASTER_PLAN の新項目に着手する
- アーキテクチャの変更を伴う
- 新規の外部ライブラリ・サービスを導入する
- 破壊的変更を伴うリファクタリング

**マイナーバージョンアップ (X.Y)** の条件（上記に該当しない場合）:
- ISSUES の解消（バグ修正・改善）
- 既存機能の微調整・UX改善
- ドキュメント整理・テスト追加

判定結果に基づいて、新しい空の `docs/{カテゴリ}/ver{次のバージョン番号}` フォルダを作成してください。

## ワークフロー選択（`workflow: quick | full`）

選定 ISSUE・タスクの性質に応じて以下ルールで決定する:

- 選定 ISSUE に `status: review` が 1 件でも含まれる場合 → **必ず `full`**
- MASTER_PLAN 新項目 / アーキテクチャ変更 / 新規ライブラリ導入を含む場合 → **必ず `full`**
- 全 `ready` で、変更対象が 3 ファイル以下かつ 100 行以下の見込みなら → `quick`
- 判断に迷う場合 → 安全側で `full`

決定結果を ROUGH_PLAN.md 冒頭の frontmatter に記録する:

```markdown
---
workflow: full
source: issues
---
```

`source` は着手対象の出所を示す: `issues`（ISSUES から拾った）/ `master_plan`（MASTER_PLAN 新項目）。

## ROUGH_PLAN.md の作成

`docs/{カテゴリ}/ver{次のバージョン番号}/ROUGH_PLAN.md` を作成する:

- `docs/{カテゴリ}/MASTER_PLAN.md`の内容に沿った機能追加・変更を行うか、 `ISSUES/{カテゴリ}` の改善を行うかを決定する。（両方は行わないこと）
  - **判断基準**: `ISSUES/{カテゴリ}/` から `status: ready` かつ `assigned: ai` の ISSUE を優先度順（high → medium → low）で抽出する。`review` / `need_human_action` / `raw` は着手対象外（直前のレビューフェーズで処理済み / 人間対応待ち）。`ready / ai` が無い場合のみ MASTER_PLAN の次項目に進む。ユーザーから明示的な指示がある場合はそちらに従う
  - どちらの、どのような内容を対応するのか明確に記述すること

- 比較的小規模で完結する切りのいいタスクを切り取り、そのタスクのみにフォーカスして、タスクの内容を説明すること
  - **後続のタスクの内容などは含めないこと**
  - 実装には踏み込まず、提供される機能の全体像を説明すること
  - **ROUGH_PLAN の粒度に注意**: 「何をするか」（機能・スコープ・ユーザー体験の変化）を記述し、「どうやるか」（具体的なAPI・実装方式）は IMPLEMENT.md に委ねること。ROUGH_PLAN で実装方式を詳述すると、IMPLEMENT.md で設計変更が生じた際に矛盾が残る
  - **後続 `/split_plan` への情報引き継ぎ**: 本ステップは新規セッションで `/split_plan` に渡されるため、`/split_plan` が ROUGH_PLAN.md だけで IMPLEMENT.md を起こせるよう、判断経緯（選定理由・除外理由）と関連ファイル・関連 ISSUE パスを漏れなく記載すること

## Git にコミットする

- 作成した `ROUGH_PLAN.md` をコミットする
- コミットメッセージ例: `docs(ver{バージョン番号}): issue_plan完了`
- **プッシュは不要**（後続ステップでまとめてプッシュする）
- **plan_review_agent は起動しない**（review は後続 `/split_plan` で実施する）
