---
status: ready
assigned: ai
priority: low
reviewed_at: "2026-04-25"
---

# costs.py `extract_model_name` を「最大 cost の model」ベースに修正

## 概要

`scripts/claude_loop_lib/costs.py::extract_model_name` は現在 `modelUsage` dict の**最初の key** を返すため、primary model ではない model（sub-tool が一瞬だけ呼ぶ haiku 等）が sidecar `model` フィールドに記録されてしまう。`modelUsage` 内で `costUSD` が最大の key を返すよう修正する。

## 背景（ver16.3 RETROSPECTIVE §3.5 A-6 で発見）

ver16.3 run `logs/workflow/20260424_231449_claude_loop_issue_plan.costs.json` で以下の乖離を観測した:

- sidecar 記録: `model: "claude-haiku-4-5-20251001"`
- 実コスト内訳:
  - `claude-opus-4-7`: $2.1728（99.98%）
  - `claude-haiku-4-5-20251001`: $0.00041（0.02%）

ログサマリも同様にミスリーディングな表示となる:

```
Cost: $2.1732 (... model: claude-haiku-4-5-20251001)
```

**原因**: `extract_model_name`（`costs.py` L149-156）が Python dict の挿入順に依存して最初の key を返す実装。CLI が haiku を先に挿入すると、実コスト上は opus が primary でも haiku が「代表 model」として拾われる。

**影響度**: 低（cost 総額・token 集計は正確、`modelUsage` 生データも完全保存されている）。ただし retrospective で「どの step でどの model を使ったか」を sidecar の `model` から素早く読む運用が成立しないため、表示目的の品質問題として修正する価値がある。

## 再現手順

1. `claude_loop.py` を `full` / `quick` いずれかの workflow で起動し、少なくとも 1 step で opus を primary、haiku を sub-tool で短時間呼ぶような実行を行う
2. 生成された `logs/workflow/*.costs.json` の `steps[].model` を確認する
3. 実 `cost_usd` 内訳（同 JSON の `modelUsage` または log 内 JSON）と突合し、`model` が最大 cost 側を指しているか確認する

## 期待動作

`extract_model_name(result)` が `result["modelUsage"]` 内で `costUSD` 値が最大の key を返す。

- `modelUsage` が空 dict / 非 dict / 欠落 → 現状どおり `None` を返す
- `modelUsage` に含まれる key が 1 つだけ → その key を返す
- 全 entry の `costUSD` が 0 / 欠落 / 非数値 → フォールバック規則を明示（例: 先頭 key を返す、または `None`）
- 同値並びの場合の挙動も明示（例: `max()` の自然な挙動に任せる）

## 影響範囲

- `scripts/claude_loop_lib/costs.py::extract_model_name` — 本体修正（5〜10 行）
- `scripts/tests/test_costs.py::TestExtractModelName` — 既存 2 テストのうち `test_picks_first_model_key` を「最大 cost の model を返す」趣旨に変更、空 / 単一 key / 同値時のエッジケース 2〜3 本を追加
- `scripts/claude_loop_lib/costs.py` 冒頭 docstring / 該当関数 docstring（「first key」表現の訂正）

`costs.py` を import している他箇所（`claude_loop.py` の sidecar 書き出し / ログ出力経路）は `extract_model_name` の戻り値の仕様（`str | None`）に変化がないため追加変更不要。

## やらないこと

- `modelUsage` に `inputTokens` / `outputTokens` など多次元情報を合算して重み付きスコアを出すような高度化は行わない（`costUSD` 最大で十分、実装も 1 行で済む）
- `model` フィールドに複数 model を記録する拡張（`primary_model` / `all_models` 等への分割）は本 ISSUE のスコープ外
- フォールバック経路（`total_cost_usd` 欠落時）の振る舞い変更は本 ISSUE のスコープ外

## 関連資料

- `docs/util/ver16.3/RETROSPECTIVE.md` §3.5 A-6（原ソース）
- `FEEDBACKS/handoff_ver16.3_to_next.md`（ver16.4 主眼候補 #1 で言及）
- `scripts/claude_loop_lib/costs.py` L149-156（対象関数）
- `scripts/tests/test_costs.py::TestExtractModelName`（対象テスト）
