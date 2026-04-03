"""Tests for logging features in scripts/claude_loop.py."""

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the scripts directory to sys.path so we can import claude_loop
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from claude_loop import (
    create_log_path, get_head_commit, format_duration, build_command, parse_args,
    notify_completion, _notify_toast, resolve_mode, resolve_command_config,
)


class TestCreateLogPath(unittest.TestCase):
    """Tests for create_log_path()."""

    @patch("claude_loop.datetime")
    def test_generates_timestamped_filename(self, mock_datetime: MagicMock) -> None:
        mock_datetime.now.return_value.strftime.return_value = "20260404_120000"
        workflow_path = Path("workflows/my_workflow.yaml")

        with patch.object(Path, "mkdir"):
            result = create_log_path(Path("logs/workflow"), workflow_path)

        assert result.name == "20260404_120000_my_workflow.log"

    @patch("claude_loop.datetime")
    def test_path_is_inside_log_dir(self, mock_datetime: MagicMock) -> None:
        mock_datetime.now.return_value.strftime.return_value = "20260404_120000"
        log_dir = Path("logs/workflow")

        with patch.object(Path, "mkdir"):
            result = create_log_path(log_dir, Path("w.yaml"))

        assert result.parent == log_dir.resolve()

    @patch("claude_loop.datetime")
    def test_uses_workflow_stem_not_full_name(self, mock_datetime: MagicMock) -> None:
        mock_datetime.now.return_value.strftime.return_value = "20260101_000000"
        workflow_path = Path("/some/dir/deploy_steps.yaml")

        with patch.object(Path, "mkdir"):
            result = create_log_path(Path("logs"), workflow_path)

        assert "deploy_steps" in result.name
        assert ".yaml" not in result.name

    @patch("claude_loop.datetime")
    def test_creates_log_directory(self, mock_datetime: MagicMock) -> None:
        mock_datetime.now.return_value.strftime.return_value = "20260101_000000"
        log_dir = Path("logs/deep/nested")

        with patch.object(Path, "mkdir") as mock_mkdir:
            create_log_path(log_dir, Path("w.yaml"))

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestGetHeadCommit(unittest.TestCase):
    """Tests for get_head_commit()."""

    @patch("claude_loop.subprocess.run")
    def test_returns_commit_hash_on_success(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="abc1234\n")
        result = get_head_commit(Path("/some/repo"))

        assert result == "abc1234"
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path("/some/repo"),
            capture_output=True,
            text=True,
            check=False,
        )

    @patch("claude_loop.subprocess.run")
    def test_returns_none_on_nonzero_exit(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=128, stdout="")
        result = get_head_commit(Path("/not-a-repo"))

        assert result is None

    @patch("claude_loop.subprocess.run", side_effect=FileNotFoundError("git not found"))
    def test_returns_none_when_git_not_found(self, mock_run: MagicMock) -> None:
        result = get_head_commit(Path("/any"))

        assert result is None

    @patch("claude_loop.subprocess.run")
    def test_strips_whitespace_from_output(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="  def5678  \n")
        result = get_head_commit(Path("."))

        assert result == "def5678"


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


class TestBuildCommandWithLogFilePath(unittest.TestCase):
    """Tests for build_command() with log_file_path parameter."""

    def _make_step(self, prompt: str = "do stuff", args: list[str] | None = None) -> dict:
        return {"name": "test-step", "prompt": prompt, "args": args or []}

    def test_without_log_file_path(self) -> None:
        cmd = build_command("claude", "-p", [], self._make_step(), log_file_path=None)

        assert "--append-system-prompt" in cmd
        idx = cmd.index("--append-system-prompt")
        assert "INTERACTIVE" in cmd[idx + 1]

    def test_with_log_file_path_adds_system_prompt_arg(self) -> None:
        log_path = "/logs/workflow/20260404_120000_test.log"
        cmd = build_command("claude", "-p", [], self._make_step(), log_file_path=log_path)

        assert "--append-system-prompt" in cmd
        idx = cmd.index("--append-system-prompt")
        prompt_value = cmd[idx + 1]
        assert f"Current workflow log: {log_path}" in prompt_value
        assert "INTERACTIVE" in prompt_value

    def test_log_file_path_appended_after_step_args(self) -> None:
        step = self._make_step(args=["--verbose"])
        log_path = "/logs/test.log"
        cmd = build_command("claude", "-p", ["--model", "opus"], step, log_file_path=log_path)

        # Prompt comes first, then common args, then step args, then system prompt
        assert cmd[:6] == [
            "claude", "-p", "do stuff",
            "--model", "opus",
            "--verbose",
        ]
        assert cmd[6] == "--append-system-prompt"
        assert f"Current workflow log: {log_path}" in cmd[7]

    def test_empty_string_log_file_path_does_not_add_args(self) -> None:
        cmd = build_command("claude", "-p", [], self._make_step(), log_file_path="")

        assert "--append-system-prompt" in cmd
        idx = cmd.index("--append-system-prompt")
        assert "Current workflow log:" not in cmd[idx + 1]
        assert "INTERACTIVE" in cmd[idx + 1]


