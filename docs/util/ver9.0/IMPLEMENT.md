# ver9.0 IMPLEMENT — `--workflow auto` 導入 + `/issue_plan` 単独 YAML 新設（PHASE6.0 §3 + §5）

## 0. 事前リファクタリング

**不要**。`claude_loop.py` の現構造（`main()` が `parse_args` → `resolve_command_config` → `_run_steps` を呼ぶ線形フロー、`workflow.resolve_*` が YAML セクション解決を持つ）を変えずに、`auto` モードは `_run_steps` を 2 回呼ぶ形で追加できる。`--workflow` 型の `Path → str` 置換も argparse の `type=` を差し替えるだけで済む。REFACTOR.md は作成しない。

## 1. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---|---|---|
| `scripts/claude_loop.py` | 変更 | `--workflow` の型を str 化 + 既定値 `"auto"` + 予約値解決ロジック + `auto` 分岐（2 段実行）を `main()` に追加 |
| `scripts/claude_loop_lib/workflow.py` | 変更 | `resolve_workflow_value(value, default_yaml_dir) -> Path | "auto"` を新設（予約値 `auto/full/quick` とパス直指定を振り分ける） |
| `scripts/claude_loop_issue_plan.yaml` | 新規 | `/issue_plan` 1 ステップの YAML。`mode` / `command` / `defaults` セクションは `claude_loop.yaml` と同期 |
| `scripts/claude_loop.yaml` | 変更 | （仕様確認のみ。`/issue_plan` がステップ 1 に存在することは ver8.0 時点で整備済み） |
| `scripts/claude_loop_quick.yaml` | 変更 | （同上） |
| `scripts/README.md` | 変更 | `--workflow auto | full | quick | <path>` の説明、`--auto` との違い、`claude_loop_issue_plan.yaml` のクイックスタート追記 |
| `.claude/skills/meta_judge/WORKFLOW.md` | 変更 | 「保守上の注意」末尾の「`--workflow auto` 分岐ロジックは ver8.1 以降で導入予定」を「実装済み（ver9.0）」に更新し、`auto` モードの動作を 1 段落で追記 |
| `tests/test_claude_loop.py` | 変更 | 予約値解決、`auto` 分岐（2 段実行）、frontmatter フォールバック、`--start` 制約のテスト追加 |
| `ISSUES/util/low/issue-plan-standalone-yaml.md` | 移動 | `/wrap_up` or `/retrospective` で `ISSUES/util/low/done/` へ移動（本ステップでは触らない） |

変更対象ファイル合計 8 件（`scripts/` 5 件 + `.claude/` 1 件 + `tests/` 1 件 + `docs/` は `/wrap_up` 側）。`ISSUES/` 移動は `/wrap_up` 側。メジャースコープ妥当。

## 2. `.claude/` 配下の編集手順

`.claude/skills/meta_judge/WORKFLOW.md` の 1 行編集が発生する。ver8.0 と同手順で `claude_sync.py` を介する:

1. `python scripts/claude_sync.py export`
2. `.claude_sync/skills/meta_judge/WORKFLOW.md` を編集
3. `python scripts/claude_sync.py import`
4. `git diff .claude/skills/meta_judge/` で反映確認

他 `.claude/` 編集が同バージョンで発生しない見込みなので、`export → 編集 → import` は 1 往復で十分。

## 3. `--workflow` の予約値解決（`workflow.py`）

### 3-1. 新規ヘルパ `resolve_workflow_value`

`scripts/claude_loop_lib/workflow.py` に追加:

