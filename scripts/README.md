# scripts/ — Claude ワークフロー自動化

## これは何か

`claude_loop.py` は YAML ワークフロー定義に従って Claude CLI を順次呼び出す Python スクリプト。プロジェクトのメジャー/マイナーバージョン管理フロー（`/split_plan` → `/imple_plan` → ...）を自動で回すための実行基盤であり、ログ出力・自動コミット・未コミット検出・デスクトップ通知・フィードバック注入などの周辺機能を備える。

## 前提条件

- Python 3.10+（`list[str] | None` などの PEP 604 型ヒント、dataclass なし、標準ライブラリのみ想定）
- PyYAML。未インストールの場合: `python -m pip install pyyaml`
- Claude CLI（`claude` コマンドが PATH 上にあること）

## ファイル一覧

| ファイル | 役割 |
|---|---|
| `claude_loop.py` | CLI エントリ。`parse_args` / `main` / `_run_steps` のみを保持 |
| `claude_loop_lib/` | ワークフロー実行に必要な関数群をモジュール分割したパッケージ（詳細は下記） |
| `claude_loop.yaml` | フルワークフロー（5 ステップ）定義 |
| `claude_loop_quick.yaml` | 軽量ワークフロー（3 ステップ）定義 |
| `claude_sync.py` | `.claude/` ⇔ `.claude_sync/` 同期スクリプト。CLI `-p` モードで `.claude/` を編集できない制約を回避するためのワークアラウンド |

### `claude_loop_lib/` のモジュール構成

| モジュール | 内容 |
|---|---|
| `workflow.py` | YAML ロード・バリデーション・`get_steps` / `resolve_defaults` / `resolve_command_config` / `resolve_mode` |
| `feedbacks.py` | `FEEDBACKS/` 配下の frontmatter 解析、ロード、消費（`done/` 移動） |
| `commands.py` | `build_command`、ステップイテレータ（`iter_steps_for_loop_limit` / `iter_steps_for_step_limit`） |
| `logging_utils.py` | `TeeWriter`、`create_log_path`、`print_step_header`、`format_duration` |
| `git_utils.py` | `get_head_commit` / `check_uncommitted_changes` / `auto_commit_changes` |
| `notify.py` | `notify_completion`（toast → beep フォールバック） |

## クイックスタート

```bash
# フルワークフロー実行
python scripts/claude_loop.py

# 軽量ワークフロー実行
python scripts/claude_loop.py -w scripts/claude_loop_quick.yaml

# ステップ 3 から開始
python scripts/claude_loop.py --start 3

# 2 ループ実行（全ステップを 2 周）
python scripts/claude_loop.py --max-loops 2

# 最大 7 ステップ分だけ実行
python scripts/claude_loop.py --max-step-runs 7

# コマンド確認のみ（実行・ログ・通知なし）
python scripts/claude_loop.py --dry-run

# ログ無効
python scripts/claude_loop.py --no-log

# 自動実行モード（対話 UI を排除）
python scripts/claude_loop.py --auto

# 事前に未コミット変更を自動コミットしてから開始
python scripts/claude_loop.py --auto-commit-before
```

## CLI オプション一覧

| オプション | 短縮 | 型 | デフォルト | 概要 |
|---|---|---|---|---|
| `--workflow` | `-w` | Path | `scripts/claude_loop.yaml` | ワークフロー YAML ファイルパス |
| `--start` | `-s` | int (>=1) | `1` | 開始ステップ番号（1-based） |
| `--cwd` | - | Path | プロジェクトルート | Claude コマンドの作業ディレクトリ |
| `--dry-run` | - | flag | `False` | コマンド確認のみ（実行・ログ・通知なし） |
| `--log-dir` | - | Path | `logs/workflow/` | ログファイル出力先ディレクトリ |
| `--no-log` | - | flag | `False` | ログファイル出力を無効化 |
| `--no-notify` | - | flag | `False` | ワークフロー完了通知を無効化 |
| `--auto-commit-before` | - | flag | `False` | ワークフロー開始前に未コミット変更を自動コミット |
| `--auto` | - | flag | `False` | 自動実行モード強制（YAML の `mode.auto` をオーバーライド） |
| `--max-loops` | - | int (>=1) | `1` | 最大ワークフローループ回数（`--max-step-runs` と排他） |
| `--max-step-runs` | - | int (>=1) | - | 最大ステップ実行回数（`--max-loops` と排他） |

## YAML ワークフロー仕様

ワークフロー YAML は `mode` / `command` / `defaults` / `steps` の 4 セクションで構成される。

```yaml
mode:
  auto: false                  # デフォルトの実行モード（--auto で CLI からオーバーライド可能）

command:
  executable: claude
  prompt_flag: -p
  args:
    - --dangerously-skip-permissions
  auto_args:                   # auto モード時のみ common_args に追加される
    - --disallowedTools "AskUserQuestion"
    - --append-system-prompt "..."

defaults:                      # 省略可。省略時は各ステップで model/effort を個別指定
  model: sonnet
  effort: medium

steps:
  - name: step_name
    prompt: /skill_name
    model: opus                # 省略可。step 側にキーが存在しない場合に defaults を継承
    effort: high               # 同上
    args:                      # 省略可。追加の CLI 引数（文字列 or リスト、shlex で分解）
      - --some-flag
```

