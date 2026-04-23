"""Tests for scripts/issue_worklist.py."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from . import _bootstrap  # noqa: F401  — must precede issue_worklist import

import issue_worklist


class TestIssueWorklist(unittest.TestCase):
    """Tests for scripts/issue_worklist.py."""

    def setUp(self) -> None:
        import issue_worklist  # noqa: F401
        self.issue_worklist = sys.modules["issue_worklist"]
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_root = Path(self._tmp.name)
        self.issues_dir = self.tmp_root / "ISSUES"
        self._patchers = [
            patch.object(self.issue_worklist, "REPO_ROOT", self.tmp_root),
            patch.object(self.issue_worklist, "ISSUES_DIR", self.issues_dir),
        ]
        for p in self._patchers:
            p.start()

    def tearDown(self) -> None:
        for p in self._patchers:
            p.stop()
        self._tmp.cleanup()

    def _write_issue(self, category: str, priority: str, name: str,
                     fm_lines: list[str] | None, body: str) -> Path:
        dir_ = self.issues_dir / category / priority
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

    def test_collect_ready_and_review_sorted_by_priority(self) -> None:
        self._write_issue(
            "util", "high", "a-ready.md",
            ["status: ready", "assigned: ai"], "# High Ready Title\n\nhigh summary",
        )
        self._write_issue(
            "util", "medium", "b-review.md",
            ["status: review", "assigned: ai"], "# Medium Review Title\n\nmed summary",
        )
        items = self.issue_worklist.collect("util", "ai", ["ready", "review"])
        assert len(items) == 2
        assert items[0]["priority"] == "high"
        assert items[0]["status"] == "ready"
        assert items[1]["priority"] == "medium"
        assert items[1]["status"] == "review"
        assert items[0]["title"] == "High Ready Title"

    def test_assigned_filter_excludes_human(self) -> None:
        # ready/human is an invalid combo but the filter must still exclude it
        self._write_issue(
            "util", "low", "ready-human.md",
            ["status: ready", "assigned: human"], "# human ready\n\nbody",
        )
        import io as _io
        with patch("sys.stderr", _io.StringIO()):
            items = self.issue_worklist.collect("util", "ai", ["ready", "review"])
        assert items == []

    def test_raw_without_frontmatter_excluded_from_defaults(self) -> None:
        self._write_issue("util", "low", "raw.md", None, "no frontmatter body")
        items = self.issue_worklist.collect("util", "ai", ["ready", "review"])
        assert items == []

    def test_json_format_has_expected_keys(self) -> None:
        self._write_issue(
            "util", "medium", "x.md",
            ["status: ready", "assigned: ai", 'reviewed_at: "2026-04-23"'],
            "# JSON Title\n\nthe summary here",
        )
        items = self.issue_worklist.collect("util", "ai", ["ready", "review"])
        out = self.issue_worklist.format_json("util", "ai", ["ready", "review"], items)
        payload = json.loads(out)
        assert payload["category"] == "util"
        assert payload["filter"] == {"assigned": "ai", "status": ["ready", "review"]}
        assert len(payload["items"]) == 1
        entry = payload["items"][0]
        assert entry["path"].startswith("ISSUES/util/medium/")
        assert entry["title"] == "JSON Title"
        assert entry["reviewed_at"] == "2026-04-23"

    def test_status_filter_ready_only_excludes_review(self) -> None:
        self._write_issue(
            "util", "high", "r.md",
            ["status: ready", "assigned: ai"], "# r\n\nbody",
        )
        self._write_issue(
            "util", "medium", "v.md",
            ["status: review", "assigned: ai"], "# v\n\nbody",
        )
        items = self.issue_worklist.collect("util", "ai", ["ready"])
        assert [it["status"] for it in items] == ["ready"]

    def test_priority_mismatch_emits_warning_and_uses_dir(self) -> None:
        self._write_issue(
            "util", "medium", "mismatch.md",
            ["status: ready", "assigned: ai", "priority: high"],
            "# m\n\nbody",
        )
        import io as _io
        buf = _io.StringIO()
        with patch("sys.stderr", buf):
            items = self.issue_worklist.collect("util", "ai", ["ready"])
        assert len(items) == 1
        assert items[0]["priority"] == "medium"
        assert "priority frontmatter='high'" in buf.getvalue()

    def test_parse_status_list_rejects_invalid(self) -> None:
        with self.assertRaises(SystemExit):
            self.issue_worklist._parse_status_list("ready,garbage")

    def test_format_text_empty_says_no_matching(self) -> None:
        text = self.issue_worklist.format_text("util", [])
        assert "(no matching issues)" in text

    def _write_n_issues(self, n: int) -> None:
        for i in range(n):
            priority = "high" if i < 2 else ("medium" if i < 4 else "low")
            self._write_issue(
                "util", priority, f"issue-{i:02d}.md",
                ["status: ready", "assigned: ai"],
                f"# Issue {i}\n\nsummary {i}",
            )

    def test_limit_returns_top_n_in_priority_order(self) -> None:
        self._write_n_issues(6)
        items = self.issue_worklist.collect("util", "ai", ["ready"])
        assert len(items) == 6
        # main() with --limit 3 should return first 3 (high×2, medium×1)
        import io as _io
        buf = _io.StringIO()
        with patch("sys.stdout", buf):
            self.issue_worklist.main(["--category", "util", "--limit", "3", "--format", "json"])
        payload = json.loads(buf.getvalue())
        assert len(payload["items"]) == 3
        assert payload["items"][0]["priority"] == "high"
        assert payload["items"][2]["priority"] == "medium"
        assert payload["total"] == 6
        assert payload["truncated"] is True
        assert payload["limit"] == 3

    def test_limit_omitted_returns_all(self) -> None:
        self._write_n_issues(5)
        import io as _io
        buf = _io.StringIO()
        with patch("sys.stdout", buf):
            self.issue_worklist.main(["--category", "util", "--format", "json"])
        payload = json.loads(buf.getvalue())
        assert len(payload["items"]) == 5
        assert "total" not in payload

    def test_limit_exceeds_count_no_truncation(self) -> None:
        self._write_n_issues(3)
        import io as _io
        buf = _io.StringIO()
        with patch("sys.stdout", buf):
            self.issue_worklist.main(["--category", "util", "--limit", "100", "--format", "json"])
        payload = json.loads(buf.getvalue())
        assert len(payload["items"]) == 3
        assert payload["truncated"] is False
        assert payload["total"] == 3

    def test_limit_text_format_appends_truncation_note(self) -> None:
        self._write_n_issues(5)
        import io as _io
        buf = _io.StringIO()
        with patch("sys.stdout", buf):
            self.issue_worklist.main(["--category", "util", "--limit", "2"])
        output = buf.getvalue()
        assert "(showing first 2 of 5 issues)" in output

    def test_limit_text_format_no_note_when_not_truncated(self) -> None:
        self._write_n_issues(2)
        import io as _io
        buf = _io.StringIO()
        with patch("sys.stdout", buf):
            self.issue_worklist.main(["--category", "util", "--limit", "10"])
        output = buf.getvalue()
        assert "showing first" not in output


if __name__ == "__main__":
    unittest.main()