```python
FULL_YAML_FILENAME = "claude_loop.yaml"
QUICK_YAML_FILENAME = "claude_loop_quick.yaml"
ISSUE_PLAN_YAML_FILENAME = "claude_loop_issue_plan.yaml"

RESERVED_WORKFLOW_VALUES = ("auto", "full", "quick")


def resolve_workflow_value(value: str, yaml_dir: Path) -> str | Path:
    """Resolve the --workflow CLI value.

    - "auto" -> returns "auto" (sentinel; caller handles two-phase execution)
    - "full" -> Path(yaml_dir / FULL_YAML_FILENAME)
    - "quick" -> Path(yaml_dir / QUICK_YAML_FILENAME)
    - other (path-like) -> Path(value).expanduser()

    Reserved-value matching is exact and case-sensitive.
    """
    if value == "auto":
        return "auto"
    if value == "full":
        return yaml_dir / FULL_YAML_FILENAME
    if value == "quick":
        return yaml_dir / QUICK_YAML_FILENAME
    return Path(value).expanduser()
```

ポイント:

- 予約値マッチは完全一致（`AUTO` や `Auto` はパス扱い、ただし通常は存在しないので `load_workflow` 側で FileNotFound エラー）
- `yaml_dir` は `claude_loop.py` 側から `DEFAULT_WORKFLOW_PATH.parent`（= `scripts/`）を渡す
- 戻り値は `Path` かリテラル `"auto"` の union。呼び出し側で `isinstance(..., str)` または `== "auto"` で分岐

### 3-2. テスト（`tests/test_claude_loop.py` に追記）

- `test_resolve_auto_returns_sentinel`: `"auto"` → `"auto"` 文字列
- `test_resolve_full_returns_full_yaml_path`: `"full"` → `<yaml_dir>/claude_loop.yaml`
- `test_resolve_quick_returns_quick_yaml_path`: `"quick"` → `<yaml_dir>/claude_loop_quick.yaml`
- `test_resolve_path_like_returns_path`: `"/tmp/foo.yaml"` → `Path("/tmp/foo.yaml")`
- `test_resolve_relative_path_preserved`: `"other.yaml"` → `Path("other.yaml")`（`yaml_dir` は付けない）
- `test_reserved_values_are_case_sensitive`: `"AUTO"` → `Path("AUTO")` （パス扱い）

## 4. `claude_loop.py` の CLI 変更

### 4-1. `--workflow` 引数

現状:

```python
parser.add_argument(
    "-w", "--workflow",
    type=Path,
    default=DEFAULT_WORKFLOW_PATH,
    help=f"Path to workflow YAML (default: {DEFAULT_WORKFLOW_PATH})",
)
```

変更後:

```python
parser.add_argument(
    "-w", "--workflow",
    type=str,
    default="auto",
    help="Workflow selector: 'auto' (default) | 'full' | 'quick' | path to a YAML file",
)
```

### 4-2. argparse 直後に予約値解決

`args = parser.parse_args()` の後、`main()` 冒頭で:

```python
yaml_dir = Path(__file__).resolve().parent
resolved = resolve_workflow_value(args.workflow, yaml_dir)
```

`resolved` は `"auto"` か `Path`。

### 4-3. `--workflow auto` + `--start > 1` の制約

`auto` モードで `--start` を 2 以上にするのは意味論的に曖昧（段階 1 の `/issue_plan` をスキップすると ROUGH_PLAN.md が書かれず、段階 2 が分岐できない）。

対処:

```python
if resolved == "auto" and args.start > 1:
    raise SystemExit(
        "--workflow auto requires --start 1 (cannot skip /issue_plan phase)."
    )
```

`--max-step-runs` については auto 段階 1 が 1 ステップ、段階 2 が最大 5 ステップなので、合計 6 を超えないよう段階 2 側で残数を計算して渡す（§5-4 参照）。

### 4-4. 非 `auto` 時の処理

`resolved` が `Path` の場合、従来通りの 1 ワークフロー実行:

```python
config = load_workflow(resolved)
steps = get_steps(config)
# ... 既存の uncommitted / tee / _run_steps 呼び出し
```

変更点は `args.workflow` を直接渡していた箇所を `resolved` に差し替えるだけ。`create_log_path(args.log_dir, resolved)` のように log 名にも `resolved` を渡す（`auto` は非 auto 分岐には来ないので安全）。

