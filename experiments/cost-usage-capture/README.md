# experiments/cost-usage-capture/

**目的**: ver16.2 PHASE8.0 §3（token/cost 計測）着手前の、Claude CLI `--output-format json` / `stream-json` 出力の実測サンプル採取と、欠測・version 出力の挙動確認。

**いつ削除してよいか**: ver16.2 (PHASE8.0 §3) が完走し、`scripts/claude_loop_lib/costs.py` の parse 経路が確定して `scripts/tests/test_costs.py` に fixture が移植された後。それまで残す。

## 本バージョンでの実行状況サマリ

`/experiment_test` SKILL の明示制約「nested `claude` / `claude -r` / `claude -p` の subprocess 起動は禁止」に従い、本ループ内では **LLM 呼び出しを伴う仮説は実走させず、`EXPERIMENT.md` 側で `未検証` 扱い**とした（該当: §U1-a / §U1-b / §U6-a / §U6-b / §U6-c）。

実走したのは §U7 (`claude --version`) のみ。これは LLM 呼び出しを伴わず、`--session-id` 衝突・同期 5 分境界・観測バイアスのいずれのリスクも発生しないため安全に実測できる。

| 仮説 | 本版で実走したか | 状態 | 参照 |
|---|---|---|---|
| §U1-a `--output-format json` 出力構造 | No | 未検証 | `single-shot-json/README.md` |
| §U1-b `modelUsage` key 名 | No | 未検証 | `modelusage-keys/README.md` |
| §U6-a live stdout 挙動 | No | 未検証 | `live-stream-compare/README.md` |
| §U6-b stream-json 最終 event 構造 | No | 未検証 | `stream-json-final-event/README.md` |
| §U6-c 欠測（`--output-format` なし）の parse 挙動 | No | 未検証 | `missing-usage/README.md` |
| §U7 `claude --version` 出力形式 | **Yes** | 確定 | `cli-version/` |

## 各仮説を次バージョンで再開する方法

LLM 呼び出しを伴う仮説（§U1-a/b, §U6-a/b/c）を実走させるには、以下のいずれかの経路が必要:

1. **ver16.1 deferred execution 経路での実走**: `scripts/claude_loop.py` の deferred 機構がユーザー主導のセッションから発火する initial run の内側でこれらのスクリプトを走らせる。`/experiment_test` の subprocess 内ではない
2. **`/experiment_test` の外部での手動実行**: ユーザーが通常 shell から `experiments/cost-usage-capture/{slug}/run.sh`（または `.ps1`）を直接実行し、出力を file に保存。後続バージョンの `/experiment_test` が結果 file を読み取って `EXPERIMENT.md` を埋める
3. **ver16.2 完走後、次版の `/experiment_test` で再実行**: ver16.2 で `costs.py` が確定すれば、同版完走後に次版（ver16.3 相当）で検証可能。ただしそのときには実装が完了しているため、検証は「後追いの裏取り」になる

どの経路でも、各 slug の `README.md` に書かれている「再開手順」を参照する。
