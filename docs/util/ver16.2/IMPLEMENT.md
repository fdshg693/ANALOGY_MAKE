---
workflow: research
version: 16.2
source: split_plan
---

# ver16.2 IMPLEMENT — PHASE8.0 §3 token/cost 計測

本ファイルは `/split_plan` 段階での実装計画。`workflow: research` のため、§0 に列挙する論点は `/research_context`（外部仕様確認）と `/experiment_test`（実機 sample 採取）で解決する。「実験判断待ち」マーカーの箇所は `/imple_plan` が RESEARCH.md / EXPERIMENT.md を読んで確定する。

## 0. リスク・不確実性（`/research_context` 入力点）

以下の論点は本 SKILL の範囲では確定できない。`/research_context` は **まず一次資料（`claude --help` / Anthropic 公式 docs / 公式 SDK `usage` 型定義 / pricing page）** を当たり、不足分のみ `use-tavily` 経由の外部調査で補うこと。`/experiment_test` は「同期実行制約（nested `claude` 禁止）」を守り、`experiments/cost-usage-capture/` 配下の短い prompt 実行で JSON 構造の実 sample を採取する。

### U1. Claude CLI usage / cost の一次取得経路

**何を確認するか**:

1. `claude -p "1+1"` を `--output-format json` で実行したとき、stdout に single JSON object が返るか、複数 event の stream が返るか
2. その JSON object（または終端 event）に含まれる usage フィールドの正確な key 名と型（候補: `usage.input_tokens` / `output_tokens` / `cache_creation_input_tokens` / `cache_read_input_tokens`、あるいは `message.usage.*`、あるいは `stop_reason` と同階層、など）
3. session ID / model name が同じ JSON 内で取れるか（cost を session_id で紐付けるため）
4. `--output-format stream-json` とは何が違うか。live streaming を残したまま usage を取れる経路があるか
5. `claude` が `--output-format json` を受け付けない場合の代替（stderr に JSON を吐く / sidecar ファイル / Anthropic API 経由で別途取得 / `claude cost` のような subcommand）

**どのソースで確認するか**:

- 一次: `claude --help` / `claude -p --help` / 公式 docs（`docs.anthropic.com/en/docs/claude-code/*`）の output format 節
- 補強: 公式 SDK（`@anthropic-ai/sdk` の `Usage` 型定義）で cache token の key 名典拠を拾う
- 最終手段: `use-tavily` で「claude code cli output-format json usage」「claude code cli cache_read_input_tokens」等を検索

**どう判定するか**: 経路候補（A: JSON 直取り / B: stderr JSON / C: sidecar / D: API 再取得）のうち、**「live log stream を壊さない」「1 invocation = 1 usage record を確実に紐付けられる」** の 2 条件を両方満たす最小構成を選ぶ。両立不可なら「live log を諦める」「cost は approximate な別経路」の trade-off を RESEARCH.md §結論に明記。

### U2. 価格表の保持方法と「計算時点」の記録

**何を確認するか**:

1. モデル単価（opus / sonnet / haiku / cache read / cache write）の 2026-04 時点の値と出典 URL
2. 単価の更新頻度と「どの日付の価格表で計算したか」を後から特定する慣行（SDK や billing API に `price_version` のような識別子はあるか）
3. cache read / cache write の扱い（input と同価格か、割引か、上乗せか）

**どう判定するか**: `PRICE_BOOK` を `costs.py` 内の **module-level constant dict**（`.claude/rules/scripts.md` §1 「dataclass/3rd-party 禁止」準拠）として持ち、`price_book_version: str`（例: `"2026-04-24-anthropic-public"`）を cost record に含める方針で確定する想定。外部ファイル化（YAML / JSON）は保留（値変動が少なければ hardcode で済むが、retrospective で頻繁に書き換えるなら外部化）。

### U3. deferred execution 経路との cost 分離

**何を確認するか**:

