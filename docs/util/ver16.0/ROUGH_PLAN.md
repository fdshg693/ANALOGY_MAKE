---
workflow: full
source: master_plan
---

# ver16.0 ROUGH_PLAN — PHASE8.0 §1 `research` workflow 新設

## バージョン種別

**メジャー（ver16.0）**。MASTER_PLAN `PHASE8.0` の最初の節（§1 調査・実験を挟む実装 workflow 追加）に着手する。新 workflow の追加（`quick | full` から `quick | full | research` への拡張）、新 SKILL の新設（`research_context` / `experiment_test`）、新 YAML（`claude_loop_research.yaml`）、新 artifact（`RESEARCH.md` / `EXPERIMENT.md`）を伴うアーキテクチャ変更のため、メジャーバージョンとして扱う。

## ISSUE 状態サマリ（util カテゴリ）

| priority | ready/ai | review/ai | need_human_action/human | raw/ai | raw/human |
|---|---|---|---|---|---|
| high | 0 | 0 | 0 | 0 | 0 |
| medium | 1 | 0 | 0 | 0 | 0 |
| low | 1 | 0 | 0 | 2 | 0 |

`review/ai` が 0 件のため、本ループの ISSUE レビューフェーズは no-op（state 遷移なし）。

## ISSUE レビュー結果

- 走査対象: util カテゴリ全件
- `review/ai` 件数: 0
- 状態遷移: なし（`ready/ai` への昇格 0 件、`need_human_action/human` への振り分け 0 件）

## 着手対象（スコープ）

MASTER_PLAN `PHASE8.0` §1 に着手し、**実装前に調査・実験を正式 step として挿入できる新 workflow `research` を追加する**。現行の `quick` / `full` と並列に置かれる第 3 の実装 workflow として定義し、`--workflow auto` の自動選択肢も `quick | full | research` へ拡張する。

### 実施する

1. **`research` workflow の新設（8 step 構成）** — `/issue_plan → /split_plan → /research_context → /experiment_test → /imple_plan → /wrap_up → /write_current → /retrospective` を定義する。現行 `full` の `/split_plan` と `/imple_plan` のあいだに調査・検証 step が差し込まれる形。

2. **新 SKILL 2 件の追加** — 調査 step `/research_context`（`use-tavily` を前提にした実装前調査、成果を `RESEARCH.md` に残す）と、検証 step `/experiment_test`（`experiments/` 配下での再現・性能・CLI 試行、成果を `EXPERIMENT.md` に残す）を新設する。

3. **`--workflow auto` 選定条件の拡張** — `/issue_plan` SKILL で `workflow: research` を選定できるよう条件を明文化する。「外部仕様 / 公式 docs 確認が主要成果に影響する」「実装方式を実験で絞り込む必要がある」「長時間コマンドを使った検証が前半で必要」「軽い隔離環境での試行が前提」のいずれかを含む課題を対象とする。

4. **`experiments/` ディレクトリ運用ルールの明文化** — 既存依存で足りる場合はそのまま利用、新しい依存が必要な場合は `experiments/` 配下に閉じる、残すスクリプトには「何を確かめるためか」「いつ削除してよいか」をファイル先頭コメントで記載する、といったルールを `experiments/README.md` に明文化する。

5. **`question` / `research` の責務境界の明示** — 「実装しない調査」=`question` / 「実装前調査」=`research` の境界を docs / SKILL / README で明記する。

ユーザーから見た変化:
- `--workflow research` で明示起動可能になり、auto 選択でも該当課題に `research` が割り当てられる
- 実装前調査 / 実験結果が `RESEARCH.md` / `EXPERIMENT.md` として version フォルダに残り、後続の `/imple_plan` から再利用できる
- `experiments/` にスクリプトを残す際の規約が明示され、保守対象化しにくくなる

### 実施しない

