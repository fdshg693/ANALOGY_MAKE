# §U6-c — 欠測（`--output-format` 未指定）の parse 挙動

## 状態

**未検証（本版 ver16.2 では `/experiment_test` SKILL 制約により実走せず、先送り）**

## 先送り理由

nested `claude -p` 禁止。1 回だけの短い実行だが、本版の「nested 禁止」ガードは LLM 呼び出しの有無（料金・時間）ではなく `--session-id` 衝突と観測バイアスが根拠であり、1 回でも違反となる。

## 参考: `json.loads` が非 JSON を拒否する挙動自体は Python 標準の仕様

本 SKILL 制約を回避するため、LLM 呼び出しなしで「非 JSON 文字列を `json.loads` に渡すと `json.decoder.JSONDecodeError` が raise される」ことだけは `EXPERIMENT.md §U6-c` に記載する（Python stdlib の規定動作、実機確認不要）。

```python
>>> import json
>>> json.loads("hello world")
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

従って `parse_usage_from_claude_output` の try/except パターンは Python の規定挙動だけで成立する。**仮説 §U6-c 本体（実機で `--output-format` なし実行が human-readable を返すこと）は未検証だが、parse 側の fallback 経路自体は Python stdlib 契約上担保されている**。

## 再開手順草稿

### 手順

1. `run.sh`（未作成）:
   ```bash
   #!/usr/bin/env bash
   # 何を確かめるためか: §U6-c — `--output-format` なしの claude -p 実行が
   #                     非 JSON 出力を返し、json.loads が JSONDecodeError を raise
   #                     する経路が実機でも機能することを確認する。
   # いつ削除してよいか: ver16.3 以降で EXPERIMENT.md §U6-c が実機結果で埋まり、
   #                     `StepCost.status="unavailable"` の fallback が確定したら削除可。
   set -euo pipefail
   claude --bare -p "1+1=?" > out.txt 2> stderr.log
   python - <<'PY'
   import json
   with open("out.txt") as f: raw = f.read()
   try:
       json.loads(raw)
       print("UNEXPECTED: parsed as JSON")
   except json.JSONDecodeError as e:
       print(f"OK: JSONDecodeError raised: {e}")
   PY
   ```
2. 出力を `EXPERIMENT.md §U6-c` に貼付

### 判定基準（RESEARCH.md §U6-c より）

- 予定通り `JSONDecodeError` → `parse_usage_from_claude_output` の try/except → `return None` を確定
- JSON parse が通る → RESEARCH 結論を再点検（想定外）
