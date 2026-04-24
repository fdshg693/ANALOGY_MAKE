# CHANGES: util ver16.2 — PHASE8.0 §3 token/cost 計測実装

## 変更ファイル一覧

### 新規追加

| ファイル | 概要 |
|---|---|
| `scripts/claude_loop_lib/costs.py` | Claude CLI invocation 単位の usage/cost 取得・計算・集計・sidecar 書き出しコアモジュール |
| `scripts/tests/test_costs.py` | `costs.py` 専用テスト（21 ケース：parse / calc / build / aggregate / sidecar / fallback / 欠測） |
| `experiments/cost-usage-capture/` | CLI `--output-format json` / `stream-json` の実機 sample 採取ディレクトリ群（research workflow 成果物） |

### 変更

| ファイル | 変更概要 |
|---|---|
| `scripts/claude_loop_lib/logging_utils.py` | `TeeWriter.write_process_output_capturing` 追加・`format_step_cost_line` / `format_run_cost_footer` 追加 |
| `scripts/tests/test_logging_utils.py` | cost formatter 5 ケース追加（14 → 19 ケース） |
| `scripts/claude_loop_lib/commands.py` | `build_command` に `output_format_json` 引数追加・`CLAUDE_OUTPUT_FORMAT_JSON` 定数追加 |
| `scripts/claude_loop.py` | `_execute_single_step` の戻り値拡張・`DeferredOutcome` TypedDict 追加・`_process_deferred` 戻り値変更・`_run_steps` に cost 収集と sidecar 書き出し追加 |
| `scripts/README.md` | 「cost 計測」節追加（取得経路・sidecar path 規約・PRICE_BOOK 更新手順） |
| `scripts/USAGE.md` | ログ出力フォーマットに cost 行を追記・sidecar 仕様を追記 |
| `docs/util/MASTER_PLAN/PHASE8.0.md` | §3 を「✅ 実装済み（ver16.2、2026-04-24）」に更新・PHASE8.0 全 3 節完走宣言 |

---

## 変更内容の詳細

### `scripts/claude_loop_lib/costs.py`（新規）

PHASE8.0 §3 のコアモジュール。公開型と主要関数:

**型定義（TypedDict）**:

| 型 | 主要フィールド |
|---|---|
| `StepCost` | `step_name`, `session_id`, `model`, `started_at`, `ended_at`, `duration_seconds`, `kind`, `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`, `num_turns`, `cost_usd`, `cost_source`, `status`, `reason` |
| `RunCostSummary` | `workflow_label`, `started_at`, `ended_at`, `claude_code_cli_version`, `price_book_source`, `total_cost_usd`, `missing_steps`, `steps` |

**`kind` の 3 値**: `"claude"` / `"deferred_resume"` / `"deferred_external"`

**主要関数**:

| 関数 | 役割 |
|---|---|
| `parse_cli_result(raw)` | `--output-format json` の raw bytes を JSON パース、`None` を返したら unavailable |
| `extract_usage(result)` | `SDKResultMessage` 互換オブジェクトから usage / total_cost_usd / modelUsage を抽出 |
| `calculate_cost_from_price_book(usage, model)` | fallback 用 PRICE_BOOK による cost 計算（primary は CLI の `total_cost_usd`） |
| `build_step_cost_from_cli_output(...)` | captured bytes → StepCost 構築（`status="unavailable"` / `reason` も設定） |
| `aggregate_run(...)` | `status="ok"` のみ合計・`missing_steps` カウント → `RunCostSummary` |
| `write_sidecar(path, summary)` | `logs/workflow/{stem}.costs.json` へ UTF-8 / indent=2 / sort_keys=True で書き出し |
| `detect_claude_code_cli_version()` | `claude --version` の結果を run record に含める |

**`cost_source` フィールド**: `"cli"` = CLI 側 `total_cost_usd` を使用 / `"fallback_price_book"` = PRICE_BOOK で計算 / `None` = usage 欠損。

**PRICE_BOOK_USD_PER_MTOK**: 2026-04-24 時点の Anthropic 公式 pricing page 値を hardcode（fallback 専用）。`PRICE_BOOK_SOURCE` にソース文字列を併記。

### `scripts/claude_loop_lib/logging_utils.py`（変更）

既存関数は未変更。以下を純増:

| 追加 | 説明 |
|---|---|
| `TeeWriter.write_process_output_capturing(process) -> tuple[int, bytes]` | 既存 `write_process_output` と同じ line-by-line tee を行いつつ全 bytes を buffer して返す |
| `format_step_cost_line(cost: StepCost) -> str` | step footer 用 1 行: `Cost: $0.0123 (in: 1200, out: 340, cache_r: 50, cache_w: 0, model: opus)` or `Cost: unavailable (reason: ...)` |
| `format_run_cost_footer(summary: RunCostSummary) -> list[str]` | run 末尾用複数行（run total / step 明細） |

