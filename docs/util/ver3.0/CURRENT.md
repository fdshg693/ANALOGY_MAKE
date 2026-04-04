# CURRENT: util ver3.0

util カテゴリのコード現況。Claude Code ワークフロー自動化基盤の全体像を記述する。

## ファイル一覧

### SKILL ファイル（`.claude/SKILLS/`）

#### フルワークフロー（5 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `split_plan/SKILL.md` | 85 | ステップ 1: 計画策定。MASTER_PLAN・ISSUES・前回 RETROSPECTIVE から今回バージョンの計画ドキュメント（ROUGH_PLAN / REFACTOR / IMPLEMENT）を作成。完了後に Git コミット |
| `imple_plan/SKILL.md` | 76 | ステップ 2: 実装。CURRENT.md + 計画ドキュメントに基づきコード実装。サブエージェントで編集・テスト実行。MEMO.md を出力 |
| `wrap_up/SKILL.md` | 44 | ステップ 3: 残課題対応。MEMO.md の項目を ✅完了 / ⏭️不要 / 📋先送り に分類し、ISSUES 整理 |
| `write_current/SKILL.md` | 74 | ステップ 4: ドキュメント更新。メジャー版は CURRENT.md、マイナー版は CHANGES.md を作成。CLAUDE.md・MASTER_PLAN も更新。完了後に Git コミット |
| `retrospective/SKILL.md` | 53 | ステップ 5: 振り返り。git diff ベースでバージョン作業を振り返り、SKILL 自体の改善を即時適用 |

#### 軽量ワークフロー quick（3 ステップ）

| ファイル | 行数 | 役割 |
|---|---|---|
| `quick_plan/SKILL.md` | 49 | ステップ 1: ISSUE 選定 + 簡潔な計画（ROUGH_PLAN.md のみ作成、plan_review_agent 省略、マイナーバージョン専用） |
| `quick_impl/SKILL.md` | 43 | ステップ 2: 実装 + MEMO 対応を統合。typecheck 最低 1 回、対応不可の MEMO は ISSUES に記載 |
| `quick_doc/SKILL.md` | 55 | ステップ 3: CHANGES.md 作成 + CLAUDE.md 更新確認 + MASTER_PLAN ステータス更新 + ISSUES 整理 + コミット＆プッシュ |

#### メタ評価

| ファイル | 行数 | 役割 |
|---|---|---|
| `meta_judge/SKILL.md` | 18 | メタ評価。ワークフロー全体の有効性を評価する手動実行専用 SKILL（`disable-model-invocation: true`） |
| `meta_judge/WORKFLOW.md` | 34 | ワークフロー概要ドキュメント。フルワークフローと軽量ワークフローの説明、選択ガイドラインを記載 |

### サブエージェント

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/agents/plan_review_agent.md` | 17 | 計画レビュー専用エージェント。Sonnet モデル、Read/Glob/Grep のみ使用。split_plan と wrap_up で利用（quick ワークフローでは使用しない） |

### ユーティリティスクリプト

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/scripts/get_latest_version.sh` | 43 | バージョン番号の算出。`latest` / `major` / `next-minor` / `next-major` の 4 モードに対応。旧形式（`ver12`）と新形式（`ver13.0`）の両方をパース |
| `scripts/claude_loop.py` | 575 | Python 自動化スクリプト。YAML ワークフロー定義に従い Claude CLI を順次実行。ログ出力・コミット追跡・完了通知・自動実行モード・未コミット検出機能付き |
| `scripts/claude_loop.yaml` | 42 | フルワークフロー定義（5 ステップ: split_plan → imple_plan → wrap_up → write_current → retrospective） |
| `scripts/claude_loop_quick.yaml` | 36 | 軽量ワークフロー定義（3 ステップ: quick_plan → quick_impl → quick_doc） |
| `scripts/claude_sync.py` | 58 | `.claude/` ⇔ `.claude_sync/` 同期スクリプト。CLI `-p` モードで `.claude/` を編集できない制約を回避するためのワークアラウンド |

### テスト

| ファイル | 行数 | 役割 |
|---|---|---|
| `tests/test_claude_loop.py` | 391 | `claude_loop.py` のユニットテスト。unittest 使用。14 テストクラス・50 テストメソッド |

