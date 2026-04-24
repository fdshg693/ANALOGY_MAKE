---
workflow: research
source: master_plan
---

# ver16.2 RESEARCH — PHASE8.0 §3 token/cost 計測 外部調査

`/research_context` で実施した外部調査の成果物。IMPLEMENT.md §0（U1/U2/U3/U6 の論点、U4/U5 は実装判断のみで外部調査不要）を入力とし、**Anthropic 公式 Claude Code / Agent SDK docs** と **公式 pricing page** を一次資料として「確定 / 部分的 / 未確定」の切り分けを行った。参照日は全て **2026-04-24**。

結論先取り: **Claude CLI `--output-format json` が `total_cost_usd` / `usage` / `modelUsage` を既に emit する**ため、本版で PRICE_BOOK を自前保持する必要性は大幅に下がる（fallback 用途に限定可能）。これは IMPLEMENT §0 U1/U2 の前提（「自前 parse + 自前計算」）を見直す重要な情報。

---

## 問い

IMPLEMENT.md §0 から、外部調査で解くべき論点を抽出する。

1. **Q1 (U1) 一次取得経路**: `claude -p "<prompt>" --output-format json` を実行したとき、stdout に何が返るか。usage / cost / session_id / model はどの key で、どの型で取れるか。`--output-format stream-json` との違いは。
2. **Q2 (U1 補強) 取得経路の候補**: JSON 直取り以外の経路（stderr / sidecar / API 経由 / subcommand）は存在するか。Claude CLI 側に「組み込みの cost 出力 / budget 機能」はあるか。
3. **Q3 (U2) 価格表と price book version**: モデル単価（Opus / Sonnet / Haiku / cache read / cache write）の 2026-04 時点の値と出典。どのキーが「どの価格表で計算したか」の識別子になるか（SDK / CLI 側にそれがあるか）。cache read / cache write / cache 5m / cache 1h の扱いは。
4. **Q4 (U3) deferred 経路での cost 分離**: ver16.1 deferred execution の `resume` subprocess は独立 invocation として usage を emit するか。足し合わせ vs 別列のどちらが自然か。Claude 側が複数 query のコスト合算を自動で提供するか。
5. **Q5 (U6 関連) live streaming との両立**: `--output-format json` を付けると stream 出力は潰れるか。`stream-json` で live event と最終 usage を両取りする公式推奨はあるか。

（**U4 cost sidecar の保存先** と **U5 欠測表現** は IMPLEMENT.md §0 で「実装判断のみ、外部調査不要」と明示されているため本 RESEARCH では扱わない）

---

## 収集した証拠

### A. Claude Code CLI 仕様（Q1 / Q2 / Q5 の一次資料）

| # | URL | 参照日 | 種別 | 要旨 |
|---|---|---|---|---|
| A1 | https://code.claude.com/docs/en/cli-reference | 2026-04-24 | PRIMARY | `--output-format` の定義: 「Specify output format for print mode (options: `text`, `json`, `stream-json`)」。例: `claude -p "query" --output-format json`。`--print`/`-p` 併用が前提。 |
| A2 | https://code.claude.com/docs/en/cli-reference | 2026-04-24 | PRIMARY | `--include-partial-messages` の定義: 「Include partial streaming events in output (requires `--print` and `--output-format=stream-json`)」→ **partial events は `stream-json` 専用**。`--output-format json` は最終 single-shot。 |
| A3 | https://code.claude.com/docs/en/cli-reference | 2026-04-24 | PRIMARY | `--input-format` の定義: 「Specify input format for print mode (options: `text`, `stream-json`)」。input 側にも stream-json があり、non-interactive での multi-turn 流し込みに使える。 |
| A4 | https://code.claude.com/docs/en/cli-reference | 2026-04-24 | PRIMARY | **`--max-budget-usd` の存在**: 「Maximum dollar amount to spend on API calls before stopping (print mode only)」。例: `claude -p --max-budget-usd 5.00 "query"`。→ **Claude CLI 自身が USD cost を tracking している**ことの CLI-level 裏付け。 |
| A5 | https://code.claude.com/docs/en/cli-reference | 2026-04-24 | PRIMARY | `--session-id` / `--resume, -r` / `--fork-session` の定義。`--resume` は既存 id の history 復元、`--session-id` は新規 UUID 採番。`--fork-session` で resume 時に新 id を採番（既定は同 id 追記）。ver16.1 RESEARCH A1/A2 と完全整合。 |
| A6 | https://code.claude.com/docs/en/headless | 2026-04-24 | PRIMARY | headless 公式 example: `session_id=$(claude -p "Start a review" --output-format json \| jq -r '.session_id') ; claude -p "Continue" --resume "$session_id"`。→ **`--output-format json` の戻り値は `.session_id` を top-level で持つ単一 JSON object**。 |
| A7 | https://code.claude.com/docs/en/headless | 2026-04-24 | PRIMARY | structured output 例: `claude -p "Summarize" --output-format json \| jq -r '.result'`。→ **top-level の `.result` が human-readable 本文**。 |
| A8 | https://code.claude.com/docs/en/headless | 2026-04-24 | PRIMARY | stream-json の用例: `claude -p "Explain recursion" --output-format stream-json --verbose --include-partial-messages`、および `jq -rj 'select(.type == "stream_event" and .event.delta.type? == "text_delta") \| .event.delta.text'` で delta を拾う。→ **stream-json は NDJSON（1 行 1 event）で、`type` / `subtype` で event 種別を判定**。 |
| A9 | https://code.claude.com/docs/en/headless | 2026-04-24 | PRIMARY | stream-json の system event spec: `type: "system"`, `subtype: "api_retry" \| "plugin_install"` 等が明記され、各 event に `uuid` と `session_id` が付く。→ stream 中に session_id を取り続けられる。 |

