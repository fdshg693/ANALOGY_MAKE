"""Tests for scripts/claude_loop_lib/logging_utils.py."""
from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from . import _bootstrap  # noqa: F401  — must precede claude_loop_lib imports

from claude_loop_lib.logging_utils import create_log_path, format_duration


class TestCreateLogPath(unittest.TestCase):
    """Tests for create_log_path()."""

    @patch("claude_loop_lib.logging_utils.datetime")
    def test_generates_timestamped_filename(self, mock_datetime: MagicMock) -> None:
        mock_datetime.now.return_value.strftime.return_value = "20260404_120000"
        workflow_path = Path("workflows/my_workflow.yaml")

        with patch.object(Path, "mkdir"):
            result = create_log_path(Path("logs/workflow"), workflow_path)

        assert result.name == "20260404_120000_my_workflow.log"

    @patch("claude_loop_lib.logging_utils.datetime")
    def test_path_is_inside_log_dir(self, mock_datetime: MagicMock) -> None:
        mock_datetime.now.return_value.strftime.return_value = "20260404_120000"
        log_dir = Path("logs/workflow")

        with patch.object(Path, "mkdir"):
            result = create_log_path(log_dir, Path("w.yaml"))

        assert result.parent == log_dir.resolve()

    @patch("claude_loop_lib.logging_utils.datetime")
    def test_uses_workflow_stem_not_full_name(self, mock_datetime: MagicMock) -> None:
        mock_datetime.now.return_value.strftime.return_value = "20260101_000000"
        workflow_path = Path("/some/dir/deploy_steps.yaml")

        with patch.object(Path, "mkdir"):
            result = create_log_path(Path("logs"), workflow_path)

        assert "deploy_steps" in result.name
        assert ".yaml" not in result.name

    @patch("claude_loop_lib.logging_utils.datetime")
    def test_creates_log_directory(self, mock_datetime: MagicMock) -> None:
        mock_datetime.now.return_value.strftime.return_value = "20260101_000000"
        log_dir = Path("logs/deep/nested")

        with patch.object(Path, "mkdir") as mock_mkdir:
            create_log_path(log_dir, Path("w.yaml"))

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestFormatDuration(unittest.TestCase):
    """Tests for format_duration()."""

    def test_seconds_only(self) -> None:
        assert format_duration(5) == "5s"

    def test_zero_seconds(self) -> None:
        assert format_duration(0) == "0s"

    def test_minutes_and_seconds(self) -> None:
        assert format_duration(125) == "2m 05s"

    def test_exactly_one_minute(self) -> None:
        assert format_duration(60) == "1m 00s"

    def test_hours_minutes_seconds(self) -> None:
        assert format_duration(3661) == "1h 01m 01s"

    def test_exactly_one_hour(self) -> None:
        assert format_duration(3600) == "1h 00m 00s"

    def test_large_duration(self) -> None:
        # 2 hours, 30 minutes, 45 seconds = 9045
        assert format_duration(9045) == "2h 30m 45s"

    def test_fractional_seconds_are_truncated(self) -> None:
        assert format_duration(59.9) == "59s"

    def test_just_under_one_minute(self) -> None:
        assert format_duration(59) == "59s"

    def test_just_over_one_minute(self) -> None:
        assert format_duration(61) == "1m 01s"


if __name__ == "__main__":
    unittest.main()