### 設定ファイル

| ファイル | 役割 |
|---|---|
| `.claude/settings.local.json` | ローカル設定。`PermissionRequest` フックで `^(?!AskUserQuestion)` マッチャーを使用し、AskUserQuestion 以外の権限要求を自動承認。`Edit(/.claude/**)` / `Write(/.claude/**)` も許可ツールに追加済み |
| `.gitignore` | `logs/`（ワークフローログ）、`.claude_sync/`（同期ワークアラウンド一時コピー）、`data/`（SQLite）、`__pycache__/`・`*.pyc` を除外 |

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
- IMPLEMENT.md / REFACTOR.md を作成しない（ROUGH_PLAN.md のみ）
- wrap_up を quick_impl に統合
- write_current の代わりに CHANGES.md のみ作成する quick_doc を使用
- retrospective を省略

### ワークフロー選択ガイドライン

| 条件 | 推奨 |
|---|---|
| MASTER_PLAN の新項目着手 | full |
| アーキテクチャ変更・新規ライブラリ導入 | full |
| 変更ファイル 4 つ以上 | full |
| ISSUES/high の対応（複雑） | full |
| ISSUES の 1 件対応（単純） | quick |
| バグ修正（原因特定済み） | quick |
| 既存機能の微調整 | quick |
| ドキュメント・テスト追加 | quick |
| 変更ファイル 3 つ以下 | quick |

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

## YAML ワークフロー定義の構造

フルワークフロー（`claude_loop.yaml`）と軽量ワークフロー（`claude_loop_quick.yaml`）は同一の 3 セクション構造を持つ。`command` セクションは完全に同一で、`steps` セクションのみが異なる。

```yaml
mode:
  auto: false                  # デフォルトの実行モード（--auto で CLI からオーバーライド可能）

command:
  executable: claude           # 実行コマンド
  prompt_flag: -p              # プロンプト引数フラグ
  args:                        # 常に付与される引数
    - --dangerously-skip-permissions
  auto_args:                   # auto モード時のみ追加される引数
    - --disallowedTools "AskUserQuestion"
    - --append-system-prompt "..."   # REQUESTS/AI/ への書き出し指示 + .claude/ 編集の注意事項

steps:                         # ワークフローステップ（full: 5個、quick: 3個）
  - name: step_name
    prompt: /skill_name
```

## scripts/claude_loop.py の実装詳細

### アーキテクチャ

単一ファイルの CLI ツール。依存は PyYAML のみ。`main()` からステップ実行ロジックを `_run_steps()` に分離し、ログ有効/無効で `TeeWriter` の有無を切り替える構造。

### 主要関数

| 関数 | 概要 |
|---|---|
| `positive_int(value)` | argparse 用バリデータ。1 以上の整数を強制 |
| `parse_args()` | argparse による CLI 引数パース（後述の CLI オプション一覧参照） |
| `load_workflow(path)` | YAML 読み込み・バリデーション。ファイル不在・非 dict 時に `SystemExit` |
| `normalize_string_list(value, field_name)` | リスト項目が全て文字列であることを検証 |
| `normalize_cli_args(value, field_name)` | YAML の args を `shlex.split` でトークン化。文字列またはリストを受け付ける |
| `get_steps(config)` | steps セクションのパース。各ステップは `name` / `prompt` / `args` |
| `resolve_command_config(config)` | command セクションから `executable` / `prompt_flag` / `common_args` / `auto_args` を取得 |
| `resolve_mode(config, cli_auto)` | 実行モード判定。優先順位: CLI `--auto` > YAML `mode.auto` > デフォルト (`False`) |
| `build_command(...)` | コマンド配列を構築。`log_file_path` と `auto_mode` の情報を単一の `--append-system-prompt` に改行区切りで結合 |
| `print_step_header(...)` | ステップヘッダーの表示（ログ無効時） |
| `create_log_path(log_dir, workflow_path)` | タイムスタンプ付きログファイルパスを生成。`{YYYYMMDD_HHMMSS}_{workflow_stem}.log` 形式 |
| `get_head_commit(cwd)` | git HEAD のショートハッシュを取得。git リポジトリでない場合は `None` |
| `check_uncommitted_changes(cwd)` | `git status --porcelain` で未コミット変更の有無を判定 |
| `auto_commit_changes(cwd)` | `git add -A` → `git commit` で自動コミット。成功時はコミットハッシュ、失敗時は `None` |
| `format_duration(seconds)` | 秒数を `Xh XXm XXs` / `Xm XXs` / `Xs` 形式に変換 |
| `notify_completion(title, message)` | デスクトップ通知を送信。toast を試行し、失敗時は beep にフォールバック |
| `_notify_toast(title, message)` | Windows PowerShell 経由のトースト通知。シングルクォートを `''` にエスケープ。タイムアウト 10 秒 |
| `_notify_beep(title, message)` | フォールバック通知（BEL 文字 + コンソール出力） |
| `iter_steps_for_loop_limit(...)` | `--max-loops` 指定時のステップイテレータ |
| `iter_steps_for_step_limit(...)` | `--max-step-runs` 指定時のステップイテレータ |
| `main()` | エントリポイント。設定読み込み → バリデーション → 未コミットチェック → ログ初期化 → `_run_steps()` → 完了通知 |
| `_run_steps(...)` | ステップ順次実行。TeeWriter によるログ出力、コミット追跡、ワークフローヘッダー/フッター出力を担当 |

