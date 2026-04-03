#!/bin/bash
# Install staged skill improvements from _staged_skills/ to .claude/skills/
# Run: bash _staged_skills/install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Skill Improvements Installer ==="
echo ""

# 1. imple_plan/SKILL.md
SRC="$SCRIPT_DIR/imple_plan_SKILL.md"
DEST="$PROJECT_DIR/.claude/skills/imple_plan/SKILL.md"

if [ -f "$SRC" ]; then
    echo "Updating: .claude/skills/imple_plan/SKILL.md"
    echo "  Changes: category-aware build commands + .claude/ protection note"
    cp "$SRC" "$DEST"
    echo "  Done."
else
    echo "SKIP: $SRC not found"
fi

echo ""
echo "=== Installation complete ==="
echo "You can now delete the _staged_skills/ directory:"
echo "  rm -rf _staged_skills/"
