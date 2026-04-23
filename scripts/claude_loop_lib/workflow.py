"""YAML workflow loading, validation, and section resolvers."""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Any

import yaml


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

        step_entry: dict[str, Any] = {
            "name": name,
            "prompt": prompt,
            "args": normalize_cli_args(raw_step.get("args"), f"steps[{index}].args"),
        }
        for key in ("model", "effort"):
            if key in raw_step and raw_step[key] is not None:
                value = raw_step[key]
                if not isinstance(value, str) or not value.strip():
                    raise SystemExit(f"steps[{index}].{key} must be a non-empty string.")
                step_entry[key] = value
        if "continue" in raw_step and raw_step["continue"] is not None:
            value = raw_step["continue"]
            if not isinstance(value, bool):
                raise SystemExit(f"steps[{index}].continue must be a boolean.")
            step_entry["continue"] = value
        steps.append(step_entry)

    return steps


def resolve_defaults(config: dict[str, Any]) -> dict[str, str]:
    """Extract defaults.model / defaults.effort from config.

    Returns a dict with only the keys that were explicitly set. Absent keys are
    omitted so dict.get() / 'in' checks can be used uniformly with step-level
    overrides.
    """
    defaults_config = config.get("defaults") or {}
    if not isinstance(defaults_config, dict):
        raise SystemExit("'defaults' must be a mapping when provided.")

    result: dict[str, str] = {}
    for key in ("model", "effort"):
        value = defaults_config.get(key)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"'defaults.{key}' must be a non-empty string.")
        result[key] = value
    return result


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
