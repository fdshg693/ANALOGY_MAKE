# ver13.0 MEMO — 実装メモ

IMPLEMENT.md に対する実装結果の記録。

## 計画からの乖離

### IMPLEMENT.md §1-2 `claude_loop.py` L100–104 の `--auto` argparse 削除

計画では argparse 標準の `unrecognized arguments` エラーで済ませる方針だったが、argparse は既定で **前方一致による省略（allow_abbrev=True）** を有効にしているため、`--auto` が `--auto-commit-before` に誤マッチする可能性があった。そのまま `--auto-commit-before` の値に吸収される挙動は破壊的変更の「明示的に拒否する」意図に反する。

**対応**: `argparse.ArgumentParser(allow_abbrev=False)` を `parse_args()` で明示。これにより `--auto` を渡すと確実に `unrecognized arguments: --auto` で落ちる。

**影響**: `--auto-commit-before` のような長いフラグは従来通り動作するが、今後ユーザーが短縮形（例: `--auto-commit`）を書いても受理されなくなる。運用上の影響は軽微（既存ユーザーは完全名で書くのが通常）。

### commands.py `--append-system-prompt` 常時注入に伴うテストの副作用

IMPLEMENT.md §1-3 で挙げていた test_commands.py の修正に加え、以下のテストも `--append-system-prompt` が minimal ケースで含まれない前提に依存しており、修正が必要だった:

- `TestBuildCommandWithFeedbacks.test_no_feedbacks`: `assert "--append-system-prompt" not in cmd` → unattended prompt 注入下では常に含まれるため、「feedback セクションだけが無い」を確認する assertion に反転
- `TestBuildCommandWithAppendSystemPrompt` の複数テスト: `assert self._asp_value(cmd) == "my-append"` のような **等号比較** を **含有比較** (`"my-append" in value`) に変更。unattended prompt と step append の連結が先頭に入るため等号比較では落ちる
- `TestBuildCommandWithAppendSystemPrompt.test_step_overrides_defaults_append`: `"A"` / `"B"` 値が unattended prompt の "A"（`AskUserQuestion`）と誤マッチして失敗。ユニークな識別子 (`STEP_VAL` / `DEFAULT_VAL`) にリネーム
- `TestOverrideInheritanceMatrix` の 4 テスト: `append_system_prompt` キーだけは「flag が常に存在する・値は unattended prompt を prefix として含む」挙動に変わるため、専用の assertion ヘルパ `_assert_contains()` を導入して key ごとに比較ロジックを切替え

## リスク検証結果（IMPLEMENT.md §6 対応）

### 6-1. `--auto` / `mode` / `auto_args` 撤去の破壊的影響 → **検証済み**

- `python scripts/claude_loop.py --auto` を実行したところ、`claude_loop.py: error: unrecognized arguments: --auto` で即座にエラー終了することを確認
- 旧 YAML (`mode: auto: true` や `command.auto_args`) を投入した場合の validation 拒否は `TestValidateRejectsLegacyKeys` に 4 ケース追加（mode, auto_args, unknown-toplevel, unknown-command）。全テスト成功
- argparse の省略前方一致対策として `allow_abbrev=False` を追加（上記「計画からの乖離」参照）

### 6-2. YAML schema 変更の validation タイミング → **検証済み**

- `workflow.py:resolve_command_config()`（runtime 側の保険）と `validation.py:_validate_command_section()` / `_validate_toplevel_keys()`（起動前 frontline）の **二重網** で拒否する実装にした
- validation 側では `command.auto_args` 専用エラー、`mode:` 専用エラー、汎用 unknown-key エラーをそれぞれ別経路で出す
- `test_validation.py::TestValidateRejectsLegacyKeys` で 4 経路（mode / command.auto_args / 未知 top-level / 未知 command キー）の拒否を検証

### 6-3. `command.args` に `--disallowedTools "AskUserQuestion"` を常時含める副作用 → **検証不要**

- 本プロジェクトの 3 YAML はいずれも `mode.auto: true` 固定だったため、旧動作下でも常に `--disallowedTools` が付加されていた。挙動後退ではないため検証不要

### 6-4. FEEDBACKS 異常終了テストの単体化難度 → **検証先送り**

- 本バージョンでは README / USAGE / docstring 側の不変条件明文化のみで担保（IMPLEMENT.md §2-2 の方針通り）
- integration テスト拡張は `ISSUES/util/medium/feedback-abnormal-exit-integration-test.md` に ISSUE として独立化。本番での兆候・対応方針を記載済み
- 本番発生時の兆候: ステップ失敗時に FEEDBACK が消えてしまった場合、再実行しても適用されない → 調査時は `git log` で `FEEDBACKS/done/` への移動時刻を確認

### 6-5. SKILL 編集の `claude_sync` 手順ミス → **検証済み**

- 作業手順: `python scripts/claude_sync.py export` → `.claude_sync/skills/{issue_plan,split_plan,retrospective}/SKILL.md` を Edit → `python scripts/claude_sync.py import`
- import 後に `grep -n "REQUESTS/AI" .claude/skills/*/SKILL.md` で残存ゼロを確認
- import 前の `.claude_sync/` 新規化は既存ディレクトリを上書き削除する挙動なので、ローカル編集の消失リスクはあったが本作業では未コミットの .claude/ 内編集はゼロだったため問題なし

### 6-6. REQUESTS ディレクトリ削除と並行作業の衝突 → **検証済み**

- 削除直前に `ls REQUESTS/AI/ REQUESTS/HUMAN/` を実行し、両者とも空であることを再確認してから `rmdir` で削除
- `REQUESTS/` 本体も空になり削除済

### 6-7. MASTER_PLAN / PHASE7.0.md の進捗表更新漏れ → **wrap_up / retrospective に委任**

- 本ステップ（imple_plan）のスコープではないため未着手
- `docs/util/MASTER_PLAN/PHASE7.0.md` L11-13 の §3 / §4 / §5 の「未着手」を「実装済」に更新する作業は `/wrap_up` または `/retrospective` SKILL に任せる
- 忘れを防ぐため本 MEMO.md に明示的に記録した

### 6-8. ver12.0 RETROSPECTIVE §2-2-b の cwd 依存教訓 → **検証済み**

- `python -m unittest discover -s scripts/tests -t .` を複数回実行し、231 tests すべて OK
- 本バージョンで YAML 構造が変わり `TestValidateStartupExistingYamls` が実際の新 YAML をロードするため、cwd 依存があれば顕在化する。問題なく通過

## 動作確認実施記録

- `python -m unittest discover -s scripts/tests -t .` → 231 tests OK
- `python scripts/claude_loop.py --dry-run --workflow full` → 6 ステップ分のコマンドが正しく構築され、unattended system prompt が全ステップに注入されることを確認
- `python scripts/claude_loop.py --auto` → argparse で unrecognized arguments エラー
- `npx nuxi typecheck` → vue-tsc の npx 解決エラー（CLAUDE.md 既知警告。Python 変更のみのため本バージョンの変更とは無関係）

## 更新候補ドキュメント

- `docs/util/MASTER_PLAN/PHASE7.0.md`: §3 / §4 / §5 のステータスを「実装済」に更新（/wrap_up or /retrospective で対応）
- `docs/util/ver12.0/CURRENT.md` / `CURRENT_scripts.md`: ver13.0 の CURRENT.md 作成時に `mode:` セクション・`command.auto_args`・`REQUESTS/AI` `REQUESTS/HUMAN` の記述を削除・置換する
