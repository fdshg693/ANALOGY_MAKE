---
step: issue_plan
---

## 背景

ver16.3 で PHASE8.0 完走後の初の minor を実施し、`/retrospective §3.5 相当` で cost tracking 初回本番突合を完了。判定結果: 6 観点中 5 観点 PASS、1 観点（A-6）で `scripts/claude_loop_lib/costs.py::extract_model_name` の軽微バグを検出。詳細は `docs/util/ver16.3/RETROSPECTIVE.md` §3.5。

## 次ループで試すこと

- **ver16.4 主眼候補（2 つ、どちらかを選ぶ or 並行）**:
  1. `extract_model_name` を「`modelUsage` 中 `costUSD` 最大の key を返す」実装に修正。現状は dict の最初の key を返すため、sub-tool が一瞬呼ぶだけの haiku が primary 表示される。**先に `ISSUES/util/low/costs-representative-model-by-max-cost.md` として正式起票してから着手**（次 `/issue_plan` で起票 → review → ready の流れを踏む）。修正は `extract_model_name` 5〜10 行 + テスト更新で済む minor スコープ
  2. 本版 §B で起票した `ISSUES/util/low/issue-review-long-carryover-redemotion.md`（`raw/ai`）を `review/ai` → `ready/ai` へ昇格判定し、可能なら `issue_review` SKILL 本体拡張の実装計画を書き始める
- **`deferred-resume-twice-verification` の様子見**: 次回 deferred 発火 run があれば A-4（kind 分離）の観察が進む。deferred 発火テストを兼ねた `research` workflow を選ぶ選択肢もあり（ver16.3 では `full` を選んだ）
- **imple_plan 実装量小ケースの effort 下げ**: ver16.3 の imple_plan は「ISSUE 1 件作成のみ」で opus-high が過剰だった兆候あり。次回 imple_plan スコープが 1〜2 ファイル編集以下に収まる見込みなら、SKILL 側で effort: medium / sonnet に下げる条件を追記する試行

## 保留事項

- **PHASE9.0 骨子作成**: 依然として時期尚早。PHASE8.0 周辺の仕上げ minor（costs.py バグ修正、issue_review SKILL 拡張）で当面吸収可能
- **`experiment_test` effort 下げ判断**: 2 サンプルのまま、次 `research` workflow で 3 サンプル目を採取してから判断
- **EXPERIMENT.md 「未検証」マーク解除**: ver16.2 EXPERIMENT の §U1-a / §U1-b / §U6-a は本 retrospective で検証完了扱い。次 `research` workflow 採用時に EXPERIMENT.md を物理的に更新する（ver16.3 では触らず）
- **A-5 (live stdout silent) は「C 案: json 一括で許容」で確定**: 再議論不要。次 run で再度重い無応答が運用に耐えない場合のみ再評価
- **quick + retrospective 混成 YAML の可否**: ver16.3 のような「観察 + 微小実装」ケースが次も発生したら、`claude_loop_quick.yaml` に retrospective step を追加できるか検討。今は 1 サンプルのみなので恒久化しない
