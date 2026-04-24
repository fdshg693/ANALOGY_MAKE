---
workflow: quick
source: issues
---

# ver16.7 CHANGES — deferred-resume-twice-verification harness 整備

前バージョン ver16.6 からの変更差分。

## 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---|---|---|
| `experiments/deferred-execution/resume-twice/run_experiment.sh` | **追加** | §U2/§U3 実測用 bash harness スクリプト |
| `experiments/deferred-execution/resume-twice/RESULTS_TEMPLATE.md` | **追加** | §U2/§U3 判定用の観測項目記入テンプレート |
| `experiments/deferred-execution/resume-twice/README.md` | **編集** | harness 起動方法・人手実行前提を追記 |

コード（`scripts/` / `server/` / `app/`）の変更ゼロ。

## 変更内容の詳細

### `run_experiment.sh`（新規）

`claude -p` + `claude -r` の 3 発話シーケンス（記憶→resume→想起）を自動化する bash harness。

- **CLI**: `./run_experiment.sh [--with-bare|--without-bare|--both]`（デフォルト: `--both`）
- **実行順**: `--bare` ありを先に実行（比較基準を先に固めるため）
- **1 周の処理内容**:
  1. `python -c "import uuid; print(uuid.uuid4())"` で session id を採番
  2. 発話1: 観測トークン `kiwi42` を記憶させる（`--session-id` 指定）
  3. 発話2: 同一 session id で resume（`-r`）して別プロンプトを投入
  4. 発話3: 同一 session id で再 resume し、観測トークンの想起を要求 → stdout を grep して §U3 判定
  5. 各発話の実行時間（ms）・終了コード・token usage（`jq .usage`）を標準出力 + ログファイルに記録
- **ログ出力先**: `experiments/deferred-execution/resume-twice/logs/{YYYYMMDD_HHMMSS}_{with|without}_bare.log`（初回実行時に自動 mkdir）

### `RESULTS_TEMPLATE.md`（新規）

§U2（`--bare` 採否）/ §U3（履歴継承）判定に必要な観測項目の記入枠。

- **§U3 セクション**: 観測トークン出現有無・終了コード・session_id 一致確認（with_bare / without_bare 各 1 セット）
- **§U2 セクション**: (1) 応答成功可否、(2) 実行時間差、(3) token 流入量差、(4) CLAUDE.md 参照痕跡（主観判定）+ 総合判定欄
- 記入後の手順（ver16.8 以降の `/issue_plan` に渡すまでのステップ）を末尾に明記

### `README.md`（編集）

ver16.2 草稿の手動手順をそのまま保持しつつ、以下を追記:

- **⚠️ 人手実行前提セクション**: nested CLI 観測バイアス回避のため `claude_loop.py` / workflow YAML 経由での自動呼び出しを明示禁止
- **harness スクリプトの使い方セクション**: 前提条件・実行コマンド・実行手順・ログ出力先
- 既存の草稿部分は「参考」として保持

## API変更

なし。

## 技術的判断

- **言語: bash（Python 不採用）**: PLAN_HANDOFF の推奨通り、既存草稿が bash コマンド列で書かれており移植コストが最小。実行環境は WSL / Git Bash で整っている
- **ISSUE `deferred-resume-twice-verification` は `ready/ai` 据え置き**: 人手実測 + ver16.8 以降での判定完了が done/ 移動の条件
- **`_execute_resume()` / `build_resume_prompt()` は未変更**: 実測結果が出るまで判断保留（ver16.8 以降で確定）
