---
workflow: quick
source: issues
---

# ver16.7 IMPLEMENT — deferred-resume-twice-verification harness 整備

## 変更ファイル一覧

| ファイル | 操作 |
|---|---|
| `experiments/deferred-execution/resume-twice/run_experiment.sh` | 新規作成 |
| `experiments/deferred-execution/resume-twice/RESULTS_TEMPLATE.md` | 新規作成 |
| `experiments/deferred-execution/resume-twice/README.md` | 編集（harness 起動方法・人手実行前提の明記を追記） |

コード（`scripts/` / `server/` / `app/`）の変更ゼロ。

## run_experiment.sh の実装内容

- CLI: `./run_experiment.sh [--with-bare|--without-bare|--both]`（デフォルト: `--both`）
- 1 周分の処理（`run_session` 関数）:
  1. `python -c "import uuid; print(uuid.uuid4())"` で session id 採番
  2. 発話1: `kiwi42` 記憶（`--session-id` 指定）
  3. 発話2: resume（`-r <session_id>`）
  4. 発話3: 観測トークン想起（`-r <session_id>`）→ stdout に `kiwi42` が含まれるか grep
  5. 各発話の実行時間（ms）・終了コード・token usage（`jq .usage`）をログ出力
- ログ出力先: `experiments/deferred-execution/resume-twice/logs/{YYYYMMDD_HHMMSS}_{with|without}_bare.log`
- `--bare` あり を先に実行（比較基準を先に固めるため、PLAN_HANDOFF §quick_impl 指定通り）
- `--help` で使用方法を表示

## RESULTS_TEMPLATE.md の構成

- §U3 履歴継承: `kiwi42` 出現有無・終了コード・session_id 一致確認（with_bare / without_bare 各 1 セット）
- §U2 --bare 採否: (1) 応答成功可否、(2) 実行時間差、(3) token 流入量差、(4) CLAUDE.md 参照痕跡（主観）
- 判定欄（ver16.8 以降の `/issue_plan` 向け総合判断枠）

## 判断・乖離の記録

ROUGH_PLAN の計画通り実装。乖離なし。
