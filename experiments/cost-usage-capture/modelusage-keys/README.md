# §U1-b — `modelUsage` キー名 / alias 解決の実測

## 状態

**未検証（本版 ver16.2 では `/experiment_test` SKILL 制約により実走せず、先送り）**

## 先送り理由

`single-shot-json/README.md` §先送り理由と同じ。nested `claude -p` 禁止が本ループでは崩せない。加えて本仮説は **3 model（既定 Opus 4.7 / `--model sonnet` / `--model haiku`）× 2 短 prompt** の採取が必要で、5 分境界により確実に衝突する。

## 再開手順草稿

### 前提

- `single-shot-json/` の実走が済んでいること（同経路で JSON を吐く前提確認）

### 手順

1. `run.sh`（未作成）:
   ```bash
   #!/usr/bin/env bash
   # 何を確かめるためか: §U1-b — `modelUsage` の key が Anthropic 公式 model ID
   #                     (kebab-case, 例: "claude-opus-4-7") そのものか確認し、
   #                     PRICE_BOOK の key 設計を確定する。
   # いつ削除してよいか: ver16.3 以降で EXPERIMENT.md への反映が済んだら削除可。
   set -euo pipefail
   for m in "" "--model sonnet" "--model haiku"; do
     slug=$(echo "$m" | tr -d '- ' | tr ' ' '_'); slug=${slug:-default}
     # shellcheck disable=SC2086
     claude --bare -p "1+1=?" --output-format json $m \
       | tee "modelusage-${slug}.json" \
       | python -c "import json,sys;d=json.load(sys.stdin);print(list((d.get('modelUsage') or {}).keys()))"
   done
   ```
2. 3 回の出力から `modelUsage` の key 一覧を抽出し、`EXPERIMENT.md §U1-b` に貼付
3. C1 pricing page の model 名と key 名の変換規則を確認

### 判定基準（RESEARCH.md §U1-b より）

- key が kebab-case model ID → PRICE_BOOK の key 設計を同形式で確定
- `modelUsage` absent になるケースがあれば fallback 分岐を再評価
