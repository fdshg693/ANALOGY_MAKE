"""Tests for scripts/claude_loop_lib/questions.py."""
from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from . import _bootstrap  # noqa: F401  — must precede claude_loop_lib imports


class TestQuestionsExtractStatusAssigned(unittest.TestCase):
    """Tests for claude_loop_lib.questions.extract_status_assigned."""

    def _write(self, tmp: Path, name: str, text: str) -> Path:
        path = tmp / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_valid_ready_ai_returns_fm_and_body(self) -> None:
        from claude_loop_lib.questions import extract_status_assigned
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            path = self._write(
                tmp, "q.md",
                "---\nstatus: ready\nassigned: ai\n---\n# title\n\nbody line\n",
            )
            status, assigned, fm, body = extract_status_assigned(path)
        assert status == "ready"
        assert assigned == "ai"
        assert isinstance(fm, dict)
        assert "body line" in body

    def test_review_status_emits_warning(self) -> None:
        """Question queue does not allow `review` (differs from ISSUES)."""
        from claude_loop_lib import questions as questions_mod
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            path = self._write(
                tmp, "q.md",
                "---\nstatus: review\nassigned: ai\n---\n# t\n",
            )
            buf = io.StringIO()
            with patch("sys.stderr", buf):
                questions_mod.extract_status_assigned(path)
            err = buf.getvalue()
        assert "unknown status 'review'" in err

    def test_no_frontmatter_falls_back_to_raw_human(self) -> None:
        from claude_loop_lib.questions import extract_status_assigned
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            path = self._write(tmp, "q.md", "# plain title\n\nbody\n")
            status, assigned, fm, body = extract_status_assigned(path)
        assert status == "raw"
        assert assigned == "human"
        assert fm is None
        assert "plain title" in body

    def test_invalid_combo_emits_warning(self) -> None:
        from claude_loop_lib import questions as questions_mod
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            path = self._write(
                tmp, "q.md",
                "---\nstatus: ready\nassigned: human\n---\n# t\n",
            )
            buf = io.StringIO()
            with patch("sys.stderr", buf):
                questions_mod.extract_status_assigned(path)
            err = buf.getvalue()
        assert "invalid combo" in err

    def test_read_error_falls_back(self) -> None:
        from claude_loop_lib.questions import extract_status_assigned
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            missing = tmp / "does-not-exist.md"
            buf = io.StringIO()
            with patch("sys.stderr", buf):
                status, assigned, fm, body = extract_status_assigned(missing)
        assert status == "raw"
        assert assigned == "human"
        assert fm is None
        assert body == ""
        assert "read failed" in buf.getvalue()


if __name__ == "__main__":
    unittest.main()
