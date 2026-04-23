"""Command construction and step iterators for workflow execution."""

from __future__ import annotations

from typing import Any


def build_command(
    executable: str,
    prompt_flag: str,
    common_args: list[str],
    step: dict[str, Any],
    log_file_path: str | None = None,
    auto_mode: bool = False,
    feedbacks: list[str] | None = None,
    defaults: dict[str, str] | None = None,
    session_id: str | None = None,
    resume: bool = False,
) -> list[str]:
    cmd = [executable, prompt_flag, step["prompt"], *common_args, *step["args"]]
    defaults = defaults or {}
    for key, flag in (("model", "--model"), ("effort", "--effort")):
        value = step.get(key, defaults.get(key))
        if value is not None:
            cmd.extend([flag, value])
    if session_id is not None:
        if resume:
            cmd.extend(["-r", session_id])
        else:
            cmd.extend(["--session-id", session_id])
    system_prompts: list[str] = []
    if log_file_path:
        system_prompts.append(f"Current workflow log: {log_file_path}")
    if auto_mode:
        system_prompts.append(
            "Workflow execution mode: AUTO (unattended). "
            "Do not use AskUserQuestion. Write requests to REQUESTS/AI/ instead."
        )
    if feedbacks:
        feedback_section = "## User Feedback\n\n" + "\n\n---\n\n".join(feedbacks)
        system_prompts.append(feedback_section)
    if system_prompts:
        cmd.extend(["--append-system-prompt", "\n\n".join(system_prompts)])
    return cmd


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
