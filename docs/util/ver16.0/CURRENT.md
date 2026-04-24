# CURRENT: util ver16.0

util カテゴリのコード現況。ver16.0 で PHASE8.0 §1（`research` workflow 新設）を実装した状態。

- [CURRENT_scripts.md](CURRENT_scripts.md) — `scripts/` 配下の Python スクリプト・YAML ワークフロー定義・テスト（ver16.0 では `WORKFLOW_YAML_FILES` レジストリ化・`claude_loop_research.yaml` 新規・テスト 4 件追加で計 280 件）
- [CURRENT_skills.md](CURRENT_skills.md) — `.claude/skills/` の SKILL ファイル群・`.claude/rules/` の rule ファイル群（ver16.0 で `research_context` / `experiment_test` SKILL 新規追加。`use-tavily` は ver15.6〜ver16.0 間で追加）

## 設定ファイル

| ファイル | 役割 |
|---|---|
| `.claude/settings.local.json` | ローカル設定。`PermissionRequest` フックで `^(?!AskUserQuestion)` マッチャーを使用し、AskUserQuestion 以外の権限要求を自動承認。`Edit(**/.claude/**)` / `Write(**/.claude/**)` を許可ツールに追加 |
| `.claude/CURRENT_CATEGORY` | 現在アクティブなカテゴリ名（1行） |
| `.claude/rules/claude_edit.md` | `.claude/**/*` に対して `claude_sync.py` 経由で編集する手順を rules として定義（`paths:` frontmatter で対象ファイルパターンを指定） |
| `.claude/rules/scripts.md` | `scripts/**/*` を対象にした stable 規約（Python 前提・パス操作・CLI 引数・frontmatter/YAML 更新作法・ログ出力）。§3 は ver16.0 で 5 ファイル同期 → 6 ファイル同期に更新済（`claude_loop_research.yaml` 追加） |
| `.gitignore` | `logs/`・`.claude_sync/`・`data/`・`__pycache__/`・`*.pyc` を除外 |

## 非同期コミュニケーション

| ディレクトリ | 役割 |
|---|---|
| `FEEDBACKS/` | ワークフローへのフィードバック。YAML frontmatter `step:` で対象ステップを指定（省略時は全ステップ対象）。`claude_loop.py` が `--append-system-prompt` に注入し、**正常完了後のみ** `FEEDBACKS/done/` へ移動 |

ver14.0 以降、`/retrospective` SKILL は「次ループで読ませたい補助入力」を `FEEDBACKS/handoff_ver*_to_next.md` として書き出せる（消費後 `done/` へ移動）。

## ワークフロー体系（ver16.0 時点）

### フルワークフロー（`claude_loop.yaml`）

6 ステップの完全ワークフロー。メジャーバージョン・アーキテクチャ変更・4 ファイル以上の変更に使用。

```
/issue_plan → /split_plan → /imple_plan → /wrap_up → /write_current → /retrospective
```

### 軽量ワークフロー quick（`claude_loop_quick.yaml`）

3 ステップの簡略ワークフロー。マイナーバージョン・単一 ISSUE 対応・3 ファイル以下の変更に使用。

```
/issue_plan → /quick_impl → /quick_doc
```

### 能動探索ワークフロー scout（`claude_loop_scout.yaml`）

ver15.0 で新設。1 ステップの opt-in 探索専用ワークフロー。`--workflow auto` には**自動混入しない**。

```
/issue_scout
```

### 調査専用ワークフロー question（`claude_loop_question.yaml`）

ver15.2 で新設。1 ステップの opt-in 調査専用ワークフロー。`--workflow auto` には**自動混入しない**。`QUESTIONS/` queue を専属で扱う。

```
/question_research
```

### 調査・実験ワークフロー research（`claude_loop_research.yaml`）

**ver16.0 新設。** 8 ステップ。実装前に調査・実験 step を正式に挟む。`--workflow auto` の対象（`workflow: research` frontmatter で選択される）。

```
/issue_plan → /split_plan → /research_context → /experiment_test → /imple_plan → /wrap_up → /write_current → /retrospective
```

#### research workflow の成果物

| 成果物 | 生成 SKILL | 出力先 | 必須 4 節 |
|---|---|---|---|
| `RESEARCH.md` | `/research_context` | `docs/{cat}/ver{X.Y}/RESEARCH.md` | `## 問い` / `## 収集した証拠` / `## 結論` / `## 未解決点` |
| `EXPERIMENT.md` | `/experiment_test` | `docs/{cat}/ver{X.Y}/EXPERIMENT.md` | `## 検証した仮説` / `## 再現手順` / `## 結果` / `## 判断` |

