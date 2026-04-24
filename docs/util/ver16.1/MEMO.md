---
workflow: research
source: master_plan
---

# MEMO: util ver16.1 — PHASE8.0 §2 deferred execution 実装メモ

## 実装サマリ

PHASE8.0 §2 deferred execution を実装完了。

- 新規: `scripts/claude_loop_lib/deferred_commands.py`（request scan / validate / execute / consume / resume prompt 組み立て / orphan 検知）
- 変更: `scripts/claude_loop.py`（`_execute_single_step` 抽出 → `_process_deferred` 追加 → `_run_steps` への差し込み、`--no-deferred` CLI フラグ追加）
- 変更: `scripts/claude_loop_research.yaml`（`/write_current` step に `effort: high` 追加）
- 変更: `scripts/USAGE.md` / `scripts/README.md`（deferred queue の概要・schema・運用追記）
- 新規テスト: `scripts/tests/test_deferred_commands.py`（14 case）+ `test_claude_loop_integration.py` に 2 case 追加
- 合計テスト数: 280 → 296（全 PASS）

## 完了条件（IMPLEMENT.md §6 / PHASE8.0 §2-3）

| # | 完了条件 | 根拠 |
|---|---|---|
| 1 | 登録 → 外部実行 → 結果保存 → request 削除 → session 再開の無人完走 | `test_deferred_request_triggers_resume`（integration test）で resume 呼出・done/ 移動・meta.json 作成を検証 |
| 2 | 結果ファイル単体で「何が走ったか / 成功か / 出力サイズ」判定可能 | meta.json に `commands` / `exit_codes` / `overall_exit_code` / `stdout_bytes` / `stderr_bytes` を格納（`test_successful_run_writes_meta_and_logs`） |
| 3 | 90 秒見守りなしで heavy task を取り込める | 機構が提供する構造（request 登録 → Python が外出し実行 → resume）で自動達成。`experiments/deferred-execution/` で方式比較記録 |
| 4 | 失敗時 orphan request ゼロ + resume 情報欠落なし | `consume_request` を try/finally の finally 相当 path（`_process_deferred` で request ごとに try/finally）で呼ぶ + `.started` marker による SIGKILL 検知（`test_orphan_detection`） |
| 5 | workflow 自己テスト方式の整理（常時組み込みはしない） | `experiments/deferred-execution/NOTES.md` に「有望な方式 / 避けるべき方式」が整理済（別 step 生成物）。本版は YAML 新規追加なし |

## リスク・不確実性の扱い（IMPLEMENT.md §5）

### §5-1. Session resume の二重起動リスク

**検証先送り**。RESEARCH.md §A3 / §A6（Anthropic 公式 docs / repo issue）で「`-p --resume <id>` が headless 継続の正典 pattern、`--fork-session` 既定オフで同一 id 再利用・履歴追記」が一次資料確定済。EXPERIMENT.md §U2/§U3 は nested `claude` 起動による観測バイアス（§5-5）のため未検証扱い。本版は `--bare` **なし**で実装（EXPERIMENT §U2/§U3 の判断に従う）。本番発生時の兆候は「resume 後に履歴欠落 / 別セッション扱いになる」など。対応方針: IMPLEMENT §5-1 fallback（新規 session id + 履歴を明示 prompt に貼る）に切替。`ISSUES/util/medium/deferred-resume-twice-verification.md` に追加済。

### §5-2. Orphan request の発生条件

**検証済**。`.started` marker 方式を実装。EXPERIMENT.md §U5 で「正常終了 → marker 消去、SIGKILL → marker 残存、scan が拾う」を実測。`_process_deferred` で orphan 検出時は workflow を停止し人手復旧を促す（副作用ある request の自動再実行を防止）。`test_orphan_detection` で scan 側を検証。

### §5-3. 巨大 stdout による prompt 肥大化

**検証済**。EXPERIMENT.md §U4 で head 20 + tail 20 行（C 案）を確定。`HEAD_EXCERPT_LINES = 20`, `TAIL_EXCERPT_LINES = 20` として `deferred_commands.py` に実装。10MB stdout でも resume prompt は 2.2KB 前後（`test_excerpt_stays_bounded_for_large_stdout` で < 4000 bytes を assert）。

### §5-4. YAML sync 契約への軽い逸脱

**検証不要**。`.claude/rules/scripts.md` §3 の sync 対象は `command` / `defaults` セクションで、`steps[].effort` は各 YAML 独自構成が前提。今回 `claude_loop_research.yaml` だけ `write_current` step に `effort: high` を追加したが、sync 契約の対象外なので他 5 YAML は変更不要。

### §5-5. research workflow 自己適用時の観測バイアス

**検証不要**。本 run の `/research_context` / `/experiment_test` では deferred を発動しなかった（artifact 書き出しのみ）。deferred 経路の実走は次回以降の run で行う。

## 計画との乖離

1. **`logging_utils.py` に `format_deferred_result` を追加する計画 → 代わりに `deferred_commands.py` に `summarize_result` を配置**。理由: `DeferredResult` TypedDict が `deferred_commands.py` で定義されており、`logging_utils.py` にロジックを分離すると型の循環参照になる。両モジュールの責務境界は「`logging_utils.py` は汎用 IO、`deferred_commands.py` は deferred 固有整形」で整合する。
2. **`validation.py` に `validate_deferred_request` を追加する計画 → 代わりに `deferred_commands.validate_request` 内でインライン実装**。理由: `validation.py` は startup 時の YAML 一括検証専用で `Violation` dataclass を返すインフラ。deferred request は実行時検査で `ValueError` を投げる方が自然かつ呼び出し側が 1 箇所に閉じる。
3. **`_execute_single_step()` シグネチャから `command_str: str` を省略**。REFACTOR.md 記載の signature では `command_str` を受けるが、抽出範囲（subprocess 実行 + footer）では未使用のため省略した（未使用引数の混入を避ける）。呼び出し側の step header 出力は抽出範囲外で維持。

## 残課題・未修整エラー

- なし（全 Python テスト 296/296 PASS）
- `npx nuxi typecheck` は vue-router volar 関連の既知エラーで失敗（CLAUDE.md で「ビルド・実行に影響なし」と明示、本版変更とは無関係）

## ドキュメント更新候補（別フロー）

- `docs/util/ver16.0/CURRENT_scripts.md` に deferred execution 節の追記（`/write_current` step で処理予定）
- `scripts/claude_loop_lib/` モジュール一覧への `deferred_commands.py` 追加（README.md に追加済）

## 次バージョン以降への引き継ぎ候補

- **ver16.2**: PHASE8.0 §3（token/cost 計測）。deferred execution の cost も観測対象に含める
- **ver16.2 以降**: EXPERIMENT.md §U2/§U3（`--bare` 採用判定・二重 resume 実測）を実環境で検証。deferred が実際に発動する経路が登場するため、実機テストが可能になる
- **ver16.2 以降**: `cleanupPeriodDays` を deferred 運用観点から明示設定するか検討（30 日を超える deferred は本版スコープ外）

## wrap_up 対応結果（ver16.1）

- ドキュメント更新候補（`CURRENT_scripts.md`）: `/write_current` step に委譲、本版スコープ外
- 次バージョン引き継ぎ候補: 本 MEMO §次バージョン以降への引き継ぎ候補 に記録済み、追加 ISSUE 不要
- 計画との乖離 3 件: 本 MEMO §計画との乖離 に理由付き記録済み、追加 ISSUE 不要
- ISSUES 状態: `deferred-resume-twice-verification.md` は raw/ai のまま継続（実機検証待ち）
