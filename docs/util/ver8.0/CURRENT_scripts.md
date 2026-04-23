# CURRENT_scripts: util ver8.0 — Python スクリプトと YAML ワークフロー定義

`scripts/` 配下のユーティリティスクリプトと YAML ワークフロー定義。ver8.0 では `claude_loop.yaml`（6 ステップに拡張）・`claude_loop_quick.yaml`（`/quick_plan` → `/issue_plan` 差し替え）・`scripts/README.md` を更新した。Python スクリプト本体（`claude_loop.py` / `claude_loop_lib/`）の変更はない。

## ファイル一覧

| ファイル | 行数 | 役割 |
|---|---|---|
| `.claude/scripts/get_latest_version.sh` | 43 | バージョン番号算出。`latest` / `major` / `next-minor` / `next-major` の 4 モード |
| `scripts/claude_loop.py` | 395 | エントリポイント。`claude_loop_lib/` を組み合わせてワークフローを実行 |
| `scripts/claude_loop_lib/__init__.py` | 0 | パッケージ初期化（空） |
| `scripts/claude_loop_lib/workflow.py` | 135 | YAML 読み込み・バリデーション・各設定値のリゾルバ |
| `scripts/claude_loop_lib/commands.py` | 69 | コマンド構築・ステップイテレータ |
| `scripts/claude_loop_lib/feedbacks.py` | 50 | フィードバックファイルのロード・消費 |
| `scripts/claude_loop_lib/frontmatter.py` | 42 | 共通 `parse_frontmatter(text) -> (dict|None, str)` 実装 |
| `scripts/claude_loop_lib/issues.py` | 53 | ISSUE frontmatter の共通ヘルパ（`VALID_STATUS` / `VALID_ASSIGNED` / `VALID_COMBOS` / `extract_status_assigned`） |
| `scripts/claude_loop_lib/logging_utils.py` | 57 | TeeWriter・ログパス生成・ステップヘッダ表示・duration フォーマット |
| `scripts/claude_loop_lib/git_utils.py` | 40 | git HEAD 取得・未コミット検出・自動コミット |
| `scripts/claude_loop_lib/notify.py` | 43 | Windows toast 通知・beep フォールバック |
| `scripts/claude_loop.yaml` | 57 | **ver8.0 で更新**。フルワークフロー定義（6 ステップ、`/issue_plan` を先頭に追加） |
| `scripts/claude_loop_quick.yaml` | 46 | **ver8.0 で更新**。軽量ワークフロー定義（3 ステップ、`/quick_plan` → `/issue_plan` に差し替え） |
| `scripts/claude_sync.py` | 58 | `.claude/` ⇔ `.claude_sync/` 同期。CLI `-p` モードの `.claude/` 編集制限を回避 |
| `scripts/issue_status.py` | 93 | `ISSUES/{category}/{high,medium,low}/*.md` の `status × assigned` 分布を表示する読み取り専用スクリプト |
| `scripts/issue_worklist.py` | 163 | `assigned` / `status` で ISSUE を絞り込み、`text` / `json` で出力する読み取り専用スクリプト |
| `scripts/README.md` | 277 | **ver8.0 で更新**。ステップ列挙・ワークフロー使い分けガイドを更新 |

## YAML ワークフロー定義

### `scripts/claude_loop.yaml`（フル）のステップ別設定（ver8.0 更新後）

| ステップ | model | effort | continue |
|---|---|---|---|
| issue_plan | opus | high | false |
| split_plan | opus | high | false |
| imple_plan | opus | high | false |
| wrap_up | sonnet（defaults） | medium（defaults） | true |
| write_current | sonnet（defaults） | low | false |
| retrospective | opus | medium（defaults） | false |

### `scripts/claude_loop_quick.yaml`（quick）のステップ別設定（ver8.0 更新後）

| ステップ | model | effort | continue |
|---|---|---|---|
| issue_plan | opus | high | false |
| quick_impl | sonnet（defaults） | high | true |
| quick_doc | sonnet（defaults） | low | true |

`/quick_impl` / `/quick_doc` の `continue: true` の起点は `/issue_plan` になる（ver8.0 以前は `/quick_plan` が起点）。

### セッション継続の設計方針

- `/issue_plan` → `/split_plan` 間は**新規セッション**（`continue: false`）。必要情報は ROUGH_PLAN.md の frontmatter + 本文経由で引き継ぐ
- `/issue_plan` → `/quick_impl` 間は `continue: true`（quick_impl が ROUGH_PLAN.md の内容をセッション継続で参照）
- `/split_plan` → `/imple_plan` 間は新規セッション（各 SKILL が個別にファイルを参照する設計）

## scripts/claude_sync.py の動作（`.claude/` 編集のワークアラウンド）

CLI `-p` モードでは `.claude/` 配下への直接 Edit/Write が弾かれるため、以下の手順で編集する:

1. `python scripts/claude_sync.py export` — `.claude/` を `.claude_sync/` にコピー
2. `.claude_sync/skills/...` を Edit/Write ツールで編集
3. `python scripts/claude_sync.py import` — `.claude_sync/` を `.claude/` に全置換

`import_claude()` は `.claude/` を `shutil.rmtree` → `copytree` で全置換するため、`.claude_sync/` で削除したファイルは確実に伝搬する。`.claude_sync/` は `.gitignore` で除外されている。

この手順は `.claude/rules/claude_edit.md` に rules として定義されており、Claude Code が自動的に参照する。

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
