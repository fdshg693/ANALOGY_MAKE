# resume-twice/ — 未検証 (ver16.2 以降)

**目的**: RESEARCH.md §U2 (`--bare` を `_execute_resume` で採用すべきか) / §U3 (同一 session id への 2 回目 `-r` が前回終了後に安全であることの実測) を nested claude CLI 呼び出しで検証する。

**未検証理由**:
- IMPLEMENT.md §5-5「本 run の `/research_context` / `/experiment_test` step 自体が deferred を発動することは禁じる」。`/experiment_test` 内で `claude -r <id>` を呼ぶと、親 workflow が使っている session と衝突 / 観測バイアス発生のリスクがある。
- 同期実行の 5 分制約にも抵触しやすい（`claude -p` 1 回 = 数十秒〜、× 3〜4 呼び）。
- ver16.1 で deferred execution 機構が実装された後、その外部経路（`DEFERRED/` 経由）で走らせるのが正統。

## ⚠️ 人手実行前提（nested CLI 観測バイアス回避）

本ディレクトリの harness スクリプトは **AI workflow（`claude_loop.py` / workflow YAML）経由での自動呼び出しを禁止** します。
AI が claude CLI を nested に呼び出すと、親セッションとの衝突・文脈汚染による観測バイアスが生じるためです（IMPLEMENT.md §5-5 / docs/util/ver16.1/RESEARCH.md §A6 参照）。

**必ず WSL / Git Bash で手動実行してください。**

## harness スクリプトの使い方

### 前提条件

- WSL または Git Bash 環境
- `claude` CLI がパスに通っている
- `jq` がインストールされている
- Python 3 が使える（UUID 生成に使用）

### 実行コマンド

```bash
cd experiments/deferred-execution/resume-twice

# --bare あり/なし の両方を連続実行（デフォルト、推奨）
./run_experiment.sh

# --bare あり のみ
./run_experiment.sh --with-bare

# --bare なし のみ
./run_experiment.sh --without-bare

# ヘルプ
./run_experiment.sh --help
```

### 実行手順

1. 上記コマンドで `./run_experiment.sh` を実行（`--both` がデフォルト）
2. `logs/YYYYMMDD_HHMMSS_with_bare.log` と `logs/YYYYMMDD_HHMMSS_without_bare.log` が生成される
3. ログファイルを参照しながら `RESULTS_TEMPLATE.md` の各欄を埋める
4. 記入後、`ISSUES/util/medium/deferred-resume-twice-verification.md` にサマリを追記
5. ver16.8 以降の `/issue_plan` で判定・コード変更が行われる

### ログ出力先

```
experiments/deferred-execution/resume-twice/logs/
  YYYYMMDD_HHMMSS_with_bare.log
  YYYYMMDD_HHMMSS_without_bare.log
```

## 検証する際の手順草稿（harness 化前の草稿、参考）

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
