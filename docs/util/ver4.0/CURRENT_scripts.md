# CURRENT_scripts: util ver4.0 — Python スクリプトと YAML ワークフロー定義

`scripts/` 配下のユーティリティスクリプト、`.claude/scripts/` のヘルパ、および YAML ワークフロー定義。

## ファイル一覧

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/scripts/get_latest_version.sh` | 43 | バージョン番号の算出。`latest` / `major` / `next-minor` / `next-major` の 4 モードに対応。旧形式（`ver12`）と新形式（`ver13.0`）の両方をパース |
| `scripts/claude_loop.py` | 698 | Python 自動化スクリプト。YAML ワークフロー定義に従い Claude CLI を順次実行。ログ出力・コミット追跡・完了通知・自動実行モード・未コミット検出・ユーザーフィードバック注入・ステップごとのモデル/エフォート指定をサポート |
| `scripts/claude_loop.yaml` | 51 | フルワークフロー定義（5 ステップ）。`defaults: {model: sonnet, effort: medium}` + ステップごとの推奨上書きを含む |
| `scripts/claude_loop_quick.yaml` | 42 | 軽量ワークフロー定義（3 ステップ）。同じく `defaults` とステップごとの上書きを含む |
| `scripts/claude_sync.py` | 58 | `.claude/` ⇔ `.claude_sync/` 同期スクリプト。CLI `-p` モードで `.claude/` を編集できない制約を回避するためのワークアラウンド |

## scripts/claude_loop.py

### アーキテクチャ

単一ファイルの CLI ツール。依存は PyYAML のみ（`shutil` / `argparse` / `pathlib` / `subprocess` / `shlex` は標準ライブラリ）。`main()` からステップ実行ロジックを `_run_steps()` に分離し、ログ有効/無効で `TeeWriter` の有無を切り替える構造。

### 主要関数

| 関数 | 行 | 概要 |
|---|---|---|
| `positive_int(value)` | 29 | argparse 用バリデータ。1 以上の整数を強制 |
| `parse_args()` | 36 | argparse による CLI 引数パース |
| `load_workflow(path)` | 109 | YAML 読み込み・バリデーション。ファイル不在・非 dict 時に `SystemExit` |
| `normalize_string_list(value, field)` | 123 | リスト項目が全て文字列であることを検証 |
| `normalize_cli_args(value, field)` | 131 | YAML の args を `shlex.split` でトークン化。文字列またはリストを受け付ける |
| `get_steps(config)` | 148 | steps セクションのパース。各ステップは `name` / `prompt` / `args` に加え、`model` / `effort` キーがあれば取り込む（`None` は未指定扱い、空文字列はエラー） |
| `resolve_defaults(config)` | 182 | **ver4.0 新規**。`defaults` セクションから `model` / `effort` を取り出し、設定されたキーだけを dict に入れて返す。`defaults` が dict 以外 / 値が空文字列 / 非文字列ならエラー |
| `resolve_command_config(config)` | 204 | command セクションから `executable` / `prompt_flag` / `common_args` / `auto_args` を取得 |
| `resolve_mode(config, cli_auto)` | 222 | 実行モード判定。優先順位: CLI `--auto` > YAML `mode.auto` > デフォルト (`False`) |
| `parse_feedback_frontmatter(content)` | 230 | フィードバック Markdown の YAML frontmatter を解析。`step` フィールドを文字列・リスト・未指定（キャッチオール）に応じて解釈 |
| `load_feedbacks(feedbacks_dir, step_name)` | 263 | `FEEDBACKS/` 直下の `*.md` を走査し、対象ステップにマッチするフィードバックを返す。`done/` サブディレクトリは対象外 |
| `consume_feedbacks(files, done_dir)` | 279 | 消費済みフィードバックファイルを `FEEDBACKS/done/` へ `shutil.move` で移動 |
| `build_command(executable, prompt_flag, common_args, step, log_file_path=None, auto_mode=False, feedbacks=None, defaults=None)` | 288 | コマンド配列を構築。`step` → `defaults` の順でキー存在ベースに `--model` / `--effort` を付与（`None` 値はスキップ）。ログパス・AUTO 通知・フィードバックを単一の `--append-system-prompt` に改行区切りで結合 |
| `print_step_header(current_index, total_steps, name)` | 320 | ステップヘッダの表示（ログ無効時） |
| `iter_steps_for_loop_limit(...)` | 324 | `--max-loops` 指定時のステップイテレータ |
| `iter_steps_for_step_limit(...)` | 335 | `--max-step-runs` 指定時のステップイテレータ |
| `create_log_path(log_dir, workflow_path)` | 349 | タイムスタンプ付きログファイルパスを生成。`{YYYYMMDD_HHMMSS}_{workflow_stem}.log` 形式 |
| `get_head_commit(cwd)` | 382 | git HEAD のショートハッシュを取得 |
| `check_uncommitted_changes(cwd)` | 394 | `git status --porcelain` で未コミット変更の有無を判定 |
| `auto_commit_changes(cwd)` | 406 | `git add -A` → `git commit` で自動コミット。成功時はコミットハッシュ、失敗時は `None` |
| `format_duration(seconds)` | 416 | 秒数を `Xh XXm XXs` / `Xm XXs` / `Xs` 形式に変換 |
| `notify_completion(title, message)` | 428 | デスクトップ通知を送信。toast を試行し、失敗時は beep にフォールバック |
| `_notify_toast(title, message)` | 436 | Windows PowerShell 経由のトースト通知。シングルクォートを `''` にエスケープ。タイムアウト 10 秒 |
| `_notify_beep(title, message)` | 457 | フォールバック通知（BEL 文字 + コンソール出力） |
| `main()` | 466 | エントリポイント。設定読み込み → `resolve_defaults` → バリデーション → 未コミットチェック → ログ初期化 → `_run_steps()` → 完了通知 |
| `_run_steps(..., defaults=None)` | 540 | ステップ順次実行。TeeWriter によるログ出力、コミット追跡、ワークフローヘッダー/フッター出力、ステップヘッダの `Model: X, Effort: Y` 行出力、フィードバックの読み込み・消費を担当 |

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

端末とログファイルの両方に同時出力するヘルパークラス（L358-）。

| メソッド | 概要 |
|---|---|
| `write_line(line)` | 1 行を stdout とログファイルの両方に出力 |
| `write_process_output(process)` | `subprocess.Popen` の stdout/stderr をストリーミング出力。終了コードを返す |

### main() の実行フロー

1. `parse_args()` で CLI 引数をパース
2. `load_workflow()` で YAML 設定を読み込み
3. `get_steps()` でステップ一覧を取得（`model` / `effort` 含む）
4. `resolve_command_config()` で実行コマンド設定を取得
5. `resolve_defaults()` で `defaults.model` / `defaults.effort` を取得
6. `resolve_mode()` で実行モードを判定、auto 時は `common_args + auto_args` を結合
7. 実行コマンドの存在確認（`shutil.which`）
8. 未コミット変更チェック（`--dry-run` 時はスキップ）
9. ステップイテレータを構築（`--max-loops` or `--max-step-runs`）
10. ログ有効時は `TeeWriter` を初期化して `_run_steps()` を呼び出し、`defaults` を引き回す
11. ワークフロー完了後に `notify_completion()` で通知（`--no-notify` / `--dry-run` 時は省略）

### ログフォーマット

```
=====================================
Workflow: {workflow_name}
Started: {timestamp}
Commit (start): {hash}
Uncommitted: {status}            ← 未コミット変更がある場合のみ
=====================================

