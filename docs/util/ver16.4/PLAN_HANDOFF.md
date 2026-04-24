---
workflow: quick
source: issues
---

# ver16.4 PLAN_HANDOFF — 後続 step 引き継ぎ

`quick` workflow の PLAN_HANDOFF は必須 2 節（関連 ISSUE / 関連ファイル + 後続 step への注意点）で運用する。ISSUE レビュー結果・状態サマリ・選定理由は `ROUGH_PLAN.md` 側に統合済み（quick では分離しない）。

## 関連 ISSUE / 関連ファイル

### 選定 ISSUE（ver16.4 の主眼）

- `ISSUES/util/low/costs-representative-model-by-max-cost.md` — 本 `/issue_plan` で新規起票し review → ready に昇格。ver16.3 RETROSPECTIVE §3.5 A-6 を原ソースとする

### 並行昇格させたが本版で着手しない ISSUE

- `ISSUES/util/low/issue-review-long-carryover-redemotion.md` — `raw/ai → ready/ai` に昇格のみ。SKILL 本体拡張の実装は ver16.5 以降に委ねる（handoff 候補 #2 は本版では取り上げない判断）

### 修正対象ファイル

- `scripts/claude_loop_lib/costs.py`
  - `extract_model_name`（L149-156）: 実装本体の書き換え
  - 該当関数の docstring: 「first key」という記述を「最大 `costUSD` の key」に更新
- `scripts/tests/test_costs.py`
  - `TestExtractModelName::test_picks_first_model_key`（L109-111）: 名前・内容とも差し替え
  - `TestExtractModelName::test_returns_none_when_absent`（L113-114）: そのまま維持
  - 追加テスト 2〜3 本: 空 `modelUsage` / 単一 key / 同値並び / `costUSD` 欠落 のエッジケース

### 参考資料（読み直す価値あり）

- `docs/util/ver16.3/RETROSPECTIVE.md` §3.5 A-6（バグ発見の一次記録、修正根拠）
- `FEEDBACKS/handoff_ver16.3_to_next.md` — ver16.4 主眼候補 #1 / #2 の分岐理由
- `docs/util/ver16.2/RESEARCH.md` §U1-a / §U1-b（`modelUsage` の key 名仕様の根拠）

### 前提条件

- `scripts/tests/test_costs.py` の既存 26 test は ver16.3 時点で全 PASS。本修正で増減するのは `TestExtractModelName` 周辺のみで、他 test クラスには影響を与えない想定
- `costs.py` を import している側（`claude_loop.py` の sidecar 書き出し経路）は `extract_model_name` の戻り値型 `str | None` が不変のため追加変更不要

## 後続 step への注意点

### `/quick_impl` への注意

1. **`modelUsage` の `costUSD` key 名は確定済み**: ver16.3 実機観測で `modelUsage[model][costUSD]` 形式（camelCase）を確認済（`docs/util/ver16.3/RETROSPECTIVE.md` §3.5 A-1 と紐づく A-6 の分析）。`cost_usd` / `cost` 等の snake_case 表記で書かない
2. **エッジケースの想定挙動を明示的に docstring へ**:
   - `modelUsage` が空 dict / 非 dict / 欠落 → `None`
   - 全 entry の `costUSD` が 0 / 欠落 / 非数値 → フォールバック規則（最初に現れた key を返す、または `None`）を関数コメントで固定
   - 同値並び → `max()` の挙動（最初に現れた最大値）に任せる旨を明記
3. **テスト追加の最低セット**（ISSUE 本文より抽出）:
   - 通常ケース: 2 model で `costUSD` 差あり → 最大側の key を返す
   - 単一 key: 現状どおり唯一の key を返す
   - 空 dict / `modelUsage` 欠落: `None` を返す（既存テスト維持で足りる）
   - `costUSD` 欠落 or 非数値: フォールバック挙動を 1 本で確認
4. **スタイル規則**: `.claude/rules/scripts.md` 準拠。PEP 604 型ヒント（`str | None`）・`pathlib.Path`・標準ライブラリのみ。本修正は型ヒント変更なしだが、新規テストのヘルパーを書く場合も同規則を守る
5. **手動動作確認は不要**: CLI 実走での sidecar 再確認は `/quick_impl` 内で必須化しない。次回 `research` / `full` workflow 運用時に自然採取される `logs/workflow/*.costs.json` で副次的に検証されれば十分（handoff: ver16.5 以降で観察）

### `/quick_doc` への注意

- `CHANGES.md` 冒頭に記録すべき差分:
  - `costs.py` 1 関数の挙動変更（`model` フィールド: 先頭 key → 最大 cost の key）
  - 新規 ISSUE 1 件追加 + 既存 1 件昇格（ISSUE 状態サマリ `ready/ai=3 → 5`, `raw/ai=3 → 2`）
  - テスト差分（2 テスト修正 + 2〜3 テスト追加、合計数は `/quick_impl` 結果で確定）
- `MASTER_PLAN.md` の PHASE8.0 サマリ行は触らない（本修正は PHASE8.0 完了後の仕上げ minor であり、サマリ上の表現「実装済み（全 3 節完了）」は維持）
- `CURRENT.md` は minor につき作成しない

### 後続版（ver16.5 以降）への引き継ぎ候補

- `issue-review-long-carryover-redemotion` の SKILL 拡張実装 — `ready/ai` に昇格済、次 minor の主眼候補
- ver16.3 §3.5 A-4（deferred 3 kind 分離）の実機観察 — 本版は deferred 発火なし見込み、次 deferred 発火 run 以降で継続
- `imple_plan` / `experiment_test` の effort 下げ判断 — 引き続き sample 蓄積待ち（quick では `imple_plan` step なし、次 full run で再評価）
- ver16.2 EXPERIMENT.md 「未検証」マーク解除の物理更新 — 次 `research` workflow 採用時に実施
