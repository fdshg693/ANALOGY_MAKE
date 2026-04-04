# CURRENT: util ver2.0

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
| `scripts/claude_loop.py` | 448 | Python 自動化スクリプト。YAML ワークフロー定義に従い Claude CLI を順次実行。ログ出力・コミット追跡機能付き |
| `scripts/claude_loop.yaml` | 38 | フルワークフロー定義。5 ステップ（split_plan → imple_plan → wrap_up → write_current → retrospective）を定義。`--append-system-prompt` で `claude_sync.py` の利用手順も注入 |
| `scripts/claude_sync.py` | 58 | `.claude/` ⇔ `.claude_sync/` 同期スクリプト。CLI `-p` モードで `.claude/` を編集できない制約を回避するためのワークアラウンド |

### テスト

| ファイル | 行数 | 役割 |
|---|---|---|
| `tests/test_claude_loop.py` | 203 | `claude_loop.py` のユニットテスト。unittest 使用。`python -m unittest tests.test_claude_loop` で実行 |

### 設定ファイル

| ファイル | 役割 |
|---|---|
| `.claude/settings.local.json` | ローカル設定。`PermissionRequest` フックで `^(?!AskUserQuestion)` マッチャーを使用し、AskUserQuestion 以外の権限要求を自動承認。`Edit(/.claude/**)` / `Write(/.claude/**)` も許可ツールに追加済み |
| `.gitignore` | `logs/`（ワークフローログ）、`.claude_sync/`（同期ワークアラウンド一時コピー）、`data/`（SQLite）を除外 |

### 非同期コミュニケーション

| ディレクトリ | 役割 |
|---|---|
| `REQUESTS/AI/` | AI → ユーザーへの確認事項を書き出す場所。自動実行モードで質問が必要な場合の代替手段 |
| `REQUESTS/HUMAN/` | ユーザー → AI への要望を記載する場所 |

## scripts/claude_loop.py の実装詳細

### アーキテクチャ

単一ファイルの CLI ツール。依存は PyYAML のみ。ver2.0 で `main()` からステップ実行ロジックを `_run_steps()` に分離し、ログ有効/無効で `TeeWriter` の有無を切り替える構造に変更。

### 主要関数

| 関数 | 概要 |
|---|---|
| `parse_args()` | argparse による CLI 引数パース。`-w`（ワークフロー指定）、`-s`（開始ステップ）、`--cwd`、`--dry-run`、`--max-loops` / `--max-step-runs`（排他）、`--log-dir`（ログ出力先）、`--no-log`（ログ無効化） |
| `load_workflow(path)` | YAML 読み込み・バリデーション |
| `normalize_cli_args(value, field_name)` | YAML の args を `shlex.split` でトークン化 |
| `get_steps(config)` | steps セクションのパース。各ステップは `name` / `prompt` / `args` |
| `resolve_command_config(config)` | command セクションから executable / prompt_flag / common_args を取得 |
| `build_command(...)` | コマンド配列を構築。`log_file_path` 指定時は `--append-system-prompt` でログパスを注入 |
| `create_log_path(log_dir, workflow_path)` | タイムスタンプ付きログファイルパスを生成。`{YYYYMMDD_HHMMSS}_{workflow_stem}.log` 形式 |
| `get_head_commit(cwd)` | git HEAD のショートハッシュを取得。git リポジトリでない場合は None |
| `format_duration(seconds)` | 秒数を `Xh XXm XXs` / `Xm XXs` / `Xs` 形式に変換 |
| `iter_steps_for_loop_limit(...)` | `--max-loops` 指定時のステップイテレータ |
| `iter_steps_for_step_limit(...)` | `--max-step-runs` 指定時のステップイテレータ |
| `main()` | エントリポイント。設定読み込み → バリデーション → ログ初期化 → `_run_steps()` 呼び出し |
| `_run_steps(...)` | ステップ順次実行。TeeWriter によるログ出力、コミット追跡、ワークフローヘッダー/フッター出力を担当 |

### TeeWriter クラス

端末とログファイルの両方に同時出力するヘルパークラス。

| メソッド | 概要 |
|---|---|
| `write_line(line)` | 1行を stdout とログファイルの両方に出力 |
| `write_process_output(process)` | `subprocess.Popen` の stdout/stderr をストリーミング出力。終了コードを返す |

### ログフォーマット

ログ有効時、以下の構造でプレーンテキストログを出力:

```
=====================================
Workflow: {workflow_name}
Started: {timestamp}
Commit (start): {hash}
=====================================

[1/N] {step_name}
Started: {timestamp}
$ {command}
--- stdout/stderr ---
（出力内容）
--- end (exit: {code}, duration: {duration}) ---
Commit: {before} -> {after}

=====================================
Finished: {timestamp}
Commit (end): {hash}
Duration: {total_duration}
Result: SUCCESS (N/N steps completed)
=====================================
```

### 実行例

```bash
python scripts/claude_loop.py                        # フル 1 ループ（デフォルト、ログ有効）
python scripts/claude_loop.py --start 3              # ステップ 3 (wrap_up) から開始
python scripts/claude_loop.py --max-loops 2          # 2 ループ実行
python scripts/claude_loop.py --max-step-runs 7      # 最大 7 ステップ実行
python scripts/claude_loop.py --dry-run              # コマンド確認のみ（ログなし）
python scripts/claude_loop.py --no-log               # ログ無効で実行
python scripts/claude_loop.py --log-dir logs/custom  # ログ出力先を変更
python scripts/claude_loop.py -w path/to.yaml        # 別ワークフロー指定
```

### 自動化時の制約

`claude_loop.yaml` の `command.args` で以下を設定:
- `--dangerously-skip-permissions`: 権限確認スキップ
- `--disallowedTools "AskUserQuestion"`: ユーザー質問禁止
- `--append-system-prompt`: 質問が必要な場合は `REQUESTS/AI/` にファイルを書き出すよう指示。加えて `.claude/` 編集時の `claude_sync.py` 利用手順も注入

ログ有効時は `build_command()` が各ステップのコマンドにもログファイルパスを `--append-system-prompt` で追加注入する。

## tests/test_claude_loop.py のテスト構成

| テストクラス | テスト数 | 対象 |
|---|---|---|
| `TestCreateLogPath` | 4 | `create_log_path()`: ファイル名形式、ディレクトリ配置、stem 抽出、ディレクトリ作成 |
| `TestGetHeadCommit` | 4 | `get_head_commit()`: 正常取得、非ゼロ終了、git 未インストール、空白トリム |
| `TestFormatDuration` | 8 | `format_duration()`: 秒・分・時のフォーマット、エッジケース |
| `TestBuildCommandWithLogFilePath` | 4 | `build_command()` のログパス引数: None 時、指定時、引数順序、空文字列 |
| `TestParseArgsLoggingOptions` | 5 | CLI オプション: `--no-log` デフォルト/有効、`--log-dir` デフォルト/カスタム、共存 |

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
