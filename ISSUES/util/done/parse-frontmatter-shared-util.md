---
status: ready
assigned: ai
priority: low
reviewed_at: "2026-04-23"
---
# YAML frontmatter パース関数の共通化

## 概要

`scripts/issue_status.py` と `scripts/claude_loop_lib/feedbacks.py` の両方で、Markdown ファイル先頭の YAML frontmatter を独立してパースしている。共通関数 `parse_frontmatter(text: str) -> dict | None` を切り出すことで DRY 化できる。

## 対応方針

- `scripts/claude_loop_lib/` に `frontmatter.py`（または既存ファイルへの追加）を作成
- `parse_frontmatter(text: str) -> dict | None` を実装（frontmatter 無し / パース失敗は `None` を返す）
- `issue_status.py` と `feedbacks.py` からインポートするよう修正

## 影響範囲

- `scripts/issue_status.py`
- `scripts/claude_loop_lib/feedbacks.py`
- 新規 `scripts/claude_loop_lib/frontmatter.py`（または既存ファイル）

## 優先度

低。現状の重複は 20 行程度で実害は小さく、バグも発生していない。
