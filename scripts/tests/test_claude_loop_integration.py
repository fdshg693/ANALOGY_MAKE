"""Integration tests for scripts/claude_loop.py."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from . import _bootstrap  # noqa: F401  — must precede claude_loop imports

import claude_loop
from claude_loop import _run_steps
from claude_loop_lib.commands import build_command
from claude_loop_lib.workflow import (
    load_workflow, get_steps, resolve_defaults,
)


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

        exit_code, _ = _run_steps(
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
        )  # returns (int, RunStats); unpacking not needed here
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

        rough_plan_path = cwd / "docs" / "util" / "ver1.0" / "ROUGH_PLAN.md"

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
            patch("claude_loop.validate_startup"),
            patch("builtins.print"),
            # Phase 1 is mocked (subprocess), so no real file is created.
            # Patch _find_latest_rough_plan to return the pre-created stub so
            # phase-2 dispatch logic can be exercised independently of threshold.
            patch("claude_loop._find_latest_rough_plan", return_value=rough_plan_path),
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


class TestAutoLoopCountSemantics(unittest.TestCase):
    """auto モードの loop カウントが phase2 のみを反映することを検証する。"""

    def test_loops_completed_excludes_phase1(self) -> None:
        """notify_completion に渡される loops_completed が phase2 のみを反映する。"""
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            (cwd / ".claude").mkdir(parents=True)
            (cwd / ".claude" / "CURRENT_CATEGORY").write_text("util", encoding="utf-8")
            vdir = cwd / "docs" / "util" / "ver1.0"
            vdir.mkdir(parents=True)
            rough_plan = vdir / "ROUGH_PLAN.md"
            rough_plan.write_text("---\nworkflow: quick\n---\nbody\n", encoding="utf-8")

            captured: list = []

            def fake_run(cmd, **kwargs):
                if cmd and cmd[0] == "git":
                    return MagicMock(returncode=0, stdout="", stderr="")
                return MagicMock(returncode=0)

            argv = [
                "claude_loop.py", "--workflow", "auto",
                "--cwd", str(cwd),
                "--no-log",
            ]
            with (
                patch("sys.argv", argv),
                patch("claude_loop.subprocess.run", side_effect=fake_run),
                patch("claude_loop.check_uncommitted_changes", return_value=False),
                patch("claude_loop.shutil.which", return_value="/usr/bin/claude"),
                patch("claude_loop.validate_startup"),
                patch("builtins.print"),
                patch("claude_loop._find_latest_rough_plan", return_value=rough_plan),
                patch("claude_loop.notify_completion", side_effect=lambda s: captured.append(s)),
            ):
                exit_code = claude_loop.main()

            assert exit_code == 0
            assert len(captured) == 1
            summary = captured[0]
            # Phase 1 (issue_plan): 1 step — its loop must NOT be counted.
            # Phase 2 (quick, steps[1:]): runs 2 steps, completing 1 loop.
            assert summary.loops_completed == 1, (
                f"Expected 1 loop (phase2 only), got {summary.loops_completed}"
            )
            # Steps: 1 (phase1) + 2 (phase2 quick steps[1:]) = 3
            assert summary.steps_completed == 3


class TestStartupValidationIntegration(unittest.TestCase):
    """Smoke test: validate_startup failure must abort before _execute_yaml."""

    def test_validation_error_prevents_execution(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            (cwd / ".claude").mkdir()
            (cwd / ".claude" / "CURRENT_CATEGORY").write_text("util", encoding="utf-8")
            (cwd / "docs" / "util").mkdir(parents=True)

            argv = [
                "claude_loop.py", "--workflow", "full",
                "--cwd", str(cwd),
                "--no-log", "--no-notify", "--dry-run",
            ]
            with (
                patch("sys.argv", argv),
                patch("claude_loop._execute_yaml") as mock_exec,
                patch("builtins.print"),
                patch("sys.stderr"),
            ):
                with self.assertRaises(SystemExit) as cm:
                    claude_loop.main()
            assert cm.exception.code == 2
            mock_exec.assert_not_called()


class TestFeedbackInvariant(unittest.TestCase):
    """Integration: FEEDBACKS/ must be preserved on non-zero step exit."""

    _SINGLE_STEP_YAML = (
        "steps:\n"
        "  - name: test-step\n"
        "    prompt: /test\n"
    )

    def _setup_cwd(self, root: Path) -> Path:
        """Create minimal cwd skeleton and place one dummy feedback file.

        Returns the FEEDBACKS/ directory path.
        """
        (root / ".claude").mkdir(parents=True, exist_ok=True)
        (root / ".claude" / "CURRENT_CATEGORY").write_text("util", encoding="utf-8")
        feedbacks = root / "FEEDBACKS"
        feedbacks.mkdir()
        (feedbacks / "dummy-feedback.md").write_text(
            "Dummy feedback body.", encoding="utf-8"
        )
        return feedbacks

    def _run_with_returncode(self, cwd: Path, mock_returncode: int) -> int:
        """Write a single-step YAML, run main(), return exit_code."""
        yaml_path = cwd / "test-workflow.yaml"
        yaml_path.write_text(self._SINGLE_STEP_YAML, encoding="utf-8")

        def fake_run(cmd, **kwargs):
            if cmd and cmd[0] == "git":
                return MagicMock(returncode=0, stdout="", stderr="")
            return MagicMock(returncode=mock_returncode)

        argv = [
            "claude_loop.py",
            "--workflow", str(yaml_path),
            "--cwd", str(cwd),
            "--no-log", "--no-notify",
        ]
        with (
            patch("sys.argv", argv),
            patch("claude_loop.subprocess.run", side_effect=fake_run),
            patch("claude_loop.check_uncommitted_changes", return_value=False),
            patch("claude_loop.shutil.which", return_value="/usr/bin/claude"),
            patch("claude_loop.validate_startup"),
            patch("builtins.print"),
        ):
            return claude_loop.main()

    def test_feedback_preserved_on_step_failure(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            feedbacks = self._setup_cwd(cwd)

            exit_code = self._run_with_returncode(cwd, mock_returncode=1)

            assert exit_code == 1
            assert (feedbacks / "dummy-feedback.md").exists(), (
                "FEEDBACK must remain under FEEDBACKS/ when step exits non-zero"
            )
            done_dir = feedbacks / "done"
            assert not done_dir.exists() or not any(done_dir.iterdir()), (
                "FEEDBACKS/done/ must not be populated on step failure"
            )

    def test_feedback_consumed_on_step_success(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            feedbacks = self._setup_cwd(cwd)

            exit_code = self._run_with_returncode(cwd, mock_returncode=0)

            assert exit_code == 0
            assert not (feedbacks / "dummy-feedback.md").exists(), (
                "FEEDBACK must be removed from FEEDBACKS/ after successful step"
            )
            assert (feedbacks / "done" / "dummy-feedback.md").exists(), (
                "FEEDBACK must be moved to FEEDBACKS/done/ after successful step"
            )


if __name__ == "__main__":
    unittest.main()