### B. Agent SDK / `SDKResultMessage` 型定義（Q1 / Q2 / Q3 / Q4 の一次資料）

Claude Code の `--output-format json` は Agent SDK の `SDKResultMessage` とフィールド互換（CLI は SDK の result を JSON シリアライズして返す構造）。

| # | URL | 参照日 | 種別 | 要旨 |
|---|---|---|---|---|
| B1 | https://code.claude.com/docs/en/agent-sdk/typescript | 2026-04-24 | PRIMARY | `SDKResultMessage` 型（success 分岐）: `{ type: "result"; subtype: "success"; uuid; session_id; duration_ms; duration_api_ms; is_error; num_turns; result; stop_reason; total_cost_usd: number; usage: NonNullableUsage; modelUsage: { [modelName: string]: ModelUsage }; permission_denials; structured_output?; deferred_tool_use? }`。→ **`total_cost_usd` / `usage` / `modelUsage` / `duration_ms` / `session_id` / `num_turns` が 1 object に揃って取れる**。 |
| B2 | https://code.claude.com/docs/en/agent-sdk/typescript | 2026-04-24 | PRIMARY | `SDKResultMessage` の error 分岐も同じ keyset: `subtype: "error_..." \| "error_max_structured_output_retries"` + `total_cost_usd` / `usage` / `modelUsage` を持つ。→ **失敗 step でも usage / cost は取れる**。 |
| B3 | https://code.claude.com/docs/en/agent-sdk/typescript | 2026-04-24 | PRIMARY | `Usage` 型（`@anthropic-ai/sdk` と同型）: `{ input_tokens: number \| null; output_tokens: number \| null; cache_creation_input_tokens?: number \| null; cache_read_input_tokens?: number \| null }`。→ **key 名が 4 件確定**。IMPLEMENT §1-1 `StepCost` の 4 key と完全一致。 |
| B4 | https://code.claude.com/docs/en/agent-sdk/typescript | 2026-04-24 | PRIMARY | `ModelUsage` 型: `{ inputTokens; outputTokens; cacheReadInputTokens; cacheCreationInputTokens; webSearchRequests; ...; costUSD: number; contextWindow; maxOutputTokens }`。→ **per-model cost が既に computed**。ハンドリング次第で自前計算を完全に省ける。 |
| B5 | https://code.claude.com/docs/en/agent-sdk/cost-tracking | 2026-04-24 | PRIMARY | **最重要 disclaimer**: 「The `total_cost_usd` and `costUSD` fields are **client-side estimates, not authoritative billing data**. The SDK computes them locally from a **price table bundled at build time**, so they can drift from what you are actually billed when: pricing changes / the installed SDK version does not recognize a model / billing rules apply that the client cannot model」。 |
| B6 | https://code.claude.com/docs/en/agent-sdk/cost-tracking | 2026-04-24 | PRIMARY | 正本 billing は 「Usage and Cost API」 or Console の Usage page を推奨。SDK の cost 値で「bill end users or trigger financial decisions」はしないよう明記。→ **本 repo の retrospective 根拠用途（「手戻り削減 vs. 追加 cost」比較）なら client-side estimate で十分**、ただし retrospective メモでは estimate である旨を明示すべき。 |
| B7 | https://code.claude.com/docs/en/agent-sdk/cost-tracking | 2026-04-24 | PRIMARY | cost scope の明示: **query() (= 1 CLI invocation) = 1 result message = 1 `total_cost_usd`**。session で複数 query を繋げても「each `query()` call reports its own cost independently」で、SDK は session-level の合算を自動提供しない（「you accumulate the totals yourself」）。→ **deferred resume の独立 cost 算出が素直に可能**（U3）。 |
| B8 | https://code.claude.com/docs/en/agent-sdk/cost-tracking | 2026-04-24 | PRIMARY | 「Always read cost data from the result message regardless of its `subtype`」→ **success / error を問わず 1 result から拾えばよい**。per-step `assistant` message 毎の加算は tool 並列で同一 id を持つため dedup が必要だが、`result.usage` / `total_cost_usd` は SDK 側で既に dedup 済。→ **per-assistant-message の加算 logic は不要、result 1 点参照で OK**。 |
| B9 | https://code.claude.com/docs/en/agent-sdk/cost-tracking | 2026-04-24 | PRIMARY | cache token の意味明示: `cache_creation_input_tokens` = 「charged at a higher rate than standard input tokens」、`cache_read_input_tokens` = 「charged at a reduced rate」。→ cache write / read の料金 tier 分離を公式 SDK が想定。 |
| B10 | https://code.claude.com/docs/en/agent-sdk/cost-tracking | 2026-04-24 | PRIMARY | Python 側の命名差: `message.usage` (dict) / `message.message_id` / `result.model_usage`（TS の camelCase が snake_case になる）。CLI の JSON output は **TS 命名（`modelUsage` camelCase + `usage` / `total_cost_usd` は snake_case）** に従う挙動（A6/A7 の example 出力と整合）。 |

