"""Unit tests for claude_loop_lib.deferred_commands (ver16.1 PHASE8.0 §2)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from . import _bootstrap  # noqa: F401

from claude_loop_lib import deferred_commands


def _write_request(
    deferred_dir: Path,
    *,
    request_id: str = "req-001",
    source_step: str = "imple_plan",
    session_id: str = "sess-abc",
    commands: list[str] | None = None,
    cwd: Path | None = None,
    extra_frontmatter: str = "",
) -> Path:
    deferred_commands.ensure_dirs(deferred_dir)
    cmd_block = "\n".join(commands or ["echo ok"])
    cwd_line = f"cwd: {cwd}\n" if cwd is not None else ""
    text = (
        "---\n"
        f"request_id: {request_id}\n"
        f"source_step: {source_step}\n"
        f"session_id: {session_id}\n"
        f"{cwd_line}{extra_frontmatter}"
        "---\n"
        "# Commands\n"
        "```bash\n"
        f"{cmd_block}\n"
        "```\n"
    )
    path = deferred_dir / f"{request_id}.md"
    path.write_text(text, encoding="utf-8")
    return path


class TestValidateRequest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.deferred_dir = self.tmp / "data" / "deferred"

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_valid_request_parses(self) -> None:
        path = _write_request(
            self.deferred_dir, commands=["echo hello", "pwd"], cwd=self.tmp,
        )
        req = deferred_commands.validate_request(path)
        assert req["request_id"] == "req-001"
        assert req["commands"] == ["echo hello", "pwd"]
        assert req["cwd"] == self.tmp
        assert req["timeout_sec"] is None

    def test_missing_frontmatter_raises(self) -> None:
        path = self.deferred_dir / "bad.md"
        self.deferred_dir.mkdir(parents=True)
        path.write_text("no frontmatter here\n```bash\necho x\n```\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            deferred_commands.validate_request(path)

    def test_missing_bash_block_raises(self) -> None:
        self.deferred_dir.mkdir(parents=True)
        path = self.deferred_dir / "nobash.md"
        path.write_text(
            "---\nrequest_id: r\nsource_step: s\nsession_id: x\n---\nbody only\n",
            encoding="utf-8",
        )
        with self.assertRaises(ValueError):
            deferred_commands.validate_request(path)

    def test_empty_required_field_raises(self) -> None:
        path = _write_request(self.deferred_dir, request_id="")
        with self.assertRaises(ValueError):
            deferred_commands.validate_request(path)


class TestExecuteRequest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.deferred_dir = self.tmp / "data" / "deferred"

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_successful_run_writes_meta_and_logs(self) -> None:
        path = _write_request(
            self.deferred_dir, commands=["echo hello"], cwd=self.tmp,
        )
        req = deferred_commands.validate_request(path)
        result = deferred_commands.execute_request(req, deferred_dir=self.deferred_dir)
        assert result["overall_exit_code"] == 0
        assert result["exit_codes"] == [0]
        meta_file = self.deferred_dir / "results" / "req-001.meta.json"
        assert meta_file.exists()
        data = json.loads(meta_file.read_text(encoding="utf-8"))
        assert data["request_id"] == "req-001"
        stdout_file = self.deferred_dir / "results" / "req-001.stdout.log"
        assert stdout_file.exists()
        assert b"hello" in stdout_file.read_bytes()

    def test_marker_removed_on_success(self) -> None:
        path = _write_request(self.deferred_dir, commands=["echo ok"], cwd=self.tmp)
        req = deferred_commands.validate_request(path)
        deferred_commands.execute_request(req, deferred_dir=self.deferred_dir)
        marker = self.deferred_dir / "req-001.started"
        assert not marker.exists()

    def test_failure_aborts_remaining_commands(self) -> None:
        import sys
        if sys.platform == "win32":
            # Windows shell: `exit 1` then a marker command that would otherwise write to stdout.
            cmds = ["exit 1", "echo after-fail"]
        else:
            cmds = ["false", "echo after-fail"]
        path = _write_request(
            self.deferred_dir, commands=cmds, cwd=self.tmp, request_id="req-fail",
        )
        req = deferred_commands.validate_request(path)
        result = deferred_commands.execute_request(req, deferred_dir=self.deferred_dir)
        # Only one exit code recorded: the failing command, rest skipped.
        assert len(result["exit_codes"]) == 1
        assert result["overall_exit_code"] != 0
        stdout_file = self.deferred_dir / "results" / "req-fail.stdout.log"
        assert b"after-fail" not in stdout_file.read_bytes()


class TestConsumeRequest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.deferred_dir = self.tmp / "data" / "deferred"

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_moves_to_done(self) -> None:
        path = _write_request(self.deferred_dir, commands=["echo x"], cwd=self.tmp)
        target = deferred_commands.consume_request(path, self.deferred_dir / "done")
        assert target.exists()
        assert not path.exists()
        assert target.parent.name == "done"

    def test_collision_appends_suffix(self) -> None:
        done_dir = self.deferred_dir / "done"
        path = _write_request(self.deferred_dir, commands=["echo x"], cwd=self.tmp)
        first = deferred_commands.consume_request(path, done_dir)
        # Create another request with the same name
        path2 = _write_request(self.deferred_dir, commands=["echo y"], cwd=self.tmp)
        second = deferred_commands.consume_request(path2, done_dir)
        assert first != second
        assert first.exists() and second.exists()


class TestScanOrphans(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.deferred_dir = self.tmp / "data" / "deferred"

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_orphan_detection(self) -> None:
        self.deferred_dir.mkdir(parents=True)
        (self.deferred_dir / "leftover.started").write_text("running\n", encoding="utf-8")
        orphans = deferred_commands.scan_orphans(self.deferred_dir)
        assert len(orphans) == 1
        assert orphans[0].name == "leftover.started"

    def test_no_orphans_when_clean(self) -> None:
        self.deferred_dir.mkdir(parents=True)
        assert deferred_commands.scan_orphans(self.deferred_dir) == []


class TestBuildResumePrompt(unittest.TestCase):
    def test_contains_exit_code_and_paths(self) -> None:
        result = deferred_commands.DeferredResult(
            request_id="r1",
            source_step="imple_plan",
            session_id="s1",
            commands=["echo hi"],
            exit_codes=[0],
            overall_exit_code=0,
            started_at="2026-04-24T18:00:00",
            ended_at="2026-04-24T18:00:01",
            duration_sec=1.0,
            stdout_bytes=3,
            stdout_path="/tmp/r1.stdout.log",
            stderr_bytes=0,
            stderr_path="/tmp/r1.stderr.log",
            head_excerpt="hi",
            tail_excerpt="",
        )
        prompt = deferred_commands.build_resume_prompt([result])
        assert "r1" in prompt
        assert "overall_exit_code: 0" in prompt
        assert "/tmp/r1.stdout.log" in prompt
        assert "DEFERRED EXECUTION COMPLETED" in prompt

    def test_empty_results_returns_empty(self) -> None:
        assert deferred_commands.build_resume_prompt([]) == ""

    def test_excerpt_stays_bounded_for_large_stdout(self) -> None:
        # Simulate ~10 MB stdout scenario: excerpt limited to HEAD+TAIL lines.
        big_head = "\n".join(f"head-line-{i}" for i in range(deferred_commands.HEAD_EXCERPT_LINES))
        big_tail = "\n".join(f"tail-line-{i}" for i in range(deferred_commands.TAIL_EXCERPT_LINES))
        result = deferred_commands.DeferredResult(
            request_id="r2",
            source_step="x",
            session_id="s",
            commands=["cat huge.log"],
            exit_codes=[0],
            overall_exit_code=0,
            started_at="",
            ended_at="",
            duration_sec=0.0,
            stdout_bytes=10_000_000,
            stdout_path="/tmp/r2.stdout.log",
            stderr_bytes=0,
            stderr_path="/tmp/r2.stderr.log",
            head_excerpt=big_head,
            tail_excerpt=big_tail,
        )
        prompt = deferred_commands.build_resume_prompt([result])
        # Bound confirmed by experiment: stays well under 4KB per result.
        assert len(prompt) < 4000


if __name__ == "__main__":
    unittest.main()
