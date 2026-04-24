"""Tests for scripts/claude_loop_lib/logging_utils.py."""
from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from . import _bootstrap  # noqa: F401  — must precede claude_loop_lib imports

from claude_loop_lib.logging_utils import (
    create_log_path,
    format_duration,
    format_run_cost_footer,
    format_step_cost_line,
)
from claude_loop_lib import costs


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


def _ok_step(name: str, cost_usd: float, kind: str = "claude") -> costs.StepCost:
    return costs.StepCost(
        step_name=name, session_id="s", model="claude-opus-4-7",
        started_at="a", ended_at="b", duration_seconds=1.0,
        kind=kind,
        input_tokens=1200, output_tokens=340,
        cache_read_input_tokens=50, cache_creation_input_tokens=0,
        num_turns=2,
        cost_usd=cost_usd, cost_source="cli",
        status="ok", reason=None,
    )


class TestFormatStepCostLine(unittest.TestCase):
    def test_ok_line_has_tokens_and_model(self) -> None:
        line = format_step_cost_line(_ok_step("demo", 0.0123))
        assert "Cost: $0.0123" in line
        assert "in: 1200" in line
        assert "out: 340" in line
        assert "claude-opus-4-7" in line

    def test_unavailable_line(self) -> None:
        step = costs.unavailable_step(
            step_name="x", session_id="s",
            started_at="a", ended_at="b", duration_seconds=0.0,
            kind="claude", reason="non-json-output",
        )
        line = format_step_cost_line(step)
        assert line.startswith("Cost: unavailable")
        assert "non-json-output" in line

    def test_kind_deferred_external_shown(self) -> None:
        step = costs.build_external_step_cost(
            step_name="ext", session_id="s",
            started_at="a", ended_at="b", duration_seconds=1.0,
        )
        line = format_step_cost_line(step)
        assert "deferred_external" in line


class TestFormatRunCostFooter(unittest.TestCase):
    def test_footer_lines_structure(self) -> None:
        summary = costs.aggregate_run(
            workflow_label="demo", started_at="t0", ended_at="t1",
            steps=[_ok_step("first", 0.10), _ok_step("second", 0.20)],
            claude_code_cli_version="2.1.117",
        )
        lines = format_run_cost_footer(summary)
        joined = "\n".join(lines)
        assert "Run cost: $0.3000 USD" in joined
        assert "Claude Code CLI 2.1.117" in joined
        assert "Steps: 2 ok / 0 unavailable" in joined
        assert "[1] first" in joined
        assert "[2] second" in joined
        # header 2 lines + "Per-step:" + N
        assert len(lines) == 2 + 1 + 2

    def test_footer_with_missing(self) -> None:
        missing = costs.unavailable_step(
            step_name="miss", session_id="s",
            started_at="a", ended_at="b", duration_seconds=0.0,
            kind="claude", reason="no-json-output",
        )
        summary = costs.aggregate_run(
            workflow_label="demo", started_at="t0", ended_at="t1",
            steps=[_ok_step("a", 0.05), missing],
        )
        joined = "\n".join(format_run_cost_footer(summary))
        assert "Steps: 1 ok / 1 unavailable" in joined
        assert "unavailable" in joined
        assert "Claude Code CLI unknown" in joined


if __name__ == "__main__":
    unittest.main()
