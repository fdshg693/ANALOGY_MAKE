"""Tests for scripts/claude_loop_lib/issues.py."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from . import _bootstrap  # noqa: F401  — must precede claude_loop_lib imports


class TestExtractStatusAssigned(unittest.TestCase):
    """Tests for claude_loop_lib.issues.extract_status_assigned (§1 refactor)."""

    def _write(self, tmp: Path, name: str, text: str) -> Path:
        path = tmp / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_no_frontmatter_returns_raw_human(self) -> None:
        from claude_loop_lib.issues import extract_status_assigned
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            path = self._write(tmp, "x.md", "# title\n\nbody\n")
            status, assigned, fm, body = extract_status_assigned(path)
        assert status == "raw"
        assert assigned == "human"
        assert fm is None
        assert "# title" in body

    def test_frontmatter_returns_fm_dict_and_body(self) -> None:
        from claude_loop_lib.issues import extract_status_assigned
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            path = self._write(
                tmp, "x.md",
                "---\nstatus: ready\nassigned: ai\n---\n# t\n\nsummary line\n",
            )
            status, assigned, fm, body = extract_status_assigned(path)
        assert status == "ready"
        assert assigned == "ai"
        assert isinstance(fm, dict)
        assert fm["status"] == "ready"
        assert "summary line" in body

    def test_invalid_combo_emits_warning(self) -> None:
        from claude_loop_lib import issues as issues_mod
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            path = self._write(
                tmp, "x.md",
                "---\nstatus: ready\nassigned: human\n---\n# t\n",
            )
            import io as _io
            buf = _io.StringIO()
            with patch("sys.stderr", buf):
                issues_mod.extract_status_assigned(path)
            err = buf.getvalue()
        assert "invalid combo" in err


if __name__ == "__main__":
    unittest.main()
