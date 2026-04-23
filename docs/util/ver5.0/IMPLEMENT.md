# ver5.0 IMPLEMENT: ワークフローのステップ間セッション継続

ROUGH_PLAN.md で確定したスコープに対する実装計画。

## 全体方針

- **セッション ID 取得方式**: **(a) `--session-id <uuid>` 事前発行方式を採用**（PHASE4.0 L64-75 の 3 候補から選択）。Claude Code CLI (2026-04-23 時点) は `--session-id <uuid>` と `-r <uuid>` の両方を公式にサポートしており（`claude --help` で確認済み）、`--output-format stream-json` のパースや `-c`（直近セッション）フォールバックは不要。UUID は Python の `uuid.uuid4()` で事前生成する。
- **状態保持**: `_run_steps` ループ内の局所変数 `previous_session_id: str | None` で保持する（ディスク永続化なし、PHASE4.0 の「やらないこと」に準拠）。
- **コマンド組み立て**: `build_command` に `session_id: str | None` と `resume: bool` の 2 引数を追加。`session_id` が `None` でない場合のみ付与し、`resume=True` なら `-r <session_id>`、`resume=False` なら `--session-id <session_id>` を出力する。
- **後方互換**: `defaults` 非設定 YAML と同様に、`continue` 非設定 YAML（ver4.x の YAML）も壊さない。`build_command` の新引数はデフォルト `None` / `False` で、既存呼び出しは書き換え不要。
- **`--dry-run` 時の挙動**: **実 UUID を `uuid.uuid4()` で毎回生成する**（ROUGH_PLAN L46 の「DRY_RUN_PLACEHOLDER 相当の識別子」案から意識的に変更）。理由: (1) コードパスを dry-run と本番で分岐させないことで分岐バグを排除、(2) dry-run の出力が本番実行時と実質同一になり、コマンドラインの事前確認という dry-run の本来目的に合致、(3) UUID 生成コストは無視できる。本変更は ROUGH_PLAN の仕様意図（「実際のセッションを作らない」）を満たしつつ、実装上のシンプルさを優先する判断。README.md にも「`--dry-run` でもランダム UUID が出力される（実セッションは作成されない）」と明記する。

## REFACTOR.md の要否

**作成不要**。事前リファクタリングは不要と判断する。理由: ver4.1 で `claude_loop_lib/` にモジュール分割済みであり、追加する責務は `commands.py` の `build_command`（引数追加 3 行・フラグ出力 4 行）と `workflow.py` の `get_steps`（`continue` キー取り込み 5 行程度）、`claude_loop.py` の `_run_steps`（セッション状態管理 20〜30 行）に局所化できる。各モジュールの責務は既に明確で、分割対象となる凝集度の低い関数は見当たらない。

## ROUGH_PLAN との差分補足

ROUGH_PLAN の影響範囲テーブル（L71）では `scripts/claude_loop_lib/logging_utils.py` を「変更」としていたが、**実装上は変更しない**方針に切り替える。理由: ログ出力の拡張（`Continue:` / `Session:` 行）は `_run_steps` 内の `descriptor_parts` リストに項目を追加するだけで完結し、`logging_utils.py` の関数（`print_step_header` / `format_duration` / `TeeWriter`）のシグネチャを変える必要がない。`logging_utils.py` は責務が「行単位の出力ユーティリティ」であり、ステップ固有のヘッダ組み立てを持ち込むと責務が肥大化する。

## 変更ファイル詳細

### 1. `scripts/claude_loop_lib/workflow.py` の変更

#### 1-1. `get_steps` に `continue` キーの取り込みを追加（L69-80 付近）

```python
# 既存: model / effort のループ
for key in ("model", "effort"):
    if key in raw_step and raw_step[key] is not None:
        value = raw_step[key]
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"steps[{index}].{key} must be a non-empty string.")
        step_entry[key] = value

# 追加: continue キー（bool）
if "continue" in raw_step and raw_step["continue"] is not None:
    value = raw_step["continue"]
    if not isinstance(value, bool):
        raise SystemExit(f"steps[{index}].continue must be a boolean.")
    step_entry["continue"] = value
```

- `continue` は Python 予約語なので dict キーとしてのみ使用。ステップ辞書からの取り出しは `step.get("continue", False)` で統一。
- 明示的に `False` が YAML に書かれた場合も取り込む（`key in raw_step` ベース判定）。`None` は「未指定」扱いで省略（`model` / `effort` と同じ方針）。