`RESEARCH.md` / `EXPERIMENT.md` は `full` / `quick` workflow では存在しない。`/imple_plan` は存在すれば読む・存在しなければエラーにしない（条件分岐）。

### `--workflow auto`（デフォルト）

`python scripts/claude_loop.py` のデフォルト挙動。2 段実行でワークフローを自動選択する:

1. `claude_loop_issue_plan.yaml`（1 ステップ）で `/issue_plan` を先行実行
2. 生成された最新 `ROUGH_PLAN.md` の frontmatter `workflow:` を読む
3. `quick` → `claude_loop_quick.yaml`、`full` → `claude_loop.yaml`、`research` → `claude_loop_research.yaml` の `steps[1:]` を実行（ver16.0 で 3 分岐化）
4. `workflow:` 未記載・不正値 → `full` にフォールバック（警告を stderr/ログに出力）
5. `--workflow auto` + `--start N>1` は併用不可（SystemExit）

`scout` / `question` は `auto` 非対象（`_run_auto` が参照しない保証）。

### `--workflow auto` での `workflow: research` 選定条件

以下 4 条件のうち **いずれか 1 つ**を満たし、かつ MASTER_PLAN 新項目 / アーキテクチャ変更 / 新規ライブラリ導入を含む場合に `research`:

1. 外部仕様・公式 docs の確認が主要成果に影響する
2. 実装方式を実験で絞り込む必要がある
3. 1 step で 5 分以上を要する実測系の長時間検証が事前に必要
4. 軽い隔離環境（`experiments/` 配下）での試行が前提

判断に迷う場合は `full` 優先（「迷ったら full」原則を継承）。

### 起動前 validation

`claude_loop.py` の `main()` が step 1 実行前に `validate_startup()` を呼び出す。ver16.0 で auto 対象 YAML が 4 本（issue_plan / full / quick / research）に拡大。詳細は [CURRENT_scripts.md](CURRENT_scripts.md) を参照。

## ISSUES 管理

`ISSUES/{category}/{high,medium,low}/` 以下の各 `*.md` ファイルに YAML frontmatter でステータスと担当を管理する。詳細仕様は `ISSUES/README.md` を参照。

### status × assigned の組み合わせ

| 組み合わせ | 意味 |
|---|---|
| `raw / human` | 人間の書きかけメモ。plan ステップは拾わない |
| `raw / ai` | AI 側の未整理メモ（`issue_scout` 起票の既定値） |
| `review / ai` | 人間 → AI へのレビュー依頼。次回 plan 冒頭で処理 |
| `ready / ai` | 着手可能。plan ステップの拾い上げ対象 |
| `need_human_action / human` | AI では判断不能。人間の対応待ち |

### QUESTIONS 管理

ver15.2 で新設。`QUESTIONS/{category}/{high,medium,low}/` 以下に `status: ready` / `assigned: ai` の調査依頼を投入。`--workflow question` で `question_research` SKILL が最上位優先度 1 件を調査し `docs/{cat}/questions/{slug}.md` に報告書を出力。`ISSUES/` とは完全に独立したキュー。

### util カテゴリの ISSUES 状況（ver16.0 完了時点）

| ファイル | priority | status | assigned |
|---|---|---|---|
| `ISSUES/util/medium/issue-review-rewrite-verification.md` | medium | ready | ai |
| `ISSUES/util/low/toast-persistence-verification.md` | low | ready | ai |
| `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md` | low | raw | ai |
| `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md` | low | raw | ai |

## experiments/ ディレクトリ（ver16.0 新設ルール）

`experiments/` は実装前の仮説検証・隔離試行の置き場（production コードではない）。`experiments/README.md` に以下規約を定義:

- 新しい依存は `experiments/{slug}/` サブディレクトリに閉じる（ルート依存を増やさない）
- 残すスクリプトの先頭コメントに「何を確かめるためか」「いつ削除してよいか」を必須記載
- `scripts/` = CI / 他 SKILL が呼ぶ production コード。`experiments/` = 試行錯誤・検証・他 SKILL が参照しない一時コード

`/experiment_test` SKILL は `experiments/` 配下でスクリプトを作成・実行し `EXPERIMENT.md` を生成する。