### 4-5. `auto` 時の処理（2 段実行）

擬似コード:

```python
if resolved == "auto":
    # ---- Phase 0: 共通初期化 ----
    # uncommitted チェック、tee/log セットアップ、feedbacks_dir 等
    phase1_yaml = yaml_dir / ISSUE_PLAN_YAML_FILENAME
    config1 = load_workflow(phase1_yaml)
    steps1 = get_steps(config1)

    # log 名は phase1 の名前を採用（"issue_plan" と分かるように）
    # → log_path は create_log_path(args.log_dir, phase1_yaml) のまま

    # --max-loops は「フェーズ 1 + フェーズ 2 合わせて 1 周」の意味で引き継ぐ
    # （既存挙動と一致: 未指定時は parse_args で 1 にセット済み）

    # --no-log / --dry-run 時は tee=None / log_path=None で既存挙動を継承
    # （下記は tee が有効な場合の例。無効時は既存 main() と同じく tee=None で _run_steps を呼ぶ）

    with open(log_path, "w", encoding="utf-8") as log_file:
        tee = TeeWriter(log_file)

        # ---- Phase 1: /issue_plan 単独実行 ----
        exit_code = _run_steps(
            iter_steps_for_loop_limit(steps1, 0, 1),  # 1 周分 = 1 ステップ
            steps1, executable, prompt_flag, common_args,
            cwd, args.dry_run, tee, log_path, auto_mode,
            uncommitted_status, defaults1,
        )
        if exit_code != 0:
            return exit_code

        # ---- Phase 2: ROUGH_PLAN.md frontmatter を読む ----
        rough_plan = _find_latest_rough_plan(cwd)
        phase2_kind = _read_workflow_kind(rough_plan)  # "full" | "quick"

        # ---- Phase 3: 後続 YAML を読み、step[1:] を実行 ----
        phase2_yaml = yaml_dir / (
            QUICK_YAML_FILENAME if phase2_kind == "quick" else FULL_YAML_FILENAME
        )
        config2 = load_workflow(phase2_yaml)
        steps2 = get_steps(config2)
        defaults2 = resolve_defaults(config2)
        # phase2 共通 args / mode は phase1 と同一であることを確認する（任意の整合チェック）

        tee.write_line("")
        tee.write_line(f"--- auto: phase2 = {phase2_kind} ({phase2_yaml.name}) ---")

        # step[1:] = /issue_plan を除く残り
        if len(steps2) < 2:
            tee.write_line("WARNING: phase2 YAML has <2 steps; nothing to run.")
            return 0

        # 残 step 数を使って max_step_runs を再計算（指定があれば）
        remaining_budget = _compute_remaining_budget(args, completed=1)

        phase2_iter = (
            iter_steps_for_step_limit(steps2, 1, remaining_budget)
            if remaining_budget is not None
            else iter_steps_for_loop_limit(steps2, 1, args.max_loops or 1)
        )

        exit_code = _run_steps(
            phase2_iter, steps2, executable, prompt_flag, common_args,
            cwd, args.dry_run, tee, log_path, auto_mode,
            uncommitted_status=None,  # 2 回目は表示しない（重複防止）
            defaults=defaults2,
        )
```

### 4-6. `_find_latest_rough_plan(cwd) -> Path`

`docs/{CURRENT_CATEGORY}/ver*/ROUGH_PLAN.md` を glob で列挙し、`st_mtime` が最大のものを返す。

```python
def _find_latest_rough_plan(cwd: Path) -> Path:
    cat_file = cwd / ".claude" / "CURRENT_CATEGORY"
    category = cat_file.read_text(encoding="utf-8").strip() if cat_file.is_file() else "app"
    docs_dir = cwd / "docs" / category
    candidates = list(docs_dir.glob("ver*/ROUGH_PLAN.md"))
    if not candidates:
        raise SystemExit(
            f"auto workflow: no ROUGH_PLAN.md found under {docs_dir}. "
            f"Did /issue_plan fail silently?"
        )
    return max(candidates, key=lambda p: p.stat().st_mtime)
```

