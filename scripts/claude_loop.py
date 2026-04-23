#!/usr/bin/env python3
"""Run Claude prompts sequentially from a YAML workflow."""

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from claude_loop_lib.workflow import (
    load_workflow, get_steps, resolve_defaults,
    resolve_command_config, resolve_mode,
)
from claude_loop_lib.feedbacks import load_feedbacks, consume_feedbacks
from claude_loop_lib.commands import (
    build_command, iter_steps_for_loop_limit, iter_steps_for_step_limit,
)
from claude_loop_lib.logging_utils import (
    TeeWriter, create_log_path, print_step_header, format_duration,
)
from claude_loop_lib.git_utils import (
    get_head_commit, check_uncommitted_changes, auto_commit_changes,
)
from claude_loop_lib.notify import notify_completion


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


def main() -> int:
    args = parse_args()
    config = load_workflow(args.workflow)
    steps = get_steps(config)

    if args.start < 1 or args.start > len(steps):
        raise SystemExit(
            f"--start must be between 1 and {len(steps)}. Received: {args.start}"
        )

    executable, prompt_flag, common_args, auto_args = resolve_command_config(config)
    defaults = resolve_defaults(config)
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
    continue_disabled = args.start > 1

    workflow_start = time.monotonic()

    if enable_log:
        log_path = create_log_path(args.log_dir, args.workflow)
        with open(log_path, "w", encoding="utf-8") as log_file:
            tee = TeeWriter(log_file)
            exit_code = _run_steps(
                step_iter, steps, executable, prompt_flag, common_args,
                cwd, args.dry_run, tee, log_path, auto_mode,
                uncommitted_status, defaults,
                continue_disabled=continue_disabled,
            )
    else:
        exit_code = _run_steps(
            step_iter, steps, executable, prompt_flag, common_args,
            cwd, args.dry_run, None, None, auto_mode,
            uncommitted_status, defaults,
            continue_disabled=continue_disabled,
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
    defaults: dict[str, str] | None = None,
    continue_disabled: bool = False,
) -> int:
    """Execute workflow steps with optional logging via TeeWriter."""
    total_steps = len(steps)
    workflow_start = time.monotonic()
    start_time = datetime.now()
    start_commit = get_head_commit(cwd)
    completed_count = 0
    feedbacks_dir = cwd / "FEEDBACKS"
    previous_session_id: str | None = None
    continue_warned = False
    loop_boundary_warned = False

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

        # --- Load feedbacks ---
        matched = load_feedbacks(feedbacks_dir, step["name"])
        feedback_contents = [content for _, content in matched]
        feedback_files = [path for path, _ in matched]

        log_file_path = str(log_path) if tee is not None else None

        requested_continue = bool(step.get("continue", False))
        effective_continue = requested_continue

        if requested_continue and continue_disabled:
            if not continue_warned:
                _out(
                    "WARNING: --start > 1 detected; "
                    "disabling 'continue: true' for all steps in this run."
                )
                continue_warned = True
            effective_continue = False

        if effective_continue and previous_session_id is None:
            if not loop_boundary_warned:
                _out(
                    f"WARNING: step '{step['name']}' requests continue:true "
                    f"but no previous session exists; starting new session."
                )
                loop_boundary_warned = True
            effective_continue = False

        if effective_continue:
            session_id = previous_session_id
            resume = True
        else:
            session_id = str(uuid.uuid4())
            resume = False

        command = build_command(
            executable, prompt_flag, common_args, step, log_file_path, auto_mode,
            feedbacks=feedback_contents or None, defaults=defaults,
            session_id=session_id, resume=resume,
        )
        command_str = shlex.join(command)

        step_start = time.monotonic()
        step_start_time = datetime.now()

        effective_defaults = defaults or {}
        effective_model = step.get("model", effective_defaults.get("model"))
        effective_effort = step.get("effort", effective_defaults.get("effort"))
        descriptor_parts: list[str] = []
        if effective_model is not None:
            descriptor_parts.append(f"Model: {effective_model}")
        if effective_effort is not None:
            descriptor_parts.append(f"Effort: {effective_effort}")
        if requested_continue:
            descriptor_parts.append(f"Continue: {effective_continue}")
        descriptor_parts.append(f"Session: {session_id[:8]}")
        descriptor_line = ", ".join(descriptor_parts) if descriptor_parts else None

        # --- Step header ---
        if tee is not None:
            _out("")
            _out(f"[{absolute_index}/{total_steps}] {step['name']}")
            _out(f"Started: {step_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            if descriptor_line:
                _out(descriptor_line)
            _out(f"$ {command_str}")
        else:
            print_step_header(absolute_index, total_steps, step["name"])
            if descriptor_line:
                _out(descriptor_line)
            print(f"$ {command_str}")

        if dry_run:
            previous_session_id = session_id
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
                _out(f"Last session (full): {session_id}")
                _out("=====================================")
            print(fail_msg, file=sys.stderr)
            return exit_code

        if feedback_files:
            consume_feedbacks(feedback_files, feedbacks_dir / "done")

        previous_session_id = session_id
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
        if previous_session_id:
            _out(f"Last session (full): {previous_session_id}")
        _out("=====================================")
    else:
        print("\nWorkflow completed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
