# CURRENT_scripts: util ver5.0 — Python スクリプトと YAML ワークフロー定義

`scripts/` 配下のユーティリティスクリプトと YAML ワークフロー定義。ver4.1 でモジュール分割完了、ver5.0 でセッション継続機能を追加。

## ファイル一覧

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/scripts/get_latest_version.sh` | 43 | バージョン番号の算出。`latest` / `major` / `next-minor` / `next-major` の 4 モードに対応 |
| `scripts/claude_loop.py` | 395 | エントリポイント。`claude_loop_lib/` の各モジュールを組み合わせてワークフローを実行 |
| `scripts/claude_loop_lib/__init__.py` | 0 | パッケージ初期化（空） |
| `scripts/claude_loop_lib/workflow.py` | 135 | YAML 読み込み・バリデーション・各設定値のリゾルバ |
| `scripts/claude_loop_lib/commands.py` | 69 | コマンド構築・ステップイテレータ |
| `scripts/claude_loop_lib/feedbacks.py` | 66 | フィードバックファイルのロード・消費 |
| `scripts/claude_loop_lib/logging_utils.py` | 57 | TeeWriter・ログパス生成・ステップヘッダ表示・duration フォーマット |
| `scripts/claude_loop_lib/git_utils.py` | 40 | git HEAD 取得・未コミット検出・自動コミット |
| `scripts/claude_loop_lib/notify.py` | 43 | Windows toast 通知・beep フォールバック |
| `scripts/claude_loop.yaml` | 53 | フルワークフロー定義（5 ステップ） |
| `scripts/claude_loop_quick.yaml` | 44 | 軽量ワークフロー定義（3 ステップ） |
| `scripts/claude_sync.py` | 58 | `.claude/` ⇔ `.claude_sync/` 同期。CLI `-p` モードの `.claude/` 編集制限を回避 |
| `scripts/README.md` | 247 | スクリプト全体のドキュメント（ver4.1 で新規作成） |

## scripts/claude_loop.py

### アーキテクチャ

エントリポイント専用。`parse_args()` と `main()` / `_run_steps()` のみを含み、実質的なロジックは `claude_loop_lib/` 各モジュールに委譲。依存は `claude_loop_lib/` + PyYAML + 標準ライブラリ（`uuid` を追加）。

### 主要関数

| 関数 | 行 | 概要 |
|---|---|---|
| `parse_args()` | 〜30 | argparse による CLI 引数パース |
| `main()` | 〜150 | 設定読み込み → バリデーション → 未コミットチェック → ログ初期化 → `_run_steps()` → 通知 |
| `_run_steps(...)` | 〜250 | ステップ順次実行。TeeWriter ログ・コミット追跡・セッション ID 管理・フィードバック注入 |

### セッション継続の実装（ver5.0）

`_run_steps()` 内で `previous_session_id: str | None` を管理:

- **`continue: false`（デフォルト）**: `uuid.uuid4()` で生成した UUID を `--session-id <uuid>` として渡す（新規セッション）
- **`continue: true`**: 直前の `previous_session_id` を `-r <uuid>` として渡す（セッション再開）
- **`--start > 1`**: 全ステップの `continue` フラグを無効化し、警告をログ出力（前ステップのセッション ID 不明のため）
- **最初のステップが `continue: true`**: 直前セッション ID が存在しないため警告を出し、`--session-id` で新規セッションとして扱う
- **`--dry-run`**: 実際の UUID を生成してコマンドに付与（本番と同一の引数構造で確認可能）
- `previous_session_id` の更新は dry_run 判定の前後 2 箇所で行い、dry-run ログにも正確な UUID を表示

### ログフォーマット

```
=====================================
Workflow: {workflow_name}
Started: {timestamp}
Commit (start): {hash}
Uncommitted: {status}
=====================================

[1/N] {step_name}
Started: {timestamp}
Model: {model}, Effort: {effort}
Continue: {true/false}           ← ver5.0 追加
Session: {uuid}                  ← ver5.0 追加
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

`Continue:` 行は常に出力（true/false を明示）。`Model:` / `Effort:` 行は未指定の側を省略、両方未指定なら行ごと省略。

### CLI オプション一覧

| オプション | 型 | デフォルト | 概要 |
|---|---|---|---|
| `-w` / `--workflow` | Path | `scripts/claude_loop.yaml` | ワークフロー YAML ファイルパス |
| `-s` / `--start` | int (>=1) | `1` | 開始ステップ番号（1-based、>1 時は continue 無効化） |
| `--cwd` | Path | プロジェクトルート | Claude コマンドの作業ディレクトリ |
| `--dry-run` | flag | `False` | コマンド確認のみ（実行・ログ・通知なし） |
| `--log-dir` | Path | `logs/workflow/` | ログファイル出力先ディレクトリ |
| `--no-log` | flag | `False` | ログファイル出力を無効化 |
| `--no-notify` | flag | `False` | ワークフロー完了通知を無効化 |
| `--auto-commit-before` | flag | `False` | ワークフロー開始前に未コミット変更を自動コミット |
| `--auto` | flag | `False` | 自動実行モード強制（YAML 設定をオーバーライド） |
| `--max-loops` | int (>=1) | `1` | 最大ワークフローループ回数（`--max-step-runs` と排他） |
| `--max-step-runs` | int (>=1) | - | 最大ステップ実行回数（`--max-loops` と排他） |

