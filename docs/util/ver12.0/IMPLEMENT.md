# IMPLEMENT: util ver12.0 — PHASE7.0 §2 起動前 validation の導入

`ROUGH_PLAN.md` の主対象「PHASE7.0 §2: category・YAML・全 step の起動前 validation」の実装方式を確定する。事前リファクタリングは不要（本 IMPLEMENT と同一コミット範囲で新規モジュール `validation.py` を追加するのみ。既存 `workflow.py` の raise-on-first-error 挙動は保持する）。

---

## 0. 方針サマリ

- `scripts/claude_loop_lib/validation.py` を**新規作成**し、`validate_startup()` を公開 API として定義する
- 既存 `workflow.py` / `commands.py` の raise-on-first-error 検証はランタイム防衛として**維持**し、起動前 validation は独立レイヤとして上位に乗せる（重複は限定的かつ意図的）
- エラーは可能な範囲で **集約** して最後に一括出力。ただし「先行段階で致命的」な場合（YAML parse 失敗 / 構造がそもそも dict でない）は後続検証を打ち切る
- `--workflow auto` は phase 1 (`claude_loop_issue_plan.yaml`) と phase 2 候補 2 本（`claude_loop.yaml` / `claude_loop_quick.yaml`）を **すべて事前検証**する。「validation 通過 = ROUGH_PLAN.md の workflow 値にかかわらず最後まで到達可能」という契約を確立する（ROUGH_PLAN §3「`--workflow auto` との接続」への回答）
- 値の whitelist（`model` / `effort`）は **warning 扱い** とし、SystemExit は発生させない。CLI 仕様が更新されても即時壊れないようにする一方、typo は検出する（§2-3 参照）
- 新規 CLI flag は **導入しない**。validation は常時実行される。（将来 escape hatch が必要になれば次バージョンで追加）

---

## 1. 設計確定事項

### 1-1. 検証カテゴリと対応する責務

ROUGH_PLAN §スコープ 1 の 5 項目を以下に割り当てる:

| # | 項目 | 実装担当関数 | 既存か新規か |
|---|---|---|---|
| ① | category 名の妥当性 | `validate_category()` | **新規** |
| ② | YAML 存在・parse・schema | `validate_yaml_shape()` | **新規** (内部で `yaml.safe_load` を直接呼ぶ。`load_workflow` の try/except でも可だが、エラーをまとめて拾いたいため別実装) |
| ③ | 全 step の参照解決（SKILL / command executable） | `validate_step_references()` | **新規** |
| ④ | step override 設定の許容範囲・必須値・継承後の有効設定 | `validate_override_schema()` | 既存 `OVERRIDE_STRING_KEYS` / `ALLOWED_STEP_KEYS` / `ALLOWED_DEFAULTS_KEYS` 定数を import して再利用。既存 raise は残し、validation レイヤは独立に **try/except 経由で重複チェック** |
| ⑤ | 実行前に判定できる入出力条件 | `validate_io_preconditions()` | **新規** (cwd 存在 / `docs/{category}/` 存在 / `shutil.which(executable)`) |

### 1-2. `Violation` データ構造

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Violation:
    source: str      # 例: "category", "yaml/claude_loop.yaml", "step[2]"
    message: str     # 人間可読のエラー文言
    severity: str    # "error" | "warning"
