---
workflow: research
source: imple_plan
---

# ver16.2 MEMO — PHASE8.0 §3 token/cost 計測 実装メモ

## 実装内容サマリ

- 新規: `scripts/claude_loop_lib/costs.py` — `StepCost` / `RunCostSummary` TypedDict、`parse_cli_result` / `extract_usage` / `calculate_cost_from_price_book` / `build_step_cost_from_cli_output` / `aggregate_run` / `write_sidecar` / `detect_claude_code_cli_version`、fallback 用 `PRICE_BOOK_USD_PER_MTOK`（2026-04-24 公式 pricing page 値）
- 新規: `scripts/tests/test_costs.py` — 21 ケース（parse / calc / build / aggregate / sidecar / fallback / 欠測）
- 変更: `scripts/claude_loop_lib/logging_utils.py` — `TeeWriter.write_process_output_capturing` / `format_step_cost_line` / `format_run_cost_footer` 追加（既存関数は unchanged）
- 変更: `scripts/tests/test_logging_utils.py` — cost formatter 5 ケース追加
- 変更: `scripts/claude_loop_lib/commands.py` — `build_command` に `output_format_json` 引数追加（既定 False、既存呼び出しは影響なし）
- 変更: `scripts/claude_loop.py` — `_execute_single_step` は `(exit_code, prev_commit, captured)` を返すよう拡張、`_process_deferred` は `DeferredOutcome` TypedDict を返すよう拡張、`_run_steps` に cost 収集ロジックと run 末尾 sidecar 書き出しを追加
- ドキュメント: `scripts/README.md` に「cost 計測」節、`scripts/USAGE.md` のログフォーマットに cost 行を追記
- 進捗: `docs/util/MASTER_PLAN/PHASE8.0.md` §3 を「✅ 実装済み（ver16.2、2026-04-24）」に更新

## 計画との乖離・判断

- **IMPLEMENT §1-1 の primary 戦略を RESEARCH §結論 Q3 に従い「`total_cost_usd` raw 記録」に変更**済。PRICE_BOOK は fallback 用途のみ残し、`cost_source` フィールドで `"cli"` / `"fallback_price_book"` を区別できるようにした
- **IMPLEMENT §1-3 の `_process_deferred` call boundary**: plan では「signature を変更せず resume subprocess の captured_output を追加で返す」と記載。実装では signature 変更は最小限に抑えるため `DeferredOutcome` TypedDict を戻り値型として導入（external_results / resume_* を束ねる）。呼び出し側は `resume_code = deferred_outcome["resume_code"]` で従来と同等の情報にアクセス可
- **IMPLEMENT §1-5 の validation ルール**: 「`command.args` に `--output-format` 混入をエラー化」は **本版では実装していない**（tee 非活性時は `--output-format json` を付与しないため、YAML 側で step 別に付けたくなるケースは現状発生しない。二重付与ガードは将来 CLI からの報告を見てから追加する方が安全と判断）
- **cost_tracking の有効化条件**: tee is None（= `--no-log` / `--dry-run`）のときは cost_tracking を無効化し、`--output-format json` も付与しない。これにより live streaming を維持したい場面（`--no-log` での手元 smoke 実行）では既存挙動を変えない

## リスク・不確実性（IMPLEMENT.md §0 / EXPERIMENT.md §判断 に対する対応）

### R1 `--output-format json` の live stdout サイレント化（EXPERIMENT §U6-a 未検証）

- **対応**: 検証済み扱いではなく **検証先送り（本番 run で観察）**。RESEARCH §結論 Q5 / §U6-a 推奨どおり A 案（json single-shot）を primary 採用
- **本番発生時の兆候**: 本版実装後の初回 log run で `--- stdout/stderr ---` と `--- end (exit: ...) ---` のあいだに何も出力されない（step 終了時に JSON 1 行がまとめて出る）
- **影響範囲**: log ファイルの可読性が step 途中で失われる。live で Claude の思考を追跡したい場合は `--no-log` を選ぶ
- **対応方針**: 運用上耐えがたいと判明したら次版で B 案（`stream-json`）に切替える。その場合は `tee.write_process_output_capturing` を「各 event を 1 行 tee + `type=="result"` event だけ buffer」に拡張する
- **ISSUE 起票**: 本版で実装後の初回 run 結果が出てから判断するため、MEMO で保留し retrospective で再評価

### R2 `SDKResultMessage` 型との実機突合未検証（EXPERIMENT §U1-a / §U1-b 未検証）

- **対応**: RESEARCH §結論 Q1 の TS 型定義（B1–B10）を信用して実装。本番 run の costs.json で実際の key 名 / 型が RESEARCH 想定と一致するか retrospective で突合する
- **本番発生時の兆候**: `costs.json` 内 step が全て `status="unavailable"` / `reason="non-json-output"` になる（= JSON が parse できなかった）、あるいは `total_cost_usd` が欠けて `cost_source="fallback_price_book"` 一色になる
- **影響範囲**: cost 計測が機能しない。本筋の workflow 実行自体には影響しない（`status="unavailable"` を入れて続行する設計）
- **対応方針**: retrospective で乖離が判明したら ver16.3 で `parse_cli_result` / `extract_usage` を修正。必要なら `experiments/cost-usage-capture/{slug}/README.md` の再開手順を元に手動 sample 採取
- **ISSUE 起票**: **先送り**。本版実装後の最初の run で自然にサンプルが取れるため、専用 ISSUE を用意するより retrospective で突合した方が実務的

### R3 PRICE_BOOK の drift（価格表更新タイミング）

