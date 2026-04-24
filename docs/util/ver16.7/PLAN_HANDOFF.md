---
workflow: quick
source: issues
---

# ver16.7 PLAN_HANDOFF

## 関連 ISSUE / 関連ファイル

### 関連 ISSUE

- `ISSUES/util/medium/deferred-resume-twice-verification.md` — 本版主眼、harness 整備後も `ready/ai` 据え置き（人手実測 + ver16.8 以降の判定完了で初めて done/ 移動）
- `ISSUES/util/low/issue-review-7day-threshold-observation.md` — F-1 観察継続、本版は未発火で追加アクションなし

### 関連ファイル（本版で新規作成 / 編集）

- `experiments/deferred-execution/resume-twice/README.md` — 既存（ver16.2 草稿、1 ファイル 28 行）。本版で harness 起動方法と人手実行前提の明記を追記
- `experiments/deferred-execution/resume-twice/run_experiment.sh` または `run_experiment.py` — **本版で新規作成**。言語選択は `/quick_impl` で確定（既存 `experiments/` 配下の他 harness の流儀と `scripts/.claude/rules/scripts.md` の規約に合わせる）
- `experiments/deferred-execution/resume-twice/RESULTS_TEMPLATE.md` — **本版で新規作成**。§U2 / §U3 判定に必要な観測項目の枠

### 関連ファイル（参照のみ、本版は編集なし）

- `scripts/claude_loop_lib/deferred_commands.py` — `_execute_resume` / `build_resume_prompt` の現行実装（`--bare` なし）。本版は touch なし
- `scripts/claude_loop.py::_process_deferred` — deferred 経路の resume 呼び出し箇所。本版は touch なし
- `docs/util/ver16.1/IMPLEMENT.md` §5-1 — 履歴継承失敗時の fallback 設計（新規 session id + 履歴明示貼付）。harness 整備でこの fallback の要否が測れるようになる
- `docs/util/ver16.1/RESEARCH.md` §Q1 / §A1〜§A6 — 一次資料裏取り済みの前提知識
- `docs/util/ver16.1/EXPERIMENT.md` §U2 / §U3 / §U2-note — 「未検証」のまま残っている EXPERIMENT。本版の harness 実測でこれを埋める前提

## 後続 step への注意点

### /quick_impl

- harness スクリプトの言語選択
  - 第一候補: **bash (`run_experiment.sh`)**。README.md 既存の草稿が bash コマンド列で書かれており、`jq` 依存も既に想定済み。移植コストが最小
  - 第二候補: **Python (`run_experiment.py`)**。`scripts/` 規約（`.claude/rules/scripts.md`）に従うなら標準ライブラリ + PyYAML のみ、`subprocess` + `pathlib.Path` の最小実装。プロジェクトの既存 Python harness（`experiments/01-basic-connection.ts` 等は TS なので参考外）と揃える価値は薄いが、Windows 実行時の `bash` 前提回避という利点はある
  - **推奨: bash**。既存草稿をそのまま harness 化するほうがレビュー負荷が低く、実行環境は WSL / Git Bash で既に整っている
- harness 構造（bash を選んだ場合）
  - CLI: `./run_experiment.sh [--with-bare|--without-bare|--both]`。`--both` がデフォルト
  - 1 周分の処理: (a) `uuidgen` or `python -c "import uuid; print(uuid.uuid4())"` で new session id 採番、(b) 第 1 発話（`kiwi42` のような観測トークンを記憶させる）、(c) 第 2 発話（resume）、(d) 第 3 発話（観測トークン想起）→ 出力に含まれるか grep で確認、(e) 各発話の実行時間と終了コードをログ
  - ログ出力先: `experiments/deferred-execution/resume-twice/logs/{YYYYMMDD_HHMMSS}_{with|without}_bare.log`（ディレクトリは初回実行時に mkdir）
