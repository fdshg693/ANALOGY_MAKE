# CURRENT_skills: util ver16.0 — SKILL ファイル・rules ファイル・サブエージェント

ver16.0 で `research_context` / `experiment_test` SKILL を新規追加。`use-tavily` は ver15.6〜ver16.0 間（`fde646f` コミット）で追加済み。その他 SKILL は ver15.0〜ver15.3 の変更を継承した状態。

## rules ファイル

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/rules/claude_edit.md` | 12 | `.claude/**/*` 編集時の `claude_sync.py` 手順を定義。`paths:` frontmatter で適用対象を限定 |
| `.claude/rules/scripts.md` | — | `scripts/**/*` を対象にした stable 規約（Python 前提・パス操作・CLI 引数・frontmatter/YAML 更新作法・ログ出力）。§3 は ver16.0 で 6 ファイル同期（`claude_loop_research.yaml` 追加） |

## フルワークフロー（6 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `issue_plan/SKILL.md` | 152 | ステップ 1: 現状把握・ISSUE レビュー・ISSUE/MASTER_PLAN 選定・ROUGH_PLAN.md + PLAN_HANDOFF.md 作成・workflow 判定（ver16.0 で `workflow: quick\|full\|research` の 3 値対応に拡張） |
| `split_plan/SKILL.md` | 46 | ステップ 2: REFACTOR/IMPLEMENT 作成 + plan_review_agent でのレビュー。ver16.0 で「research workflow 時の追加注意」節（`IMPLEMENT.md` の「リスク・不確実性」節の具体化指示）を末尾に追加 |
| `imple_plan/SKILL.md` | 98 | ステップ 3: 実装。CURRENT.md + 計画ドキュメントに基づきコード実装。ver16.0 で「`RESEARCH.md` / `EXPERIMENT.md` が存在すれば読む、なければエラーにしない」を入力読み込み節に追記 |
| `wrap_up/SKILL.md` | 46 | ステップ 4: 残課題対応。MEMO.md の項目を ✅完了 / ⏭️不要 / 📋先送り に分類し ISSUES 整理 |
| `write_current/SKILL.md` | 83 | ステップ 5: ドキュメント更新。メジャー版は CURRENT.md、マイナー版は CHANGES.md を作成。150 行超の場合は `CURRENT_{トピック名}.md` に分割 |
| `retrospective/SKILL.md` | 184 | ステップ 6: 振り返り。§3.5（workflow prompt/model 評価）・§4.5（FEEDBACK handoff）を含む |

## 軽量ワークフロー quick（3 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `issue_plan/SKILL.md` | 152 | ステップ 1: quick でも同じ SKILL を使用 |
| `quick_impl/SKILL.md` | 44 | ステップ 2: 実装 + MEMO 対応を統合。「ワークフロー YAML 同期チェック」を実装品質ガイドラインに含む（ver15.2） |
| `quick_doc/SKILL.md` | 55 | ステップ 3: CHANGES.md 作成 + CLAUDE.md 更新確認 + ISSUES 整理 + コミット＆プッシュ |

## 能動探索ワークフロー scout（1 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `issue_scout/SKILL.md` | 149 | ver15.0 新規。潜在課題の能動探索と ISSUE 起票専用 SKILL |

### `issue_scout/SKILL.md` の構成

frontmatter: `name: issue_scout` / `disable-model-invocation: true` / `user-invocable: true`

7 節構成: コンテキスト / 役割 / 探索手順（3 段階：棚卸し→抽出→重複排除） / 起票ルール（最大 3 件、`raw/ai` 既定） / サマリ報告 / やらないこと / Git コミット

## 調査専用ワークフロー question（1 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `question_research/SKILL.md` | 116 | ver15.2 新規。`QUESTIONS/` の `ready/ai` を 1 件調査し、`docs/{cat}/questions/{slug}.md` に固定 5 セクション報告書を出力 |

報告書の固定 5 セクション: `## 問い` / `## 確認した証拠` / `## 結論` / `## 不確実性` / `## 次アクション候補`

## 調査・実験ワークフロー research（8 ステップ）— ver16.0 新設

| ファイル | 行数 | 役割 |
|---|---|---|
| `research_context/SKILL.md` | 82 | **ver16.0 新規。** research workflow の 3 step 目。外部調査（公式 docs / 仕様の裏取り）を行い `RESEARCH.md` を生成 |
| `experiment_test/SKILL.md` | 84 | **ver16.0 新規。** research workflow の 4 step 目。`experiments/` 配下でスクリプトを書いて検証し `EXPERIMENT.md` を生成 |

### `research_context/SKILL.md` の構成

frontmatter: `name: research_context` / `disable-model-invocation: true` / `user-invocable: true`

`## 役割` で `question_research` との責務境界テーブル（3 観点）を明示:

