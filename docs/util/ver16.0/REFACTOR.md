---
workflow: full
source: master_plan
---

# ver16.0 REFACTOR — `research` workflow 追加のための事前整理

## 目的

PHASE8.0 §1 で `scripts/claude_loop_lib/workflow.py` と `validation.py` に 6 つ目の workflow 値 `research` を追加する前に、**値ごとのリテラル分岐を 1 箇所のレジストリに集約しておく**。これにより `research` 追加時の diff を「レジストリに 1 行追加 + YAML 1 ファイル新設」に抑え、将来の workflow 追加（§2 deferred execution / §3 cost 計測で追加の可能性）にも耐える形にする。

handoff で指定された「過剰整理は避ける」方針に従い、**本版で重複する箇所のみ**を先行整理する。`command`/`defaults`/`steps` 検証ロジックなど、workflow 値とは独立した部分には手を入れない。

## 対象と非対象

**対象（本 REFACTOR 実施）**:

- `scripts/claude_loop_lib/workflow.py` の workflow 値 → YAML ファイル名マッピング
- `scripts/claude_loop_lib/validation.py` の `_resolve_target_yamls`（auto モード時の YAML 列挙）
- `scripts/claude_loop.py` の `_read_workflow_kind`（ROUGH_PLAN.md frontmatter `workflow:` 許容値）

**非対象（IMPLEMENT.md で扱う・または本版では触らない）**:

- 新 YAML `claude_loop_research.yaml` の新規作成（IMPLEMENT.md）
- 新 SKILL `research_context` / `experiment_test` の新規作成（IMPLEMENT.md）
- `claude_loop.py` の `_run_auto` 関数における phase2 分岐（IMPLEMENT.md）
- `build_command` / feedback / session 継続など workflow 値と独立したロジック

## Step 1. `workflow.py` に workflow 値レジストリを導入

現状（`scripts/claude_loop_lib/workflow.py:12-55`）:

```python
FULL_YAML_FILENAME = "claude_loop.yaml"
QUICK_YAML_FILENAME = "claude_loop_quick.yaml"
ISSUE_PLAN_YAML_FILENAME = "claude_loop_issue_plan.yaml"
SCOUT_YAML_FILENAME = "claude_loop_scout.yaml"
QUESTION_YAML_FILENAME = "claude_loop_question.yaml"

RESERVED_WORKFLOW_VALUES = ("auto", "full", "quick", "scout", "question")

def resolve_workflow_value(value: str, yaml_dir: Path) -> str | Path:
    if value == "auto":
        return "auto"
    if value == "full":
        return yaml_dir / FULL_YAML_FILENAME
    if value == "quick":
        return yaml_dir / QUICK_YAML_FILENAME
    if value == "scout":
        return yaml_dir / SCOUT_YAML_FILENAME
    if value == "question":
        return yaml_dir / QUESTION_YAML_FILENAME
    return Path(value).expanduser()
```

変更後:

```python
FULL_YAML_FILENAME = "claude_loop.yaml"
QUICK_YAML_FILENAME = "claude_loop_quick.yaml"
ISSUE_PLAN_YAML_FILENAME = "claude_loop_issue_plan.yaml"
SCOUT_YAML_FILENAME = "claude_loop_scout.yaml"
QUESTION_YAML_FILENAME = "claude_loop_question.yaml"

# workflow 値 → YAML ファイル名（"auto" は sentinel のため含めない）
WORKFLOW_YAML_FILES: dict[str, str] = {
    "full": FULL_YAML_FILENAME,
    "quick": QUICK_YAML_FILENAME,
    "scout": SCOUT_YAML_FILENAME,
    "question": QUESTION_YAML_FILENAME,
}

RESERVED_WORKFLOW_VALUES: tuple[str, ...] = ("auto",) + tuple(WORKFLOW_YAML_FILES)

def resolve_workflow_value(value: str, yaml_dir: Path) -> str | Path:
    """Resolve the --workflow CLI value.

    - "auto" -> returns "auto" (sentinel; caller handles two-phase execution)
    - registered name (full/quick/scout/question/...) -> yaml_dir / filename
    - other (path-like) -> Path(value).expanduser()
    """
    if value == "auto":
        return "auto"
    filename = WORKFLOW_YAML_FILES.get(value)
    if filename is not None:
        return yaml_dir / filename
    return Path(value).expanduser()
```

