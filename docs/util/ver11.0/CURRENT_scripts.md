# CURRENT_scripts: util ver11.0 — Python スクリプトと YAML ワークフロー定義

`scripts/` 配下のユーティリティスクリプト・YAML ワークフロー定義・Python テスト。ver11.0 で `scripts/tests/` を新設し、Python テストをアプリ本体テスト（Vitest）から物理的に分離した。プロダクションコード（`claude_loop.py` / `claude_loop_lib/` / YAML）は変更なし。

## ファイル一覧

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/scripts/get_latest_version.sh` | 43 | バージョン番号算出。`latest` / `major` / `next-minor` / `next-major` の 4 モード |
| `scripts/claude_loop.py` | 601 | エントリポイント。`--workflow auto` 分岐・各種ヘルパ。descriptor に `SystemPrompt: set` / `AppendSystemPrompt: set` 存在ビットあり |
| `scripts/claude_loop_lib/__init__.py` | 0 | パッケージ初期化（空） |
| `scripts/claude_loop_lib/workflow.py` | 187 | YAML 読み込み・バリデーション・各設定値のリゾルバ。`OVERRIDE_STRING_KEYS` / `ALLOWED_STEP_KEYS` / `ALLOWED_DEFAULTS_KEYS` 定数を含む |
| `scripts/claude_loop_lib/commands.py` | 76 | コマンド構築・ステップイテレータ。`--system-prompt` / `--append-system-prompt` 合成ロジック |
| `scripts/claude_loop_lib/feedbacks.py` | 50 | フィードバックファイルのロード・消費 |
| `scripts/claude_loop_lib/frontmatter.py` | 42 | 共通 `parse_frontmatter(text) -> (dict|None, str)` 実装 |
| `scripts/claude_loop_lib/issues.py` | 53 | ISSUE frontmatter の共通ヘルパ（`VALID_STATUS` / `VALID_ASSIGNED` / `VALID_COMBOS` / `extract_status_assigned`） |
| `scripts/claude_loop_lib/logging_utils.py` | 57 | TeeWriter・ログパス生成・ステップヘッダ表示・duration フォーマット |
| `scripts/claude_loop_lib/git_utils.py` | 40 | git HEAD 取得・未コミット検出・自動コミット |
| `scripts/claude_loop_lib/notify.py` | 43 | Windows toast 通知・beep フォールバック |
| `scripts/claude_loop.yaml` | 63 | フルワークフロー定義（6 ステップ） |
| `scripts/claude_loop_quick.yaml` | 52 | 軽量ワークフロー定義（3 ステップ） |
| `scripts/claude_loop_issue_plan.yaml` | 42 | `/issue_plan` 単独実行用 YAML |
| `scripts/claude_sync.py` | 58 | `.claude/` ⇔ `.claude_sync/` 同期 |
| `scripts/issue_status.py` | 93 | `ISSUES/{category}/{high,medium,low}/*.md` の `status × assigned` 分布を表示 |
| `scripts/issue_worklist.py` | 163 | `--limit N` オプション付き ISSUE 絞り込み。`assigned` / `status` で絞り込み `text` / `json` で出力 |
| `scripts/README.md` | ~346 | **ver11.0 で「## テスト」節を更新**。新テスト実行コマンド（`python -m unittest discover -s scripts/tests -t .`）に置換済み |

## テストディレクトリ（ver11.0 新設）

`scripts/tests/` — Python テスト専用ディレクトリ。詳細は [CURRENT_tests.md](CURRENT_tests.md) を参照。

| ファイル | 役割 |
|---|---|
| `__init__.py` | パッケージ初期化（空）。`discover -t .` での `scripts.tests.xxx` ドット記法アクセスを可能にする |
| `_bootstrap.py` | `sys.path` への `scripts/` 追加（重複ガード付き）。全テストファイルが冒頭で参照 |
| `test_*.py`（11 ファイル） | `claude_loop_lib/` 8 モジュール + CLI + 統合テスト + `issue_worklist.py` に 1:1 対応 |

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

## step 単位 override（ver10.0 追加）

### override 可能なキー

| YAML キー | CLI flag | 役割 |
|---|---|---|
| `model` | `--model` | 使用モデル |
| `effort` | `--effort` | 推論努力レベル |
| `system_prompt` | `--system-prompt` | デフォルト system prompt を**完全置換** |
| `append_system_prompt` | `--append-system-prompt` | デフォルト system prompt に追加 |

未知キー・空文字列は YAML パース時に `SystemExit`。

### 継承ルール（3 段階優先）

1. `steps[i].<key>` にキーが存在し値が non-`None` → step 値を採用
2. 上記が無く `defaults.<key>` にキーが存在し値が non-`None` → defaults 値を採用
3. 上記いずれも無ければ Claude CLI の既定挙動に従う（該当フラグを渡さない）

### `append_system_prompt` の合成順序

`build_command()` が `--append-system-prompt` 本文を以下の順で連結する（区切りは空行 1 つ）:

1. `Current workflow log: {path}` 行（ログ有効時）
2. AUTO mode 注意文（auto モード時）
3. `## User Feedback` セクション（feedback 注入時）
4. step / defaults の `append_system_prompt` 値（指定時）

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
| `_rough_plan_candidates(cwd)` | `docs/{CURRENT_CATEGORY}/ver*/ROUGH_PLAN.md` の候補列挙 |
| `_version_key(path)` | `ver{X}.{Y}` → `(X, Y)` タプル。自然順ソート用 |
| `_find_latest_rough_plan(cwd, mtime_threshold=None)` | 最新 ROUGH_PLAN.md を返す。`mtime_threshold` 指定時は threshold 超えファイルのみ候補 |
| `_read_workflow_kind(rough_plan)` | ROUGH_PLAN.md frontmatter の `workflow:` を読む。不正値→`full` フォールバック |
| `_compute_remaining_budget(args, completed)` | `--max-step-runs` の残予算計算 |
| `_resolve_uncommitted_status(args, cwd)` | 未コミット検出・自動コミット処理を共通化 |
| `_execute_yaml(yaml_path, args, cwd, ...)` | 単一 YAML を読んでステップを実行する共通ヘルパ |
| `_run_auto(args, cwd, yaml_dir, ...)` | `--workflow auto` の 2 段実行ロジック |

## `scripts/claude_sync.py`（変更なし）

CLI `-p` モードでは `.claude/` 配下への直接 Edit/Write が弾かれるため、以下の手順で編集する:

1. `python scripts/claude_sync.py export` — `.claude/` を `.claude_sync/` にコピー
2. `.claude_sync/skills/...` を Edit/Write ツールで編集
3. `python scripts/claude_sync.py import` — `.claude_sync/` を `.claude/` に全置換

## 自動化時の制約

YAML の `command.args` で `--dangerously-skip-permissions` を設定。`command.auto_args`（auto モード時のみ付与）では `--disallowedTools "AskUserQuestion"` と、質問を `REQUESTS/AI/` に書き出す指示 + `.claude/` 編集時の `claude_sync.py` 利用手順を `--append-system-prompt` で注入。
