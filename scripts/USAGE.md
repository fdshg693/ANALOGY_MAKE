# scripts/ 使い方詳細 — CLI オプション・YAML 仕様

詳細リファレンス。日常操作は [`README.md`](README.md) のクイックスタートで十分。

## issue_worklist.py

`ISSUES/{category}/{high,medium,low}/*.md` を走査し、frontmatter の
`status` / `assigned` で絞り込んだ ISSUE 一覧を出力する読み取り専用スクリプト。
`issue_status.py` が件数サマリを返すのに対し、こちらは個別 ISSUE のリストを返す。

```bash
# デフォルト（現在カテゴリ、assigned=ai、status=ready,review、text 出力）
python scripts/issue_worklist.py

# JSON で取得（機械可読）
python scripts/issue_worklist.py --format json

# 人間向け need_human_action を確認
python scripts/issue_worklist.py --assigned human --status need_human_action

# 別カテゴリを指定
python scripts/issue_worklist.py --category app
```

`--category` の既定値は `.claude/CURRENT_CATEGORY` の内容（未設定時は `app`）。
`--status` はカンマ区切りで複数指定可。受理される値は `raw` / `review` / `ready` / `need_human_action`。

`/retrospective` SKILL も本スクリプトを使って次バージョン推奨の材料を収集する。

## CLI オプション一覧

| オプション | 短縮 | 型 | デフォルト | 概要 |
|---|---|---|---|---|
| `--workflow` | `-w` | str | `auto` | `auto` / `full` / `quick` / YAML パスのいずれか |
| `--start` | `-s` | int (>=1) | `1` | 開始ステップ番号（1-based） |
| `--cwd` | - | Path | プロジェクトルート | Claude コマンドの作業ディレクトリ |
| `--dry-run` | - | flag | `False` | コマンド確認のみ（実行・ログ・通知なし） |
| `--log-dir` | - | Path | `logs/workflow/` | ログファイル出力先ディレクトリ |
| `--no-log` | - | flag | `False` | ログファイル出力を無効化 |
| `--no-notify` | - | flag | `False` | ワークフロー完了通知を無効化（run 単位で 1 回発火、中断時も含め抑止対象） |
| `--auto-commit-before` | - | flag | `False` | ワークフロー開始前に未コミット変更を自動コミット |
| `--max-loops` | - | int (>=1) | `1` | 最大ワークフローループ回数（`--max-step-runs` と排他） |
| `--max-step-runs` | - | int (>=1) | - | 最大ステップ実行回数（`--max-loops` と排他） |

## YAML ワークフロー仕様

ワークフロー YAML は `command` / `defaults` / `steps` の 3 セクションで構成される（ver13.0 で `mode:` セクションは撤去）。

```yaml
command:
  executable: claude
  prompt_flag: -p
  args:
    - --dangerously-skip-permissions
    - --disallowedTools "AskUserQuestion"

defaults:                      # 省略可。省略時は各ステップで個別指定
  model: sonnet
  effort: medium
  # system_prompt / append_system_prompt も指定可

steps:
  - name: step_name
    prompt: /skill_name
    model: opus                # 省略可。step 側にキーが存在しない場合に defaults を継承
    effort: high               # 同上
    system_prompt: "..."       # 省略可。Claude CLI の --system-prompt（デフォルト置換）
    append_system_prompt: "..."# 省略可。Claude CLI の --append-system-prompt
    continue: true             # 省略可。直前ステップのセッションを引き継いで実行
    args:                      # 省略可。追加の CLI 引数（文字列 or リスト、shlex で分解）
      - --some-flag
```

### セクションの意味

- **command.executable / prompt_flag / args**: Claude 実行コマンドの構築素材。全ステップ共通
- **defaults.model / effort / system_prompt / append_system_prompt**: 全ステップに適用する共通値。各ステップでキーが存在しない場合のみ参照される（**キー存在ベース**の上書き）
- **steps[].model / effort / system_prompt / append_system_prompt**: ステップ固有の上書き。`None` は「未指定」として扱い defaults を継承。空文字列はエラー
- **steps[].continue**: `true` なら直前ステップで使用した session ID を `-r <uuid>` で再利用し、前ステップの会話履歴を引き継いで実行する。`false` または省略時は新規 session ID（`uuid.uuid4()` で発行）を `--session-id <uuid>` で起動する。bool 以外（文字列・整数等）はエラー

