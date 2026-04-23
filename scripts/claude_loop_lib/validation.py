"""Startup-time validation for workflow configurations.

Runs before any step executes. Collects violations across all target YAMLs
and exits with a bulk report on error. Warnings print to stderr and execution
proceeds.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from claude_loop_lib.workflow import (
    ALLOWED_DEFAULTS_KEYS,
    ALLOWED_STEP_KEYS,
    FULL_YAML_FILENAME,
    ISSUE_PLAN_YAML_FILENAME,
    OVERRIDE_STRING_KEYS,
    QUICK_YAML_FILENAME,
)


KNOWN_MODELS: frozenset[str] = frozenset({"opus", "sonnet", "haiku"})
KNOWN_EFFORTS: frozenset[str] = frozenset({"low", "medium", "high", "xhigh", "max"})


@dataclass(frozen=True)
class Violation:
    source: str
    message: str
    severity: str  # "error" | "warning"


def validate_startup(
    resolved: str | Path,
    args: argparse.Namespace,
    yaml_dir: Path,
    cwd: Path,
) -> None:
    """Collect violations across all target YAMLs and report.

    Raises SystemExit(2) with a bulk report if any error-severity violation is
    collected. Warnings print to stderr and execution proceeds.
    """
    violations: list[Violation] = []
    violations.extend(_validate_category(cwd))
    violations.extend(_validate_cwd(cwd))
    yaml_paths = _resolve_target_yamls(resolved, args, yaml_dir)
    for yaml_path in yaml_paths:
        violations.extend(_validate_single_yaml(yaml_path, cwd))
    _report(violations)


def _resolve_target_yamls(
    resolved: str | Path,
    args: argparse.Namespace,  # noqa: ARG001 - kept for future extensibility
    yaml_dir: Path,
) -> list[Path]:
    if resolved == "auto":
        return [
            yaml_dir / ISSUE_PLAN_YAML_FILENAME,
            yaml_dir / FULL_YAML_FILENAME,
            yaml_dir / QUICK_YAML_FILENAME,
        ]
    return [resolved if isinstance(resolved, Path) else Path(resolved)]


def _validate_category(cwd: Path) -> list[Violation]:
    cat_file = cwd / ".claude" / "CURRENT_CATEGORY"
    if not cat_file.is_file():
        return [Violation(
            "category",
            ".claude/CURRENT_CATEGORY not found; defaulting to 'app'.",
            "warning",
        )]
    category = cat_file.read_text(encoding="utf-8").strip()
    if not category:
        return [Violation(
            "category",
            ".claude/CURRENT_CATEGORY is empty.",
            "error",
        )]
    if "/" in category or "\\" in category or category.startswith("."):
        return [Violation(
            "category",
            f"Invalid category name: {category!r}",
            "error",
        )]
    docs_dir = cwd / "docs" / category
    if not docs_dir.is_dir():
        return [Violation(
            "category",
            f"docs/{category}/ directory does not exist.",
            "error",
        )]
    return []


def _validate_cwd(cwd: Path) -> list[Violation]:
    if not cwd.is_dir():
        return [Violation("cwd", f"Not a directory: {cwd}", "error")]
    return []


def _validate_single_yaml(yaml_path: Path, cwd: Path) -> list[Violation]:
    source_prefix = f"yaml/{yaml_path.name}"
    violations: list[Violation] = []

    if not yaml_path.is_file():
        violations.append(Violation(source_prefix, f"File not found: {yaml_path}", "error"))
        return violations

    try:
        raw = yaml_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        violations.append(Violation(source_prefix, f"YAML parse error: {exc}", "error"))
        return violations
    except OSError as exc:
        violations.append(Violation(source_prefix, f"Read error: {exc}", "error"))
        return violations

    if not isinstance(data, dict):
        violations.append(Violation(
            source_prefix, "Top-level YAML must be a mapping.", "error",
        ))
        return violations

    violations.extend(_validate_command_section(data, source_prefix))
    violations.extend(_validate_defaults_section(data, source_prefix))
    violations.extend(_validate_steps_section(data, source_prefix, cwd))

    return violations


def _validate_command_section(data: dict[str, Any], prefix: str) -> list[Violation]:
    violations: list[Violation] = []
    command_config = data.get("command")
    if command_config is not None and not isinstance(command_config, dict):
        violations.append(Violation(
            f"{prefix}/command",
            "'command' must be a mapping when provided.",
            "error",
        ))
        return violations

    if isinstance(command_config, dict):
        executable = command_config.get("executable", "claude")
    else:
        executable = "claude"

    if isinstance(executable, str) and executable.strip():
        if shutil.which(executable) is None:
            violations.append(Violation(
                f"{prefix}/command.executable",
                f"Executable not found on PATH: {executable}",
                "error",
            ))
    elif executable is not None:
        violations.append(Violation(
            f"{prefix}/command.executable",
            "Must be a non-empty string.",
            "error",
        ))
    return violations


def _validate_defaults_section(data: dict[str, Any], prefix: str) -> list[Violation]:
    violations: list[Violation] = []
    defaults_config = data.get("defaults")
    if defaults_config is None:
        return []
    if not isinstance(defaults_config, dict):
        violations.append(Violation(
            f"{prefix}/defaults", "'defaults' must be a mapping.", "error",
        ))
        return violations
    unknown = set(defaults_config.keys()) - ALLOWED_DEFAULTS_KEYS
    if unknown:
        violations.append(Violation(
            f"{prefix}/defaults",
            f"Unknown keys: {sorted(unknown)}. Allowed: {sorted(ALLOWED_DEFAULTS_KEYS)}",
            "error",
        ))
    for key in OVERRIDE_STRING_KEYS:
        value = defaults_config.get(key)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            violations.append(Violation(
                f"{prefix}/defaults.{key}",
                "Must be a non-empty string.",
                "error",
            ))
            continue
        violations.extend(_check_value_whitelist(key, value, f"{prefix}/defaults.{key}"))
    return violations


def _validate_steps_section(
    data: dict[str, Any], prefix: str, cwd: Path,
) -> list[Violation]:
    violations: list[Violation] = []
    raw_steps = data.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        violations.append(Violation(
            f"{prefix}/steps", "Must be a non-empty list.", "error",
        ))
        return violations

    skills_dir = cwd / ".claude" / "skills"
    for index, raw_step in enumerate(raw_steps, start=1):
        step_source = f"{prefix}/steps[{index}]"
        if not isinstance(raw_step, dict):
            violations.append(Violation(step_source, "Must be a mapping.", "error"))
            continue

        prompt = raw_step.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            violations.append(Violation(
                f"{step_source}.prompt", "Must be a non-empty string.", "error",
            ))
        else:
            stripped = prompt.strip()
            if stripped.startswith("/"):
                skill_name = stripped.split(None, 1)[0].lstrip("/")
                skill_md = skills_dir / skill_name / "SKILL.md"
                if not skill_md.is_file():
                    violations.append(Violation(
                        f"{step_source}.prompt",
                        f"SKILL '/{skill_name}' not found at "
                        f".claude/skills/{skill_name}/SKILL.md",
                        "error",
                    ))

        name = raw_step.get("name")
        if name is not None and not isinstance(name, str):
            violations.append(Violation(
                f"{step_source}.name", "Must be a string.", "error",
            ))

        unknown = set(raw_step.keys()) - ALLOWED_STEP_KEYS
        if unknown:
            violations.append(Violation(
                step_source,
                f"Unknown keys: {sorted(unknown)}. Allowed: {sorted(ALLOWED_STEP_KEYS)}",
                "error",
            ))

        for key in OVERRIDE_STRING_KEYS:
            if key not in raw_step or raw_step[key] is None:
                continue
            value = raw_step[key]
            if not isinstance(value, str) or not value.strip():
                violations.append(Violation(
                    f"{step_source}.{key}", "Must be a non-empty string.", "error",
                ))
                continue
            violations.extend(_check_value_whitelist(key, value, f"{step_source}.{key}"))

        if "continue" in raw_step and raw_step["continue"] is not None:
            if not isinstance(raw_step["continue"], bool):
                violations.append(Violation(
                    f"{step_source}.continue", "Must be a boolean.", "error",
                ))

    return violations


def _check_value_whitelist(key: str, value: str, source: str) -> list[Violation]:
    if key == "model" and value not in KNOWN_MODELS:
        return [Violation(
            source,
            f"Unknown model {value!r}. Known: {sorted(KNOWN_MODELS)}",
            "warning",
        )]
    if key == "effort" and value not in KNOWN_EFFORTS:
        return [Violation(
            source,
            f"Unknown effort {value!r}. Known: {sorted(KNOWN_EFFORTS)}",
            "warning",
        )]
    return []


def _report(violations: list[Violation]) -> None:
    if not violations:
        return
    errors = [v for v in violations if v.severity == "error"]
    warnings = [v for v in violations if v.severity == "warning"]

    for v in warnings:
        print(f"VALIDATION WARNING [{v.source}]: {v.message}", file=sys.stderr)

    if not errors:
        return

    print("", file=sys.stderr)
    print(f"Startup validation failed ({len(errors)} error(s)):", file=sys.stderr)
    for v in errors:
        print(f"  [{v.source}] {v.message}", file=sys.stderr)
    raise SystemExit(2)
