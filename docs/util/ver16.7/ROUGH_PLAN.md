---
workflow: quick
source: issues
---

# ver16.7 ROUGH_PLAN — `deferred-resume-twice-verification` 用の人手実測 harness 準備

## 位置づけ

minor 版。ver16.1 PHASE8.0 §2 で実装した deferred execution の resume 経路（同一 session id で 2 回 `claude -r` を実行した際の履歴継承）と、`_execute_resume()` における `--bare` 採用可否を外部シェルで実測するための **harness を本版で整備する**。実測そのものは AI の nested CLI 実行が観測バイアスを持つため人手作業に委ねるが、実行コマンド列・結果記録テンプレが毎回手作業になっている現状を解消する。

## バージョン種別

**マイナー（ver16.7）**。コード変更ゼロ（`scripts/` / `server/` / `app/` は touch しない）、追加対象は `experiments/deferred-execution/resume-twice/` 配下のみ。アーキテクチャ変更 / 新規外部依存 / 破壊的変更いずれもなし。メジャー昇格条件に該当しない。

## ワークフロー選択

**`quick`**。根拠:

- 選定 ISSUE は `ready/ai` のみ（`review/ai` を含まず、`full` 強制条件に該当せず）
- MASTER_PLAN 新項目 / アーキ変更 / 新規外部ライブラリ導入のいずれにも該当しない（`research` 必要条件の前提を満たさない）
- 実装は `experiments/deferred-execution/resume-twice/` 配下の 3 ファイル以内（harness 本体 + 結果テンプレ + README 微修正）、計 100 行以下の見込み
- 既存 `experiments/` 規約（ver16.0 §1）に従うだけで新規運用ルール策定は不要

## 着手対象 / スコープ

### 実施する

1. `experiments/deferred-execution/resume-twice/` に **人手実測用の harness スクリプト**を 1 本追加する（bash または Python、言語は後続 `/quick_impl` で確定）
   - `claude -p "..." --session-id <uuid>` 起動 → `claude -p "..." -r <uuid>` 2 回分 → 最後に履歴継承確認の 3 回目、という README.md §検証する際の手順草稿 を忠実に自動化
   - `--bare` ありパス と `--bare` なしパス の 2 周を同一スクリプトで連続実行可能にする（`--with-bare` / `--without-bare` 相当の CLI 切替）
   - 出力・終了コード・実行時間を標準出力 + ログファイルに記録する
2. `experiments/deferred-execution/resume-twice/RESULTS_TEMPLATE.md` を新規作成し、§U2（`--bare` 採否）/ §U3（履歴継承）判定に必要な観測項目（`kiwi42` など想定トークンの出現有無・総実行時間・token 流入量・CLAUDE.md 再注入の痕跡）を事前に枠として用意
3. `experiments/deferred-execution/resume-twice/README.md` に (a) harness スクリプトの起動方法、(b) RESULTS_TEMPLATE.md への記入ルート、(c) **人手実行前提である旨（nested CLI 観測バイアス回避）** を追記
4. 実測結果の AI による解釈・判定・コード変更（`_execute_resume` の `--bare` 採否確定 / `build_resume_prompt` 調整）は **ver16.8 以降の別版に持ち越す**旨を ROUGH_PLAN 末尾・RESULTS_TEMPLATE.md 双方に明記

### 実施しない

- **実測実行そのもの**: AI の workflow loop 内で `claude -p` を nested に起動することは観測バイアスの元（ISSUE §RESEARCH.md §A6・IMPLEMENT.md §5-5）。本版の AI タスクは harness の整備まで
- **`_execute_resume()` / `build_resume_prompt()` の実装変更**: 実測結果が出るまで判断保留
- **`ISSUES/util/medium/deferred-resume-twice-verification.md` の done/ 移動**: 人手実測 + ver16.8 以降での判定完了まで ready/ai で据え置き
- **`issue-review-rewrite-verification`（medium, ready/ai）**: 他カテゴリで `review/ai` ISSUE が発生しない限り観察機会ゼロ、本版未着手
- **`toast-persistence-verification`（low, ready/ai）**: Windows 実機目視必須で AI 単独消化不能（医療的には harness 化が可能だが本版は優先度 medium を先に消化）
- **`issue-review-7day-threshold-observation`（low, ready/ai）**: 本日時点で §1.5 発火対象ゼロ、時間経過観察継続
- **`raw/ai` 2 件の review 昇格**: ver16.6 PLAN_HANDOFF で「ver16.7 時点で昇格ルート整備検討」の示唆があったが、本版は medium ready/ai 消化を優先する SKILL ルール（high→medium→low）に従い、meta 改善は ver16.8 以降の候補として温存
- **PHASE9.0 骨子作成**: PHASE8.0 完走済だが、既存 ready/ai が 4 件あり MASTER_PLAN ガイドライン 1（既存 ISSUES 消化優先）に従い次 PHASE 着手は見送り

