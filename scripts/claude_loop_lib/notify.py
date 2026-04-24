"""Desktop notification helpers (toast on Windows, beep fallback).

`notify_completion` receives a `RunSummary` describing the entire workflow run
and emits one Windows toast (with a beep + console fallback on failure).
The toast XML aims for "stays until the user dismisses it" behaviour by using
`scenario='reminder'` + an explicit dismiss action; if that XML is rejected by
the OS a simpler `duration='long'` variant is retried before giving up.
"""

from __future__ import annotations

import subprocess
from xml.sax.saxutils import escape as _xml_escape

from claude_loop_lib.logging_utils import format_duration


RESULT_SUCCESS = "success"
RESULT_FAILED = "failed"
RESULT_INTERRUPTED = "interrupted"


class RunSummary:
    """Immutable-ish summary of a single workflow run, passed to notify_completion.

    `workflow_label` is a free-form identifier (e.g. ``"claude_loop_full"`` or
    ``"auto(full)"``). ``result`` is one of ``"success" / "failed" / "interrupted"``.
    """

    def __init__(
        self,
        workflow_label: str,
        result: str,
        duration_seconds: float,
        loops_completed: int,
        steps_completed: int,
        exit_code: int | None = None,
        failed_step: str | None = None,
        interrupt_reason: str | None = None,
    ) -> None:
        self.workflow_label = workflow_label
        self.result = result
        self.duration_seconds = duration_seconds
        self.loops_completed = loops_completed
        self.steps_completed = steps_completed
        self.exit_code = exit_code
        self.failed_step = failed_step
        self.interrupt_reason = interrupt_reason

    def title(self) -> str:
        if self.result == RESULT_SUCCESS:
            return "Workflow Complete"
        if self.result == RESULT_INTERRUPTED:
            return "Workflow Interrupted"
        return "Workflow Failed"

    def message(self) -> str:
        loops = self.loops_completed
        steps = self.steps_completed
        loops_word = "loop" if loops == 1 else "loops"
        steps_word = "step" if steps == 1 else "steps"
        duration = format_duration(self.duration_seconds)
        tail = f"{self.workflow_label} / {loops} {loops_word} / {steps} {steps_word} / {duration}"

        if self.result == RESULT_SUCCESS:
            return tail
        if self.result == RESULT_INTERRUPTED:
            reason = self.interrupt_reason or "interrupted"
            head = f"interrupted ({reason})"
            if self.failed_step:
                head = f"{head} at {self.failed_step}"
            return f"{head} / {tail}"
        # failed
        head = "failed"
        if self.failed_step:
            head = f"{head} at {self.failed_step}"
        if self.exit_code is not None:
            head = f"{head} (exit {self.exit_code})"
        return f"{head} / {tail}"


def notify_completion(summary: RunSummary) -> None:
    """Send desktop notification. Falls back to beep on failure."""
    title = summary.title()
    message = summary.message()
    try:
        _notify_toast(title, message)
    except Exception:
        _notify_beep(title, message)


def _build_toast_xml(title: str, message: str, *, persistent: bool) -> str:
    """Build a toast XML payload.

    ``persistent=True`` uses ``scenario='reminder'`` plus an explicit dismiss
    action (Windows keeps the notification in Action Center until the user
    interacts). ``persistent=False`` falls back to ``duration='long'`` only,
    which is accepted by older Windows builds that reject `reminder` scenario
    without the required full shape.
    """
    # Escape body text (title/message) and include ", ' escapes for attribute safety
    safe_title = _xml_escape(title, {'"': "&quot;", "'": "&apos;"})
    safe_message = _xml_escape(message, {'"': "&quot;", "'": "&apos;"})
    if persistent:
        return (
            "<toast scenario='reminder' duration='long'>"
            "<visual>"
            "<binding template='ToastGeneric'>"
            f"<text>{safe_title}</text>"
            f"<text>{safe_message}</text>"
            "</binding>"
            "</visual>"
            "<actions>"
            "<action content='閉じる' arguments='dismiss' activationType='system'/>"
            "</actions>"
            "</toast>"
        )
    return (
        "<toast duration='long'>"
        "<visual>"
        "<binding template='ToastGeneric'>"
        f"<text>{safe_title}</text>"
        f"<text>{safe_message}</text>"
        "</binding>"
        "</visual>"
        "</toast>"
    )


def _toast_powershell_script(xml: str) -> str:
    """Wrap a toast XML payload in a PowerShell invocation script."""
    # XML is built with single quotes only, so it is safe to embed inside a
    # PowerShell double-quoted here-string-free literal by escaping the XML's
    # `'` against PS by doubling (PowerShell rule for single-quoted strings).
    safe_xml = xml.replace("'", "''")
    return (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
        "$xml = New-Object Windows.Data.Xml.Dom.XmlDocument; "
        f"$xml.LoadXml('{safe_xml}'); "
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); "
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Claude Workflow').Show($toast)"
    )


def _run_powershell(script: str) -> int:
    """Invoke powershell with the given script; return exit code."""
    result = subprocess.run(
        ["powershell", "-Command", script],
        capture_output=True, check=False, timeout=10,
    )
    return result.returncode


def _notify_toast(title: str, message: str) -> None:
    """Windows toast notification via PowerShell.

    Tries the persistent (``reminder``) XML first and falls back to the
    ``duration='long'`` variant if the OS rejects the richer XML.
    """
    for persistent in (True, False):
        xml = _build_toast_xml(title, message, persistent=persistent)
        script = _toast_powershell_script(xml)
        rc = _run_powershell(script)
        if rc == 0:
            return
    raise RuntimeError("Toast notification failed")


def _notify_beep(title: str, message: str) -> None:
    """Fallback: beep + console output."""
    print("\a")
    print(f"\n{'=' * 40}")
    print(f"  {title}")
    print(f"  {message}")
    print(f"{'=' * 40}\n")
