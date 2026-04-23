"""Tests for scripts/claude_loop_lib/commands.py."""
from __future__ import annotations

import unittest
from typing import Any

from . import _bootstrap  # noqa: F401  — must precede claude_loop_lib imports

from claude_loop_lib.commands import build_command


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


class TestBuildCommandWithSystemPrompt(unittest.TestCase):
    """Tests for build_command() with --system-prompt flag (ver10.0)."""

    def _make_step(self, **kwargs: Any) -> dict:
        step = {"name": "test", "prompt": "/test", "args": []}
        step.update(kwargs)
        return step

    def test_step_system_prompt_emits_flag(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(system_prompt="hello"), defaults={},
        )
        assert "--system-prompt" in cmd
        assert cmd[cmd.index("--system-prompt") + 1] == "hello"

    def test_defaults_system_prompt_used_when_step_omits(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(),
            defaults={"system_prompt": "from-defaults"},
        )
        assert cmd[cmd.index("--system-prompt") + 1] == "from-defaults"

    def test_step_overrides_defaults_system_prompt(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(system_prompt="step-val"),
            defaults={"system_prompt": "defaults-val"},
        )
        assert cmd[cmd.index("--system-prompt") + 1] == "step-val"
        assert "defaults-val" not in cmd

    def test_no_system_prompt_when_unset(self) -> None:
        cmd = build_command("claude", "-p", [], self._make_step(), defaults={})
        assert "--system-prompt" not in cmd


class TestBuildCommandWithAppendSystemPrompt(unittest.TestCase):
    """Tests for build_command() with append_system_prompt step override (ver10.0)."""

    def _make_step(self, **kwargs: Any) -> dict:
        step = {"name": "test", "prompt": "/test", "args": []}
        step.update(kwargs)
        return step

    def _asp_value(self, cmd: list[str]) -> str:
        return cmd[cmd.index("--append-system-prompt") + 1]

    def test_step_append_only(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(append_system_prompt="my-append"),
            defaults={},
        )
        assert "--append-system-prompt" in cmd
        assert self._asp_value(cmd) == "my-append"

    def test_appends_after_log_path(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(append_system_prompt="my-append"),
            log_file_path="/log.log",
        )
        value = self._asp_value(cmd)
        log_pos = value.index("Current workflow log:")
        append_pos = value.index("my-append")
        assert log_pos < append_pos

    def test_appends_after_auto_mode(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(append_system_prompt="my-append"),
            auto_mode=True,
        )
        value = self._asp_value(cmd)
        auto_pos = value.index("AUTO (unattended)")
        append_pos = value.index("my-append")
        assert auto_pos < append_pos

    def test_appends_after_feedbacks(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(append_system_prompt="my-append"),
            feedbacks=["feedback-text"],
        )
        value = self._asp_value(cmd)
        fb_pos = value.index("## User Feedback")
        append_pos = value.index("my-append")
        assert fb_pos < append_pos

    def test_full_combination_order(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(append_system_prompt="my-append"),
            log_file_path="/log.log",
            auto_mode=True,
            feedbacks=["fbtext"],
        )
        value = self._asp_value(cmd)
        log_pos = value.index("Current workflow log:")
        auto_pos = value.index("AUTO (unattended)")
        fb_pos = value.index("## User Feedback")
        append_pos = value.index("my-append")
        assert log_pos < auto_pos < fb_pos < append_pos

    def test_defaults_append_used_when_step_omits(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(),
            defaults={"append_system_prompt": "default-append"},
        )
        assert self._asp_value(cmd) == "default-append"

    def test_step_overrides_defaults_append(self) -> None:
        cmd = build_command(
            "claude", "-p", [], self._make_step(append_system_prompt="B"),
            defaults={"append_system_prompt": "A"},
        )
        value = self._asp_value(cmd)
        assert value == "B"
        assert "A" not in value


if __name__ == "__main__":
    unittest.main()
