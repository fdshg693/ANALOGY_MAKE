# §U1-a — `--output-format json` 実出力サンプル採取

## 状態

**未検証（本版 ver16.2 では `/experiment_test` SKILL 制約により実走せず、先送り）**

## 先送り理由

本ループは `research` workflow の中で `/experiment_test` SKILL が `claude -p` subprocess として同期実行されている。その内側でさらに `claude -p "1+1=?" --output-format json` を呼ぶと:

1. **`--session-id` 衝突**: 親 workflow が `--session-id` で保持している session に子呼び出しが紛れ込む恐れ
2. **観測バイアス**: ver16.1 で導入した deferred execution 機構がまだ本番発動していない中、その機構を使わない経路で nested 呼び出しを行うと、本版 §3 の設計判断（deferred 経路で cost を取る方針）を歪める
3. **同期 5 分境界**: `claude -p` の 1 往復は数十秒オーダーで、短い prompt でも 3 variant × 3 model = 9 回走らせるとルーチン的に 5 分境界を越える

SKILL `experiment_test` の手順書も同旨のガードを明記している（該当節: 「やらないこと / nested `claude` の subprocess 起動」）。

## 再開手順草稿（次バージョン ver16.3 以降）

### 前提

- ver16.2 で `costs.py` の primary 経路が「`--output-format json` を付与 → stdout 全量を `json.loads`」で確定している
- ver16.2 で deferred execution が本番発動した実績があり、次ループ開始時には deferred 経路から本実験を走らせる素地がある

### 手順

1. 本ディレクトリ直下に `run.sh` を作成（未作成）:
   ```bash
   #!/usr/bin/env bash
   # 何を確かめるためか: §U1-a — `--output-format json` stdout が SDKResultMessage 互換の
   #                     single JSON object を返すこと、および usage/total_cost_usd/modelUsage
   #                     の 4 key が揃うことを確認する。
   # いつ削除してよいか: ver16.3 以降で検証が EXPERIMENT.md に記録され、
   #                     `scripts/tests/test_costs.py` に fixture 移植されたら削除可。
   set -euo pipefail
   claude --bare -p "1+1=?" --output-format json > stdout.json 2> stderr.log
   echo "--- exit=$?" >> stderr.log
   python - <<'PY'
   import json, sys
   with open("stdout.json") as f:
       data = json.load(f)
   for k in ("type","subtype","session_id","total_cost_usd","usage","modelUsage","num_turns","duration_ms"):
       print(f"{k}: {'present' if k in data else 'ABSENT'}")
   PY
   ```
2. 実行: `bash experiments/cost-usage-capture/single-shot-json/run.sh`
3. 出力 `stdout.json` / `stderr.log` を `EXPERIMENT.md §U1-a` に貼付
4. 4 key (`usage` / `total_cost_usd` / `modelUsage` / `session_id`) の有無と型を検証

### 判定基準（RESEARCH.md §U1-a より）

- 成功 → `parse_usage_from_claude_output` の prototype をそのまま採用
- 部分成功（一部 key 無し）→ `StepCost` TypedDict の該当 field を `Optional` に
- 失敗（JSON でない / single-shot でない）→ stream-json 経路（§U6-b）に primary 振替

## 実走時の注意

- 本実験の実走時、環境変数 `ANTHROPIC_API_KEY` か Claude Code のログイン状態が必要
- 課金額は `--bare -p "1+1=?"` で 1¢ 未満の見込みだが、3 variant × 3 model を全部回すと 10¢ オーダー