### C. 公式 Pricing Page（Q3 の一次資料）

2026-04-24 時点。単位: USD per million tokens（MTok）。

| # | URL | 参照日 | 種別 | 要旨 |
|---|---|---|---|---|
| C1 | https://platform.claude.com/docs/en/about-claude/pricing | 2026-04-24 | PRIMARY | 料金テーブル（抜粋、Base Input / 5m Cache Writes / 1h Cache Writes / Cache Hits & Refreshes / Output Tokens）: |
|  |  |  |  | `Claude Opus 4.7` = `$5` / `$6.25` / `$10` / `$0.50` / `$25` |
|  |  |  |  | `Claude Opus 4.6` = `$5` / `$6.25` / `$10` / `$0.50` / `$25` |
|  |  |  |  | `Claude Opus 4.5` = `$5` / `$6.25` / `$10` / `$0.50` / `$25` |
|  |  |  |  | `Claude Opus 4.1` / `Claude Opus 4` = `$15` / `$18.75` / `$30` / `$1.50` / `$75` |
|  |  |  |  | `Claude Sonnet 4.6` / `4.5` / `4` = `$3` / `$3.75` / `$6` / `$0.30` / `$15` |
|  |  |  |  | `Claude Haiku 4.5` = `$1` / `$1.25` / `$2` / `$0.10` / `$5` |
|  |  |  |  | `Claude Haiku 3.5` = `$0.80` / `$1` / `$1.6` / `$0.08` / `$4` |
| C2 | 同上 | 2026-04-24 | PRIMARY | 「MTok = Million tokens. The 'Base Input Tokens' column shows standard input pricing, 'Cache Writes' and 'Cache Hits' are…」の注記。**cache は write (5m / 1h 2 tier) と hit の 3 区分**が公式枠組み。SDK 型定義（B3）は write / read の 2 区分しか持たないため、**5m vs 1h の区別を本版で明示保持するかは設計判断**（Agent SDK の `costUSD` にはどちらを適用したかの情報が含まれないため、区別したいなら自前計算が必要）。 |
| C3 | 同上 | 2026-04-24 | PRIMARY | Opus 4.7 注記: 「new tokenizer compared to previous models…may use up to 35% more tokens for the same fixed text」→ 価格表は tok 単価のみ。tok 数自体は model によって変わる。 |
| C4 | 同上 | 2026-04-24 | PRIMARY | Region 価格: Sonnet 4.5 / Haiku 4.5 以降で「Regional and multi-region endpoints include a 10% premium over global endpoints」。**本 repo は global endpoint 想定**（CLAUDE.md / 既存 env vars に region 設定なし）のため 10% premium は適用外扱いで OK。 |

