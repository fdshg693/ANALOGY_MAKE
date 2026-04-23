# ver13.0 IMPLEMENT — PHASE7.0 §3+§4+§5 実装計画

`docs/util/ver13.0/ROUGH_PLAN.md` を前提とする。§3（`--auto` / `mode` / `auto_args` 撤去）、§4（FEEDBACKS 運用ルール明文化）、§5（`REQUESTS/AI` `REQUESTS/HUMAN` 廃止と ISSUES 統合）を一括で実装する。

## 0. 前提条件 / 既知の制約

- `.claude/` 配下のファイルは CLI `-p` モードで直接編集できないため、`python scripts/claude_sync.py export` → `.claude_sync/` で編集 → `python scripts/claude_sync.py import` の手順を使う（`.claude/rules/claude_edit.md`）。
- 本バージョンの変更対象には `.claude/skills/issue_plan/SKILL.md`・`.claude/skills/split_plan/SKILL.md`・`.claude/skills/retrospective/SKILL.md` が含まれるため、実装ステップで `claude_sync` 手順の経由を明示する。
- `scripts/tests/` は `python -m unittest discover scripts/tests` で実行する想定（既存運用に合わせる）。
- `REQUESTS/AI/` `REQUESTS/HUMAN/` は現状空（`ls` 確認済）。ファイル移行は発生しない。

## 1. §3: `--auto` / `mode` / `auto_args` の撤去

### 1-1. 仕様確定

- CLI `--auto` を撤去する。今後 `--auto` は argparse で `unrecognized argument` になり、ユーザーは自然にエラーになる。ただし「移行案内」を残すため、`argparse.ArgumentParser` の `error` オーバーライドは行わず、README / USAGE に「`--auto` は廃止された。通常起動がその挙動を内包する」旨を明記する方針を取る（argparse 標準のエラー文言で十分識別可能なため、追加ハンドリングは過剰設計と判断）。
- YAML 側の `mode:` キーと `command.auto_args` キーは削除する。**旧キー検出時は明示的な `SystemExit` を発生させる**（PHASE7.0 §3-1 の「黙って無視しない」方針に従う）。検出箇所は後述の validation。
- `command.args` に旧 `auto_args` の内容（`--disallowedTools "AskUserQuestion"` と `--append-system-prompt ...`）を統合する。ただし `--append-system-prompt` は `build_command()` 側で組み立てる `system_prompts` へ寄せて YAML からは外し、`USAGE.md` 現行の「独立 2 引数になる既存挙動」の不整合（USAGE.md:122 記載）を本バージョンで解消する。
- 新 YAML 構成:
  - `command.args`: `--dangerously-skip-permissions` と `--disallowedTools "AskUserQuestion"` のみ（全モード共通）
  - `command.auto_args`: 削除
  - `--append-system-prompt` 相当の文言は `commands.py` の `build_command()` が既に組み立てる `system_prompts` に寄せる（§5 で文言自体を書き換え）

### 1-2. 変更詳細（ファイル単位）

#### `scripts/claude_loop.py`

- **削除**: L100–104 の `parser.add_argument("--auto", ...)` ブロック。
- **変更**: L249–253 付近
  - 現: `executable, prompt_flag, common_args, auto_args = resolve_command_config(config)` / `auto_mode = resolve_mode(config, args.auto)` / `if auto_mode: common_args = common_args + auto_args`
  - 新: `executable, prompt_flag, common_args = resolve_command_config(config)` のみ。`auto_mode` / `auto_args` の計算と結合はすべて削除。
- **変更**: L267–272 付近の `_run_steps(..., auto_mode, ...)` 呼び出しから `auto_mode` 引数を削除。
- **変更**: `_run_steps` 定義（L394–408）のシグネチャから `auto_mode: bool = False` を除去（L404）。
- **変更**: `_run_steps` 内の `build_command()` 呼び出し（L478–482、`auto_mode` を **positional** 引数として渡している）から `auto_mode` を除去。positional 位置ずれに注意。
- `args.auto` の参照箇所（`claude_loop.py` 全体）が L251 のみであることを grep で再確認し、他にあれば同様に除去。本バージョンの実装確認手順でも `grep -n "auto_mode\|args\.auto" scripts/claude_loop.py` を走らせ、残存ゼロを確認する。

