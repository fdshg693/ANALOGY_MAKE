# IMPLEMENT: util ver3.2

## 概要

`claude_loop.py` に、ユーザーが `FEEDBACKS/` ディレクトリに配置した Markdown ファイルを読み込み、該当ステップの `--append-system-prompt` に注入する機能を追加する。

## FB ファイルフォーマット

```markdown
---
step: split_plan
---

ここにフィードバック内容を記述
```

- `step` フィールド: 文字列またはリスト（例: `step: [split_plan, imple_plan]`）
- `step` フィールド省略時: 全ステップに注入（キャッチオール）
- 本文: フィードバック内容（プロンプトに注入される）

## ディレクトリ構成

```
FEEDBACKS/
├── fix_typo.md       # 未消費（ステップ実行前に読み込まれる）
├── improve_ux.md     # 未消費
└── done/             # 消費済み（成功時にここに移動）
    └── old_fb.md
```

- `FEEDBACKS/` は `--cwd`（デフォルト: プロジェクトルート）からの相対パス
- `done/` サブディレクトリに移動して履歴を保持（削除ではなく移動）
- `.gitignore` への追加は本バージョンでは行わない

## 新規関数

### 1. `parse_feedback_frontmatter(content: str) -> tuple[list[str] | None, str]`

Markdown ファイルの YAML frontmatter を解析し、対象ステップ名と本文を返す。

```python
def parse_feedback_frontmatter(content: str) -> tuple[list[str] | None, str]:
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, content

    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            frontmatter_str = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1:]).strip()
            break
    else:
        return None, content

    try:
        frontmatter = yaml.safe_load(frontmatter_str)
    except yaml.YAMLError:
        return None, content

    if not isinstance(frontmatter, dict):
        return None, body

    step = frontmatter.get("step")
    if step is None:
        return None, body
    if isinstance(step, str):
        return [step], body
    if isinstance(step, list) and all(isinstance(s, str) for s in step):
        return step, body
    return None, body
```

- frontmatter なし → `(None, 全文)` = 全ステップ対象
- `step` フィールドなし → `(None, 本文)` = 全ステップ対象
- `step` が文字列 → `([step], 本文)`
- `step` がリスト → `(step, 本文)`
- YAML パースエラー → `(None, 全文)` = 全ステップ対象（無視せず注入）

### 2. `load_feedbacks(feedbacks_dir: Path, step_name: str) -> list[tuple[Path, str]]`

指定ステップに該当する FB ファイルを検出し、`(ファイルパス, 本文)` のリストを返す。

```python
def load_feedbacks(feedbacks_dir: Path, step_name: str) -> list[tuple[Path, str]]:
    if not feedbacks_dir.is_dir():
        return []

    results: list[tuple[Path, str]] = []
    for md_file in sorted(feedbacks_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        step_names, body = parse_feedback_frontmatter(content)
        if not body:
            continue
        if step_names is None or step_name in step_names:
            results.append((md_file, body))
    return results
```

- `feedbacks_dir` が存在しない → 空リスト（エラーにしない）
- `done/` 配下は `*.md` の glob が直下のみのため自動的に除外
- `sorted()` でファイル名順に安定した注入順を保証
- 本文が空の FB ファイルはスキップ

### 3. `consume_feedbacks(files: list[Path], done_dir: Path) -> None`

消費済み FB ファイルを `done/` に移動する。

```python
def consume_feedbacks(files: list[Path], done_dir: Path) -> None:
    if not files:
        return
    done_dir.mkdir(parents=True, exist_ok=True)
    for file_path in files:
        shutil.move(str(file_path), str(done_dir / file_path.name))
```

- `shutil.move()` を使用（Windows でのクロスデバイス対応）
- `shutil` は既にインポート済み
- 同名ファイルが `done/` に存在する場合は上書き

## 既存関数の変更

### 4. `build_command()` — `feedbacks` パラメータ追加

```python
def build_command(
    executable: str,
    prompt_flag: str,
    common_args: list[str],
    step: dict[str, Any],
    log_file_path: str | None = None,
    auto_mode: bool = False,
    feedbacks: list[str] | None = None,  # 追加
) -> list[str]:
    # ... 既存ロジック ...
    if feedbacks:
        feedback_section = "## User Feedback\n\n" + "\n\n---\n\n".join(feedbacks)
        system_prompts.append(feedback_section)
    # ... 残りは同じ ...
```

