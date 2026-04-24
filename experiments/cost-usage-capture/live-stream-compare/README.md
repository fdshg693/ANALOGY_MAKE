# §U6-a — `--output-format json` の live stdout 挙動

## 状態

**未検証（本版 ver16.2 では `/experiment_test` SKILL 制約により実走せず、先送り）**

## 先送り理由

nested `claude -p` 禁止が本ループでは崩せない。本仮説は 3 variant (`json` / `stream-json --verbose` / `stream-json --verbose --include-partial-messages`) の live stdout を line 単位で採取する必要があり、全 variant で実時間計測するため時間コストも大きい。

## 再開手順草稿

### 手順

1. `run.sh`（未作成）:
   ```bash
   #!/usr/bin/env bash
   # 何を確かめるためか: §U6-a — `--output-format json` が実行中サイレントか、
   #                     human-readable + 末尾 JSON 混合か、stream-json variant で
   #                     live stdout が保てるかを比較する。
   # いつ削除してよいか: ver16.3 以降で live streaming の primary/fallback 判断が
   #                     確定し EXPERIMENT.md に記録されたら削除可。
   set -euo pipefail
   for v in "--output-format json" "--output-format stream-json --verbose" "--output-format stream-json --verbose --include-partial-messages"; do
     slug=$(echo "$v" | tr -d '- ' | tr ' ' '_')
     # 1 行目到着までの elapsed を ts で計測（gnu coreutils の `ts` 不在なら awk で置換）
     # shellcheck disable=SC2086
     { time claude --bare -p "Explain recursion briefly" $v | awk '{ printf "[%d.%06d] %s\n", systime(), systime(), $0 }' > "out-${slug}.log" ; } 2> "time-${slug}.log"
   done
   ```
2. 各 variant の `out-*.log` から:
   - 行数
   - 1 行目到着までの経過時間（`time-*.log` と併読）
   - JSON 形式か human-readable か
   を採取し `EXPERIMENT.md §U6-a` に貼付

### 判定基準（RESEARCH.md §U6-a より）

- json variant が 1 行だけ → A 確定（primary: buffer + json.loads）
- json variant が複数行 or 混合 → C（hybrid）検討
- stream-json variant の最終 event に usage が含まれる → B 採用可（§U6-b と併せ判定）
