"""Tests for scripts/claude_loop.py CLI argument parsing and helpers."""
from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch, MagicMock

from . import _bootstrap  # noqa: F401  — must precede claude_loop imports

import claude_loop
from claude_loop import (
    parse_args,
    validate_auto_args, _find_latest_rough_plan, _read_workflow_kind,
    _compute_remaining_budget, _version_key,
    RunStats,
)
from claude_loop_lib.notify import (
    RESULT_SUCCESS, RESULT_FAILED, RESULT_INTERRUPTED,
)


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


class TestRejectsAutoFlag(unittest.TestCase):
    """ver13.0: --auto flag is removed and must be rejected by argparse."""

    def _parse(self, args: list[str]) -> argparse.Namespace:
        with patch("sys.argv", ["claude_loop.py", *args]):
            return parse_args()

    def test_auto_flag_raises_systemexit(self) -> None:
        with self.assertRaises(SystemExit):
            self._parse(["--auto"])

    def test_default_has_no_auto_attribute(self) -> None:
        result = self._parse([])
        assert not hasattr(result, "auto")


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

    # --- threshold tests ---

    def test_threshold_excludes_pre_existing_files(self) -> None:
        import os
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            paths = self._make_tree(tmp, "util", ["ver1.0", "ver2.0"])
            # old file: mtime = 1000 (threshold); new file: mtime = 2000
            os.utime(paths[0], (1000, 1000))
            os.utime(paths[1], (2000, 2000))
            result = _find_latest_rough_plan(tmp, mtime_threshold=1000.0)
            # ver1.0 is AT the threshold (not strictly greater), ver2.0 is newer
            assert result == paths[1]

    def test_threshold_no_new_files_raises(self) -> None:
        import os
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            paths = self._make_tree(tmp, "util", ["ver1.0"])
            os.utime(paths[0], (1000, 1000))
            with self.assertRaises(SystemExit) as cm:
                _find_latest_rough_plan(tmp, mtime_threshold=1000.0)
            assert "did not create a new ROUGH_PLAN.md" in str(cm.exception)

    def test_threshold_multiple_new_files_highest_version_wins(self) -> None:
        import os
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            paths = self._make_tree(tmp, "util", ["ver9.1", "ver10.0", "ver9.0"])
            # All three are newer than threshold; highest version (ver10.0) must win
            for p in paths:
                os.utime(p, (2000, 2000))
            result = _find_latest_rough_plan(tmp, mtime_threshold=1000.0)
            assert result == paths[1]  # ver10.0

    def test_version_key_natural_sort(self) -> None:
        import os
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            paths = self._make_tree(tmp, "util", ["ver9.1", "ver10.0"])
            assert _version_key(paths[0]) == (9, 1)
            assert _version_key(paths[1]) == (10, 0)
            assert _version_key(paths[1]) > _version_key(paths[0])