## 想定成果物

- `docs/util/ver16.7/ROUGH_PLAN.md`（本ファイル）
- `docs/util/ver16.7/PLAN_HANDOFF.md`
- `docs/util/ver16.7/IMPLEMENT.md`（`/quick_impl` 生成、~30 行規模）
- `docs/util/ver16.7/CHANGES.md`（`/write_current`）
- `docs/util/ver16.7/MEMO.md`（`/wrap_up`、任意）
- `experiments/deferred-execution/resume-twice/run_experiment.sh` または `run_experiment.py`（1 本）
- `experiments/deferred-execution/resume-twice/RESULTS_TEMPLATE.md`
- `experiments/deferred-execution/resume-twice/README.md`（微修正）

## 事前リファクタリング要否

**不要**。既存 `experiments/deferred-execution/resume-twice/` には README.md 1 ファイルのみが存在し、refactor 対象のコード・スクリプトが存在しない。新規ファイル追加のみで完結。

---

## ISSUE レビュー結果

- `review/ai` → `ready/ai` に遷移: 0 件（対象ファイルなし）
- `review/ai` → `need_human_action/human` に遷移: 0 件
- 追記した `## AI からの依頼`: 0 件

## ISSUE 状態サマリ

| status / assigned | 件数 |
|---|---|
| ready / ai | 4 |
| review / ai | 0 |
| need_human_action / human | 0 |
| raw / human | 0 |
| raw / ai | 2 |

内訳:

- **ready / ai (4)**: `issue-review-rewrite-verification` (medium), `deferred-resume-twice-verification` (medium), `toast-persistence-verification` (low), `issue-review-7day-threshold-observation` (low)
- **raw / ai (2)**: `rules-paths-frontmatter-autoload-verification`, `scripts-readme-usage-boundary-clarification`

## 選定理由・除外理由

### 選定: `deferred-resume-twice-verification`（medium, ready/ai）

- 優先度順（high → medium → low）で medium ready/ai 2 件のうち、**AI 単独で前進可能**なのは本 ISSUE のみ。harness 整備という分離可能な前段作業が明確に存在する
- もう 1 件の medium `issue-review-rewrite-verification` は他カテゴリ（`app` / `infra`）で `review/ai` ISSUE が発生する外部契機待ちで、本版時点で AI からの能動的前進余地なし
- PHASE8.0 §2 deferred execution は ver16.1 で実装後、本番経路での初回発火が観測されていない。harness を先行整備しておくことで、次に deferred が走ったとき / human が気付いたときにその場で実測 → 判定が可能となる保険としての価値が高い

### 除外 ISSUE

| ISSUE | 除外理由 |
|---|---|
| `issue-review-rewrite-verification` (medium) | 他カテゴリで `review/ai` ISSUE が発生しない限り観察機会ゼロ、AI 能動消化不可 |
| `toast-persistence-verification` (low) | priority 低、かつ medium ready/ai 消化を優先（SKILL ルール high→medium→low） |
| `issue-review-7day-threshold-observation` (low) | 本日時点で §1.5 発火対象ゼロ、時間経過観察継続 |
| `rules-paths-frontmatter-autoload-verification` (raw/ai) | triage 据え置き継続（ver16.3〜ver16.6 の 4 ループ同様）、本版も medium ready/ai を優先 |
| `scripts-readme-usage-boundary-clarification` (raw/ai) | 同上 |
| PHASE9.0 骨子作成 | MASTER_PLAN ガイドライン 1 に従い既存 ready/ai 消化優先、PHASE 未着手は維持 |

---

## 再判定推奨 ISSUE

該当なし（`ready/ai` で 7 日以上停滞している ISSUE はない）。

※ 参考（本日 2026-04-25 時点の ready/ai 4 件の `reviewed_at` 経過日数）:

- `issue-review-rewrite-verification` — reviewed_at: 2026-04-23（2 日経過）
- `deferred-resume-twice-verification` — reviewed_at: 2026-04-24（1 日経過）
- `toast-persistence-verification` — reviewed_at: 2026-04-24（1 日経過）
- `issue-review-7day-threshold-observation` — reviewed_at: 2026-04-25（0 日経過）

初回発火予測: `issue-review-rewrite-verification` が 2026-04-30 以降で閾値 7 日に到達（途中で `review/ai` に差し戻されなければ）。F-1 観察継続。
