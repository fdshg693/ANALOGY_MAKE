"""Tests for scripts/question_worklist.py."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from . import _bootstrap  # noqa: F401  — must precede question_worklist import

import question_worklist


class TestQuestionWorklist(unittest.TestCase):
    """Tests for scripts/question_worklist.py."""

    def setUp(self) -> None:
        import question_worklist  # noqa: F401
        self.question_worklist = sys.modules["question_worklist"]
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_root = Path(self._tmp.name)
        self.questions_dir = self.tmp_root / "QUESTIONS"
        self._patchers = [
            patch.object(self.question_worklist, "REPO_ROOT", self.tmp_root),
            patch.object(self.question_worklist, "QUESTIONS_DIR", self.questions_dir),
        ]
        for p in self._patchers:
            p.start()

    def tearDown(self) -> None:
        for p in self._patchers:
            p.stop()
        self._tmp.cleanup()

    def _write_question(self, category: str, priority: str, name: str,
                        fm_lines: list[str] | None, body: str) -> Path:
        dir_ = self.questions_dir / category / priority
        dir_.mkdir(parents=True, exist_ok=True)
        path = dir_ / name
        parts: list[str] = []
        if fm_lines is not None:
            parts.append("---")
            parts.extend(fm_lines)
            parts.append("---")
            parts.append("")
        parts.append(body)
        path.write_text("\n".join(parts), encoding="utf-8")
        return path

    def test_default_status_is_ready_only(self) -> None:
        """Question worklist default does not include `review` (differs from ISSUES)."""
        from question_worklist import parse_args
        args = parse_args(["--category", "util"])
        from question_worklist import _parse_status_list
        assert _parse_status_list(args.status) == ["ready"]

    def test_review_status_value_rejected(self) -> None:
        """`review` is not a valid Question status — CLI must reject it."""
        from question_worklist import _parse_status_list
        with self.assertRaises(SystemExit):
            _parse_status_list("ready,review")

    def test_filter_by_category(self) -> None:
        self._write_question(
            "util", "high", "u.md",
            ["status: ready", "assigned: ai"], "# Util Q\n\nbody",
        )
        self._write_question(
            "app", "high", "a.md",
            ["status: ready", "assigned: ai"], "# App Q\n\nbody",
        )
        items = self.question_worklist.collect("util", "ai", ["ready"])
        assert len(items) == 1
        assert items[0]["title"] == "Util Q"

    def test_priority_frontmatter_mismatch_warns(self) -> None:
        self._write_question(
            "util", "medium", "mismatch.md",
            ["status: ready", "assigned: ai", "priority: high"],
            "# Mismatch\n\nbody",
        )
        buf = io.StringIO()
        with patch("sys.stderr", buf):
            items = self.question_worklist.collect("util", "ai", ["ready"])
        assert len(items) == 1
        assert items[0]["priority"] == "medium"
        assert "priority frontmatter='high'" in buf.getvalue()

    def test_format_text_empty_says_no_matching_questions(self) -> None:
        text = self.question_worklist.format_text("util", [])
        assert "(no matching questions)" in text

    def test_limit_and_truncation_in_json_output(self) -> None:
        for i in range(5):
            priority = "high" if i < 2 else ("medium" if i < 4 else "low")
            self._write_question(
                "util", priority, f"q-{i:02d}.md",
                ["status: ready", "assigned: ai"],
                f"# Q {i}\n\nsummary {i}",
            )
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            self.question_worklist.main(
                ["--category", "util", "--limit", "3", "--format", "json"]
            )
        payload = json.loads(buf.getvalue())
        assert len(payload["items"]) == 3
        assert payload["total"] == 5
        assert payload["truncated"] is True
        assert payload["items"][0]["priority"] == "high"

    def test_json_output_schema(self) -> None:
        self._write_question(
            "util", "low", "x.md",
            ["status: ready", "assigned: ai", 'reviewed_at: "2026-04-24"'],
            "# Schema Title\n\nthe summary",
        )
        items = self.question_worklist.collect("util", "ai", ["ready"])
        out = self.question_worklist.format_json("util", "ai", ["ready"], items)
        payload = json.loads(out)
        assert payload["category"] == "util"
        assert payload["filter"] == {"assigned": "ai", "status": ["ready"]}
        assert len(payload["items"]) == 1
        entry = payload["items"][0]
        assert entry["path"].startswith("QUESTIONS/util/low/")
        assert entry["title"] == "Schema Title"
        assert entry["reviewed_at"] == "2026-04-24"


if __name__ == "__main__":
    unittest.main()