#### 1-2. 新規関数は追加しない

`defaults` に `continue: bool` を設けることは **やらない**（スコープ外）。`defaults.continue` は意味が不明瞭（全ステップが前ステップを継続すると初回ステップの扱いが曖昧）で、YAML を読む人を混乱させるため、ステップごとの明示指定のみに限定する。

### 2. `scripts/claude_loop_lib/commands.py` の変更

#### 2-1. `build_command` に引数追加

```python
def build_command(
    executable: str,
    prompt_flag: str,
    common_args: list[str],
    step: dict[str, Any],
    log_file_path: str | None = None,
    auto_mode: bool = False,
    feedbacks: list[str] | None = None,
    defaults: dict[str, str] | None = None,
    session_id: str | None = None,     # 追加
    resume: bool = False,              # 追加
) -> list[str]:
    cmd = [executable, prompt_flag, step["prompt"], *common_args, *step["args"]]
    defaults = defaults or {}
    for key, flag in (("model", "--model"), ("effort", "--effort")):
        value = step.get(key, defaults.get(key))
        if value is not None:
            cmd.extend([flag, value])

    # 追加: session 指定
    if session_id is not None:
        if resume:
            cmd.extend(["-r", session_id])
        else:
            cmd.extend(["--session-id", session_id])

    # 既存の system_prompts 処理（変更なし）
    ...
```

#### 2-2. フラグ順序

`--session-id` / `-r` は `--model` / `--effort` の**後**、`--append-system-prompt` の**前**に配置する。理由: モデル/effort は既に現方式で特定の位置に配置されており、ログの一貫性を保つ。`--append-system-prompt` は常に末尾が望ましい（長文で可読性を下げるため）。

### 3. `scripts/claude_loop.py` の `_run_steps` 改修

#### 3-1. シグネチャ変更

```python
def _run_steps(
    step_iter,
    steps: list[dict[str, Any]],
    executable: str,
    prompt_flag: str,
    common_args: list[str],
    cwd: Path,
    dry_run: bool,
    tee: TeeWriter | None,
    log_path: Path | None,
    auto_mode: bool = False,
    uncommitted_status: str | None = None,
    defaults: dict[str, str] | None = None,
    continue_disabled: bool = False,    # 追加（--start > 1 の場合に True）
) -> int:
```

#### 3-2. セッション状態管理ロジック

**`import uuid` の追加位置**: `scripts/claude_loop.py` の既存 import ブロック（L6-14 の標準ライブラリ群）に、`import time` の直後あたりに追加する。モジュールレベルで `import uuid` すれば `uuid` は `claude_loop` モジュールの属性となり、`@patch("claude_loop.uuid.uuid4")` で差し替えられる（標準的な Python モックパターン）。`claude_loop_lib/` 配下では `uuid` を直接使わない方針（セッション生成は `_run_steps` に集約）。

`_run_steps` のループ先頭（既存の `for step, absolute_index in step_iter:` の直前）で初期化:

```python
previous_session_id: str | None = None
continue_warned = False  # --start での警告を一度だけ出す
loop_boundary_warned = False  # 「前セッションがない状態での continue:true」警告を一度だけ出す
```

**警告の出力回数ポリシー**: `--start > 1` 警告と「ループ境界前セッション不在」警告はそれぞれ `_run_steps` 呼び出しあたり **最大 1 回** に統一する。複数ループで同じステップが該当しても重複表示しない。ログの冗長化を避けるため。

ループ内（step のフィードバック読み込み直後、`build_command` 呼び出し直前）に追加:

```python
requested_continue = bool(step.get("continue", False))
effective_continue = requested_continue

if requested_continue and continue_disabled:
    if not continue_warned:
        _out(
            "WARNING: --start > 1 detected; "
            "disabling 'continue: true' for all steps in this run."
        )
        continue_warned = True
    effective_continue = False

if effective_continue and previous_session_id is None:
    # ループ初回ステップで continue:true が指定されたが、前ループの最終セッションがない
    # (= ワークフロー全体の最初のステップ、または複数ループで 2 ループ目以降の冒頭が continue:true)
    if not loop_boundary_warned:
        _out(
            f"WARNING: step '{step['name']}' requests continue:true "
            f"but no previous session exists; starting new session."
        )
        loop_boundary_warned = True
    effective_continue = False

if effective_continue:
    session_id = previous_session_id  # 既存 ID を再利用（resume 時は UUID そのまま）
    resume = True
else:
    session_id = str(uuid.uuid4())
    resume = False
```