class TestParseArgsLoggingOptions(unittest.TestCase):
    """Tests for --no-log and --log-dir CLI options in parse_args()."""

    def _parse(self, args: list[str]) -> MagicMock:
        with patch("sys.argv", ["claude_loop.py", *args]):
            return parse_args()

    def test_no_log_default_is_false(self) -> None:
        result = self._parse([])
        assert result.no_log is False

    def test_no_log_flag_sets_true(self) -> None:
        result = self._parse(["--no-log"])
        assert result.no_log is True

    def test_log_dir_default(self) -> None:
        result = self._parse([])
        assert result.log_dir == Path("logs/workflow")

    def test_log_dir_custom(self) -> None:
        result = self._parse(["--log-dir", "/tmp/my_logs"])
        assert result.log_dir == Path("/tmp/my_logs")

    def test_no_log_and_log_dir_can_coexist(self) -> None:
        result = self._parse(["--no-log", "--log-dir", "/tmp/logs"])
        assert result.no_log is True
        assert result.log_dir == Path("/tmp/logs")


class TestNotifyCompletion(unittest.TestCase):
    """Tests for notify_completion()."""

    @patch("claude_loop._notify_toast")
    def test_calls_toast_on_success(self, mock_toast: MagicMock) -> None:
        notify_completion("title", "msg")
        mock_toast.assert_called_once_with("title", "msg")

    @patch("claude_loop._notify_beep")
    @patch("claude_loop._notify_toast", side_effect=Exception("fail"))
    def test_falls_back_to_beep_on_toast_failure(self, mock_toast: MagicMock, mock_beep: MagicMock) -> None:
        notify_completion("title", "msg")
        mock_beep.assert_called_once_with("title", "msg")

    @patch("claude_loop.subprocess.run")
    def test_toast_escapes_single_quotes(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        _notify_toast("it's done", "user's workflow")
        call_args = mock_run.call_args[0][0]
        cmd_str = " ".join(call_args)
        assert "it''s done" in cmd_str


class TestResolveMode(unittest.TestCase):
    """Tests for resolve_mode()."""

    def test_default_is_interactive(self) -> None:
        assert resolve_mode({}, cli_auto=False, cli_interactive=False) is False

    def test_yaml_auto_true(self) -> None:
        assert resolve_mode({"mode": {"auto": True}}, False, False) is True

    def test_cli_auto_overrides_yaml(self) -> None:
        assert resolve_mode({"mode": {"auto": False}}, cli_auto=True, cli_interactive=False) is True

    def test_cli_interactive_overrides_yaml(self) -> None:
        assert resolve_mode({"mode": {"auto": True}}, cli_auto=False, cli_interactive=True) is False


class TestBuildCommandWithMode(unittest.TestCase):
    """Tests for build_command() with auto_mode parameter."""

    def _make_step(self) -> dict:
        return {"name": "test", "prompt": "/test", "args": []}

    def test_auto_mode_includes_auto_prompt(self) -> None:
        cmd = build_command("claude", "-p", [], self._make_step(), auto_mode=True)
        assert "--append-system-prompt" in cmd
        idx = cmd.index("--append-system-prompt")
        assert "AUTO" in cmd[idx + 1]

    def test_interactive_mode_includes_interactive_prompt(self) -> None:
        cmd = build_command("claude", "-p", [], self._make_step(), auto_mode=False)
        assert "--append-system-prompt" in cmd
        idx = cmd.index("--append-system-prompt")
        assert "INTERACTIVE" in cmd[idx + 1]

    def test_log_and_mode_combined_in_single_prompt(self) -> None:
        cmd = build_command("claude", "-p", [], self._make_step(),
                           log_file_path="/log.log", auto_mode=True)
        assert cmd.count("--append-system-prompt") == 1


class TestParseArgsModeOptions(unittest.TestCase):
    """Tests for --auto / --interactive CLI options."""

    def _parse(self, args: list[str]) -> argparse.Namespace:
        with patch("sys.argv", ["claude_loop.py", *args]):
            return parse_args()

    def test_auto_default_is_false(self) -> None:
        result = self._parse([])
        assert result.auto is False

    def test_interactive_default_is_false(self) -> None:
        result = self._parse([])
        assert result.interactive is False

    def test_auto_flag(self) -> None:
        result = self._parse(["--auto"])
        assert result.auto is True

    def test_interactive_flag(self) -> None:
        result = self._parse(["--interactive"])
        assert result.interactive is True

    def test_auto_and_interactive_are_mutually_exclusive(self) -> None:
        with self.assertRaises(SystemExit):
            self._parse(["--auto", "--interactive"])


class TestParseArgsNotifyOption(unittest.TestCase):
    """Tests for --no-notify CLI option."""

    def _parse(self, args: list[str]) -> argparse.Namespace:
        with patch("sys.argv", ["claude_loop.py", *args]):
            return parse_args()

    def test_no_notify_default_is_false(self) -> None:
        result = self._parse([])
        assert result.no_notify is False

    def test_no_notify_flag(self) -> None:
        result = self._parse(["--no-notify"])
        assert result.no_notify is True


class TestResolveCommandConfigAutoArgs(unittest.TestCase):
    """Tests for auto_args in resolve_command_config()."""

    def test_returns_auto_args(self) -> None:
        config = {"command": {"auto_args": ["--disallowedTools AskUserQuestion"]}}
        _, _, _, auto_args = resolve_command_config(config)
        assert "--disallowedTools" in auto_args

    def test_empty_auto_args_default(self) -> None:
        config = {"command": {}}
        _, _, _, auto_args = resolve_command_config(config)
        assert auto_args == []


if __name__ == "__main__":
    unittest.main()
