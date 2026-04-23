# scripts/ — Claude ワークフロー自動化

## これは何か

`claude_loop.py` は YAML ワークフロー定義に従って Claude CLI を順次呼び出す Python スクリプト。プロジェクトのメジャー/マイナーバージョン管理フロー（`/issue_plan` → `/split_plan` → `/imple_plan` → ...）を自動で回すための実行基盤であり、ログ出力・自動コミット・未コミット検出・デスクトップ通知・フィードバック注入などの周辺機能を備える。

## 前提条件

- Python 3.10+（`list[str] | None` などの PEP 604 型ヒント、dataclass なし、標準ライブラリのみ想定）
- PyYAML。未インストールの場合: `python -m pip install pyyaml`
- Claude CLI（`claude` コマンドが PATH 上にあること）

## ファイル一覧

### ワークフロー実行（`claude_loop` 系）

| ファイル | 役割 |
|---|---|
| `claude_loop.py` | CLI エントリ。`parse_args` / `main` / `_run_steps` のみを保持 |
| `claude_loop_lib/` | ワークフロー実行に必要な関数群をモジュール分割したパッケージ |
| `claude_loop.yaml` | フルワークフロー（6 ステップ）定義 |
| `claude_loop_quick.yaml` | 軽量ワークフロー（3 ステップ）定義 |
| `claude_loop_issue_plan.yaml` | `/issue_plan` 単独実行用 YAML（`--workflow auto` の第 1 段でも使用） |

`claude_loop_lib/` のモジュール構成:

| モジュール | 内容 |
|---|---|
| `workflow.py` | YAML ロード・バリデーション・`get_steps` / `resolve_defaults` / `resolve_command_config` / `resolve_mode` |
| `feedbacks.py` | `FEEDBACKS/` 配下の frontmatter 解析、ロード、消費（`done/` 移動） |
| `commands.py` | `build_command`、ステップイテレータ（`iter_steps_for_loop_limit` / `iter_steps_for_step_limit`） |
| `logging_utils.py` | `TeeWriter`、`create_log_path`、`print_step_header`、`format_duration` |
| `git_utils.py` | `get_head_commit` / `check_uncommitted_changes` / `auto_commit_changes` |
| `notify.py` | `notify_completion`（toast → beep フォールバック） |
| `issues.py` | ISSUE frontmatter 共通ヘルパ（`VALID_STATUS` / `VALID_ASSIGNED` / `extract_status_assigned`）。`issue_status.py` と `issue_worklist.py` の共通基盤 |

### ISSUES 管理ツール

| ファイル | 役割 |
|---|---|
| `issue_status.py` | `ISSUES/{category}/{high,medium,low}/*.md` の `status` / `assigned` 分布を表示する読み取り専用スクリプト |
| `issue_worklist.py` | `assigned` / `status` で ISSUE を絞り込み、`text` / `json` で出力する読み取り専用スクリプト（詳細: [USAGE.md](USAGE.md)） |

### 補助ツール

| ファイル | 役割 |
|---|---|
| `claude_sync.py` | `.claude/` ⇔ `.claude_sync/` 同期スクリプト。CLI `-p` モードで `.claude/` を編集できない制約を回避するためのワークアラウンド |

## クイックスタート

```bash
# デフォルト（= --workflow auto、/issue_plan の判定に従って full/quick 自動選択）
python scripts/claude_loop.py

# 明示的に full/quick を指定
python scripts/claude_loop.py --workflow full
python scripts/claude_loop.py --workflow quick

# /issue_plan だけ 1 回回す（SKILL 調整・ISSUE レビュー定期実行向け）
python scripts/claude_loop.py --workflow scripts/claude_loop_issue_plan.yaml

# ステップ 3 から開始（auto モードでは使えない）
python scripts/claude_loop.py --workflow full --start 3

# 2 ループ実行（全ステップを 2 周）
python scripts/claude_loop.py --max-loops 2

# コマンド確認のみ（実行・ログ・通知なし）
python scripts/claude_loop.py --dry-run

# 自動実行モード（対話 UI を排除）
python scripts/claude_loop.py --auto

# 事前に未コミット変更を自動コミットしてから開始
python scripts/claude_loop.py --auto-commit-before
```