1. ver16.1 実装の deferred execution（`_process_deferred` → resume via `-r <session-id>`）において、resume 後の Claude invocation も独立した step 扱いで usage が取れるか。取れる場合、元 step の usage と足し合わせるか別列で持つか
2. 外部コマンド実行（`deferred_commands.execute_request` 内の `subprocess.run`）は Claude token を消費しないため cost = 0 だが、「duration は長いが cost は 0」の step が混じることを cost sidecar / log 表示でどう区別するか

**どう判定するか**: cost record に `kind: "claude" | "deferred_resume" | "deferred_external"` を持たせる方針を仮置き。実取得経路が `kind="deferred_resume"` を独立 invocation として emit するかは U1 の結論に依存するため **実験判断待ち**。

### U4. cost sidecar の保存先と命名

**何を確認するか**（実装判断のみ、外部調査不要）:

1. `logs/workflow/{timestamp}_{workflow}.log` と同じディレクトリに置くか、`logs/workflow/costs/{timestamp}_{workflow}.json` のような sub-dir に分けるか
2. run 単位（1 log 1 sidecar）にするか、step 単位（複数 json）にするか
3. `.gitignore` 追加が必要か（現行 `logs/workflow/*.log` は ignored 想定なので確認）

**仮決め**: `logs/workflow/{timestamp}_{workflow}.costs.json` とする（1 run 1 sidecar、log と stem 共有で紐付け容易）。`/experiment_test` で `logs/workflow/` の実運用 sample を確認し `.gitignore` 状況と衝突しないことを確認する。

### U5. 欠測表現

**何を確認するか**（実装判断のみ）:

1. usage が取れなかった step を `null` で残すか、`{"status": "unavailable", "reason": "..."}` で残すか。retrospective 集計スクリプト（ver16.2 では未実装、将来想定）が扱いやすい方
2. 合計行では欠測 step を「除外」するか「0 として加算」するか（後者は誤魔化しに該当するので ROUGH_PLAN では禁止済）

**仮決め**: `{"status": "unavailable", "reason": "<string>"}` で残し、sum 計算時は欠測を除外して `"missing_steps": N` を run total に併記する方針。`/experiment_test` で 1 度意図的に欠測を起こす（例: `--output-format json` 非対応 flag 組み合わせ）ことで扱いやすさを確認する。

### U6. `--output-format json` が live stderr 出力を潰すか（experiment で実測）

U1 の副次論点だが実機確認が主になるため分離。現行 `_execute_single_step` は `stdout=subprocess.PIPE, stderr=subprocess.STDOUT` で merge して `tee.write_process_output` に line-by-line で流している。`--output-format json` を足したとき:

- A) 「実行中はログが出ず最後に JSON 1 行」になるのか
- B) ツール呼び出しなど中間 event が stream される `stream-json` モードが別にあるのか
- C) 現行の human-readable 出力 + 末尾 JSON の組み合わせで得られる hybrid mode があるか

を `experiments/cost-usage-capture/` で `claude -p "1+1=?" --output-format json` と `--output-format stream-json` の **両方** を実行し比較する（同期実行制約を守るため、`experiments/` 配下スクリプトを single-shot で起動する範囲に留める）。

**判断ゲート（`/experiment_test` が EXPERIMENT.md §判断 に書くべき結論）**:

- 結果が **A** の場合 → `_execute_single_step` を `--output-format json` 経路に切り替え、captured_output を buffer して step 終了後に `json.loads` する実装を選ぶ。live log は「実行中サイレント、終了後に JSON を human-readable に成形して tee に流す」方式で代替
- 結果が **B**（`stream-json` で live event も来る）の場合 → `stream-json` を採用し、`tee.write_process_output` を「各 event を 1 行としてそのまま tee + 最終 `message_stop` 相当 event だけを buffer」に拡張する方針
- 結果が **C**（hybrid mode が利用可能）の場合 → 現行 live log を壊さず末尾 JSON だけ buffer する最小改修で済む
- いずれも不可（= JSON usage 経路が Claude CLI に存在しない）の場合 → U1 の代替経路 D（API 経由で usage 再取得 / `claude cost` 相当 subcommand）に fallback。RESEARCH.md §結論でその経路仕様を確定する