- `feedbacks` は本文のリスト（`load_feedbacks` の戻り値から抽出）
- `## User Feedback` ヘッダー付きで、複数 FB は `---` 区切り
- 既存の `system_prompts` リストに追加し、`\n\n` で結合される

### 5. `_run_steps()` — FB 読み込み・消費ロジック追加

ステップ実行ループ内で、`build_command()` 呼び出し前に FB を読み込み、成功後に消費する。

```python
# _run_steps() 内:
# feedbacks_dir はループ外で1回だけ生成（値が変わらないため）
feedbacks_dir = cwd / "FEEDBACKS"

for step, absolute_index in step_iter:
    ran_any_step = True

    # --- Load feedbacks ---
    matched = load_feedbacks(feedbacks_dir, step["name"])
    feedback_contents = [content for _, content in matched]
    feedback_files = [path for path, _ in matched]

    log_file_path = str(log_path) if tee is not None else None
    command = build_command(
        executable, prompt_flag, common_args, step,
        log_file_path, auto_mode,
        feedbacks=feedback_contents or None,
    )

    # --- (既存のステップ実行ロジック) ---

    if dry_run:
        continue  # dry-run 時は FB の読み込みのみ、消費はしない

    # ... ステップ実行 ...

    if exit_code != 0:
        # 既存: return exit_code で関数を抜けるため、
        # FB は消費されず、リトライ時に再注入される
        ...

    # 成功後（completed_count += 1 の直前）:
    if feedback_files:
        consume_feedbacks(feedback_files, feedbacks_dir / "done")

    completed_count += 1
```

- `feedbacks_dir` はループ外で1回だけ生成
- 失敗時は `return exit_code` で関数を抜けるため、`consume_feedbacks` に到達しない
- `dry_run` 時は `continue` で消費をスキップ（読み込みのみ実行）
- `--max-loops > 1` 時: 1ループ目で FB が `done/` に移動されるため、2ループ目以降は同じ FB は注入されない（設計上意図的）

## テスト計画

`tests/test_claude_loop.py` に以下のテストクラスを追加する。

### TestParseFeedbackFrontmatter

| テスト | 内容 |
|---|---|
| `test_with_step_string` | `step: split_plan` → `(["split_plan"], body)` |
| `test_with_step_list` | `step: [a, b]` → `(["a", "b"], body)` |
| `test_without_frontmatter` | frontmatter なし → `(None, content)` |
| `test_without_step_field` | frontmatter あり・step なし → `(None, body)` |
| `test_invalid_yaml` | 不正な YAML → `(None, content)` |
| `test_empty_body` | frontmatter のみ → `(step_names, "")` |

### TestLoadFeedbacks

| テスト | 内容 |
|---|---|
| `test_no_directory` | ディレクトリ不在 → 空リスト |
| `test_empty_directory` | 空ディレクトリ → 空リスト |
| `test_matching_step` | ステップ名一致 → FB 返却 |
| `test_non_matching_step` | ステップ名不一致 → 空リスト |
| `test_catch_all` | step フィールドなし → 全ステップで返却 |
| `test_done_excluded` | `done/` 配下は除外 |
| `test_sorted_order` | ファイル名順で返却 |

### TestConsumeFeedbacks

| テスト | 内容 |
|---|---|
| `test_moves_to_done` | ファイルが `done/` に移動される |
| `test_creates_done_dir` | `done/` ディレクトリが自動作成される |
| `test_empty_list` | 空リスト → 何もしない |
| `test_overwrites_existing` | `done/` に同名ファイルが存在する場合に上書きされる |

### TestBuildCommandWithFeedbacks

| テスト | 内容 |
|---|---|
| `test_feedbacks_injected` | FB がシステムプロンプトに含まれる |
| `test_multiple_feedbacks` | 複数 FB が `---` 区切りで結合 |
| `test_no_feedbacks` | `None` → 既存動作と同じ |

## リスク・不確実性

- **`shutil.move()` の同名ファイル上書き**: `done/` に同名ファイルが既に存在する場合、上書きされる。ファイル名の一意性はユーザーの責任とする
- **大量 FB ファイル時のプロンプト肥大化**: FB が多数ある場合、`--append-system-prompt` が非常に長くなる可能性がある。本バージョンではサイズ制限は設けない（実運用で問題が発生した場合に対応）
