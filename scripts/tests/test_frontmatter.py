"""Tests for scripts/claude_loop_lib/frontmatter.py."""
from __future__ import annotations

import unittest

from . import _bootstrap  # noqa: F401  — must precede claude_loop_lib imports

from claude_loop_lib.frontmatter import parse_frontmatter


class TestParseFrontmatter(unittest.TestCase):
    """Tests for the shared parse_frontmatter()."""

    def test_valid_dict(self) -> None:
        fm, body = parse_frontmatter("---\nkey: value\n---\nbody")
        assert fm == {"key": "value"}
        assert body == "body"

    def test_no_leading_delimiter(self) -> None:
        text = "no frontmatter here"
        fm, body = parse_frontmatter(text)
        assert fm is None
        assert body == text

    def test_missing_closing_delimiter(self) -> None:
        text = "---\nkey: value\nbody text"
        fm, body = parse_frontmatter(text)
        assert fm is None
        assert body == text

    def test_invalid_yaml(self) -> None:
        text = "---\n: : : invalid\n---\nbody"
        fm, body = parse_frontmatter(text)
        assert fm is None
        assert body == text

    def test_non_dict_yaml(self) -> None:
        fm, body = parse_frontmatter("---\n- a\n- b\n---\nbody")
        assert fm is None
        assert body == "body"


if __name__ == "__main__":
    unittest.main()
