# CURRENT: util ver15.0

util カテゴリのコード現況。ver15.0 で PHASE7.1 §1（`issue_scout` workflow 新設）を実装した状態。

- [CURRENT_scripts.md](CURRENT_scripts.md) — `scripts/` 配下の Python スクリプト・YAML ワークフロー定義・テスト（ver15.0 では `workflow.py` に `SCOUT_YAML_FILENAME` 追加・`claude_loop_scout.yaml` 新規・テスト 3 件追加）
- [CURRENT_skills.md](CURRENT_skills.md) — `.claude/skills/` の SKILL ファイル群・`.claude/rules/` の rule ファイル群（ver15.0 で `issue_scout/SKILL.md` 新規追加）
- [CURRENT_tests.md](CURRENT_tests.md) — `scripts/tests/` 配下の Python テスト構成（ver15.0 での追加・更新）

## 設定ファイル

| ファイル | 役割 |
|---|---|
| `.claude/settings.local.json` | ローカル設定。`PermissionRequest` フックで `^(?!AskUserQuestion)` マッチャーを使用し、AskUserQuestion 以外の権限要求を自動承認。`Edit(**/.claude/**)` / `Write(**/.claude/**)` を許可ツールに追加 |
| `.claude/CURRENT_CATEGORY` | 現在アクティブなカテゴリ名（1行） |
| `.claude/rules/claude_edit.md` | `.claude/**/*` に対して `claude_sync.py` 経由で編集する手順を rules として定義（`paths:` frontmatter で対象ファイルパターンを指定） |
| `.claude/rules/scripts.md` | `scripts/**/*` を対象にした stable 規約（Python 前提・パス操作・CLI 引数・frontmatter/YAML 更新作法・ログ出力）。ver14.0 で新規追加。§3 は ver15.0 `/retrospective` で 4 ファイル同期（`claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` / `claude_loop_scout.yaml`）に更新済 |
| `.gitignore` | `logs/`・`.claude_sync/`・`data/`・`__pycache__/`・`*.pyc` を除外 |

## 非同期コミュニケーション

| ディレクトリ | 役割 |
|---|---|
| `FEEDBACKS/` | ワークフローへのフィードバック。YAML frontmatter `step:` で対象ステップを指定（省略時は全ステップ対象）。`claude_loop.py` が `--append-system-prompt` に注入し、**正常完了後のみ** `FEEDBACKS/done/` へ移動（異常終了時は `FEEDBACKS/` に残り次回 run で再消費される） |

`REQUESTS/AI/` / `REQUESTS/HUMAN/` は ver13.0 で廃止・削除済。AI / 人間への依頼はすべて `ISSUES/{category}/{priority}/*.md` に集約する。

ver14.0 以降、`/retrospective` SKILL は「次ループで読ませたい補助入力」を `FEEDBACKS/handoff_ver*_to_next.md` として書き出せる（§4.5 handoff）。handoff ファイルも通常 FEEDBACK と同じ消費経路（1回読まれた後 `FEEDBACKS/done/` へ移動）で処理される。

## ワークフロー体系

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

起動: `python scripts/claude_loop.py --workflow scout --category <cat>`  
出力: `ISSUES/{cat}/{priority}/` への新規 ISSUE 起票（0〜3 件）のみ。コード実装・ドキュメント更新は行わない。

### `--workflow auto`（デフォルト）

`python scripts/claude_loop.py` のデフォルト挙動。2 段実行でワークフローを自動選択する:

1. `claude_loop_issue_plan.yaml`（1 ステップ）で `/issue_plan` を先行実行
2. 生成された最新 `ROUGH_PLAN.md` の frontmatter `workflow:` を読む
3. `quick` → `claude_loop_quick.yaml` の `steps[1:]`、`full` → `claude_loop.yaml` の `steps[1:]` を実行
4. `workflow:` 未記載・不正値 → `full` にフォールバック（警告を stderr/ログに出力）
5. `--workflow auto` + `--start N>1` は併用不可（SystemExit）

### 起動前 validation

`claude_loop.py` の `main()` が step 1 実行前に `validate_startup()` を呼び出す。詳細は [CURRENT_scripts.md](CURRENT_scripts.md) の「validation.py モジュール」節を参照。

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

### util カテゴリの ISSUES 状況（ver15.0 完了時点）

| ファイル | priority | status | assigned |
|---|---|---|---|
| `ISSUES/util/medium/issue-review-rewrite-verification.md` | medium | ready | ai |
| `ISSUES/util/medium/issue-scout-noise-risk.md` | medium | raw | ai |
| `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md` | low | raw | ai |
| `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md` | low | raw | ai |