#### `scripts/claude_loop_lib/workflow.py`（最優先で着手）

- **削除**: L182–188 `resolve_mode()` 関数定義。**関数自体を削除**する（call site だけ直しても後続で呼び直されるリスクが残るため、シンボル自体を消す）。
- **変更**: L164–179 `resolve_command_config()`
  - 戻り値を 4-tuple → 3-tuple に変更: `(executable, prompt_flag, common_args)`
  - L172 `auto_args = normalize_cli_args(...)` を削除
  - `command_config.get("auto_args")` が存在する場合（validation で拾えない経路のダブルチェック用）、`SystemExit("'command.auto_args' is removed in ver13.0. Merge values into 'command.args' instead.")` を発生させる

#### `scripts/claude_loop_lib/validation.py`

- **新規追加**: `_validate_single_yaml()`（L111–139）に「トップレベル unknown-key」検査を追加。現行は top-level の unknown key を一切見ていないため、新規に `ALLOWED_TOPLEVEL_KEYS = frozenset({"command", "defaults", "steps"})` を定義し、`data.keys() - ALLOWED_TOPLEVEL_KEYS` を検出する。`mode` が含まれていた場合のみ、汎用の unknown-key エラーではなく **専用のエラー** `"'mode:' is removed in ver13.0. Auto mode is now the default. Remove the 'mode:' section from YAML."` を出す。
- **新規追加**: `_validate_command_section()`（L142–171）に「`command` 配下の unknown-key」検査を追加。`ALLOWED_COMMAND_KEYS = frozenset({"executable", "prompt_flag", "args"})` を定義し、`command_config.keys() - ALLOWED_COMMAND_KEYS` を検出。`auto_args` が含まれていた場合は専用エラー `"'command.auto_args' is removed in ver13.0. Merge its values into 'command.args'."` を出す。
- 以上 2 つの検査により、起動前 validation フェーズで旧 YAML 形式が確実に拒否される。`workflow.py` 側の保険的な `SystemExit` 分岐は validation をすり抜けた場合の二重網として残す。

#### `scripts/claude_loop_lib/commands.py`

- **変更**: `build_command()` シグネチャから `auto_mode: bool = False` パラメータを削除。
- **変更**: L38–42 の `if auto_mode:` ブロックを **無条件化**（常に append）。ただし文言は §5 で書き換える（REQUESTS/AI 参照削除）。具体的には:
  - 旧: `"Workflow execution mode: AUTO (unattended). Do not use AskUserQuestion. Write requests to REQUESTS/AI/ instead."`
  - 新: `"Workflow execution mode: unattended. Do not use AskUserQuestion. If human input is required, stop and write an ISSUE under ISSUES/{category}/{priority}/ with frontmatter `status: need_human_action` / `assigned: human`."`
  - この system prompt が常時注入されることが前提になるため、旧 YAML の同等文言（`--append-system-prompt "you cannot ask questions..."`）は YAML から除去し、`build_command()` 側に一本化する。
- **副作用**: 現行 `test_commands.py` は「`auto_mode=False` / `log_file_path=None` / no feedbacks の最小ケースで `--append-system-prompt` が **含まれない**」ことをアサートするテストが複数存在する（`TestBuildCommandWithLogFilePath.test_without_log_file_path` L18–21 / `test_empty_string_log_file_path_does_not_add_args` L46–49）。本変更により **最小ケースでも常に `--append-system-prompt` が含まれる** ようになるため、これらのテストは意味が変わる:
  - `test_without_log_file_path`: 「log_file_path=None でも unattended prompt が含まれる」にアサーションを反転
  - `test_empty_string_log_file_path_does_not_add_args`: 同上。`log_file_path=""` でログ行は含まれないが unattended prompt は含まれることをアサート
  - この挙動変更（＝通常の非対話起動が常に unattended 挙動）は PHASE7.0 §3-2 完了条件「実行者が『自動実行にするための別モード』を意識しなくてよい」に合致する意図的な変更。

#### `scripts/claude_loop.yaml` / `scripts/claude_loop_quick.yaml` / `scripts/claude_loop_issue_plan.yaml`