### `scripts/claude_loop_lib/commands.py`（変更）

```python
CLAUDE_OUTPUT_FORMAT_JSON: tuple[str, ...] = ("--output-format", "json")

def build_command(..., output_format_json: bool = False) -> list[str]:
    ...
    if output_format_json:
        cmd.extend(CLAUDE_OUTPUT_FORMAT_JSON)
```

既存呼び出しは `output_format_json` を渡さないため影響なし。YAML の `command.args` / `defaults` / `steps` の公開キーは不変（YAML 同期不要）。

### `scripts/claude_loop.py`（変更）

**1. `_execute_single_step` 戻り値拡張**

```
以前: (exit_code, prev_commit)
以後: (exit_code, prev_commit, captured_output)  # captured_output: bytes | None
```

`capture_output=True`（tee 有効かつ cost tracking 有効）のとき `write_process_output_capturing` を呼んで bytes を返す。tee=None 時は `None`。

**2. `DeferredOutcome` TypedDict 追加**

```python
class DeferredOutcome(TypedDict):
    resume_code: int
    external_results: list[deferred_commands.DeferredResult]
    resume_started_at: datetime | None
    resume_ended_at: datetime | None
    resume_duration_seconds: float
    resume_captured_output: bytes | None
```

`_process_deferred` の戻り値を `int`（resume_code のみ）から `DeferredOutcome` に変更。呼び出し側は `outcome["resume_code"]` で旧来の resume_code にアクセスできる。

**3. `_run_steps` への cost 収集追加**

- step ごとに `costs.build_step_cost_from_cli_output(...)` で `StepCost` を生成、`step_costs` リストに追加
- `kind="claude"` / `"deferred_resume"` / `"deferred_external"` で種別管理
- step 終了時に `format_step_cost_line` を tee に書き出し
- run 終了時（success/failed 両方）に `costs.aggregate_run(...)` → `costs.write_sidecar(sidecar_path, summary)` + `format_run_cost_footer` を出力
- sidecar path: `logs/workflow/{stem}.costs.json`

**cost tracking の有効化条件**: `tee is not None`（= `--no-log` / `--dry-run` 時は無効）。tee=None run は全 step が `status="unavailable"` / `reason="no-log run"` となり `missing_steps=N`。

### `experiments/cost-usage-capture/`（新規）

research workflow の `/experiment_test` が生成した実機 sample ディレクトリ群:

| サブディレクトリ | 内容 |
|---|---|
| `single-shot-json/` | `--output-format json` の SDKResultMessage 構造確認 |
| `stream-json-final-event/` | `--output-format stream-json` の最終 event 確認 |
| `live-stream-compare/` | single-shot vs stream-json の live 出力比較 |
| `missing-usage/` | usage 欠損ケースのサンプル採取 |
| `modelusage-keys/` | `modelUsage` キー構造の確認 |
| `cli-version/` | `claude --version` 出力のサンプル |

---

## 技術的判断

### primary cost source を `total_cost_usd` に変更

IMPLEMENT.md §1-1 では PRICE_BOOK による計算を primary として計画していたが、RESEARCH.md §結論 Q3 により Claude CLI の `--output-format json` 出力に `total_cost_usd`（CLI 側の価格表で計算済み）が含まれることが確認できた。そのため primary 経路を `total_cost_usd` の raw 記録に変更し、PRICE_BOOK は fallback 専用に格下げ。`cost_source` フィールドで `"cli"` / `"fallback_price_book"` を区別。

### `--output-format json` による live stdout サイレント化は先送り

`--output-format json` 採用時、step 実行中はログ出力がなく終了時に JSON 1 行がまとめて出る（A 案）挙動を EXPERIMENT で確認。live ストリームが失われる影響は初回本番 run で観察し、耐えがたい場合は ver16.3 で `stream-json`（B 案）に切り替える方針（R1 リスク）。

### `_process_deferred` の戻り値を `DeferredOutcome` に拡張

IMPLEMENT.md では「signature 変更は captured_output 追加だけに閉じる」と計画していたが、`resume_started_at` / `resume_ended_at` / `external_results` も cost 集計のために必要となったため `DeferredOutcome` TypedDict にまとめた。呼び出し側の変更は最小（`resume_code` は `outcome["resume_code"]` でアクセス）。

### `command.args` への `--output-format` 混入ガードは本版では実装しない

tee 非活性時は `--output-format json` を付与しないため、YAML 側で step 別に付けたくなるケースは現状発生しない。二重付与ガードは将来 CLI 運用報告を見てから追加する方が安全と判断（MEMO.md §計画との乖離）。
