#!/usr/bin/env bash
# 何を確かめるためか: §U7 — `claude --version` の出力形式を採取し、
#                     ver16.2 `costs.py` の `RunCostSummary.claude_code_cli_version`
#                     フィールドで保持する文字列形式を確定する。
# いつ削除してよいか: ver16.2 (PHASE8.0 §3) 完走後、`costs.py` に version parse が
#                     取り込まれたら削除可。
set -euo pipefail
claude --version
