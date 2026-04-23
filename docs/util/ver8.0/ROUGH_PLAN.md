# ver8.0 ROUGH_PLAN — `/issue_plan` SKILL 新設とプラン前半/後半の責務分離（PHASE6.0 §2）

## ISSUE レビュー結果

`ISSUES/util/{high,medium,low}/*.md` を走査した結果、`status: review` かつ `assigned: ai` の ISSUE は **0 件**。frontmatter の書き換えは発生しなかった。

## ISSUE 状態サマリ（util カテゴリ）

| priority | raw/human | raw/ai | review/ai | ready/ai | need_human_action/human |
|---|---|---|---|---|---|
| high | 0 | 0 | 0 | 0 | 0 |
| medium | 0 | 0 | 0 | 1 | 0 |
| low | 0 | 0 | 0 | 0 | 0 |

`ready/ai` の 1 件は `ISSUES/util/medium/issue-review-rewrite-verification.md`（ver6.0 持ち越し）。これは `issue_review` SKILL の書き換えロジックを app/infra カテゴリのワークフロー上で実動作検証するタスクであり、util カテゴリ単体では消化できない。ver7.0 RETROSPECTIVE 3-1 と同様、本バージョンでも util 側では着手せず持ち越しとする。

## バージョン種別の判定

**メジャー（ver8.0）**。判定根拠:

- MASTER_PLAN PHASE6.0 §2（`/issue_plan` SKILL 新設 + `/split_plan` / `/quick_plan` の責務変更）はワークフローのアーキテクチャ変更に該当する
- 新規 SKILL を追加し、既存 2 SKILL の責務境界を引き直す破壊的変更
- ver7.0 RETROSPECTIVE 3-3 で「次バージョンは ver8.0（メジャー）として PHASE6.0 §2 に着手する」が最終推奨として記録されており、それに従う

## スコープ（本バージョンでやること）

PHASE6.0 §2 の範囲に限定する。プラン前半（「何をやるか」の決定）と後半（「どう実装するか」の詳細化）の責務を分離し、両ワークフロー（full / quick）の入口を共通の `/issue_plan` ステップに揃える。

### 1. `/issue_plan` SKILL の新設

- 新規 SKILL `.claude/skills/issue_plan/SKILL.md` を作成
- 責務（MASTER_PLAN PHASE6.0 §2-1 準拠）:
  - 現状把握（`CURRENT.md` / 直前 `RETROSPECTIVE.md` / `MASTER_PLAN.md` の参照）
  - ISSUE レビューフェーズ（現在 `/split_plan` / `/quick_plan` に重複記載されている手順をここに集約）
  - `status: ready` / `assigned: ai` の ISSUE 抽出（着手候補の取得）
  - 今回取り組む候補を 1〜2 件に絞り、ROUGH_PLAN.md を作成
  - ROUGH_PLAN.md の冒頭 frontmatter に `workflow: quick | full` と `source: issues | master_plan` を記録
  - review は実施しない（plan_review_agent は起動しない）
- ワークフロー選択ルール（MASTER_PLAN PHASE6.0 §2-1 準拠）:
  - 選定 ISSUE に `review` が 1 件でも含まれれば `full`
  - MASTER_PLAN 新項目 / アーキテクチャ変更 / 新規ライブラリ導入を含むなら `full`
  - 全 `ready` で小規模変更なら `quick`
  - 迷う場合は安全側で `full`

### 2. 既存 `/split_plan` SKILL の責務縮小

- `.claude/skills/split_plan/SKILL.md` を「後半ステップ」の責務に書き換える
- 新しい責務:
  - `ROUGH_PLAN.md`（既に `/issue_plan` で作成済み）を読み、対象タスクを固定
  - REFACTOR.md / IMPLEMENT.md を作成
  - plan_review_agent を起動して実装計画の review を実施（SKILL 内で唯一 review を行うステップ）