`/imple_plan` は EXPERIMENT.md §判断 の A/B/C/D を読んで §1-3 の「captured_output 追加方式」を 1 つに確定する。

## 1. 実装対象モジュール

### 1-1. 新規: `scripts/claude_loop_lib/costs.py`

**責務**: Claude 1 invocation の usage 情報から cost を算出し、run 全体の集計を行う。

**公開 API（暫定）**:

```python
# 型定義 — TypedDict（dataclass 禁止 per .claude/rules/scripts.md §1）
class StepCost(TypedDict):
    step_name: str
    session_id: str
    model: str | None
    started_at: str           # ISO 8601
    ended_at: str
    duration_seconds: float
    kind: str                 # "claude" | "deferred_resume" | "deferred_external"
    input_tokens: int | None
    output_tokens: int | None
    cache_read_input_tokens: int | None
    cache_creation_input_tokens: int | None
    cost_usd: float | None
    price_book_version: str | None
    status: str               # "ok" | "unavailable"
    reason: str | None        # populated when status == "unavailable"

class RunCostSummary(TypedDict):
    workflow_label: str
    started_at: str
    ended_at: str
    total_cost_usd: float
    missing_steps: int
    price_book_version: str   # run 全体で使用した PRICE_BOOK_VERSION（step 側と同値、run 単位で 1 度だけ記録）
    steps: list[StepCost]

# 価格表 — 2026-04 時点の定数。単価 = USD / 1M tokens（Anthropic の公開表記に合わせる想定）
PRICE_BOOK_VERSION: str   # e.g. "2026-04-24-anthropic-public" — U2 で確定
PRICE_BOOK: dict[str, dict[str, float]]
# 例（確定は U2）:
#   PRICE_BOOK["opus"] = {
#       "input": 15.0, "output": 75.0,
#       "cache_read": 1.50, "cache_creation": 18.75,
#   }

def parse_usage_from_claude_output(raw: bytes | str, *, output_format: str) -> dict | None:
    """Extract usage dict from Claude CLI output. Returns None if not present.

    Exact implementation depends on U1/U6 conclusion (JSON key path, stream vs single-shot).
    【実験判断待ち】 parse strategy is pinned after RESEARCH.md §U1 + EXPERIMENT.md §U6.
    """

def calculate_cost(usage: dict, *, model: str, price_book: dict | None = None) -> float:
    """Given usage dict + model name, return USD cost via PRICE_BOOK lookup.

    Unknown model raises ValueError (caller should wrap to set status='unavailable').
    """

def build_step_cost(
    *, step_name: str, session_id: str, model: str | None,
    started_at: str, ended_at: str, duration_seconds: float,
    kind: str, usage: dict | None, reason: str | None = None,
) -> StepCost:
    """Construct a StepCost, filling status='unavailable' when usage is None."""

def aggregate_run(workflow_label: str, started_at: str, ended_at: str,
                  steps: list[StepCost]) -> RunCostSummary:
    """Sum cost_usd across steps with status='ok'; count missing."""

def write_sidecar(path: Path, summary: RunCostSummary) -> None:
    """Write JSON sidecar (UTF-8, indent=2, sort_keys=True)."""

def format_run_summary_for_log(summary: RunCostSummary) -> list[str]:
    """Return lines for appending to the workflow footer (via TeeWriter)."""
```

**注記**:

- `parse_usage_from_claude_output` の実装詳細は U1 結論で確定。現時点の prototype は「単一 JSON object を `json.loads`、`.usage` または `.message.usage` から 4 key を拾う」想定。stream-json なら「最後の `message_stop` 相当 event の usage を採る」想定
- cache token の key 名（`cache_read_input_tokens` vs `cache_read` vs 他）は U1 で確定。内部表現は 2026-04 Anthropic 公式 SDK の命名 (`cache_creation_input_tokens` / `cache_read_input_tokens`) に寄せる方針（不確定なら RESEARCH.md で上書き）