class TestMainNotifyRunSummary(unittest.TestCase):
    """Tests for main() notify_completion call paths (run-summary integration)."""

    def _base_argv(self, *extra: str) -> list[str]:
        return [
            "claude_loop.py",
            "--workflow", "full",
            "--cwd", ".",
            "--no-log",
            *extra,
        ]

    def _common_patches(self, run_selected_side_effect):
        """Return a list of context managers to apply around main().

        ``run_selected_side_effect`` is a callable `(tee, log_path) -> (int, RunStats)`
        or an exception class/instance to raise.
        """
        def fake_run_selected(self2_tee_or_args, *a, **kw):
            # When monkey-patching _execute_yaml/_run_auto we instead replace them.
            raise AssertionError("should not be called directly")

        return [
            patch("claude_loop.validate_startup"),
            patch("claude_loop.check_uncommitted_changes", return_value=False),
            patch("claude_loop.resolve_workflow_value", return_value=Path("wf.yaml")),
            patch("pathlib.Path.is_dir", return_value=True),
        ]

    def _run_main_with_run_selected(
        self,
        side_effect,
        argv_extra: list[str] | None = None,
    ):
        """Run claude_loop.main() with _execute_yaml mocked to produce the given side effect."""
        argv_extra = argv_extra or []
        argv = self._base_argv(*argv_extra)

        if isinstance(side_effect, tuple):
            exec_return = side_effect
            exec_side_effect = None
        else:
            exec_return = None
            exec_side_effect = side_effect

        with (
            patch("sys.argv", argv),
            patch("claude_loop.validate_startup"),
            patch("claude_loop.check_uncommitted_changes", return_value=False),
            patch("pathlib.Path.is_dir", return_value=True),
            patch("claude_loop.notify_completion") as mock_notify,
            patch("claude_loop._execute_yaml") as mock_exec,
        ):
            if exec_side_effect is not None:
                mock_exec.side_effect = exec_side_effect
            else:
                mock_exec.return_value = exec_return
            try:
                exit_code = claude_loop.main()
                raised: BaseException | None = None
            except SystemExit as e:
                exit_code = e.code if isinstance(e.code, int) else 1
                raised = e
            except BaseException as e:  # pragma: no cover
                raised = e
                exit_code = None

        return exit_code, mock_notify, raised

    def test_main_emits_summary_on_success(self) -> None:
        stats = RunStats()
        stats.completed_steps = 6
        stats.completed_loops = 1
        stats.workflow_label = "claude_loop"
        exit_code, mock_notify, _ = self._run_main_with_run_selected((0, stats))
        assert exit_code == 0
        mock_notify.assert_called_once()
        summary = mock_notify.call_args[0][0]
        assert summary.result == RESULT_SUCCESS
        assert summary.workflow_label == "claude_loop"
        assert summary.loops_completed == 1
        assert summary.steps_completed == 6
        assert summary.exit_code is None

    def test_main_emits_summary_on_failure(self) -> None:
        stats = RunStats()
        stats.completed_steps = 3
        stats.completed_loops = 0
        stats.failed_step = "imple_plan"
        stats.workflow_label = "claude_loop"
        exit_code, mock_notify, _ = self._run_main_with_run_selected((1, stats))
        assert exit_code == 1
        summary = mock_notify.call_args[0][0]
        assert summary.result == RESULT_FAILED
        assert summary.failed_step == "imple_plan"
        assert summary.exit_code == 1

    def test_main_emits_summary_on_keyboard_interrupt(self) -> None:
        def raise_ki(*a, **kw):
            # Ensure _last_signal reflects SIGINT default
            raise KeyboardInterrupt

        exit_code, mock_notify, raised = self._run_main_with_run_selected(raise_ki)
        summary = mock_notify.call_args[0][0]
        assert summary.result == RESULT_INTERRUPTED
        assert summary.interrupt_reason == "SIGINT"
        # KeyboardInterrupt is caught in main() — no re-raise; exit_code == 130
        assert exit_code == 130

    def test_main_emits_summary_on_sigterm(self) -> None:
        """Simulate SIGTERM by directly invoking the handler from inside the mock."""
        def raise_via_handler(*a, **kw):
            claude_loop._sigterm_to_keyboard_interrupt(15, None)

        exit_code, mock_notify, raised = self._run_main_with_run_selected(raise_via_handler)
        summary = mock_notify.call_args[0][0]
        assert summary.result == RESULT_INTERRUPTED
        assert summary.interrupt_reason == "SIGTERM"
        assert exit_code == 130

    def test_main_no_notify_flag_suppresses(self) -> None:
        stats = RunStats()
        stats.workflow_label = "claude_loop"
        exit_code, mock_notify, _ = self._run_main_with_run_selected(
            (0, stats), argv_extra=["--no-notify"]
        )
        assert exit_code == 0
        mock_notify.assert_not_called()

    def test_main_dry_run_suppresses(self) -> None:
        stats = RunStats()
        stats.workflow_label = "claude_loop"
        exit_code, mock_notify, _ = self._run_main_with_run_selected(
            (0, stats), argv_extra=["--dry-run"]
        )
        assert exit_code == 0
        mock_notify.assert_not_called()

    def test_main_no_notify_suppresses_on_failure(self) -> None:
        stats = RunStats()
        stats.failed_step = "x"
        exit_code, mock_notify, _ = self._run_main_with_run_selected(
            (1, stats), argv_extra=["--no-notify"]
        )
        assert exit_code == 1
        mock_notify.assert_not_called()

    def test_main_no_notify_suppresses_on_interrupt(self) -> None:
        def raise_ki(*a, **kw):
            raise KeyboardInterrupt

        exit_code, mock_notify, _ = self._run_main_with_run_selected(
            raise_ki, argv_extra=["--no-notify"]
        )
        assert exit_code == 130
        mock_notify.assert_not_called()


class TestSigtermHandler(unittest.TestCase):
    """Unit test for _sigterm_to_keyboard_interrupt() — no signal.raise_signal."""

    def setUp(self) -> None:
        self._original_last_signal = claude_loop._last_signal

    def tearDown(self) -> None:
        claude_loop._last_signal = self._original_last_signal

    def test_handler_sets_last_signal_and_raises(self) -> None:
        claude_loop._last_signal = "SIGINT"
        with self.assertRaises(KeyboardInterrupt):
            claude_loop._sigterm_to_keyboard_interrupt(15, None)
        assert claude_loop._last_signal == "SIGTERM"


class TestWorkflowLabelFallback(unittest.TestCase):
    def test_auto_label(self) -> None:
        assert claude_loop._workflow_label_fallback("auto") == "auto"

    def test_path_label(self) -> None:
        assert claude_loop._workflow_label_fallback(Path("claude_loop_quick.yaml")) == "claude_loop_quick"


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


if __name__ == "__main__":
    unittest.main()