[1/N] {step_name}
Started: {timestamp}
Model: {model}, Effort: {effort}  ← 未指定の側は省略、両方未指定なら行ごと省略（ver4.0 追加）
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

コマンドログ出力は `shlex.join(command)` を使用（ver3.1 より）、スペースや特殊文字を含む引数は自動でシェルクォートされる。

### 自動化時の制約

YAML の `command.args` で `--dangerously-skip-permissions` を設定。`command.auto_args`（auto モード時のみ付与）では `--disallowedTools "AskUserQuestion"` と、質問を `REQUESTS/AI/` に書き出す指示 + `.claude/` 編集時の `claude_sync.py` 利用手順を `--append-system-prompt` で注入。

ログ有効時は `build_command()` が各ステップのコマンドにもログファイルパスを `--append-system-prompt` で追加注入する。auto モード時はログパス・モード情報・フィードバックが単一の `--append-system-prompt` に改行区切りで結合される。

### ver4.0 のモデル/エフォート指定仕様

- **上書き判定ロジック**: `step.get(key, defaults.get(key))` による **キー存在ベース**。step dict に該当キーが存在しない場合のみ defaults を参照。`None` は「未指定」として扱い defaults が継承される
- **空文字列**: step 側 / defaults 側いずれも `SystemExit` でエラー（意図しない空値の検出）
- **CLI への反映**: 値が非 `None` の場合のみ `--model <value>` / `--effort <value>` を cmd に追加
- **`--append-system-prompt` との順序**: `--model` / `--effort` は `--append-system-prompt` より前に配置（ログ追跡性のため）
- **後方互換**: `defaults` を持たない既存 YAML・`defaults=None` で呼ばれた既存テストは壊れない（`build_command` の `defaults` 引数はデフォルト `None`）

