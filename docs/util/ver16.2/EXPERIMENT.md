---
workflow: research
source: master_plan
---

# ver16.2 EXPERIMENT — PHASE8.0 §3 token/cost 計測 実験

`/experiment_test` で実施した実験の成果物。`RESEARCH.md §未解決点` の仮説 6 件（§U1-a / §U1-b / §U6-a / §U6-b / §U6-c / §U7）に対し、**SKILL 制約（nested `claude -p` 禁止）**により LLM 呼び出しを伴う 5 件は **`未検証`** 扱いとし、nested LLM を伴わない §U7（`claude --version`）のみ実機で確定させた。先送り 5 件は `experiments/cost-usage-capture/{slug}/README.md` に再開手順草稿を残した（`/experiment_test` SKILL 「やらないこと」§3 準拠）。

参照日は全て **2026-04-24**。

---

## 検証した仮説

`RESEARCH.md §未解決点` からそのまま引き写し、各仮説に「成功条件」と「本版での実走可否」を併記する。

### §U1-a. `--output-format json` の実出力サンプル採取

- **仮説**: `claude --bare -p "1+1=?" --output-format json` は stdout に single JSON object を吐き、`total_cost_usd` / `usage.input_tokens` / `usage.output_tokens` / `usage.cache_read_input_tokens` / `usage.cache_creation_input_tokens` / `modelUsage` / `session_id` / `duration_ms` / `num_turns` を含む。
- **成功条件**: 9 key すべて present、型が RESEARCH §結論 Q1 の TS 型と整合。
- **本版での実走**: **なし**。nested `claude -p` が SKILL 制約で禁止のため。

### §U1-b. `modelUsage` のキー名 / alias 解決の実測

- **仮説**: `modelUsage` の key は kebab-case の Anthropic 公式 model ID（例: `claude-opus-4-7`）そのもので、PRICE_BOOK の key と 1:1 対応。
- **成功条件**: 3 model（既定 / `--model sonnet` / `--model haiku`）で採取した key が kebab-case model ID。
- **本版での実走**: **なし**（§U1-a と同じ理由）。

### §U6-a. `--output-format json` の live stdout 挙動

- **仮説**: `--output-format json` は「実行中サイレント、終了時に single JSON」（A 案）挙動。
- **成功条件**: json variant が 1 行だけ返り、1 行目到着時刻 ≒ 実行終了時刻。
- **本版での実走**: **なし**（nested `claude -p` 禁止 + 5 分同期境界への接近）。

### §U6-b. `stream-json` 最終 event の構造確認

- **仮説**: `--output-format stream-json` の NDJSON 末尾近くに `type:"result"` event が出現し、`total_cost_usd` / `usage` / `modelUsage` を含む。
- **成功条件**: RESEARCH §結論 Q1 の key set と完全一致。
- **本版での実走**: **なし**（§U6-a の出力が前提で、§U6-a が未実走のため連鎖的に未実走）。

### §U6-c. 欠測を意図的に起こす

- **仮説**: `--output-format` 未指定の出力は非 JSON で、`json.loads` が `JSONDecodeError` を raise する。
- **成功条件**: `JSONDecodeError` が raised される。
- **本版での実走**: **なし**。ただし Python stdlib の規定挙動として「非 JSON 文字列に対し `json.loads` が `JSONDecodeError` を raise する」ことは仕様上担保されている点のみ確認（下記「結果 §U6-c」参照）。

### §U7. `claude --version` の出力形式確認

- **仮説**: `claude --version` は `"2.x.y"` 形式の 1 行を返し、そのまま `StepCost.claude_code_cli_version`（あるいは `RunCostSummary.claude_code_cli_version`）に保存可能。
- **成功条件**: single line、semver っぽい先頭トークン。
- **本版での実走**: **あり**（LLM 呼び出しなし、`--session-id` 衝突なし、5 分境界無関係）。

---

## 再現手順

### §U7（本版で実走）

- 実行コマンド: `bash experiments/cost-usage-capture/cli-version/run.sh`（中身は `claude --version` の 1 行）
- 前提条件: Claude Code CLI がログイン済で PATH に `claude` がある
- 必要な環境変数: なし
- 使用ファイル:
  - `experiments/cost-usage-capture/cli-version/run.sh`
  - `experiments/cost-usage-capture/cli-version/output.txt`（実行結果）

### §U1-a / §U1-b / §U6-a / §U6-b / §U6-c（未検証）