- **PHASE8.0 §2（長時間コマンド deferred execution）** — ver16.1 に切り出す。本バージョンでは `research` workflow の「器」の整備に集中し、長時間コマンドの外部実行・resume 機構は扱わない。§1 完了条件には「§2 のような長時間検証も本 workflow 上で自然に組み込める」ことが含まれるため、将来の接続点は意識しつつも実装はしない。
- **PHASE8.0 §3（step 単位 token/cost 計測）** — ver16.2 に切り出す。本バージョンでは cost 可視化は扱わない。
- **`toast-persistence-verification.md`（low）** — Windows 実機目視検証が必須で AUTO / ヘッドレス前提では完結しない。継続持ち越し。
- **`issue-review-rewrite-verification.md`（medium）** — util 単体消化不能（`app` / `infra` カテゴリ起動待ち）。継続持ち越し。
- **`rules-paths-frontmatter-autoload-verification.md` / `scripts-readme-usage-boundary-clarification.md`（low, raw/ai）** — 本バージョンはメジャー PHASE 着手に集中するため、raw 観察系は未着手。
- **workflow 自己テスト（self-host）の本格実装** — PHASE8.0 §2-2 にある「workflow 自身の end-to-end テストを外部ランナーへ逃がす」は本版スコープ外。`research` workflow の利用シーンとしての検討は ver16.1 以降で行う。

## 想定成果物

- `scripts/claude_loop_research.yaml` — 新規作成（8 step の research workflow 定義）
- `scripts/claude_loop.py` — 変更（`research` workflow 分岐追加、`--workflow auto` の 3 分岐化）
- `scripts/claude_loop_lib/workflow.py` — 変更（`workflow: research` 解決、YAML 同期契約）
- `scripts/claude_loop_lib/validation.py` — 変更（`workflow` 値に `research` を追加）
- `.claude/skills/research_context/SKILL.md` — 新規作成
- `.claude/skills/experiment_test/SKILL.md` — 新規作成
- `.claude/skills/issue_plan/SKILL.md` — 変更（`workflow: research` 選定条件の追記、`ROUGH_PLAN.md` frontmatter 拡張）
- `.claude/skills/split_plan/SKILL.md` — 変更（`/research_context` / `/experiment_test` への handoff 節追加）
- `.claude/skills/imple_plan/SKILL.md` — 変更（`RESEARCH.md` / `EXPERIMENT.md` を入力として読む手順追加）
- `.claude/SKILLS/meta_judge/WORKFLOW.md` — 変更（3 系統として再定義）
- `.claude/rules/scripts.md` — 変更（workflow YAML 同期対象追加）
- `scripts/README.md` / `scripts/USAGE.md` — 変更（`research` workflow 説明 / `experiments/` 運用ルール）
- `experiments/README.md` — 新規作成（実験ファイル規約）
- `scripts/tests/test_claude_loop_cli.py` — 変更（`--workflow research` と auto 3 分岐のテスト追加）
- `scripts/tests/test_claude_loop_integration.py` — 変更（新 workflow end-to-end 経路の検証）
- `docs/util/ver16.0/CURRENT.md` — メジャー版のため現況完全版を作成
- `docs/util/MASTER_PLAN/PHASE8.0.md` — §1 を「実装済み」へ更新

## ワークフロー選択根拠

**`workflow: full`** を選択。

- MASTER_PLAN 新項目への着手は SKILL 規定で `full` 必須（quick 条件の「3 ファイル以下・100 行以下」を大幅に超え、新 SKILL 2 件・新 YAML・新 artifact を伴うアーキテクチャ変更）
- `/split_plan` による設計分解が必要（8 step 構成の妥当性・artifact 名確定・auto 選定条件の粒度決定など、事前リファクタリングと実装計画の両方を要する論点が複数ある）
- 新規 SKILL の責務境界（`/research_context` と `/experiment_test` の分担、`question` workflow との違い）を plan_review_agent レビューにかけて検証する価値が高い

## 事前リファクタリング要否

**要**。ただし軽微。`scripts/claude_loop_lib/workflow.py` と `validation.py` の `workflow` 値分岐が現在 `quick | full` の 2 値を前提としており、`research` 追加前に分岐構造を「値リスト駆動」に寄せておくと `research` 追加の差分が小さくなる見込み。詳細根拠は `PLAN_HANDOFF.md` 参照（後続 `/split_plan` で `REFACTOR.md` として具体化）。

PLAN_HANDOFF.md は別ファイルで作成（full 必須節: ISSUE レビュー結果 / ISSUE 状態サマリ / 選定理由・除外理由 / 関連 ISSUE / 関連ファイル / 前提条件 / 後続 step への注意点）。
