#!/usr/bin/env python3
"""Run Claude prompts sequentially from a YAML workflow."""

from __future__ import annotations

import argparse
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from claude_loop_lib.workflow import (
    load_workflow, get_steps, resolve_defaults,
    resolve_command_config,
    resolve_workflow_value,
    ISSUE_PLAN_YAML_FILENAME,
    WORKFLOW_YAML_FILES,
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
from claude_loop_lib.notify import (
    notify_completion,
    RunSummary,
    RESULT_SUCCESS, RESULT_FAILED, RESULT_INTERRUPTED,
)
from claude_loop_lib.validation import validate_startup
from claude_loop_lib import deferred_commands


YAML_DIR = Path(__file__).resolve().parent
DEFAULT_WORKING_DIRECTORY = Path(__file__).resolve().parent.parent

# Updated by the SIGTERM handler so the KeyboardInterrupt handler in main()
# can distinguish SIGTERM from a plain Ctrl-C.
_last_signal: str = "SIGINT"


def _sigterm_to_keyboard_interrupt(signum: int, frame: Any) -> None:
    global _last_signal
    _last_signal = "SIGTERM"
    raise KeyboardInterrupt


class RunStats:
    """Mutable counters aggregated during a run; converted to RunSummary in main()."""

    def __init__(self) -> None:
        self.completed_steps: int = 0
        self.completed_loops: int = 0
        self.failed_step: str | None = None
        self.workflow_label: str | None = None

    def merge(self, other: "RunStats") -> None:
        self.completed_steps += other.completed_steps
        self.completed_loops += other.completed_loops
        if self.failed_step is None and other.failed_step is not None:
            self.failed_step = other.failed_step
        if other.workflow_label is not None:
            self.workflow_label = other.workflow_label


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Claude workflow defined in YAML.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "-w",
        "--workflow",
        type=str,
        default="auto",
        help=(
            "Workflow selector: 'auto' (default) | 'full' | 'quick' | 'research' | "
            "'scout' | 'question' | path to a YAML file"
        ),
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
        "--no-deferred",
        action="store_true",
        help="Disable the deferred-command queue scan between steps (ver16.1 PHASE8.0 §2)",
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

    Returns "full", "quick", or "research". Falls back to "full" with a
    warning on any error (missing frontmatter / missing key / invalid value).
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
    if value not in ("quick", "full", "research"):
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


def _workflow_label_fallback(resolved: str | Path) -> str:
    """Derive a workflow label when RunStats has no label set."""
    if resolved == "auto":
        return "auto"
    if isinstance(resolved, Path):
        return resolved.stem
    return str(resolved)


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
) -> tuple[int, RunStats]:
    """Load a single YAML and execute its steps with the given slicing."""
    config = load_workflow(yaml_path)
    steps = get_steps(config)
    if start_index < 0 or start_index >= len(steps):
        raise SystemExit(
            f"start_index {start_index} out of range for {yaml_path.name} "
            f"(steps: {len(steps)})."
        )

    executable, prompt_flag, common_args = resolve_command_config(config)
    defaults = resolve_defaults(config)
    if shutil.which(executable) is None:
        raise SystemExit(f"Command not found: {executable}")

    if max_step_runs_override is not None:
        if max_step_runs_override <= 0:
            stats = RunStats()
            stats.workflow_label = yaml_path.stem
            return 0, stats
        step_iter = iter_steps_for_step_limit(steps, start_index, max_step_runs_override)
    elif args.max_step_runs is not None:
        step_iter = iter_steps_for_step_limit(steps, start_index, args.max_step_runs)
    else:
        loops = max_loops_override if max_loops_override is not None else args.max_loops
        step_iter = iter_steps_for_loop_limit(steps, start_index, loops)

    exit_code, stats = _run_steps(
        step_iter, steps, executable, prompt_flag, common_args,
        cwd, args.dry_run, tee, log_path,
        uncommitted_status, defaults,
        continue_disabled=continue_disabled,
        deferred_enabled=not args.no_deferred,
    )
    stats.workflow_label = yaml_path.stem
    return exit_code, stats


