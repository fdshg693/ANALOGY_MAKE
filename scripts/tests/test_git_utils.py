"""Tests for scripts/claude_loop_lib/git_utils.py."""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from . import _bootstrap  # noqa: F401  — must precede claude_loop_lib imports

from claude_loop_lib.git_utils import (
    get_head_commit, check_uncommitted_changes, auto_commit_changes,
)


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


if __name__ == "__main__":
    unittest.main()