### 1-2. 変更: `scripts/claude_loop_lib/logging_utils.py`

追加する関数（既存には触らない、純増分）:

```python
def format_step_cost_line(cost: StepCost) -> str:
    """Return a single line for the step footer:
    'Cost: $0.0123 (in: 1200, out: 340, cache_r: 50, cache_w: 0, model: opus)'
    or 'Cost: unavailable (reason: ...)' when status='unavailable'.
    """

def format_run_cost_footer(summary: RunCostSummary) -> list[str]:
    """Lines appended to the SUCCESS / FAILED workflow footer:
      Run cost: $0.234 USD (price book: 2026-04-24-anthropic-public)
      Steps: 8 ok / 0 unavailable
      Per-step:
        [1] issue_plan    $0.045 (opus)
        [2] split_plan    $0.032 (opus)
        ...
    """
```

`format_duration` / `TeeWriter` / `print_step_header` / `create_log_path` は変更しない。

### 1-3. 変更: `scripts/claude_loop.py`

**変更点 3 箇所**:

1. **`_execute_single_step` の戻り値拡張** — 現行 `(exit_code, prev_commit)` → `(exit_code, prev_commit, captured_output)`。`captured_output` は `bytes | None`（tee 経路のときのみ `bytearray` を buffer して返す、tee 非経路は None）。呼び出し側で `costs.parse_usage_from_claude_output` に渡す
   - **実装判断待ち**: live streaming を壊さず capture するため、`tee.write_process_output` を「行ごとに tee + buffer に append」する形に拡張するか、別関数 `tee.write_process_output_capturing(process) -> tuple[int, bytes]` を追加する。後者が副作用最小（U1/U6 で経路確定後に決める）
   - cost 経路が「別 invocation で usage を再取得」になる場合（U1 経路 D）は captured_output 不要なので、この変更自体を取りやめ、別 API で取得する
   - **tee=None 経路（`--no-log` / `--dry-run` 経由）の扱い（意図的スコープ限定）**: `tee is None` の場合 `subprocess.run(...)` に `capture_output=True` を付け足す選択肢もあるが、本版では **行わない**。`--no-log` は開発者が手元で short smoke を回す用途であり cost sidecar を残す意味が薄く、`--dry-run` はコマンド確認のみで実行しない。よって tee 非経路の全 step は `captured_output=None` → `status="unavailable"` / `reason="no-log run"`（または `"dry-run"`）で sidecar に残す。run total は自然に `missing_steps=N` となる。この挙動は `scripts/README.md` / `USAGE.md` の cost 節に明記する

2. **`_run_steps` に cost collector を組み込む** — ループ内 step 終了後（success path / `consume_feedbacks` の直前）に以下を挿入:

   ```python
   step_cost = costs.build_step_cost(
       step_name=step["name"], session_id=session_id, model=effective_model,
       started_at=step_start_time.isoformat(), ended_at=datetime.now().isoformat(),
       duration_seconds=time.monotonic() - step_start, kind="claude",
       usage=costs.parse_usage_from_claude_output(captured_output, output_format=...),
   )
   step_costs.append(step_cost)
   if tee is not None:
       tee.write_line(logging_utils.format_step_cost_line(step_cost))
   ```

   - deferred resume 経路も同様に `kind="deferred_resume"` で独立 record を追加
   - `_process_deferred` 内の外部コマンドは `kind="deferred_external"`、usage=None（Claude token 非消費）

   **call boundary（現時点で確定）**: cost record 収集は `_process_deferred` の **呼び出し側（= `_run_steps`）** で行う。`_process_deferred` の signature は変更せず、既存どおり `resume_code` を返すまま。`_run_steps` 側で:

   ```python
   # _process_deferred 呼び出し前後で started_at / ended_at / session_id / captured_output を取得
   deferred_start = datetime.now()
   deferred_monotonic = time.monotonic()
   resume_code, deferred_captured = _process_deferred(...)  # 戻り値拡張
   deferred_end = datetime.now()
   step_costs.append(costs.build_step_cost(
       step_name=f"{step['name']} (deferred_resume)",
       session_id=session_id, model=effective_model,
       started_at=deferred_start.isoformat(), ended_at=deferred_end.isoformat(),
       duration_seconds=time.monotonic() - deferred_monotonic,
       kind="deferred_resume",
       usage=costs.parse_usage_from_claude_output(deferred_captured, output_format=...),
   ))
   ```

   `_process_deferred` 内の外部コマンド群 (`deferred_commands.execute_request`) の cost は `DeferredResult` から逆算する（record は「外部コマンド 1 件 = 1 record」ではなく run 単位集計としてまとめる。詳細は `/imple_plan` で `DeferredResult` 構造を読んで確定）。これにより `_process_deferred` の public interface 変更は resume subprocess の captured_output を追加で返すだけに閉じる