### D. repo 内の関係コード（内部一次資料、U6 判断の前提）

| # | path | 要旨 |
|---|---|---|
| D1 | `scripts/claude_loop_lib/commands.py:8-51` | `build_command` は `common_args` / step `args` / `--model` / `--effort` / `--system-prompt` / `--session-id` or `-r` / `--append-system-prompt` を組み立てる。**`--output-format` は現状一切指定していない**（= 既定 `text` で動作）。→ ver16.2 で付与する場所は `build_command` 内が最短ルート。 |
| D2 | `scripts/claude_loop.py` の `_execute_single_step`（ver16.1 実装の tee 経路） | `subprocess.Popen(..., stdout=subprocess.PIPE, stderr=subprocess.STDOUT)` + `tee.write_process_output` で line-by-line に tee。**現状は text 出力を前提**。`--output-format json` にすると「実行中はサイレントで最後に JSON 1 行」になる見込み → EXPERIMENT で実測する（§U6）。 |
| D3 | `.claude/rules/scripts.md` §1/§3 | Python 3.10+、標準ライブラリと PyYAML のみ、dataclass 禁止（TypedDict 使用）、6 YAML の `command`/`defaults` セクションは同一内容を保つ。→ 本版の `costs.py` は TypedDict + stdlib だけで組む必然。 |
| D4 | ver16.1 RESEARCH §結論 Q2 / F1 | `build_command` は `-r` / `--session-id` を既に仕様どおり使い分け済。deferred resume の CLI 側呼び出し構造は本版で変更不要（出力 format 付与のみ）。 |

---

## 結論

各問いに対し「確定（3 ソース以上 or 一次資料で spec 定義） / 部分的（1–2 ソースのみ） / 未確定（実験待ち）」で判定する。

### Q1 `--output-format json` の戻り値構造

**確定**（A6 + A7 + B1 + B3 + B4 の 5 本、うち 4 本が一次資料）。

- `claude -p "<prompt>" --output-format json` は **stdout に単一 JSON object（改行なし or 末尾 \n 1 個）** を返す（A6 の `jq -r '.session_id'` が成立していることから「1 object」が前提、`result.session_id` ではなく top-level `.session_id` で取れることも確定）。
- その object は **`SDKResultMessage` 型と互換**の以下フィールドを含む（B1 の TS 型定義が一次典拠）:
  ```
  {
    "type": "result",
    "subtype": "success" | "error_...",
    "uuid": "<uuid>",
    "session_id": "<uuid>",
    "duration_ms": <int>,
    "duration_api_ms": <int>,
    "is_error": <bool>,
    "num_turns": <int>,
    "result": "<string>",           // success のみ
    "stop_reason": "<string> | null",
    "total_cost_usd": <float>,
    "usage": {
      "input_tokens": <int | null>,
      "output_tokens": <int | null>,
      "cache_creation_input_tokens": <int | null>,
      "cache_read_input_tokens": <int | null>
    },
    "modelUsage": {
      "<modelName>": {
        "inputTokens": <int>,
        "outputTokens": <int>,
        "cacheReadInputTokens": <int>,
        "cacheCreationInputTokens": <int>,
        "webSearchRequests": <int>,
        "costUSD": <float>,
        "contextWindow": <int>,
        "maxOutputTokens": <int>
      }
    },
    "permission_denials": [...]
  }
  ```
- **success / error どちらの subtype でも `usage` / `total_cost_usd` / `modelUsage` が揃う**（B2 + B8）。欠測が発生するのは「`--output-format json` を付けなかった step」「CLI が panic して JSON を吐けなかった step」等のエッジに限定。
- IMPLEMENT §1-1 の `StepCost` TypedDict の 4 token field 名（`input_tokens` / `output_tokens` / `cache_read_input_tokens` / `cache_creation_input_tokens`）は **B3 の SDK 型と 1:1 で一致**。→ 命名変更不要、そのまま採用。

### Q2 取得経路の代替候補

**確定**。Q1 の公式経路（`--output-format json`）が `total_cost_usd` / `usage` / `modelUsage` を直接提供するため、IMPLEMENT §0 U1 が列挙していた「代替経路 B (stderr JSON) / C (sidecar) / D (API 経由)」は本版で **fallback 扱いでよい**。追加発見として:

