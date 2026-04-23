# CURRENT_scripts: util ver9.0 — Python スクリプトと YAML ワークフロー定義

`scripts/` 配下のユーティリティスクリプトと YAML ワークフロー定義。ver9.0 では `scripts/claude_loop.py`（`--workflow auto` 分岐・各種ヘルパ追加）・`scripts/claude_loop_lib/workflow.py`（`resolve_workflow_value` 追加）・`scripts/claude_loop_issue_plan.yaml`（新規）・`scripts/claude_loop.yaml` / `claude_loop_quick.yaml`（NOTE コメント追加）・`scripts/README.md`（`--workflow` 説明更新）を変更した。

## ファイル一覧

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/scripts/get_latest_version.sh` | 43 | バージョン番号算出。`latest` / `major` / `next-minor` / `next-major` の 4 モード |
| `scripts/claude_loop.py` | 551 | **ver9.0 で大幅変更**。エントリポイント。`--workflow auto` 分岐・各種ヘルパ追加 |
| `scripts/claude_loop_lib/__init__.py` | 0 | パッケージ初期化（空） |
| `scripts/claude_loop_lib/workflow.py` | 161 | **ver9.0 で変更**。YAML 読み込み・バリデーション・各設定値のリゾルバ。`resolve_workflow_value` と定数追加 |
| `scripts/claude_loop_lib/commands.py` | 69 | コマンド構築・ステップイテレータ |
| `scripts/claude_loop_lib/feedbacks.py` | 50 | フィードバックファイルのロード・消費 |
| `scripts/claude_loop_lib/frontmatter.py` | 42 | 共通 `parse_frontmatter(text) -> (dict|None, str)` 実装 |
| `scripts/claude_loop_lib/issues.py` | 53 | ISSUE frontmatter の共通ヘルパ（`VALID_STATUS` / `VALID_ASSIGNED` / `VALID_COMBOS` / `extract_status_assigned`） |
| `scripts/claude_loop_lib/logging_utils.py` | 57 | TeeWriter・ログパス生成・ステップヘッダ表示・duration フォーマット |
| `scripts/claude_loop_lib/git_utils.py` | 40 | git HEAD 取得・未コミット検出・自動コミット |
| `scripts/claude_loop_lib/notify.py` | 43 | Windows toast 通知・beep フォールバック |
| `scripts/claude_loop.yaml` | 61 | **ver9.0 で NOTE コメント追加**。フルワークフロー定義（6 ステップ） |
| `scripts/claude_loop_quick.yaml` | 50 | **ver9.0 で NOTE コメント追加**。軽量ワークフロー定義（3 ステップ） |
| `scripts/claude_loop_issue_plan.yaml` | 40 | **ver9.0 で新規作成**。`/issue_plan` 単独実行用 YAML（`--workflow auto` の phase 1 でも使用） |
| `scripts/claude_sync.py` | 58 | `.claude/` ⇔ `.claude_sync/` 同期。CLI `-p` モードの `.claude/` 編集制限を回避 |
| `scripts/issue_status.py` | 93 | `ISSUES/{category}/{high,medium,low}/*.md` の `status × assigned` 分布を表示する読み取り専用スクリプト |
| `scripts/issue_worklist.py` | 163 | `assigned` / `status` で ISSUE を絞り込み、`text` / `json` で出力する読み取り専用スクリプト |
| `scripts/README.md` | 306 | **ver9.0 で更新**。`--workflow auto | full | quick | <path>` 説明・`--auto` との違い・`auto` 分岐仕様節を追記 |

## YAML ワークフロー定義

### `scripts/claude_loop.yaml`（フル）のステップ別設定

| ステップ | model | effort | continue |
|---|---|---|---|
| issue_plan | opus | high | false |
| split_plan | opus | high | false |
| imple_plan | opus | high | false |
| wrap_up | sonnet（defaults） | medium（defaults） | true |
| write_current | sonnet（defaults） | low | false |
| retrospective | opus | medium（defaults） | false |

### `scripts/claude_loop_quick.yaml`（quick）のステップ別設定

| ステップ | model | effort | continue |
|---|---|---|---|
| issue_plan | opus | high | false |
| quick_impl | sonnet（defaults） | high | true |
| quick_doc | sonnet（defaults） | low | true |

### `scripts/claude_loop_issue_plan.yaml`（issue_plan 単独）のステップ別設定

| ステップ | model | effort | continue |
|---|---|---|---|
| issue_plan | opus | high | false |

`mode` / `command` / `defaults` は `claude_loop.yaml` と厳密一致。`steps` のみが 1 要素。

### セッション継続の設計方針

- `/issue_plan` → `/split_plan` 間は**新規セッション**（`continue: false`）。必要情報は ROUGH_PLAN.md の frontmatter + 本文経由で引き継ぐ
- `/issue_plan` → `/quick_impl` 間は `continue: true`（quick_impl が ROUGH_PLAN.md の内容をセッション継続で参照）
- `/split_plan` → `/imple_plan` 間は新規セッション（各 SKILL が個別にファイルを参照する設計）
- `--workflow auto` フェーズ 2 では `previous_session_id` を引き継がない（フェーズ 1 と 2 は別 `_execute_yaml()` 呼び出し）

### 3 ファイル同期義務

`claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` の `command` / `mode` / `defaults` セクションは常に同一内容を維持する。いずれかを変更した場合は必ず 3 ファイル全てを同期すること（`.claude/skills/meta_judge/WORKFLOW.md` の「保守上の注意」参照）。

## `scripts/claude_loop.py` の主要構成（ver9.0 変更後）

### 新規追加のヘルパ関数

| 関数 | 役割 |
|---|---|
| `validate_auto_args(resolved, args)` | `--workflow auto` + `--start > 1` の組み合わせを禁止（SystemExit） |
| `_find_latest_rough_plan(cwd)` | `docs/{CURRENT_CATEGORY}/ver*/ROUGH_PLAN.md` を glob し最新 mtime のものを返す |
| `_read_workflow_kind(rough_plan)` | ROUGH_PLAN.md frontmatter の `workflow:` を読む。不正値時は `"full"` フォールバック |
| `_compute_remaining_budget(args, completed)` | `--max-step-runs` の残予算を計算（`max(max_step_runs - completed, 0)` or None） |
| `_resolve_uncommitted_status(args, cwd)` | 未コミット検出・自動コミット処理を共通化。uncommitted_status 文字列を返す |
| `_execute_yaml(yaml_path, args, cwd, ...)` | 単一 YAML を読んでステップを実行する共通ヘルパ。start_index / max_step_runs_override を受け取る |
| `_run_auto(args, cwd, yaml_dir, ...)` | `--workflow auto` の 2 段実行ロジック（phase 1: issue_plan、phase 2: full/quick steps[1:]） |

### `--workflow` の型変更

ver8.0: `type=Path, default=DEFAULT_WORKFLOW_PATH`（固定 YAML パス）
ver9.0: `type=str, default="auto"`（予約値 + パス直指定の両対応）

`resolve_workflow_value(value, yaml_dir)` で `"auto"` / `"full"` / `"quick"` の予約値を解決し、それ以外は `Path(value).expanduser()` を返す。予約値マッチは完全一致・大文字小文字区別。

### `main()` のフロー（ver9.0）

```
parse_args()
  └─ resolve_workflow_value() → resolved ("auto" | Path)
  └─ validate_auto_args()
  └─ _resolve_uncommitted_status()
  └─ enable_log 判定
  └─ _run_selected()
       ├─ resolved == "auto" → _run_auto()
       └─ resolved は Path → _execute_yaml()
