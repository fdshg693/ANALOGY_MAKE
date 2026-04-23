"""Filter ISSUEs by assigned/status and print text or JSON.

Usage:
    python scripts/issue_worklist.py
    python scripts/issue_worklist.py --format json
    python scripts/issue_worklist.py --category app
    python scripts/issue_worklist.py --assigned human --status need_human_action

走査対象:
    ISSUES/{category}/{high,medium,low}/*.md

既定値:
    --category  : .claude/CURRENT_CATEGORY の値（未設定時は 'app'）
    --assigned  : ai
    --status    : ready,review
    --format    : text
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

# ISSUE の title / summary に日本語や em-dash を含むため、Windows の cp932 既定では
# UnicodeEncodeError で落ちる。スクリプト実行時点で stdout/stderr を UTF-8 に固定する。
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if isinstance(sys.stderr, io.TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
ISSUES_DIR = REPO_ROOT / "ISSUES"
CURRENT_CATEGORY_FILE = REPO_ROOT / ".claude" / "CURRENT_CATEGORY"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from claude_loop_lib.issues import (  # noqa: E402
    VALID_ASSIGNED,
    VALID_STATUS,
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
            reviewed_at: str | None = None
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


def format_text(category: str, items: list[dict],
                total: int | None = None, limit: int | None = None) -> str:
    lines = [f"[{category}]"]
    if not items:
        lines.append("  (no matching issues)")
        return "\n".join(lines)
    for it in items:
        lines.append(
            f"- {it['priority']:<6} | {it['status']:<6} | {it['assigned']:<5} "
            f"| {it['path']} | {it['title']}"
        )
    if total is not None and limit is not None and total > limit:
        lines.append(f"(showing first {limit} of {total} issues)")
    return "\n".join(lines)


def format_json(category: str, assigned: str, status_list: list[str],
                items: list[dict],
                total: int | None = None, limit: int | None = None) -> str:
    payload: dict = {
        "category": category,
        "filter": {"assigned": assigned, "status": status_list},
        "items": items,
    }
    if total is not None:
        payload["total"] = total
        payload["truncated"] = total > len(items)
        payload["limit"] = limit
    return json.dumps(payload, ensure_ascii=False, indent=2)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", default=_default_category())
    parser.add_argument("--assigned", default="ai", choices=sorted(VALID_ASSIGNED))
    parser.add_argument("--status", default="ready,review",
                        help="comma-separated status values")
    parser.add_argument("--format", default="text", choices=["text", "json"])
    parser.add_argument("--limit", type=int, default=None,
                        help="maximum number of issues to return (default: all)")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    status_list = _parse_status_list(args.status)
    items = collect(args.category, args.assigned, status_list)
    limit: int | None = args.limit
    total: int | None = None
    if limit is not None:
        total = len(items)
        items = items[:limit]
    if args.format == "json":
        print(format_json(args.category, args.assigned, status_list, items,
                          total=total, limit=limit))
    else:
        print(format_text(args.category, items, total=total, limit=limit))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
