# CURRENT: util ver1.0

util カテゴリのコード現況。Claude Code ワークフロー自動化基盤の全体像を記述する。

## ファイル一覧

### SKILL ファイル（`.claude/SKILLS/`）

| ファイル | 行数 | 役割 |
|---|---|---|
| `split_plan/SKILL.md` | 81 | ステップ 1: 計画策定。MASTER_PLAN・ISSUES・前回 RETROSPECTIVE から今回バージョンの計画ドキュメント（ROUGH_PLAN / REFACTOR / IMPLEMENT）を作成 |
| `imple_plan/SKILL.md` | 75 | ステップ 2: 実装。CURRENT.md + 計画ドキュメントに基づきコード実装。サブエージェントで編集・テスト実行。MEMO.md を出力 |
| `wrap_up/SKILL.md` | 44 | ステップ 3: 残課題対応。MEMO.md の項目を ✅完了 / ⏭️不要 / 📋先送り に分類し、ISSUES 整理 |
| `write_current/SKILL.md` | 70 | ステップ 4: ドキュメント更新。メジャー版は CURRENT.md、マイナー版は CHANGES.md を作成。CLAUDE.md・MASTER_PLAN も更新 |
| `retrospective/SKILL.md` | 51 | ステップ 5: 振り返り。git diff ベースでバージョン作業を振り返り、SKILL 自体の改善を即時適用 |
| `meta_judge/SKILL.md` | 18 | メタ評価。ワークフロー全体の有効性を評価する手動実行専用 SKILL（`disable-model-invocation: true`） |
| `meta_judge/WORKFLOW.md` | 12 | meta_judge 参照用のワークフロー概要ドキュメント |

### サブエージェント

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/agents/plan_review_agent.md` | 17 | 計画レビュー専用エージェント。Sonnet モデル、Read/Glob/Grep のみ使用。split_plan と wrap_up で利用 |

### ユーティリティスクリプト

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/scripts/get_latest_version.sh` | 43 | バージョン番号の算出。`latest` / `major` / `next-minor` / `next-major` の 4 モードに対応。旧形式（`ver12`）と新形式（`ver13.0`）の両方をパース |
| `scripts/claude_loop.py` | 252 | Python 自動化スクリプト。YAML ワークフロー定義に従い Claude CLI を順次実行 |
| `scripts/claude_loop.yaml` | 27 | フルワークフロー定義。5 ステップ（split_plan → imple_plan → wrap_up → write_current → retrospective）を定義 |
| `scripts/claude_sync.py` | 58 | `.claude/` ⇔ `.claude_sync/` 同期スクリプト。CLI `-p` モードで `.claude/` を編集できない制約を回避するためのワークアラウンド |

### 非同期コミュニケーション

| ディレクトリ | 役割 |
|---|---|
| `REQUESTS/AI/` | AI → ユーザーへの確認事項を書き出す場所。自動実行モードで質問が必要な場合の代替手段 |
| `REQUESTS/HUMAN/` | ユーザー → AI への要望を記載する場所 |

## scripts/claude_loop.py の実装詳細

### アーキテクチャ

単一ファイルの CLI ツール。依存は PyYAML のみ。

### 主要関数

| 関数 | 概要 |
|---|---|
| `parse_args()` | argparse による CLI 引数パース。`-w`（ワークフロー指定）、`-s`（開始ステップ）、`--cwd`、`--dry-run`、`--max-loops` / `--max-step-runs`（排他） |
| `load_workflow(path)` | YAML 読み込み・バリデーション |
| `normalize_cli_args(value, field_name)` | YAML の args を `shlex.split` でトークン化 |
| `get_steps(config)` | steps セクションのパース。各ステップは `name` / `prompt` / `args` |
| `resolve_command_config(config)` | command セクションから executable / prompt_flag / common_args を取得 |
| `build_command(...)` | `[executable, prompt_flag, prompt, *common_args, *step_args]` のコマンド配列を構築 |
| `iter_steps_for_loop_limit(...)` | `--max-loops` 指定時のステップイテレータ。初回ループは start_index から、2 回目以降は先頭から |
| `iter_steps_for_step_limit(...)` | `--max-step-runs` 指定時のステップイテレータ。ステップ数上限でループ |
| `main()` | エントリポイント。設定読み込み → バリデーション → ステップ順次実行（`subprocess.run`） |

### 実行例

```bash
python scripts/claude_loop.py                   # フル 1 ループ（デフォルト）
python scripts/claude_loop.py --start 3         # ステップ 3 (wrap_up) から開始
python scripts/claude_loop.py --max-loops 2     # 2 ループ実行
python scripts/claude_loop.py --max-step-runs 7 # 最大 7 ステップ実行
python scripts/claude_loop.py --dry-run         # コマンド確認のみ
python scripts/claude_loop.py -w path/to.yaml   # 別ワークフロー指定
```

### 自動化時の制約

`claude_loop.yaml` の `command.args` で以下を設定:
- `--dangerously-skip-permissions`: 権限確認スキップ
- `--disallowedTools "AskUserQuestion"`: ユーザー質問禁止
- `--append-system-prompt`: 質問が必要な場合は `REQUESTS/AI/` にファイルを書き出すよう指示。加えて `.claude/` 編集時の `claude_sync.py` 利用手順も注入

## scripts/claude_sync.py の実装詳細

### 背景・目的

Claude CLI の `-p`（プロンプト）モードではセキュリティ制約により `.claude/` ディレクトリ内のファイルを直接編集できない。自動化ワークフロー（`claude_loop.py`）では全ステップが `-p` モードで実行されるため、SKILL ファイルや設定の編集が不可能になる。

`claude_sync.py` はこの制約を回避するワークアラウンドで、`.claude/` の内容を書き込み可能な `.claude_sync/` にコピーし、編集後に書き戻す仕組みを提供する。

### アーキテクチャ

単一ファイルの CLI ツール。外部依存なし（標準ライブラリの `shutil` / `argparse` / `pathlib` のみ使用）。

### 主要関数

| 関数 | 概要 |
|---|---|
| `export_claude()` | `.claude/` → `.claude_sync/` に完全コピー。既存の `.claude_sync/` がある場合は削除してから上書き |
| `import_claude()` | `.claude_sync/` → `.claude/` に反映。`.claude/` を削除してから `.claude_sync/` の内容で置き換え |
| `main()` | argparse で `export` / `import` サブコマンドをパースし、対応する関数を呼び出す |

### 実行例

```bash
python scripts/claude_sync.py export   # .claude/ -> .claude_sync/ にコピー
python scripts/claude_sync.py import   # .claude_sync/ -> .claude/ に反映
```

### 自動化ワークフローでの利用

`claude_loop.yaml` の `--append-system-prompt` で、自動実行される各ステップの Claude に対して以下の手順が指示される:

1. `python scripts/claude_sync.py export` — `.claude/` を `.claude_sync/` にコピー
2. `.claude_sync/` 内の対応ファイルを編集（このディレクトリは書き込み可能）
3. `python scripts/claude_sync.py import` — `.claude_sync/` の内容を `.claude/` に書き戻し

これにより、retrospective ステップでの SKILL 改善など、`.claude/` 配下のファイル編集を伴う操作が自動化ワークフロー内でも実行可能になる。