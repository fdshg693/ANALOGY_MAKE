---
step: issue_plan
---

## 背景

ver16.5 で `issue_review` SKILL §1.5 / §5 第 3 ブロック（`ready/ai` 長期持ち越し再判定推奨ルート）を導入した。本版 retrospective 時点では util カテゴリ ready/ai 5 件のすべてが `reviewed_at < 7 日` のため §1.5 発火なし。次ループ `/issue_plan` が本機能の**初回実走**となる。

また、wrap_up で観察 ISSUE を 2 件起票（F-1 閾値妥当性 / F-3 LLM 日付計算確認）。ready/ai は 4→5 件に増加。

## 次ループで試すこと

1. **F-3 消化**: 次 `/issue_plan` 実行時、ROUGH_PLAN.md に `## 再判定推奨 ISSUE` ブロックが正しい書式（ゼロ件でも「該当なし」1 行）で出力されているか目視確認する。書式崩れがなければ `ISSUES/util/low/issue-review-llm-date-calc-observation.md` を done/ へ移動して消化（次版 retrospective で実行）
2. **imple_plan effort 下げ試行**: ver16.3 §8 / ver16.5 §8 で「実装量小ケースの opus-high は過剰」が 2 サンプル目。次ループで実装量が小（`/split_plan` 生成 IMPLEMENT.md が ~100 行以下 & 編集対象 3 ファイル以下）と判定された場合のみ、`claude_loop.yaml` の `imple_plan` step を `effort: medium` で 1 回試行する。品質差が実用上問題なければ SKILL / YAML 恒久変更を ver16.7 以降で判断
3. **ver16.5 版主眼効果の副次観察**: `/issue_plan` 実行後の util ready/ai 件数が §1.5 判定結果（該当なし予想）と整合しているかを PLAN_HANDOFF に記録する

## 保留事項

- **F-1 閾値妥当性**: 自然な時間経過でのみ採取可能。最早発火予測は 2026-04-30 頃（`issue-review-rewrite-verification` の `reviewed_at: 2026-04-23` が 7 日経過）。ver16.7〜16.8 で観察予定、それまで handoff し続ける必要はない
- **ver16.5 §3.5 の「version bump 速度ギャップ」観察**: F-1 発火時にこの視点（実経過日数 vs version 番号の乖離）も併せて記録する予定。次ループでは不要
- **`raw/ai` 2 件の triage 停滞**: `rules-paths-frontmatter-autoload-verification` / `scripts-readme-usage-boundary-clarification` は ver16.3 以降、`raw → review` 昇格ルートが機能せず据え置きが続いている。次ループでも同判定の可能性が高いが、3 ループ連続で停滞した場合（ver16.7 到達時点）は「raw/ai 長期停滞向け review 昇格ルート」整備を ver16.7+ で検討する（本版と同型の meta 改善）
- **deferred 3 kind 分離**（ver16.3 A-4）: 継続観察、次 deferred 発火 run まで handoff 不要
- **ver16.2 EXPERIMENT.md 「未検証」マーク解除**: 次 research workflow 採用時に回収、継続待機