### `--auto` と `--workflow auto` の違い

| フラグ | 意味 |
|---|---|
| `--auto` | 無人実行モード。`command.auto_args` を結合し、AskUserQuestion を無効化 |
| `--workflow auto` | ワークフロー自動選択。`/issue_plan` を先行実行して結果に応じて full/quick を選ぶ |

両者は独立。併用例: `python scripts/claude_loop.py --auto --workflow auto`（無人モードでワークフロー自動選択）。

## フル/quick の使い分け

| 条件 | 推奨 |
|---|---|
| MASTER_PLAN の新項目着手・アーキテクチャ変更・新規ライブラリ導入 | full |
| 変更ファイル 4 つ以上、または `ISSUES/*/high` の複雑な対応 | full |
| 単一 ISSUE 対応・バグ修正（原因特定済み）・既存機能の微調整 | quick |
| ドキュメント/テスト追加、変更ファイル 3 つ以下 | quick |

テキスト編集のみで各ファイル数行程度の変更なら、4 ファイル以上でも quick を選択してよい。

## ログの見方

ログファイルは `logs/workflow/{YYYYMMDD_HHMMSS}_{workflow_stem}.log`（`.gitignore` 済、手動削除可）。

**失敗ステップの特定**: `--- end (exit: {code}, ...)` 行の exit code が非 0 の箇所を探す。直前の stdout/stderr に原因が記録されている。

**手動再開**: ワークフローフッターの `Last session (full):` UUID を使って `claude -r <uuid>` で続きから実行できる。または `--start N` でステップ番号を指定して再実行（auto モード以外）。

**繰り返すエラーの切り分け**: `continue: true` のステップは前ステップのセッションを引き継ぐため、前ステップで混乱があると後続でも連鎖することがある。その場合は `--start N` で問題ステップから単独再実行する。

詳細フォーマット仕様は [`USAGE.md`](USAGE.md) の「ログフォーマット（詳細）」を参照。

## フィードバック注入機能

`FEEDBACKS/*.md` を作成すると対応するステップ実行時に `--append-system-prompt` に注入される。`step:` frontmatter でステップを絞り込み可（省略で全ステップに適用）。ステップ正常終了後に `FEEDBACKS/done/` へ移動される。詳細は [`USAGE.md`](USAGE.md) を参照。

## claude_sync.py

Claude CLI の `-p` モードではセキュリティ制約により `.claude/` 配下のファイルを直接編集できない。`claude_sync.py` は `.claude/` の内容を書き込み可能な `.claude_sync/` にコピーし、編集後に書き戻すための補助スクリプト。

```bash
# .claude/ → .claude_sync/ に書き出し
python scripts/claude_sync.py export

# .claude_sync/ → .claude/ に反映
python scripts/claude_sync.py import
```

外部依存なし（標準ライブラリのみ）。

## テスト

```bash
# 全件実行（推奨）
python -m unittest discover -s scripts/tests -t .

# 個別ファイル指定
python -m unittest scripts.tests.test_commands

# 個別クラス指定
python -m unittest scripts.tests.test_workflow.TestOverrideInheritanceMatrix
```

テストは `scripts/tests/` 配下に対象モジュール別に分割されている（`test_<module>.py` の命名規則）。

## 関連ドキュメント

- [`USAGE.md`](USAGE.md) — CLI オプション一覧・YAML 仕様詳細・ログフォーマット詳細・拡張ガイド
- `docs/util/MASTER_PLAN.md` — util カテゴリ全体のロードマップ
- `docs/util/ver{最新}/CURRENT.md` — コード現況のインデックス
- `docs/util/ver{最新}/CURRENT_scripts.md` — スクリプトとモジュールの詳細（内部情報）
