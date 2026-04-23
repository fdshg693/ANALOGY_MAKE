# ver7.0 IMPLEMENT — issue_worklist.py 導入

ROUGH_PLAN.md のスコープ（PHASE6.0 §1 + §4 + ドキュメント/テスト）に沿った実装計画。

---

## 0. 事前リファクタリング（REFACTOR.md の扱い）

`scripts/issue_status.py` と新規 `scripts/issue_worklist.py` は、以下のヘルパ・定数を共有する:

- `VALID_STATUS` / `VALID_ASSIGNED` / `VALID_COMBOS`
- `_extract_status_assigned(path) -> tuple[status, assigned]`

共有しないと 2 つのスクリプト間で妥当性判定ロジックが drift する（例: 将来 `status` の種類が増えた時、片方だけ更新されるリスク）。

### 方針

`scripts/claude_loop_lib/issues.py` を新設し、上記定数・ヘルパを集約する。`issue_status.py` はそれをインポートする形に書き換える。

変更規模:

- 新規: `scripts/claude_loop_lib/issues.py`（~50 行）
- 変更: `scripts/issue_status.py`（定数・`_extract_status_assigned` をインポートに置換、~30 行削除）
- 既存テスト `TestParseFrontmatter`（frontmatter 共通化時に追加済み）はそのまま通る

範囲が限定的・変更がほぼ機械的・ISSUE 仕様の再利用メリットが明確なため、**REFACTOR.md を独立ファイルとしては作成せず、本 IMPLEMENT.md §1 に組み込む**（ROUGH_PLAN の「事前リファクタリングの必要性次第で判断」を、ここで「必要・IMPLEMENT に同梱」と確定）。

---

## 1. 共通 ISSUE ヘルパの切り出し（REFACTOR 同梱）

### 1-1. 新規 `scripts/claude_loop_lib/issues.py`

```python
"""Shared helpers for reading ISSUE frontmatter."""

from __future__ import annotations

import sys
from pathlib import Path

from .frontmatter import parse_frontmatter

VALID_STATUS = {"raw", "review", "ready", "need_human_action"}
VALID_ASSIGNED = {"human", "ai"}

VALID_COMBOS = {
    ("raw", "human"),
    ("raw", "ai"),
    ("review", "ai"),
    ("ready", "ai"),
    ("need_human_action", "human"),
}


def _warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)


def extract_status_assigned(path: Path) -> tuple[str, str, dict | None, str]:
    """Return (status, assigned, frontmatter, body) for a single ISSUE file.

    Fallbacks:
      - read error / no frontmatter / parse error -> ("raw", "human", None, text or "")
    Warnings are emitted to stderr for unknown status/assigned and invalid combos.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        _warn(f"{path}: read failed ({exc})")
        return "raw", "human", None, ""

    fm, body = parse_frontmatter(text)
    if fm is None:
        return "raw", "human", None, body

    status = str(fm.get("status", "raw"))
    assigned = str(fm.get("assigned", "human"))

    if status not in VALID_STATUS:
        _warn(f"{path}: unknown status '{status}'")
    if assigned not in VALID_ASSIGNED:
        _warn(f"{path}: unknown assigned '{assigned}'")
    if (status, assigned) not in VALID_COMBOS:
        _warn(f"{path}: invalid combo status={status}, assigned={assigned}")

    return status, assigned, fm, body
```

ポイント:

- 既存 `issue_status.py` の `_extract_status_assigned` と比べ、戻り値に `fm`（frontmatter dict）と `body` を追加した 4-tuple にする。`issue_status.py` は `(status, assigned)` のみ必要、`issue_worklist.py` は `reviewed_at` や `title` / `summary` 抽出に `fm` / `body` が必要
- `_warn` は `issues.py` 内の module-private ヘルパとしてそのまま持ち込む（`issue_status.py` の既存 `warn()` と名前衝突しない）

### 1-2. `scripts/issue_status.py` の書き換え

- トップの `VALID_STATUS` / `VALID_ASSIGNED` / `VALID_COMBOS` 定義を削除し、`from claude_loop_lib.issues import VALID_STATUS, VALID_ASSIGNED, VALID_COMBOS, extract_status_assigned` でインポート
- ローカル `_extract_status_assigned` を削除
- 呼び出し部 `counter[_extract_status_assigned(md_file)] += 1` は `status, assigned, _fm, _body = extract_status_assigned(md_file)` → `counter[(status, assigned)] += 1` に書き換え
- `warn()` ローカル関数は残置（`main()` での "category not found" 警告で使用中）

### 1-3. 挙動同一性の確認