## YAML ワークフロー定義の構造

`claude_loop.yaml` と `claude_loop_quick.yaml` は同一の 4 セクション構造。`command` セクションは両ファイルで完全に同一、`defaults` も同値（sonnet / medium）、`steps` セクションのみ異なる。

```yaml
mode:
  auto: false                  # デフォルトの実行モード（--auto で CLI からオーバーライド可能）

command:
  executable: claude
  prompt_flag: -p
  args:
    - --dangerously-skip-permissions
  auto_args:
    - --disallowedTools "AskUserQuestion"
    - --append-system-prompt "..."   # REQUESTS/AI/ への書き出し指示 + .claude/ 編集の注意事項

defaults:                      # ver4.0 追加（省略可、省略時は CLI デフォルト）
  model: sonnet
  effort: medium

steps:
  - name: step_name
    prompt: /skill_name
    model: opus                # 省略時は defaults.model を継承（ver4.0 追加、省略可）
    effort: high               # 省略時は defaults.effort を継承（ver4.0 追加、省略可）
```

### `scripts/claude_loop.yaml`（フル）のステップ別設定

| ステップ | model | effort | 理由 |
|---|---|---|---|
| split_plan | opus | high | 計画策定は重いため |
| imple_plan | opus | high | 実装計画も重い |
| wrap_up | （defaults: sonnet） | （defaults: medium） | 中間的な整理タスク |
| write_current | （defaults: sonnet） | low | ドキュメント整形中心のため effort を下げる |
| retrospective | （defaults: sonnet） | （defaults: medium） | 振り返りの中間タスク |

### `scripts/claude_loop_quick.yaml`（quick）のステップ別設定

| ステップ | model | effort | 理由 |
|---|---|---|---|
| quick_plan | （defaults: sonnet） | （defaults: medium） | 軽量計画 |
| quick_impl | （defaults: sonnet） | high | 実装本体のため effort を上げる |
| quick_doc | （defaults: sonnet） | low | ドキュメント生成中心 |

## scripts/claude_sync.py

Claude CLI の `-p` モードではセキュリティ制約により `.claude/` ディレクトリ内のファイルを直接編集できない。`claude_sync.py` は `.claude/` の内容を書き込み可能な `.claude_sync/` にコピーし、編集後に書き戻す仕組みを提供する。外部依存なし（標準ライブラリのみ）。

| 関数 | 概要 |
|---|---|
| `export_claude()` | `.claude/` → `.claude_sync/` に完全コピー。既存の `.claude_sync/` がある場合は削除してから上書き |
| `import_claude()` | `.claude_sync/` → `.claude/` に反映。`.claude/` を削除してから `.claude_sync/` の内容で置き換え |
| `main()` | argparse で `export` / `import` サブコマンドをパースし、対応する関数を呼び出す |
