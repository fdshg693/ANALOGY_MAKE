"""Tests for scripts/claude_loop_lib/notify.py."""
from __future__ import annotations

import unittest
from unittest.mock import patch, MagicMock

from . import _bootstrap  # noqa: F401  — must precede claude_loop_lib imports

from claude_loop_lib.notify import notify_completion, _notify_toast


class TestNotifyCompletion(unittest.TestCase):
    """Tests for notify_completion()."""

    @patch("claude_loop_lib.notify._notify_toast")
    def test_calls_toast_on_success(self, mock_toast: MagicMock) -> None:
        notify_completion("title", "msg")
        mock_toast.assert_called_once_with("title", "msg")

    @patch("claude_loop_lib.notify._notify_beep")
    @patch("claude_loop_lib.notify._notify_toast", side_effect=Exception("fail"))
    def test_falls_back_to_beep_on_toast_failure(self, mock_toast: MagicMock, mock_beep: MagicMock) -> None:
        notify_completion("title", "msg")
        mock_beep.assert_called_once_with("title", "msg")

    @patch("claude_loop_lib.notify.subprocess.run")
    def test_toast_escapes_single_quotes(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        _notify_toast("it's done", "user's workflow")
        call_args = mock_run.call_args[0][0]
        cmd_str = " ".join(call_args)
        assert "it''s done" in cmd_str


if __name__ == "__main__":
    unittest.main()