`build_command` 呼び出しを更新:

```python
command = build_command(
    executable, prompt_flag, common_args, step, log_file_path, auto_mode,
    feedbacks=feedback_contents or None, defaults=defaults,
    session_id=session_id, resume=resume,
)
```

ステップ実行後、**成功確定後**（既存の `completed_count += 1` と同じ位置）に状態更新:

```python
# 次ステップに引き継ぐ session ID を更新
# resume=True の場合、Claude CLI は --fork-session なしなら同じ ID を維持するため session_id をそのまま保持
# resume=False の場合、新たに発行した UUID を次ステップの候補にする
previous_session_id = session_id
completed_count += 1
```

**更新位置の意図**: 失敗時は `_run_steps` が即 `return exit_code` するため (R5 で整理済み)、成功ステップのみ `previous_session_id` が更新される。コードの読み順として `completed_count += 1` と並べることで「成功時にのみ到達する」ことが視覚的に明確になる。

#### 3-3. ログ出力の拡張

ステップヘッダの `descriptor_line` を拡張（`Model / Effort` の組み立て直後）:

```python
# 既存: Model / Effort の descriptor_parts 組み立て
...
if requested_continue:
    # YAML 上の宣言を保持（実際に継続されたかは別途表示）
    descriptor_parts.append(f"Continue: {effective_continue}")
descriptor_parts.append(f"Session: {session_id[:8]}")  # 先頭8文字（UUID 短縮表示）
descriptor_line = ", ".join(descriptor_parts) if descriptor_parts else None
```

- **Continue 行**: YAML で `continue: true` が指定されたステップにのみ表示（`false` のステップには出さない、可読性重視）。`effective_continue` を表示することで警告等で無効化された場合も分かる。
  - **既知の非対称性**: 「`continue: false` を明示したステップ」と「`continue` を省略したステップ」はログ上区別できない（どちらも `Continue:` 行が出ない）。トラブルシュート時に YAML を併読する前提とする。README.md の `continue` セクションにこの点を明記する。
- **Session 行**: 常に表示（トラブルシュート時に `claude -r <id>` で手動再開するため）。先頭 8 文字のみ表示して端末幅を節約。完全な UUID はログファイルに残すために別途フッターに出力する（下記）。

ワークフローフッター（成功時 L329-341 付近、失敗時 L303-316 付近）に session 情報を追加:

```python
# 成功時フッター末尾
_out(f"Result: SUCCESS ({completed_count}/{completed_count} steps completed)")
if previous_session_id:
    _out(f"Last session (full): {previous_session_id}")  # 完全な UUID
_out("=====================================")
```

失敗時フッターにも同様の行を追加（step の session_id を表示）。

#### 3-4. main() から `--start > 1` 情報の引き渡し

```python
# 既存: if args.max_step_runs is not None: ...
continue_disabled = args.start > 1  # 追加

if enable_log:
    ...
    exit_code = _run_steps(
        ..., defaults, continue_disabled=continue_disabled,
    )
else:
    ...
    exit_code = _run_steps(
        ..., defaults, continue_disabled=continue_disabled,
    )
```

### 4. `scripts/claude_loop.yaml`（full）の変更

```yaml
steps:
  - name: split_plan
    prompt: /split_plan
    model: opus
    effort: high
    # continue 未設定 = false

  - name: imple_plan
    prompt: /imple_plan
    model: opus
    effort: high
    continue: true        # 追加（split_plan の判断経緯を引き継ぐ）

  - name: wrap_up
    prompt: /wrap_up
    continue: true        # 追加（実装ステップの判断経緯を引き継ぐ）

  - name: write_current
    prompt: /write_current
    # continue 未設定 = false（現況を新規視点で整理）

  - name: retrospective
    prompt: /retrospective
    model: opus
    # continue 未設定 = false（振り返りは独立したフレーミングで）
```

### 5. `scripts/claude_loop_quick.yaml`（quick）の変更

