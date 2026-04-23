# CURRENT_scripts: util ver14.0 — Python スクリプトと YAML ワークフロー定義

`scripts/` 配下のユーティリティスクリプト・YAML ワークフロー定義・Python テスト。ver14.0 では Python コード自体は変更なし。`scripts/README.md` / `scripts/USAGE.md` に rules への参照を追記し、`test_claude_loop_integration.py` に `TestFeedbackInvariant` を追加した。

## ファイル一覧

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/scripts/get_latest_version.sh` | 43 | バージョン番号算出。`latest` / `major` / `next-minor` / `next-major` の 4 モード |
| `scripts/claude_loop.py` | 596 | エントリポイント。`--workflow auto` 分岐・各種ヘルパ |
| `scripts/claude_loop_lib/__init__.py` | 0 | パッケージ初期化（空） |
| `scripts/claude_loop_lib/workflow.py` | 184 | YAML 読み込み・バリデーション・各設定値のリゾルバ |
| `scripts/claude_loop_lib/validation.py` | 349 | 起動前 validation |
| `scripts/claude_loop_lib/commands.py` | 76 | コマンド構築・ステップイテレータ |
| `scripts/claude_loop_lib/feedbacks.py` | 61 | フィードバックファイルのロード・消費 |
| `scripts/claude_loop_lib/frontmatter.py` | 42 | 共通 `parse_frontmatter(text) -> (dict|None, str)` 実装 |
| `scripts/claude_loop_lib/issues.py` | 53 | ISSUE frontmatter の共通ヘルパ（`VALID_STATUS` / `VALID_ASSIGNED` / `VALID_COMBOS` / `extract_status_assigned`） |
| `scripts/claude_loop_lib/logging_utils.py` | 57 | TeeWriter・ログパス生成・ステップヘッダ表示・duration フォーマット |
| `scripts/claude_loop_lib/git_utils.py` | 40 | git HEAD 取得・未コミット検出・自動コミット |
| `scripts/claude_loop_lib/notify.py` | 43 | Windows toast 通知・beep フォールバック |
| `scripts/claude_loop.yaml` | 43 | フルワークフロー定義（6 ステップ） |
| `scripts/claude_loop_quick.yaml` | 32 | 軽量ワークフロー定義（3 ステップ） |
| `scripts/claude_loop_issue_plan.yaml` | 22 | `/issue_plan` 単独実行用 YAML |
| `scripts/claude_sync.py` | 58 | `.claude/` ⇔ `.claude_sync/` 同期 |
| `scripts/issue_status.py` | 93 | `ISSUES/{category}/{high,medium,low}/*.md` の `status × assigned` 分布を表示 |
| `scripts/issue_worklist.py` | 163 | `--limit N` オプション付き ISSUE 絞り込み |
| `scripts/README.md` | 173 | 概要・ファイル一覧・クイックスタート。ver14.0 で `前提条件` 節に `.claude/rules/scripts.md` が scripts 系の stable 規約を集約している旨の 1 段落を追記 |
| `scripts/USAGE.md` | 243 | CLI オプション一覧・YAML 仕様詳細・ログ読解・拡張ガイド。ver14.0 で「拡張ガイド」節冒頭に rules へのポインタ追記・各 bullet に `（rules §N）` 参照を付与 |

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
