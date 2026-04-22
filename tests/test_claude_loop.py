"""Tests for logging features in scripts/claude_loop.py."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch, MagicMock

# Add the scripts directory to sys.path so we can import claude_loop
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from claude_loop import parse_args
from claude_loop_lib.workflow import (
    load_workflow, get_steps, resolve_defaults,
    resolve_command_config, resolve_mode,
)
from claude_loop_lib.feedbacks import (
    parse_feedback_frontmatter, load_feedbacks, consume_feedbacks,
)
from claude_loop_lib.commands import build_command
from claude_loop_lib.logging_utils import (
    create_log_path, format_duration,
)
from claude_loop_lib.git_utils import (
    get_head_commit, check_uncommitted_changes, auto_commit_changes,
)
from claude_loop_lib.notify import notify_completion, _notify_toast


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


class TestGetHeadCommit(unittest.TestCase):
    """Tests for get_head_commit()."""

    @patch("claude_loop_lib.git_utils.subprocess.run")
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

    @patch("claude_loop_lib.git_utils.subprocess.run")
    def test_returns_none_on_nonzero_exit(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=128, stdout="")
        result = get_head_commit(Path("/not-a-repo"))

        assert result is None

    @patch("claude_loop_lib.git_utils.subprocess.run", side_effect=FileNotFoundError("git not found"))
    def test_returns_none_when_git_not_found(self, mock_run: MagicMock) -> None:
        result = get_head_commit(Path("/any"))

        assert result is None

    @patch("claude_loop_lib.git_utils.subprocess.run")
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

        assert "--append-system-prompt" not in cmd

    def test_with_log_file_path_adds_system_prompt_arg(self) -> None:
        log_path = "/logs/workflow/20260404_120000_test.log"
        cmd = build_command("claude", "-p", [], self._make_step(), log_file_path=log_path)

        assert "--append-system-prompt" in cmd
        idx = cmd.index("--append-system-prompt")
        prompt_value = cmd[idx + 1]
        assert f"Current workflow log: {log_path}" in prompt_value

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

        assert "--append-system-prompt" not in cmd


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


class TestResolveMode(unittest.TestCase):
    """Tests for resolve_mode()."""

    def test_default_is_not_auto(self) -> None:
        assert resolve_mode({}, cli_auto=False) is False

    def test_yaml_auto_true(self) -> None:
        assert resolve_mode({"mode": {"auto": True}}, cli_auto=False) is True

    def test_cli_auto_overrides_yaml(self) -> None:
        assert resolve_mode({"mode": {"auto": False}}, cli_auto=True) is True


class TestBuildCommandWithMode(unittest.TestCase):
    """Tests for build_command() with auto_mode parameter."""

    def _make_step(self) -> dict:
        return {"name": "test", "prompt": "/test", "args": []}

    def test_auto_mode_includes_auto_prompt(self) -> None:
        cmd = build_command("claude", "-p", [], self._make_step(), auto_mode=True)
        assert "--append-system-prompt" in cmd
        idx = cmd.index("--append-system-prompt")
        assert "AUTO" in cmd[idx + 1]

    def test_non_auto_mode_has_no_mode_prompt(self) -> None:
        cmd = build_command("claude", "-p", [], self._make_step(), auto_mode=False)
        assert "--append-system-prompt" not in cmd

    def test_log_and_mode_combined_in_single_prompt(self) -> None:
        cmd = build_command("claude", "-p", [], self._make_step(),
                           log_file_path="/log.log", auto_mode=True)
        assert cmd.count("--append-system-prompt") == 1


class TestParseArgsAutoOption(unittest.TestCase):
    """Tests for --auto CLI option."""

    def _parse(self, args: list[str]) -> argparse.Namespace:
        with patch("sys.argv", ["claude_loop.py", *args]):
            return parse_args()

    def test_auto_default_is_false(self) -> None:
        result = self._parse([])
        assert result.auto is False

    def test_auto_flag(self) -> None:
        result = self._parse(["--auto"])
        assert result.auto is True


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


class TestCheckUncommittedChanges(unittest.TestCase):
    """Tests for check_uncommitted_changes()."""

    @patch("claude_loop_lib.git_utils.subprocess.run")
    def test_returns_true_when_changes_exist(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout=" M file.txt\n")
        result = check_uncommitted_changes(Path("/repo"))

        assert result is True
        mock_run.assert_called_once_with(
            ["git", "status", "--porcelain"],
            cwd=Path("/repo"), capture_output=True, text=True, check=False,
        )

    @patch("claude_loop_lib.git_utils.subprocess.run")
    def test_returns_false_when_no_changes(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        result = check_uncommitted_changes(Path("/repo"))

        assert result is False

    @patch("claude_loop_lib.git_utils.subprocess.run", side_effect=FileNotFoundError("git not found"))
    def test_returns_false_when_git_not_found(self, mock_run: MagicMock) -> None:
        result = check_uncommitted_changes(Path("/any"))

        assert result is False


class TestAutoCommitChanges(unittest.TestCase):
    """Tests for auto_commit_changes()."""

    @patch("claude_loop_lib.git_utils.get_head_commit", return_value="abc1234")
    @patch("claude_loop_lib.git_utils.subprocess.run")
    def test_success_returns_commit_hash(self, mock_run: MagicMock, mock_head: MagicMock) -> None:
        result = auto_commit_changes(Path("/repo"))

        assert result == "abc1234"
        assert mock_run.call_count == 2
        mock_run.assert_any_call(["git", "add", "-A"], cwd=Path("/repo"), check=True)
        mock_run.assert_any_call(
            ["git", "commit", "-m", "auto-commit before workflow"],
            cwd=Path("/repo"), check=True,
        )

    @patch("claude_loop_lib.git_utils.subprocess.run", side_effect=subprocess.CalledProcessError(1, "git add"))
    def test_returns_none_on_git_add_failure(self, mock_run: MagicMock) -> None:
        result = auto_commit_changes(Path("/repo"))

        assert result is None

    @patch("claude_loop_lib.git_utils.subprocess.run")
    def test_returns_none_on_git_commit_failure(self, mock_run: MagicMock) -> None:
        def side_effect(*args, **kwargs):
            if args[0][1] == "commit":
                raise subprocess.CalledProcessError(1, "git commit")
            return MagicMock(returncode=0)
        mock_run.side_effect = side_effect
        result = auto_commit_changes(Path("/repo"))

        assert result is None


class TestParseArgsAutoCommitBefore(unittest.TestCase):
    """Tests for --auto-commit-before CLI option."""

    def _parse(self, args: list[str]) -> argparse.Namespace:
        with patch("sys.argv", ["claude_loop.py", *args]):
            return parse_args()

    def test_default_is_false(self) -> None:
        result = self._parse([])
        assert result.auto_commit_before is False

    def test_flag_sets_true(self) -> None:
        result = self._parse(["--auto-commit-before"])
        assert result.auto_commit_before is True


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


class TestBuildCommandWithFeedbacks(unittest.TestCase):
    """Tests for build_command() with feedbacks parameter."""

    def _build(self, feedbacks: list[str] | None = None) -> list[str]:
        return build_command(
            executable="claude",
            prompt_flag="-p",
            common_args=[],
            step={"name": "test", "prompt": "/test", "args": []},
            feedbacks=feedbacks,
        )

    def test_feedbacks_injected(self) -> None:
        cmd = self._build(feedbacks=["Fix the typo"])
        assert "--append-system-prompt" in cmd
        prompt_idx = cmd.index("--append-system-prompt")
        prompt_value = cmd[prompt_idx + 1]
        assert "## User Feedback" in prompt_value
        assert "Fix the typo" in prompt_value

    def test_multiple_feedbacks(self) -> None:
        cmd = self._build(feedbacks=["First feedback", "Second feedback"])
        prompt_idx = cmd.index("--append-system-prompt")
        prompt_value = cmd[prompt_idx + 1]
        assert "First feedback" in prompt_value
        assert "Second feedback" in prompt_value
        assert "---" in prompt_value

    def test_no_feedbacks(self) -> None:
        cmd = self._build(feedbacks=None)
        assert "--append-system-prompt" not in cmd


class TestResolveDefaults(unittest.TestCase):
    """Tests for resolve_defaults()."""

    def test_returns_empty_when_key_absent(self) -> None:
        assert resolve_defaults({}) == {}

    def test_parses_model_and_effort(self) -> None:
        result = resolve_defaults({"defaults": {"model": "opus", "effort": "high"}})
        assert result == {"model": "opus", "effort": "high"}

    def test_omits_absent_keys(self) -> None:
        result = resolve_defaults({"defaults": {"model": "opus"}})
        assert result == {"model": "opus"}
        assert "effort" not in result

    def test_raises_on_non_mapping(self) -> None:
        with self.assertRaises(SystemExit):
            resolve_defaults({"defaults": "opus"})

    def test_raises_on_empty_string(self) -> None:
        with self.assertRaises(SystemExit):
            resolve_defaults({"defaults": {"model": ""}})

    def test_raises_on_non_string(self) -> None:
        with self.assertRaises(SystemExit):
            resolve_defaults({"defaults": {"effort": 5}})


class TestBuildCommandWithModelEffort(unittest.TestCase):
    """Tests for build_command() with defaults/model/effort."""

    def _make_step(self, **kwargs: Any) -> dict:
        step = {"name": "test", "prompt": "/test", "args": []}
        step.update(kwargs)
        return step

    def test_no_model_no_effort_when_unset(self) -> None:
        cmd = build_command("claude", "-p", [], self._make_step(), defaults={})
        assert "--model" not in cmd
        assert "--effort" not in cmd

    def test_uses_defaults_when_step_omits(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(),
            defaults={"model": "sonnet", "effort": "medium"},
        )
        assert "--model" in cmd
        assert cmd[cmd.index("--model") + 1] == "sonnet"
        assert "--effort" in cmd
        assert cmd[cmd.index("--effort") + 1] == "medium"

    def test_step_overrides_defaults(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(model="opus"),
            defaults={"model": "sonnet"},
        )
        assert cmd[cmd.index("--model") + 1] == "opus"
        assert "sonnet" not in cmd

    def test_step_sets_when_no_defaults(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(effort="high"), defaults={},
        )
        assert cmd[cmd.index("--effort") + 1] == "high"
        assert "--model" not in cmd

    def test_defaults_none_equivalent_to_empty(self) -> None:
        cmd = build_command("claude", "-p", [], self._make_step(), defaults=None)
        assert "--model" not in cmd
        assert "--effort" not in cmd

    def test_model_effort_before_append_system_prompt(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(),
            log_file_path="/log.log",
            defaults={"model": "sonnet", "effort": "medium"},
        )
        asp_idx = cmd.index("--append-system-prompt")
        assert cmd.index("--model") < asp_idx
        assert cmd.index("--effort") < asp_idx


class TestGetStepsModelEffort(unittest.TestCase):
    """Tests for get_steps() with model/effort fields."""

    def _config(self, step: dict) -> dict:
        return {"steps": [step]}

    def test_step_without_model_effort_omits_keys(self) -> None:
        steps = get_steps(self._config({"name": "s", "prompt": "/s"}))
        assert "model" not in steps[0]
        assert "effort" not in steps[0]

    def test_step_with_model_and_effort(self) -> None:
        steps = get_steps(self._config(
            {"name": "s", "prompt": "/s", "model": "opus", "effort": "high"}
        ))
        assert steps[0]["model"] == "opus"
        assert steps[0]["effort"] == "high"

    def test_step_with_only_effort(self) -> None:
        steps = get_steps(self._config({"name": "s", "prompt": "/s", "effort": "low"}))
        assert steps[0]["effort"] == "low"
        assert "model" not in steps[0]

    def test_raises_on_empty_model(self) -> None:
        with self.assertRaises(SystemExit):
            get_steps(self._config({"name": "s", "prompt": "/s", "model": ""}))

    def test_raises_on_non_string_effort(self) -> None:
        with self.assertRaises(SystemExit):
            get_steps(self._config({"name": "s", "prompt": "/s", "effort": 5}))

    def test_none_value_treated_as_absent(self) -> None:
        steps = get_steps(self._config(
            {"name": "s", "prompt": "/s", "model": None, "effort": None}
        ))
        assert "model" not in steps[0]
        assert "effort" not in steps[0]


class TestYamlIntegration(unittest.TestCase):
    """Integration: load_workflow + get_steps + resolve_defaults + build_command."""

    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_full_yaml_flow(self) -> None:
        yaml_path = self.tmp_dir / "wf.yaml"
        yaml_path.write_text(
            "defaults:\n"
            "  model: sonnet\n"
            "  effort: medium\n"
            "steps:\n"
            "  - name: heavy\n"
            "    prompt: /heavy\n"
            "    model: opus\n"
            "    effort: high\n"
            "  - name: light\n"
            "    prompt: /light\n"
            "    effort: low\n",
            encoding="utf-8",
        )
        config = load_workflow(yaml_path)
        steps = get_steps(config)
        defaults = resolve_defaults(config)

        # Heavy step overrides both
        heavy_cmd = build_command("claude", "-p", [], steps[0], defaults=defaults)
        assert heavy_cmd[heavy_cmd.index("--model") + 1] == "opus"
        assert heavy_cmd[heavy_cmd.index("--effort") + 1] == "high"

        # Light step inherits model from defaults, overrides effort
        light_cmd = build_command("claude", "-p", [], steps[1], defaults=defaults)
        assert light_cmd[light_cmd.index("--model") + 1] == "sonnet"
        assert light_cmd[light_cmd.index("--effort") + 1] == "low"


if __name__ == "__main__":
    unittest.main()