### CLI オプション一覧

| オプション | 型 | デフォルト | 概要 |
|---|---|---|---|
| `-w` / `--workflow` | Path | `scripts/claude_loop.yaml` | ワークフロー YAML ファイルパス |
| `-s` / `--start` | int (>=1) | `1` | 開始ステップ番号（1-based） |
| `--cwd` | Path | プロジェクトルート | Claude コマンドの作業ディレクトリ |
| `--dry-run` | flag | `False` | コマンド確認のみ（実行・ログ・通知なし） |
| `--log-dir` | Path | `logs/workflow/` | ログファイル出力先ディレクトリ |
| `--no-log` | flag | `False` | ログファイル出力を無効化 |
| `--no-notify` | flag | `False` | ワークフロー完了通知を無効化 |
| `--auto-commit-before` | flag | `False` | ワークフロー開始前に未コミット変更を自動コミット |
| `--auto` | flag | `False` | 自動実行モード強制（YAML 設定をオーバーライド） |
| `--max-loops` | int (>=1) | `1` | 最大ワークフローループ回数（`--max-step-runs` と排他） |
| `--max-step-runs` | int (>=1) | - | 最大ステップ実行回数（`--max-loops` と排他） |

### TeeWriter クラス

端末とログファイルの両方に同時出力するヘルパークラス。

| メソッド | 概要 |
|---|---|
| `write_line(line)` | 1 行を stdout とログファイルの両方に出力 |
| `write_process_output(process)` | `subprocess.Popen` の stdout/stderr をストリーミング出力。終了コードを返す |

### main() の実行フロー

1. `parse_args()` で CLI 引数をパース
2. `load_workflow()` で YAML 設定を読み込み
3. `get_steps()` でステップ一覧を取得
4. `resolve_command_config()` で実行コマンド設定を取得
5. `resolve_mode()` で実行モードを判定、auto 時は `common_args + auto_args` を結合
6. 実行コマンドの存在確認（`shutil.which`）
7. 未コミット変更チェック（`--dry-run` 時はスキップ）
   - `--auto-commit-before` 指定時: 自動コミット実行
   - フラグなし: stderr に警告出力
8. ステップイテレータを構築（`--max-loops` or `--max-step-runs`）
9. ログ有効時は `TeeWriter` を初期化して `_run_steps()` を呼び出し
10. ワークフロー完了後に `notify_completion()` で通知（`--no-notify` / `--dry-run` 時は省略）

### ログフォーマット

ログ有効時、以下の構造でプレーンテキストログを出力:

