"""Workflow log helpers: tee writer, log path builder, step header, duration format."""

from __future__ import annotations

import io
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from claude_loop_lib.costs import RunCostSummary, StepCost


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

    def write_process_output_capturing(
        self, process: subprocess.Popen,
    ) -> tuple[int, bytes]:
        """Like write_process_output, but also buffers the raw bytes and
        returns (exit_code, captured_bytes).

        Used by cost tracking (PHASE8.0 §3) to parse `--output-format json`
        output after each step while preserving live tee streaming.
        """
        buffer = bytearray()
        for raw_line in process.stdout:
            buffer.extend(raw_line)
            line = raw_line.decode("utf-8", errors="replace").rstrip("\n\r")
            print(line)
            self.log_file.write(line + "\n")
            self.log_file.flush()
        process.wait()
        return process.returncode, bytes(buffer)


def write_stderr(line: str) -> None:
    """Write a line to stderr. TeeWriter-independent; safe to call after workflow ends."""
    print(line, file=sys.stderr)


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


def _format_cost_usd(value: float | None) -> str:
    if value is None:
        return "n/a"
    if value == 0:
        return "$0.0000"
    return f"${value:.4f}"


def format_step_cost_line(cost: StepCost) -> str:
    """Single-line footer describing one step's cost."""
    if cost["status"] != "ok":
        reason = cost.get("reason") or "unknown"
        return f"Cost: unavailable (reason: {reason})"
    parts: list[str] = [f"Cost: {_format_cost_usd(cost['cost_usd'])}"]
    token_bits: list[str] = []
    for label, key in (
        ("in", "input_tokens"),
        ("out", "output_tokens"),
        ("cache_r", "cache_read_input_tokens"),
        ("cache_w", "cache_creation_input_tokens"),
    ):
        value = cost.get(key)
        if value is not None:
            token_bits.append(f"{label}: {value}")
    if cost.get("model"):
        token_bits.append(f"model: {cost['model']}")
    if cost.get("kind") and cost["kind"] != "claude":
        token_bits.append(f"kind: {cost['kind']}")
    if token_bits:
        parts.append(f"({', '.join(token_bits)})")
    return " ".join(parts)


def format_run_cost_footer(summary: RunCostSummary) -> list[str]:
    """Multi-line footer appended to the workflow log."""
    lines: list[str] = []
    version = summary.get("claude_code_cli_version") or "unknown"
    lines.append(
        f"Run cost: {_format_cost_usd(summary['total_cost_usd'])} USD "
        f"(Claude Code CLI {version})"
    )
    ok_count = sum(1 for s in summary["steps"] if s["status"] == "ok")
    missing = summary["missing_steps"]
    lines.append(f"Steps: {ok_count} ok / {missing} unavailable")
    if summary["steps"]:
        lines.append("Per-step:")
        for idx, step in enumerate(summary["steps"], start=1):
            if step["status"] == "ok":
                cost_str = _format_cost_usd(step["cost_usd"])
            else:
                cost_str = "unavailable"
            model_tag = step.get("model") or "?"
            kind = step.get("kind") or "claude"
            suffix = f" [{kind}]" if kind != "claude" else ""
            lines.append(
                f"  [{idx}] {step['step_name']:<28} {cost_str:>10}  ({model_tag}){suffix}"
            )
    return lines
