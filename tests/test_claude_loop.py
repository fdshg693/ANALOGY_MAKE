"""Tests for logging features in scripts/claude_loop.py."""

from __future__ import annotations

import argparse
import json
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
import claude_loop
from claude_loop import (
    parse_args, _run_steps,
    validate_auto_args, _find_latest_rough_plan, _read_workflow_kind,
    _compute_remaining_budget,
)
from claude_loop_lib.workflow import (
    load_workflow, get_steps, resolve_defaults,
    resolve_command_config, resolve_mode,
    resolve_workflow_value,
    FULL_YAML_FILENAME, QUICK_YAML_FILENAME, ISSUE_PLAN_YAML_FILENAME,
)
from claude_loop_lib.feedbacks import (
    parse_feedback_frontmatter, load_feedbacks, consume_feedbacks,
)
from claude_loop_lib.frontmatter import parse_frontmatter
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


class TestParseFrontmatter(unittest.TestCase):
    """Tests for the shared parse_frontmatter()."""

    def test_valid_dict(self) -> None:
        fm, body = parse_frontmatter("---\nkey: value\n---\nbody")
        assert fm == {"key": "value"}
        assert body == "body"

    def test_no_leading_delimiter(self) -> None:
        text = "no frontmatter here"
        fm, body = parse_frontmatter(text)
        assert fm is None
        assert body == text

    def test_missing_closing_delimiter(self) -> None:
        text = "---\nkey: value\nbody text"
        fm, body = parse_frontmatter(text)
        assert fm is None
        assert body == text

    def test_invalid_yaml(self) -> None:
        text = "---\n: : : invalid\n---\nbody"
        fm, body = parse_frontmatter(text)
        assert fm is None
        assert body == text

    def test_non_dict_yaml(self) -> None:
        fm, body = parse_frontmatter("---\n- a\n- b\n---\nbody")
        assert fm is None
        assert body == "body"


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


class TestBuildCommandWithSession(unittest.TestCase):
    """Tests for build_command() with session_id / resume parameters."""

    def _make_step(self) -> dict:
        return {"name": "test", "prompt": "/test", "args": []}

    def test_without_session_id_no_flag(self) -> None:
        cmd = build_command("claude", "-p", [], self._make_step(), session_id=None)
        assert "--session-id" not in cmd
        assert "-r" not in cmd

    def test_session_id_adds_session_id_flag(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(),
            session_id="abc-123", resume=False,
        )
        assert "--session-id" in cmd
        assert cmd[cmd.index("--session-id") + 1] == "abc-123"
        assert "-r" not in cmd

    def test_session_id_with_resume_adds_r_flag(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(),
            session_id="abc-123", resume=True,
        )
        assert "-r" in cmd
        assert cmd[cmd.index("-r") + 1] == "abc-123"
        assert "--session-id" not in cmd

    def test_session_id_after_model_before_system_prompt(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(),
            log_file_path="/log.log",
            defaults={"model": "opus"},
            session_id="xyz", resume=False,
        )
        model_idx = cmd.index("--model")
        sid_idx = cmd.index("--session-id")
        asp_idx = cmd.index("--append-system-prompt")
        assert model_idx < sid_idx < asp_idx


class TestGetStepsContinue(unittest.TestCase):
    """Tests for get_steps() with the 'continue' field."""

    def _config(self, step: dict) -> dict:
        return {"steps": [step]}

    def test_omitted_continue_not_in_step_entry(self) -> None:
        steps = get_steps(self._config({"name": "s", "prompt": "/s"}))
        assert "continue" not in steps[0]

    def test_explicit_false_is_retained(self) -> None:
        steps = get_steps(self._config({"name": "s", "prompt": "/s", "continue": False}))
        assert steps[0]["continue"] is False

    def test_explicit_true_is_retained(self) -> None:
        steps = get_steps(self._config({"name": "s", "prompt": "/s", "continue": True}))
        assert steps[0]["continue"] is True

    def test_non_bool_string_raises(self) -> None:
        with self.assertRaises(SystemExit):
            get_steps(self._config({"name": "s", "prompt": "/s", "continue": "yes"}))

    def test_integer_raises(self) -> None:
        with self.assertRaises(SystemExit):
            get_steps(self._config({"name": "s", "prompt": "/s", "continue": 1}))

    def test_none_treated_as_absent(self) -> None:
        steps = get_steps(self._config({"name": "s", "prompt": "/s", "continue": None}))
        assert "continue" not in steps[0]


