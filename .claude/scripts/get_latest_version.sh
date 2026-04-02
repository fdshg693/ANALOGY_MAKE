#!/bin/bash
CAT=$(cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app)
VER=$(ls -1d "docs/$CAT/ver"*/ 2>/dev/null | sed 's|.*/ver||;s|/||' | sort -n | tail -1)
echo "${VER:-0}"