ポイント:

- カテゴリ解決は `/issue_plan` SKILL と同じ規則（CURRENT_CATEGORY 未設定時は `app` フォールバック）
- 最新判定は `st_mtime`。`/issue_plan` が今回のフェーズ 1 で新規作成した ROUGH_PLAN.md は必ず最新になる
- **注意**: 既に存在する ver(N-1) の ROUGH_PLAN.md より mtime が新しいという前提。`auto` フェーズ 1 が走った直後に読むのでこれは成立する（中断や人間編集による mtime 逆転は R2 に記載）

### 4-7. `_read_workflow_kind(rough_plan_path) -> Literal["full", "quick"]`

```python
def _read_workflow_kind(rough_plan: Path) -> str:
    text = rough_plan.read_text(encoding="utf-8")
    fm, _body = parse_frontmatter(text)
    if fm is None:
        print(
            f"WARNING: no frontmatter in {rough_plan}; falling back to 'full'.",
            file=sys.stderr,
        )
        return "full"
    value = fm.get("workflow")
    if value not in ("quick", "full"):
        print(
            f"WARNING: invalid workflow={value!r} in {rough_plan}; falling back to 'full'.",
            file=sys.stderr,
        )
        return "full"
    return value
```

フォールバックは常に安全側（`full`）に倒す。警告は stderr へ（tee が拾えばログにも残る）。

### 4-8. `_compute_remaining_budget(args, completed)`

`--max-step-runs` が指定されている場合は `max(args.max_step_runs - completed, 0)` を返す。`--max-loops` なら None を返して既存のループ制限ロジックへ。

```python
def _compute_remaining_budget(args: argparse.Namespace, completed: int) -> int | None:
    if args.max_step_runs is None:
        return None
    return max(args.max_step_runs - completed, 0)
```

## 5. `scripts/claude_loop_issue_plan.yaml`（新規）

```yaml
mode:
  auto: true

command:
  executable: claude
  prompt_flag: -p
  args:
    - --dangerously-skip-permissions
  auto_args:
    - --disallowedTools "AskUserQuestion"
    - >-
      --append-system-prompt "you cannot ask questions to the user. so,
      whenever you think you should get human feedback, just write a file under
      `REQUESTS/AI` folder. Human will see this after you finish this step.
      (**So you cannot directly ask nor get human feedback in this session.**)

      ## Editing files under .claude/

      Files under `.claude/` cannot be directly edited in CLI `-p` mode (security restriction).
      To edit files in `.claude/`, use `scripts/claude_sync.py` with the following steps:

      1. `python scripts/claude_sync.py export` — Copy `.claude/` to `.claude_sync/`
      2. Edit the corresponding files in `.claude_sync/` (this directory is writable)
      3. `python scripts/claude_sync.py import` — Write back `.claude_sync/` contents to `.claude/`

      **Note**: Run export/import via the Bash tool with `python scripts/claude_sync.py <command>`."

defaults:
  model: sonnet
  effort: medium

steps:
  - name: issue_plan
    prompt: /issue_plan
    model: opus
    effort: high
```

`mode` / `command` / `defaults` は `claude_loop.yaml` と厳密一致。`steps` のみが 1 要素。

### 5-1. 保守義務の追記

`.claude/skills/meta_judge/WORKFLOW.md` の「保守上の注意」節に以下を追記:

```
- `claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` の
  `command` / `mode` / `defaults` セクションは同一内容で維持する
  （いずれかを変更した場合は必ず 3 ファイル全てを同期すること）
```

## 6. `scripts/claude_loop.yaml` / `scripts/claude_loop_quick.yaml`

