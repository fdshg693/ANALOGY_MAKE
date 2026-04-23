# CURRENT: util ver6.0

util カテゴリのコード現況。ver5.0 でセッション継続機能が完成し、ver6.0 で ISSUE ステータス・担当管理（PHASE5.0）を実装した状態。`issue_review` SKILL の新設、`split_plan` / `quick_plan` への ISSUE レビューフェーズのインライン展開、`scripts/issue_status.py` の追加が主な変更点。

- [CURRENT_skills.md](CURRENT_skills.md) — `.claude/skills/` の SKILL ファイル群・サブエージェント
- [CURRENT_scripts.md](CURRENT_scripts.md) — `scripts/` 配下の Python スクリプトと YAML ワークフロー定義
- [CURRENT_tests.md](CURRENT_tests.md) — `tests/test_claude_loop.py` のユニットテスト構成

## 設定ファイル

| ファイル | 役割 |
|---|---|
| `.claude/settings.local.json` | ローカル設定。`PermissionRequest` フックで `^(?!AskUserQuestion)` マッチャーを使用し、AskUserQuestion 以外の権限要求を自動承認。`Edit(**/.claude/**)` / `Write(**/.claude/**)` を許可ツールに追加（ver6.0 で `/` 始まりから `**/` 始まりに修正し、Windows パスにも正しくマッチするよう修正） |
| `.claude/CURRENT_CATEGORY` | 現在アクティブなカテゴリ名（1行） |
| `.gitignore` | `logs/`（ワークフローログ）、`.claude_sync/`（同期ワークアラウンド一時コピー）、`data/`（SQLite）、`__pycache__/`・`*.pyc` を除外 |

## 非同期コミュニケーション

| ディレクトリ | 役割 |
|---|---|
| `REQUESTS/AI/` | AI → ユーザーへの確認事項を書き出す場所。自動実行モードで質問が必要な場合の代替手段 |
| `REQUESTS/HUMAN/` | ユーザー → AI への要望を記載する場所 |
| `FEEDBACKS/` | ワークフローへのユーザーフィードバック置き場。各 `*.md` は YAML frontmatter の `step:` フィールドで対象ステップを指定（省略時は全ステップ対象）。`claude_loop.py` がステップ実行時に読み込み `--append-system-prompt` に `## User Feedback` セクションとして注入。正常完了後に `FEEDBACKS/done/` へ移動 |

## ワークフロー体系

### フルワークフロー（`claude_loop.yaml`）

5 ステップの完全ワークフロー。メジャーバージョン、アーキテクチャ変更、4 ファイル以上の変更に使用。

```
/split_plan → /imple_plan → /wrap_up → /write_current → /retrospective
```

各ステップに推奨モデル/エフォート値が定義済み（詳細は CURRENT_scripts.md）。

### 軽量ワークフロー quick（`claude_loop_quick.yaml`）

3 ステップの簡略ワークフロー。マイナーバージョン、単一 ISSUE 対応、3 ファイル以下の変更に使用。

```
/quick_plan → /quick_impl → /quick_doc
```

フルワークフローとの主な違い:
- plan_review_agent を使用しない
- IMPLEMENT.md / REFACTOR.md を作成しない（ROUGH_PLAN.md のみ）
- wrap_up を quick_impl に統合
- write_current の代わりに CHANGES.md のみ作成する quick_doc を使用
- retrospective を省略

### ワークフロー選択ガイドライン

| 条件 | 推奨 |
|---|---|
| MASTER_PLAN の新項目着手 | full |
| アーキテクチャ変更・新規ライブラリ導入 | full |
| 変更ファイル 4 つ以上（※） | full |
| ISSUES/high の対応（複雑） | full |
| ISSUES の 1 件対応（単純） | quick |
| バグ修正（原因特定済み） | quick |
| 既存機能の微調整 | quick |
| ドキュメント・テスト追加 | quick |
| 変更ファイル 3 つ以下 | quick |

※ 全ファイルがテキスト編集のみ（SKILL 文言修正・ドキュメント更新等）で、各ファイルの変更が数行程度の場合は quick を推奨

### 実行方法

```bash
python scripts/claude_loop.py                                        # フルワークフロー（デフォルト）
python scripts/claude_loop.py -w scripts/claude_loop_quick.yaml      # 軽量ワークフロー
python scripts/claude_loop.py --start 3                              # ステップ 3 から開始
python scripts/claude_loop.py --max-loops 2                          # 2 ループ実行
python scripts/claude_loop.py --max-step-runs 7                      # 最大 7 ステップ実行
python scripts/claude_loop.py --dry-run                              # コマンド確認のみ（ログなし）
python scripts/claude_loop.py --no-log                               # ログ無効で実行
python scripts/claude_loop.py --log-dir logs/custom                  # ログ出力先を変更
python scripts/claude_loop.py --auto                                 # 自動実行モード
python scripts/claude_loop.py --auto-commit-before                   # ワークフロー前に自動コミット
python scripts/claude_loop.py --no-notify                            # 完了通知を無効化
```

## ISSUES 管理（ver6.0 で追加）

`ISSUES/{category}/{high,medium,low}/` 以下の各 `*.md` ファイルに YAML frontmatter でステータスと担当を管理する。詳細仕様は `ISSUES/README.md` を参照。

### status × assigned の組み合わせ

| 組み合わせ | 意味 |
|---|---|
| `raw / human` | 人間の書きかけメモ。plan ステップは拾わない |
| `raw / ai` | AI 側の未整理メモ（深掘り前のラフ起票） |
| `review / ai` | 人間 → AI へのレビュー依頼。次回 plan 冒頭で処理 |
| `ready / ai` | 着手可能。plan ステップの拾い上げ対象 |
| `need_human_action / human` | AI では判断不能。人間の対応待ち |

frontmatter 無しのファイルは後方互換として `raw / human` 扱い。

### 分布確認コマンド

```bash
python scripts/issue_status.py            # 全カテゴリ
python scripts/issue_status.py util       # カテゴリ指定
```

### util カテゴリの ISSUES 状況（ver6.0 完了時点）

| ファイル | status | assigned |
|---|---|---|
| `ISSUES/util/medium/issue-review-rewrite-verification.md` | ready | ai |
| `ISSUES/util/low/parse-frontmatter-shared-util.md` | raw | ai |
