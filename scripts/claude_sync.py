"""
.claude <-> .claude_sync 同期スクリプト

使い方:
  python scripts/claude_sync.py export   # .claude -> .claude_sync にコピー
  python scripts/claude_sync.py import   # .claude_sync -> .claude に反映
"""

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / ".claude"
CPY_DIR = REPO_ROOT / ".claude_sync"


def export_claude() -> None:
    """`.claude` の内容を `.claude_sync` に完全コピーする。"""
    if CPY_DIR.exists():
        shutil.rmtree(CPY_DIR)
        print(f"既存の {CPY_DIR.name}/ を削除しました")

    shutil.copytree(SRC_DIR, CPY_DIR)
    print(f"{SRC_DIR.name}/ -> {CPY_DIR.name}/ にコピーしました")


def import_claude() -> None:
    """`.claude_sync` の内容を `.claude` に反映する。"""
    if not CPY_DIR.exists():
        print(f"エラー: {CPY_DIR.name}/ が存在しません。先に export を実行してください。", file=sys.stderr)
        sys.exit(1)

    # .claude の中身を削除して .claude_sync の内容で置き換える
    if SRC_DIR.exists():
        shutil.rmtree(SRC_DIR)
    shutil.copytree(CPY_DIR, SRC_DIR)
    print(f"{CPY_DIR.name}/ -> {SRC_DIR.name}/ に反映しました")


def main() -> None:
    parser = argparse.ArgumentParser(description=".claude <-> .claude_sync 同期ツール")
    parser.add_argument(
        "command",
        choices=["export", "import"],
        help="export: .claude -> .claude_sync / import: .claude_sync -> .claude",
    )
    args = parser.parse_args()

    if args.command == "export":
        export_claude()
    elif args.command == "import":
        import_claude()


if __name__ == "__main__":
    main()