- **削除**: L7–8 `mode: auto: true`
- **削除**: L15–32 `auto_args` ブロック全体
- **変更**: `command.args` に `--disallowedTools "AskUserQuestion"` を追加（`--dangerously-skip-permissions` の下）
- **変更**: 冒頭 NOTE コメント L1–3
  - 現: "NOTE: --workflow auto uses steps[1:] of this file. steps[0] must be /issue_plan.  The `command` / `mode` / `defaults` sections must stay in sync with ..."
  - 新: "NOTE: --workflow auto uses steps[1:] of this file. steps[0] must be /issue_plan.  The `command` / `defaults` sections must stay in sync with ..."
  - 「`--workflow auto`」への言及自体は `--auto` とは別概念なので **残す**（ROUGH_PLAN §3 対象外明記）
- 旧 YAML の長大な append_system_prompt 文言（`.claude/` 編集手順ガイド）は、`.claude/rules/claude_edit.md` に同内容が既に存在するため YAML からは除去する（既存ルールファイルで代替可能）。

### 1-3. 既存テストへの影響

- `scripts/tests/test_workflow.py`
  - `TestResolveMode`（L23–34）: **削除**（対象関数が消える）
  - `TestResolveCommandConfigAutoArgs`（L36–47）: **削除**
  - 代わりに `TestResolveCommandConfigRejectsAutoArgs`（新規）: `{"command": {"auto_args": [...]}}` を渡すと `SystemExit` になることを検証
  - 新規 `TestRejectsModeKey`: `{"mode": {"auto": True}}` を渡すと `SystemExit` になることを検証（追加先は `test_validation.py` が存在すればそちら）
  - `from claude_loop_lib.workflow import resolve_mode` の import を削除

- `scripts/tests/test_commands.py`
  - `TestBuildCommandWithMode`（L52–72）: **削除**（`auto_mode` 引数消滅）
  - `TestBuildCommandWithAppendSystemPrompt.test_appends_after_auto_mode`（L267–275）: **削除**（`auto_mode=True` 引数消滅）
  - `TestBuildCommandWithAppendSystemPrompt.test_full_combination_order`（L287–299）: `auto_mode=True` 引数を削除し、順序アサートは `log_pos < auto_pos < fb_pos < append_pos` のまま（unattended prompt が常時注入されるため `auto_pos` は依然として取得可能）。`_asp_value` の順序アサート内の `"AUTO (unattended)"` は文言変更に合わせて `"unattended"` にマッチするよう更新
  - `TestBuildCommandWithLogFilePath.test_without_log_file_path`（L18–21）: アサーション反転（`"--append-system-prompt" in cmd` へ）
  - `TestBuildCommandWithLogFilePath.test_empty_string_log_file_path_does_not_add_args`（L46–49）: 同上。テスト名も意図に合わせて `test_empty_string_log_file_path_omits_log_line_but_still_injects_unattended` 等に改名
  - `build_command()` が常時 unattended system prompt を注入することを確認する新テスト `TestBuildCommandAlwaysInjectsUnattendedPrompt` を追加（minimal ケースで `"unattended"` が含まれ、`"AUTO"` 文字列（旧）が含まれないことを確認）

- `scripts/tests/test_claude_loop_cli.py`
  - `TestParseArgsAutoOption`（L49–63）: **削除**
  - 新規 `TestRejectsAutoFlag`: `_parse(["--auto"])` が `SystemExit` を発生させることを検証（argparse 標準挙動の確認）

### 1-4. docs 更新

- `scripts/README.md`
  - L74 / L77 / L80–87 / L114 周辺: `--auto` 説明セクションを削除し、「通常起動 (`python scripts/claude_loop.py`) が常に auto 挙動を内包する」旨に書き換え
- `scripts/USAGE.md`
  - L41–42, L51–52, L59, L82–83, L122: `--auto` / `mode:` / `auto_args` 説明を削除し、`command.args` のみの構成に書き換え

## 2. §4: FEEDBACKS 運用ルール明文化

### 2-1. 現状把握からの結論

- `feedbacks.py:34` は `feedbacks_dir.glob("*.md")` を使用し、**既に `FEEDBACKS/done/` は自動読込対象外**（再帰しない glob）。§4「`FEEDBACKS/done/` 自動再読込の抑止」はコード変更不要。
- `claude_loop.py:573` は step が `exit_code == 0` のときのみ `consume_feedbacks()` を呼び出す。異常終了（非ゼロ exit / 例外 / Ctrl-C）時は FEEDBACK は `FEEDBACKS/` に残る。§4「異常終了時の移動有無の仕様確定」は「**異常終了時は移動しない（retry のため温存）**」で確定し、コードは現状維持・ドキュメント追記のみ。

