"""Tests for scripts/claude_loop_lib/feedbacks.py."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from . import _bootstrap  # noqa: F401  — must precede claude_loop_lib imports

from claude_loop_lib.feedbacks import (
    parse_feedback_frontmatter, load_feedbacks, consume_feedbacks,
)


class TestParseFeedbackFrontmatter(unittest.TestCase):
    """Tests for parse_feedback_frontmatter()."""

    def test_with_step_string(self) -> None:
        content = "---\nstep: split_plan\n---\n\nSome feedback"
        steps, body = parse_feedback_frontmatter(content)
        assert steps == ["split_plan"]
        assert body == "Some feedback"

    def test_with_step_list(self) -> None:
        content = "---\nstep: [a, b]\n---\n\nFeedback body"
        steps, body = parse_feedback_frontmatter(content)
        assert steps == ["a", "b"]
        assert body == "Feedback body"

    def test_without_frontmatter(self) -> None:
        content = "Just plain text"
        steps, body = parse_feedback_frontmatter(content)
        assert steps is None
        assert body == "Just plain text"

    def test_without_step_field(self) -> None:
        content = "---\ntitle: something\n---\n\nBody text"
        steps, body = parse_feedback_frontmatter(content)
        assert steps is None
        assert body == "Body text"

    def test_invalid_yaml(self) -> None:
        content = "---\n: : : invalid\n---\n\nBody"
        steps, body = parse_feedback_frontmatter(content)
        assert steps is None
        assert body == content

    def test_empty_body(self) -> None:
        content = "---\nstep: split_plan\n---\n"
        steps, body = parse_feedback_frontmatter(content)
        assert steps == ["split_plan"]
        assert body == ""


class TestLoadFeedbacks(unittest.TestCase):
    """Tests for load_feedbacks()."""

    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_no_directory(self) -> None:
        result = load_feedbacks(self.tmp_dir / "nonexistent", "split_plan")
        assert result == []

    def test_empty_directory(self) -> None:
        fb_dir = self.tmp_dir / "fb"
        fb_dir.mkdir()
        result = load_feedbacks(fb_dir, "split_plan")
        assert result == []

    def test_matching_step(self) -> None:
        fb_dir = self.tmp_dir / "fb"
        fb_dir.mkdir()
        fb_file = fb_dir / "test.md"
        fb_file.write_text("---\nstep: split_plan\n---\n\nFeedback", encoding="utf-8")
        result = load_feedbacks(fb_dir, "split_plan")
        assert len(result) == 1
        assert result[0][0] == fb_file
        assert result[0][1] == "Feedback"

    def test_non_matching_step(self) -> None:
        fb_dir = self.tmp_dir / "fb"
        fb_dir.mkdir()
        (fb_dir / "test.md").write_text("---\nstep: wrap_up\n---\n\nFeedback", encoding="utf-8")
        result = load_feedbacks(fb_dir, "split_plan")
        assert result == []

    def test_catch_all(self) -> None:
        fb_dir = self.tmp_dir / "fb"
        fb_dir.mkdir()
        (fb_dir / "test.md").write_text("Just feedback, no frontmatter", encoding="utf-8")
        result = load_feedbacks(fb_dir, "any_step")
        assert len(result) == 1

    def test_done_excluded(self) -> None:
        fb_dir = self.tmp_dir / "fb"
        fb_dir.mkdir()
        done_dir = fb_dir / "done"
        done_dir.mkdir()
        (done_dir / "old.md").write_text("Old feedback", encoding="utf-8")
        result = load_feedbacks(fb_dir, "any_step")
        assert result == []

    def test_sorted_order(self) -> None:
        fb_dir = self.tmp_dir / "fb"
        fb_dir.mkdir()
        (fb_dir / "b.md").write_text("Second", encoding="utf-8")
        (fb_dir / "a.md").write_text("First", encoding="utf-8")
        result = load_feedbacks(fb_dir, "any_step")
        assert [r[0].name for r in result] == ["a.md", "b.md"]


class TestConsumeFeedbacks(unittest.TestCase):
    """Tests for consume_feedbacks()."""

    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_moves_to_done(self) -> None:
        fb_dir = self.tmp_dir / "fb"
        fb_dir.mkdir()
        fb_file = fb_dir / "test.md"
        fb_file.write_text("content", encoding="utf-8")
        done_dir = fb_dir / "done"

        consume_feedbacks([fb_file], done_dir)

        assert not fb_file.exists()
        assert (done_dir / "test.md").exists()
        assert (done_dir / "test.md").read_text(encoding="utf-8") == "content"

    def test_creates_done_dir(self) -> None:
        fb_dir = self.tmp_dir / "fb"
        fb_dir.mkdir()
        fb_file = fb_dir / "test.md"
        fb_file.write_text("content", encoding="utf-8")
        done_dir = fb_dir / "done"

        consume_feedbacks([fb_file], done_dir)
        assert done_dir.is_dir()

    def test_empty_list(self) -> None:
        done_dir = self.tmp_dir / "done"
        consume_feedbacks([], done_dir)
        assert not done_dir.exists()

    def test_overwrites_existing(self) -> None:
        fb_dir = self.tmp_dir / "fb"
        fb_dir.mkdir()
        done_dir = fb_dir / "done"
        done_dir.mkdir()
        (done_dir / "test.md").write_text("old content", encoding="utf-8")
        fb_file = fb_dir / "test.md"
        fb_file.write_text("new content", encoding="utf-8")

        consume_feedbacks([fb_file], done_dir)
        assert (done_dir / "test.md").read_text(encoding="utf-8") == "new content"


if __name__ == "__main__":
    unittest.main()