```

- `severity == "error"` が 1 件でもあれば SystemExit（exit code 2）
- `severity == "warning"` のみの場合は stderr に列挙して実行続行
- 列挙順は `source` のソースコード上の出現順を保つ（list append 順）

### 1-3. エラー集約戦略（"可能な範囲で" の切り分け）

| フェーズ | 失敗時の挙動 |
|---|---|
| YAML file 存在チェック | 全 YAML について一括確認し、1 本でも欠ければ後続の schema 検証を**当該 YAML のみスキップ**（他 YAML の検証は継続） |
| YAML parse | 同上。parse 失敗 YAML は schema 検証を skip、他 YAML は継続 |
| 上位 schema (mapping でない等) | 当該 YAML の後続 schema 検証を skip |
| step schema (prompt 欠如 / 未知キー / 型不正) | 当該 step のみ skip し、同 YAML 内の他 step は継続検証 |
| defaults schema | 当該 YAML のみ skip、step 検証は続行 |
| category / executable / cwd | 独立チェック、他と並列に実行 |
| step reference (SKILL 未解決) | 該当 step のみ violation 追加、継続 |

「YAML A の parse が壊れていても YAML B の step 5 の typo は同じ実行で報告される」ことを保証する。

### 1-4. `--workflow auto` との接続

- CLI 引数が `--workflow auto` の場合、検証対象 YAML は **3 本**（`claude_loop_issue_plan.yaml` + `claude_loop.yaml` + `claude_loop_quick.yaml`）
- `--workflow full` / `--workflow quick` / 任意パスの場合は **当該 1 本のみ**を検証
- phase 2 の workflow 種別は ROUGH_PLAN.md 生成後に決まるため、auto では両分岐を先回り検証する。既存 `_run_auto()` の分岐ロジックには手を入れない
- `claude_loop_issue_plan.yaml` は step が 1 本のみだが、他 2 本と `command` / `mode` / `defaults` が同期すべきとコメントで指定されている。**cross-YAML sync 検証は本バージョンの scope 外**（ROUGH_PLAN §スコープに含まれず、YAML コメントで運用されているのみ）。将来必要になれば別バージョンで拾う

### 1-5. エントリーポイント統合

`scripts/claude_loop.py` の `main()` に以下を挿入:

```python
def main() -> int:
    args = parse_args()
    resolved = resolve_workflow_value(args.workflow, YAML_DIR)
    validate_auto_args(resolved, args)

    cwd = args.cwd.expanduser().resolve()
    if not cwd.is_dir():
        raise SystemExit(f"Working directory not found: {cwd}")

    # --- 新規挿入 ここから ---
    from claude_loop_lib.validation import validate_startup
    validate_startup(resolved, args, YAML_DIR, cwd)
    # --- 新規挿入 ここまで ---

    uncommitted_status = _resolve_uncommitted_status(args, cwd)
    # ... (既存処理)