def _run_auto(
    args: argparse.Namespace,
    cwd: Path,
    yaml_dir: Path,
    tee: TeeWriter | None,
    log_path: Path | None,
    uncommitted_status: str | None,
) -> tuple[int, RunStats]:
    """Run --workflow auto: phase 1 = /issue_plan, phase 2 = full|quick steps[1:]."""
    phase1_yaml = yaml_dir / ISSUE_PLAN_YAML_FILENAME
    combined = RunStats()
    combined.workflow_label = "auto"

    # Record mtime of every existing ROUGH_PLAN.md before phase 1 runs.
    # Only files created after this snapshot (mtime > threshold) will be
    # considered as the phase-1 output, guarding against stale touch / coarse
    # filesystem resolution causing a wrong file to be picked up.
    _, pre_existing = _rough_plan_candidates(cwd)
    mtime_threshold = max((p.stat().st_mtime for p in pre_existing), default=0.0)

    exit_code, phase1_stats = _execute_yaml(
        phase1_yaml, args, cwd, tee, log_path, uncommitted_status,
        start_index=0, continue_disabled=False,
        max_step_runs_override=1,
    )
    # Aggregate phase1 steps only, not loops. Phase1 is a single-step gateway
    # (issue_plan); its loop completion must not inflate the user-visible loop count.
    combined.completed_steps += phase1_stats.completed_steps
    if phase1_stats.failed_step is not None:
        combined.failed_step = phase1_stats.failed_step
    combined.workflow_label = "auto"
    if exit_code != 0:
        return exit_code, combined

    def _out(line: str) -> None:
        if tee is not None:
            tee.write_line(line)
        else:
            print(line)

    if args.dry_run:
        _out("")
        _out("--- auto: phase2 skipped (--dry-run) ---")
        combined.workflow_label = "auto"
        return 0, combined

    rough_plan = _find_latest_rough_plan(cwd, mtime_threshold=mtime_threshold)
    phase2_kind = _read_workflow_kind(rough_plan)
    # phase2_kind は _read_workflow_kind により "quick" / "full" / "research" のいずれか。
    # WORKFLOW_YAML_FILES を経由することで workflow 値が増えても分岐追加が不要。
    phase2_yaml = yaml_dir / WORKFLOW_YAML_FILES[phase2_kind]

    _out("")
    _out(f"--- auto: phase2 = {phase2_kind} ({phase2_yaml.name}) ---")

    config2 = load_workflow(phase2_yaml)
    steps2 = get_steps(config2)
    if len(steps2) < 2:
        _out(f"WARNING: phase2 YAML has {len(steps2)} step(s); nothing to run.")
        combined.workflow_label = f"auto({phase2_kind})"
        return 0, combined
    first_name = steps2[0].get("name")
    if first_name != "issue_plan":
        _out(
            f"WARNING: phase2 YAML step[0] is {first_name!r}, "
            f"expected 'issue_plan'. Skipping anyway."
        )

    remaining_budget = _compute_remaining_budget(args, completed=1)

    exit_code, phase2_stats = _execute_yaml(
        phase2_yaml, args, cwd, tee, log_path,
        uncommitted_status=None,
        start_index=1, continue_disabled=False,
        max_step_runs_override=remaining_budget,
    )
    combined.merge(phase2_stats)
    combined.workflow_label = f"auto({phase2_kind})"
    return exit_code, combined


