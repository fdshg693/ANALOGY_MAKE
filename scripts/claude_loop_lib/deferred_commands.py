"""Deferred command execution queue (ver16.1 PHASE8.0 §2).

Allows a Claude step to register long-running shell commands as structured
markdown request files. After the step exits, `_run_steps` scans the deferred
queue, executes each request out-of-process, writes a result artifact, and
resumes Claude via `-r <session-id>` with a structured summary prompt.

Layout under the configured deferred_dir (default: `<cwd>/data/deferred/`):

    deferred_dir/
      <request_id>.md          # pending request (frontmatter + body)
      <request_id>.started     # marker while execute_request is running
      done/<request_id>.md     # moved here after execute_request returns
      results/
        <request_id>.meta.json # structured metadata (schema in build_result_meta)
        <request_id>.stdout.log
        <request_id>.stderr.log

Schema / rationale: see docs/util/ver16.1/RESEARCH.md §Q6–Q9 and
docs/util/ver16.1/EXPERIMENT.md §U4/§U5.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

from claude_loop_lib.frontmatter import parse_frontmatter


HEAD_EXCERPT_LINES = 20
TAIL_EXCERPT_LINES = 20
REQUIRED_REQUEST_FIELDS = ("request_id", "source_step", "session_id")


class DeferredRequest(TypedDict):
    path: Path
    request_id: str
    source_step: str
    session_id: str
    cwd: Path
    commands: list[str]
    timeout_sec: int | None
    expected_artifacts: list[str]
    note: str


class DeferredResult(TypedDict):
    request_id: str
    source_step: str
    session_id: str
    commands: list[str]
    exit_codes: list[int]
    overall_exit_code: int
    started_at: str
    ended_at: str
    duration_sec: float
    stdout_bytes: int
    stdout_path: str
    stderr_bytes: int
    stderr_path: str
    head_excerpt: str
    tail_excerpt: str


def ensure_dirs(deferred_dir: Path) -> None:
    """Create deferred_dir and its done/ results/ subdirs if missing."""
    deferred_dir.mkdir(parents=True, exist_ok=True)
    (deferred_dir / "done").mkdir(exist_ok=True)
    (deferred_dir / "results").mkdir(exist_ok=True)


def scan_pending(deferred_dir: Path) -> list[Path]:
    """Return sorted list of pending request markdown paths (non-recursive)."""
    if not deferred_dir.is_dir():
        return []
    return sorted(p for p in deferred_dir.glob("*.md") if p.is_file())


def scan_orphans(deferred_dir: Path) -> list[Path]:
    """Return sorted list of stale `.started` marker files.

    A marker left behind indicates `execute_request` was killed mid-run and
    the corresponding request may have produced partial side effects.
    """
    if not deferred_dir.is_dir():
        return []
    return sorted(deferred_dir.glob("*.started"))


def validate_request(path: Path) -> DeferredRequest:
    """Parse and validate a request markdown file. Raises ValueError on error."""
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    if fm is None:
        raise ValueError(f"{path.name}: missing or invalid YAML frontmatter")

    for key in REQUIRED_REQUEST_FIELDS:
        value = fm.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{path.name}: frontmatter field '{key}' must be a non-empty string")

    commands = _extract_bash_block(body)
    if not commands:
        raise ValueError(f"{path.name}: body must contain a fenced ```bash``` block with at least one command")

    cwd_field = fm.get("cwd")
    if cwd_field is None:
        req_cwd = path.resolve().parents[2] if len(path.resolve().parents) >= 3 else Path.cwd()
    elif isinstance(cwd_field, str) and cwd_field.strip():
        req_cwd = Path(cwd_field).expanduser()
    else:
        raise ValueError(f"{path.name}: frontmatter 'cwd' must be a non-empty string if set")

    timeout_sec = fm.get("timeout_sec")
    if timeout_sec is not None and not isinstance(timeout_sec, int):
        raise ValueError(f"{path.name}: frontmatter 'timeout_sec' must be an integer if set")

    expected = fm.get("expected_artifacts") or []
    if not isinstance(expected, list) or not all(isinstance(x, str) for x in expected):
        raise ValueError(f"{path.name}: 'expected_artifacts' must be a list of strings if set")

    note = fm.get("note") or ""
    if not isinstance(note, str):
        raise ValueError(f"{path.name}: 'note' must be a string if set")

    return DeferredRequest(
        path=path,
        request_id=fm["request_id"].strip(),
        source_step=fm["source_step"].strip(),
        session_id=fm["session_id"].strip(),
        cwd=req_cwd,
        commands=commands,
        timeout_sec=timeout_sec,
        expected_artifacts=expected,
        note=note,
    )


def _extract_bash_block(body: str) -> list[str]:
    """Return non-empty command lines from the first fenced ```bash``` block."""
    lines = body.split("\n")
    in_block = False
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not in_block:
            if stripped.startswith("```") and "bash" in stripped.lower():
                in_block = True
            continue
        if stripped.startswith("```"):
            break
        if stripped and not stripped.startswith("#"):
            collected.append(line.rstrip())
    return collected


def execute_request(req: DeferredRequest, *, deferred_dir: Path) -> DeferredResult:
    """Execute each command sequentially and persist stdout/stderr + meta.json.

    A `.started` marker file is written before execution and removed in a
    finally block so orphan detection can spot SIGKILL-style terminations.
    Commands run with `check=False` and stdout/stderr piped directly to log
    files (no PIPE, per subprocess docs D2 deadlock warning).
    """
    ensure_dirs(deferred_dir)
    results_dir = deferred_dir / "results"
    stdout_path = results_dir / f"{req['request_id']}.stdout.log"
    stderr_path = results_dir / f"{req['request_id']}.stderr.log"
    meta_path = results_dir / f"{req['request_id']}.meta.json"
    marker_path = deferred_dir / f"{req['request_id']}.started"

    started_at = datetime.now()
    start_monotonic = time.monotonic()
    exit_codes: list[int] = []

    marker_path.write_text("running\n", encoding="utf-8")
    try:
        with open(stdout_path, "wb") as out_f, open(stderr_path, "wb") as err_f:
            for cmd_line in req["commands"]:
                proc = subprocess.run(
                    cmd_line,
                    shell=True,
                    cwd=str(req["cwd"]),
                    stdout=out_f,
                    stderr=err_f,
                    check=False,
                    timeout=req["timeout_sec"],
                )
                exit_codes.append(proc.returncode)
                out_f.flush()
                err_f.flush()
                if proc.returncode != 0:
                    break
    finally:
        marker_path.unlink(missing_ok=True)

    duration_sec = time.monotonic() - start_monotonic
    ended_at = datetime.now()

    overall_exit_code = next((c for c in exit_codes if c != 0), 0)
    stdout_bytes = stdout_path.stat().st_size if stdout_path.exists() else 0
    stderr_bytes = stderr_path.stat().st_size if stderr_path.exists() else 0
    head_excerpt, tail_excerpt = _build_excerpts(stdout_path)

    result: DeferredResult = DeferredResult(
        request_id=req["request_id"],
        source_step=req["source_step"],
        session_id=req["session_id"],
        commands=list(req["commands"]),
        exit_codes=exit_codes,
        overall_exit_code=overall_exit_code,
        started_at=started_at.isoformat(timespec="seconds"),
        ended_at=ended_at.isoformat(timespec="seconds"),
        duration_sec=round(duration_sec, 3),
        stdout_bytes=stdout_bytes,
        stdout_path=str(stdout_path),
        stderr_bytes=stderr_bytes,
        stderr_path=str(stderr_path),
        head_excerpt=head_excerpt,
        tail_excerpt=tail_excerpt,
    )
    meta_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return result


def _build_excerpts(stdout_path: Path) -> tuple[str, str]:
    """Return (head_excerpt, tail_excerpt) from the stdout log, truncated by line."""
    if not stdout_path.exists():
        return "", ""
    try:
        text = stdout_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "", ""
    lines = text.splitlines()
    if len(lines) <= HEAD_EXCERPT_LINES + TAIL_EXCERPT_LINES:
        return "\n".join(lines), ""
    head = "\n".join(lines[:HEAD_EXCERPT_LINES])
    tail = "\n".join(lines[-TAIL_EXCERPT_LINES:])
    return head, tail


def consume_request(req_path: Path, done_dir: Path) -> Path:
    """Move the request file to done_dir, returning the new path.

    Must be called in both success and failure paths to keep the pending
    queue orphan-free (completion condition 4). Filename collisions are
    resolved by appending a numeric suffix.
    """
    done_dir.mkdir(parents=True, exist_ok=True)
    target = done_dir / req_path.name
    if target.exists():
        stem, suffix = req_path.stem, req_path.suffix
        idx = 1
        while True:
            candidate = done_dir / f"{stem}.{idx}{suffix}"
            if not candidate.exists():
                target = candidate
                break
            idx += 1
    shutil.move(str(req_path), str(target))
    return target


def build_resume_prompt(results: list[DeferredResult]) -> str:
    """Compose the additional prompt passed to `claude -r <session_id> -p ...`.

    Size-bounded: only the head/tail excerpts of stdout are embedded; full
    logs are referenced by path so Claude can Read them on demand. See
    EXPERIMENT.md §U4 for the excerpt-size experiment result.
    """
    if not results:
        return ""
    blocks: list[str] = ["DEFERRED EXECUTION COMPLETED:"]
    for r in results:
        block = (
            f"- request_id: {r['request_id']}\n"
            f"  source_step: {r['source_step']}\n"
            f"  overall_exit_code: {r['overall_exit_code']}\n"
            f"  exit_codes: {r['exit_codes']}\n"
            f"  duration_sec: {r['duration_sec']}\n"
            f"  stdout_bytes: {r['stdout_bytes']} (log: {r['stdout_path']})\n"
            f"  stderr_bytes: {r['stderr_bytes']} (log: {r['stderr_path']})\n"
            f"  head_excerpt: |\n{_indent(r['head_excerpt'], 4)}\n"
            f"  tail_excerpt: |\n{_indent(r['tail_excerpt'], 4)}"
        )
        blocks.append(block)
    blocks.append(
        "必要に応じて meta.json や stdout/stderr のログを Read して判断してください。"
        " 次 step に進む場合は workflow を継続し、致命的失敗なら exit 1 で停止してください。"
    )
    return "\n\n".join(blocks)


def _indent(text: str, spaces: int) -> str:
    prefix = " " * spaces
    if not text:
        return f"{prefix}(empty)"
    return "\n".join(f"{prefix}{line}" for line in text.split("\n"))


def default_deferred_dir(cwd: Path) -> Path:
    """Default deferred queue location (repo-relative, gitignored via data/)."""
    return cwd / "data" / "deferred"


def summarize_result(result: DeferredResult) -> list[str]:
    """2〜4 行の要約を返す。step footer 直後の log 行として使う。"""
    return [
        f"[deferred] {result['request_id']} from '{result['source_step']}'",
        f"  exit_codes={result['exit_codes']} overall={result['overall_exit_code']}"
        f" duration={result['duration_sec']}s",
        f"  stdout={result['stdout_bytes']}B ({result['stdout_path']})",
        f"  stderr={result['stderr_bytes']}B ({result['stderr_path']})",
    ]