- `--bare` あり/なしの周回順序は `--bare` **あり** を先にする（ver16.1 未採用側の動作確認が主目的のため、比較基準を先に固めたい）
- **nested CLI 観測バイアス回避のため、本 harness を `claude_loop.py` / workflow YAML 経由で自動呼び出ししてはならない**。README.md にもこの制約を明示的に書き残すこと
- RESULTS_TEMPLATE.md の観測項目（最低限）
  - §U3 履歴継承: 第 3 発話の stdout に観測トークン（`kiwi42`）が含まれたか Yes/No、各発話の session_id 一致
  - §U2 `--bare` 採否: `--bare` あり/なしでの (1) 応答成功可否、(2) 実行時間差、(3) token 流入量差（`--output-format json` の `.usage` から），(4) CLAUDE.md 参照有無（応答品質の主観判定枠）
- **完了条件（本版の scope 完了判定）**: harness スクリプトが local で `--help` 実行に成功し、RESULTS_TEMPLATE.md のセクション構成が §U2 / §U3 両判定に必要な項目を網羅している、まで。実測データの記入は human 作業で本版 scope 外
- `imple_plan effort 下げ試行`（ver16.5 handoff §2、ver16.6 PLAN_HANDOFF 末尾で「ver16.7 以降で full ワークフローかつ実装量小ケースが出た際に再試行」と handoff されていた）は本版 quick のため対象外。次に `full` で実装量小のケースが出た版に再度 handoff する

### /write_current

- CHANGES.md のみ作成（minor）
- 必須記載: (a) harness 新設 2 ファイル（スクリプト + テンプレ）+ README 更新、(b) コード（`scripts/` / `server/` / `app/`）変更ゼロ、(c) ISSUE は `ready/ai` 据え置きで done/ 移動なし（人手実測と ver16.8 以降の判定完了が前提）
- 前版 ver16.6 との差分は「`experiments/deferred-execution/resume-twice/` に 2 ファイル追加 + README 編集」

### /wrap_up

- MEMO.md は任意。書くなら以下を記録:
  - harness 完成後の **人手実行タスク**: 開発者が WSL / Git Bash で `./run_experiment.sh --both` を実行 → RESULTS_TEMPLATE.md に結果記入 → ver16.8 以降の `/issue_plan` で拾い直し判定
  - `--bare` 採否の判定が出たら `scripts/claude_loop_lib/deferred_commands.py::_execute_resume` の修正 or 現状維持を ver16.8+ の主眼として起票する
  - 本版で `deferred-resume-twice-verification.md` を done/ へは移動しない（人手実測分が未完）
- F-1 閾値妥当性は本版も未発火のため追加アクションなし。次版 handoff で継続観察項目として引き継ぐ
- `raw/ai` 2 件の停滞は ver16.3 から本版まで 5 ループ据え置き継続。ver16.8 以降で meta 改善（ver16.5 §1.5 同型の `raw/ai` 長期停滞 review 昇格ルート）起案の優先度を一段上げる旨、handoff に明記する

### raw/ai 2 件の停滞観察（継続記録）

- `rules-paths-frontmatter-autoload-verification` / `scripts-readme-usage-boundary-clarification` は ver16.3 から本版まで **5 ループ連続据え置き**（ver16.3 / 16.4 / 16.5 / 16.6 / 16.7）
- ver16.5 handoff では「3 ループ停滞で昇格ルート整備検討」とあったが、本版で既に 5 ループ目。ver16.6 handoff と同じ温度感で ver16.8 以降へ handoff する
- 具体案: ver16.5 §1.5 と同型で、`issue_review` SKILL に「`raw/ai` で N 日（例: 14 日）以上 triage されていない ISSUE を review 昇格候補として列挙する」ルートを追加する meta 改善版を、次に medium ready/ai が尽きた版で起案

### §1.5 予測 vs 実績の整合性記録（ver16.5 handoff §3 からの継続事項）

- **予測**（ver16.6 完了時点で自然継承された状態）: ready/ai 4 件すべて `reviewed_at < 7 日` → §1.5 出力「該当なし」
- **実績**（本 ROUGH_PLAN §再判定推奨 ISSUE）: 該当ゼロ、列挙 ISSUE 0 件、「該当なし」1 行出力
- **整合判定**: 予測通り（2 サンプル目: ver16.6 に続き本版でも §1.5 書式の「該当ゼロ版」が安定出力されることを確認）。F-1 ISSUE の「2 版（ver16.7 相当）経過後も未発火 → 閾値調整の後続 ISSUE を起票」の期限に本版が到達。次版 /wrap_up で F-1 閾値調整 ISSUE 起票を検討対象に含める
