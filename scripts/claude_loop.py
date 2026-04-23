#!/usr/bin/env python3
"""Run Claude prompts sequentially from a YAML workflow."""

from __future__ import annotations

import argparse
import re
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
    resolve_workflow_value,
    FULL_YAML_FILENAME, QUICK_YAML_FILENAME, ISSUE_PLAN_YAML_FILENAME,
)
from claude_loop_lib.frontmatter import parse_frontmatter
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


YAML_DIR = Path(__file__).resolve().parent
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
        type=str,
        default="auto",
        help="Workflow selector: 'auto' (default) | 'full' | 'quick' | path to a YAML file",
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


def validate_auto_args(resolved: str | Path, args: argparse.Namespace) -> None:
    """Raise SystemExit if --workflow auto is used with unsupported options."""
    if resolved == "auto" and args.start > 1:
        raise SystemExit(
            "--workflow auto requires --start 1 (cannot skip /issue_plan phase)."
        )


def _rough_plan_candidates(cwd: Path) -> tuple[Path, list[Path]]:
    """Return (docs_dir, candidate_paths) for all ROUGH_PLAN.md under the current category."""
    cat_file = cwd / ".claude" / "CURRENT_CATEGORY"
    category = cat_file.read_text(encoding="utf-8").strip() if cat_file.is_file() else "app"
    docs_dir = cwd / "docs" / category
    return docs_dir, list(docs_dir.glob("ver*/ROUGH_PLAN.md"))


def _version_key(path: Path) -> tuple[int, int]:
    """Extract (major, minor) for natural version sort from a ROUGH_PLAN.md path."""
    m = re.match(r"ver(\d+)(?:\.(\d+))?$", path.parent.name)
    if m:
        return (int(m.group(1)), int(m.group(2)) if m.group(2) is not None else -1)
    return (0, 0)


def _find_latest_rough_plan(cwd: Path, mtime_threshold: float | None = None) -> Path:
    """Locate the ROUGH_PLAN.md created by phase 1 of --workflow auto.

    When mtime_threshold is given, only files with mtime strictly greater than
    the threshold are considered (guards against pre-existing files being picked up
    by a touch or coarse-resolution filesystem). Among qualifying files the highest
    version number wins. Raises SystemExit if none found.

    When mtime_threshold is None, falls back to the original mtime-max behaviour
    (used by callers that do not track the pre-phase-1 snapshot).
    """
    docs_dir, candidates = _rough_plan_candidates(cwd)
    if not candidates:
        raise SystemExit(
            f"auto workflow: no ROUGH_PLAN.md found under {docs_dir}. "
            f"Did /issue_plan fail silently? "
            f"(When .claude/CURRENT_CATEGORY is unset, 'app' is used.)"
        )
    if mtime_threshold is None:
        return max(candidates, key=lambda p: p.stat().st_mtime)

    new_candidates = [p for p in candidates if p.stat().st_mtime > mtime_threshold]
    if not new_candidates:
        raise SystemExit(
            f"auto workflow: /issue_plan did not create a new ROUGH_PLAN.md "
            f"(no file under {docs_dir} has mtime newer than the pre-phase-1 snapshot). "
            f"Check that /issue_plan ran successfully and wrote its output."
        )
    return max(new_candidates, key=_version_key)


def _read_workflow_kind(rough_plan: Path) -> str:
    """Read the `workflow:` frontmatter value from a ROUGH_PLAN.md.

    Returns "full" or "quick". Falls back to "full" with a warning on any
    error (missing frontmatter / missing key / invalid value).
    """
    text = rough_plan.read_text(encoding="utf-8")
    fm, _body = parse_frontmatter(text)
    if fm is None:
        print(
            f"WARNING: no frontmatter in {rough_plan}; falling back to 'full'.",
            file=sys.stderr,
        )
        return "full"
    value = fm.get("workflow")
    if value not in ("quick", "full"):
        print(
            f"WARNING: invalid workflow={value!r} in {rough_plan}; falling back to 'full'.",
            file=sys.stderr,
        )
        return "full"
    return value


def _compute_remaining_budget(args: argparse.Namespace, completed: int) -> int | None:
    """Return remaining --max-step-runs budget after `completed` steps, or None if unset."""
    if args.max_step_runs is None:
        return None
    return max(args.max_step_runs - completed, 0)


def _resolve_uncommitted_status(args: argparse.Namespace, cwd: Path) -> str | None:
    if args.dry_run:
        return None
    if not check_uncommitted_changes(cwd):
        return None
    if args.auto_commit_before:
        commit_hash = auto_commit_changes(cwd)
        if commit_hash:
            print(f"Auto-committed uncommitted changes: {commit_hash}")
            return f"auto-committed ({commit_hash})"
        print("WARNING: Auto-commit failed. Proceeding with uncommitted changes.", file=sys.stderr)
        return "auto-commit failed, proceeding with uncommitted changes"
    print(
        "WARNING: Uncommitted changes detected. Consider committing before running the workflow.",
        file=sys.stderr,
    )
    return "uncommitted changes detected (no --auto-commit-before)"


