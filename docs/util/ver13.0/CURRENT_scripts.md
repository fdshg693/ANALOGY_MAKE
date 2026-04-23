# CURRENT_scripts: util ver13.0 — Python スクリプトと YAML ワークフロー定義

`scripts/` 配下のユーティリティスクリプト・YAML ワークフロー定義・Python テスト。ver13.0 で §3（`--auto` / `mode` / `auto_args` 撤去）・§4（FEEDBACKS 運用ルール明文化）・§5（REQUESTS 廃止）を実装した。

## ファイル一覧

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/scripts/get_latest_version.sh` | 43 | バージョン番号算出。`latest` / `major` / `next-minor` / `next-major` の 4 モード |
| `scripts/claude_loop.py` | 596 | エントリポイント。`--workflow auto` 分岐・各種ヘルパ。ver13.0 で `--auto` argparse 削除・`allow_abbrev=False` 追加・`auto_mode` / `auto_args` 関連コード除去 |
| `scripts/claude_loop_lib/__init__.py` | 0 | パッケージ初期化（空） |
| `scripts/claude_loop_lib/workflow.py` | 184 | YAML 読み込み・バリデーション・各設定値のリゾルバ。ver13.0 で `resolve_mode()` 削除・`resolve_command_config()` を 4-tuple → 3-tuple 化・`auto_args` 保険 `SystemExit` 追加 |
| `scripts/claude_loop_lib/validation.py` | 349 | 起動前 validation。ver13.0 で `ALLOWED_TOPLEVEL_KEYS` / `ALLOWED_COMMAND_KEYS` 定数追加、`_validate_toplevel_keys()` / `_validate_command_section()` を新設し legacy key（`mode:` / `command.auto_args`）を専用エラーで拒否 |
| `scripts/claude_loop_lib/commands.py` | 76 | コマンド構築・ステップイテレータ。ver13.0 で `auto_mode` 引数削除・unattended system prompt を**常時**注入する設計に変更 |
| `scripts/claude_loop_lib/feedbacks.py` | 61 | フィードバックファイルのロード・消費。ver13.0 で docstring 補強（`FEEDBACKS/done/` 自動再読込抑止・異常終了時は移動しない旨を明記） |
| `scripts/claude_loop_lib/frontmatter.py` | 42 | 共通 `parse_frontmatter(text) -> (dict|None, str)` 実装 |
| `scripts/claude_loop_lib/issues.py` | 53 | ISSUE frontmatter の共通ヘルパ（`VALID_STATUS` / `VALID_ASSIGNED` / `VALID_COMBOS` / `extract_status_assigned`） |
| `scripts/claude_loop_lib/logging_utils.py` | 57 | TeeWriter・ログパス生成・ステップヘッダ表示・duration フォーマット |
| `scripts/claude_loop_lib/git_utils.py` | 40 | git HEAD 取得・未コミット検出・自動コミット |
| `scripts/claude_loop_lib/notify.py` | 43 | Windows toast 通知・beep フォールバック |
| `scripts/claude_loop.yaml` | 43 | フルワークフロー定義（6 ステップ）。ver13.0 で `mode:` / `command.auto_args` 削除・`--disallowedTools "AskUserQuestion"` を `command.args` に移動 |
| `scripts/claude_loop_quick.yaml` | 32 | 軽量ワークフロー定義（3 ステップ）。同上 |
| `scripts/claude_loop_issue_plan.yaml` | 22 | `/issue_plan` 単独実行用 YAML。同上 |
| `scripts/claude_sync.py` | 58 | `.claude/` ⇔ `.claude_sync/` 同期 |
| `scripts/issue_status.py` | 93 | `ISSUES/{category}/{high,medium,low}/*.md` の `status × assigned` 分布を表示 |
| `scripts/issue_worklist.py` | 163 | `--limit N` オプション付き ISSUE 絞り込み。ver12.1 で `total` 計算タイミング修正済み |
| `scripts/README.md` | 171 | 概要・ファイル一覧・クイックスタート。ver13.0 で `--auto` / FEEDBACKS 異常終了・REQUESTS 廃止を反映 |
| `scripts/USAGE.md` | 240 | CLI オプション一覧・YAML 仕様詳細・ログ読解・拡張ガイド。ver13.0 で `--auto` / `mode:` / `auto_args` を削除・FEEDBACKS 異常終了ふるまいを追加 |

## ver13.0 の主要変更

### §3: `--auto` / `mode:` / `command.auto_args` 撤去

#### `scripts/claude_loop.py`

- `parser.add_argument("--auto", ...)` ブロックを**削除**
- `argparse.ArgumentParser(allow_abbrev=False)` を `parse_args()` で明示（`--auto` が `--auto-commit-before` に誤マッチするのを防止）
- `resolve_command_config()` 呼び出しを 4-tuple unpacking → 3-tuple unpacking に修正
- `auto_mode` / `auto_args` の計算・結合コードを削除
- `_run_steps()` シグネチャから `auto_mode: bool` を除去
- `build_command()` 呼び出しから `auto_mode` を除去

#### `scripts/claude_loop_lib/workflow.py`

- `resolve_mode()` 関数を**削除**（シンボル自体を消去）
- `resolve_command_config()` の戻り値を 4-tuple `(executable, prompt_flag, common_args, auto_args)` → 3-tuple `(executable, prompt_flag, common_args)` に変更
- `command_config.get("auto_args")` が存在する場合、`SystemExit`（runtime 保険）

#### `scripts/claude_loop_lib/validation.py`

- `ALLOWED_TOPLEVEL_KEYS = frozenset({"command", "defaults", "steps"})` を新規定義
- `ALLOWED_COMMAND_KEYS = frozenset({"executable", "prompt_flag", "args"})` を新規定義
- `_validate_toplevel_keys()` を新設：`mode:` キーを専用エラーで拒否、その他未知 top-level キーも汎用エラーで拒否
- `_validate_command_section()` を新設：`command.auto_args` キーを専用エラーで拒否、その他未知 command キーも汎用エラーで拒否

#### `scripts/claude_loop_lib/commands.py`

- `build_command()` から `auto_mode: bool = False` パラメータを**削除**
- 旧 `if auto_mode:` ブロックを**無条件化**（常に unattended system prompt を注入）
- system prompt 文言を更新:
  - 旧: `"Workflow execution mode: AUTO (unattended). Do not use AskUserQuestion. Write requests to REQUESTS/AI/ instead."`
  - 新: `"Workflow execution mode: unattended. Do not use AskUserQuestion. If human input is required, stop and write an ISSUE under ISSUES/{category}/{priority}/ with frontmatter \`status: need_human_action\` / \`assigned: human\`."`

#### YAML 3 ファイル共通変更

- `mode: auto: true` セクション（L7–8）を削除
- `command.auto_args` ブロック（L15–32）を削除
- `--disallowedTools "AskUserQuestion"` を `command.args` に追加
- NOTE コメントから `mode` への言及を除去
- 旧 `--append-system-prompt` 文言（`.claude/` 編集手順ガイド）を YAML から除去（`.claude/rules/claude_edit.md` に同内容が存在するため不要）

### §4: FEEDBACKS 運用ルール明文化

コード変更なし。docstring と docs の追記のみ:

- `feedbacks.py:load_feedbacks()` docstring: "Non-recursive glob — `FEEDBACKS/done/` は対象外"
- `feedbacks.py:consume_feedbacks()` docstring: "caller が step 正常終了時のみ呼び出すこと。異常終了時は呼び出されず、次回 run で再消費される"
- `scripts/USAGE.md`: 「異常終了時のふるまい」小節を新設

### §5: REQUESTS 廃止

- `REQUESTS/AI/` / `REQUESTS/HUMAN/` / `REQUESTS/` を`rmdir`で削除（空だったため `git rm` 不要）
- `CLAUDE.md`: `REQUESTS/` ディレクトリの説明行を削除
- `ISSUES/README.md`: 「REQUESTS からの移行経緯」セクションを追加
- SKILL 更新は「CURRENT_skills.md」参照

## validation.py モジュール（現況）

### 公開 API

- `validate_startup(resolved, args, yaml_dir, cwd) -> None` — 唯一の公開関数。SystemExit(2) を副作用として投げる
- `Violation` dataclass（`source: str`, `message: str`, `severity: str`）/ `KNOWN_MODELS` / `KNOWN_EFFORTS` / `ALLOWED_TOPLEVEL_KEYS` / `ALLOWED_COMMAND_KEYS` もテスト import 用に公開

### 検証項目と重大度

| # | 検証項目 | 重大度 |
|---|---|---|
| ① | `.claude/CURRENT_CATEGORY` の存在・中身（空文字・パス区切り文字を含む無効名）、`docs/{category}/` の存在 | error（ファイル未存在は warning + `app` フォールバック） |
| ② | YAML ファイルの存在・parse 成功・top-level が mapping であること | error |
| ② | top-level に `mode:` キーがある場合は専用エラー（ver13.0 廃止） | error |
| ② | top-level に未知キーがある場合は汎用エラー | error |
| ③ | `command.executable` が `shutil.which` で解決できること | error |
| ③ | `command` 配下に `auto_args` がある場合は専用エラー（ver13.0 廃止） | error |
| ③ | `command` 配下に未知キーがある場合は汎用エラー | error |
| ④ | `defaults` / `steps[]` のキー集合が `ALLOWED_DEFAULTS_KEYS` / `ALLOWED_STEP_KEYS` に収まること | error |
| ④ | override キー（`model` / `effort` / `system_prompt` / `append_system_prompt`）が非空 string であること | error |
| ④ | `continue` が bool であること | error |
| ④ | `model` 値が `KNOWN_MODELS = {"opus", "sonnet", "haiku"}` に含まれること | **warning** |
| ④ | `effort` 値が `KNOWN_EFFORTS = {"low", "medium", "high", "xhigh", "max"}` に含まれること | **warning** |
| ⑤ | `step.prompt` が `/` 始まりの場合、`.claude/skills/<name>/SKILL.md` が存在すること | error |

## YAML ワークフロー定義

### 3 ファイル同期義務

`claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` の `command` / `defaults` セクションは常に同一内容を維持する（`mode` セクションは ver13.0 で廃止済み）。

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

## `scripts/claude_loop.py` の主要構成

### `main()` のフロー

```
parse_args()
  └─ resolve_workflow_value() → resolved ("auto" | Path)
  └─ validate_auto_args()
  └─ _resolve_uncommitted_status()
  └─ enable_log 判定
  └─ validate_startup()
  └─ _run_selected()
       ├─ resolved == "auto" → _run_auto()
       └─ resolved は Path → _execute_yaml()
```

## 自動化時の制約

`command.args` に `--dangerously-skip-permissions` と `--disallowedTools "AskUserQuestion"` を設定（常時）。`build_command()` が unattended system prompt を**常時注入**する（ver13.0 から `auto_mode` 条件分岐なし）。
