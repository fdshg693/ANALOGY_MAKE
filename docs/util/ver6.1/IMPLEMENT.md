# ver6.1 IMPLEMENT — parse_frontmatter 共通化

## 方針

`scripts/claude_loop_lib/frontmatter.py` を新設し、`parse_frontmatter(text: str) -> dict | None` を単一の真実源にする。既存の 2 箇所（`issue_status.py` / `feedbacks.py`）はこの関数を呼ぶ薄いラッパーにリライトする。

## 1. 新規 `scripts/claude_loop_lib/frontmatter.py`

### 1-1. 公開 API

```python
def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """
    Parse a YAML frontmatter block from the head of text.

    Returns (frontmatter, body):
      - frontmatter: dict if the block exists, is closed by `---`, is valid YAML,
                     and parses to a mapping. None otherwise.
      - body: text after the closing `---`, or the original text if no frontmatter.

    Fallback rules (all return (None, <appropriate body>)):
      - No leading `---` line → body = text
      - Missing closing `---` → body = text
      - YAML parse error → body = text (unparseable content treated as no fm)
      - YAML parses to non-dict (list/scalar) → body = text after closer
    """
```

**戻り値を tuple にする理由**: 現行 `feedbacks.py` は body も必要、`issue_status.py` は dict のみ必要。tuple で両方返しておけば呼び出し側でどちらを捨ててもよく、共通化の粒度として自然。

### 1-2. 実装スケッチ

```python
from __future__ import annotations

import yaml


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, text

    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            fm_str = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1:]).strip()
            break
    else:
        return None, text

    try:
        fm = yaml.safe_load(fm_str)
    except yaml.YAMLError:
        return None, text

    if not isinstance(fm, dict):
        return None, body

    return fm, body
```

行数目安: 25 行程度（docstring 込み）。

## 2. `scripts/claude_loop_lib/feedbacks.py` の書き換え

`parse_feedback_frontmatter` は高水準の「step フィールド解釈」を残したまま、下位の YAML 抽出だけを `parse_frontmatter` に委ねる。

```python
from claude_loop_lib.frontmatter import parse_frontmatter


def parse_feedback_frontmatter(content: str) -> tuple[list[str] | None, str]:
    fm, body = parse_frontmatter(content)
    if fm is None:
        return None, body  # parse_frontmatter 側で cases 1-3 は body=content、case 4 は strip 済み body を返す

    step = fm.get("step")
    if step is None:
        return None, body
    if isinstance(step, str):
        return [step], body
    if isinstance(step, list) and all(isinstance(s, str) for s in step):
        return step, body
    return None, body
```

### 挙動同一性の注意点

現行 `parse_feedback_frontmatter` は以下 4 パターンで戻り値が分岐:

| 入力 | 現行 body 戻り値 | 新 `parse_frontmatter` 戻り body | 一致 |
|---|---|---|---|
| 先頭 `---` 無し | `content`（非 strip） | `text`（= `content`、非 strip） | ✅ |
| 閉じ `---` 無し | `content`（非 strip） | `text`（= `content`、非 strip） | ✅ |
| YAML パース失敗 | `content`（非 strip） | `text`（= `content`、非 strip） | ✅ |
| dict 以外にパース（list 等） | `body`（strip 済み） | `body`（strip 済み） | ✅ |

`parse_frontmatter` 側の実装スケッチ（§1-2）で、YAML パース失敗時は `return None, text`（非 strip のオリジナル）、dict 以外パース時は `return None, body`（strip 済みの閉じ後テキスト）、と**明示的に分岐済み**。よってラッパー側は `return None, body` の一行で上記 4 パターン全てを現行と一致させられる。

`tests/test_claude_loop.py` の `TestParseFeedbackFrontmatter` が全パターンをカバー済みのため、リファクタリング後もこれを pass することで挙動同一性を保証する。

## 3. `scripts/issue_status.py` の書き換え

既存の `parse_frontmatter(path: Path) -> tuple[str, str]` は「ファイルパスを受け取り `(status, assigned)` を返す」という独自シグネチャ。`frontmatter.py` 側の `parse_frontmatter(text: str) -> tuple[dict | None, str]` と名前衝突するため、`issue_status.py` 側の関数は **`_extract_status_assigned` にリネーム** してから中身を共通関数呼び出しに差し替える。