3. **run 終了時の sidecar 書き出し + 合計行** — `_run_steps` の成功 footer / 失敗 footer で:

   ```python
   summary = costs.aggregate_run(workflow_label, run_started, datetime.now().isoformat(), step_costs)
   if log_path is not None:
       sidecar_path = log_path.with_suffix(".costs.json")
       costs.write_sidecar(sidecar_path, summary)
       for line in logging_utils.format_run_cost_footer(summary):
           _out(line)
   ```

   `stats: RunStats` に `cost_summary: RunCostSummary | None` を追加して `main()` 側で notify 連携する選択肢もあるが、notify 文字数を肥大化させるため **本版では log / sidecar のみ**、notify は据え置き（retrospective §3.5 で判断）。

**`--output-format json` / `stream-json` の付与**:

- `resolve_command_config` が返す `common_args` に追加するか、`build_command` 内で無条件に追加するか、どちらも U1 結論次第。追加先は **commands.py の `build_command` 内**を第一候補（YAML 同期契約に触れないため）
- **実験判断待ち**: YAML の `command.args` に入れるなら 6 YAML 同期が発生する。`build_command` 内での hardcode は sync 対象外で済むが、stream-json が future-breaking な場合に差し替えできる柔軟性を失う

### 1-4. 変更: `scripts/claude_loop_lib/commands.py`

**変更内容**（U1/U6 確定後）:

- `build_command` の末尾に `cmd.extend(["--output-format", "<決定値>"])` を追加する候補
- ただし、 step 側 / defaults 側に `output_format` override を許す必要があるか（`use-tavily` や MCP 系 step で別 format を要求するケースがあるか）は U1 で確認。ない見込みだが、念のため RESEARCH.md §U1 の付随論点として触れる
- **実験判断待ち**: format 値は `json` / `stream-json` / 現行（未指定）のいずれか

### 1-5. 変更: `scripts/claude_loop_lib/validation.py`

新規 validation ルール（追加した場合のみ）:

- `command.args` に `--output-format` 指定が混入していないか（`build_command` 側で付与する契約と二重付与を防ぐため）
- `defaults` / `steps[]` に `output_format` override キーを追加する場合、`OVERRIDE_STRING_KEYS` と `ALLOWED_*_KEYS` に追加
- cost 設定キー（例: `cost.disable: true` のような run 単位無効化）を追加する場合、top-level `cost` セクションを新設し `ALLOWED_TOPLEVEL_KEYS` を拡張

**仮判断**: 本版では `output_format` override と `cost` セクションを **追加しない**。`build_command` 内で `--output-format json`（または U1 結論値）を hardcode し、YAML 同期を避ける。U1 結論が「override 必要」と示したら `/imple_plan` で再判断。

**`.claude/rules/scripts.md` §3 との整合**: 追加する validation（`command.args` に `--output-format` が混入したらエラー）は **guard チェック**であり、「新しい override キー追加」ではない。`ALLOWED_COMMAND_KEYS` / `ALLOWED_DEFAULTS_KEYS` / `ALLOWED_STEP_KEYS` / `OVERRIDE_STRING_KEYS` は **不変**。よって「6 YAML `command` / `defaults` セクションは同一」契約を破らない。