既存 `issue_status.py` のテストは存在しないため、手動確認:

- `python scripts/issue_status.py` の出力が変更前と一致すること
- `python scripts/issue_status.py util` の出力が変更前と一致すること
- `python scripts/issue_status.py存在しないカテゴリ` で警告が出ること

---

## 2. `scripts/issue_worklist.py` の新規作成

### 2-1. 責務と CLI

```
python scripts/issue_worklist.py \
    [--category util|app|infra|cicd] \
    [--assigned ai|human] \
    [--status ready,review|ready|review|ready,review,need_human_action] \
    [--format text|json]
```

| オプション | 既定値 | 備考 |
|---|---|---|
| `--category` | `.claude/CURRENT_CATEGORY` の値。未設定時は `app` | `issue_status.py` と同じフォールバック |
| `--assigned` | `ai` | `human` 指定も可能 |
| `--status` | `ready,review` | カンマ区切りで複数指定可。`{raw, review, ready, need_human_action}` のみ受理 |
| `--format` | `text` | `json` を指定すると JSON 配列を stdout に出力 |

PHASE6.0 §1 で明記された「`status in {ready, review}` かつ `assigned == <指定値>` の ISSUE だけ」という要求を、このフラグ構成で柔軟に満たす。

### 2-2. 出力データモデル

各 ISSUE について以下を返す（PHASE6.0 §1-3 準拠 + 必要最小限の拡張）:

| フィールド | 型 | 出所 |
|---|---|---|
| `path` | str | リポジトリルート相対パス（POSIX スラッシュ） |
| `title` | str | 本文冒頭の最初の `# ` 見出し。無ければファイル名 stem |
| `priority` | str | ディレクトリ名（`high` / `medium` / `low`） |
| `status` | str | frontmatter（フォールバック `raw`） |
| `assigned` | str | frontmatter（フォールバック `human`） |
| `reviewed_at` | str | null | `str(fm.get("reviewed_at"))` 存在時のみ |
| `summary` | str | タイトル行を除いた本文の最初の非空行（先頭 120 文字） |

### 2-3. フィルタリング仕様

1. `ISSUES/{category}/{high,medium,low}/*.md` のみを走査対象とする（`done/` 配下・直下ファイル・README.md は除外）
2. `extract_status_assigned` で `(status, assigned)` を取得
3. 除外条件:
   - frontmatter なし（= `raw / human` 扱い）→ 既定呼び出し（`--status ready,review --assigned ai`）では自然に除外される
   - `status not in --status` で除外
   - `assigned != --assigned` で除外
   - `status` または `assigned` が `VALID_STATUS` / `VALID_ASSIGNED` 外 → `extract_status_assigned` が警告を出したうえで、そのまま突き合わせに使う（`--status` / `--assigned` が拾わない限り結果には現れない）
4. `priority` と frontmatter の `priority` が不一致 → `stderr` に警告（ディレクトリ名を採用）

### 2-4. 出力フォーマット

#### `text` フォーマット

```text
[util]
- high   | ready  | ai | ISSUES/util/high/foo.md                    | タイトル本文要約...
- medium | ready  | ai | ISSUES/util/medium/bar.md                  | タイトル本文要約...
- medium | review | ai | ISSUES/util/medium/baz.md                  | タイトル本文要約...
```

- カテゴリ見出しは 1 行目のみ
- 各行: `- {priority:6} | {status:6} | {assigned:5} | {path} | {title}`
- **`summary` は text 出力では使わず、JSON 出力専用**（text は 1 行でコンパクトに、JSON は機械消費向けに詳細を残す）
- 0 件の場合は `[util]` の次行に `  (no matching issues)` を出す（パイプ経由の後段処理で判定しやすくするため）

#### `json` フォーマット

```json
{
  "category": "util",
  "filter": {"assigned": "ai", "status": ["ready", "review"]},
  "items": [
    {
      "path": "ISSUES/util/medium/issue-review-rewrite-verification.md",
      "title": "issue_review SKILL の書き換えロジック実動作確認（ver6.0 持ち越し）",
      "priority": "medium",
      "status": "ready",
      "assigned": "ai",
      "reviewed_at": "2026-04-23",
      "summary": "ver6.0 で導入した issue_review SKILL の..."
    }
  ]
}
```

- `json.dumps(payload, ensure_ascii=False, indent=2)` で出力
- `items` は priority 順（high → medium → low）→ path アルファベット順でソート

### 2-5. 実装スケルトン

