"""Desktop notification helpers (toast on Windows, beep fallback)."""

from __future__ import annotations

import subprocess


def notify_completion(title: str, message: str) -> None:
    """Send desktop notification. Falls back to beep on failure."""
    try:
        _notify_toast(title, message)
    except Exception:
        _notify_beep(title, message)


def _notify_toast(title: str, message: str) -> None:
    """Windows toast notification via PowerShell."""
    safe_title = title.replace("'", "''")
    safe_message = message.replace("'", "''")
    script = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
        "$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
        "$text = $template.GetElementsByTagName('text'); "
        f"$text[0].AppendChild($template.CreateTextNode('{safe_title}')) | Out-Null; "
        f"$text[1].AppendChild($template.CreateTextNode('{safe_message}')) | Out-Null; "
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Claude Workflow').Show($toast)"
    )
    result = subprocess.run(
        ["powershell", "-Command", script],
        capture_output=True, check=False, timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError("Toast notification failed")


def _notify_beep(title: str, message: str) -> None:
    """Fallback: beep + console output."""
    print("\a")
    print(f"\n{'=' * 40}")
    print(f"  {title}")
    print(f"  {message}")
    print(f"{'=' * 40}\n")
