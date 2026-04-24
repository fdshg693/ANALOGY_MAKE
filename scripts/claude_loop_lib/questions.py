"""Shared helpers for reading Question frontmatter."""

from __future__ import annotations

import sys
from pathlib import Path

from .frontmatter import parse_frontmatter

VALID_STATUS = {"raw", "ready", "need_human_action"}
VALID_ASSIGNED = {"human", "ai"}

VALID_COMBOS = {
    ("raw", "human"),
    ("raw", "ai"),
    ("ready", "ai"),
    ("need_human_action", "human"),
}


def _warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)


def extract_status_assigned(path: Path) -> tuple[str, str, dict | None, str]:
    """Return (status, assigned, frontmatter, body) for a single QUESTION file.

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
