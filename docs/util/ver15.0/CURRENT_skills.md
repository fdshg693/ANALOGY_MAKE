# CURRENT_skills: util ver15.0 — SKILL ファイル・rules ファイル・サブエージェント

ver15.0 で `issue_scout/SKILL.md` を新規追加。その他の SKILL・rules・サブエージェントは ver14.0 と同一。

## rules ファイル

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/rules/claude_edit.md` | 12 | `.claude/**/*` 編集時の `claude_sync.py` 手順を定義。`paths:` frontmatter で適用対象を限定 |
| `.claude/rules/scripts.md` | — | `scripts/**/*` を対象にした stable 規約（Python 前提・パス操作・CLI 引数・frontmatter/YAML 更新作法・ログ出力）。ver14.0 で新規追加。ver15.2 で §3 を「5 ファイル間同期」（`claude_loop_question.yaml` 追加）・§4 に `questions.py` 参照注記を追記 |

## フルワークフロー（6 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `issue_plan/SKILL.md` | 102 | ステップ 1: 現状把握・ISSUE レビュー・ISSUE/MASTER_PLAN 選定・ROUGH_PLAN.md 作成・workflow 判定。`issue_worklist.py --limit 20` で ISSUE 一覧を取得。FEEDBACK handoff 受信指示あり |
| `split_plan/SKILL.md` | 38 | ステップ 2: REFACTOR/IMPLEMENT 作成 + plan_review_agent での review のみ |
| `imple_plan/SKILL.md` | 81 | ステップ 3: 実装。CURRENT.md + 計画ドキュメントに基づきコード実装。MEMO.md を出力。検証先送りリスクは `ISSUES/` に独立ファイルを作成 |
| `wrap_up/SKILL.md` | 46 | ステップ 4: 残課題対応。MEMO.md の項目を ✅完了 / ⏭️不要 / 📋先送り に分類し、ISSUES 整理 |
| `write_current/SKILL.md` | 83 | ステップ 5: ドキュメント更新。メジャー版は CURRENT.md、マイナー版は CHANGES.md を作成。150 行超の場合は `CURRENT_{トピック名}.md` に分割 |
| `retrospective/SKILL.md` | 182 | ステップ 6: 振り返り。§3.5（workflow prompt/model 評価）・§4.5（FEEDBACK handoff）を含む |

## 軽量ワークフロー quick（3 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `issue_plan/SKILL.md` | 102 | ステップ 1: quick でも同じ前半ステップを使用 |
| `quick_impl/SKILL.md` | 43 | ステップ 2: 実装 + MEMO 対応を統合 |
| `quick_doc/SKILL.md` | 55 | ステップ 3: CHANGES.md 作成 + CLAUDE.md 更新確認 + ISSUES 整理 + コミット＆プッシュ |

## 能動探索ワークフロー scout（1 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/skills/issue_scout/SKILL.md` | 149 | **ver15.0 新規。** 潜在課題の能動探索と ISSUE 起票専用 SKILL（直接起動 or `--workflow scout` 経由） |

### `issue_scout/SKILL.md` の構成

frontmatter: `name: issue_scout` / `disable-model-invocation: true` / `user-invocable: true`

本文 7 節構成:
1. **コンテキスト** — 現カテゴリ・最新バージョン・既存 ISSUES 分布（`issue_status.py`）・直近 RETROSPECTIVE・MASTER_PLAN 進捗をシェル補間で注入
2. **役割** — ISSUE 起票のみ。コード実装・テスト修正・ドキュメント更新・バージョンディレクトリ作成をしないことを明記
3. **探索手順（3 段階）** — 既存資産の棚卸し → 潜在課題の抽出（壊れ兆候・docs×実装乖離・RETROSPECTIVE 未 ISSUE 化事項）→ 重複排除ゲート
4. **起票ルール** — 最大 3 件・`status: raw` / `assigned: ai` 既定（昇格条件を満たす場合のみ `ready / ai` 許可）・`priority` 必須・ファイル命名規約・本文テンプレ
5. **サマリ報告** — 起票件数・パス一覧・スキップ件数を stdout に出力
6. **やらないこと** — コード修正 / テスト実行 / ドキュメント更新 / `.claude/` 編集 / `docs/{cat}/ver*/` 作成 / 既存 ISSUE の書き換え
7. **Git コミット** — 新規 ISSUE 起票のみをコミット。プッシュしない

重複検出: タイトル正規化後の完全一致 + 本文冒頭 50 文字の Jaccard ≥ 0.5 をヒューリスティックとして SKILL 内で実施（Python スクリプト化せず）。

## 調査専用ワークフロー question（1 ステップ）

**ver15.2 新規。** `--workflow question` で起動する opt-in 調査専用 workflow。`--workflow auto` には混入しない。`QUESTIONS/` queue を専属で扱い、既存 ISSUES flow とは完全に独立。

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/skills/question_research/SKILL.md` | — | **ver15.2 新規。** `QUESTIONS/` の `ready / ai` を 1 件調査し、`docs/{category}/questions/{slug}.md` に固定 5 セクション報告書を出力する専用 SKILL |

### `question_research/SKILL.md` の構成

frontmatter: `name: question_research` / `disable-model-invocation: true` / `user-invocable: true`

本文構成:
1. **コンテキスト** — 現カテゴリ・最新バージョン・既存 QUESTIONS 分布（`question_status.py`）をシェル補間で注入
2. **役割** — 調査報告書の出力のみ。コード実装・テスト修正・デプロイまで進めないことを明記
3. **調査手順（3 段階）** — Question 選定（`question_worklist.py` で最上位優先度 `ready/ai` を 1 件）→ 証拠収集（コードベース・docs・既存 ISSUE・外部資料）→ 結論判定
4. **報告書の出力（固定 5 セクション）** — `docs/{category}/questions/{slug}.md` に「問い / 確認した証拠 / 結論 / 不確実性 / 次アクション候補」を必須出力
5. **後処理ルール** — 結論確定 → `QUESTIONS/{category}/done/` へ `git mv`・実装課題は `ISSUES/` に起票。結論未確定 → `need_human_action / human` に書き換え（`done/` 移動なし）
6. **やらないこと** — コード実装 / テスト実行 / バージョンディレクトリ作成 / `.claude/` 編集 / Question 以外の ISSUES 操作
7. **Git コミット** — 報告書・Question 移動・新規 ISSUE 起票のみをコミット。プッシュしない

## ISSUE レビュー仕様書

| ファイル | 行数 | 役割 |
|---|---|---|
| `issue_review/SKILL.md` | 99 | ISSUE レビューフェーズの一次資料。`/issue_plan` が参照し、スキャン → 個別レビュー → 書き換えガード → サマリ報告 の手順を定義。**直接起動しない** |

## メタ評価・ワークフロー文書

| ファイル | 行数 | 役割 |
|---|---|---|
| `meta_judge/SKILL.md` | 18 | メタ評価。ワークフロー全体の有効性を評価する手動実行専用 SKILL |
| `meta_judge/WORKFLOW.md` | 49 | 保守上の注意（4 ファイル同期義務・`--workflow auto` 実装済み）を定義 |

## サブエージェント

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/agents/plan_review_agent.md` | 17 | 計画レビュー専用エージェント。Sonnet モデル、Read/Glob/Grep のみ使用。`/split_plan` で利用（quick ワークフローでは使用しない） |
