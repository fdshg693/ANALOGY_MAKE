"""Feedback loading/consumption with YAML frontmatter parsing."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml


def parse_feedback_frontmatter(content: str) -> tuple[list[str] | None, str]:
    """Parse YAML frontmatter from a feedback Markdown file.
    Returns (step_names, body). step_names is None for catch-all."""
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


def load_feedbacks(feedbacks_dir: Path, step_name: str) -> list[tuple[Path, str]]:
    """Load feedback files matching the given step name."""
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


def consume_feedbacks(files: list[Path], done_dir: Path) -> None:
    """Move consumed feedback files to the done directory."""
    if not files:
        return
    done_dir.mkdir(parents=True, exist_ok=True)
    for file_path in files:
        shutil.move(str(file_path), str(done_dir / file_path.name))