### 2-2. 変更詳細

- **追加**: `scripts/claude_loop_lib/feedbacks.py` の `load_feedbacks()` / `consume_feedbacks()` docstring に下記を明記
  - `load_feedbacks`: "Non-recursive glob — `FEEDBACKS/done/` は対象外"
  - `consume_feedbacks`: "caller が step 正常終了時のみ呼び出すこと。異常終了時は呼び出されず、次回 run で再消費される"
- **追加**: `scripts/USAGE.md` L180 周辺に「異常終了時のふるまい」小節を新設
  - "step が非ゼロ exit / 例外で終了した場合、consume は実行されず FEEDBACK は `FEEDBACKS/` 直下に残る。次回 run で再度読込まれる"
- **追加テスト方針（本バージョンでは行わない）**: 「step 失敗時に `consume_feedbacks` が呼ばれない」は `claude_loop.py:570` 付近の制御フロー不変条件であり、単体テスト化には subprocess / TeeWriter / 一時 cwd の組立が必要で ver12.0 RETROSPECTIVE §2-2-b の cwd 依存問題を再発させやすい。したがって **本バージョンでは追加テストを行わず、README / USAGE / docstring での不変条件明文化のみで担保する**。integration テスト拡張は `MEMO.md` に「次バージョン以降で検討」として明記する。

### 2-3. docs 更新

- `scripts/README.md` L114: 既に「ステップ正常終了後に `FEEDBACKS/done/` へ移動される」と記載あり。加えて「異常終了時は移動しない（retry のため温存）」を追記。
- `scripts/USAGE.md` L180 付近: 同上。

## 3. §5: REQUESTS → ISSUES 統合

### 3-1. 削除対象

- `REQUESTS/AI/` ディレクトリ（空）: `git rm -r REQUESTS/AI` で削除
- `REQUESTS/HUMAN/` ディレクトリ（空）: `git rm -r REQUESTS/HUMAN` で削除
- `REQUESTS/` 自体も空になるため削除する（Git 管理からは自動で外れる）

### 3-2. docs / SKILL 置換