def _execute_yaml(
    yaml_path: Path,
    args: argparse.Namespace,
    cwd: Path,
    tee: TeeWriter | None,
    log_path: Path | None,
    uncommitted_status: str | None,
    start_index: int,
    continue_disabled: bool,
    max_step_runs_override: int | None = None,
    max_loops_override: int | None = None,
) -> int:
    """Load a single YAML and execute its steps with the given slicing."""
    config = load_workflow(yaml_path)
    steps = get_steps(config)
    if start_index < 0 or start_index >= len(steps):
        raise SystemExit(
            f"start_index {start_index} out of range for {yaml_path.name} "
            f"(steps: {len(steps)})."
        )

    executable, prompt_flag, common_args, auto_args = resolve_command_config(config)
    defaults = resolve_defaults(config)
    auto_mode = resolve_mode(config, args.auto)
    if auto_mode:
        common_args = common_args + auto_args
    if shutil.which(executable) is None:
        raise SystemExit(f"Command not found: {executable}")

    if max_step_runs_override is not None:
        if max_step_runs_override <= 0:
            return 0
        step_iter = iter_steps_for_step_limit(steps, start_index, max_step_runs_override)
    elif args.max_step_runs is not None:
        step_iter = iter_steps_for_step_limit(steps, start_index, args.max_step_runs)
    else:
        loops = max_loops_override if max_loops_override is not None else args.max_loops
        step_iter = iter_steps_for_loop_limit(steps, start_index, loops)

    return _run_steps(
        step_iter, steps, executable, prompt_flag, common_args,
        cwd, args.dry_run, tee, log_path, auto_mode,
        uncommitted_status, defaults,
        continue_disabled=continue_disabled,
    )


def _run_auto(
    args: argparse.Namespace,
    cwd: Path,
    yaml_dir: Path,
    tee: TeeWriter | None,
    log_path: Path | None,
    uncommitted_status: str | None,
) -> int:
    """Run --workflow auto: phase 1 = /issue_plan, phase 2 = full|quick steps[1:]."""
    phase1_yaml = yaml_dir / ISSUE_PLAN_YAML_FILENAME

    # Record mtime of every existing ROUGH_PLAN.md before phase 1 runs.
    # Only files created after this snapshot (mtime > threshold) will be
    # considered as the phase-1 output, guarding against stale touch / coarse
    # filesystem resolution causing a wrong file to be picked up.
    _, pre_existing = _rough_plan_candidates(cwd)
    mtime_threshold = max((p.stat().st_mtime for p in pre_existing), default=0.0)

    exit_code = _execute_yaml(
        phase1_yaml, args, cwd, tee, log_path, uncommitted_status,
        start_index=0, continue_disabled=False,
        max_step_runs_override=1,
    )
    if exit_code != 0:
        return exit_code

    def _out(line: str) -> None:
        if tee is not None:
            tee.write_line(line)
        else:
            print(line)

    if args.dry_run:
        _out("")
        _out("--- auto: phase2 skipped (--dry-run) ---")
        return 0

    rough_plan = _find_latest_rough_plan(cwd, mtime_threshold=mtime_threshold)
    phase2_kind = _read_workflow_kind(rough_plan)
    phase2_yaml = yaml_dir / (
        QUICK_YAML_FILENAME if phase2_kind == "quick" else FULL_YAML_FILENAME
    )

    _out("")
    _out(f"--- auto: phase2 = {phase2_kind} ({phase2_yaml.name}) ---")

    config2 = load_workflow(phase2_yaml)
    steps2 = get_steps(config2)
    if len(steps2) < 2:
        _out(f"WARNING: phase2 YAML has {len(steps2)} step(s); nothing to run.")
        return 0
    first_name = steps2[0].get("name")
    if first_name != "issue_plan":
        _out(
            f"WARNING: phase2 YAML step[0] is {first_name!r}, "
            f"expected 'issue_plan'. Skipping anyway."
        )

    remaining_budget = _compute_remaining_budget(args, completed=1)

    return _execute_yaml(
        phase2_yaml, args, cwd, tee, log_path,
        uncommitted_status=None,
        start_index=1, continue_disabled=False,
        max_step_runs_override=remaining_budget,
    )


def main() -> int:
    args = parse_args()
    resolved = resolve_workflow_value(args.workflow, YAML_DIR)
    validate_auto_args(resolved, args)

    cwd = args.cwd.expanduser().resolve()
    if not cwd.is_dir():
        raise SystemExit(f"Working directory not found: {cwd}")

    uncommitted_status = _resolve_uncommitted_status(args, cwd)

    enable_log = not args.no_log and not args.dry_run
    log_yaml_for_naming = (
        YAML_DIR / ISSUE_PLAN_YAML_FILENAME if resolved == "auto" else resolved
    )

    workflow_start = time.monotonic()

    def _run_selected(tee: TeeWriter | None, log_path: Path | None) -> int:
        if resolved == "auto":
            return _run_auto(args, cwd, YAML_DIR, tee, log_path, uncommitted_status)
        if args.start < 1:
            raise SystemExit(f"--start must be >= 1. Received: {args.start}")
        return _execute_yaml(
            resolved, args, cwd, tee, log_path, uncommitted_status,
            start_index=args.start - 1,
            continue_disabled=args.start > 1,
        )

    if enable_log:
        log_path = create_log_path(args.log_dir, log_yaml_for_naming)
        with open(log_path, "w", encoding="utf-8") as log_file:
            tee = TeeWriter(log_file)
            exit_code = _run_selected(tee, log_path)
    else:
        exit_code = _run_selected(None, None)

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