- **Claude CLI 自身が内部で cost を tracking**（A4 `--max-budget-usd` の存在）。API 経由で re-compute するまでもない。
- `stream-json` 経路（A2 / A8）でも最終 event（`type: "result"` と推定、B1 と同 spec の末尾 event）から同じ `total_cost_usd` が取れる見込み。ただし「stream-json の最終 event が `SDKResultMessage` そのものか」は公式 docs で明言されていないため **Q5 経由で EXPERIMENT 実測に回す**（§U6-b）。
- API 経由（`platform.claude.com/docs/en/build-with-claude/usage-cost-api`、B6）は authoritative billing 用途で、retrospective 根拠には over-engineering。本版スコープ外。

結論: **本版の主経路は `--output-format json`**。stream-json は U6 実験結果で live streaming を保ったまま cost を取る必要があれば移行を検討する（落とす判断も可）。

### Q3 価格表と price book version

**確定、ただし方針を update**。

- **最大の方針変更**: IMPLEMENT §1-1 の「PRICE_BOOK を自前保持し `calculate_cost` で計算する」を **primary strategy から降ろし**、primary は「`SDKResultMessage.total_cost_usd` / `modelUsage[*].costUSD` をそのまま記録」に切り替える（B5 / B6 の「client-side estimate」と本版の retrospective 用途が整合、B8 の「always read from result」が強い根拠）。
  - メリット: 「どの価格表で計算したか」は実質「使った Claude Code CLI のバージョン」で特定できる（B5 の「bundled at build time」）。我々が自前で version 管理する必要がない。
  - `price_book_version` フィールドは残すが、値を **`claude_code_cli_version`** に改名候補（`claude --version` 相当の文字列。例: `"2.0.31"`）。実値は EXPERIMENT で `claude --version` 出力を 1 回採取して `costs.py` に書く実装案。
- **PRICE_BOOK は fallback 用途で残す**（`modelUsage` / `total_cost_usd` が欠落 or null、もしくは SDK が未知モデルで cost を 0 / undefined にしたケース）。C1 の 2026-04-24 公式表を hardcode する。cache の 5m / 1h 区別は SDK 側で情報落ちする（B4 の `ModelUsage` は cache write を 1 本にまとめている）ため、**fallback 計算時は「cache write は 5m 相当の単価で計算」で近似**する（実運用では cache write の大多数は 5m。長時間 cache は contextual caching で別途指定時のみ発生）。
- cache read / cache write の料金 tier は **C2 + B9 で公式整合**。fallback 計算時の token key 対応:
  - `input_tokens` × `base_input` 単価
  - `output_tokens` × `output` 単価
  - `cache_read_input_tokens` × `cache_hits` 単価
  - `cache_creation_input_tokens` × `cache_writes_5m` 単価（5m/1h 区別不能時の仮定）
- 2026-04-24 時点の PRICE_BOOK 具体値（C1）:

  ```python
  # scripts/claude_loop_lib/costs.py
  CLAUDE_CODE_PRICE_BOOK_SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing retrieved 2026-04-24"
  PRICE_BOOK_USD_PER_MTOK: dict[str, dict[str, float]] = {
      # alias 'opus' / 'sonnet' / 'haiku' は最新世代（4.5 以降）に解決する運用。
      # 具体 model-id は claude_code が modelUsage で返すキー名に合わせる必要があり、EXPERIMENT で 1 回確認する。
      "claude-opus-4-7": {"input": 5.0, "cache_write_5m": 6.25, "cache_write_1h": 10.0, "cache_read": 0.50, "output": 25.0},
      "claude-opus-4-6": {"input": 5.0, "cache_write_5m": 6.25, "cache_write_1h": 10.0, "cache_read": 0.50, "output": 25.0},
      "claude-sonnet-4-6": {"input": 3.0, "cache_write_5m": 3.75, "cache_write_1h": 6.0, "cache_read": 0.30, "output": 15.0},
      "claude-haiku-4-5":  {"input": 1.0, "cache_write_5m": 1.25, "cache_write_1h": 2.0, "cache_read": 0.10, "output": 5.0},
  }
  ```

  `/imple_plan` は本 dict の先頭行（source + 日付）と key 一覧を `costs.py` に移植する。**fallback 経路は「`modelUsage` が欠落したときに近似値を提示する」用途**であり、primary は `total_cost_usd` の raw 記録。

### Q4 deferred execution 経路での cost 分離

**確定**。