- `CLAUDE.md` L35: `- `REQUESTS/` — 機能リクエスト（分類別: `workflow/` 等）` の行を **削除**。同じ場所に「ISSUES/` — 課題管理」の行は既にあるため追記は不要。
- `ISSUES/README.md`: 「REQUESTS からの移行経緯」セクション（1 段落）を追加。「これまで `REQUESTS/AI/` `REQUESTS/HUMAN/` で扱っていた『人間への依頼』は本ディレクトリの ISSUE に集約する。AI 向けは `assigned: ai`、人間対応要は `assigned: human` / `status: need_human_action` を使う」。
- `.claude/skills/issue_plan/SKILL.md`: `REQUESTS/AI/ に方向性確認のリクエストを書き出した上で、暫定的に既存 ISSUES 消化に倒す` という記述を `ISSUES/{カテゴリ}/medium/ に "direction-check-ver{X.Y}.md" を作成（frontmatter: status=need_human_action, assigned=human）し、暫定的に既存 ISSUES 消化に倒す` に置換。実装時は `grep -n "REQUESTS/AI" .claude/skills/issue_plan/SKILL.md` で現在位置を再確認する（行番号は時間経過で動く可能性あり）。
- `.claude/skills/split_plan/SKILL.md`: `REQUESTS/AI/ に整合性エラーとして記録し終了する` という記述を `logs/workflow/ にエラー記録しつつ、ISSUES/{カテゴリ}/high/ に "split-plan-consistency-error-ver{X.Y}.md" を作成（frontmatter: status=need_human_action, assigned=human）して終了する` に置換。実装時は grep で位置を再確認。
- `.claude/skills/retrospective/SKILL.md`: `REQUESTS/AI/ の整理` セクション全体を **削除**（REQUESTS 廃止により不要）。実装時は grep で位置を再確認。

### 3-3. scripts/commands.py の system prompt

- §1-2 で既に書き換え済（`REQUESTS/AI/` 言及を ISSUE 生成指示に置換）。YAML からも同文言を除去済。

### 3-4. 検索漏れ防止

- 実装完了直前に `grep -rn "REQUESTS/AI\|REQUESTS/HUMAN" --exclude-dir={.git,node_modules,.venv,data,.nuxt,.output,dist}` を走らせ、残存が docs 系（`docs/util/verX.Y/*.md` などの履歴）のみであることを確認。履歴系は書き換えない（過去バージョンの事実記録として残す）。
- `grep -rn "--auto\b\|mode:\s*$\|auto_args"` も同様に残存確認（CLI `--auto-commit-before` や PowerShell `--%` などと誤ヒットしないよう `\b` / 文脈を絞る）。

## 4. 実装順序

コード変更は **callee（下流ライブラリ）から caller（上流スクリプト）へ** 進める。`workflow.py:resolve_command_config()` の戻り値 arity 変更を先にすると、`claude_loop.py` の unpacking が即 `ValueError` になるため、unpacking 側（caller）を先に直す必要がある。したがって正しい順序は **caller → callee** ではなく、**引数の型変更と caller の両方を同じコミットで整合させる** ことが安全。以下は作業単位ごとの順序:

1. **テスト先行**: §3 の新規テスト（旧 YAML 拒否、`--auto` 拒否など）を先に追加し、赤を確認
2. **コード変更（§3）を一続きで適用**:
   a. `workflow.py`: `resolve_mode()` 削除、`resolve_command_config()` の 3-tuple 化、`auto_args` 保険 `SystemExit` 追加
   b. `claude_loop.py`: L100–104 `--auto` argparse 削除、L249–253 unpacking 修正、`_run_steps` L394–408 と L478 の `auto_mode` 除去、L267–272 呼び出し修正
   c. `commands.py`: `build_command()` の `auto_mode` 引数削除と unattended prompt 無条件化（文言は §5 版）
   d. `validation.py`: top-level unknown-key 検査と `command` 配下 unknown-key 検査を追加（`mode:` / `command.auto_args` の専用エラー）
   e. この 4 ファイルは **1 コミット** でまとめて適用し、step 間の中間状態で `ImportError` / `ValueError` が発生しない状態を保つ
3. **YAML 更新**: 3 本の YAML を同時更新（構造を同期）。NOTE コメントから `mode` 参照も除去
4. **旧テスト整理**: `TestResolveMode` / `TestResolveCommandConfigAutoArgs` / `TestBuildCommandWithMode` / `TestParseArgsAutoOption` / `TestBuildCommandWithAppendSystemPrompt.test_appends_after_auto_mode` / `TestBuildCommandWithLogFilePath.test_without_log_file_path` / `test_empty_string_log_file_path_does_not_add_args` / `test_full_combination_order`（`auto_mode` 引数箇所）の削除・反転・リネーム
5. **FEEDBACKS docstring / USAGE 追記**: §4 の文書更新
6. **REQUESTS 削除**: `ls REQUESTS/AI/ REQUESTS/HUMAN/` で空を最終確認した上で `git rm -r REQUESTS/`（§5）
7. **SKILL 更新**: `python scripts/claude_sync.py export` → `.claude_sync/skills/{issue_plan,split_plan,retrospective}/SKILL.md` を `grep` で位置確認して編集 → `python scripts/claude_sync.py import`（§5）
8. **docs 更新**: `CLAUDE.md`・`ISSUES/README.md`・`scripts/README.md`・`scripts/USAGE.md`（§3 / §4 / §5 まとめて）
9. **テスト全実行**: `python -m unittest discover scripts/tests`
10. **grep 最終確認**: 参照漏れが docs 系（`docs/util/ver*`）のみに限られていることを確認

## 5. 実装確認コマンド

- Python テスト: `python -m unittest discover scripts/tests`
- YAML ロード smoke: `python scripts/claude_loop.py --dry-run --workflow full`（および `quick` / `auto`）
- 旧 YAML 拒否確認: 一時的に `mode: auto: true` を差し戻して `--dry-run` で `SystemExit` になることを手動確認（コミット前に元に戻す）
- grep: `grep -rn "REQUESTS/AI\|REQUESTS/HUMAN\|--auto\b\|auto_args\|resolve_mode" --exclude-dir={.git,.venv,node_modules,data,docs,.nuxt,.output,dist}`

## 6. リスク・不確実性

### 6-1. `--auto` / `mode` / `auto_args` 撤去の破壊的影響

- **リスク**: 利用者のローカル wrapper / メモ / CI で `--auto` を渡している場合、argparse の `unrecognized argument` エラーで即座に落ちる。
- **緩和**: README / USAGE に大きく「`--auto` は ver13.0 で廃止。通常起動がその挙動を内包する」と記載。argparse エラー文言に追加の移行案内を載せることも検討したが、標準の `error: unrecognized arguments: --auto` で十分識別可能と判断し、追加ハンドリングは行わない。
- **残リスク**: CI ログでの初見エラーは不親切。MEMO に「利用者から混乱報告があれば argparse.error オーバーライドで移行案内を追加」と記録。

### 6-2. YAML schema 変更の validation タイミング

- **リスク**: `validation.py` のエントリポイントが複数あり、一部経路で旧 YAML 拒否がすり抜ける可能性。
- **緩和**: 拒否ロジックは `load_workflow()` か `resolve_command_config()` の最上流一箇所に置く。`validation.py` は補助として `ALLOWED_*` セットによる unknown key 検出も残す（二重網）。
- **残リスク**: `resolve_command_config()` が呼ばれない経路が存在する場合、拒否がすり抜ける。全呼び出し経路を grep で確認する。

### 6-3. `command.args` に `--disallowedTools "AskUserQuestion"` を常時含める副作用

- **リスク**: 対話的デバッグ用途で一時的に `AskUserQuestion` を許可したくなるケースが出た場合、YAML 編集が必要になる。
- **緩和**: 元々 `mode.auto: true` 固定だったため現状と挙動は同等。対話的用途は `claude` コマンド直叩きで代替可能。
- **残リスク**: なし（挙動後退ではない）。

### 6-4. FEEDBACKS 異常終了テストの単体化難度

- **リスク**: 「step 失敗時に `consume_feedbacks` が呼ばれない」は `claude_loop.py:570` 付近の分岐挙動であり、単体テスト化には subprocess / TeeWriter 等の依存が絡む。
- **緩和**: まずは README / USAGE / docstring に不変条件を明記して運用で担保する。integration テストの拡張は `MEMO.md` に次バージョン候補として記録。
- **残リスク**: コード側で invariant が破れても CI で気付かない。ただし本バージョンでは当該分岐に手を入れないため影響は低。

### 6-5. SKILL 編集の `claude_sync` 手順ミス

- **リスク**: `.claude/skills/*/SKILL.md` を直接編集しようとして CLI セキュリティで弾かれる。
- **緩和**: 実装順序 (§4) で `claude_sync export → edit → import` を明示。実装時は `claude_sync` 実行ログを `MEMO.md` に残す。
- **残リスク**: `claude_sync import` の上書きで既存ローカル編集を失う可能性。`import` 前に `.claude_sync/` の git status を確認する手順を徹底。

### 6-6. REQUESTS ディレクトリ削除と並行作業の衝突

- **リスク**: 別ブランチ / FEEDBACK 等で `REQUESTS/AI/*.md` が新規作成されている場合、`git rm -r` で消してしまう。
- **緩和**: 削除直前に `ls REQUESTS/AI/ REQUESTS/HUMAN/` で空を再確認し、空でなければ中身を Review してから削除判断。
- **残リスク**: 低（シングルブランチ運用）。

### 6-7. MASTER_PLAN / PHASE7.0.md の進捗表更新漏れ

- **リスク**: PHASE7.0.md L11–13 の §3 / §4 / §5 の「未着手」ステータスを「実装済」に更新しそびれる。
- **緩和**: `/retrospective` SKILL で MASTER_PLAN 進捗同期は通常行われているかを要確認。行われていない場合、本バージョンの `wrap_up` or `retrospective` ステップで PHASE7.0.md の表を更新する TODO を明示する。
- **残リスク**: 後続バージョンで §3–§5 を再掘削してしまう可能性。wrap_up チェックリストで拾う。

### 6-8. ver12.0 RETROSPECTIVE §2-2-b の cwd 依存教訓

- **リスク**: 既存 integration テストが cwd 依存の assertion を持ち、YAML 変更で顕在化する。
- **緩和**: テスト変更後に `scripts/tests/` 配下全件を実行して確認。既存 `TestResolveMode` 等の削除のみで済む想定。
