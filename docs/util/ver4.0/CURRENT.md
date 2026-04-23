# CURRENT: util ver4.0

util カテゴリのコード現況。Claude Code ワークフロー自動化基盤に、ステップごとの `--model` / `--effort` 指定機能を追加した状態。top-level `defaults:` で全ステップ共通値を定義し、各ステップで必要に応じて上書きできる（キー存在ベース判定）。セッション継続（`-r` / `--session-id` / `stream-json` 解析）は未実装（ver4.1 以降）。

- [CURRENT_skills.md](CURRENT_skills.md) — `.claude/SKILLS/` の SKILL ファイル群・サブエージェント
- [CURRENT_scripts.md](CURRENT_scripts.md) — `scripts/` 配下の Python スクリプトと YAML ワークフロー定義
- [CURRENT_tests.md](CURRENT_tests.md) — `tests/test_claude_loop.py` のユニットテスト構成

## 設定ファイル

| ファイル | 役割 |
|---|---|
| `.claude/settings.local.json` | ローカル設定。`PermissionRequest` フックで `^(?!AskUserQuestion)` マッチャーを使用し、AskUserQuestion 以外の権限要求を自動承認。`Edit(/.claude/**)` / `Write(/.claude/**)` も許可ツールに追加済み |
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

各ステップに推奨モデル/エフォート値が設定済み（詳細は CURRENT_scripts.md）。

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

## ISSUES（util）

| 優先度 | ファイル | 内容 |
|---|---|---|
| medium | `ISSUES/util/medium/スクリプト改善.md` | `scripts/` 配下の README 新規作成・ファイル分割（ver4.1 以降で対応予定） |

`high` / `low` ディレクトリは現在空。