```

### `--dry-run` + `auto` の挙動

phase 1 のコマンドを表示後、`"--- auto: phase2 skipped (--dry-run) ---"` を出力して終了。ROUGH_PLAN.md を実際には作らないため phase 2 はスキップ。

## `scripts/claude_loop_lib/workflow.py` の追加内容

```python
FULL_YAML_FILENAME = "claude_loop.yaml"
QUICK_YAML_FILENAME = "claude_loop_quick.yaml"
ISSUE_PLAN_YAML_FILENAME = "claude_loop_issue_plan.yaml"

RESERVED_WORKFLOW_VALUES = ("auto", "full", "quick")

def resolve_workflow_value(value: str, yaml_dir: Path) -> str | Path:
    ...
```

## scripts/claude_sync.py の動作（`.claude/` 編集のワークアラウンド）

CLI `-p` モードでは `.claude/` 配下への直接 Edit/Write が弾かれるため、以下の手順で編集する:

1. `python scripts/claude_sync.py export` — `.claude/` を `.claude_sync/` にコピー
2. `.claude_sync/skills/...` を Edit/Write ツールで編集
3. `python scripts/claude_sync.py import` — `.claude_sync/` を `.claude/` に全置換

`import_claude()` は `.claude/` を `shutil.rmtree` → `copytree` で全置換するため、`.claude_sync/` で削除したファイルは確実に伝搬する。`.claude_sync/` は `.gitignore` で除外されている。

## scripts/issue_worklist.py

`/issue_plan` SKILL のコンテキスト先頭で `!` バックティック展開として実行される（`--format json`）。

### CLI

```bash
python scripts/issue_worklist.py [--category util|app|infra|cicd] [--assigned ai|human] [--status ready,review|...] [--format text|json]
```

| オプション | 既定値 | 備考 |
|---|---|---|
| `--category` | `.claude/CURRENT_CATEGORY` の値。未設定時 `app` | |
| `--assigned` | `ai` | |
| `--status` | `ready,review` | カンマ区切りで複数指定可 |
| `--format` | `text` | `json` で JSON 配列出力 |

## 自動化時の制約

YAML の `command.args` で `--dangerously-skip-permissions` を設定。`command.auto_args`（auto モード時のみ付与）では `--disallowedTools "AskUserQuestion"` と、質問を `REQUESTS/AI/` に書き出す指示 + `.claude/` 編集時の `claude_sync.py` 利用手順を `--append-system-prompt` で注入。
