---
status: ready
assigned: ai
priority: low
reviewed_at: 2026-04-24
---

# PLAN_HANDOFF.md と ROUGH_PLAN.md の frontmatter drift 検出

## 概要

ver15.3 で `PLAN_HANDOFF.md` が新設された。frontmatter の `workflow:` / `source:` は `ROUGH_PLAN.md` と**同値で重複保持**する設計（one source of truth は `ROUGH_PLAN.md` 側）。現状は目視確認のみで、機械的な drift 検出は行っていない。

## 本番発生時の兆候

- `ROUGH_PLAN.md`: `workflow: full` だが `PLAN_HANDOFF.md`: `workflow: quick` などの乖離
- `--workflow auto` が `ROUGH_PLAN.md` 側を読むため runtime 影響は即時には出ないが、後続 step が `PLAN_HANDOFF.md` の frontmatter を参照するように拡張された場合に誤読が発生しうる

## 対応方針

1. ver15.4〜15.5 の 2 バージョンほど運用し、frontmatter 乖離の実発生率を観察
2. 発生率が非ゼロなら `scripts/claude_loop_lib/validation.py` の `validate_startup()` に軽量チェックを追加（`ROUGH_PLAN.md` と `PLAN_HANDOFF.md` の `workflow` / `source` を読んで不一致なら警告）
3. 発生率ゼロが続くなら本 ISSUE を `done/` へ移動（監視不要と判定）

## 影響範囲

- 後続 step が誤った workflow / source を参照する可能性（現状は runtime 影響なし）
- 運用者の目視負荷（乖離検出を人間に依存）

## 関連

- `docs/util/ver15.3/IMPLEMENT.md` §9 リスク表 3 行目、§8.3 validation.py 先送り結論
- `.claude/skills/issue_plan/SKILL.md` 「frontmatter は ... 同値で重複保持する」の記述