### override 可能なキー（defaults / steps[] 共通）

string 型のみ。`None` は未指定扱い、空文字列はエラー。

| キー | CLI flag | 役割 |
|---|---|---|
| `model` | `--model` | 使用モデル（`opus` / `sonnet` 等） |
| `effort` | `--effort` | 推論努力レベル（`low` / `medium` / `high` / `xhigh` / `max`） |
| `system_prompt` | `--system-prompt` | デフォルト system prompt を完全置換 |
| `append_system_prompt` | `--append-system-prompt` | デフォルト system prompt に追加 |

未知キー（例: `temperature`, `max_tokens`）は YAML パース時にエラーで落とす（silent ignore はしない）。Claude CLI が当該フラグをサポートする必要あり。

> **注意**: `system_prompt` はデフォルト system prompt を完全置換するため、CLAUDE.md 自動読込みなど Claude Code 既定挙動を失う可能性がある。通常は `append_system_prompt` を使うこと。

### 継承ルール

各 step の有効設定は次の 3 段階で解決される:

1. `steps[i].<key>` にキーが存在し値が non-`None` → step 値を採用
2. 上記が無く `defaults.<key>` にキーが存在し値が non-`None` → defaults 値を採用
3. 上記いずれも無ければ Claude CLI の既定挙動に従う（該当フラグを渡さない）

`append_system_prompt` も同じ 3 段階継承（step 値が defaults 値を上書きし、合成は行わない）。

### `append_system_prompt` の合成順序

`build_command()` は `--append-system-prompt` 引数の本文を以下の順で連結する（区切りは空行 1 つ）。ver13.0 以降、2. の unattended 注意文は**常時**注入される（旧 auto モード分岐は撤去）:

1. `Current workflow log: {path}` 行（ログ有効時）
2. Unattended 実行注意文（常時注入。`AskUserQuestion` 禁止と ISSUE 経由の人間依頼手順を指示）
3. `## User Feedback` セクション（feedback 注入時）
4. step / defaults の `append_system_prompt` 値（指定時）

### `continue` の使い分け

- **継続したいケース**: 前ステップの判断経緯（ツール使用結果やトレードオフの検討）を引き継ぎたい整理系ステップ。例: `imple_plan`（split_plan の判断を踏まえる）、`wrap_up`（実装ステップの判断を踏まえる）、`quick_impl` / `quick_doc`
- **新規セッションが望ましいケース**: 別視点で書き起こす整理系ステップ。例: `write_current`（現況を新規視点で整理）、`retrospective`（独立したフレーミングで振り返る）、`issue_plan` / `split_plan`（ワークフロー前半、必要情報は ROUGH_PLAN.md 経由で伝達）

### `continue` のエッジケース

- **`--start > 1`**: ワークフロー全体で `continue: true` が無効化される（前ステップ実行が無いため文脈が再現できない）。1 度だけ `WARNING: --start > 1` ログを出力する
- **ループ初回ステップ**: 1 ループ目の最初のステップに `continue: true` を指定した場合、前セッションが存在しないため `WARNING: ... no previous session exists` を 1 度出力し、新規セッションで起動する。複数ループ実行時の 2 ループ目以降の冒頭が `continue: true` のときも同様（前ループ最終ステップのセッション ID は引き継がれない）
- **`--dry-run`**: 実セッションは作成しないが、コードパスの単純化のため毎回ランダムな UUID を `uuid.uuid4()` で生成して表示する

### `--workflow auto` の分岐仕様

1. `scripts/claude_loop_issue_plan.yaml` で `/issue_plan` を実行
2. `docs/{category}/ver*/ROUGH_PLAN.md` の最新 mtime ファイルを開き frontmatter の `workflow:` を読む
3. `quick` → `claude_loop_quick.yaml` の `steps[1:]`、`full` → `claude_loop.yaml` の `steps[1:]`、`research` → `claude_loop_research.yaml` の `steps[1:]` を実行
4. `workflow:` 未記載・不正値 → `full` にフォールバック（警告を log/stderr に出力）
5. `--workflow auto` と `--start N>1` は併用不可（エラー終了）
6. `--workflow auto --dry-run` 併用時はフェーズ 1 のコマンドのみ表示し、フェーズ 2 はスキップ

