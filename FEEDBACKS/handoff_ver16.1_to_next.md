---
step: issue_plan
---

## 背景

ver16.1 で PHASE8.0 §2（deferred execution）を完走。PHASE8.0 は §3（token/cost 計測）のみ残存で、MASTER_PLAN で ver16.2 に明示割当済。本版の `research` workflow 初の self-apply は成功し、`research_context` / `experiment_test` / `imple_plan` の直列パイプ（未解決論点 → 調査 → 実験 → 実装）が実働することを確認した。

## 次ループで試すこと

- **PHASE8.0 §3（token/cost 計測）着手**: MASTER_PLAN で ver16.2 に割当済。`scripts/claude_loop_lib/costs.py` 新規・`logging_utils.py` 変更・`test_costs.py` 新規が中心
- **workflow 選定の判断**: §3 は基本 `full` workflow で十分だが、「Claude usage/billing API の取得経路が CLI output と 1 対 1 に紐づくか」は事前調査の価値あり。外部仕様確認が主要成果に影響する場合のみ `research` を採用。閾値判定は `/issue_plan` SKILL §選定条件に従い、判断根拠を `ROUGH_PLAN.md` に明示する
- **新規追加 ISSUE の扱い**: `ISSUES/util/medium/deferred-resume-twice-verification.md`（`raw/ai`）は ver16.2 の deferred 経路本番発動後に実機検証可能。§3 本体とは独立のため ver16.2 では **triage のみ実施（`ready/ai` 化）** して実走は後続に回す判断を推奨

## 保留事項

- **`write_current` effort high の他 YAML 波及**: ver16.1 では `claude_loop_research.yaml` のみ引上げ。ver16.2 で `claude_loop.yaml` / `claude_loop_quick.yaml` にも同調整を波及するかは、§3 完走後の `CHANGES.md` / `CURRENT_*.md` 生成品質を見て判断。**ver16.2 では保留**
- **YAML sync 契約の生成元 1 箇所化**: §3 で `command` / `defaults` に新キー（例: cost log 関連）を追加する場合は ver16.2 で優先度上げ。`effort` のみの調整なら sync 対象外のため据え置き
- **`research_context` / `experiment_test` の model 下げ**: 初走 1 サンプルで下げ判断は危険。ver16.2 で `research` を再採用した場合のみ差分観察する
- **持ち越し ISSUE 4 件**（`issue-review-rewrite-verification` / `toast-persistence-verification` / `rules-paths-frontmatter-autoload-verification` / `scripts-readme-usage-boundary-clarification`）: 本ループで 4 バージョン連続持ち越しに到達。ver16.2 で `need_human_action/human` への振り直しを検討する余地あり