```python
"""Filter ISSUEs by assigned/status and print text or JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ISSUES_DIR = REPO_ROOT / "ISSUES"
CURRENT_CATEGORY_FILE = REPO_ROOT / ".claude" / "CURRENT_CATEGORY"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from claude_loop_lib.issues import (  # noqa: E402
    VALID_STATUS,
    VALID_ASSIGNED,
    extract_status_assigned,
)

PRIORITIES = ["high", "medium", "low"]


def _default_category() -> str:
    if CURRENT_CATEGORY_FILE.is_file():
        value = CURRENT_CATEGORY_FILE.read_text(encoding="utf-8").strip()
        if value:
            return value
    return "app"


def _parse_status_list(raw: str) -> list[str]:
    items = [s.strip() for s in raw.split(",") if s.strip()]
    invalid = [s for s in items if s not in VALID_STATUS]
    if invalid:
        raise SystemExit(f"invalid --status values: {invalid}")
    return items


def _extract_title_and_summary(body: str, fallback: str) -> tuple[str, str]:
    title = fallback
    summary = ""
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# ") and title == fallback:
            title = stripped[2:].strip()
            continue
        if not summary:
            summary = stripped[:120]
            if title != fallback:
                break
    return title, summary


def collect(category: str, assigned: str, status_list: list[str]) -> list[dict]:
    items: list[dict] = []
    category_dir = ISSUES_DIR / category
    if not category_dir.is_dir():
        return items
    for priority in PRIORITIES:
        priority_dir = category_dir / priority
        if not priority_dir.is_dir():
            continue
        for md_file in sorted(priority_dir.glob("*.md")):
            st, asg, fm, body = extract_status_assigned(md_file)
            if st not in status_list or asg != assigned:
                continue
            if fm is not None:
                fm_prio = fm.get("priority")
                if fm_prio is not None and str(fm_prio) != priority:
                    print(
                        f"warning: {md_file}: priority frontmatter='{fm_prio}' "
                        f"but directory='{priority}'",
                        file=sys.stderr,
                    )
            title, summary = _extract_title_and_summary(body, md_file.stem)
            reviewed_at = None
            if fm is not None and fm.get("reviewed_at") is not None:
                reviewed_at = str(fm["reviewed_at"])
            items.append({
                "path": md_file.relative_to(REPO_ROOT).as_posix(),
                "title": title,
                "priority": priority,
                "status": st,
                "assigned": asg,
                "reviewed_at": reviewed_at,
                "summary": summary,
            })
    return items


def format_text(category: str, items: list[dict]) -> str:
    lines = [f"[{category}]"]
    if not items:
        lines.append("  (no matching issues)")
        return "\n".join(lines)
    for it in items:
        lines.append(
            f"- {it['priority']:<6} | {it['status']:<6} | {it['assigned']:<5} "
            f"| {it['path']} | {it['title']}"
        )
    return "\n".join(lines)


def format_json(category: str, assigned: str, status_list: list[str],
                items: list[dict]) -> str:
    payload = {
        "category": category,
        "filter": {"assigned": assigned, "status": status_list},
        "items": items,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", default=_default_category())
    parser.add_argument("--assigned", default="ai", choices=sorted(VALID_ASSIGNED))
    parser.add_argument("--status", default="ready,review",
                        help="comma-separated status values")
    parser.add_argument("--format", default="text", choices=["text", "json"])
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    status_list = _parse_status_list(args.status)
    items = collect(args.category, args.assigned, status_list)
    if args.format == "json":
        print(format_json(args.category, args.assigned, status_list, items))
    else:
        print(format_text(args.category, items))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

---

## 3. テスト追加

`tests/test_claude_loop.py` に `TestIssueWorklist` クラスを追加（ver6.1 で `TestParseFrontmatter` を同ファイルに追加したのと同じ方針）。既存 testsuite と同居させることで unittest 一本で回せる。

### 3-1. セットアップ

テストはファイルシステム依存のため、`tempfile.TemporaryDirectory` で一時 `ISSUES/` ツリーを組み、`issue_worklist.REPO_ROOT` / `issue_worklist.ISSUES_DIR` をモンキーパッチする方式をとる。

### 3-2. ケース一覧（最低 6 ケース）

| # | ケース | 期待 |
|---|---|---|
| 1 | `high/ready-ai.md` + `medium/review-ai.md` を用意 → `--assigned ai --status ready,review` | 2 件ヒット、priority 順で high が先 |
| 2 | `low/ready-human.md`（`ready / human` は本来無効組み合わせだが、warnings 経由で除外されるか） | 警告が出つつ結果に含まれない（`assigned=ai` フィルタで落ちる） |
| 3 | frontmatter 無しの `low/raw.md` | `--status ready,review` なら除外 |
| 4 | `--format json` 出力のパース検証 | `category` / `filter` / `items` キーが揃い、`items[*].path` が POSIX パスで始まる |
| 5 | `--status ready` のみ指定 | `review` ファイルは除外される |
| 6 | `priority` frontmatter ミスマッチ（dir=medium, fm.priority=high） | `items[*].priority == "medium"`、stderr に warning |

加えて、§1 のリファクタの挙動同一性を担保する軽量テスト（任意）:

| # | ケース | 期待 |
|---|---|---|
| 7 | `extract_status_assigned` が frontmatter 無しファイルで `("raw", "human", None, "")` を返す | 既存 `issue_status.py` のフォールバックと同等 |
| 8 | `extract_status_assigned` が正常 frontmatter で `fm` dict を返す | 既存挙動の拡張部分が期待通り |

### 3-3. CLI レベルのスモークテスト

実際の `ISSUES/util/` 配下（現状 `medium/issue-review-rewrite-verification.md` 1 件）で以下を手動実行:

```bash
python scripts/issue_worklist.py                           # [util] の ready/ai 1 件
python scripts/issue_worklist.py --format json             # JSON 妥当性確認
python scripts/issue_worklist.py --category app            # app カテゴリ
python scripts/issue_worklist.py --status ready,need_human_action --assigned human  # フォーマット確認
```

---

## 4. `scripts/README.md` の更新

`## ファイル一覧` テーブルに `issue_worklist.py` を追加:

