"""Git helpers: HEAD commit lookup, uncommitted-change detection, auto-commit."""

from __future__ import annotations

import subprocess
from pathlib import Path


def get_head_commit(cwd: Path) -> str | None:
    """Get current HEAD commit hash, or None if not a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd, capture_output=True, text=True, check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except FileNotFoundError:
        return None


def check_uncommitted_changes(cwd: Path) -> bool:
    """Check if there are uncommitted changes in the working directory."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd, capture_output=True, text=True, check=False,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except FileNotFoundError:
        return False


def auto_commit_changes(cwd: Path) -> str | None:
    """Stage all changes and commit. Returns the new commit hash or None on failure."""
    try:
        subprocess.run(["git", "add", "-A"], cwd=cwd, check=True)
        subprocess.run(["git", "commit", "-m", "auto-commit before workflow"], cwd=cwd, check=True)
        return get_head_commit(cwd)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
