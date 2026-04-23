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
| `validation.py` | 起動前 validation。`validate_startup()` を公開（詳細は下記「起動前 validation」節） |
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

## 起動前 validation

`claude_loop.py` は step 1 を実行する前に以下を検査する。1 件でも `error` があれば exit code 2 で終了し、step 実行には進まない。`--dry-run` 時も走る。

| 検査項目 | 重大度 |
|---|---|
| `.claude/CURRENT_CATEGORY` の中身（空・不正文字は error、欠如は warning → `app` フォールバック） | error / warning |
| `docs/{category}/` ディレクトリが存在すること | error |
| `command.executable` が PATH 上で解決できること (`shutil.which`) | error |
| YAML の存在・parse 成功・top-level mapping | error |
| `defaults` / `steps[]` のキー集合が許容範囲内 (`model` / `effort` / `system_prompt` / `append_system_prompt` / `name` / `prompt` / `args` / `continue`) | error |
| override キーの型（非空 string） / `continue` の型（bool） | error |
| `model` 値が既知セット (`opus` / `sonnet` / `haiku`) に含まれること | **warning** |
| `effort` 値が既知セット (`low` / `medium` / `high` / `xhigh` / `max`) に含まれること | **warning** |
| step.prompt の先頭が `/` の場合、`.claude/skills/<name>/SKILL.md` が存在すること | error |
| `command` セクションが指定された場合、mapping であること | error |

`--workflow auto` の場合、phase 1 (`claude_loop_issue_plan.yaml`) と phase 2 候補 2 本 (`claude_loop.yaml` / `claude_loop_quick.yaml`) を**すべて事前に検証**する。これにより ROUGH_PLAN.md 生成結果に関わらず「validation 通過 = 最後まで到達可能」という契約が成り立つ。

エラーは可能な範囲で一括収集されて末尾に列挙される（例: YAML A が parse 失敗しても、YAML B 内の step typo はそのまま報告される）。ただし、YAML 単位での parse 失敗や top-level 非 mapping など致命的な段階では当該 YAML の後続検証のみスキップされる。

### 拡張ガイド

`validation.py` は `workflow.py` から `ALLOWED_STEP_KEYS` / `ALLOWED_DEFAULTS_KEYS` / `OVERRIDE_STRING_KEYS` を import しており、両者は片方の変更に自動で追随する。新しい override キーを追加する場合は `workflow.py` の定数のみ更新すればよい。

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