- 各 `claude` CLI invocation が独立した result message を吐き、独立した `total_cost_usd` を持つ（B7）。→ `kind="claude"`（本発話）と `kind="deferred_resume"`（deferred 完了後の resume）は **別 record として独立 cost 加算**でよい。IMPLEMENT §1-3 の「足し合わせ vs 別列」の二択は「別列（= 別 record）」で確定。
- 外部コマンド（`kind="deferred_external"`）は Claude token を消費しないため `usage=None` / `cost_usd=0.0`（欠測扱いではなく明示 0）で run total に加算。SDK の `costUSD` 概念とは独立なので `StepCost.status="ok"` + `cost_usd=0.0` が自然。
- `num_turns` / `duration_api_ms` / `duration_ms` も result に含まれる（B1）ため、`StepCost` に `num_turns` / `duration_api_ms` を追加保持するかは `/imple_plan` で判断（retrospective で「API 側時間 vs. clock 時間」比較に使えるため残す価値あり、ただし scope 拡大）。**仮決め: `num_turns` のみ追加、`duration_api_ms` は見送り**（retrospective で必要性が出たら追う）。

### Q5 `--output-format json` と live streaming の両立

**部分的 → 実験に委ねる（§U6-a / §U6-b）**。

- 一次資料範囲で確定できたこと:
  - `--output-format json` は **single-shot 結果返却**（A6/A7 の example が `jq` で 1 object をパースしている＝stream ではない）。→ 実行中は stdout サイレントの可能性が高い。
  - `--output-format stream-json` は **NDJSON stream**（A8/A9 の spec）。stream event には `session_id` / `uuid` / `type` / `subtype` が揃い、`--include-partial-messages` で delta まで拾える。
- 未確定な点（EXPERIMENT §U6 で実測）:
  - A) `--output-format json` を付けたときに「実行中の tee 出力が完全に消える」のか「human-readable + 末尾 JSON の混合」になるのか。
  - B) `--output-format stream-json` の最終 event が `SDKResultMessage` 型と同じ構造で `total_cost_usd` / `usage` / `modelUsage` を含むか（docs は Q1 の result 型を stream-json 側でも使う前提で書かれているが、CLI が stream の末尾で改めて result event を emit するかは実測が必要）。
  - C) stream-json を採用した場合、`tee.write_process_output` に「各 event を 1 行として tee + 最終 result event を buffer」する最小差分実装が組めるか。

判断ゲート（IMPLEMENT §0 §U6 に既に書かれている A/B/C/D 選択肢の再整理）:

- **A (json, 実行中サイレント)**: `_execute_single_step` で output を buffer → 終了後 `json.loads` → live log は「実行中サイレント、終了時に `.result` 本文を人間可読に整形して tee」という挙動に切替。
- **B (stream-json + 最終 result event)**: tee は各 event を 1 行としてそのまま流し、`type=="result"` の event だけ buffer。live streaming を保てる。実装は A より重いが retrospective 上の観察性が高い。
- **C (hybrid)**: 公式 docs に記載なし。採用可能性は低いが EXPERIMENT で否定的に確認することで A/B の選択理由を強化できる。
- **D (JSON 経路そのものが使えない)**: Q1 の確定度合い（B1 の型定義が SDK reference に掲載済）から **起こりえない**。本 RESEARCH で **D は棄却**して良い。

**推奨デフォルト**: まず **A (`--output-format json`)** で最小実装し、live streaming が「実行中サイレント」で retrospective 的に耐えがたい場合のみ **B (`stream-json`)** に切替。理由:

- `StepCost` は 1 step = 1 result で十分（B8 の「per-assistant dedup 不要、result 参照で OK」）
- `_execute_single_step` の差分が最小（stdout buffer + 末尾 `json.loads` のみ）
- stream-json は tee を線形拡張できるが、「各 event を改行で 1 行として tee」は event text 本文に改行が含まれるケースで line 粒度が壊れる。単純な text 出力より可読性が下がる恐れあり
- ただし「実行中サイレント」が運用上厳しいと判明したら B に移行する（EXPERIMENT §U6 判定次第）

### まとめ: IMPLEMENT.md §0 への影響