| ファイル | 役割 |
|---|---|
| `issue_worklist.py` | **（追加）** `assigned` / `status` で ISSUE を絞り込み、`text` / `json` で出力する読み取り専用スクリプト |

`## クイックスタート` 直後、または `## テスト` の直前に新セクション `## issue_worklist.py` を追加:

```markdown
## issue_worklist.py

`ISSUES/{category}/{high,medium,low}/*.md` を走査し、frontmatter の
`status` / `assigned` で絞り込んだ ISSUE 一覧を出力する。

### 使い方

```bash
# デフォルト（現在カテゴリ、assigned=ai、status=ready,review、text 出力）
python scripts/issue_worklist.py

# JSON で取得
python scripts/issue_worklist.py --format json

# 人間向け need_human_action を確認
python scripts/issue_worklist.py --assigned human --status need_human_action

# 別カテゴリを指定
python scripts/issue_worklist.py --category app
```

`/retrospective` SKILL も本スクリプトを使って次バージョン推奨の材料を収集する。
```

※ 出力例は本文中にフルで貼らず、簡潔に留める（README 肥大化抑止）。

---

## 5. `.claude/skills/retrospective/SKILL.md` の更新

### 5-1. 追記箇所

§3「次バージョンの種別推奨」冒頭に、`issue_worklist.py` 呼び出しステップを追記する。最終的な構造:

```markdown
## 3. 次バージョンの種別推奨

次バージョンの方針を決める前に、AI が着手可能・レビュー待ちの ISSUE を把握する:

- 現在カテゴリの着手候補: !`python scripts/issue_worklist.py`
- 機械可読形式: !`python scripts/issue_worklist.py --format json`

次に予定されるタスク（MASTER_PLAN の次項目、未解決 ISSUES）を踏まえて、
次バージョンがメジャー・マイナーのどちらが適切かを推奨する。

- 次のマイナーバージョン候補: !`bash .claude/scripts/get_latest_version.sh next-minor`
- 次のメジャーバージョン候補: !`bash .claude/scripts/get_latest_version.sh next-major`
```

ポイント:

- 2 つの `issue_worklist.py` 呼び出し（text / json）を SKILL 冒頭コンテキストとして `!` バックティックで展開
- json 版を同時に出すのは、後続 `/issue_plan`（ver7.1 で新設予定）との整合のため。retrospective でも json の形を見慣れておく

### 5-2. 既存テキストへの影響

§3 の既存 3 行（「次に予定されるタスク…」「次のマイナーバージョン候補」「次のメジャーバージョン候補」）は変更せず温存。`retrospective/SKILL.md` の他セクション（§1 / §2 / §4 / §5）は無変更。

---

## 6. 実装順序

0. **事前権限チェック**: `.claude/skills/retrospective/SKILL.md` への Edit / Write が可能か、テストとして末尾に空行を足して戻すか、`Read → Edit (no-op)` を試行して確認する。失敗する場合は R5 のフォールバック（`scripts/claude_sync.py` 経由）に切り替える判断を imple_plan 冒頭で行う
1. `claude_loop_lib/issues.py` を作成（§1-1）
2. `issue_status.py` を書き換え（§1-2）、手動スモーク確認（§1-3）
3. `issue_worklist.py` を作成（§2）、手動スモーク確認（§2-5 の最後）
4. `tests/test_claude_loop.py` に `TestIssueWorklist` を追加（§3）、unittest 実行
5. `scripts/README.md` 更新（§4）
6. `.claude/skills/retrospective/SKILL.md` 更新（§5）
7. 全体検証: `python -m unittest tests.test_claude_loop`、`python scripts/issue_status.py`、`python scripts/issue_worklist.py`

---

## 7. リスク・不確実性

### R1: `.claude/CURRENT_CATEGORY` 読み込み順序

`_default_category()` は `argparse` のデフォルト値計算のため `parse_args` 呼び出し時に評価される。テストで `CURRENT_CATEGORY_FILE` を差し替える場合、テスト実行中は `_default_category` 内の定数参照を通すのではなく、`argparse` に流入する前に置換が効いていることを確認する必要がある。

→ 対処: テスト時は `--category` を明示指定してフォールバックを経由しない（テストシンプル化）。`_default_category` 単体の挙動は 1 ケースだけ別途確認する。

### R2: `issue_status.py` のテスト不在

`issue_status.py` には現状ユニットテストがないため、§1-2 のリファクタリング後の挙動同一性は手動確認に頼る。誤りが入り込むリスクがある。

→ 対処: §3-2 のケース 7・8 で `extract_status_assigned` 単体を検証しておく。`issue_status.py` 本体は `print_category()` が薄いラッパーのため、手動確認 3 ケース（全カテゴリ / util 指定 / 存在しないカテゴリ）で十分と判断。

### R3: `title` 抽出で日本語見出しを正しく拾えるか

`#` の次に半角スペースを必須としたシンプルな実装のため、`#タイトル`（スペース無し）や `## タイトル`（h2）は拾えず、ファイル stem にフォールバックする。

→ 対処: 現行の ISSUE ファイル（`parse-frontmatter-shared-util.md` 等）は `# タイトル` 形式で揃っているため実害なし。§3-2 でシンプルな `# ` 形式のみテストする。

### R4: `priority` 不一致警告のテスト難度

stderr への warning は `capsys`（pytest）や `unittest.mock.patch(sys.stderr)` で拾う必要がある。

→ 対処: `io.StringIO` を `sys.stderr` に差し替えて文字列で assert する標準手法で対応（ver6.1 の `_warn` 系テストで実績あり）。

### R5: `.claude/skills/` 配下の編集権限

ver6.0 retrospective で、Claude CLI の一部モードで `.claude/` 配下に Write/Edit できない制約が報告されている（`scripts/claude_sync.py` で回避）。本バージョンでは `.claude/skills/retrospective/SKILL.md` を編集する必要がある。

→ 対処: imple_plan ステップで Edit ツールが失敗した場合のみ、`scripts/claude_sync.py` 経由または bash でのファイル書き換えに切り替える。事前の権限確認を imple_plan の最初に行う。

---

## 8. 成否判定基準

ROUGH_PLAN §「成否判定基準」に加え:

- `claude_loop_lib/issues.py` が存在し、`extract_status_assigned` が 4-tuple を返す
- `issue_status.py` のローカル定数定義が消え、`from claude_loop_lib.issues import ...` の 1 行に置き換わっている
- `python scripts/issue_status.py` の出力が変更前と一致する（目視比較）
- `python scripts/issue_worklist.py` / `--format json` / `--category app` / `--assigned human --status need_human_action` の 4 呼び出しが例外なく終了する
- `python -m unittest tests.test_claude_loop` が全件成功し、`TestIssueWorklist` が追加 6 ケース以上を含む
- `scripts/README.md` に `issue_worklist.py` の使い方が記載されている
- `.claude/skills/retrospective/SKILL.md` §3 冒頭に `issue_worklist.py` 呼び出しが追加されている

---

## 9. 次バージョンへの申し送り

本バージョン完了後に ver7.1（PHASE6.0 §2: `/issue_plan` 分離）で以下を利用する:

- `issue_worklist.py --format json` の出力を `/issue_plan` SKILL の冒頭コンテキストとして `!` バックティック展開で注入
- `claude_loop_lib/issues.py` の `extract_status_assigned` を、`ROUGH_PLAN.md` frontmatter の自動生成（ISSUE 状態サマリ）にも再利用できるか検討
- 本バージョンで `retrospective/SKILL.md` に入れた `issue_worklist.py` 呼び出しは、ver7.1 でさらに「ready と review の件数に応じた推奨ロジック」を追記する余地あり（PHASE6.0 §4 参照）
