"""Token / USD cost tracking for Claude CLI invocations (PHASE8.0 §3).

Parses `--output-format json` output of the Claude Code CLI (SDKResultMessage-
compatible) to extract usage / total_cost_usd / modelUsage, records per-step
StepCost entries, and writes a sidecar JSON next to the workflow log.

Primary cost source: `total_cost_usd` field of the CLI JSON output (client-side
estimate computed by the CLI itself using the price table it was built with).
PRICE_BOOK_USD_PER_MTOK below is a fallback used only when total_cost_usd is
absent but usage tokens are available (e.g. partial output).

See docs/util/ver16.2/RESEARCH.md and EXPERIMENT.md for rationale.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, TypedDict


# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------


class StepCost(TypedDict):
    step_name: str
    session_id: str
    model: str | None
    started_at: str
    ended_at: str
    duration_seconds: float
    kind: str  # "claude" | "deferred_resume" | "deferred_external"
    input_tokens: int | None
    output_tokens: int | None
    cache_read_input_tokens: int | None
    cache_creation_input_tokens: int | None
    num_turns: int | None
    cost_usd: float | None
    cost_source: str | None  # "cli" | "fallback_price_book" | None
    status: str  # "ok" | "unavailable"
    reason: str | None


class RunCostSummary(TypedDict):
    workflow_label: str
    started_at: str
    ended_at: str
    claude_code_cli_version: str | None
    price_book_source: str
    total_cost_usd: float
    missing_steps: int
    steps: list[StepCost]


# ---------------------------------------------------------------------------
# Fallback price book (used only when CLI does not emit total_cost_usd)
# ---------------------------------------------------------------------------

PRICE_BOOK_SOURCE: str = (
    "https://platform.claude.com/docs/en/about-claude/pricing retrieved 2026-04-24"
)

# Unit: USD per million tokens (MTok). cache_write uses the 5m-tier rate
# because the Agent SDK Usage type does not carry the 5m/1h distinction
# (see RESEARCH.md Q3 / C2). Covers current-gen models only; unknown models
# fall through to status="unavailable" via calculate_cost.
PRICE_BOOK_USD_PER_MTOK: dict[str, dict[str, float]] = {
    "claude-opus-4-7":   {"input": 5.0, "cache_write": 6.25, "cache_read": 0.50, "output": 25.0},
    "claude-opus-4-6":   {"input": 5.0, "cache_write": 6.25, "cache_read": 0.50, "output": 25.0},
    "claude-opus-4-5":   {"input": 5.0, "cache_write": 6.25, "cache_read": 0.50, "output": 25.0},
    "claude-opus-4-1":   {"input": 15.0, "cache_write": 18.75, "cache_read": 1.50, "output": 75.0},
    "claude-opus-4":     {"input": 15.0, "cache_write": 18.75, "cache_read": 1.50, "output": 75.0},
    "claude-sonnet-4-6": {"input": 3.0, "cache_write": 3.75, "cache_read": 0.30, "output": 15.0},
    "claude-sonnet-4-5": {"input": 3.0, "cache_write": 3.75, "cache_read": 0.30, "output": 15.0},
    "claude-sonnet-4":   {"input": 3.0, "cache_write": 3.75, "cache_read": 0.30, "output": 15.0},
    "claude-haiku-4-5":  {"input": 1.0, "cache_write": 1.25, "cache_read": 0.10, "output": 5.0},
    "claude-haiku-3-5":  {"input": 0.80, "cache_write": 1.0, "cache_read": 0.08, "output": 4.0},
}


# ---------------------------------------------------------------------------
# CLI output parsing
# ---------------------------------------------------------------------------


def parse_cli_result(raw: bytes | str | None) -> dict[str, Any] | None:
    """Extract the SDKResultMessage JSON object from `--output-format json` output.

    Returns the parsed dict (expected to contain `usage`, `total_cost_usd`,
    `modelUsage`, `session_id`, `num_turns`, etc.) or None when the output is
    empty, non-JSON, or not a mapping. Caller wraps None into a
    status="unavailable" StepCost via build_step_cost.
    """
    if raw is None:
        return None
    if isinstance(raw, bytes):
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception:
            return None
    else:
        text = raw
    text = text.strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def _extract_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def extract_usage(result: dict[str, Any]) -> dict[str, int | None]:
    """Pull the 4 token counters out of a parsed CLI JSON object.

    Returns dict with keys input_tokens / output_tokens /
    cache_read_input_tokens / cache_creation_input_tokens, each int | None.
    """
    usage = result.get("usage")
    if not isinstance(usage, dict):
        return {
            "input_tokens": None,
            "output_tokens": None,
            "cache_read_input_tokens": None,
            "cache_creation_input_tokens": None,
        }
    return {
        "input_tokens": _extract_int(usage.get("input_tokens")),
        "output_tokens": _extract_int(usage.get("output_tokens")),
        "cache_read_input_tokens": _extract_int(usage.get("cache_read_input_tokens")),
        "cache_creation_input_tokens": _extract_int(usage.get("cache_creation_input_tokens")),
    }


def extract_model_name(result: dict[str, Any]) -> str | None:
    """Pick a model identifier from the modelUsage mapping (first key)."""
    model_usage = result.get("modelUsage")
    if isinstance(model_usage, dict) and model_usage:
        for key in model_usage.keys():
            if isinstance(key, str) and key:
                return key
    return None


def calculate_cost_from_price_book(
    usage: dict[str, int | None],
    *,
    model: str | None,
    price_book: dict[str, dict[str, float]] | None = None,
) -> float | None:
    """Fallback cost calculation when CLI does not report total_cost_usd.

    Returns None when model is unknown or all token counts are missing.
    """
    if model is None:
        return None
    book = price_book if price_book is not None else PRICE_BOOK_USD_PER_MTOK
    rates = book.get(model)
    if rates is None:
        return None
    total = 0.0
    any_counted = False
    for token_key, rate_key in (
        ("input_tokens", "input"),
        ("output_tokens", "output"),
        ("cache_read_input_tokens", "cache_read"),
        ("cache_creation_input_tokens", "cache_write"),
    ):
        count = usage.get(token_key)
        if count is None:
            continue
        rate = rates.get(rate_key)
        if rate is None:
            continue
        total += count * rate / 1_000_000.0
        any_counted = True
    if not any_counted:
        return None
    return total


# ---------------------------------------------------------------------------
# StepCost construction
# ---------------------------------------------------------------------------


def build_step_cost_from_cli_output(
    *,
    step_name: str,
    session_id: str,
    started_at: str,
    ended_at: str,
    duration_seconds: float,
    kind: str,
    raw_output: bytes | str | None,
    default_model: str | None = None,
    reason_when_missing: str = "no-json-output",
) -> StepCost:
    """Parse raw CLI output and produce a StepCost record."""
    result = parse_cli_result(raw_output)
    if result is None:
        return _unavailable_step(
            step_name=step_name,
            session_id=session_id,
            started_at=started_at,
            ended_at=ended_at,
            duration_seconds=duration_seconds,
            kind=kind,
            model=default_model,
            reason=reason_when_missing,
        )

    usage = extract_usage(result)
    model = extract_model_name(result) or default_model

    cost_value = result.get("total_cost_usd")
    cost_usd: float | None
    cost_source: str | None
    if isinstance(cost_value, (int, float)) and not isinstance(cost_value, bool):
        cost_usd = float(cost_value)
        cost_source = "cli"
    else:
        cost_usd = calculate_cost_from_price_book(usage, model=model)
        cost_source = "fallback_price_book" if cost_usd is not None else None

    num_turns = _extract_int(result.get("num_turns"))

    return StepCost(
        step_name=step_name,
        session_id=session_id,
        model=model,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration_seconds,
        kind=kind,
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
        cache_read_input_tokens=usage["cache_read_input_tokens"],
        cache_creation_input_tokens=usage["cache_creation_input_tokens"],
        num_turns=num_turns,
        cost_usd=cost_usd,
        cost_source=cost_source,
        status="ok",
        reason=None,
    )


def build_external_step_cost(
    *,
    step_name: str,
    session_id: str,
    started_at: str,
    ended_at: str,
    duration_seconds: float,
) -> StepCost:
    """Record a deferred external (non-Claude) command with cost=0."""
    return StepCost(
        step_name=step_name,
        session_id=session_id,
        model=None,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration_seconds,
        kind="deferred_external",
        input_tokens=None,
        output_tokens=None,
        cache_read_input_tokens=None,
        cache_creation_input_tokens=None,
        num_turns=None,
        cost_usd=0.0,
        cost_source=None,
        status="ok",
        reason=None,
    )


def _unavailable_step(
    *,
    step_name: str,
    session_id: str,
    started_at: str,
    ended_at: str,
    duration_seconds: float,
    kind: str,
    model: str | None,
    reason: str,
) -> StepCost:
    return StepCost(
        step_name=step_name,
        session_id=session_id,
        model=model,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration_seconds,
        kind=kind,
        input_tokens=None,
        output_tokens=None,
        cache_read_input_tokens=None,
        cache_creation_input_tokens=None,
        num_turns=None,
        cost_usd=None,
        cost_source=None,
        status="unavailable",
        reason=reason,
    )


def unavailable_step(
    *,
    step_name: str,
    session_id: str,
    started_at: str,
    ended_at: str,
    duration_seconds: float,
    kind: str,
    reason: str,
    model: str | None = None,
) -> StepCost:
    """Public constructor for an explicitly-unavailable StepCost."""
    return _unavailable_step(
        step_name=step_name,
        session_id=session_id,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration_seconds,
        kind=kind,
        model=model,
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Run aggregation + sidecar I/O
# ---------------------------------------------------------------------------


def aggregate_run(
    *,
    workflow_label: str,
    started_at: str,
    ended_at: str,
    steps: list[StepCost],
    claude_code_cli_version: str | None = None,
) -> RunCostSummary:
    total = 0.0
    missing = 0
    for step in steps:
        if step["status"] == "ok" and step["cost_usd"] is not None:
            total += step["cost_usd"]
        elif step["status"] != "ok":
            missing += 1
    return RunCostSummary(
        workflow_label=workflow_label,
        started_at=started_at,
        ended_at=ended_at,
        claude_code_cli_version=claude_code_cli_version,
        price_book_source=PRICE_BOOK_SOURCE,
        total_cost_usd=total,
        missing_steps=missing,
        steps=list(steps),
    )


def write_sidecar(path: Path, summary: RunCostSummary) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# CLI version probe
# ---------------------------------------------------------------------------


_VERSION_TOKEN_RE = re.compile(r"^\d+\.\d+\.\d+$")


def detect_claude_code_cli_version(executable: str = "claude") -> str | None:
    """Run `<executable> --version` once and return the leading semver token.

    Returns None on any subprocess error or non-semver first token. Safe to
    call on startup; does not consume Claude API tokens.
    """
    try:
        completed = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    stdout = completed.stdout.decode("utf-8", errors="replace").strip()
    if not stdout:
        return None
    first_line = stdout.splitlines()[0].strip()
    if not first_line:
        return None
    token = first_line.split(None, 1)[0]
    if _VERSION_TOKEN_RE.match(token):
        return token
    return token or None
