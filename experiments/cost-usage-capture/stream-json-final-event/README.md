# §U6-b — `stream-json` 最終 event の構造確認

## 状態

**未検証（本版 ver16.2 では `/experiment_test` SKILL 制約により実走せず、先送り）**

## 先送り理由

`live-stream-compare/` の実走が前提で、同じく nested `claude -p` 禁止により先送り。

## 再開手順草稿

### 手順

1. `live-stream-compare/out-stream_json_verbose.log` を入力として使う（再実行は不要）
2. `run.sh`（未作成、純 parse スクリプト）:
   ```bash
   #!/usr/bin/env bash
   # 何を確かめるためか: §U6-b — stream-json の末尾に SDKResultMessage 互換の
   #                     `type:"result"` event が出現し、total_cost_usd/usage/modelUsage
   #                     が揃うか確認する。
   # いつ削除してよいか: ver16.3 以降で live streaming primary/fallback 判定が
   #                     確定し EXPERIMENT.md に記録されたら削除可。
   set -euo pipefail
   INPUT="../live-stream-compare/out-stream_json_verbose.log"
   tail -n 20 "$INPUT" \
     | grep -F '"type":"result"' \
     | head -n 1 \
     | python -c "import json,sys;line=sys.stdin.read().strip();print() if not line else [print(f'{k}: {\"present\" if k in json.loads(line) else \"ABSENT\"}') for k in ('type','subtype','total_cost_usd','usage','modelUsage','session_id','num_turns')]"
   ```

### 判定基準（RESEARCH.md §U6-b より）

- `type:"result"` event が見つかり RESEARCH §結論 Q1 の key set と一致 → B 案が使える（primary 振替は retrospective cost 比で判断）
- `type:"result"` event がない / key 不一致 → B 棄却、A 案確定