両 YAML の step 1 は既に `/issue_plan` になっている（ver8.0 で整備済み）。`auto` フェーズ 2 は `step[1:]` を使うため、step 1 が `/issue_plan` 固定であることが本実装の前提。

### 6-1. 前提アサーション（コメントのみ）

両 YAML の先頭コメントに「`auto` モードはこの YAML の step[1:] を使う」旨を 1 行記載しておく:

```yaml
# NOTE: --workflow auto uses steps[1:] of this file. steps[0] must be /issue_plan.
```

（YAML ロード時のバリデーションには加えない。`auto` 分岐実装側で `steps2[0]["name"] == "issue_plan"` をチェックして警告を出すに留める）

### 6-2. `auto` 側の先頭名チェック（軽量）

```python
if steps2[0].get("name") != "issue_plan":
    tee.write_line(
        f"WARNING: phase2 YAML step[0] is {steps2[0].get('name')!r}, "
        f"expected 'issue_plan'. Skipping anyway."
    )
```

## 7. `scripts/README.md` 更新

### 7-1. クイックスタート節

既存「フルワークフロー実行」「軽量ワークフロー実行」を以下に差し替え・追記:

```bash
# デフォルト（= --workflow auto、/issue_plan の判定に従って full/quick 自動選択）
python scripts/claude_loop.py

# 明示的に full/quick を指定
python scripts/claude_loop.py --workflow full
python scripts/claude_loop.py --workflow quick

# /issue_plan だけ 1 回回す（SKILL 調整・ISSUE レビュー定期実行向け）
python scripts/claude_loop.py --workflow scripts/claude_loop_issue_plan.yaml

# 従来互換: 明示的な YAML パス指定
python scripts/claude_loop.py --workflow scripts/claude_loop_quick.yaml
```

### 7-2. CLI オプション表の `--workflow` 行

```
| `--workflow` | `-w` | str | `auto` | `auto` / `full` / `quick` / YAML パスのいずれか |
```

### 7-3. `--auto` と `--workflow auto` の違い節（新設）

`## クイックスタート` の直後に短い節を新設:

```markdown
### `--auto` と `--workflow auto` の違い

| フラグ | 意味 |
|---|---|
| `--auto` | 無人実行モード。`command.auto_args` を結合し、AskUserQuestion を無効化 |
| `--workflow auto` | ワークフロー自動選択。`/issue_plan` を先行実行して結果に応じて full/quick を選ぶ |

両者は独立。併用例: `python scripts/claude_loop.py --auto --workflow auto`（無人モードでワークフロー自動選択）。
```

### 7-4. `auto` 分岐仕様節（新設、YAML 仕様の後）

```markdown
### `--workflow auto` の分岐仕様

1. `scripts/claude_loop_issue_plan.yaml` で `/issue_plan` を実行
2. `docs/{category}/ver*/ROUGH_PLAN.md` の最新 mtime ファイルを開き frontmatter の `workflow:` を読む
3. `quick` → `claude_loop_quick.yaml` の `steps[1:]`、`full` → `claude_loop.yaml` の `steps[1:]` を実行
4. `workflow:` 未記載・不正値 → `full` にフォールバック（警告を log/stderr に出力）
5. `--workflow auto` と `--start N>1` は併用不可（エラー終了）
```

### 7-5. ファイル一覧への追加

```
| `claude_loop_issue_plan.yaml` | `/issue_plan` 単独実行用 YAML（`--workflow auto` の第 1 段でも使用） |
```

## 8. テスト追加（`tests/test_claude_loop.py`）

### 8-1. `TestResolveWorkflowValue`

`resolve_workflow_value` の単体テスト（§3-2 の 6 ケース）。

### 8-2. `TestParseArgsWorkflow`

- `test_default_is_auto_string`: `parse_args([])` → `args.workflow == "auto"`
- `test_explicit_full_reserved`: `parse_args(["-w", "full"])` → `args.workflow == "full"`
- `test_explicit_path`: `parse_args(["-w", "custom.yaml"])` → `args.workflow == "custom.yaml"`

