"""Shared YAML frontmatter parsing for Markdown files."""

from __future__ import annotations

import yaml


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Parse a YAML frontmatter block from the head of text.

    Returns (frontmatter, body):
      - frontmatter: dict if the block exists, is closed by `---`, is valid YAML,
                     and parses to a mapping. None otherwise.
      - body: text after the closing `---`, or the original text if no frontmatter.

    Fallback rules (all return (None, <appropriate body>)):
      - No leading `---` line -> body = text
      - Missing closing `---` -> body = text
      - YAML parse error -> body = text (unparseable content treated as no fm)
      - YAML parses to non-dict (list/scalar) -> body = text after closer
    """
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