```yaml
steps:
  - name: quick_plan
    prompt: /quick_plan
    # continue 未設定 = false

  - name: quick_impl
    prompt: /quick_impl
    effort: high
    continue: true        # 追加（計画を引き継ぐ）

  - name: quick_doc
    prompt: /quick_doc
    effort: low
    continue: true        # 追加（実装経緯を引き継ぐ）
```

### 6. `scripts/README.md` の変更

既存の「YAML ワークフロー仕様」セクションに以下を追記:

- `continue` キーの説明（`true` / `false` / 省略時の挙動）
- 継続対象ステップの推奨パターン（「前ステップの判断経緯を参照したい整理系ステップに設定」）
- エッジケース: `--start > 1` の場合は全ステップ無効化、ループ初回 `continue: true` の扱い
- ログの `Continue:` / `Session:` 行の意味と `Last session (full):` の用途（手動 `claude -r <uuid>` 再開）
- ログの **非対称性** 注記: `continue: false` 明示と省略はログ上区別できない（YAML 併読前提）
- `--dry-run` でもランダム UUID が出力される（実セッションは作成されない）旨

### 7. `tests/test_claude_loop.py` の変更

#### 7-1. `TestBuildCommandWithSession`（新規クラス）

- `test_without_session_id_no_flag`: `session_id=None` のとき `--session-id` / `-r` どちらも出ない
- `test_session_id_adds_session_id_flag`: `session_id="abc..." resume=False` で `--session-id abc...` が付く
- `test_session_id_with_resume_adds_r_flag`: `session_id="abc..." resume=True` で `-r abc...` が付く
- `test_session_id_after_model_before_system_prompt`: `--model opus --session-id X --append-system-prompt Y` の順序を検証

#### 7-2. `TestGetStepsContinue`（新規クラス）

- `test_omitted_continue_not_in_step_entry`: `continue` を YAML に書かなければ `step` dict に `continue` キーが入らない
- `test_explicit_false_is_retained`: `continue: false` を明示したら `step["continue"] is False`
- `test_explicit_true_is_retained`: `continue: true` で `step["continue"] is True`
- `test_non_bool_raises`: `continue: "yes"` → `SystemExit`
- `test_integer_raises`: `continue: 1` → `SystemExit`
  - 補足: Python の型階層上 `isinstance(True, int) is True` だが、逆方向の `isinstance(1, bool) is False`。`yaml.safe_load` は YAML の `1` を `int`、`true` を `bool` に変換するため `isinstance(value, bool)` チェックで `1` を拒絶できる。

#### 7-3. `TestRunStepsSessionTracking`（新規クラス、`_run_steps` 統合テスト）

`_run_steps` の session 引き継ぎロジックをテスト。`subprocess.run` / `subprocess.Popen` を `MagicMock` で置き換え、`build_command` の呼び出し履歴を検証する形。

- `test_first_step_uses_new_session_id`: 1 ステップ目は `resume=False` で呼ばれる
- `test_continue_step_resumes_previous_session`: 2 ステップ目が `continue: true` なら 1 ステップ目の UUID で `resume=True` 呼び出し
- `test_loop_boundary_warns_when_first_step_continues`: 初回ステップが `continue: true` のケースで `WARNING` ログが 1 度だけ出る
- `test_start_greater_than_one_disables_continue`: `continue_disabled=True` で渡すと全ステップが `resume=False` になり、1 度警告が出る

既存テストへの影響:
- 既存の `TestBuildCommand*` 群はデフォルト引数（`session_id=None` / `resume=False`）で変更なし
- `@patch` パターンは `claude_loop_lib.commands.uuid.uuid4` / 呼び出し側（`_run_steps`）の `uuid.uuid4` を固定値に差し替える（`_run_steps` は `claude_loop.py` 直下に存在するため `claude_loop.uuid.uuid4` を patch）

## リスク・不確実性

### R1. `--session-id <uuid>` の動作仕様

**不確実性**: CLI `--help` に記載はあるが、以下は未検証:
- 同一 UUID を 2 回使うとどうなるか（エラー？上書き？）
- 複数プロセスで同時に同 UUID を使うとどうなるか
- `--session-id` と `-r` を同時に指定した場合の優先順位

**検証方法**: IMPLE ステップで `claude -p --session-id 00000000-... "hello"` を 2 回実行して結果を確認。MEMO.md に記録する。

**リスク緩和**: `uuid.uuid4()` を使うため衝突確率は 1/2^122 で現実的には無視できる。同時実行は `claude_loop.py` のループ構造上起こらない（各ステップは直列）。ただしユーザーが並行で別途 `claude` を走らせている場合は衝突の可能性ゼロではない（実質無視）。