def main() -> int:
    args = parse_args()
    resolved = resolve_workflow_value(args.workflow, YAML_DIR)
    validate_auto_args(resolved, args)

    global _last_signal
    _last_signal = "SIGINT"
    try:
        signal.signal(signal.SIGTERM, _sigterm_to_keyboard_interrupt)
    except (ValueError, OSError):
        pass  # best-effort on platforms where SIGTERM handlers cannot be set

    workflow_start = time.monotonic()
    result = RESULT_SUCCESS
    exit_code = 0
    interrupt_reason: str | None = None
    stats = RunStats()

    try:
        cwd = args.cwd.expanduser().resolve()
        if not cwd.is_dir():
            raise SystemExit(f"Working directory not found: {cwd}")

        validate_startup(resolved, args, YAML_DIR, cwd)

        uncommitted_status = _resolve_uncommitted_status(args, cwd)

        enable_log = not args.no_log and not args.dry_run
        log_yaml_for_naming = (
            YAML_DIR / ISSUE_PLAN_YAML_FILENAME if resolved == "auto" else resolved
        )

        def _run_selected(tee: TeeWriter | None, log_path: Path | None) -> tuple[int, RunStats]:
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
                exit_code, stats = _run_selected(tee, log_path)
        else:
            exit_code, stats = _run_selected(None, None)

        if exit_code != 0:
            result = RESULT_FAILED
    except KeyboardInterrupt:
        result = RESULT_INTERRUPTED
        interrupt_reason = _last_signal
        exit_code = 130
    except SystemExit as e:
        code = e.code
        if isinstance(code, int):
            exit_code = code
        elif code is None:
            exit_code = 0
        else:
            exit_code = 1
        if exit_code != 0:
            result = RESULT_FAILED
        raise
    finally:
        if not args.no_notify and not args.dry_run:
            total_duration = time.monotonic() - workflow_start
            label = stats.workflow_label or _workflow_label_fallback(resolved)
            summary = RunSummary(
                workflow_label=label,
                result=result,
                duration_seconds=total_duration,
                loops_completed=stats.completed_loops,
                steps_completed=stats.completed_steps,
                exit_code=exit_code if result != RESULT_SUCCESS else None,
                failed_step=stats.failed_step,
                interrupt_reason=interrupt_reason if result == RESULT_INTERRUPTED else None,
            )
            notify_completion(summary)

    return exit_code


