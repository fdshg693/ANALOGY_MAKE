# resume-twice/ — 未検証 (ver16.2 以降)

**目的**: RESEARCH.md §U2 (`--bare` を `_execute_resume` で採用すべきか) / §U3 (同一 session id への 2 回目 `-r` が前回終了後に安全であることの実測) を nested claude CLI 呼び出しで検証する。

**未検証理由**:
- IMPLEMENT.md §5-5「本 run の `/research_context` / `/experiment_test` step 自体が deferred を発動することは禁じる」。`/experiment_test` 内で `claude -r <id>` を呼ぶと、親 workflow が使っている session と衝突 / 観測バイアス発生のリスクがある。
- 同期実行の 5 分制約にも抵触しやすい（`claude -p` 1 回 = 数十秒〜、× 3〜4 呼び）。
- ver16.1 で deferred execution 機構が実装された後、その外部経路（`DEFERRED/` 経由）で走らせるのが正統。

**検証する際の手順草稿** (ver16.2 以降で実施):

1. 新規 uuid を採番: `NEW_ID=$(python -c "import uuid; print(uuid.uuid4())")`
2. 初回発話:
   ```bash
   claude --bare -p "私は実験のために 'kiwi42' を記憶してください。" --session-id "$NEW_ID" --output-format json | jq -r '.session_id'
   ```
3. 2 回目 (同 id で resume、別プロンプト):
   ```bash
   claude --bare -p "次の step に進みます。処理を続けてください。" -r "$NEW_ID"
   ```
4. 3 回目 (履歴継承確認):
   ```bash
   claude --bare -p "先ほど記憶をお願いした単語を答えてください。" -r "$NEW_ID"
   ```
   出力に `kiwi42` が含まれれば §U3 PASS。
5. `--bare` なしで 1〜4 を再実施し、応答品質・実行時間を比較 → §U2 判定。

**削除条件**: ver16.2 以降で本手順の実測が完了し、`scripts/claude_loop_lib/deferred_commands.py::_execute_resume` の `--bare` 採用可否が確定した時点で削除。