### 8-3. `TestAutoStartConstraint`

- `test_auto_with_start_1_ok`: `main()` 実行できる
- `test_auto_with_start_2_raises`: `main()` → `SystemExit`（メッセージに "--start 1" 含む）

`main()` 全体をモックするのは大がかりなので、制約チェック部分を `validate_auto_args(resolved, args)` 等のヘルパに切り出して単体テスト可能にする。

### 8-4. `TestReadWorkflowKind`

テンポラリディレクトリに ROUGH_PLAN.md を書き、`_read_workflow_kind()` を直接呼ぶ:

- `test_valid_quick_returns_quick`
- `test_valid_full_returns_full`
- `test_missing_frontmatter_falls_back_to_full_with_warning`（`sys.stderr` キャプチャ）
- `test_missing_workflow_key_falls_back_to_full`
- `test_invalid_workflow_value_falls_back_to_full`（例: `workflow: banana`）

### 8-5. `TestFindLatestRoughPlan`

- `test_single_rough_plan_returned`: 1 ファイルだけ置いて返り値確認
- `test_latest_mtime_wins`: 3 ファイル作成して `os.utime` で mtime 差をつける
- `test_no_rough_plan_raises`: ディレクトリ空 → `SystemExit`
- `test_uses_current_category_file`: `.claude/CURRENT_CATEGORY` を書いて正しいカテゴリが選ばれること

### 8-6. `TestAutoWorkflowIntegration`

`subprocess.run` と `_find_latest_rough_plan` / `_read_workflow_kind` をモックして `main()` を 2 段実行させる:

- `test_auto_runs_issue_plan_then_full`: ROUGH_PLAN.md frontmatter `workflow: full` を返すモック → `subprocess.run` が 1 (issue_plan) + 5 (split_plan..retrospective) = 6 回呼ばれる
- `test_auto_runs_issue_plan_then_quick`: `workflow: quick` → 1 + 2 = 3 回
- `test_auto_phase1_failure_aborts`: フェーズ 1 が exit 1 → フェーズ 2 は呼ばれない
- `test_auto_fallback_on_invalid_frontmatter`: `workflow: banana` → `full` に倒す
- `test_auto_dry_run_skips_phase2`: `--dry-run` 併用時はフェーズ 1 のコマンドのみ表示され、フェーズ 2 は実行もログ出力もスキップされる（R4）
- `test_auto_no_log_passes_none_to_run_steps`: `--no-log` 併用時は `tee=None` / `log_path=None` でフェーズ 1・2 とも `_run_steps` が呼ばれる

既存の `TestRunStepsSessionTracking` と同じパッチ手法（`@patch("claude_loop.subprocess.run")` + `@patch("claude_loop.uuid.uuid4")`）を踏襲。

### 8-7. 既存テストへの影響確認

`TestParseArgsLoggingOptions` 等で `args.workflow` のデフォルト値（旧: `Path(...)`, 新: `"auto"`）を参照しているテストがあれば更新。`grep` 確認対象:

```bash
grep -n "args.workflow" tests/test_claude_loop.py
grep -n "DEFAULT_WORKFLOW_PATH" tests/test_claude_loop.py
```

影響ありそうなアサーションがあれば `args.workflow == "auto"` に置換。

## 9. 実行順序・検証手順（`/imple_plan` で実施）

