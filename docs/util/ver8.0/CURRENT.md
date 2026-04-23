# CURRENT: util ver8.0

util カテゴリのコード現況。ver7.0 で PHASE6.0 §1（`issue_worklist.py` 新設・`/retrospective` 活用）を実装した後、ver8.0 で PHASE6.0 §2 として `/issue_plan` SKILL を新設し、プラン前半（現状把握・ISSUE 選定・ROUGH_PLAN 作成）を前段の共通ステップに切り出した。`/split_plan` を後半専用に縮小し、`/quick_plan` を削除した状態。

- [CURRENT_skills.md](CURRENT_skills.md) — `.claude/skills/` の SKILL ファイル群・サブエージェント
- [CURRENT_scripts.md](CURRENT_scripts.md) — `scripts/` 配下の Python スクリプトと YAML ワークフロー定義
- [CURRENT_tests.md](CURRENT_tests.md) — `tests/test_claude_loop.py` のユニットテスト構成

## 設定ファイル

| ファイル | 役割 |
|---|---|
| `.claude/settings.local.json` | ローカル設定。`PermissionRequest` フックで `^(?!AskUserQuestion)` マッチャーを使用し、AskUserQuestion 以外の権限要求を自動承認。`Edit(**/.claude/**)` / `Write(**/.claude/**)` を許可ツールに追加 |
| `.claude/CURRENT_CATEGORY` | 現在アクティブなカテゴリ名（1行） |
| `.claude/rules/claude_edit.md` | **ver8.0 で追加**。`.claude/**/*` に対して `claude_sync.py` 経由で編集する手順を rules として定義（`paths:` frontmatter で対象ファイルパターンを指定） |
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

### ワークフロー選択ガイドライン

| 条件 | 推奨 |
|---|---|
| MASTER_PLAN の新項目着手 | full |
| アーキテクチャ変更・新規ライブラリ導入 | full |
| 変更ファイル 4 つ以上（※） | full |
| ISSUES/high の対応（複雑） | full |
| ISSUES の 1 件対応（単純） | quick |
| バグ修正（原因特定済み） | quick |
| 既存機能の微調整・ドキュメント追加 | quick |
| 変更ファイル 3 つ以下 | quick |

※ 全ファイルがテキスト編集のみで各ファイルの変更が数行程度の場合は quick を推奨

### 実行方法

```bash
python scripts/claude_loop.py                                   # フルワークフロー
python scripts/claude_loop.py -w scripts/claude_loop_quick.yaml # 軽量ワークフロー
python scripts/claude_loop.py --start 3                         # ステップ 3 から開始
python scripts/claude_loop.py --auto                            # 自動実行モード
python scripts/claude_loop.py --auto-commit-before              # ワークフロー前に自動コミット
```

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

frontmatter 無しのファイルは後方互換として `raw / human` 扱い。

### 分布確認・一覧取得コマンド

```bash
python scripts/issue_status.py            # 全カテゴリの status × assigned 分布
python scripts/issue_status.py util       # カテゴリ指定

python scripts/issue_worklist.py          # 現在カテゴリの AI 向け ready/review 一覧（text）
python scripts/issue_worklist.py --format json      # JSON 出力（機械可読）
python scripts/issue_worklist.py --category app     # カテゴリ指定
python scripts/issue_worklist.py --assigned human --status need_human_action
```

### util カテゴリの ISSUES 状況（ver8.0 完了時点）

| ファイル | priority | status | assigned |
|---|---|---|---|
| `ISSUES/util/medium/issue-review-rewrite-verification.md` | medium | ready | ai |
| `ISSUES/util/medium/issue-plan-split-plan-handoff-verification.md` | medium | ready | ai |
| `ISSUES/util/low/issue-worklist-json-context-bloat.md` | low | ready | ai |
| `ISSUES/util/low/issue-plan-standalone-yaml.md` | low | ready | ai |
