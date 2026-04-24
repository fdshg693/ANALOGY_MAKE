"""Tests for scripts/claude_loop_lib/notify.py."""
from __future__ import annotations

import unittest
from unittest.mock import patch, MagicMock

from . import _bootstrap  # noqa: F401  — must precede claude_loop_lib imports

from claude_loop_lib.notify import (
    notify_completion,
    _notify_toast,
    RunSummary,
    RESULT_SUCCESS,
    RESULT_FAILED,
    RESULT_INTERRUPTED,
)


def _make_summary(**overrides) -> RunSummary:
    defaults = {
        "workflow_label": "claude_loop",
        "result": RESULT_SUCCESS,
        "duration_seconds": 0.0,
        "loops_completed": 1,
        "steps_completed": 1,
    }
    defaults.update(overrides)
    return RunSummary(**defaults)


class TestRunSummaryTitle(unittest.TestCase):
    def test_title_success(self) -> None:
        assert _make_summary(result=RESULT_SUCCESS).title() == "Workflow Complete"

    def test_title_failed(self) -> None:
        assert _make_summary(result=RESULT_FAILED).title() == "Workflow Failed"

    def test_title_interrupted(self) -> None:
        assert _make_summary(result=RESULT_INTERRUPTED).title() == "Workflow Interrupted"


class TestRunSummaryMessage(unittest.TestCase):
    def test_success_format(self) -> None:
        s = _make_summary(
            workflow_label="full",
            result=RESULT_SUCCESS,
            duration_seconds=872.0,
            loops_completed=2,
            steps_completed=12,
        )
        assert s.message() == "full / 2 loops / 12 steps / 14m 32s"

    def test_singular_loop_and_step(self) -> None:
        s = _make_summary(loops_completed=1, steps_completed=1, duration_seconds=5.0)
        # "1 loop" / "1 step" (singular), not "1 loops" / "1 steps"
        assert "1 loop" in s.message()
        assert "1 step" in s.message()
        assert "1 loops" not in s.message()
        assert "1 steps" not in s.message()

    def test_failed_includes_step_and_exit(self) -> None:
        s = _make_summary(
            workflow_label="full",
            result=RESULT_FAILED,
            duration_seconds=251.0,
            loops_completed=1,
            steps_completed=3,
            exit_code=1,
            failed_step="imple_plan",
        )
        msg = s.message()
        assert "imple_plan" in msg
        assert "exit 1" in msg

    def test_interrupted_includes_reason(self) -> None:
        s = _make_summary(
            result=RESULT_INTERRUPTED,
            duration_seconds=422.0,
            loops_completed=1,
            steps_completed=5,
            interrupt_reason="SIGINT",
            failed_step="write_current",
        )
        msg = s.message()
        assert "SIGINT" in msg
        assert "write_current" in msg


class TestNotifyCompletion(unittest.TestCase):
    @patch("claude_loop_lib.notify._notify_toast")
    def test_calls_toast_with_summary_strings(self, mock_toast: MagicMock) -> None:
        s = _make_summary(workflow_label="quick", result=RESULT_SUCCESS)
        notify_completion(s)
        mock_toast.assert_called_once_with(s.title(), s.message())

    @patch("claude_loop_lib.notify._notify_beep")
    @patch("claude_loop_lib.notify._notify_toast", side_effect=Exception("fail"))
    def test_falls_back_to_beep_on_toast_failure(
        self, mock_toast: MagicMock, mock_beep: MagicMock
    ) -> None:
        s = _make_summary()
        notify_completion(s)
        mock_beep.assert_called_once_with(s.title(), s.message())


class TestToastXml(unittest.TestCase):
    @patch("claude_loop_lib.notify.subprocess.run")
    def test_toast_xml_contains_scenario_and_duration(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        _notify_toast("t", "m")
        call_args = mock_run.call_args_list[0][0][0]
        cmd_str = " ".join(call_args)
        assert "scenario=''reminder''" in cmd_str or "scenario='reminder'" in cmd_str
        assert "duration=''long''" in cmd_str or "duration='long'" in cmd_str

    @patch("claude_loop_lib.notify.subprocess.run")
    def test_toast_escapes_xml_entities(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        _notify_toast("a<b>", "x&y")
        cmd_str = " ".join(mock_run.call_args_list[0][0][0])
        assert "&lt;" in cmd_str
        assert "&gt;" in cmd_str
        assert "&amp;" in cmd_str
        # raw characters must not leak into payload (outside XML structure chars)
        # Search within <text> bodies: ensure '<b>' substring absent
        assert "<b>" not in cmd_str
        # raw 'x&y' (unescaped) must not appear
        assert "x&y" not in cmd_str

    @patch("claude_loop_lib.notify.subprocess.run")
    def test_toast_falls_back_to_duration_long_on_reminder_rejection(
        self, mock_run: MagicMock
    ) -> None:
        # First call (reminder XML) fails; second call (duration=long) succeeds
        mock_run.side_effect = [
            MagicMock(returncode=1),
            MagicMock(returncode=0),
        ]
        _notify_toast("t", "m")
        assert mock_run.call_count == 2
        first_cmd = " ".join(mock_run.call_args_list[0][0][0])
        second_cmd = " ".join(mock_run.call_args_list[1][0][0])
        assert "scenario=" in first_cmd
        assert "scenario=" not in second_cmd
        assert "duration=''long''" in second_cmd or "duration='long'" in second_cmd

    @patch("claude_loop_lib.notify.subprocess.run")
    def test_toast_raises_when_both_variants_fail(
        self, mock_run: MagicMock
    ) -> None:
        mock_run.return_value = MagicMock(returncode=1)
        with self.assertRaises(RuntimeError):
            _notify_toast("t", "m")
        assert mock_run.call_count == 2


if __name__ == "__main__":
    unittest.main()