### R2. `-r` 時のモデル/effort 切替

**不確実性**: `-r <session-id> --model opus` のように、継続先セッションと異なるモデル/effort を指定した場合の挙動（PHASE4.0 リスク項目に明記）。

**検証方法**: IMPLE ステップで `-r <sonnet-session> --model opus` を試し、エラーになるか、モデル切替が有効になるか、無視されるかを確認。MEMO.md に記録する。

**リスク緩和**:
- もしエラーになる場合: `_run_steps` で `continue: true` のステップは前ステップの `model` / `effort` を強制継承するよう制限を入れる。ROUGH_PLAN の設定（`imple_plan` は `split_plan` と同じ opus/high）は幸い一貫しているので実害は少ない。
- もし無視される場合: YAML で指定した値が反映されない旨を `scripts/README.md` に警告として記載する。
- もし有効な場合: そのまま使える。

### R3. Session ID の stdout 出力形式

**不確実性**: Claude CLI が `--session-id` 指定時に、指定した UUID を stdout / stderr に出力するかは未検証。出力されない場合は `_run_steps` のログ上で「UUID は Python 側で発行しただけ」という状態になり、実際に CLI がその UUID でセッションを作ったかは `-r` 実行時までわからない。

**検証方法**: IMPLE ステップで実際に 2 ステップ連続で実行し、2 ステップ目の `-r` が正しく前セッションに接続できることをログから確認。

**リスク緩和**: `_run_steps` がログに出力する `Session: <uuid>` は「CLI に渡した UUID」であり、CLI 側の session persistence が無効化されている場合（`--no-session-persistence` フラグ）は動作しないが、現 YAML では未使用。

### R4. TeeWriter との UUID 出力の両立

**不確実性**: なし。UUID は Python 側で生成する文字列で、subprocess 出力には依存しない。TeeWriter のロジックに変更は不要。

**リスク緩和**: 不要。

### R5. `continue: true` で前ステップが失敗した場合

**整理**: 現行仕様では前ステップが exit_code ≠ 0 なら `_run_steps` が即 `return exit_code` するため、後続の `continue: true` ステップは実行されない。このケースは発生しない。別プロセスのフローとしても検討不要。

## 実装順序

1. **`get_steps` に `continue` キー取り込み追加** + ユニットテスト（`TestGetStepsContinue`）
2. **`build_command` に `session_id` / `resume` 引数追加** + ユニットテスト（`TestBuildCommandWithSession`）
3. **`_run_steps` のセッション状態管理実装** + 統合テスト（`TestRunStepsSessionTracking`）
4. **`main()` に `continue_disabled` 受け渡し追加**（`--start > 1` の判定）
5. **`claude_loop.yaml` / `claude_loop_quick.yaml` に `continue: true` を設定**
6. **R1-R3 を実機検証**（`claude -p --session-id ...` を手動実行して結果を MEMO.md に記録）
7. **`scripts/README.md` に `continue` セクション追加**
8. **全テスト green を確認**（`python -m unittest tests.test_claude_loop` 想定: 既存 89 件 + 新規 10〜15 件）
9. **`--dry-run --no-log` で full/quick 両方のコマンド一覧を ver4.1 と差分比較**（期待: 各ステップに `--session-id <uuid>` または `-r <uuid>` が追加されるのみ）

## 完了条件

- `python -m unittest tests.test_claude_loop` がグリーン
- `pnpm test` が既存件数グリーン（影響なし見込み）
- `scripts/claude_loop.py -w scripts/claude_loop.yaml --dry-run --no-log` が `--session-id <uuid>` 付きのコマンドを出力する
- `scripts/claude_loop.py -w scripts/claude_loop.yaml --start 3 --dry-run --no-log` 実行時、`continue: true` を指定した `imple_plan` / `wrap_up` が `--session-id`（`-r` ではなく）でコマンドを出し、`WARNING: --start > 1` の警告ログが出る
- 実機で 2 ステップ連続実行し、2 ステップ目が前ステップの会話を参照できることをログから確認（MEMO.md に記録）
- `docs/util/MASTER_PLAN.md` の PHASE4.0 ステータスが「部分実装」から「実装済み」に更新可能（`write_current` ステップで実施）