本版では実走していないが、後続バージョンで実行するための **再開手順草稿** を `experiments/cost-usage-capture/{slug}/README.md` に配置した。再開経路 3 案（deferred execution 経路で自動 / ユーザー手動で shell 実行 / 次版 `/experiment_test` で再実行）を `experiments/cost-usage-capture/README.md` に整理済。

- `experiments/cost-usage-capture/single-shot-json/README.md`（§U1-a）
- `experiments/cost-usage-capture/modelusage-keys/README.md`（§U1-b）
- `experiments/cost-usage-capture/live-stream-compare/README.md`（§U6-a）
- `experiments/cost-usage-capture/stream-json-final-event/README.md`（§U6-b）
- `experiments/cost-usage-capture/missing-usage/README.md`（§U6-c）

各 README には本版で実走しなかった理由と、`run.sh` の草稿コマンド、判定基準（RESEARCH §未解決点からの引き写し）が記載されている。

---

## 結果

### §U7（実走）

**コマンド**:

```
$ claude --version
```

**stdout**:

```
2.1.117 (Claude Code)
```

**exit code**: `0`

**観察**:

- 出力は **1 行のみ**、末尾改行 1 個。
- フォーマット: `<semver> (Claude Code)` の 2 トークン。`<semver>` は **厳密な 3 要素 semver**（`MAJOR.MINOR.PATCH`）で、サフィックスなし（pre-release / build meta なし）。
- 括弧内リテラル `(Claude Code)` は固定文字列と推定（今回の観測では 1 回のみのため確信度中）。

**検証対象のバージョン・日付**: CLI version `2.1.117`、採取日 2026-04-24。本版 ROUGH_PLAN / RESEARCH の参照日と整合。

**`costs.py` への示唆**:

- 保持するフィールド名は RESEARCH §結論 Q3 で提案された `claude_code_cli_version` のまま採用可。
- parse 規則は「stdout の 1 行目を whitespace で split した先頭トークン」（例: `"2.1.117"`）を保存。括弧内の `"(Claude Code)"` は冗長なので捨てる方針を推奨（retrospective 上 semver 比較だけ出来れば十分）。
- `RunCostSummary`（run 単位）で 1 回採取するだけで十分。step 毎の保持は冗長（RESEARCH §結論 Q3 の判断と整合）。

### §U1-a / §U1-b / §U6-a / §U6-b（未検証）

本版では実走していない。RESEARCH §結論 Q1 / Q2 / Q3 / Q5 は **Anthropic 公式 CLI docs（A1–A9）/ Agent SDK TypeScript reference（B1–B10）/ 公式 pricing page（C1–C4）** という一次資料 3 本立て（計 23 引用）で spec 定義レベルの確定がついている。

従って `/imple_plan` は:

- **primary path**: RESEARCH 結論をそのまま信用して実装に進む（`SDKResultMessage` 互換の JSON object が `--output-format json` で返る前提）
- **fallback path**: `costs.py` の `parse_usage_from_claude_output` に `try/except json.JSONDecodeError` を置き、万一 spec と実機が乖離した場合に `StepCost.status="unavailable"` を返す経路で受け止める（§U5 の欠測表現と同経路）

で進める。実機サンプル採取は ver16.2 §3 完走後の最初の workflow run で自然に発生する（本番 usage JSON が `logs/workflow/*.costs.json` に残る）ため、その時点で RESEARCH 仕様との突合を retrospective で行えば実質的に §U1-a / §U1-b の裏取りになる。

### §U6-c（未検証、ただし stdlib 契約上担保）

`--output-format` 未指定の claude 実走はしていないが、**Python 標準ライブラリの契約として**:

```python
>>> import json
>>> json.loads("hello world")
Traceback (most recent call last):
  ...
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

が raise されることは確定（`json` module の規定挙動、CPython / PyPy 共通）。従って `parse_usage_from_claude_output` の `try/except json.JSONDecodeError: return None` 経路は Python 契約だけで機能する。実機で `--output-format` なし実行が **本当に非 JSON を返すか**（例: 万一仕様変更で素の JSON を吐くようになっていないか）は未検証だが、RESEARCH §結論 Q1 の A1（「`--output-format` の options: `text`, `json`, `stream-json`」）と A6–A8（`text` 既定時は human-readable）から、`text` が JSON を返す可能性は spec 上ない。

---

## 判断

### §U7 — `claude --version` の扱い: **確定**

- `RunCostSummary.claude_code_cli_version` に `"2.1.117"` 相当の semver 文字列を保存する方針で `/imple_plan` に進める。
- parse は「stdout 1 行目の whitespace split 先頭トークン」。括弧以降は捨てる。
- 採取タイミング: run 冒頭で 1 回だけ `claude --version` を subprocess 実行（LLM 呼び出しではないので本 SKILL 制約の対象外）。

### §U1-a / §U1-b / §U6-a / §U6-b — 取得経路・key 名・live 挙動: **未検証（SKILL 制約による先送り）**

- 本版で実走していない。RESEARCH §結論（公式 docs 一次資料 3 本立て）の確定度合いを primary として `/imple_plan` に進む。
- 次アクション: ver16.2 で `costs.py` の primary 経路を「`--output-format json` 付与 → `json.loads`」で実装し、本番 workflow run の 1 回目で取得された実 JSON を **retrospective で spec 突合** する。spec 乖離が見つかった場合は ver16.3 相当で修正。
- deferred execution 経路が本番発動する ver16.2 以降は、次版の `/experiment_test` で `experiments/cost-usage-capture/{slug}/README.md` 記載の再開手順から実走可能になる見込み。

### §U6-c — 欠測の parse 経路: **実装に使える形で担保（実機未検証）**

- Python stdlib 契約で `JSONDecodeError` が raise されることは確定。実装の `try/except` 経路は spec 上成立。
- 実機での「`--output-format` なしが非 JSON を返すこと」自体は未検証だが、CLI docs の `--output-format` 定義（A1）と `text` 既定の example（A7 が `--output-format json` を明示的に付ける）から逆算すると高確度で非 JSON。

### §実装方式の確定 / 却下

| 論点 | 本版での結論 |
|---|---|
| **primary 取得経路** | `--output-format json` 付与 → stdout 全量 `json.loads` → top-level key 取得（RESEARCH §結論 Q1 に追従、実機未検証） |
| **fallback 取得経路** | `try/except json.JSONDecodeError` → `return None`、呼び出し側で `StepCost.status="unavailable"` / `reason="non-json-output"` を付与（Python stdlib 契約で担保） |
| **PRICE_BOOK の位置づけ** | `modelUsage[*].costUSD` / `total_cost_usd` を primary、PRICE_BOOK は `modelUsage` 欠落時のみ使う fallback（RESEARCH §結論 Q3 追従） |
| **`claude_code_cli_version` の保持** | run 単位で 1 回 `claude --version` を実行し、semver 先頭トークンを保存（本版 §U7 で実機確定済） |
| **deferred 経路の cost 分離** | `kind="claude" \| "deferred_resume" \| "deferred_external"` の 3 値で別 record 保持、`num_turns` を `StepCost` に追加（RESEARCH §結論 Q4 追従） |
| **live streaming primary / fallback** | primary = `--output-format json`（A 案）、実行中サイレントが運用上耐えがたいと判明した時点で `stream-json`（B 案）へ振替。本版での実機判定はできないため `/imple_plan` は A 案で進める |

### §未検証項目の再検証タイミング

- ver16.2 §3 の最初の本番 workflow run（`/wrap_up` または次版 `/split_plan` 相当）で `logs/workflow/*.costs.json` に実データが溜まる
- `/retrospective` SKILL が RESEARCH §結論 Q1/Q3 の spec と実機 JSON を突合（実質的な §U1-a / §U1-b の裏取り）
- 乖離があれば ver16.3 で `parse_usage_from_claude_output` 修正 + 本 EXPERIMENT の追記

---

## 付録: 本版で実走しなかった理由（SKILL 制約の要約）

`/experiment_test` SKILL は `research` workflow 内で `claude -p` subprocess として同期実行されているため、そこから更に `claude -p "..."` を起動すると:

1. `--session-id` 衝突（親 workflow の session に子呼び出しが紛れる恐れ）
2. 観測バイアス（ver16.1 deferred execution 機構の本番発動前に、その機構を経由しない nested 呼び出しをしてしまうと、本版 §3 の設計判断を歪める）
3. 同期 5 分境界（1 往復数十秒 × 複数 variant × 複数 model で確実に接近）

の 3 重リスクが発生する。SKILL 本体の「やらないこと」§3 に同旨のガードが明記されており、該当仮説は **実走させず `未検証` 扱いで先送り**、`deferred execution 経路が本番発動する次バージョン以降に回す**、と書かれている。本 EXPERIMENT はこれに準拠。