- 削除する責務（`/issue_plan` に移管したもの）:
  - 現状把握・ISSUE レビューフェーズ・ISSUE 選定
  - ROUGH_PLAN.md 新規作成とその review
- バージョン種別判定（メジャー / マイナー）の記述は `/issue_plan` 側にも残すため、`/split_plan` には不要

### 3. 既存 `/quick_plan` SKILL の責務縮小

- `.claude/skills/quick_plan/SKILL.md` を `/issue_plan` の後続ステップとして再定義、もしくは deprecated 案内に統合
- 本バージョンでの採用方針（MASTER_PLAN PHASE6.0 §2-3 の推奨案）:
  - quick ワークフローの先頭を `/issue_plan` に置き換え、`/quick_plan` は quick 専用の実装計画作成ステップとして残す（= full の `/split_plan` 相当の後半ステップ）
  - または、quick では前半のみで実装計画を省略する既存方針を維持し、`/quick_plan` 自体を quick YAML から削除する
  - どちらを採るかは IMPLEMENT.md で確定する（※ROUGH_PLAN では決めない）

### 4. ワークフロー YAML の先頭ステップ差し替え

- `scripts/claude_loop.yaml`（full）と `scripts/claude_loop_quick.yaml`（quick）の 1 ステップ目を `/issue_plan` に差し替える
- 後続ステップのモデル・effort 指定・continue フラグは現状を維持
- full は `/issue_plan → /split_plan → /imple_plan → /wrap_up → /write_current → /retrospective` の 6 ステップ
- quick は `/issue_plan → /quick_impl → /quick_doc` の 3 ステップ（`/quick_plan` を削除する案を採った場合）

### 5. ドキュメント最小更新

- `scripts/README.md` の「フルワークフロー」「軽量ワークフロー」セクションで先頭ステップ名を更新
- `ISSUES/README.md` / プロジェクトルート `CLAUDE.md` / `.claude/CLAUDE.md` の記述に `/split_plan` / `/quick_plan` が登場するかを確認し、登場する場合のみ最小限の用語整合を取る

## スコープ外（本バージョンではやらないこと）

以下は PHASE6.0 §3 / §5 に属し、ver8.1 以降で扱う:

- `scripts/claude_loop.py` の `--workflow auto` 導入（予約値解決、`issue_plan` 実行後の分岐ロジック）
- `scripts/claude_loop_issue_plan.yaml`（`/issue_plan` 単独実行用 YAML）の新規作成
- `tests/test_claude_loop.py` への `--workflow auto` 分岐テスト追加
- `.claude/skills/meta_judge/WORKFLOW.md` の自動選択フロー図の更新
- `retrospective` SKILL 側の `issue_worklist.py` 追加利用（ver7.0 で適用済み）

これらは `/issue_plan` の SKILL が確立した後に一体で扱うほうが安全で、本バージョンの変更量を抑えるためにも分離する。

## 方針への補足

- **変更対象ファイル見込み**: 新規 1（`issue_plan/SKILL.md`）+ 既存編集 2〜3（`split_plan/SKILL.md` / `quick_plan/SKILL.md` or 削除 / 2 YAML ファイル）+ ドキュメント微修正。4 ファイル超となるためメジャーワークフローで妥当
- **`.claude/` 配下編集の権限制約**: ver7.0 RETROSPECTIVE 2-2 の通り、`claude_sync.py` 経由での編集を要する。IMPLEMENT.md で明示する
- **`/issue_plan` では plan_review_agent を起動しない**点は MASTER_PLAN の明記事項。現在 `/split_plan` / `/quick_plan` 冒頭で review を行う運用は `/split_plan`（後半）のみに集約する
- **事前リファクタリング**: 現時点では不要の見込み（既存 SKILL の内容を新 SKILL に切り出すだけで、既存共通ロジック関数の抽出などは発生しない）。必要性は IMPLEMENT.md 作成時に再評価する