### 1-6. 新規: `scripts/tests/test_costs.py`

**unittest（pytest 非採用、既存踏襲）** で以下の単体テストを追加:

| ケース | 検証内容 |
|---|---|
| `test_parse_usage_single_shot_json` | Anthropic-style JSON fixture（`{"usage": {"input_tokens": 10, "output_tokens": 20, ...}}`）から 4 key を抽出 |
| `test_parse_usage_stream_json_final_event` | stream-json 最終 event fixture から usage 抽出（U6 で経路が stream-json と確定した場合） |
| `test_parse_usage_missing_returns_none` | usage fielf 不在時に `None` を返す |
| `test_calculate_cost_opus` | `{input: 1M, output: 1M, cache_r: 1M, cache_w: 1M}` を PRICE_BOOK で計算し期待値に一致 |
| `test_calculate_cost_unknown_model_raises` | 未知 model で `ValueError` |
| `test_build_step_cost_unavailable_when_usage_none` | `usage=None` / `reason="..."` 指定時に `status="unavailable"` で全 token field が None |
| `test_aggregate_run_sums_ok_only` | 3 step（ok / ok / unavailable）で total が 2 step 合計、missing_steps=1 |
| `test_write_sidecar_roundtrip` | 一時ディレクトリに書き出して `json.loads` で同値 |
| `test_price_book_version_in_summary` | run summary に `price_book_version` が含まれる |

fixture は `test_costs.py` 内の string literal として持つ（3rd-party 依存禁止、pytest fixture 機構不使用）。

### 1-7. 変更: `scripts/tests/test_logging_utils.py`

追加ケース:

- `test_format_step_cost_line_ok`
- `test_format_step_cost_line_unavailable`
- `test_format_run_cost_footer_lines_structure`（`[N] name  $X.XXX (model)` 行の行数が `len(steps)` + header 2 行 と等しい等）
- `test_format_run_cost_footer_with_missing_steps`（`missing_steps > 0` の run summary で「Steps: N ok / M unavailable」行が含まれ、`status="unavailable"` の step 行では `$X.XXX` 欄が `unavailable` 表記になる）

### 1-8. 変更: `scripts/tests/test_claude_loop_integration.py`（必要な場合のみ）

**実験判断待ち**: 既存 integration test は subprocess を mock しているため、usage JSON も mock で差し込めば sidecar 生成経路のテストは書ける。ただし、既存テストが Claude CLI を実起動せず mock 経由で走る構造になっているか確認した上で加除を決める（本 SKILL では未確認。`/imple_plan` 時点で検証）。

候補ケース:

- `test_run_generates_costs_sidecar`: dry-run 以外の短い workflow を mock で走らせ、`logs/workflow/*.costs.json` が作られていること + JSON spec を満たすことを assert

### 1-9. 変更: `scripts/README.md` / `scripts/USAGE.md`

- `README.md`: 「cost 計測」節を追加（1 段落 + sidecar path 規約 + `PRICE_BOOK_VERSION` の更新手順）
- `USAGE.md`:
  - CLI オプション表に cost 関連は（現状）追加しない（本版では CLI オプション化しない方針）
  - 「YAML ワークフロー仕様」節に `--output-format` 付与が `build_command` 内で行われる旨と、`command.args` で重複付与禁止である旨を追記（U1 結論で付与場所が変わったら更新）
  - 「実行時出力」節（あれば）に sidecar 仕様を追加

### 1-10. 変更: `docs/util/MASTER_PLAN/PHASE8.0.md`

`§3 実装進捗` テーブルの状態を「未着手」→「✅ 実装済み（ver16.2、2026-04-DD）」に更新し、PHASE8.0 全 3 節完走を宣言する（`/wrap_up` で行う想定だが、本 SKILL でもマイルストーン記録として触れる）。

### 1-11. `.claude/rules/scripts.md`（判断は `/wrap_up` 以降）