- **対応**: primary 経路（`total_cost_usd`）を使う限り、本 repo の PRICE_BOOK drift は fallback 経路のみ影響する。primary 経路が機能している限り retrospective 集計に直接影響しない
- **本番発生時の兆候**: CLI が古いモデルを使っている場合 / `modelUsage` が欠落した step で fallback が動き、Anthropic 公式 pricing page との乖離が発生する
- **影響範囲**: fallback 経路を通った step の `cost_usd` のみ誤差（primary 経路は CLI 側の価格表で算出される）
- **対応方針**: pricing page 更新時に `PRICE_BOOK_USD_PER_MTOK` と `PRICE_BOOK_SOURCE` の 2 箇所を同時更新（README.md の cost 節に記載）
- **ISSUE 起票**: **不要**（fallback の精度は retrospective で十分な精度。運用上 primary 経路が常用される想定）

### R4 deferred execution での cost 分離（IMPLEMENT §0 U3）

- **対応**: 実装済み。`kind="claude" | "deferred_resume" | "deferred_external"` の 3 値で個別 record、external は `cost_usd=0.0`
- **検証状況**: deferred execution の本番実行機会が本版 §3 完走後の run で発生するため実機検証は retrospective 待ち
- **本番発生時の兆候**: costs.json の `steps[]` に `kind != "claude"` の record が出現しない / `resume_code != 0` で record が欠落する等
- **ISSUE 起票**: **不要**（既存の ISSUES/util/medium/deferred-resume-twice-verification.md と同じ実機観察 queue に合流させる）

### R5 YAML 同期契約（PLAN_HANDOFF §4 / IMPLEMENT §3）

- **対応**: 本版では **YAML 同期は発生しない**。`--output-format json` の付与は `build_command` 内で hardcode したため、`command.args` / `defaults` / `steps[]` に新キーを増やしていない。6 YAML の `command` / `defaults` / `steps` の公開キーは不変
- **リスク**: 将来 step 単位で `output_format` を切り替えたくなった場合のみ、6 YAML 同期か生成元 1 箇所化の判断が再浮上する
- **ISSUE 起票**: **不要**

## 後続バージョンへの引き継ぎ

1. **初回 log run の retrospective 突合**: `--workflow quick` / `--workflow full` を log 有効で 1 回走らせ、生成された `logs/workflow/*.costs.json` を観察:
   - `modelUsage` の key 名（RESEARCH 想定: `claude-opus-4-7` kebab-case 一致するか）
   - `cost_source` が `"cli"` 多数 / `"fallback_price_book"` 少数の比率
   - `status="unavailable"` step が大量発生していないか
2. **Live streaming 体験の評価**: json single-shot モードでログ可読性が運用上耐えがたいと判明したら、ver16.3 以降で `stream-json` 経路への切替を計画
3. **`experiments/cost-usage-capture/` の扱い**: `/experiment_test` が残した README 草稿は本版完走後の最初の本番 run で自然に裏取りが進むため、retrospective 結果次第で削除可否を判断
4. **`.claude/rules/scripts.md` の cost log 仕様 stable 化**: 本版で実装経路が固まり retrospective で大筋問題ないと確認できたら、`scripts/README.md` 側の「cost 計測」節を rule に昇格させる判断を次版で実施（PLAN_HANDOFF §1-11）

## 更新候補ドキュメント（`write_current` / retrospective で処理）

- `docs/util/ver16.0/CURRENT_scripts.md` — `claude_loop_lib/` モジュール一覧に `costs.py` を追加、`claude_loop.py` の step footer / run footer に cost 行が追加された旨を反映
- `docs/util/ver16.2/CHANGES.md` — 本版の差分（ver16.1 → ver16.2）を /write_current フローで生成

## テスト結果

- `python -m unittest scripts.tests.test_costs` → 21 tests OK
- `python -m unittest scripts.tests.test_logging_utils` → 19 tests OK（既存 14 + 新規 5）
- `python -m unittest scripts.tests.test_{commands,deferred_commands,claude_loop_integration,claude_loop_cli,feedbacks,frontmatter,git_utils,issue_worklist,issues,notify,question_worklist,questions,validation,workflow}` → 322 tests 総計 OK（regression なし）
- `npx nuxi typecheck` — vue-router volar の既知警告のみ（CLAUDE.md 記載、本変更と無関係）
- smoke: `python scripts/claude_loop.py --dry-run -w quick` は既存挙動と同じ（cost tracking は tee=None のため無効）

## wrap_up 対応結果（2026-04-24）

plan_review_agent による確認済み。

| リスク | 判定 | 内容 |
|---|---|---|
| R1 live サイレント | ⏭️ 対応不要 | 初回 run 結果が出てから判断。retrospective で観察、問題あれば ver16.3 で B 案（stream-json）に切替 |
| R2 実機突合未検証 | ⏭️ 対応不要 | 本番 run の costs.json で自然に裏取り。retrospective で突合し乖離があれば ver16.3 で修正 |
| R3 PRICE_BOOK drift | ✅ 対応完了 | fallback 経路のみ影響。primary（total_cost_usd）が機能する限り許容範囲 |
| R4 deferred cost 分離 | ✅ 対応完了 | 実装済み（3 kind 別 record）。実機検証は retrospective 待ち |
| R5 YAML 同期契約 | ✅ 対応完了 | build_command 内 hardcode のため 6 YAML 変更なし |

ISSUES 整理:
- 新規起票: なし（R1/R2 とも retrospective 後まで保留が適切との判断）
- 既存 ISSUE 変更: なし（deferred-resume-twice-verification は ver16.2 対象外）
- 削除: なし（ver16.2 の対応で解決済み ISSUE なし）

コミット: `docs(ver16.2): wrap_up完了`（MEMO.md の対応結果追記のみ）
