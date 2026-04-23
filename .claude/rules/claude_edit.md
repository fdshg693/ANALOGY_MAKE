---
paths:
  - ".claude/**/*"
---

Files under `.claude/` cannot be directly edited in CLI `-p` mode (security restriction).
To edit files in `.claude/`, use `scripts/claude_sync.py` with the following steps:

1. `python scripts/claude_sync.py export` — Copy `.claude/` to `.claude_sync/`
2. Edit the corresponding files in `.claude_sync/` (this directory is writable)
3. `python scripts/claude_sync.py import` — Write back `.claude_sync/` contents to `.claude/`

**Note**: Run export/import via the Bash tool with `python scripts/claude_sync.py <command>`.