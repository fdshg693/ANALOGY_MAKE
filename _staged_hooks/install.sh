#!/bin/bash
# Install hook files to .claude/ directory
# Run from project root: bash _staged_hooks/install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Installing hooks to $PROJECT_DIR/.claude/..."

# Create hooks directory
mkdir -p "$PROJECT_DIR/.claude/hooks"

# Copy permission_handler.py
cp "$SCRIPT_DIR/permission_handler.py" "$PROJECT_DIR/.claude/hooks/permission_handler.py"
echo "  ✓ .claude/hooks/permission_handler.py"

# Backup current settings.local.json
if [ -f "$PROJECT_DIR/.claude/settings.local.json" ]; then
  cp "$PROJECT_DIR/.claude/settings.local.json" "$PROJECT_DIR/.claude/settings.local.json.bak"
  echo "  ✓ Backed up settings.local.json → settings.local.json.bak"
fi

# Copy new settings.local.json
cp "$SCRIPT_DIR/settings.local.json" "$PROJECT_DIR/.claude/settings.local.json"
echo "  ✓ .claude/settings.local.json"

echo ""
echo "Done! You can remove _staged_hooks/ after verifying."
echo "  rm -rf _staged_hooks/"