1. 現状の `python -m unittest tests.test_claude_loop` が通ることを確認（青色ベースライン）
2. `resolve_workflow_value` を `workflow.py` に追加、対応テスト（§8-1）を先に書いて TDD 風に実装
3. `claude_loop_issue_plan.yaml` を新規作成、YAML 妥当性を `python -c "import yaml; yaml.safe_load(open('scripts/claude_loop_issue_plan.yaml'))"` で確認
4. `claude_loop.py` の `--workflow` 型変更＋制約チェック実装、テスト（§8-2, §8-3）
5. `_find_latest_rough_plan` / `_read_workflow_kind` / `_compute_remaining_budget` を `claude_loop.py` に追加、テスト（§8-4, §8-5）
6. `main()` に `auto` 分岐を実装、統合テスト（§8-6）
7. `claude_loop.yaml` / `claude_loop_quick.yaml` に先頭 NOTE コメントを追加
8. `scripts/README.md` 更新（§7）
9. `.claude/skills/meta_judge/WORKFLOW.md` 更新（§5-1 の保守義務追記 + `auto` 実装済み記述）→ `claude_sync.py` 経由
10. 全テスト実行: `python -m unittest tests.test_claude_loop`（件数増加想定: 103 → 120 前後）
11. ドライラン: `python scripts/claude_loop.py --workflow auto --dry-run --no-notify`
    - issue_plan ステップのコマンドが 1 回表示されることを確認
    - （ドライランは ROUGH_PLAN.md を実際には作らないので、`auto` フェーズ 2 はスキップする仕様を実装する必要あり。下記 §10 R4 参照）
12. `--no-log` 併用ドライラン: `python scripts/claude_loop.py --workflow auto --no-log --dry-run --no-notify`
    - ログファイルが生成されず、コマンド 1 回表示のみで終了すること
    - 既存 `main()` の `enable_log = not args.no_log and not args.dry_run` 分岐を踏襲し、`auto` ブロック内でも `tee=None` / `log_path=None` で `_run_steps` を呼ぶ経路をカバー

## 10. リスク・不確実性

### R1: `_find_latest_rough_plan` の mtime 依存

- **状況**: `auto` フェーズ 1 で書かれた ROUGH_PLAN.md を「最新 mtime」で同定する前提
- **影響**: 人間が過去の ROUGH_PLAN.md を手動で `touch` したり、複数バージョンが同秒内に書き込まれると誤同定の可能性
- **対処**: 初期実装では mtime 採用で割り切る。将来的には「フェーズ 1 開始時点の最大 mtime を記録しておき、それを超えるものを候補とする」形に強化可能。ver9.0 スコープでは不要

### R2: `auto` フェーズ 2 のセッション引き継ぎ

- **状況**: フェーズ 1 末尾の session_id をフェーズ 2 の先頭ステップに引き継ぐべきか
- **影響**: 現状の `claude_loop.yaml` では `/split_plan` は `continue: false`（省略）のため、引き継がない方が整合的
- **対処**: `auto` フェーズ 2 の `_run_steps` 呼び出しでは `previous_session_id` を渡さない（内部変数がローカルなので自動的にそうなる）。`continue: true` を先頭に持つステップがあれば既存の「no previous session」警告が出る。これは意図通り

### R3: `--max-step-runs` との整合

- **状況**: `--max-step-runs 3 --workflow auto` でフェーズ 1（1 ステップ）＋フェーズ 2 残り 2 ステップが期待値
- **影響**: 残数計算を間違えるとフェーズ 2 が想定と違うステップ数を走らせる
- **対処**: `_compute_remaining_budget(args, completed=1)` で `max(max_step_runs - 1, 0)` を返す。`remaining == 0` のときはフェーズ 2 を走らせず早期 return

### R4: `--dry-run` との相性

- **状況**: `--workflow auto --dry-run` では `/issue_plan` が実行されないため ROUGH_PLAN.md が作られず、フェーズ 2 の frontmatter 読み取りが失敗する
- **影響**: エラーで落ちる or 無限ループっぽい振る舞い
- **対処**: `--dry-run` が有効かつ `resolved == "auto"` の場合は、フェーズ 1 のコマンドだけ表示してフェーズ 2 はスキップする。ログに `"--- auto: phase2 skipped (--dry-run) ---"` を出す。テスト `test_auto_dry_run_skips_phase2` を §8-6 に追加