## scripts/claude_loop_lib/workflow.py

| 関数 | 概要 |
|---|---|
| `load_workflow(path)` | YAML 読み込み・バリデーション |
| `normalize_string_list(value, field)` | リスト項目が全て文字列であることを検証 |
| `normalize_cli_args(value, field)` | YAML の args を `shlex.split` でトークン化 |
| `get_steps(config)` | steps パース。`name` / `prompt` / `args` / `model` / `effort` / `continue`（bool、ver5.0 追加）を正規化 |
| `resolve_defaults(config)` | `defaults.model` / `defaults.effort` を取り出し設定済みキーのみ dict で返す |
| `resolve_command_config(config)` | command セクションから `executable` / `prompt_flag` / `common_args` / `auto_args` を取得 |
| `resolve_mode(config, cli_auto)` | 実行モード判定。優先順位: CLI `--auto` > YAML `mode.auto` > `False` |

`get_steps()` の `continue` バリデーション: 値が bool でなければ `SystemExit`。省略時は `False` として正規化。

## scripts/claude_loop_lib/commands.py

| 関数 | 概要 |
|---|---|
| `build_command(executable, prompt_flag, common_args, step, log_file_path, auto_mode, feedbacks, defaults, session_id, resume)` | コマンド配列を構築。`session_id` が非 None かつ `resume=True` なら `-r <uuid>`、`resume=False` なら `--session-id <uuid>` を付与（ver5.0 追加） |
| `iter_steps_for_loop_limit(steps, start_index, max_loops)` | `--max-loops` 指定時のステップイテレータ |
| `iter_steps_for_step_limit(steps, start_index, max_step_runs)` | `--max-step-runs` 指定時のステップイテレータ |

`build_command()` のフラグ順序: `--model` / `--effort` → `-r` / `--session-id` → `--append-system-prompt`。

## scripts/claude_loop_lib/logging_utils.py

| クラス/関数 | 概要 |
|---|---|
| `TeeWriter` | stdout とログファイルへの同時出力。`write_line(line)` / `write_process_output(process)` |
| `create_log_path(log_dir, workflow_path)` | `{YYYYMMDD_HHMMSS}_{workflow_stem}.log` 形式のパス生成 |
| `print_step_header(current_index, total_steps, name)` | `[N/M] {name}` 形式のヘッダ表示 |
| `format_duration(seconds)` | `Xh XXm XXs` / `Xm XXs` / `Xs` 形式に変換 |

## YAML ワークフロー定義の構造

```yaml
mode:
  auto: true

command:
  executable: claude
  prompt_flag: -p
  args:
    - --dangerously-skip-permissions
  auto_args:
    - --disallowedTools "AskUserQuestion"
    - --append-system-prompt "..."

defaults:
  model: sonnet
  effort: medium

steps:
  - name: step_name
    prompt: /skill_name
    model: opus          # 省略時は defaults.model を継承
    effort: high         # 省略時は defaults.effort を継承
    continue: true       # ver5.0 追加。省略時は false
```

### `scripts/claude_loop.yaml`（フル）のステップ別設定

| ステップ | model | effort | continue | 理由 |
|---|---|---|---|---|
| split_plan | opus | high | false | 計画策定は重い。前提セッションなし |
| imple_plan | opus | high | true | split_plan の計画文脈を引き継ぐ |
| wrap_up | sonnet（defaults） | medium（defaults） | true | imple_plan の実装文脈を引き継ぐ |
| write_current | sonnet（defaults） | low | false | ドキュメント整形中心。独立セッション |
| retrospective | opus | medium（defaults） | false | 振り返り。独立セッション |

### `scripts/claude_loop_quick.yaml`（quick）のステップ別設定

| ステップ | model | effort | continue | 理由 |
|---|---|---|---|---|
| quick_plan | sonnet（defaults） | medium（defaults） | false | 軽量計画。独立セッション |
| quick_impl | sonnet（defaults） | high | true | quick_plan の計画文脈を引き継ぐ |
| quick_doc | sonnet（defaults） | low | true | quick_impl の実装文脈を引き継ぐ |

## 自動化時の制約

YAML の `command.args` で `--dangerously-skip-permissions` を設定。`command.auto_args`（auto モード時のみ付与）では `--disallowedTools "AskUserQuestion"` と、質問を `REQUESTS/AI/` に書き出す指示 + `.claude/` 編集時の `claude_sync.py` 利用手順を `--append-system-prompt` で注入。

ログ有効時は `build_command()` が各ステップのコマンドにログファイルパスを `--append-system-prompt` で追加注入する。auto モード時はログパス・モード情報・フィードバックが単一の `--append-system-prompt` に改行区切りで結合される。
