#!/usr/bin/env python3
"""Run Claude prompts sequentially from a YAML workflow."""

from __future__ import annotations

import argparse
import io
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - import failure path
    raise SystemExit(
        "PyYAML is required. Install it with: python -m pip install pyyaml"
    ) from exc


DEFAULT_WORKFLOW_PATH = Path(__file__).with_name("claude_loop.yaml")
DEFAULT_WORKING_DIRECTORY = Path(__file__).resolve().parent.parent


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Claude workflow defined in YAML."
    )
    parser.add_argument(
        "-w",
        "--workflow",
        type=Path,
        default=DEFAULT_WORKFLOW_PATH,
        help=f"Path to workflow YAML (default: {DEFAULT_WORKFLOW_PATH})",
    )
    parser.add_argument(
        "-s",
        "--start",
        type=positive_int,
        default=1,
        help="1-based step number to start from (default: 1)",
    )
    parser.add_argument(
        "--cwd",
        type=Path,
        default=DEFAULT_WORKING_DIRECTORY,
        help=f"Working directory for Claude commands (default: {DEFAULT_WORKING_DIRECTORY})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without running them",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path("logs/workflow"),
        help="Directory for workflow log files (default: logs/workflow/)",
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="Disable log file output",
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="Disable desktop notification on workflow completion",
    )
    parser.add_argument(
        "--auto-commit-before",
        action="store_true",
        help="Automatically commit uncommitted changes before starting the workflow",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Force auto (unattended) execution mode",
    )
    loop_group = parser.add_mutually_exclusive_group()
    loop_group.add_argument(
        "--max-loops",
        type=positive_int,
        help="Maximum number of workflow loops to run",
    )
    loop_group.add_argument(
        "--max-step-runs",
        type=positive_int,
        help="Maximum total number of step executions to run",
    )

    args = parser.parse_args()
    if args.max_loops is None and args.max_step_runs is None:
        args.max_loops = 1
    return args


def load_workflow(path: Path) -> dict[str, Any]:
    workflow_path = path.expanduser().resolve()
    if not workflow_path.is_file():
        raise SystemExit(f"Workflow file not found: {workflow_path}")

    with workflow_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise SystemExit("Workflow YAML must contain a top-level mapping.")

    return data


def normalize_string_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SystemExit(f"'{field_name}' must be a list of strings.")
    return value