cost log / sidecar の stable rule 化は §3 完走後に判断（FEEDBACKS handoff §後続 step への注意点 §4 より）。本 SKILL では記載しない。

## 2. 実装順序

1. `costs.py` の型定義 + `PRICE_BOOK`（U2 確定値）+ `calculate_cost` + `build_step_cost` + `aggregate_run` + `write_sidecar`
2. `test_costs.py` 単体テスト（mock fixture ベース、外部実行なし）
3. `logging_utils.py` に `format_step_cost_line` / `format_run_cost_footer` 追加 + `test_logging_utils.py` 拡張
4. `costs.parse_usage_from_claude_output` を U1/U6 結論で実装
5. `claude_loop.py` の `_execute_single_step` / `_run_steps` 改修 + commands.py への `--output-format` 付与
6. integration test 追加（必要なら）
7. `scripts/README.md` / `USAGE.md` 追記
8. `docs/util/MASTER_PLAN/PHASE8.0.md` §3 完走マーク

## 3. YAML 同期契約への影響

本版で YAML の `command` / `defaults` / `steps` 公開キーを増やさない方針のため、**6 YAML 同期は不要**（`build_command` 内に `--output-format` を hardcode する前提）。

ただし `/research_context` / `/experiment_test` の結果、「step 単位で `output_format` を切り替える必要がある」と判明した場合は以下の分岐:

- (a) 6 YAML に `output_format` キーを同期追加（手動同期、ver16.0 RETROSPECTIVE で既知リスク）
- (b) YAML sync 契約の生成元 1 箇所化（scope 膨張、別バージョンへ）

→ 判断は `/imple_plan` が RESEARCH.md §U1 + EXPERIMENT.md §U6 の結論を読んで行う（PLAN_HANDOFF §後続 step への注意点 §4 と整合）。

## 4. 後続 step（`/research_context` / `/experiment_test` / `/imple_plan`）への引き継ぎ

- `/research_context`: §0 の U1 / U2 / U3 を一次資料優先で確定。RESEARCH.md §結論 は「取得経路 X、price book Y、cache key 名 Z、kind 分類 W」を明示
- `/experiment_test`: §0 の U6（+ U1 実機確認）を `experiments/cost-usage-capture/` 配下で実証。具体的には `claude -p "1+1=?" --output-format json` と `--output-format stream-json` の 2 回実行、および usage が欠落する組み合わせ（例: `--dry-run` 類）を 1 回実行して欠測 sample を得る。`experiments/` 先頭コメントに「PHASE8.0 §3 U1/U6 確認用、ver16.2 完了後削除可」と明記
- `/imple_plan`:
  - (i) §1-3 の「実験判断待ち」（`tee.write_process_output_capturing` 追加 vs 既存拡張 / `--output-format` 付与場所 / kind 分類の sidecar 表現）を確定
  - (ii) §3 の YAML sync 判断 (a)/(b) を確定
  - (iii) integration test 追加の要否を既存 test 構造確認後に確定

## 5. 完了条件（本版 / PHASE8.0 §3-2 由来）

- すべての Claude 呼び出し step に対し `StepCost` record が生成され、欠測時は `status="unavailable"` + `reason` が付く
- 1 run 終了時に step 別 cost 行と合計行が workflow log に残り、`logs/workflow/{stem}.costs.json` sidecar が生成される
- `price_book_version` が record に含まれ、どの価格表で計算したかが後から判別できる
- deferred execution の外部コマンドは `kind="deferred_external"` として cost=0 扱い、Claude resume は `kind="deferred_resume"` として独立 cost 加算される
- 単体テストが `costs.py` の主要経路（parse / calc / aggregate / sidecar IO / missing）をカバーする
- `scripts/README.md` / `scripts/USAGE.md` に cost 計測節 / sidecar 仕様が追記されている
- `docs/util/MASTER_PLAN/PHASE8.0.md` §3 が ✅ となり PHASE8.0 完走宣言が書かれる