```python
from claude_loop_lib.frontmatter import parse_frontmatter


def _extract_status_assigned(path: Path) -> tuple[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        warn(f"{path}: read failed ({exc})")
        return "raw", "human"

    fm, _ = parse_frontmatter(text)
    if fm is None:
        return "raw", "human"

    status = str(fm.get("status", "raw"))
    assigned = str(fm.get("assigned", "human"))

    if status not in VALID_STATUS:
        warn(f"{path}: unknown status '{status}'")
    if assigned not in VALID_ASSIGNED:
        warn(f"{path}: unknown assigned '{assigned}'")
    if (status, assigned) not in VALID_COMBOS:
        warn(f"{path}: invalid combo status={status}, assigned={assigned}")

    return status, assigned
```

`collect_priority` 内の `parse_frontmatter(md_file)` 呼び出しを `_extract_status_assigned(md_file)` に置換。

### 警告出力の差異

現行の `issue_status.py` は「YAML パース失敗時」に `warn(f"{path}: YAML parse failed ({exc})")` を出す。共通化後は `parse_frontmatter` 側が YAML エラーを握り潰して `(None, text)` を返すため、この警告が消える。

**対応**: 共通関数から警告を出すと責務が混ざるため、`issue_status.py` 側で `fm is None` かつ「先頭 `---` あり」の場合を判定して警告するヘルパーを追加する…ほどの価値はない。**警告は落ちてよい**（frontmatter 破損は `raw / human` にフォールバックされる運用で既に十分な可視性がある）。本点は MEMO.md に残す。

## 4. インポートパスの確認

`scripts/claude_loop_lib/feedbacks.py` 内での相対 import は、既存の同ディレクトリファイル（`workflow.py` 等）の慣例に合わせる:

```python
from claude_loop_lib.frontmatter import parse_frontmatter
```

※ `scripts/claude_loop.py` が `sys.path` に `scripts/` を追加しているかは実装着手時に `claude_loop.py` / `claude_loop_lib/__init__.py` を読んで確認する。相対 import `from .frontmatter import parse_frontmatter` が通る可能性もあるため、実装時に既存パターンを踏襲する。

`scripts/issue_status.py` は独立実行スクリプトのため、`sys.path` 調整が必要な可能性あり:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from claude_loop_lib.frontmatter import parse_frontmatter
```

既存の `issue_status.py` は `claude_loop_lib` を import していない（`yaml` 直使用のみ）ので、この import パス調整が本 ISSUE 最大の実装リスク。`pytest` で `issue_status.py` の単体動作確認を加える余地あり。

## 5. テスト

`tests/test_claude_loop.py` の `TestParseFeedbackFrontmatter` は既存のまま全通過する必要がある。追加テストは任意だが、`parse_frontmatter` 単体テストを `TestParseFrontmatter` クラスとして 5 ケース程度追加しておくと PHASE6.0 での再利用時に安心できる。

追加テスト案（全 5 ケース、30 行程度）:

1. 正常系: `---\nkey: value\n---\nbody` → `({"key": "value"}, "body")`
2. 先頭 `---` 無し → `(None, 元テキスト)`
3. 閉じ `---` 無し → `(None, 元テキスト)`
4. YAML 不正 → `(None, 元テキスト)`
5. dict 以外（list） → `(None, body)`

## 6. 検証手順

1. `python scripts/issue_status.py util` の出力を変更前/変更後で diff → 完全一致
2. `python scripts/issue_status.py` の出力を変更前/変更後で diff → 完全一致
3. `pytest tests/test_claude_loop.py -k Feedback` が全通過
4. 追加した `TestParseFrontmatter` が全通過（追加する場合）

## リスク・不確実性

- **import パス調整**: `issue_status.py` が `claude_loop_lib` をはじめて import するため、`sys.path` 設定が必要。失敗した場合は相対 import / `PYTHONPATH` 環境変数 / `pyproject.toml` の `tool.setuptools` 等で解決。実装時に既存 `claude_loop.py` の方式を参照する
- **feedback テストの挙動同一性**: `(None, content)` と `(None, body)` の微妙な戻り分岐を新旧で一致させる必要あり。`TestParseFeedbackFrontmatter` の 4 ケース（no fm / unclosed / invalid yaml / non-dict）を pass することで担保
- **警告メッセージの消失**: `issue_status.py` の「YAML parse failed」警告が消える点は運用影響小だが MEMO.md に記録

## ファイル変更一覧

| ファイル | 操作 | 行数目安 |
|---|---|---|
| `scripts/claude_loop_lib/frontmatter.py` | 新規 | +25 |
| `scripts/claude_loop_lib/feedbacks.py` | 書き換え | ±15 |
| `scripts/issue_status.py` | 書き換え | -40 / +15 |
| `tests/test_claude_loop.py` | 追加テスト（任意） | +30 |

正味コード変更: 約 50 行（テスト追加込みで 80 行）。
