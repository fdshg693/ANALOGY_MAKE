# scripts/ — Claude ワークフロー自動化

## これは何か

`claude_loop.py` は YAML ワークフロー定義に従って Claude CLI を順次呼び出す Python スクリプト。プロジェクトのメジャー/マイナーバージョン管理フロー（`/issue_plan` → `/split_plan` → `/imple_plan` → ...）を自動で回すための実行基盤であり、ログ出力・自動コミット・未コミット検出・デスクトップ通知・フィードバック注入などの周辺機能を備える。

## 前提条件

- Python 3.10+（`list[str] | None` などの PEP 604 型ヒント、dataclass なし、標準ライブラリのみ想定）
- PyYAML。未インストールの場合: `python -m pip install pyyaml`
- Claude CLI（`claude` コマンドが PATH 上にあること）

`scripts/` 編集時に毎回守るべき stable な規約（Python 前提・pathlib 使用・CLI 引数処理・frontmatter 作法・ログ出力）は `.claude/rules/scripts.md` に集約されている。本 README は全体像と詳細仕様の一次資料、rules は agents 向け簡潔版という責務分担。

## ファイル一覧

### ワークフロー実行（`claude_loop` 系）

| ファイル | 役割 |
|---|---|
| `claude_loop.py` | CLI エントリ。`parse_args` / `main` / `_run_steps` のみを保持 |
| `claude_loop_lib/` | ワークフロー実行に必要な関数群をモジュール分割したパッケージ |
| `claude_loop.yaml` | フルワークフロー（6 ステップ）定義 |
| `claude_loop_quick.yaml` | 軽量ワークフロー（3 ステップ）定義 |
| `claude_loop_research.yaml` | 調査・実験ワークフロー（8 ステップ）定義。`/research_context` / `/experiment_test` を挟む |
| `claude_loop_issue_plan.yaml` | `/issue_plan` 単独実行用 YAML（`--workflow auto` の第 1 段でも使用） |
| `claude_loop_scout.yaml` | `--workflow scout` で起動する能動 ISSUE 探索 YAML（1 ステップ、`auto` 非混入） |
| `claude_loop_question.yaml` | `--workflow question` で起動する調査専用 YAML（1 ステップ、`auto` 非混入） |

`claude_loop_lib/` のモジュール構成:

