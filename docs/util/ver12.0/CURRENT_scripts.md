# CURRENT_scripts: util ver12.0 — Python スクリプトと YAML ワークフロー定義

`scripts/` 配下のユーティリティスクリプト・YAML ワークフロー定義・Python テスト。ver12.0 で `scripts/claude_loop_lib/validation.py` を新規追加し、起動前 validation を実装した。その他のプロダクションコードは行数微増のみ（`claude_loop.py`）。

## ファイル一覧

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/scripts/get_latest_version.sh` | 43 | バージョン番号算出。`latest` / `major` / `next-minor` / `next-major` の 4 モード |
| `scripts/claude_loop.py` | 604 | エントリポイント。`--workflow auto` 分岐・各種ヘルパ。ver12.0 で `validate_startup()` import と `main()` への呼び出し追加 |
| `scripts/claude_loop_lib/__init__.py` | 0 | パッケージ初期化（空） |
| `scripts/claude_loop_lib/workflow.py` | 187 | YAML 読み込み・バリデーション・各設定値のリゾルバ。`OVERRIDE_STRING_KEYS` / `ALLOWED_STEP_KEYS` / `ALLOWED_DEFAULTS_KEYS` 定数を含む。これらの定数は `validation.py` にも import される |
| `scripts/claude_loop_lib/validation.py` | 308 | **ver12.0 新規**。起動前 validation。`validate_startup()` を公開 API とし、`Violation` dataclass で error/warning を集約して一括報告 |
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
| `scripts/README.md` | 175 | 概要・ファイル一覧・クイックスタート。ver12.0 で「起動前 validation」節と `validation.py` モジュール行を追記 |
| `scripts/USAGE.md` | 245 | CLI オプション一覧・YAML 仕様詳細・ログ読解・拡張ガイド。ver12.0 で「起動前 validation」段落を追記 |

## validation.py モジュール（ver12.0 新規）

### 公開 API

- `validate_startup(resolved, args, yaml_dir, cwd) -> None` — 唯一の公開関数。SystemExit(2) を副作用として投げる
- `Violation` dataclass（`source: str`, `message: str`, `severity: str`）/ `KNOWN_MODELS` / `KNOWN_EFFORTS` もテスト import 用に公開

### 検証項目と重大度

| # | 検証項目 | 重大度 |
|---|---|---|
| ① | `.claude/CURRENT_CATEGORY` の存在・中身（空文字・パス区切り文字を含む無効名）、`docs/{category}/` の存在 | error（ファイル未存在は warning + `app` フォールバック） |
| ② | YAML ファイルの存在・parse 成功・top-level が mapping であること | error |
| ③ | `command.executable` が `shutil.which` で解決できること | error |
| ④ | `defaults` / `steps[]` のキー集合が `ALLOWED_DEFAULTS_KEYS` / `ALLOWED_STEP_KEYS` に収まること | error |
| ④ | override キー（`model` / `effort` / `system_prompt` / `append_system_prompt`）が非空 string であること | error |
| ④ | `continue` が bool であること | error |
| ④ | `model` 値が `KNOWN_MODELS = {"opus", "sonnet", "haiku"}` に含まれること | **warning** |
| ④ | `effort` 値が `KNOWN_EFFORTS = {"low", "medium", "high", "xhigh", "max"}` に含まれること | **warning** |
| ⑤ | `step.prompt` が `/` 始まりの場合、`.claude/skills/<name>/SKILL.md` が存在すること | error |

### エラー集約戦略

- YAML A の parse 失敗があっても YAML B の schema エラーは同一実行で報告される
- error が 1 件でもあれば `SystemExit(2)` で終了し、error 一覧を stderr に出力
- warning のみの場合は stderr に出力して実行続行

### `--workflow auto` との接続

- `--workflow auto` の場合、phase 1 (`claude_loop_issue_plan.yaml`) と phase 2 候補 2 本（`claude_loop.yaml` / `claude_loop_quick.yaml`）を**全て事前検証**
- `--workflow full` / `--workflow quick` / 任意パスの場合は当該 1 本のみ検証

### `claude_loop.py main()` への挿入位置

```
parse_args()
  └─ resolve_workflow_value()
  └─ validate_auto_args()
  └─ cwd.is_dir() チェック
  └─ validate_startup()   ← ver12.0 で挿入（SystemExit(2) の可能性）
  └─ _resolve_uncommitted_status()
  └─ _run_selected()
```

`--dry-run` 時も validation は実行される。

### 既存 raise との関係

`workflow.py` / `commands.py` の raise-on-first-error 挙動は**ランタイム防衛として維持**。`validation.py` は独立した上位レイヤとして動作し、責務重複は意図的（多段防御）。

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

### 継承ルール（3 段階優先）

1. `steps[i].<key>` にキーが存在し値が non-`None` → step 値を採用
2. 上記が無く `defaults.<key>` にキーが存在し値が non-`None` → defaults 値を採用
3. 上記いずれも無ければ Claude CLI の既定挙動に従う（該当フラグを渡さない）

### 実装上の定数（`workflow.py`・`validation.py` 双方から参照）

```python
OVERRIDE_STRING_KEYS: tuple[str, ...] = ("model", "effort", "system_prompt", "append_system_prompt")
ALLOWED_STEP_KEYS = frozenset({"name", "prompt", "args", "continue"} | set(OVERRIDE_STRING_KEYS))
ALLOWED_DEFAULTS_KEYS = frozenset(OVERRIDE_STRING_KEYS)
```

`validation.py` はこれらを `workflow.py` から import する（循環依存なし）。定数を変更する際は validation ルールも同時に追随する。

## `scripts/claude_loop.py` の主要構成

### `main()` のフロー

```
parse_args()
  └─ resolve_workflow_value() → resolved ("auto" | Path)
  └─ validate_auto_args()
  └─ _resolve_uncommitted_status()
  └─ enable_log 判定
  └─ validate_startup()   ← ver12.0 追加
  └─ _run_selected()
       ├─ resolved == "auto" → _run_auto()
       └─ resolved は Path → _execute_yaml()
```

### 主要ヘルパ関数（変更なし）

| 関数 | 役割 |
|---|---|
| `validate_auto_args(resolved, args)` | `--workflow auto` + `--start > 1` の組み合わせを禁止 |
| `_rough_plan_candidates(cwd)` | `docs/{CURRENT_CATEGORY}/ver*/ROUGH_PLAN.md` の候補列挙 |
| `_version_key(path)` | `ver{X}.{Y}` → `(X, Y)` タプル。自然順ソート用 |
| `_find_latest_rough_plan(cwd, mtime_threshold=None)` | 最新 ROUGH_PLAN.md を返す |
| `_read_workflow_kind(rough_plan)` | ROUGH_PLAN.md frontmatter の `workflow:` を読む。不正値→`full` フォールバック |
| `_compute_remaining_budget(args, completed)` | `--max-step-runs` の残予算計算 |
| `_resolve_uncommitted_status(args, cwd)` | 未コミット検出・自動コミット処理を共通化 |
| `_execute_yaml(yaml_path, args, cwd, ...)` | 単一 YAML を読んでステップを実行する共通ヘルパ |
| `_run_auto(args, cwd, yaml_dir, ...)` | `--workflow auto` の 2 段実行ロジック |

## 自動化時の制約

YAML の `command.args` で `--dangerously-skip-permissions` を設定。`command.auto_args`（auto モード時のみ付与）では `--disallowedTools "AskUserQuestion"` と、質問を `REQUESTS/AI/` に書き出す指示 + `.claude/` 編集時の `claude_sync.py` 利用手順を `--append-system-prompt` で注入。
