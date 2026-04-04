# CURRENT: util ver3.0

util カテゴリのコード現況。Claude Code ワークフロー自動化基盤の全体像を記述する。

## ファイル一覧

### SKILL ファイル（`.claude/SKILLS/`）

#### フルワークフロー（5 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `split_plan/SKILL.md` | 85 | ステップ 1: 計画策定。MASTER_PLAN・ISSUES・前回 RETROSPECTIVE から今回バージョンの計画ドキュメント（ROUGH_PLAN / REFACTOR / IMPLEMENT）を作成 |
| `imple_plan/SKILL.md` | 76 | ステップ 2: 実装。CURRENT.md + 計画ドキュメントに基づきコード実装。サブエージェントで編集・テスト実行。MEMO.md を出力 |
| `wrap_up/SKILL.md` | 44 | ステップ 3: 残課題対応。MEMO.md の項目を ✅完了 / ⏭️不要 / 📋先送り に分類し、ISSUES 整理 |
| `write_current/SKILL.md` | 74 | ステップ 4: ドキュメント更新。メジャー版は CURRENT.md、マイナー版は CHANGES.md を作成。CLAUDE.md・MASTER_PLAN も更新 |
| `retrospective/SKILL.md` | 53 | ステップ 5: 振り返り。git diff ベースでバージョン作業を振り返り、SKILL 自体の改善を即時適用 |

#### 軽量ワークフロー quick（3 ステップ）— ver3.0 で新規追加

| ファイル | 行数 | 役割 |
|---|---|---|
| `quick_plan/SKILL.md` | 49 | ステップ 1: ISSUE 選定 + 簡潔な計画（ROUGH_PLAN.md のみ作成、plan_review_agent 省略、マイナーバージョン専用） |
| `quick_impl/SKILL.md` | 43 | ステップ 2: 実装 + MEMO対応を統合。typecheck 最低 1 回、対応不可の MEMO は ISSUES に記載 |
| `quick_doc/SKILL.md` | 55 | ステップ 3: CHANGES.md 作成 + CLAUDE.md 更新確認 + MASTER_PLAN ステータス更新 + ISSUES 整理 + コミット＆プッシュ |

#### メタ評価

| ファイル | 行数 | 役割 |
|---|---|---|
| `meta_judge/SKILL.md` | 18 | メタ評価。ワークフロー全体の有効性を評価する手動実行専用 SKILL |
| `meta_judge/WORKFLOW.md` | 34 | ワークフロー概要ドキュメント。フルワークフローと軽量ワークフローの説明、選択ガイドラインを記載 |

### サブエージェント

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/agents/plan_review_agent.md` | 17 | 計画レビュー専用エージェント。Sonnet モデル、Read/Glob/Grep のみ使用。split_plan と wrap_up で利用（quick ワークフローでは使用しない） |

### ユーティリティスクリプト

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/scripts/get_latest_version.sh` | 43 | バージョン番号の算出。`latest` / `major` / `next-minor` / `next-major` の 4 モードに対応 |
| `scripts/claude_loop.py` | 575 | Python 自動化スクリプト。YAML ワークフロー定義に従い Claude CLI を順次実行。ログ出力・コミット追跡機能付き |
| `scripts/claude_loop.yaml` | 42 | フルワークフロー定義（5 ステップ） |
| `scripts/claude_loop_quick.yaml` | 36 | 軽量ワークフロー定義（3 ステップ）— ver3.0 で新規追加 |
| `scripts/claude_sync.py` | 58 | `.claude/` ⇔ `.claude_sync/` 同期スクリプト。CLI `-p` モードで `.claude/` を編集できない制約を回避するためのワークアラウンド |

### テスト

| ファイル | 行数 | 役割 |
|---|---|---|
| `tests/test_claude_loop.py` | 391 | `claude_loop.py` のユニットテスト。unittest 使用。`python -m unittest tests.test_claude_loop` で実行 |

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

## ワークフロー体系

### フルワークフロー（`claude_loop.yaml`）

5 ステップの完全ワークフロー。メジャーバージョン、アーキテクチャ変更、4 ファイル以上の変更に使用。

```
/split_plan → /imple_plan → /wrap_up → /write_current → /retrospective
```

### 軽量ワークフロー quick（`claude_loop_quick.yaml`）

3 ステップの簡略ワークフロー。マイナーバージョン、単一 ISSUE 対応、3 ファイル以下の変更に使用。

```
/quick_plan → /quick_impl → /quick_doc
```

フルワークフローとの主な違い:
- plan_review_agent を使用しない
- IMPLEMENT.md / REFACTOR.md を作成しない
- wrap_up を quick_impl に統合
- write_current の代わりに CHANGES.md のみ作成する quick_doc を使用
- retrospective を省略

### 実行方法

```bash
python scripts/claude_loop.py                                        # フルワークフロー
python scripts/claude_loop.py -w scripts/claude_loop_quick.yaml      # 軽量ワークフロー
```

## scripts/claude_loop.py の実装詳細

### アーキテクチャ

単一ファイルの CLI ツール。依存は PyYAML のみ。`main()` からステップ実行ロジックを `_run_steps()` に分離し、ログ有効/無効で `TeeWriter` の有無を切り替える構造。

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
| `get_head_commit(cwd)` | git HEAD のショートハッシュを取得 |
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

## scripts/claude_sync.py の実装詳細

### 背景・目的

Claude CLI の `-p` モードではセキュリティ制約により `.claude/` ディレクトリ内のファイルを直接編集できない。`claude_sync.py` は `.claude/` の内容を書き込み可能な `.claude_sync/` にコピーし、編集後に書き戻す仕組みを提供する。

### 主要関数

| 関数 | 概要 |
|---|---|
| `export_claude()` | `.claude/` → `.claude_sync/` に完全コピー |
| `import_claude()` | `.claude_sync/` → `.claude/` に反映 |
| `main()` | argparse で `export` / `import` サブコマンドをパース |

## tests/test_claude_loop.py のテスト構成

| テストクラス | テスト数 | 対象 |
|---|---|---|
| `TestCreateLogPath` | 4 | `create_log_path()`: ファイル名形式、ディレクトリ配置、stem 抽出、ディレクトリ作成 |
| `TestGetHeadCommit` | 4 | `get_head_commit()`: 正常取得、非ゼロ終了、git 未インストール、空白トリム |
| `TestFormatDuration` | 8 | `format_duration()`: 秒・分・時のフォーマット、エッジケース |
| `TestBuildCommandWithLogFilePath` | 4 | `build_command()` のログパス引数: None 時、指定時、引数順序、空文字列 |
| `TestParseArgsLoggingOptions` | 5 | CLI オプション: `--no-log` デフォルト/有効、`--log-dir` デフォルト/カスタム、共存 |