| モジュール | 内容 |
|---|---|
| `workflow.py` | YAML ロード・バリデーション・`get_steps` / `resolve_defaults` / `resolve_command_config` |
| `validation.py` | 起動前 validation。`validate_startup()` を公開（詳細は下記「起動前 validation」節） |
| `feedbacks.py` | `FEEDBACKS/` 配下の frontmatter 解析、ロード、消費（`done/` 移動） |
| `commands.py` | `build_command`、ステップイテレータ（`iter_steps_for_loop_limit` / `iter_steps_for_step_limit`） |
| `logging_utils.py` | `TeeWriter`、`create_log_path`、`print_step_header`、`format_duration` |
| `git_utils.py` | `get_head_commit` / `check_uncommitted_changes` / `auto_commit_changes` |
| `notify.py` | `notify_completion(RunSummary)`（toast → beep フォールバック、run サマリ化・永続表示寄り） |
| `deferred_commands.py` | Deferred command queue（ver16.1）。`data/deferred/` の request 走査・外部実行・結果保存・resume prompt 組み立てを担う（詳細: [USAGE.md](USAGE.md#deferred-command-queue)） |
| `issues.py` | ISSUE frontmatter 共通ヘルパ（`VALID_STATUS` / `VALID_ASSIGNED` / `extract_status_assigned`）。`issue_status.py` と `issue_worklist.py` の共通基盤 |
| `questions.py` | Question frontmatter 共通ヘルパ（`issues.py` の並列実装、`review` ステータスを持たない）。`question_status.py` と `question_worklist.py` の共通基盤 |

### ISSUES 管理ツール

| ファイル | 役割 |
|---|---|
| `issue_status.py` | `ISSUES/{category}/{high,medium,low}/*.md` の `status` / `assigned` 分布を表示する読み取り専用スクリプト |
| `issue_worklist.py` | `assigned` / `status` で ISSUE を絞り込み、`text` / `json` で出力する読み取り専用スクリプト（詳細: [USAGE.md](USAGE.md)） |
| `question_status.py` | `QUESTIONS/{category}/{high,medium,low}/*.md` の `status` / `assigned` 分布を表示する読み取り専用スクリプト |
| `question_worklist.py` | `assigned` / `status` で Question を絞り込み、`text` / `json` で出力する読み取り専用スクリプト |

### 補助ツール

| ファイル | 役割 |
|---|---|
| `claude_sync.py` | `.claude/` ⇔ `.claude_sync/` 同期スクリプト。CLI `-p` モードで `.claude/` を編集できない制約を回避するためのワークアラウンド |

## クイックスタート

```bash
# デフォルト（= --workflow auto、/issue_plan の判定に従って full/quick 自動選択）
python scripts/claude_loop.py

# 明示的に full/quick/research を指定
python scripts/claude_loop.py --workflow full
python scripts/claude_loop.py --workflow quick
python scripts/claude_loop.py --workflow research

# /issue_plan だけ 1 回回す（SKILL 調整・ISSUE レビュー定期実行向け）
python scripts/claude_loop.py --workflow scripts/claude_loop_issue_plan.yaml

# ステップ 3 から開始（auto モードでは使えない）
python scripts/claude_loop.py --workflow full --start 3

# 2 ループ実行（全ステップを 2 周）
python scripts/claude_loop.py --max-loops 2

# コマンド確認のみ（実行・ログ・通知なし）
python scripts/claude_loop.py --dry-run

# 事前に未コミット変更を自動コミットしてから開始
python scripts/claude_loop.py --auto-commit-before
```

### 無人実行モードについて

ver13.0 で `--auto` フラグと YAML の `mode: / command.auto_args` 設定は撤去された。通常起動 (`python scripts/claude_loop.py`) が常に無人挙動を内包する（`AskUserQuestion` 無効化・unattended system prompt 注入）ため、別モードを意識する必要はない。

旧 CLI `--auto` を指定した場合は argparse の `unrecognized arguments` エラーで即座に落ちる。旧 YAML の `mode:` / `command.auto_args` は起動前 validation で拒否される（エラーメッセージに「removed in ver13.0」と表示される）。

`--workflow auto` は別概念（ワークフロー自動選択。`/issue_plan` を先行実行して結果に応じて full/quick を選ぶ）であり、撤去されていない。

## full / quick / research の使い分け

| 条件 | 推奨 |
|---|---|
| MASTER_PLAN の新項目着手で外部仕様確認・実装方式実験・長時間検証・隔離環境試行のいずれか 1 つを要する | research |
| MASTER_PLAN の新項目着手・アーキテクチャ変更・新規ライブラリ導入（research 条件に該当しない） | full |
| 変更ファイル 4 つ以上、または `ISSUES/*/high` の複雑な対応 | full |
| 単一 ISSUE 対応・バグ修正（原因特定済み）・既存機能の微調整 | quick |
| ドキュメント/テスト追加、変更ファイル 3 つ以下 | quick |

テキスト編集のみで各ファイル数行程度の変更なら、4 ファイル以上でも quick を選択してよい。

## research（実装前調査・実験）

`--workflow research` は実装前に調査・実験を正式 step として挟む 8 step workflow（ver16.0 で追加）。`research_context` / `experiment_test` SKILL が `docs/{cat}/ver{X.Y}/RESEARCH.md` / `EXPERIMENT.md` を生成し、後続 `/imple_plan` がそれを入力として実装方式を確定する。

```bash
python scripts/claude_loop.py --workflow research
```

8 step 構成: `/issue_plan → /split_plan → /research_context → /experiment_test → /imple_plan → /wrap_up → /write_current → /retrospective`。

`--workflow auto` は `ROUGH_PLAN.md` frontmatter `workflow: research` を検出した場合に phase2 で自動選択する。選定条件・詳細は `.claude/skills/issue_plan/SKILL.md` および `.claude/skills/meta_judge/WORKFLOW.md` §3 を参照。

### `question` / `research` の責務境界

| 観点 | `question` (`QUESTIONS/`) | `research` (`docs/{cat}/ver{X.Y}/RESEARCH.md`) |
|---|---|---|
| (a) 最終成果物 | 報告書のみ（`docs/{cat}/questions/{slug}.md`） | **コード変更**（`RESEARCH.md` は中間成果物） |
| (b) 入力キュー | `QUESTIONS/{cat}/{priority}/` | `ISSUES/{cat}/{priority}/` または MASTER_PLAN |
| (c) workflow | 調査→報告書で終了（実装に進まない） | 調査→実験→実装→retrospective まで 8 step 完走 |

実験スクリプトの配置規約は [`../experiments/README.md`](../experiments/README.md) を参照。

## scout（能動探索）

`--workflow scout` は ISSUE 起票専用の opt-in workflow（ver15.0 で追加）。定期監査・節目での潜在課題洗い出しに使う。

```bash
python scripts/claude_loop.py --workflow scout --category util
```

1 run で以下のみを実施して終了する:

- 対象カテゴリのコード / tests / docs / 直近 `RETROSPECTIVE.md` / `MASTER_PLAN.md` / 既存 `ISSUES/` を走査
- 潜在課題を **最大 3 件** まで `ISSUES/{カテゴリ}/{priority}/*.md` に新規起票（原則 `raw / ai`、昇格条件を満たす小粒のみ `ready / ai`）
- 起票件数・パス・重複でスキップした候補をサマリ出力

**`--workflow auto` には自動混入しない**（明示起動のみ）。起票された ISSUE は次回 `/issue_plan` のレビューフェーズで既存の `review / ai` → `ready / ai` or `need_human_action / human` 遷移に乗る。推奨頻度は週次〜ループ節目程度（毎ループ実行しない）。

## question（調査専用）

`--workflow question` は調査専用の opt-in workflow（ver15.2 で追加）。`QUESTIONS/{カテゴリ}/{priority}/*.md` の `ready / ai` を 1 件選び、コードベース・ドキュメント・既存 ISSUE を読み解いて報告書を出力する。

```bash
python scripts/claude_loop.py --workflow question --category util
```

1 run で以下のみを実施して終了する:

- `QUESTIONS/{カテゴリ}/{priority}/*.md` から最上位優先度の `ready / ai` を 1 件選定（0 件ならノーオペで終了）
- 関連コード・docs・既存 ISSUE を調査し、`docs/{カテゴリ}/questions/{slug}.md` に固定 5 セクションの報告書を出力（**問い** / **確認した証拠** / **結論** / **不確実性** / **次アクション候補**）
- 結論確定 → Question を `QUESTIONS/{カテゴリ}/done/` へ移動
- 結論未確定（情報不足等） → Question を `need_human_action / human` に書き換え（`done/` 移動はしない）
- 実装課題が明確化した場合は新規 ISSUE を `ISSUES/` に起票（実装はしない）

**`--workflow auto` には自動混入しない**（明示起動のみ）。`QUESTIONS/` は本 workflow 専属の queue であり、`auto` / `full` / `quick` / `scout` は走査しない。詳細仕様（frontmatter / ライフサイクル）は [`QUESTIONS/README.md`](../QUESTIONS/README.md) を参照。

## ログの見方

ログファイルは `logs/workflow/{YYYYMMDD_HHMMSS}_{workflow_stem}.log`（`.gitignore` 済、手動削除可）。

**失敗ステップの特定**: `--- end (exit: {code}, ...)` 行の exit code が非 0 の箇所を探す。直前の stdout/stderr に原因が記録されている。

**手動再開**: ワークフローフッターの `Last session (full):` UUID を使って `claude -r <uuid>` で続きから実行できる。または `--start N` でステップ番号を指定して再実行（auto モード以外）。

**繰り返すエラーの切り分け**: `continue: true` のステップは前ステップのセッションを引き継ぐため、前ステップで混乱があると後続でも連鎖することがある。その場合は `--start N` で問題ステップから単独再実行する。

詳細フォーマット仕様は [`USAGE.md`](USAGE.md) の「ログフォーマット（詳細）」を参照。

## 完了通知（run 単位）

ver15.4 から、通知は **workflow 全体の終了時に 1 回だけ** 発火する。`--max-loops N` で複数ループ回しても通知は最後に 1 回のみ。通知タイミングは以下の 3 経路に一貫:

- 正常終了: 「Workflow Complete / {label} / {loops} loops / {steps} steps / {duration}」
- step 失敗: 「Workflow Failed / failed at {step} (exit {code}) / ...」
- 中断（Ctrl+C / SIGTERM）: 「Workflow Interrupted / interrupted ({reason}) at {step} / ...」

Windows トーストは `scenario='reminder'` + dismiss ボタン構成で Action Center に残ることを狙い、OS がこれを拒否した場合は `duration='long'` にフォールバックする（さらに失敗すると beep + console 出力）。`--no-notify` / `--dry-run` は通知を抑止する（成功/失敗/中断のいずれの経路でも）。

## フィードバック注入機能

`FEEDBACKS/*.md` を作成すると対応するステップ実行時に `--append-system-prompt` に注入される。`step:` frontmatter でステップを絞り込み可（省略で全ステップに適用）。ステップ正常終了後に `FEEDBACKS/done/` へ移動される。異常終了（非ゼロ exit / 例外 / Ctrl-C 等）時は移動されず、`FEEDBACKS/` に残って次回 run で再消費される（retry のための温存）。なお `load_feedbacks()` は非再帰 glob で `FEEDBACKS/done/` を読まないため、done/ のファイルを再利用したい場合は `FEEDBACKS/` へ手動で戻す必要がある。詳細は [`USAGE.md`](USAGE.md) を参照。

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

`--workflow auto` の場合、phase 1 (`claude_loop_issue_plan.yaml`) と phase 2 候補 3 本 (`claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_research.yaml`) を**すべて事前に検証**する。これにより ROUGH_PLAN.md 生成結果に関わらず「validation 通過 = 最後まで到達可能」という契約が成り立つ。

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