| 論点 | 本 RESEARCH での更新 |
|---|---|
| U1 (取得経路) | **確定**。`--output-format json` 単一経路で `total_cost_usd` / `usage` / `modelUsage` / `session_id` / `duration_ms` / `num_turns` が 1 object で取れる。`parse_usage_from_claude_output` の実装は「single JSON `json.loads` → top-level の 4 key を拾う」で OK。 |
| U2 (価格表) | **方針転換**。PRICE_BOOK 自前計算を primary から降ろし、primary は `total_cost_usd` raw 記録 + `claude_code_cli_version` 保持。PRICE_BOOK は fallback として残す（C1 の値を `costs.py` に hardcode、出典日付コメント付）。 |
| U3 (deferred 分離) | **確定**。別 record として独立 cost 加算。`kind="claude" \| "deferred_resume" \| "deferred_external"` の 3 値で OK。`num_turns` を `StepCost` に追加することを推奨。 |
| U6 (live stream) | **部分的 → 実験**。A (json 単発) 案を primary に、B (stream-json) を fallback に設定。判定は EXPERIMENT 側で実測。 |

---

## 未解決点

EXPERIMENT.md (`/experiment_test`) で確かめる仮説を列挙する。`experiments/cost-usage-capture/` 配下に配置（PLAN_HANDOFF §後続 step への注意点 §3 準拠、先頭コメントに削除条件「PHASE8.0 §3 U1/U6 確認用、ver16.2 完了後削除可」）。

### §U1-a. `--output-format json` の実出力サンプル採取（Q1 の実測裏取り）

- **仮説**: `claude --bare -p "1+1=?" --output-format json` は stdout に single JSON object を吐き、`total_cost_usd` / `usage.input_tokens` / `usage.output_tokens` / `usage.cache_read_input_tokens` / `usage.cache_creation_input_tokens` / `modelUsage` / `session_id` / `duration_ms` / `num_turns` を含む。
- **検証手順**: `experiments/cost-usage-capture/single-shot-json/run.sh`（または `.ps1`）で `claude --bare -p "1+1=?" --output-format json` を 1 回実行し、stdout / stderr を file に保存 → `json.loads` で parse → 上記 key の有無と型を assert。
- **判定基準**:
  - **成功** → IMPLEMENT §1-1 `parse_usage_from_claude_output` の prototype（`json.loads(raw) → return result.get("usage")`）をそのまま採用。
  - **部分成功**（一部 key が無い） → RESEARCH.md §結論 Q1 の型仕様との diff を EXPERIMENT.md に明記し、`/imple_plan` が `StepCost` TypedDict の該当 field を `Optional` にする判断。
  - **失敗**（JSON 形式ですらない / single-shot ではない） → stream-json 経路（§U6-b）に primary を振り替え。

### §U1-b. `modelUsage` のキー名 / alias 解決の実測（Q3 の実測補強）

- **仮説**: `modelUsage` のキーは `claude_opus_4_7` のような内部コード名ではなく、Anthropic 公式 model ID（例: `claude-opus-4-7`）そのもの。PRICE_BOOK の key と 1:1 で対応できる。
- **検証手順**: §U1-a で採取した JSON から `modelUsage` の key 一覧を抽出。既定 model（CLAUDE.md 記載の Opus 4.7）で走らせた場合と `--model sonnet` / `--model haiku` 指定の場合で計 3 回採取し、key 名をリスト化。
- **判定基準**:
  - 公式 pricing page（C1）の model 名と snake-case / kebab-case の変換規則さえ確認できれば PRICE_BOOK のキー設計が固まる。
  - 仮に `modelUsage` がそもそも absent になる状況があれば（例: `--bare` で model 情報が落ちる等）、RESEARCH §結論 Q3 の primary / fallback 分岐を再評価。

### §U6-a. `--output-format json` の live stdout 挙動（Q5 の実測 A / B / C 判定）

- **仮説**: `--output-format json` は「実行中サイレント、終了時に single JSON」（A 案）の挙動。
- **検証手順**: `experiments/cost-usage-capture/live-stream-compare/run.sh` で同一 prompt を `--output-format json` / `--output-format stream-json --verbose` / `--output-format stream-json --verbose --include-partial-messages` の 3 variant 実行し、stdout を行ベースで採取（開始 / 中間 / 終了の行数・1 行目受信までの elapsed）。
- **判定基準**:
  - json variant が 1 行だけ返る → A 確定 → IMPLEMENT §1-3 の「buffer + `json.loads`」案採用。
  - json variant が複数行になる、あるいは human-readable + 末尾 JSON 混合 → C（hybrid）確定 → 最小改修で済む。
  - stream-json variant が `type: "result"` の最終 event に `total_cost_usd` / `usage` / `modelUsage` を含む → B が使えると確定。primary を B に振り替えるかは retrospective コスト比で判断。

