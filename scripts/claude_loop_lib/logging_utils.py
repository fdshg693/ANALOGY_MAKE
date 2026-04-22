"""Workflow log helpers: tee writer, log path builder, step header, duration format."""

from __future__ import annotations

import io
import subprocess
from datetime import datetime
from pathlib import Path


def create_log_path(log_dir: Path, workflow_path: Path) -> Path:
    """Generate timestamped log file path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workflow_name = workflow_path.stem  # e.g. "claude_loop"
    log_dir = log_dir.resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{timestamp}_{workflow_name}.log"


class TeeWriter:
    """Write to both a file and stdout simultaneously."""

    def __init__(self, log_file: io.TextIOWrapper):
        self.log_file = log_file

    def write_line(self, line: str) -> None:
        """Write a line to both stdout and log file."""
        print(line)
        self.log_file.write(line + "\n")
        self.log_file.flush()

    def write_process_output(self, process: subprocess.Popen) -> int:
        """Stream process stdout/stderr to both stdout and log file.
        Returns the process exit code."""
        for raw_line in process.stdout:
            line = raw_line.decode("utf-8", errors="replace").rstrip("\n\r")
            print(line)
            self.log_file.write(line + "\n")
            self.log_file.flush()
        process.wait()
        return process.returncode


def print_step_header(current_index: int, total_steps: int, name: str) -> None:
    print(f"\n[{current_index}/{total_steps}] {name}")


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration string."""
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes:02d}m {secs:02d}s"
    if minutes > 0:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"