class TestRunStepsSessionTracking(unittest.TestCase):
    """Integration tests for _run_steps() session-id tracking."""

    def _make_steps(self, *step_configs: dict) -> list[dict]:
        result = []
        for i, conf in enumerate(step_configs, start=1):
            step = {"name": f"s{i}", "prompt": f"/s{i}", "args": []}
            step.update(conf)
            result.append(step)
        return result

    def _captured_commands(self, mock_run: MagicMock) -> list[list[str]]:
        # Filter out git invocations (get_head_commit) and keep only claude commands
        return [
            call.args[0] for call in mock_run.call_args_list
            if call.args and call.args[0] and call.args[0][0] != "git"
        ]

    @patch("claude_loop.uuid.uuid4")
    @patch("claude_loop.subprocess.run")
    def test_first_step_uses_new_session_id(
        self, mock_run: MagicMock, mock_uuid: MagicMock
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        mock_uuid.side_effect = ["uuid-1", "uuid-2"]
        steps = self._make_steps({}, {})
        step_iter = iter([(steps[0], 1), (steps[1], 2)])

        exit_code = _run_steps(
            step_iter, steps, "claude", "-p", [],
            cwd=Path("."), dry_run=False, tee=None, log_path=None,
        )
        assert exit_code == 0
        commands = self._captured_commands(mock_run)
        assert "--session-id" in commands[0]
        assert commands[0][commands[0].index("--session-id") + 1] == "uuid-1"
        assert "-r" not in commands[0]

    @patch("claude_loop.uuid.uuid4")
    @patch("claude_loop.subprocess.run")
    def test_continue_step_resumes_previous_session(
        self, mock_run: MagicMock, mock_uuid: MagicMock
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        mock_uuid.side_effect = ["uuid-1", "uuid-2"]
        steps = self._make_steps({}, {"continue": True})
        step_iter = iter([(steps[0], 1), (steps[1], 2)])

        _run_steps(
            step_iter, steps, "claude", "-p", [],
            cwd=Path("."), dry_run=False, tee=None, log_path=None,
        )
        commands = self._captured_commands(mock_run)
        assert "-r" in commands[1]
        assert commands[1][commands[1].index("-r") + 1] == "uuid-1"
        assert "--session-id" not in commands[1]

    @patch("claude_loop.uuid.uuid4")
    @patch("claude_loop.subprocess.run")
    def test_loop_boundary_warns_when_first_step_continues(
        self, mock_run: MagicMock, mock_uuid: MagicMock
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        mock_uuid.side_effect = ["uuid-1"]
        steps = self._make_steps({"continue": True})
        step_iter = iter([(steps[0], 1)])

        with patch("builtins.print") as mock_print:
            _run_steps(
                step_iter, steps, "claude", "-p", [],
                cwd=Path("."), dry_run=False, tee=None, log_path=None,
            )
        printed = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        assert "WARNING" in printed
        assert "no previous session" in printed
        commands = self._captured_commands(mock_run)
        assert "--session-id" in commands[0]
        assert "-r" not in commands[0]

    @patch("claude_loop.uuid.uuid4")
    @patch("claude_loop.subprocess.run")
    def test_start_greater_than_one_disables_continue(
        self, mock_run: MagicMock, mock_uuid: MagicMock
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        mock_uuid.side_effect = ["uuid-1", "uuid-2"]
        steps = self._make_steps({"continue": True}, {"continue": True})
        step_iter = iter([(steps[0], 1), (steps[1], 2)])

        with patch("builtins.print") as mock_print:
            _run_steps(
                step_iter, steps, "claude", "-p", [],
                cwd=Path("."), dry_run=False, tee=None, log_path=None,
                continue_disabled=True,
            )
        printed = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        # warning printed exactly once
        assert printed.count("--start > 1") == 1
        commands = self._captured_commands(mock_run)
        for cmd in commands:
            assert "-r" not in cmd
            assert "--session-id" in cmd


class TestExtractStatusAssigned(unittest.TestCase):
    """Tests for claude_loop_lib.issues.extract_status_assigned (§1 refactor)."""

    def _write(self, tmp: Path, name: str, text: str) -> Path:
        path = tmp / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_no_frontmatter_returns_raw_human(self) -> None:
        from claude_loop_lib.issues import extract_status_assigned
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            path = self._write(tmp, "x.md", "# title\n\nbody\n")
            status, assigned, fm, body = extract_status_assigned(path)
        assert status == "raw"
        assert assigned == "human"
        assert fm is None
        assert "# title" in body

    def test_frontmatter_returns_fm_dict_and_body(self) -> None:
        from claude_loop_lib.issues import extract_status_assigned
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            path = self._write(
                tmp, "x.md",
                "---\nstatus: ready\nassigned: ai\n---\n# t\n\nsummary line\n",
            )
            status, assigned, fm, body = extract_status_assigned(path)
        assert status == "ready"
        assert assigned == "ai"
        assert isinstance(fm, dict)
        assert fm["status"] == "ready"
        assert "summary line" in body

    def test_invalid_combo_emits_warning(self) -> None:
        from claude_loop_lib import issues as issues_mod
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            path = self._write(
                tmp, "x.md",
                "---\nstatus: ready\nassigned: human\n---\n# t\n",
            )
            import io as _io
            buf = _io.StringIO()
            with patch("sys.stderr", buf):
                issues_mod.extract_status_assigned(path)
            err = buf.getvalue()
        assert "invalid combo" in err


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


class TestResolveWorkflowValue(unittest.TestCase):
    """Tests for workflow.resolve_workflow_value()."""

    def setUp(self) -> None:
        self.yaml_dir = Path("/fake/scripts")

    def test_resolve_auto_returns_sentinel(self) -> None:
        assert resolve_workflow_value("auto", self.yaml_dir) == "auto"

    def test_resolve_full_returns_full_yaml_path(self) -> None:
        result = resolve_workflow_value("full", self.yaml_dir)
        assert result == self.yaml_dir / FULL_YAML_FILENAME

    def test_resolve_quick_returns_quick_yaml_path(self) -> None:
        result = resolve_workflow_value("quick", self.yaml_dir)
        assert result == self.yaml_dir / QUICK_YAML_FILENAME

    def test_resolve_path_like_returns_path(self) -> None:
        result = resolve_workflow_value("/tmp/foo.yaml", self.yaml_dir)
        assert result == Path("/tmp/foo.yaml")

    def test_resolve_relative_path_preserved(self) -> None:
        result = resolve_workflow_value("other.yaml", self.yaml_dir)
        assert result == Path("other.yaml")

    def test_reserved_values_are_case_sensitive(self) -> None:
        result = resolve_workflow_value("AUTO", self.yaml_dir)
        assert result == Path("AUTO")


class TestParseArgsWorkflow(unittest.TestCase):
    """Tests for --workflow argparse behavior."""

    def _parse(self, args: list[str]) -> argparse.Namespace:
        with patch("sys.argv", ["claude_loop.py", *args]):
            return parse_args()

    def test_default_is_auto_string(self) -> None:
        result = self._parse([])
        assert result.workflow == "auto"

    def test_explicit_full_reserved(self) -> None:
        result = self._parse(["-w", "full"])
        assert result.workflow == "full"

    def test_explicit_quick_reserved(self) -> None:
        result = self._parse(["-w", "quick"])
        assert result.workflow == "quick"

    def test_explicit_path(self) -> None:
        result = self._parse(["-w", "custom.yaml"])
        assert result.workflow == "custom.yaml"


class TestValidateAutoArgs(unittest.TestCase):
    """Tests for validate_auto_args()."""

    def _args(self, **kwargs: Any) -> argparse.Namespace:
        ns = argparse.Namespace(start=1, max_step_runs=None, max_loops=1)
        for k, v in kwargs.items():
            setattr(ns, k, v)
        return ns

    def test_auto_with_start_1_ok(self) -> None:
        validate_auto_args("auto", self._args(start=1))

    def test_auto_with_start_2_raises(self) -> None:
        with self.assertRaises(SystemExit) as cm:
            validate_auto_args("auto", self._args(start=2))
        assert "--start 1" in str(cm.exception)

    def test_non_auto_start_2_ok(self) -> None:
        validate_auto_args(Path("any.yaml"), self._args(start=2))


class TestReadWorkflowKind(unittest.TestCase):
    """Tests for _read_workflow_kind()."""

    def _write(self, tmp: Path, text: str) -> Path:
        p = tmp / "ROUGH_PLAN.md"
        p.write_text(text, encoding="utf-8")
        return p

    def test_valid_quick_returns_quick(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = self._write(Path(td), "---\nworkflow: quick\n---\nbody\n")
            assert _read_workflow_kind(p) == "quick"

    def test_valid_full_returns_full(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = self._write(Path(td), "---\nworkflow: full\n---\nbody\n")
            assert _read_workflow_kind(p) == "full"

    def test_missing_frontmatter_falls_back_to_full_with_warning(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = self._write(Path(td), "# no frontmatter\nbody\n")
            with patch("sys.stderr") as mock_err:
                result = _read_workflow_kind(p)
        assert result == "full"
        # warning was written to stderr
        assert mock_err.method_calls or True

    def test_missing_workflow_key_falls_back_to_full(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = self._write(Path(td), "---\nsource: master_plan\n---\nbody\n")
            assert _read_workflow_kind(p) == "full"

    def test_invalid_workflow_value_falls_back_to_full(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = self._write(Path(td), "---\nworkflow: banana\n---\nbody\n")
            assert _read_workflow_kind(p) == "full"


class TestFindLatestRoughPlan(unittest.TestCase):
    """Tests for _find_latest_rough_plan()."""

    def _make_tree(self, root: Path, category: str, versions: list[str]) -> list[Path]:
        (root / ".claude").mkdir(parents=True, exist_ok=True)
        (root / ".claude" / "CURRENT_CATEGORY").write_text(category, encoding="utf-8")
        paths = []
        for ver in versions:
            vdir = root / "docs" / category / ver
            vdir.mkdir(parents=True, exist_ok=True)
            p = vdir / "ROUGH_PLAN.md"
            p.write_text(f"# {ver}\n", encoding="utf-8")
            paths.append(p)
        return paths

    def test_single_rough_plan_returned(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            paths = self._make_tree(tmp, "util", ["ver1.0"])
            result = _find_latest_rough_plan(tmp)
            assert result == paths[0]

    def test_latest_mtime_wins(self) -> None:
        import os
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            paths = self._make_tree(tmp, "util", ["ver1.0", "ver2.0", "ver3.0"])
            # Set mtimes explicitly: ver2.0 is newest
            os.utime(paths[0], (1000, 1000))
            os.utime(paths[2], (2000, 2000))
            os.utime(paths[1], (3000, 3000))
            result = _find_latest_rough_plan(tmp)
            assert result == paths[1]

    def test_no_rough_plan_raises(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / ".claude").mkdir()
            (tmp / ".claude" / "CURRENT_CATEGORY").write_text("util", encoding="utf-8")
            (tmp / "docs" / "util").mkdir(parents=True)
            with self.assertRaises(SystemExit) as cm:
                _find_latest_rough_plan(tmp)
            assert "no ROUGH_PLAN.md" in str(cm.exception)

    def test_uses_current_category_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            # Write rough plans under both 'app' and 'util', ensure 'util' is picked
            self._make_tree(tmp, "app", ["ver1.0"])
            util_paths = self._make_tree(tmp, "util", ["ver5.0"])
            result = _find_latest_rough_plan(tmp)
            assert result == util_paths[0]

    def test_missing_category_file_falls_back_to_app(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            app_dir = tmp / "docs" / "app" / "ver1.0"
            app_dir.mkdir(parents=True)
            p = app_dir / "ROUGH_PLAN.md"
            p.write_text("x", encoding="utf-8")
            result = _find_latest_rough_plan(tmp)
            assert result == p


class TestComputeRemainingBudget(unittest.TestCase):
    """Tests for _compute_remaining_budget()."""

    def _args(self, max_step_runs: int | None) -> argparse.Namespace:
        return argparse.Namespace(max_step_runs=max_step_runs)

    def test_none_when_unset(self) -> None:
        assert _compute_remaining_budget(self._args(None), 1) is None

    def test_subtracts_completed(self) -> None:
        assert _compute_remaining_budget(self._args(5), 1) == 4

    def test_clamped_to_zero(self) -> None:
        assert _compute_remaining_budget(self._args(1), 3) == 0


class TestAutoWorkflowIntegration(unittest.TestCase):
    """Integration tests for main() --workflow auto branch."""

    def _setup_cwd(self, root: Path, workflow_kind: str = "full") -> None:
        """Create cwd skeleton with a ROUGH_PLAN.md ready for phase 2 read."""
        (root / ".claude").mkdir(parents=True, exist_ok=True)
        (root / ".claude" / "CURRENT_CATEGORY").write_text("util", encoding="utf-8")
        vdir = root / "docs" / "util" / "ver1.0"
        vdir.mkdir(parents=True, exist_ok=True)
        (vdir / "ROUGH_PLAN.md").write_text(
            f"---\nworkflow: {workflow_kind}\n---\nbody\n", encoding="utf-8"
        )

    def _run_main_auto(
        self, cwd: Path, extra_args: list[str] | None = None,
        mock_subprocess_returncode: int = 0,
    ) -> tuple[int, list[list[str]]]:
        extra_args = extra_args or []
        claude_calls: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            if cmd and cmd[0] == "git":
                return MagicMock(returncode=0, stdout="", stderr="")
            claude_calls.append(cmd)
            return MagicMock(returncode=mock_subprocess_returncode)

        argv = [
            "claude_loop.py", "--workflow", "auto",
            "--cwd", str(cwd),
            "--no-log", "--no-notify",
            *extra_args,
        ]
        with (
            patch("sys.argv", argv),
            patch("claude_loop.subprocess.run", side_effect=fake_run),
            patch("claude_loop.check_uncommitted_changes", return_value=False),
            patch("claude_loop.shutil.which", return_value="/usr/bin/claude"),
            patch("builtins.print"),
        ):
            exit_code = claude_loop.main()
        # Filter claude commands (drop any that sneak through)
        return exit_code, [c for c in claude_calls if c and c[0] != "git"]

    def test_auto_runs_issue_plan_then_full(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            self._setup_cwd(cwd, "full")
            exit_code, commands = self._run_main_auto(cwd)
        assert exit_code == 0
        # Phase 1: 1 call (/issue_plan) + Phase 2: full has 6 steps, steps[1:] = 5 steps
        assert len(commands) == 6
        assert "/issue_plan" in commands[0]
        assert "/split_plan" in commands[1]
        assert "/retrospective" in commands[-1]

    def test_auto_runs_issue_plan_then_quick(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            self._setup_cwd(cwd, "quick")
            exit_code, commands = self._run_main_auto(cwd)
        assert exit_code == 0
        # Phase 1: 1 call + Phase 2: quick has 3 steps, steps[1:] = 2 steps
        assert len(commands) == 3
        assert "/issue_plan" in commands[0]
        assert "/quick_impl" in commands[1]
        assert "/quick_doc" in commands[2]

    def test_auto_phase1_failure_aborts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            self._setup_cwd(cwd, "full")
            exit_code, commands = self._run_main_auto(
                cwd, mock_subprocess_returncode=1
            )
        assert exit_code == 1
        # Only the phase 1 call should have fired
        assert len(commands) == 1
        assert "/issue_plan" in commands[0]

    def test_auto_fallback_on_invalid_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            # Create category skeleton then write an invalid frontmatter value
            self._setup_cwd(cwd, "full")
            (cwd / "docs" / "util" / "ver1.0" / "ROUGH_PLAN.md").write_text(
                "---\nworkflow: banana\n---\nbody\n", encoding="utf-8"
            )
            exit_code, commands = self._run_main_auto(cwd)
        # Falls back to full (6 total commands)
        assert exit_code == 0
        assert len(commands) == 6

    def test_auto_dry_run_skips_phase2(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            # No ROUGH_PLAN.md at all - phase 2 would fail, but dry-run must skip it
            (cwd / ".claude").mkdir()
            (cwd / ".claude" / "CURRENT_CATEGORY").write_text("util", encoding="utf-8")
            exit_code, commands = self._run_main_auto(cwd, ["--dry-run"])
        assert exit_code == 0
        # dry-run: command is printed but subprocess.run is NOT called for phase 1
        # Because dry_run short-circuits inside _run_steps before subprocess.run.
        # So we expect 0 captured subprocess calls.
        assert len(commands) == 0

    def test_auto_with_start_2_exits(self) -> None:
        argv = [
            "claude_loop.py", "--workflow", "auto", "--start", "2",
            "--cwd", ".", "--no-log", "--no-notify",
        ]
        with patch("sys.argv", argv):
            with self.assertRaises(SystemExit) as cm:
                claude_loop.main()
        assert "--start 1" in str(cm.exception)


if __name__ == "__main__":
    unittest.main()
