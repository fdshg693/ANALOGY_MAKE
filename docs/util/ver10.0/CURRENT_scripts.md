# CURRENT_scripts: util ver10.0 — Python スクリプトと YAML ワークフロー定義

`scripts/` 配下のユーティリティスクリプトと YAML ワークフロー定義。ver9.1 で `_find_latest_rough_plan` に mtime 閾値対応を追加、ver9.2 で `issue_worklist.py --limit` を追加、ver10.0 で `workflow.py` / `commands.py` / `claude_loop.py` に step 単位 override 機能を導入した状態。

## ファイル一覧

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/scripts/get_latest_version.sh` | 43 | バージョン番号算出。`latest` / `major` / `next-minor` / `next-major` の 4 モード |
| `scripts/claude_loop.py` | 601 | エントリポイント。`--workflow auto` 分岐・各種ヘルパ。**ver10.0**: descriptor に `SystemPrompt: set` / `AppendSystemPrompt: set` 存在ビットを追加 |
| `scripts/claude_loop_lib/__init__.py` | 0 | パッケージ初期化（空） |
| `scripts/claude_loop_lib/workflow.py` | 187 | **ver10.0 で変更**。YAML 読み込み・バリデーション・各設定値のリゾルバ。`OVERRIDE_STRING_KEYS` / `ALLOWED_STEP_KEYS` / `ALLOWED_DEFAULTS_KEYS` 定数を追加し `get_steps` / `resolve_defaults` を拡張 |
| `scripts/claude_loop_lib/commands.py` | 76 | **ver10.0 で変更**。コマンド構築・ステップイテレータ。`--system-prompt` フラグ追加・`--append-system-prompt` 合成に `append_system_prompt` キーを統合 |
| `scripts/claude_loop_lib/feedbacks.py` | 50 | フィードバックファイルのロード・消費 |
| `scripts/claude_loop_lib/frontmatter.py` | 42 | 共通 `parse_frontmatter(text) -> (dict|None, str)` 実装 |
| `scripts/claude_loop_lib/issues.py` | 53 | ISSUE frontmatter の共通ヘルパ（`VALID_STATUS` / `VALID_ASSIGNED` / `VALID_COMBOS` / `extract_status_assigned`） |
| `scripts/claude_loop_lib/logging_utils.py` | 57 | TeeWriter・ログパス生成・ステップヘッダ表示・duration フォーマット |
| `scripts/claude_loop_lib/git_utils.py` | 40 | git HEAD 取得・未コミット検出・自動コミット |
| `scripts/claude_loop_lib/notify.py` | 43 | Windows toast 通知・beep フォールバック |
| `scripts/claude_loop.yaml` | 63 | **ver10.0 で sync コメント拡張**。フルワークフロー定義（6 ステップ） |
| `scripts/claude_loop_quick.yaml` | 52 | **ver10.0 で sync コメント拡張**。軽量ワークフロー定義（3 ステップ） |
| `scripts/claude_loop_issue_plan.yaml` | 42 | **ver10.0 で sync コメント拡張**。`/issue_plan` 単独実行用 YAML |
| `scripts/claude_sync.py` | 58 | `.claude/` ⇔ `.claude_sync/` 同期 |
| `scripts/issue_status.py` | 93 | `ISSUES/{category}/{high,medium,low}/*.md` の `status × assigned` 分布を表示 |
| `scripts/issue_worklist.py` | 163 | **ver9.2 で変更**。`--limit N` オプション追加。`assigned` / `status` で ISSUE を絞り込み `text` / `json` で出力 |
| `scripts/README.md` | 346 | **ver10.0 で大幅拡張**。YAML スキーマの override キー一覧表・継承ルール・`append_system_prompt` 合成順序・ログフォーマット更新を追記 |

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

### 3 ファイル同期義務

`claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` の `command` / `mode` / `defaults` セクションは常に同一内容を維持する。

## step 単位 override（ver10.0 新機能）

### override 可能なキー

YAML の `defaults:` および `steps[]` に指定できる文字列型の override キー:

| YAML キー | CLI flag | 役割 | バージョン |
|---|---|---|---|
| `model` | `--model` | 使用モデル | 既存 |
| `effort` | `--effort` | 推論努力レベル | 既存 |
| `system_prompt` | `--system-prompt` | デフォルト system prompt を**完全置換** | ver10.0 新規 |
| `append_system_prompt` | `--append-system-prompt` | デフォルト system prompt に追加 | ver10.0 新規 |

未知キー（例: `temperature`, `max_tokens`）は YAML パース時に `SystemExit`。空文字列も同様にエラー。

### 継承ルール（3 段階優先）

1. `steps[i].<key>` にキーが存在し値が non-`None` → step 値を採用
2. 上記が無く `defaults.<key>` にキーが存在し値が non-`None` → defaults 値を採用
3. 上記いずれも無ければ Claude CLI の既定挙動に従う（該当フラグを渡さない）

`None` は「未指定」として扱う（`get_steps()` がパース時に strip）。

### `append_system_prompt` の合成順序

`build_command()` が `--append-system-prompt` 本文を以下の順で連結する（区切りは空行 1 つ）:

1. `Current workflow log: {path}` 行（ログ有効時）
2. AUTO mode 注意文（auto モード時）
3. `## User Feedback` セクション（feedback 注入時）
4. step / defaults の `append_system_prompt` 値（指定時）

YAML 側 `command.auto_args` の `--append-system-prompt` と `build_command()` 組立の `--append-system-prompt` は CLI に独立した 2 引数として渡る（既存挙動、PHASE7.0 §3 で整理予定）。

### 実装上の定数（`workflow.py`）

```python
OVERRIDE_STRING_KEYS: tuple[str, ...] = ("model", "effort", "system_prompt", "append_system_prompt")
ALLOWED_STEP_KEYS = frozenset({"name", "prompt", "args", "continue"} | set(OVERRIDE_STRING_KEYS))
ALLOWED_DEFAULTS_KEYS = frozenset(OVERRIDE_STRING_KEYS)
```

## `scripts/claude_loop.py` の主要構成

### `main()` のフロー

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

### 主要ヘルパ関数

| 関数 | 役割 |
|---|---|
| `validate_auto_args(resolved, args)` | `--workflow auto` + `--start > 1` の組み合わせを禁止 |
| `_rough_plan_candidates(cwd)` | `docs/{CURRENT_CATEGORY}/ver*/ROUGH_PLAN.md` の候補列挙（ver9.1 で切り出し） |
| `_version_key(path)` | `ver{X}.{Y}` → `(X, Y)` タプル。ver10.0 > ver9.1 の自然順ソート用（ver9.1 追加） |
| `_find_latest_rough_plan(cwd, mtime_threshold=None)` | 最新 ROUGH_PLAN.md を返す。`mtime_threshold` 指定時は threshold 超えファイルのみ候補（ver9.1 拡張） |
| `_read_workflow_kind(rough_plan)` | ROUGH_PLAN.md frontmatter の `workflow:` を読む。不正値→`full` フォールバック |
| `_compute_remaining_budget(args, completed)` | `--max-step-runs` の残予算計算 |
| `_resolve_uncommitted_status(args, cwd)` | 未コミット検出・自動コミット処理を共通化 |
| `_execute_yaml(yaml_path, args, cwd, ...)` | 単一 YAML を読んでステップを実行する共通ヘルパ |
| `_run_auto(args, cwd, yaml_dir, ...)` | `--workflow auto` の 2 段実行ロジック |

### descriptor 行フォーマット（ver10.0 拡張後）

各ステップ起動前に表示する descriptor には以下が含まれる:
- `Model: <name>` / `Effort: <level>`（設定時のみ）
- `Continue: true`（セッション継続時のみ）
- `Session: <id>`（セッション ID 付与時のみ）
- `SystemPrompt: set` / `AppendSystemPrompt: set`（override 設定時のみ・**ver10.0 追加**・値は非表示）

## `scripts/issue_worklist.py`（ver9.2 変更後）

### CLI

```bash
python scripts/issue_worklist.py [--category util|app|infra|cicd] [--assigned ai|human] [--status ready,review|...] [--format text|json] [--limit N]
```

| オプション | 既定値 | 備考 |
|---|---|---|
| `--category` | `.claude/CURRENT_CATEGORY` の値。未設定時 `app` | |
| `--assigned` | `ai` | |
| `--status` | `ready,review` | カンマ区切りで複数指定可 |
| `--format` | `text` | `json` で JSON 出力 |
| `--limit N` | None（全件） | 指定時は上位 N 件のみ。JSON には `total` / `truncated` / `limit` フィールドが追加される |

`/issue_plan` SKILL は `--format json --limit 20` で呼び出す（ver9.2 以降）。

## `scripts/claude_sync.py`（変更なし）

CLI `-p` モードでは `.claude/` 配下への直接 Edit/Write が弾かれるため、以下の手順で編集する:

1. `python scripts/claude_sync.py export` — `.claude/` を `.claude_sync/` にコピー
2. `.claude_sync/skills/...` を Edit/Write ツールで編集
3. `python scripts/claude_sync.py import` — `.claude_sync/` を `.claude/` に全置換

## 自動化時の制約

YAML の `command.args` で `--dangerously-skip-permissions` を設定。`command.auto_args`（auto モード時のみ付与）では `--disallowedTools "AskUserQuestion"` と、質問を `REQUESTS/AI/` に書き出す指示 + `.claude/` 編集時の `claude_sync.py` 利用手順を `--append-system-prompt` で注入。
