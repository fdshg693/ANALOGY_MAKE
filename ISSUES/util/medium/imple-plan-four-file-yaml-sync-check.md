---
status: raw
assigned: ai
priority: medium
reviewed_at: "2026-04-24"
---

# /imple_plan・/quick_impl に 4 ファイル YAML 同期チェックを明記

## 症状

ワークフロー YAML は現在 4 ファイル（`scripts/claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` / `claude_loop_scout.yaml`）あり、`command` / `defaults` セクションは同一内容を保つ契約になっている（`.claude/rules/scripts.md` §3 / `scripts/USAGE.md` L137 で規定）。

しかし ver15.0 で scout YAML を追加した際、`scripts/README.md` / `scripts/USAGE.md` は 4 ファイル同期へ更新されたのに対し、`.claude/rules/scripts.md` §3 の「3 ファイル」記述だけが取り残された（ver15.0 `/retrospective` §4 で事後的に即時修正）。原因は「YAML ファイル増減時に rule 側の同期対象リストを更新する」明示的チェックが `/imple_plan` / `/quick_impl` SKILL 本文に存在しないため。

同様の漏れは、将来 5 ファイル目の YAML（例: PHASE7.1 §2 想定の `question` workflow YAML）を追加するときにも再発する。ver15.0 で発見された「4 ファイル同期契約の rule と docs のずれ」は `FEEDBACKS/done/handoff_ver15.0_to_next.md` §保留事項 2 で引き継がれたが、handoff は 1 回消費で `done/` 化されるため、ISSUE 化しないと次の YAML 増減時に忘れられる。

## 影響

- YAML 増減のたびに rule / docs のどちらかが取り残される（静かに rot する）
- rule は agents 注入のトリガーとなるため、食い違いは agents の行動規約に混乱をもたらす
- 発見は結局人間の目視に頼ることになり、ver15.0 のように事後修正で辻褄合わせになる

## なぜ今見る価値があるか

- PHASE7.1 §2（`QUESTIONS/` + `question` workflow 新設）が ver15.1 or ver15.2 で予定されており、新 YAML 追加の蓋然性が高い。§2 着手前に本チェックを仕込めば、手戻り（事後的な rule 更新漏れ）を予防できる
- handoff 経由でしか伝達されておらず、ISSUE 化されていないため放置リスクが高い（本 scout 起票の主目的）
- 対応範囲は SKILL 本文 1〜2 ファイル（`/imple_plan/SKILL.md` / `/quick_impl/SKILL.md`）への短い注意文追記程度で、3 ファイル / 100 行枠に収まる見込み

## 想定修正方向（任意）

1. `/imple_plan/SKILL.md` のチェックリスト相当箇所に「ワークフロー YAML を新規追加・削除した場合は `.claude/rules/scripts.md` §3 の同期対象リスト（現 4 ファイル）と `scripts/USAGE.md` L137 の記述、および既存 YAML 先頭コメントの相互参照を全て更新する」旨を追記
2. `/quick_impl/SKILL.md` にも同等の一文を追記（quick 経路でも YAML 変更が発生しうる前提）
3. ver15.1 smoke test で発見があれば本 ISSUE を `ready / ai` 昇格、なければそのまま PHASE7.1 §2 着手時に `ready` 昇格

## 参照

- `.claude/rules/scripts.md` §3（4 ファイル同期契約の一次資料）
- `scripts/USAGE.md` L137（docs 側の同期契約記述）
- `scripts/claude_loop.yaml` / `claude_loop_quick.yaml` / `claude_loop_issue_plan.yaml` / `claude_loop_scout.yaml` 先頭コメント（相互参照）
- `docs/util/ver15.0/RETROSPECTIVE.md` §2「4 ファイル同期契約の docs と rule のずれ」
- `FEEDBACKS/done/handoff_ver15.0_to_next.md` §保留事項 2（handoff 経由で 1 回だけ伝達済）