def normalize_cli_args(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []

    raw_items = [value] if isinstance(value, str) else value
    if not isinstance(raw_items, list) or not all(
        isinstance(item, str) for item in raw_items
    ):
        raise SystemExit(f"'{field_name}' must be a string or list of strings.")

    parsed_args: list[str] = []
    for item in raw_items:
        parsed_args.extend(shlex.split(item, posix=True))

    return parsed_args


def get_steps(config: dict[str, Any]) -> list[dict[str, Any]]:
    raw_steps = config.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise SystemExit("Workflow YAML must define a non-empty 'steps' list.")

    steps: list[dict[str, Any]] = []
    for index, raw_step in enumerate(raw_steps, start=1):
        if not isinstance(raw_step, dict):
            raise SystemExit(f"Step {index} must be a mapping.")

        prompt = raw_step.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise SystemExit(f"Step {index} must define a non-empty 'prompt'.")

        name = raw_step.get("name") or f"step-{index}"
        if not isinstance(name, str):
            raise SystemExit(f"Step {index} field 'name' must be a string.")

        steps.append(
            {
                "name": name,
                "prompt": prompt,
                "args": normalize_cli_args(raw_step.get("args"), f"steps[{index}].args"),
            }
        )

    return steps


def resolve_command_config(config: dict[str, Any]) -> tuple[str, str, list[str], list[str]]:
    command_config = config.get("command") or {}
    if not isinstance(command_config, dict):
        raise SystemExit("'command' must be a mapping when provided.")

    executable = command_config.get("executable", "claude")
    prompt_flag = command_config.get("prompt_flag", "-p")
    common_args = normalize_cli_args(command_config.get("args"), "command.args")
    auto_args = normalize_cli_args(command_config.get("auto_args"), "command.auto_args")

    if not isinstance(executable, str) or not executable.strip():
        raise SystemExit("'command.executable' must be a non-empty string.")
    if not isinstance(prompt_flag, str) or not prompt_flag.strip():
        raise SystemExit("'command.prompt_flag' must be a non-empty string.")

    return executable, prompt_flag, common_args, auto_args


def resolve_mode(config: dict[str, Any], cli_auto: bool) -> bool:
    """Determine execution mode. Returns True for auto mode."""
    if cli_auto:
        return True
    mode_config = config.get("mode") or {}
    return bool(mode_config.get("auto", False))


def build_command(
    executable: str,
    prompt_flag: str,
    common_args: list[str],
    step: dict[str, Any],
    log_file_path: str | None = None,
    auto_mode: bool = False,
) -> list[str]:
    cmd = [executable, prompt_flag, step["prompt"], *common_args, *step["args"]]
    system_prompts: list[str] = []
    if log_file_path:
        system_prompts.append(f"Current workflow log: {log_file_path}")
    if auto_mode:
        system_prompts.append(
            "Workflow execution mode: AUTO (unattended). "
            "Do not use AskUserQuestion. Write requests to REQUESTS/AI/ instead."
        )
    if system_prompts:
        cmd.extend(["--append-system-prompt", "\n\n".join(system_prompts)])
    return cmd


def print_step_header(current_index: int, total_steps: int, name: str) -> None:
    print(f"\n[{current_index}/{total_steps}] {name}")


def iter_steps_for_loop_limit(
    steps: list[dict[str, Any]],
    start_index: int,
    max_loops: int,
):
    for loop_index in range(max_loops):
        current_start = start_index if loop_index == 0 else 0
        for step_index in range(current_start, len(steps)):
            yield steps[step_index], step_index + 1


def iter_steps_for_step_limit(
    steps: list[dict[str, Any]],
    start_index: int,
    max_step_runs: int,
):
    remaining = max_step_runs
    step_index = start_index

    while remaining > 0:
        remaining -= 1
        yield steps[step_index], step_index + 1
        step_index = (step_index + 1) % len(steps)


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


def get_head_commit(cwd: Path) -> str | None:
    """Get current HEAD commit hash, or None if not a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd, capture_output=True, text=True, check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except FileNotFoundError:
        return None


def check_uncommitted_changes(cwd: Path) -> bool:
    """Check if there are uncommitted changes in the working directory."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd, capture_output=True, text=True, check=False,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except FileNotFoundError:
        return False


def auto_commit_changes(cwd: Path) -> str | None:
    """Stage all changes and commit. Returns the new commit hash or None on failure."""
    try:
        subprocess.run(["git", "add", "-A"], cwd=cwd, check=True)
        subprocess.run(["git", "commit", "-m", "auto-commit before workflow"], cwd=cwd, check=True)
        return get_head_commit(cwd)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


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


def notify_completion(title: str, message: str) -> None:
    """Send desktop notification. Falls back to beep on failure."""
    try:
        _notify_toast(title, message)
    except Exception:
        _notify_beep(title, message)


def _notify_toast(title: str, message: str) -> None:
    """Windows toast notification via PowerShell."""
    safe_title = title.replace("'", "''")
    safe_message = message.replace("'", "''")
    script = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
        "$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
        "$text = $template.GetElementsByTagName('text'); "
        f"$text[0].AppendChild($template.CreateTextNode('{safe_title}')) | Out-Null; "
        f"$text[1].AppendChild($template.CreateTextNode('{safe_message}')) | Out-Null; "
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Claude Workflow').Show($toast)"
    )
    result = subprocess.run(
        ["powershell", "-Command", script],
        capture_output=True, check=False, timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError("Toast notification failed")


def _notify_beep(title: str, message: str) -> None:
    """Fallback: beep + console output."""
    print("\a")
    print(f"\n{'=' * 40}")
    print(f"  {title}")
    print(f"  {message}")
    print(f"{'=' * 40}\n")


def main() -> int:
    args = parse_args()
    config = load_workflow(args.workflow)
    steps = get_steps(config)

    if args.start < 1 or args.start > len(steps):
        raise SystemExit(
            f"--start must be between 1 and {len(steps)}. Received: {args.start}"
        )

    executable, prompt_flag, common_args, auto_args = resolve_command_config(config)
    auto_mode = resolve_mode(config, args.auto)
    if auto_mode:
        common_args = common_args + auto_args
    if shutil.which(executable) is None:
        raise SystemExit(f"Command not found: {executable}")

    cwd = args.cwd.expanduser().resolve()
    if not cwd.is_dir():
        raise SystemExit(f"Working directory not found: {cwd}")

    uncommitted_status: str | None = None
    if not args.dry_run:
        if check_uncommitted_changes(cwd):
            if args.auto_commit_before:
                commit_hash = auto_commit_changes(cwd)
                if commit_hash:
                    uncommitted_status = f"auto-committed ({commit_hash})"
                    print(f"Auto-committed uncommitted changes: {commit_hash}")
                else:
                    uncommitted_status = "auto-commit failed, proceeding with uncommitted changes"
                    print("WARNING: Auto-commit failed. Proceeding with uncommitted changes.", file=sys.stderr)
            else:
                uncommitted_status = "uncommitted changes detected (no --auto-commit-before)"
                print("WARNING: Uncommitted changes detected. Consider committing before running the workflow.", file=sys.stderr)

    if args.max_step_runs is not None:
        step_iter = iter_steps_for_step_limit(steps, args.start - 1, args.max_step_runs)
    else:
        step_iter = iter_steps_for_loop_limit(steps, args.start - 1, args.max_loops)

    enable_log = not args.no_log and not args.dry_run

    workflow_start = time.monotonic()

    if enable_log:
        log_path = create_log_path(args.log_dir, args.workflow)
        with open(log_path, "w", encoding="utf-8") as log_file:
            tee = TeeWriter(log_file)
            exit_code = _run_steps(
                step_iter, steps, executable, prompt_flag, common_args,
                cwd, args.dry_run, tee, log_path, auto_mode,
                uncommitted_status,
            )
    else:
        exit_code = _run_steps(
            step_iter, steps, executable, prompt_flag, common_args,
            cwd, args.dry_run, None, None, auto_mode,
            uncommitted_status,
        )

    total_duration = time.monotonic() - workflow_start

    if not args.no_notify and not args.dry_run:
        duration_str = format_duration(total_duration)
        if exit_code == 0:
            notify_completion("Workflow Complete", f"All steps succeeded ({duration_str})")
        else:
            notify_completion("Workflow Failed", f"Exit code: {exit_code} ({duration_str})")

    return exit_code


def _run_steps(
    step_iter,
    steps: list[dict[str, Any]],
    executable: str,
    prompt_flag: str,
    common_args: list[str],
    cwd: Path,
    dry_run: bool,
    tee: TeeWriter | None,
    log_path: Path | None,
    auto_mode: bool = False,
    uncommitted_status: str | None = None,
) -> int:
    """Execute workflow steps with optional logging via TeeWriter."""
    total_steps = len(steps)
    workflow_start = time.monotonic()
    start_time = datetime.now()
    start_commit = get_head_commit(cwd)
    completed_count = 0

    def _out(line: str) -> None:
        if tee is not None:
            tee.write_line(line)
        else:
            print(line)

    # --- Workflow header ---
    if tee is not None:
        _out("=====================================")
        _out(f"Workflow: {log_path.stem.split('_', 2)[-1] if log_path else 'unknown'}")
        _out(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if start_commit:
            _out(f"Commit (start): {start_commit}")
        if uncommitted_status:
            _out(f"Uncommitted: {uncommitted_status}")
        _out("=====================================")

    ran_any_step = False
    prev_commit = start_commit

    for step, absolute_index in step_iter:
        ran_any_step = True

        log_file_path = str(log_path) if tee is not None else None
        command = build_command(executable, prompt_flag, common_args, step, log_file_path, auto_mode)
        command_str = " ".join(command)

        step_start = time.monotonic()
        step_start_time = datetime.now()

        # --- Step header ---
        if tee is not None:
            _out("")
            _out(f"[{absolute_index}/{total_steps}] {step['name']}")
            _out(f"Started: {step_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            _out(f"$ {command_str}")
        else:
            print_step_header(absolute_index, total_steps, step["name"])
            print(f"$ {command_str}")

        if dry_run:
            continue

        # --- Execute step ---
        if tee is not None:
            _out("--- stdout/stderr ---")
            process = subprocess.Popen(
                command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            exit_code = tee.write_process_output(process)
        else:
            completed = subprocess.run(command, cwd=cwd, check=False)
            exit_code = completed.returncode

        step_duration = time.monotonic() - step_start
        duration_str = format_duration(step_duration)

        # --- Step footer ---
        if tee is not None:
            _out(f"--- end (exit: {exit_code}, duration: {duration_str}) ---")
            # Check for commit change
            current_commit = get_head_commit(cwd)
            if current_commit and prev_commit and current_commit != prev_commit:
                _out(f"Commit: {prev_commit} -> {current_commit}")
            prev_commit = current_commit

        # --- Handle failure ---
        if exit_code != 0:
            fail_msg = f"Step failed with exit code {exit_code}: {step['name']}"
            if tee is not None:
                # Write workflow footer on failure
                end_time = datetime.now()
                total_duration = time.monotonic() - workflow_start
                end_commit = get_head_commit(cwd)
                _out("")
                _out("=====================================")
                _out(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                if end_commit:
                    _out(f"Commit (end): {end_commit}")
                _out(f"Duration: {format_duration(total_duration)}")
                _out(f"Result: FAILED at step {absolute_index}/{total_steps} ({step['name']})")
                _out("=====================================")
            print(fail_msg, file=sys.stderr)
            return exit_code

        completed_count += 1

    if not ran_any_step:
        _out("No steps to run.")
        return 0

    # --- Workflow footer ---
    if tee is not None:
        end_time = datetime.now()
        total_duration = time.monotonic() - workflow_start
        end_commit = get_head_commit(cwd)
        _out("")
        _out("=====================================")
        _out(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if end_commit:
            _out(f"Commit (end): {end_commit}")
        _out(f"Duration: {format_duration(total_duration)}")
        _out(f"Result: SUCCESS ({completed_count}/{completed_count} steps completed)")
        _out("=====================================")
    else:
        print("\nWorkflow completed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
