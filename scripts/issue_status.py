"""ISSUE ステータス・担当の分布を表示する読み取り専用スクリプト.

Usage:
    python scripts/issue_status.py              # 全カテゴリを集計
    python scripts/issue_status.py <category>   # 指定カテゴリのみ集計

集計対象:
    ISSUES/{category}/{high,medium,low}/*.md

frontmatter 仕様は ISSUES/README.md を参照.
フォールバック:
    - frontmatter 無し / パース失敗 -> status=raw, assigned=human として集計
    - 既定値外の値 -> そのまま集計しつつ stderr に警告
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ISSUES_DIR = REPO_ROOT / "ISSUES"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from claude_loop_lib.frontmatter import parse_frontmatter  # noqa: E402

CATEGORIES = ["util", "app", "infra", "cicd"]
PRIORITIES = ["high", "medium", "low"]

VALID_STATUS = {"raw", "review", "ready", "need_human_action"}
VALID_ASSIGNED = {"human", "ai"}

VALID_COMBOS = {
    ("raw", "human"),
    ("raw", "ai"),
    ("review", "ai"),
    ("ready", "ai"),
    ("need_human_action", "human"),
}

DISPLAY_ORDER: list[tuple[str, str]] = [
    ("ready", "ai"),
    ("review", "ai"),
    ("need_human_action", "human"),
    ("raw", "human"),
    ("raw", "ai"),
]


def warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)


def _extract_status_assigned(path: Path) -> tuple[str, str]:
    """Return (status, assigned) for a single ISSUE file with fallbacks."""
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


def collect_priority(category_dir: Path, priority: str) -> Counter[tuple[str, str]]:
    """Count (status, assigned) pairs in a priority subdirectory."""
    counter: Counter[tuple[str, str]] = Counter()
    priority_dir = category_dir / priority
    if not priority_dir.is_dir():
        return counter
    for md_file in sorted(priority_dir.glob("*.md")):
        counter[_extract_status_assigned(md_file)] += 1
    return counter


def format_priority_line(priority: str, counter: Counter[tuple[str, str]]) -> str:
    """Format a single priority row with the 5 canonical slots always shown."""
    parts: list[str] = []
    for status, assigned in DISPLAY_ORDER:
        parts.append(f"{status}/{assigned}={counter.get((status, assigned), 0)}")
    extras = sorted(k for k in counter if k not in set(DISPLAY_ORDER))
    for status, assigned in extras:
        parts.append(f"{status}/{assigned}={counter[(status, assigned)]}")
    label = f"{priority}:".ljust(8)
    return f"  {label} " + ", ".join(parts)


def print_category(category: str) -> None:
    category_dir = ISSUES_DIR / category
    if not category_dir.is_dir():
        return
    print(f"{category}:")
    for priority in PRIORITIES:
        counter = collect_priority(category_dir, priority)
        print(format_priority_line(priority, counter))


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        category = argv[1]
        if not (ISSUES_DIR / category).is_dir():
            warn(f"category '{category}' not found under ISSUES/")
            return 0
        print_category(category)
    else:
        for category in CATEGORIES:
            if (ISSUES_DIR / category).is_dir():
                print_category(category)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