### R5: `/issue_plan` が frontmatter を書き忘れた場合

- **状況**: ver8.0 の `/issue_plan` SKILL は frontmatter に `workflow` を書く責務を持つが、実行時に忘れられる可能性
- **影響**: フェーズ 2 が `full` にフォールバックするが、利用者はそれに気づきにくい
- **対処**: §4-7 の警告を stderr と tee 両方に出す。加えて `/issue_plan` SKILL 本文（`.claude_sync/skills/issue_plan/SKILL.md`）側でも「`workflow:` frontmatter 必須」を強調する文言を追記するかは見送り（ver8.0 で既に明記済み）

### R6: `load_workflow` のパス解決と既定値変更の相互作用

- **状況**: 旧デフォルトは `Path(__file__).with_name("claude_loop.yaml")` という絶対パス、新デフォルトは文字列 `"auto"`
- **影響**: `claude_loop.py` を別ディレクトリから `python scripts/claude_loop.py --workflow foo.yaml` で呼ぶと、`resolve_workflow_value` は `Path("foo.yaml")`（相対）を返す。`load_workflow` は `.expanduser().resolve()` するので `os.getcwd()/foo.yaml` を見に行く
- **対処**: 従来と同じ挙動（`Path("foo.yaml")` を `--workflow` に与えたら cwd からの相対扱い）なので互換維持。テスト `test_resolve_relative_path_preserved` でカバー

### R7: `.claude/CURRENT_CATEGORY` 未設定時の挙動

- **状況**: `_find_latest_rough_plan` が `app` フォールバックを使うが、`docs/app/ver*/ROUGH_PLAN.md` が全く存在しない環境（= app 初回 auto 実行）では `SystemExit`
- **影響**: エラーメッセージで原因が分かりづらい可能性
- **対処**: `SystemExit` のメッセージに「CURRENT_CATEGORY 未設定時は `app` が使われる」旨と、`/issue_plan` 実行ログを確認するよう案内を含める

### R8: `issue_worklist.py` の出力が `/issue_plan` SKILL の `!` バックティック展開で失敗するケース

- **状況**: `issue_worklist.py` が何らかの理由でエラー終了すると、SKILL の冒頭コンテキスト展開が失敗する
- **影響**: `/issue_plan` 自体が起動しない → フェーズ 1 が exit ≠ 0
- **対処**: §4-5 の「`if exit_code != 0: return exit_code`」で確実に中断するため新規作業は不要。本 ISSUE は `issue_worklist.py` 側の堅牢性で別途扱う

## 11. コミット戦略

`/imple_plan` ステップで以下の粒度でコミットする想定（参考情報）:

1. `scripts/claude_loop_lib/workflow.py` に `resolve_workflow_value` 追加 + テスト
2. `scripts/claude_loop_issue_plan.yaml` 新規作成
3. `scripts/claude_loop.py` に `auto` 分岐・ヘルパ追加 + テスト
4. `scripts/claude_loop.yaml` / `scripts/claude_loop_quick.yaml` の先頭 NOTE コメント追加
5. `scripts/README.md` 更新
6. `.claude/skills/meta_judge/WORKFLOW.md` 更新（claude_sync.py 経由、1 往復）
7. `ISSUES/util/low/issue-plan-standalone-yaml.md` の移動は `/wrap_up` / `/retrospective` 側で実施

`.claude/` と `scripts/` を同一コミットに混ぜない（ver8.0 踏襲）。

## 12. スコープ外（次バージョン以降）

- `--workflow auto` の `--start N>1` 対応（フェーズ 2 からの再開）
- `issue_worklist.py --limit` オプション
- `/issue_plan` → `/split_plan` 間の `continue: true` 化
- `claude_loop_issue_plan.yaml` / `claude_loop.yaml` / `claude_loop_quick.yaml` の `command` セクション重複解消（includes 機構の導入）

これらは PHASE6.0 §3 の範囲外、または別 ISSUE として計画する。