```
=====================================
Workflow: {workflow_name}
Started: {timestamp}
Commit (start): {hash}
Uncommitted: {status}            ← 未コミット変更がある場合のみ
=====================================

[1/N] {step_name}
Started: {timestamp}
$ {command}
--- stdout/stderr ---
（出力内容）
--- end (exit: {code}, duration: {duration}) ---
Commit: {before} -> {after}     ← コミットが変化した場合のみ

=====================================
Finished: {timestamp}
Commit (end): {hash}
Duration: {total_duration}
Result: SUCCESS (N/N steps completed)
=====================================
```

### 自動化時の制約

YAML の `command.args` で以下を設定:
- `--dangerously-skip-permissions`: 権限確認スキップ

`command.auto_args`（auto モード時のみ付与）:
- `--disallowedTools "AskUserQuestion"`: ユーザー質問禁止
- `--append-system-prompt`: 質問が必要な場合は `REQUESTS/AI/` にファイルを書き出すよう指示。加えて `.claude/` 編集時の `claude_sync.py` 利用手順も注入

ログ有効時は `build_command()` が各ステップのコマンドにもログファイルパスを `--append-system-prompt` で追加注入する。auto モード時はログパスとモード情報が単一の `--append-system-prompt` に改行区切りで結合される。

## scripts/claude_sync.py の実装詳細

### 背景・目的

Claude CLI の `-p` モードではセキュリティ制約により `.claude/` ディレクトリ内のファイルを直接編集できない。`claude_sync.py` は `.claude/` の内容を書き込み可能な `.claude_sync/` にコピーし、編集後に書き戻す仕組みを提供する。

### アーキテクチャ

単一ファイルの CLI ツール。外部依存なし（標準ライブラリの `shutil` / `argparse` / `pathlib` のみ使用）。

### 主要関数

| 関数 | 概要 |
|---|---|
| `export_claude()` | `.claude/` → `.claude_sync/` に完全コピー。既存の `.claude_sync/` がある場合は削除してから上書き |
| `import_claude()` | `.claude_sync/` → `.claude/` に反映。`.claude/` を削除してから `.claude_sync/` の内容で置き換え |
| `main()` | argparse で `export` / `import` サブコマンドをパースし、対応する関数を呼び出す |

## tests/test_claude_loop.py のテスト構成

14 テストクラス、50 テストメソッドで構成。

| テストクラス | テスト数 | 対象 |
|---|---|---|
| `TestCreateLogPath` | 4 | `create_log_path()`: ファイル名形式、ディレクトリ配置、stem 抽出、ディレクトリ作成 |
| `TestGetHeadCommit` | 4 | `get_head_commit()`: 正常取得、非ゼロ終了、git 未インストール、空白トリム |
| `TestFormatDuration` | 10 | `format_duration()`: 秒・分・時のフォーマット、境界値、小数点切り捨て |
| `TestBuildCommandWithLogFilePath` | 4 | `build_command()` のログパス引数: None 時、指定時、引数順序、空文字列 |
| `TestParseArgsLoggingOptions` | 5 | `--no-log` / `--log-dir` のデフォルト・指定・共存 |
| `TestNotifyCompletion` | 3 | `notify_completion()`: toast 成功、beep フォールバック、シングルクォートエスケープ |
| `TestResolveMode` | 3 | `resolve_mode()`: デフォルト、YAML auto=true、CLI `--auto` オーバーライド |
| `TestBuildCommandWithMode` | 3 | `build_command()` の auto_mode: AUTO プロンプト注入、非 AUTO 時プロンプトなし、ログ＋モードの単一プロンプト結合 |
| `TestParseArgsAutoOption` | 2 | `--auto` フラグのデフォルト・指定 |
| `TestParseArgsNotifyOption` | 2 | `--no-notify` フラグのデフォルト・指定 |
| `TestResolveCommandConfigAutoArgs` | 2 | `resolve_command_config()` の `auto_args` 抽出・デフォルト空リスト |
| `TestCheckUncommittedChanges` | 3 | `check_uncommitted_changes()`: 変更あり、変更なし、git 未検出 |
| `TestAutoCommitChanges` | 3 | `auto_commit_changes()`: 成功→ハッシュ返却、git add 失敗→None、git commit 失敗→None |
| `TestParseArgsAutoCommitBefore` | 2 | `--auto-commit-before` フラグのデフォルト・指定 |