def _execute_single_step(
    *,
    command: list[str],
    cwd: Path,
    tee: TeeWriter | None,
    prev_commit: str | None,
    step_start: float,
) -> tuple[int, str | None]:
    """Run one step's subprocess and emit the footer. Returns (exit_code, new_prev_commit)."""
    if tee is not None:
        tee.write_line("--- stdout/stderr ---")
        process = subprocess.Popen(
            command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        exit_code = tee.write_process_output(process)
    else:
        completed = subprocess.run(command, cwd=cwd, check=False)
        exit_code = completed.returncode

    duration_str = format_duration(time.monotonic() - step_start)

    if tee is not None:
        tee.write_line(f"--- end (exit: {exit_code}, duration: {duration_str}) ---")
        current_commit = get_head_commit(cwd)
        if current_commit and prev_commit and current_commit != prev_commit:
            tee.write_line(f"Commit: {prev_commit} -> {current_commit}")
        return exit_code, current_commit

    return exit_code, prev_commit


def _process_deferred(
    *,
    cwd: Path,
    session_id: str,
    executable: str,
    prompt_flag: str,
    common_args: list[str],
    tee: TeeWriter | None,
    out: Any,
) -> int:
    """Scan, execute, and consume pending deferred requests; resume Claude.

    Returns the resume subprocess exit code, or 0 when there is nothing pending.
    On orphan marker detection (prior SIGKILL mid-run), returns non-zero without
    executing any request so the workflow halts for human triage.
    """
    deferred_dir = deferred_commands.default_deferred_dir(cwd)

    orphans = deferred_commands.scan_orphans(deferred_dir)
    if orphans:
        out("")
        out(f"ERROR: deferred orphan markers detected ({len(orphans)} file(s)):")
        for marker in orphans:
            out(f"  - {marker}")
        out("Resolve manually (inspect / delete markers) before rerunning.")
        return 1

    pending = deferred_commands.scan_pending(deferred_dir)
    if not pending:
        return 0

    out("")
    out(f"--- deferred: {len(pending)} request(s) pending ---")

    results: list[deferred_commands.DeferredResult] = []
    done_dir = deferred_dir / "done"
    for req_path in pending:
        try:
            req = deferred_commands.validate_request(req_path)
        except ValueError as exc:
            out(f"[deferred] skip invalid request {req_path.name}: {exc}")
            deferred_commands.consume_request(req_path, done_dir)
            continue
        out(f"[deferred] executing {req['request_id']} from '{req['source_step']}'")
        try:
            result = deferred_commands.execute_request(req, deferred_dir=deferred_dir)
        finally:
            deferred_commands.consume_request(req_path, done_dir)
        for line in deferred_commands.summarize_result(result):
            out(line)
        results.append(result)

    if not results:
        return 0

    resume_prompt = deferred_commands.build_resume_prompt(results)
    resume_command = build_command(
        executable, prompt_flag, common_args,
        step={"prompt": resume_prompt, "args": []},
        session_id=session_id, resume=True,
    )
    out("--- deferred: resuming Claude ---")
    out(f"$ {shlex.join(resume_command)}")
    resume_start = time.monotonic()
    if tee is not None:
        process = subprocess.Popen(
            resume_command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        resume_code = tee.write_process_output(process)
    else:
        completed = subprocess.run(resume_command, cwd=cwd, check=False)
        resume_code = completed.returncode
    out(
        f"--- deferred: resume end (exit: {resume_code}, "
        f"duration: {format_duration(time.monotonic() - resume_start)}) ---"
    )
    return resume_code


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
    uncommitted_status: str | None = None,
    defaults: dict[str, str] | None = None,
    continue_disabled: bool = False,
    deferred_enabled: bool = True,
) -> tuple[int, RunStats]:
    """Execute workflow steps with optional logging via TeeWriter."""
    total_steps = len(steps)
    workflow_start = time.monotonic()
    start_time = datetime.now()
    start_commit = get_head_commit(cwd)
    stats = RunStats()
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
            executable, prompt_flag, common_args, step, log_file_path,
            feedbacks=feedback_contents or None, defaults=defaults,
            session_id=session_id, resume=resume,
        )
        command_str = shlex.join(command)

        step_start = time.monotonic()
        step_start_time = datetime.now()

        effective_defaults = defaults or {}
        effective_model = step.get("model", effective_defaults.get("model"))
        effective_effort = step.get("effort", effective_defaults.get("effort"))
        effective_system_prompt = step.get(
            "system_prompt", effective_defaults.get("system_prompt")
        )
        effective_append_sp = step.get(
            "append_system_prompt", effective_defaults.get("append_system_prompt")
        )
        descriptor_parts: list[str] = []
        if effective_model is not None:
            descriptor_parts.append(f"Model: {effective_model}")
        if effective_effort is not None:
            descriptor_parts.append(f"Effort: {effective_effort}")
        if effective_system_prompt is not None:
            descriptor_parts.append("SystemPrompt: set")
        if effective_append_sp is not None:
            descriptor_parts.append("AppendSystemPrompt: set")
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

        exit_code, prev_commit = _execute_single_step(
            command=command,
            cwd=cwd,
            tee=tee,
            prev_commit=prev_commit,
            step_start=step_start,
        )

        # --- Handle failure ---
        if exit_code != 0:
            stats.failed_step = step["name"]
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
            return exit_code, stats

        if feedback_files:
            consume_feedbacks(feedback_files, feedbacks_dir / "done")

        if deferred_enabled:
            resume_code = _process_deferred(
                cwd=cwd,
                session_id=session_id,
                executable=executable,
                prompt_flag=prompt_flag,
                common_args=common_args,
                tee=tee,
                out=_out,
            )
            if resume_code != 0:
                stats.failed_step = f"{step['name']} (deferred resume)"
                fail_msg = (
                    f"Deferred resume failed with exit code {resume_code} "
                    f"after step: {step['name']}"
                )
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
                    _out(
                        f"Result: FAILED at deferred resume after step "
                        f"{absolute_index}/{total_steps} ({step['name']})"
                    )
                    _out(f"Last session (full): {session_id}")
                    _out("=====================================")
                print(fail_msg, file=sys.stderr)
                return resume_code, stats

        previous_session_id = session_id
        stats.completed_steps += 1
        if absolute_index == total_steps:
            stats.completed_loops += 1

    if not ran_any_step:
        _out("No steps to run.")
        return 0, stats

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
        _out(f"Result: SUCCESS ({stats.completed_steps}/{stats.completed_steps} steps completed)")
        if previous_session_id:
            _out(f"Last session (full): {previous_session_id}")
        _out("=====================================")
    else:
        print("\nWorkflow completed.")

    return 0, stats


if __name__ == "__main__":
    raise SystemExit(main())