### セクションの意味

- **mode.auto**: `true` なら `command.args + command.auto_args` を結合した引数で Claude CLI を起動する。CLI の `--auto` で常に強制可能
- **command.executable / prompt_flag / args / auto_args**: Claude 実行コマンドの構築素材。`args` は全モード共通、`auto_args` は auto モード時のみ追加
- **defaults.model / effort**: 全ステップに適用する共通値。各ステップでキーが存在しない場合のみ参照される（**キー存在ベース**の上書き）
- **steps[].model / effort**: ステップ固有の上書き。`None` は「未指定」として扱い defaults を継承。空文字列はエラー

### サンプル YAML

- フル: [`claude_loop.yaml`](claude_loop.yaml) — 5 ステップ（`split_plan` → `imple_plan` → `wrap_up` → `write_current` → `retrospective`）
- 軽量: [`claude_loop_quick.yaml`](claude_loop_quick.yaml) — 3 ステップ（`quick_plan` → `quick_impl` → `quick_doc`）

## フル/quick の使い分け

| 条件 | 推奨 |
|---|---|
| MASTER_PLAN の新項目着手・アーキテクチャ変更・新規ライブラリ導入 | full |
| 変更ファイル 4 つ以上、または `ISSUES/*/high` の複雑な対応 | full |
| 単一 ISSUE 対応・バグ修正（原因特定済み）・既存機能の微調整 | quick |
| ドキュメント/テスト追加、変更ファイル 3 つ以下 | quick |

テキスト編集のみで各ファイル数行程度の変更なら、4 ファイル以上でも quick を選択してよい。

## フィードバック注入機能

`FEEDBACKS/*.md` を作成すると、対応するステップ実行時に `--append-system-prompt` に `## User Feedback` セクションとして注入される。

### `step` フィールドの書き方

```markdown
---
step: split_plan
---

split_plan に対するフィードバック本文
```

```markdown
---
step: [split_plan, imple_plan]
---

複数ステップに適用したい場合
```

`step` を省略した場合は**全ステップに注入**されるキャッチオール扱い。

### 消費後の挙動

ステップが正常終了した時点で、注入されたフィードバックファイルは `FEEDBACKS/done/` に `shutil.move` される。`FEEDBACKS/done/` 配下は次回以降のロードでは対象外。

## ログフォーマット

ログファイル名: `{YYYYMMDD_HHMMSS}_{workflow_stem}.log`（デフォルト出力先: `logs/workflow/`）

```
=====================================
Workflow: {workflow_name}
Started: {timestamp}
Commit (start): {hash}
Uncommitted: {status}                ← 未コミット変更がある場合のみ
=====================================

[1/N] {step_name}
Started: {timestamp}
Model: {model}, Effort: {effort}     ← 未指定の側は省略、両方未指定なら行ごと省略
$ {command}
--- stdout/stderr ---
（出力内容）
--- end (exit: {code}, duration: {duration}) ---
Commit: {before} -> {after}          ← コミットが変化した場合のみ

=====================================
Finished: {timestamp}
Commit (end): {hash}
Duration: {total_duration}
Result: SUCCESS (N/N steps completed)
=====================================
```

コマンドログは `shlex.join(command)` で出力されるため、スペース・特殊文字を含む引数は自動でシェルクォートされる。

## claude_sync.py

Claude CLI の `-p` モードではセキュリティ制約により `.claude/` 配下のファイルを直接編集できない。`claude_sync.py` は `.claude/` の内容を書き込み可能な `.claude_sync/` にコピーし、編集後に書き戻すための補助スクリプト。

```bash
# .claude/ → .claude_sync/ に書き出し
python scripts/claude_sync.py export

# .claude_sync/ → .claude/ に反映
python scripts/claude_sync.py import
```

外部依存なし（標準ライブラリのみ）。

## 拡張ガイド

- **新しい SKILL を追加する場合**: `claude_loop.yaml` または `claude_loop_quick.yaml` の `steps:` に `{ name, prompt, model?, effort?, args? }` を追記する
- **Python コードを拡張する場合**: 触る関心事に対応する `claude_loop_lib/` 配下のモジュールに手を入れる。責務分担は上記「モジュール構成」を参照
- **新規 CLI オプションを追加する場合**: `claude_loop.py` の `parse_args()` と、追加した値を渡す先（多くは `claude_loop_lib/commands.py` の `build_command`）の両方を更新する必要がある
- **フィードバックのスキーマ拡張**: `claude_loop_lib/feedbacks.py` の `parse_feedback_frontmatter` に追加フィールドのパースを足す

## テスト

```bash
python -m unittest tests.test_claude_loop
```

現状 89 件。`tests/test_claude_loop.py` は `claude_loop_lib.*` のパッチターゲットを使って個別モジュールをモックしている。

## 関連ドキュメント

- `docs/util/MASTER_PLAN.md` — util カテゴリ全体のロードマップ
- `docs/util/ver{最新}/CURRENT.md` — コード現況のインデックス
- `docs/util/ver{最新}/CURRENT_scripts.md` — スクリプトとモジュールの詳細（本 README と重複しない内部情報）
