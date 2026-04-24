---
workflow: quick
---

# ver16.4 MEMO

## 残課題・引き継ぎ

特記事項なし。修正は計画通り `extract_model_name` 1 関数 + テスト更新のみで完結し、乖離は発生しなかった。

## 後続版（ver16.5 以降）への引き継ぎ

- `issue-review-long-carryover-redemotion`（ready/ai）の SKILL 拡張実装が次 minor の主眼候補
- ver16.3 §3.5 A-4（deferred 3 種分離）の実機観察は次 deferred 発火 run で継続
- `imple_plan` / `experiment_test` の effort 調整は sample 蓄積待ち（次 full run で再評価）
- ver16.2 EXPERIMENT.md 「未検証」マーク解除は次 research workflow 採用時に実施
- `extract_model_name` の修正が実 sidecar に反映されているかの副次確認は次回 full / quick run の `*.costs.json` で自然採取