```

挿入位置の根拠:
- `resolve_workflow_value` / `validate_auto_args` 後: 検証対象 YAML を確定させた上で走らせる
- `cwd.is_dir()` 後: cwd に依存する category file / category docs dir の検査のため
- `_resolve_uncommitted_status` 前: commit を動かす前に構成エラーを検知する（余計な auto-commit を避ける）

`--dry-run` 時も validation を実行する（構成チェックは実行の有無に関わらず有用。ROUGH_PLAN 期待挙動「最初の step を実行せず終了」と整合）。

### 1-6. ver10.0 §1 条件③の吸収

PHASE7.0 §1 完了条件③「無効な model 名 / 未解決 prompt 参照 / 型不正な設定値は実行前 validation で検出される」は以下で充足する:

| 項目 | 充足手段 |
|---|---|
| 型不正な設定値 | `validate_override_schema()` が `OVERRIDE_STRING_KEYS` を走査し、非空 string であることを確認（既存 `get_steps` / `resolve_defaults` と同等の検査を非 raise 版で実装）|
| 未解決 prompt 参照 | `validate_step_references()` が step.prompt が `/` で始まる場合に `.claude/skills/{name}/SKILL.md` の存在を確認（未存在時は **error**。理由: ROUGH_PLAN §2 の「validation 通過 = 最後まで到達可能」という契約を満たすため。現行 3 YAML の prompt はすべて `.claude/skills/` 配下の SKILL に対応しており、未解決は実行時に確実に失敗する）|
| 無効な model 名 | `validate_override_schema()` が model 値を `MODEL_WHITELIST = {"opus", "sonnet", "haiku"}` 相当と照合（未存在時は **warning**。理由: CLI 側で増えたモデル名に追従する柔軟性を残す）|

**`/wrap_up` 引き継ぎ事項**: PHASE7.0.md「実装進捗」表の §1 を「**実装済**」に更新、§2 を「**実装済**（ver12.0 で充足）」に更新。

### 1-7. 既知の model / effort 値

CLI ヘルプ（ver10.0 IMPLEMENT §2-5(a) で参照済）より:

```python
# scripts/claude_loop_lib/validation.py 冒頭
KNOWN_MODELS: frozenset[str] = frozenset({"opus", "sonnet", "haiku"})
KNOWN_EFFORTS: frozenset[str] = frozenset({"low", "medium", "high", "xhigh", "max"})
```

両者とも warning-only。ユーザが明示的な model エイリアス（`claude-3-5-sonnet-20241022` 等）を指定する可能性を残す。

---

## 2. 実装詳細

### 2-1. `scripts/claude_loop_lib/validation.py`（新規）

#### 2-1-1. モジュール概形

```python
"""Startup-time validation for workflow configurations.

Runs before any step executes. Collects violations across all target
YAMLs and exits with a bulk report on error.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from claude_loop_lib.workflow import (
    ALLOWED_STEP_KEYS,
    ALLOWED_DEFAULTS_KEYS,
    OVERRIDE_STRING_KEYS,
    FULL_YAML_FILENAME,
    QUICK_YAML_FILENAME,
    ISSUE_PLAN_YAML_FILENAME,
)

KNOWN_MODELS: frozenset[str] = frozenset({"opus", "sonnet", "haiku"})
KNOWN_EFFORTS: frozenset[str] = frozenset({"low", "medium", "high", "xhigh", "max"})


@dataclass(frozen=True)
class Violation:
    source: str
    message: str
    severity: str  # "error" | "warning"


def validate_startup(
    resolved: str | Path,
    args: argparse.Namespace,
    yaml_dir: Path,
    cwd: Path,
) -> None:
    """Entry point. Raises SystemExit(2) with bulk error report if any
    error-severity violation is collected. Warnings print to stderr and
    execution proceeds.
    """
    violations: list[Violation] = []
    violations.extend(_validate_category(cwd))
    violations.extend(_validate_executable_and_cwd(cwd))
    yaml_paths = _resolve_target_yamls(resolved, args, yaml_dir)
    for yaml_path in yaml_paths:
        violations.extend(_validate_single_yaml(yaml_path, cwd))
    _report(violations)
```

#### 2-1-2. 個別検証関数

**`_resolve_target_yamls()`**

```python
def _resolve_target_yamls(
    resolved: str | Path,
    args: argparse.Namespace,
    yaml_dir: Path,
) -> list[Path]:
    if resolved == "auto":
        return [
            yaml_dir / ISSUE_PLAN_YAML_FILENAME,
            yaml_dir / FULL_YAML_FILENAME,
            yaml_dir / QUICK_YAML_FILENAME,
        ]
    # resolved は Path オブジェクト（`resolve_workflow_value` が返す）。
    # 念のため Path でラップして isinstance 保証を与える。
    return [resolved if isinstance(resolved, Path) else Path(resolved)]
```

**`_validate_category()`**

```python
def _validate_category(cwd: Path) -> list[Violation]:
    cat_file = cwd / ".claude" / "CURRENT_CATEGORY"
    if not cat_file.is_file():
        # 未設定フォールバック("app")は既存挙動と一致。警告のみ
        return [Violation(
            "category",
            f".claude/CURRENT_CATEGORY not found; defaulting to 'app'.",
            "warning",
        )]
    category = cat_file.read_text(encoding="utf-8").strip()
    if not category:
        return [Violation(
            "category",
            f".claude/CURRENT_CATEGORY is empty.",
            "error",
        )]
    if "/" in category or "\\" in category or category.startswith("."):
        return [Violation(
            "category",
            f"Invalid category name: {category!r}",
            "error",
        )]
    docs_dir = cwd / "docs" / category
    if not docs_dir.is_dir():
        return [Violation(
            "category",
            f"docs/{category}/ directory does not exist.",
            "error",
        )]
    return []
```

「有効なカテゴリ名」の定義: `docs/{name}/` が実在するディレクトリであること。CLAUDE.md で列挙される `app` / `infra` / `cicd` / `util` の hard-code は避ける（将来カテゴリ追加で CLAUDE.md と同期しなくなるリスクを回避）。

**`_validate_executable_and_cwd()`**

```python
def _validate_executable_and_cwd(cwd: Path) -> list[Violation]:
    # cwd は main() で既にチェック済みだが、保険として残す
    violations: list[Violation] = []
    if not cwd.is_dir():
        violations.append(Violation("cwd", f"Not a directory: {cwd}", "error"))
    # executable チェックは YAML ごとに異なる可能性があるため _validate_single_yaml 側で行う
    return violations
```

**`_validate_single_yaml()`**

```python
def _validate_single_yaml(yaml_path: Path, cwd: Path) -> list[Violation]:
    source_prefix = f"yaml/{yaml_path.name}"
    violations: list[Violation] = []

    if not yaml_path.is_file():
        violations.append(Violation(source_prefix, f"File not found: {yaml_path}", "error"))
        return violations

    try:
        raw = yaml_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        violations.append(Violation(source_prefix, f"YAML parse error: {exc}", "error"))
        return violations

    if not isinstance(data, dict):
        violations.append(Violation(
            source_prefix, "Top-level YAML must be a mapping.", "error",
        ))
        return violations

    # command セクションの型検証と executable の事前検査
    command_config = data.get("command")
    if command_config is not None and not isinstance(command_config, dict):
        violations.append(Violation(
            f"{source_prefix}/command",
            "'command' must be a mapping when provided.",
            "error",
        ))
        command_config = None  # 後続の executable 検証をスキップ

    if command_config is None:
        # command 未指定または型不正で skip した場合、executable デフォルト値 "claude" を検査する
        executable = "claude"
    else:
        executable = command_config.get("executable", "claude")
    if isinstance(executable, str) and executable.strip():
        if shutil.which(executable) is None:
            violations.append(Violation(
                f"{source_prefix}/command.executable",
                f"Executable not found on PATH: {executable}",
                "error",
            ))

    # defaults 検証
    violations.extend(_validate_defaults_section(data, source_prefix))

    # steps 検証
    violations.extend(_validate_steps_section(data, source_prefix, cwd))

    return violations
```

**`_validate_defaults_section()`**

ロジックは既存 `resolve_defaults()` と等価だが raise せずに violations に追記:

```python
def _validate_defaults_section(data: dict[str, Any], prefix: str) -> list[Violation]:
    violations: list[Violation] = []
    defaults_config = data.get("defaults")
    if defaults_config is None:
        return []
    if not isinstance(defaults_config, dict):
        violations.append(Violation(
            f"{prefix}/defaults", "'defaults' must be a mapping.", "error",
        ))
        return violations
    unknown = set(defaults_config.keys()) - ALLOWED_DEFAULTS_KEYS
    if unknown:
        violations.append(Violation(
            f"{prefix}/defaults",
            f"Unknown keys: {sorted(unknown)}. Allowed: {sorted(ALLOWED_DEFAULTS_KEYS)}",
            "error",
        ))
    for key in OVERRIDE_STRING_KEYS:
        value = defaults_config.get(key)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            violations.append(Violation(
                f"{prefix}/defaults.{key}",
                "Must be a non-empty string.",
                "error",
            ))
            continue
        violations.extend(_check_value_whitelist(key, value, f"{prefix}/defaults.{key}"))
    return violations
```

**`_validate_steps_section()`**

```python
def _validate_steps_section(data: dict[str, Any], prefix: str, cwd: Path) -> list[Violation]:
    violations: list[Violation] = []
    raw_steps = data.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        violations.append(Violation(
            f"{prefix}/steps", "Must be a non-empty list.", "error",
        ))
        return violations

    skills_dir = cwd / ".claude" / "skills"
    for index, raw_step in enumerate(raw_steps, start=1):
        step_source = f"{prefix}/steps[{index}]"
        if not isinstance(raw_step, dict):
            violations.append(Violation(step_source, "Must be a mapping.", "error"))
            continue

        # prompt
        prompt = raw_step.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            violations.append(Violation(
                f"{step_source}.prompt", "Must be a non-empty string.", "error",
            ))
        else:
            # SKILL reference 解決
            stripped = prompt.strip()
            if stripped.startswith("/"):
                skill_name = stripped.split(None, 1)[0].lstrip("/")
                skill_md = skills_dir / skill_name / "SKILL.md"
                if not skill_md.is_file():
                    violations.append(Violation(
                        f"{step_source}.prompt",
                        f"SKILL '/{skill_name}' not found at {skill_md.relative_to(cwd)}",
                        "error",
                    ))

        # name
        name = raw_step.get("name")
        if name is not None and not isinstance(name, str):
            violations.append(Violation(
                f"{step_source}.name", "Must be a string.", "error",
            ))

        # unknown keys
        unknown = set(raw_step.keys()) - ALLOWED_STEP_KEYS
        if unknown:
            violations.append(Violation(
                step_source,
                f"Unknown keys: {sorted(unknown)}. Allowed: {sorted(ALLOWED_STEP_KEYS)}",
                "error",
            ))

        # override keys
        for key in OVERRIDE_STRING_KEYS:
            if key not in raw_step or raw_step[key] is None:
                continue
            value = raw_step[key]
            if not isinstance(value, str) or not value.strip():
                violations.append(Violation(
                    f"{step_source}.{key}", "Must be a non-empty string.", "error",
                ))
                continue
            violations.extend(_check_value_whitelist(key, value, f"{step_source}.{key}"))

        # continue
        if "continue" in raw_step and raw_step["continue"] is not None:
            if not isinstance(raw_step["continue"], bool):
                violations.append(Violation(
                    f"{step_source}.continue", "Must be a boolean.", "error",
                ))

    return violations
```

**`_check_value_whitelist()`**

```python
def _check_value_whitelist(key: str, value: str, source: str) -> list[Violation]:
    if key == "model" and value not in KNOWN_MODELS:
        return [Violation(
            source,
            f"Unknown model {value!r}. Known: {sorted(KNOWN_MODELS)}",
            "warning",
        )]
    if key == "effort" and value not in KNOWN_EFFORTS:
        return [Violation(
            source,
            f"Unknown effort {value!r}. Known: {sorted(KNOWN_EFFORTS)}",
            "warning",
        )]
    return []
```

**`_report()`**

```python
def _report(violations: list[Violation]) -> None:
    if not violations:
        return
    errors = [v for v in violations if v.severity == "error"]
    warnings = [v for v in violations if v.severity == "warning"]

    for v in warnings:
        print(f"VALIDATION WARNING [{v.source}]: {v.message}", file=sys.stderr)

    if not errors:
        return

    print("", file=sys.stderr)
    print(f"Startup validation failed ({len(errors)} error(s)):", file=sys.stderr)
    for v in errors:
        print(f"  [{v.source}] {v.message}", file=sys.stderr)
    raise SystemExit(2)
```

（`sys` は §2-1-1 のモジュール概形の import リストに追加済み）

#### 2-1-3. 公開 API

- `validate_startup(resolved, args, yaml_dir, cwd) -> None` — 唯一の公開関数。副作用として SystemExit を投げる
- `Violation` dataclass / `KNOWN_MODELS` / `KNOWN_EFFORTS` もテスト import 用に公開（module-level 定義で到達可能）

### 2-2. `scripts/claude_loop.py` — `validate_startup()` の呼び出し

#### 変更点 (a): import 追加

```python
from claude_loop_lib.validation import validate_startup
```

（§1-5 ではインラインインポートで示したが、他モジュール同様トップレベルでの import に改める。循環依存は発生しない: `validation` は `workflow` を import するが `workflow` は `validation` を import しない）

#### 変更点 (b): `main()` への挿入

§1-5 に示したとおり `cwd.is_dir()` チェック後、`_resolve_uncommitted_status()` 前に挿入。

#### 変更点 (c): `_execute_yaml()` 内の `shutil.which` は**維持**

`_execute_yaml()` 内 L253-254 の `shutil.which(executable)` チェックは残す（多段防御）。validation 側で同等チェックをしてもランタイム段階での safety net として残置。

### 2-3. 既存 3 本の YAML の整合性事前確認

`validate_startup()` を実装後、既存 YAML が全て pass することを手動実行で確認する:

```bash
python scripts/claude_loop.py --workflow auto --dry-run
python scripts/claude_loop.py --workflow full --dry-run
python scripts/claude_loop.py --workflow quick --dry-run
```

いずれも validation を通過すべき。もし fail した場合はそれ自体が ROUGH_PLAN §リスク「既存 3 本の workflow YAML が schema 違反として検出される可能性」の顕在化であり、当該 YAML を修正する（同一コミット範囲内）。

想定値に基づく事前評価:
- 3 本の `defaults` / `steps` は現在 `model`, `effort`, `continue`, `prompt`, `name` のみ使用 → `ALLOWED_*` 集合に収まる
- 使用中の model 値は `opus` / `sonnet` のみ → `KNOWN_MODELS` に含まれる
- 使用中の effort 値は `high` / `medium` / `low` のみ → `KNOWN_EFFORTS` に含まれる
- 全 step の `/prompt` は `.claude/skills/{name}/` に対応ディレクトリが存在（§探索で確認済）
- `command.executable: claude` → `shutil.which("claude")` は開発環境で解決する想定（実開発者側の責任）

**潜在リスク**: CI/GitHub Actions 等 `claude` CLI が未インストールの環境で validation 呼び出しが走ると error を吐く。ただし `claude_loop.py` 自体が `claude` CLI を呼ぶため、CI では元々動かせない前提であり、本 validation 追加による新たな CI 破壊は発生しない。

### 2-4. `scripts/tests/test_validation.py`（新規）

新規テストファイル。既存テストは修正不要。

#### クラス構成

| クラス | ケース数 | カバレッジ |
|---|---|---|
| `TestValidateCategory` | 5 | CURRENT_CATEGORY 欠如 / 空 / 不正文字 / docs dir 欠如 / 正常 |
| `TestValidateSingleYamlShape` | 6 | ファイル欠如 / parse 失敗 / 非 dict / defaults 非 dict / steps 非 list / 正常 |
| `TestValidateStepSchema` | 8 | prompt 欠如 / prompt 非 str / unknown key / override 型不正 / continue 型不正 / name 非 str / 複数違反の集約 / 正常 |
| `TestValidateOverrideWhitelist` | 4 | 未知 model / 未知 effort（いずれも warning） / 既知 model / 既知 effort |
| `TestValidateStepReferences` | 4 | 存在しない SKILL / 存在する SKILL / `/` 非始まり prompt / prompt 後続引数付き（`/foo bar` → `foo` で lookup） |
| `TestValidateStartupAggregation` | 5 | 3 YAML すべて正常 / 1 YAML だけ parse 失敗（他検証継続） / step[2] の違反が step[5] と並列収集 / warning のみで SystemExit しない / error があると exit code 2 |
| `TestValidateStartupExistingYamls` | 3 | `claude_loop.yaml` / `_quick.yaml` / `_issue_plan.yaml` を実ファイルで validate → violations が空 / 空ではない場合は fail させる（regression guard） |

#### テスト実装ガイド

- `setUp` で `tempfile.TemporaryDirectory()` を使い、`.claude/CURRENT_CATEGORY` / `.claude/skills/<name>/SKILL.md` / `docs/<cat>/` の最小構造を用意する
- `TestValidateStartupExistingYamls` のみ repo root の実体を使う。`_bootstrap.py` は `sys.path` 操作のための副作用 import として使い、リポジトリルートは `from claude_loop import DEFAULT_WORKING_DIRECTORY` で取得する（既存 `test_claude_loop_integration.py` の慣行と整合）
- `validate_startup()` を直接呼び、`SystemExit` の有無と `violations` 相当の内部状態（`_validate_single_yaml` を独立に呼んで list を取得）で検証する
- whitelist warning は stderr capture (`capsys` / `unittest.mock.patch('sys.stderr')`) で確認

#### テスト実行

```bash
python -m unittest tests.test_validation -v
python -m unittest discover tests -v   # 全テスト
```

既存ケース（ver11.1 時点 130 件弱）はそのまま pass するはず。本バージョンでは **新規ケースは約 35 件** 追加される見込み。

### 2-5. `scripts/README.md` の更新

#### 追加する節

「YAML ワークフロー仕様」節の後、**「起動前 validation」節を新設**:

```markdown
### 起動前 validation

`scripts/claude_loop.py` は step 1 を実行する前に以下を検査する。1 件でも `error` があれば exit code 2 で終了する。

| 検査項目 | 重大度 |
|---|---|
| `.claude/CURRENT_CATEGORY` の存在・中身 / `docs/{category}/` の存在 | error (欠如時は警告→`app` フォールバック) |
| `command.executable` が PATH 上で解決できること (`shutil.which`) | error |
| YAML の存在・parse 成功・top-level mapping | error |
| `defaults` / `steps[]` のキー集合が許容範囲内 (`model` / `effort` / `system_prompt` / `append_system_prompt` / `name` / `prompt` / `args` / `continue`) | error |
| override キーの型（非空 string） / `continue` の型（bool） | error |
| `model` 値が既知セット (`opus` / `sonnet` / `haiku`) に含まれること | **warning** |
| `effort` 値が既知セット (`low` / `medium` / `high` / `xhigh` / `max`) に含まれること | **warning** |
| step.prompt の先頭が `/` の場合、`.claude/skills/<name>/SKILL.md` が存在すること | error |
| `command` セクションが指定された場合、mapping であること | error |

`--workflow auto` の場合、phase 1 (`claude_loop_issue_plan.yaml`) と phase 2 候補 2 本（`claude_loop.yaml` / `claude_loop_quick.yaml`）を**全て事前に検証**する。ROUGH_PLAN.md の `workflow:` 値にかかわらず、validation 通過後は最後まで到達可能なことを保証する。

エラーは可能な範囲で一括収集されて末尾に列挙される。例えば YAML A が parse 失敗しても、YAML B 内の step typo はそのまま報告される。
```

`--dry-run` 時も validation は実行される旨を追記。

#### テストケース件数の更新

既存 README 内に「現状 N 件」記述があれば `+35` 相当に差し替える（ver10.0 IMPLEMENT §5-5 同様、`/wrap_up` 段階で確定値に置換）。

### 2-6. `scripts/USAGE.md`

存在する場合、「起動時挙動」節に 1 行「step 1 実行前に validation が走る（失敗時は exit code 2）」を追記。存在しなければ作成不要。

---

## 3. テスト計画

### 3-1. 既存テスト

- `tests/test_workflow.py` / `test_commands.py` / `test_claude_loop_integration.py` / `test_claude_loop_cli.py` は **無改変で pass** することを必須
- 既存挙動（`get_steps` / `resolve_defaults` の raise タイミング）は保持される

### 3-2. 新規テスト

§2-4 参照（7 クラス、計約 35 ケース）。

### 3-3. 統合 smoke test

`test_claude_loop_integration.py` に `TestStartupValidationIntegration` を 1 クラス追加し、`main()` 相当フローをモックして `validate_startup` が fail した場合に `_execute_yaml` が呼ばれないことを assert する（1〜2 ケース）。

---

## 4. 実装順序（推奨）

1. `scripts/claude_loop_lib/validation.py` の雛形を作成（関数シグネチャと `Violation` のみ、本体 pass）
2. `tests/test_validation.py` の `TestValidateCategory` / `TestValidateStepSchema` を先に書き、TDD で `_validate_category` / `_validate_steps_section` を実装
3. `_validate_single_yaml` 実装 → `TestValidateSingleYamlShape` / `TestValidateStepReferences` / `TestValidateOverrideWhitelist` で確認
4. `validate_startup` の top-level 実装 → `TestValidateStartupAggregation` / `TestValidateStartupExistingYamls` で確認
5. `scripts/claude_loop.py` の `main()` に呼び出し挿入
6. `test_claude_loop_integration.py` に smoke test 追加
7. `scripts/README.md` 更新
8. `python -m unittest discover tests -v` で全テスト pass 確認 → 単一コミット
9. 手動確認: `python scripts/claude_loop.py --workflow auto --dry-run` が validation を通過することを確認

---

## 5. コミット分割案（`/imple_plan` 引き継ぎ用）

単一コミットとする:

**`feat(util ver12.0): PHASE7.0 §2 startup validation`**

- `scripts/claude_loop_lib/validation.py`（新規）
- `scripts/claude_loop.py`（`main()` への呼び出し挿入、import 追加）
- `scripts/tests/test_validation.py`（新規）
- `scripts/tests/test_claude_loop_integration.py`（smoke test 追加）
- `scripts/README.md`（起動前 validation 節追加）

PHASE7.0.md「実装進捗」表の §1 / §2 状態更新は `/wrap_up` の責務として持ち越し。

---

## 6. リスク・不確実性

### 6-1. `shutil.which` による executable チェックの OS 依存性

- Windows / Linux / macOS で `shutil.which` の挙動は同等だが、**CI 環境（`claude` CLI 未インストール）では error が発生する**
- 影響評価: `scripts/claude_loop.py` 自体が `claude` CLI を要求するため CI で本 script を実行する前提は元々ない。validation の追加によって CI 要件が変わらない
- **対策**: `test_validation.py` は `shutil.which` を `unittest.mock.patch` で mock し、CI でも通るようにする

### 6-2. SKILL 解決の `/prompt args` パース

- `step.prompt` は `"/split_plan"` の他 `"/split_plan some-arg"` のように引数を持つ可能性がある（現状の 3 YAML では引数付き prompt は存在しない）
- 実装では `prompt.strip().split(None, 1)[0].lstrip("/")` で最初のトークンを SKILL 名として抽出
- 引数の意味的 validation は本バージョンでは扱わない（Claude CLI に委ねる）

### 6-3. warning と error の境界線

- 「未知 model」「未知 effort」「未存在 SKILL」を warning にするか error にするかで挙動が大きく変わる
- 本 IMPLEMENT では **warning** としたが、ROUGH_PLAN §2 期待挙動「1 件でも重大な不整合があれば最初の step を実行せず終了する」の「重大な」の解釈に幅がある
- 選択根拠:
  - model / effort: CLI が新 alias を追加する可能性があり、warning のほうが柔軟
  - SKILL: 現行 3 YAML の全 step prompt は `.claude/skills/` 配下の SKILL に対応しており、未解決は実行時に確実に失敗する。ROUGH_PLAN §2「validation 通過 = 最後まで到達可能」という契約を満たすため **error** として扱う（plan_review_agent 指摘を反映）
  - 型不正・unknown key・YAML parse 失敗・`command` 非 dict: これらは **error** として扱う（フェイルファースト効果が高い）

### 6-4. 既存 3 YAML の regression guard

- `TestValidateStartupExistingYamls` は実ファイルをロードするため、将来 YAML 編集で validation が通らなくなるとテスト失敗する
- これは **意図した挙動**（YAML 編集と validation ルール変更のセットで破壊されないよう保証する）
- 副作用として、YAML 更新時にテストも併せて調整する必要がある点は README に明記

### 6-5. `OVERRIDE_STRING_KEYS` 等の再 import 依存

- `validation.py` が `workflow.py` から `ALLOWED_STEP_KEYS` / `ALLOWED_DEFAULTS_KEYS` / `OVERRIDE_STRING_KEYS` を import することで、片方を変更すれば両方が追随する
- 循環 import は起きない（`workflow.py` は `validation.py` を import しない）
- このコンベンションを README「拡張ガイド」節に 1 文追記する

### 6-6. エラーメッセージ I18N

- エラー文言は英語で統一（既存 `workflow.py` と整合）。日本語混在は避ける

### 6-7. Windows パス表記

- `skill_md.relative_to(cwd)` は Windows でも POSIX 形式で表示されない可能性があるが、エラーメッセージとしての可読性は十分

---

## 7. plan_review_agent への論点

レビュー観点として以下を明示的に尋ねる:

1. **warning / error の境界線**（§6-3）は妥当か。特に「未知 model」「未解決 SKILL」を warning にした判断
2. **`--workflow auto` で phase 2 候補 2 本を両方検証する設計**（§1-4）は過剰か。phase 1 のみの検証に絞るほうが良いか
3. **独立モジュール (`validation.py`) + 既存 raise 処理の温存**（§0 / §1-1 ④）は責務重複が問題になるか。`workflow.py` を refactor して collect-mode に統一したほうが良いか
4. **`docs/{category}/` 存在でカテゴリ有効性を判定する**（§2-1-2 `_validate_category`）設計は妥当か。CLAUDE.md 列挙値の hard-code の方が安全か
5. **`validate_startup` の SystemExit exit code (2)** は既存 SystemExit (1) と区別する意図だが、`_resolve_uncommitted_status` 等他所の `raise SystemExit` と整合しているか
6. **既存 YAML の regression guard test** で実ファイルをロードする是非（§6-4）
