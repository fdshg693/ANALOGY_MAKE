# CURRENT: util ver12.0

util カテゴリのコード現況。ver12.0 で PHASE7.0 §2「起動前 validation」を実装した状態。`scripts/claude_loop_lib/validation.py` を新規追加し、`claude_loop.py` の `main()` に `validate_startup()` 呼び出しを挿入した。PHASE7.0 §1 完了条件③（無効 model 名 / 未解決 prompt 参照 / 型不正設定値の事前検出）も同時に充足。

- [CURRENT_scripts.md](CURRENT_scripts.md) — `scripts/` 配下の Python スクリプト・YAML ワークフロー定義・新規 `validation.py` モジュール
- [CURRENT_skills.md](CURRENT_skills.md) — `.claude/skills/` の SKILL ファイル群・サブエージェント（ver11.0 から変更なし）
- [CURRENT_tests.md](CURRENT_tests.md) — `scripts/tests/` 配下の Python テスト構成（`test_validation.py` 追加）

## 設定ファイル

| ファイル | 役割 |
|---|---|
| `.claude/settings.local.json` | ローカル設定。`PermissionRequest` フックで `^(?!AskUserQuestion)` マッチャーを使用し、AskUserQuestion 以外の権限要求を自動承認。`Edit(**/.claude/**)` / `Write(**/.claude/**)` を許可ツールに追加 |
| `.claude/CURRENT_CATEGORY` | 現在アクティブなカテゴリ名（1行） |
| `.claude/rules/claude_edit.md` | `.claude/**/*` に対して `claude_sync.py` 経由で編集する手順を rules として定義（`paths:` frontmatter で対象ファイルパターンを指定） |
| `.gitignore` | `logs/`・`.claude_sync/`・`data/`・`__pycache__/`・`*.pyc` を除外 |

## 非同期コミュニケーション

| ディレクトリ | 役割 |
|---|---|
| `REQUESTS/AI/` | AI → ユーザーへの確認事項。自動実行モードで質問が必要な場合の代替手段 |
| `REQUESTS/HUMAN/` | ユーザー → AI への要望 |
| `FEEDBACKS/` | ワークフローへのフィードバック。YAML frontmatter `step:` で対象ステップを指定（省略時は全ステップ対象）。`claude_loop.py` が `--append-system-prompt` に注入し、正常完了後 `FEEDBACKS/done/` へ移動 |

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

### `--workflow auto`（デフォルト）

`python scripts/claude_loop.py` のデフォルト挙動。2 段実行でワークフローを自動選択する:

1. `claude_loop_issue_plan.yaml`（1 ステップ）で `/issue_plan` を先行実行
2. 生成された最新 `ROUGH_PLAN.md` の frontmatter `workflow:` を読む
3. `quick` → `claude_loop_quick.yaml` の `steps[1:]`、`full` → `claude_loop.yaml` の `steps[1:]` を実行
4. `workflow:` 未記載・不正値 → `full` にフォールバック（警告を stderr/ログに出力）
5. `--workflow auto` + `--start N>1` は併用不可（SystemExit）

### 起動前 validation（ver12.0 新規）

`claude_loop.py` の `main()` が step 1 実行前に `validate_startup()` を呼び出す。詳細は [CURRENT_scripts.md](CURRENT_scripts.md) の「validation.py モジュール」節を参照。

## ISSUES 管理

`ISSUES/{category}/{high,medium,low}/` 以下の各 `*.md` ファイルに YAML frontmatter でステータスと担当を管理する。詳細仕様は `ISSUES/README.md` を参照。

### status × assigned の組み合わせ

| 組み合わせ | 意味 |
|---|---|
| `raw / human` | 人間の書きかけメモ。plan ステップは拾わない |
| `raw / ai` | AI 側の未整理メモ |
| `review / ai` | 人間 → AI へのレビュー依頼。次回 plan 冒頭で処理 |
| `ready / ai` | 着手可能。plan ステップの拾い上げ対象 |
| `need_human_action / human` | AI では判断不能。人間の対応待ち |

### util カテゴリの ISSUES 状況（ver12.0 完了時点）

| ファイル | priority | status | assigned |
|---|---|---|---|
| `ISSUES/util/medium/issue-review-rewrite-verification.md` | medium | ready | ai |
| `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md` | medium | raw | ai |
| `ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md` | medium | raw | ai |
| `ISSUES/util/low/system-prompt-replacement-behavior-risk.md` | low | raw | ai |
