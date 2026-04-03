#!/usr/bin/env python3
"""PermissionRequest hook handler.

Auto-allows all permission requests except AskUserQuestion.
AskUserQuestion は自動許可せず、通常のパーミッションダイアログを表示させる。
"""
import json
import sys


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # JSON パース失敗時は何もせず終了（通常のダイアログを表示）
        sys.exit(0)

    tool_name = data.get("tool_name", "")

    # AskUserQuestion は自動許可しない → ユーザーが回答できるようにする
    if tool_name == "AskUserQuestion":
        sys.exit(0)

    # それ以外のツールは自動許可
    result = {
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {
                "behavior": "allow"
            }
        }
    }
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