**挙動互換性**: `RESERVED_WORKFLOW_VALUES` の要素順は既存と一致（`auto` が先頭、残りの挿入順は `dict` リテラル順）。外部公開定数（`FULL_YAML_FILENAME` など）は維持するため、既存 import（`validation.py` の `ISSUE_PLAN_YAML_FILENAME` / `FULL_YAML_FILENAME` / `QUICK_YAML_FILENAME` や `claude_loop.py` の同一定数 import）は変更不要。

## Step 2. `validation.py` の `_resolve_target_yamls` を見直し

現状（`scripts/claude_loop_lib/validation.py:65-76`）:

```python
def _resolve_target_yamls(resolved, args, yaml_dir) -> list[Path]:
    if resolved == "auto":
        return [
            yaml_dir / ISSUE_PLAN_YAML_FILENAME,
            yaml_dir / FULL_YAML_FILENAME,
            yaml_dir / QUICK_YAML_FILENAME,
        ]
    return [resolved if isinstance(resolved, Path) else Path(resolved)]
```

変更後:

```python
def _resolve_target_yamls(resolved, args, yaml_dir) -> list[Path]:
    # auto モードは /issue_plan を phase1 に、phase2 で選択される候補 YAML 全てを
    # 事前検証する（起動時に全候補のスキーマ不備を一括検出するため）。
    if resolved == "auto":
        return [yaml_dir / name for name in AUTO_TARGET_YAMLS]
    return [resolved if isinstance(resolved, Path) else Path(resolved)]
```

同ファイル冒頭に以下を追加（`workflow.py` 側で定義してそれを import する方針に統一）:

```python
# workflow.py 側:
AUTO_TARGET_YAMLS: tuple[str, ...] = (
    ISSUE_PLAN_YAML_FILENAME,
    FULL_YAML_FILENAME,
    QUICK_YAML_FILENAME,
)
```

そして `validation.py` の import を以下に変更:

```python
from claude_loop_lib.workflow import (
    ALLOWED_DEFAULTS_KEYS,
    ALLOWED_STEP_KEYS,
    AUTO_TARGET_YAMLS,
    FULL_YAML_FILENAME,
    ISSUE_PLAN_YAML_FILENAME,
    OVERRIDE_STRING_KEYS,
    QUICK_YAML_FILENAME,
)
```

**意図**: `AUTO_TARGET_YAMLS` を IMPLEMENT.md 側で `RESEARCH_YAML_FILENAME` 追加時に 1 行増やすだけで対応できるようにする（`scout` / `question` は auto 非対象のまま据え置き）。

## Step 3. `claude_loop.py` の `_read_workflow_kind` 許容値

現状（`scripts/claude_loop.py:207-228`）:

```python
def _read_workflow_kind(rough_plan: Path) -> str:
    ...
    value = fm.get("workflow")
    if value not in ("quick", "full"):
        print(f"WARNING: invalid workflow={value!r} ...; falling back to 'full'.")
        return "full"
    return value
```

**本 REFACTOR では触らない**。理由: 許容値拡張は `research` 追加と一体の変更であり、`research` 追加前に先行して許容値だけ広げても意味がなく、逆に「`research` に落ちる後続 YAML が未整備」という一時的な整合崩れを生むため。IMPLEMENT.md で `claude_loop_research.yaml` 作成と同時に許容値を `("quick", "full", "research")` へ拡張する。

ここで本 REFACTOR の対象は Step 1〜Step 2 のみ。

## Step 4. テスト（本 REFACTOR 範囲のみ）

- `scripts/tests/test_claude_loop_cli.py` に `resolve_workflow_value` の既存 5 値（auto / full / quick / scout / question）を網羅する unit test が既にあるか確認し、無ければ追加（`RESERVED_WORKFLOW_VALUES` を逐次走査して `yaml_dir / filename` が返ることを確認）
- 既存テストは本 REFACTOR で落ちてはならない（全 green 維持が前提）

## ロールバック容易性

- Step 1 / Step 2 いずれも純粋な内部リファクタで、公開 API（関数シグネチャ・戻り値）を変えない
- 失敗時は `git revert` 1 コミットで戻せる粒度を維持（REFACTOR コミットは 1 個にまとめる）

## コミット方針

- REFACTOR.md 実施は **1 コミット** でまとめる: `refactor(ver16.0): workflow 値レジストリ化（research 追加の前段）`
- IMPLEMENT.md のコミットとは別にする（レビュー時に REFACTOR 部分のみを比較できるよう）