**起動前 validation**: step 1 実行より前に、対象となる全 YAML（`--workflow auto` では 4 本すべて — `issue_plan` / `full` / `quick` / `research`）に対して validation が走る。1 件でも error があれば exit code 2 で終了し、step は実行されない（`--dry-run` 時も実行される）。詳細は [`README.md` 「起動前 validation」節](README.md) を参照。

`command` / `defaults` セクションは `claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_research.yaml` / `claude_loop_issue_plan.yaml` / `claude_loop_scout.yaml` / `claude_loop_question.yaml` の 6 ファイルで同一内容を維持する必要がある（いずれかを変更した場合は必ず 6 ファイル全てを同期すること）。

### サンプル YAML

- フル: [`claude_loop.yaml`](claude_loop.yaml) — 6 ステップ（`issue_plan` → `split_plan` → `imple_plan` → `wrap_up` → `write_current` → `retrospective`）
- 軽量: [`claude_loop_quick.yaml`](claude_loop_quick.yaml) — 3 ステップ（`issue_plan` → `quick_impl` → `quick_doc`）
- 調査・実験（ver16.0 追加）: [`claude_loop_research.yaml`](claude_loop_research.yaml) — 8 ステップ（`issue_plan` → `split_plan` → `research_context` → `experiment_test` → `imple_plan` → `wrap_up` → `write_current` → `retrospective`）。`--workflow research` で明示起動、または `--workflow auto` 時に ROUGH_PLAN frontmatter `workflow: research` で選択される
- issue_plan 単独: [`claude_loop_issue_plan.yaml`](claude_loop_issue_plan.yaml) — 1 ステップ（`issue_plan` のみ）。`--workflow auto` の第 1 段でも使用される
- scout（能動探索、ver15.0 追加）: [`claude_loop_scout.yaml`](claude_loop_scout.yaml) — 1 ステップ（`issue_scout` のみ）。`--workflow scout` で明示起動。`--workflow auto` には自動混入しない
- question（調査専用、ver15.2 追加）: [`claude_loop_question.yaml`](claude_loop_question.yaml) — 1 ステップ（`question_research` のみ）。`--workflow question` で明示起動。`QUESTIONS/` 専属で `--workflow auto` には自動混入しない

```yaml
# claude_loop_scout.yaml 抜粋
command:
  executable: claude
  prompt_flag: -p
  args:
    - --dangerously-skip-permissions
    - --disallowedTools "AskUserQuestion"

defaults:
  model: sonnet
  effort: medium

steps:
  - name: issue_scout
    prompt: /issue_scout
    model: opus
    effort: high
```

```yaml
# claude_loop_question.yaml 抜粋
command:
  executable: claude
  prompt_flag: -p
  args:
    - --dangerously-skip-permissions
    - --disallowedTools "AskUserQuestion"

defaults:
  model: sonnet
  effort: medium

steps:
  - name: question_research
    prompt: /question_research
    model: opus
    effort: high
```

## QUESTIONS/ と ISSUES/ の境界

実装依頼は `ISSUES/` に、調査依頼（成果物が報告書になるもの）は `QUESTIONS/` に置く。`QUESTIONS/` は `question` workflow（`--workflow question`）の専属 queue で、`auto` / `full` / `quick` / `scout` は走査しない。詳細仕様（frontmatter / ライフサイクル / 報告書配置）は [`QUESTIONS/README.md`](../QUESTIONS/README.md) を一次資料とする。

## フィードバック注入機能（詳細）

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

ステップが正常終了した時点で、注入されたフィードバックファイルは `FEEDBACKS/done/` に `shutil.move` される。`FEEDBACKS/done/` 配下は `load_feedbacks()` の非再帰 glob の対象外のため、次回以降のロードでは拾われない（done/ のファイルを再利用したい場合は `FEEDBACKS/` に手動で戻す）。

### 異常終了時のふるまい

ステップが非ゼロ exit / 例外 / Ctrl-C で終了した場合、`consume_feedbacks()` は呼ばれず、FEEDBACK は `FEEDBACKS/` 直下に残る。次回 run で再度読み込まれるため、retry 時に同じフィードバックが再適用される挙動になる（仕様）。

## 完了通知（詳細）

通知は workflow 全体の終了時に **1 回のみ** 発火する（ver15.4〜）。`--max-loops N` で複数ループ回しても途中では発火しない。成功 / 失敗 / 中断（Ctrl+C / SIGTERM）のいずれの経路でも `main()` の `finally` 経路に収束する。本文フォーマット:

| 結果 | タイトル | 本文例 |
|---|---|---|
| success | `Workflow Complete` | `claude_loop / 1 loop / 6 steps / 14m 32s` |
| failed  | `Workflow Failed`   | `failed at imple_plan (exit 1) / claude_loop / 1 loop / 3 steps / 4m 11s` |
| interrupted | `Workflow Interrupted` | `interrupted (SIGINT) at write_current / claude_loop / 1 loop / 5 steps / 7m 02s` |

- `--no-notify` は成功/失敗/中断いずれの経路でも通知を抑止する
- `--dry-run` 時も通知は発火しない
- `--workflow auto` の場合、workflow ラベルは `auto(full)` / `auto(quick)` の形で phase2 種別を含む
- Windows では `scenario='reminder'` + dismiss アクション構成で Action Center に残る挙動を狙う。OS が拒否した場合は `duration='long'` → beep + console に段階的フォールバック

## ログフォーマット（詳細）

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
Model: {model}, Effort: {effort}, SystemPrompt: set, AppendSystemPrompt: set, Continue: {bool}, Session: {uuid8}
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
Last session (full): {full_uuid}     ← 末尾ステップの完全な session ID
=====================================
```

descriptor 行（Model / Effort / SystemPrompt / AppendSystemPrompt / Continue / Session）の表示ルール:

- `Model:` / `Effort:` は値が未指定の側を省略、すべて未指定なら descriptor 全体が `Session:` のみになる
- `SystemPrompt: set` / `AppendSystemPrompt: set` は step または defaults に該当キーが指定された場合のみ表示（値そのものは表示しない。ログ肥大化防止のため）
- `Continue:` は `continue: true` を YAML で明示したステップにのみ表示。実際に継続が無効化された場合（`--start > 1` やループ境界）は `Continue: False` と表示される
- **既知の非対称性**: `continue: false` を明示したステップと `continue` を省略したステップは descriptor 上区別できない（どちらも `Continue:` 行が出ない）。トラブルシュート時は YAML を併読すること
- `Session:` は常に表示（先頭 8 文字）。完全な UUID はワークフローフッターの `Last session (full):` に出力されるので、`claude -r <uuid>` で手動再開する場合はそちらを参照

コマンドログは `shlex.join(command)` で出力されるため、スペース・特殊文字を含む引数は自動でシェルクォートされる。

### ログの読み方（トラブルシュート）

**失敗したステップを特定する**: `--- end (exit: {code}, ...)` 行で exit code が非 0 のステップを探す。その直前の stdout/stderr 出力に原因が記録されている。

**同じエラーが複数ステップで繰り返される場合**: `continue: true` のステップは前ステップのセッションを引き継ぐため、前ステップで混乱が生じていると後続ステップでも誤った判断が連鎖する（セッション汚染）。この場合は `--start N` で問題ステップから単独再実行して切り分ける。

**手動で特定ステップを再実行する**:

```bash
# ワークフローフッターの "Last session (full):" UUID を使って続きから実行
claude -r <full-uuid>

# または --start でステップ番号を指定して再実行（auto モード以外）
python scripts/claude_loop.py --workflow full --start 3
```

**ログファイルの管理**: `logs/workflow/` は `.gitignore` で除外済みのため手動削除して問題ない。蓄積が多い場合は `logs/workflow/` ごと削除するか、古い `.log` ファイルを選択削除する。ローテーション自動化は未実装。

## 拡張ガイド

scripts 系を編集・追加するときに毎回守るべき stable な規約は `.claude/rules/scripts.md` に集約。本節は「拡張時の手順」に関する詳細のみを扱う。

- **新しい SKILL を追加する場合**: `claude_loop.yaml` または `claude_loop_quick.yaml` の `steps:` に `{ name, prompt, model?, effort?, system_prompt?, append_system_prompt?, args?, continue? }` を追記する
- **Python コードを拡張する場合**: 触る関心事に対応する `claude_loop_lib/` 配下のモジュールに手を入れる。責務分担はファイル一覧を参照
- **新規 CLI オプションを追加する場合**（rules §3）: `claude_loop.py` の `parse_args()` と、追加した値を渡す先（多くは `claude_loop_lib/commands.py` の `build_command`）の両方を更新する必要がある
- **フィードバックのスキーマ拡張**（rules §4）: `claude_loop_lib/feedbacks.py` の `parse_feedback_frontmatter` に追加フィールドのパースを足す
