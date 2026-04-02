#!/usr/bin/env python3
"""Run Claude prompts sequentially from a YAML workflow."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
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
                "args": normalize_string_list(raw_step.get("args"), f"steps[{index}].args"),
            }
        )

    return steps


def resolve_command_config(config: dict[str, Any]) -> tuple[str, str, list[str]]:
    command_config = config.get("command") or {}
    if not isinstance(command_config, dict):
        raise SystemExit("'command' must be a mapping when provided.")

    executable = command_config.get("executable", "claude")
    prompt_flag = command_config.get("prompt_flag", "-p")
    common_args = normalize_string_list(command_config.get("args"), "command.args")

    if not isinstance(executable, str) or not executable.strip():
        raise SystemExit("'command.executable' must be a non-empty string.")
    if not isinstance(prompt_flag, str) or not prompt_flag.strip():
        raise SystemExit("'command.prompt_flag' must be a non-empty string.")

    return executable, prompt_flag, common_args


def build_command(
    executable: str,
    prompt_flag: str,
    common_args: list[str],
    step: dict[str, Any],
) -> list[str]:
    return [executable, prompt_flag, step["prompt"], *common_args, *step["args"]]


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


def main() -> int:
    args = parse_args()
    config = load_workflow(args.workflow)
    steps = get_steps(config)

    if args.start < 1 or args.start > len(steps):
        raise SystemExit(
            f"--start must be between 1 and {len(steps)}. Received: {args.start}"
        )

    executable, prompt_flag, common_args = resolve_command_config(config)
    if shutil.which(executable) is None:
        raise SystemExit(f"Command not found: {executable}")

    cwd = args.cwd.expanduser().resolve()
    if not cwd.is_dir():
        raise SystemExit(f"Working directory not found: {cwd}")

    if args.max_step_runs is not None:
        step_iter = iter_steps_for_step_limit(steps, args.start - 1, args.max_step_runs)
    else:
        step_iter = iter_steps_for_loop_limit(steps, args.start - 1, args.max_loops)

    ran_any_step = False
    for step, absolute_index in step_iter:
        ran_any_step = True
        command = build_command(executable, prompt_flag, common_args, step)
        print_step_header(absolute_index, len(steps), step["name"])
        print(f"$ {' '.join(command)}")

        if args.dry_run:
            continue

        completed = subprocess.run(command, cwd=cwd, check=False)
        if completed.returncode != 0:
            print(
                f"Step failed with exit code {completed.returncode}: {step['name']}",
                file=sys.stderr,
            )
            return completed.returncode

    if not ran_any_step:
        print("No steps to run.")
        return 0

    print("\nWorkflow completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())