### §U6-b. `stream-json` 最終 event の構造確認（Q5 の B 案の裏取り）

- **仮説**: `--output-format stream-json` の NDJSON の最終行（または末尾近く）に `SDKResultMessage` 相当（`type: "result"`, `subtype: "success"`, `total_cost_usd`, `usage`, `modelUsage`）の event が現れる。
- **検証手順**: §U6-a で採取した stream-json の最終 20 行を grep で抽出し、`type == "result"` の event を探す。見つかった event を `json.loads` で parse し、RESEARCH §結論 Q1 で列挙した key set と一致するか確認。
- **判定基準**:
  - 一致 → B 案が実用化可能。`/imple_plan` は A/B のトレードオフで最終決定（live streaming の優先度次第）。
  - 不一致 or `type: "result"` event が出ない → B 棄却。A 案確定。

### §U6-c. 欠測を意図的に起こす（U5 欠測表現の実装確認）

- **仮説**: `--output-format` を付けなかった step（= 既定 `text`）は JSON として parse 不能で `parse_usage_from_claude_output` が `None` を返し、`StepCost.status="unavailable"` が付く。
- **検証手順**: `experiments/cost-usage-capture/missing-usage/run.sh` で `claude --bare -p "1+1=?"`（`--output-format` なし）を 1 回実行し、stdout を `json.loads` に渡すと `JSONDecodeError` が raised されることを確認。
- **判定基準**: 予定通り raise → `parse_usage_from_claude_output` で try/except → `return None` パターンが機能することを裏付け。EXPERIMENT.md §判断 に「欠測は `JSONDecodeError` を握って None 返し、呼び出し側で `status="unavailable"` / `reason="non-json-output"` を付ける」と明記。

### §U7. `claude --version` の出力形式確認（Q3 の `claude_code_cli_version` 保持のため）

- **仮説**: `claude --version` は `"2.x.y"` 形式の 1 行を返し、そのまま `StepCost.claude_code_cli_version` フィールドに保存可能。
- **検証手順**: `claude --version` を `experiments/cost-usage-capture/cli-version/run.sh` で 1 回実行し、stdout の行数 / 形式を採取。
- **判定基準**:
  - single line で semver っぽい → そのまま採用。version は run 開始時に 1 回採取して `RunCostSummary` に格納（step 毎の保持は冗長なので `run` 単位）。
  - 複数行 or 非 semver → EXPERIMENT.md に samplewr 書き、`/imple_plan` が parse 規則を追加判断。

---

## 参考: 本 RESEARCH で「調査不要」と判断した IMPLEMENT §0 項目

- **§U4 cost sidecar の保存先**: 実装判断のみで外部調査不要と IMPLEMENT.md §0 に明示済。`logs/workflow/{stem}.costs.json`（log と stem 共有）案を `/imple_plan` 段で確定。`.gitignore` 状況は `/experiment_test` が副次確認（`experiments/cost-usage-capture/missing-usage/` 側で触れる）。
- **§U5 欠測表現**: 実装判断のみで外部調査不要と IMPLEMENT.md §0 に明示済。`{"status": "unavailable", "reason": "<str>"}` 方式を `/imple_plan` 段で確定。欠測を意図的に起こす実機確認は §U6-c で副次取得。

---

## 付録: 本 RESEARCH の採録・棄却 URL リスト

**PRIMARY（一次資料として結論に採録）**:

- https://code.claude.com/docs/en/cli-reference (A1–A5, A の主要部)
- https://code.claude.com/docs/en/headless (A6–A9)
- https://code.claude.com/docs/en/agent-sdk/typescript (B1–B4, B10)
- https://code.claude.com/docs/en/agent-sdk/cost-tracking (B5–B9)
- https://platform.claude.com/docs/en/about-claude/pricing (C1–C4)

**SECONDARY / 未採録（ノイズ or 重複）**:

- https://blakecrosley.com/guides/claude-code — 二次情報、結論に採録不要
- https://shipyard.build/blog/claude-code-cheat-sheet/ — 二次情報、重複
- https://github.com/anthropics/claude-code/issues/24594 — `stream-json` 周辺の community issue、公式 docs（A8/A9）で代替可
- https://www.eesel.ai/blog/claude-code-cli-reference — 二次情報、公式 A1 で代替可
- https://github.com/ollama/ollama/issues/15529 — Ollama local model の話で本件と無関係
- 価格系二次 blog（metacto / evolink / finout / ssdnodes / silicondata） — C1（公式 pricing page）で完全代替可
