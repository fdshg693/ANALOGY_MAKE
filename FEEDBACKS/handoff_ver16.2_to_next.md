---
step: issue_plan
---

## 背景

ver16.2 で PHASE8.0 §3（token/cost 計測）を完走し、PHASE8.0 全 3 節（§1 research / §2 deferred / §3 cost）が揃った。ただし本 run は ver16.1 完走コミット（`80455c3`）の `claude_loop.py` process で起動したため **本版自体では cost tracking が動作していない**。次 run が cost tracking 付きの初回本番 run となり、ver16.2 RESEARCH / EXPERIMENT で先送りした検証事項（§U1-a / §U1-b / §U6-a / R1 / R2 / R4）がここで自然採取される。

## 次ループで試すこと

- **次バージョン種別の推奨: ver16.3（マイナー）**。PHASE8.0 完走直後だが、PHASE9.0 骨子作成は時期尚早。次ループは「cost tracking 実機突合」＋「既存 ready/ai 3 件のうち消化可能なものの triage」に絞る。
- **cost tracking 初回突合**: 次 run 終了後に `logs/workflow/{stem}.costs.json` を確認し、以下を RETROSPECTIVE §3.5 相当で突合する:
  - `modelUsage` の key 名が kebab-case Anthropic model ID か（ver16.2 §U1-b 仮説）
  - `total_cost_usd` が各 step で取れているか（`cost_source="cli"` 比率 vs `"fallback_price_book"` 比率）
  - `status="unavailable"` が大量発生していないか（実装 bug / 仕様乖離の signal）
  - `kind="deferred_resume"` / `"deferred_external"` の record が deferred 発火 run で出現するか
  - live stdout サイレント化（`--output-format json` 付与時の `--- stdout/stderr ---` 区間の空白度）が運用上耐えうるか
  - 耐えがたい場合は ver16.3 内で `stream-json`（B 案）への切替を検討
- **`deferred-resume-twice-verification.md`（`ready/ai`）**: cost tracking 実走時の deferred 発火経路で自然に実機観察が進む可能性あり。次ループの `/wrap_up` or `/retrospective` で所見を追記し、解消見込みがあればクローズ判断。
- **持ち越し ready/ai 4 件の扱い**: `issue-review-rewrite-verification` / `toast-persistence-verification` / `rules-paths-frontmatter-autoload-verification` / `scripts-readme-usage-boundary-clarification` は 5 バージョン連続持ち越し。`/issue_plan` SKILL の review フェーズは `ready/ai` を `need_human_action/human` に降格できない仕様のため、「長期持ち越し ready/ai の再判定手順」を `issue_review` SKILL 側に追加する ISSUE 起票を次ループで検討する。

## 保留事項

- **`experiment_test` effort 下げ判断**: ver16.2 は実走 1 件（§U7）のみで artifact 負荷軽く effort: high の必要性が低く見えたが、判断材料が 2 サンプルだけ。次回 `research` 採用時に effort: high → medium の試行を検討（本ループでは即変更せず観察継続）。
- **`research_context` / `experiment_test` の model 下げ**: 2 サンプル取得済だが、2 件とも artifact 構造が似通っており model 下げ判断には至らず。3 サンプル目まで据え置き。
- **`write_current` effort high の他 YAML 波及**: ver16.2 でも minor 回で high 維持の効果を確認（CHANGES.md 147 行 + 技術的判断 4 件）。ただし `claude_loop.yaml` / `claude_loop_quick.yaml` への波及可否は別議論で据え置き。
- **PHASE9.0 骨子作成**: 本版 RETROSPECTIVE §1 / §3 で「既存 ISSUES 消化優先、骨子は次ループ判断」と明示。次ループ `/issue_plan` で「cost 実機突合 + 既存 ISSUE 消化」を超えるテーマがあるか判断し、見つからなければ minor 継続。