| 観点 | `question` | `research` |
|---|---|---|
| (a) 最終成果物 | 報告書のみ | コード変更（RESEARCH.md は中間成果物） |
| (b) 入力キュー | `QUESTIONS/` | `ISSUES/` または MASTER_PLAN |
| (c) workflow | 調査→報告書で終了 | 調査→実験→実装→retrospective まで 8 step 完走 |

手順 3 段階: 入力読み込み（ROUGH_PLAN.md / PLAN_HANDOFF.md / REFACTOR.md / IMPLEMENT.md の「リスク・不確実性」節）→ 外部調査（3 箇所以上で裏取り、証拠は URL + 参照日 + 要約）→ `RESEARCH.md` 出力（4 節必須）

### `experiment_test/SKILL.md` の構成

frontmatter: `name: experiment_test` / `disable-model-invocation: true` / `user-invocable: true`

`experiments/` ディレクトリ運用ルール（ver16.0 新設）を内包:

- 新しい依存は `experiments/{slug}/` に閉じる
- 残すスクリプトの先頭コメントに「何を確かめるためか」「いつ削除してよいか」を必須記載

手順 3 段階: 仮説整理（`RESEARCH.md` の「未解決点」から抽出）→ 実験スクリプト作成・実行（`experiments/` 配下）→ `EXPERIMENT.md` 出力（4 節必須）

`## 長時間コマンドの扱い（ver16.1 以降の拡張ポイント）`: 本 step では同期実行に限定。5 分超の場合は「未検証」として `EXPERIMENT.md` に明記し ver16.1 の deferred execution に委譲。

## use-tavily SKILL（外部調査補助）

| ファイル | 役割 |
|---|---|
| `use-tavily/SKILL.md` | 161 行。Tavily を使った外部調査の実務ルール・判断フロー |
| `use-tavily/src/search_topic.py` | キーワード検索 |
| `use-tavily/src/extract_url_content.py` | URL 単体の本文抽出 |
| `use-tavily/src/crawl_site_content.py` | サイト全体のクロール |
| `use-tavily/src/map_site_titles.py` | サイトのページ一覧取得 |
| `use-tavily/src/map_extract_site_content.py` | ページ一覧 + 本文抽出の組み合わせ |
| `use-tavily/src/search_extract_topic.py` | 検索 + 本文抽出の組み合わせ |
| `use-tavily/src/research_topic.py` | トピック調査の総合ヘルパ |
| `use-tavily/src/tavily_common.py` | 共通ユーティリティ |
| `use-tavily/.env.example` | `TAVILY_API_KEY` 環境変数の設定例 |

`/research_context` SKILL はこの `use-tavily` SKILL を前提として外部調査を行う。

## issue_plan/SKILL.md のワークフロー選択ロジック（ver16.0 拡張後）

```
- review ISSUE が 1 件でも含まれる → full
- MASTER_PLAN 新項目 / アーキテクチャ変更 / 新規ライブラリ導入を含み、かつ 4 条件いずれか 1 つを満たす → research
  - 外部仕様・公式 docs の確認が主要成果に影響する
  - 実装方式を実験で絞り込む必要がある
  - 1 step で 5 分以上を要する実測系の長時間検証が前提
  - 軽い隔離環境（experiments/）での試行が前提
- MASTER_PLAN 新項目 / アーキテクチャ変更だが 4 条件に該当しない → full
- 全 ready かつ 3 ファイル以下・100 行以下の見込み → quick
- 迷ったら → full
```

`ROUGH_PLAN.md` frontmatter 許容値: `workflow: full | quick | research`

## メタ評価・ワークフロー文書

| ファイル | 行数 | 役割 |
|---|---|---|
| `meta_judge/SKILL.md` | 18 | メタ評価。ワークフロー全体の有効性を評価する手動実行専用 SKILL |
| `meta_judge/WORKFLOW.md` | — | 3 系統（quick / full / research）として再定義（ver16.0）。6 ファイル同期義務・`--workflow auto` 実装済みを記載 |

### `meta_judge/WORKFLOW.md` の 3 系統定義（ver16.0）

- **§1 quick**: `/issue_plan → /quick_impl → /quick_doc`（3 step）
- **§2 full**: `/issue_plan → /split_plan → /imple_plan → /wrap_up → /write_current → /retrospective`（6 step）
- **§3 research**: `/issue_plan → /split_plan → /research_context → /experiment_test → /imple_plan → /wrap_up → /write_current → /retrospective`（8 step）

## ISSUE レビュー仕様書

| ファイル | 行数 | 役割 |
|---|---|---|
| `issue_review/SKILL.md` | 99 | ISSUE レビューフェーズの一次資料。`/issue_plan` が参照。**直接起動しない** |

## サブエージェント

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/agents/plan_review_agent.md` | 17 | 計画レビュー専用エージェント。Sonnet モデル、Read/Glob/Grep のみ使用。`/split_plan` で利用（quick ワークフローでは使用しない） |
