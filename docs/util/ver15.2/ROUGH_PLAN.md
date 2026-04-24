---
workflow: full
source: master_plan
---

# ver15.2 ROUGH_PLAN

PHASE7.1 §2（`QUESTIONS/` ディレクトリ新設 + 調査専用 `question` workflow 追加）を add-only で実装するマイナーバージョン。PHASE7.1 §1（`issue_scout` workflow、ver15.0 実装 / ver15.1 smoke test 済）に続く 2 番目の節。

## ISSUE レビュー結果

`ISSUES/util/{high,medium,low}/` を走査したが、`status: review` かつ `assigned: ai` の ISSUE は **0 件**。遷移対象なし（書き換え実施なし）。

## ISSUE 状態サマリ

util カテゴリの `status × assigned` 分布（`python scripts/issue_status.py util` 実行結果、ver15.2 `/issue_plan` 起動時点）:

| priority | ready/ai | review/ai | need_human_action/human | raw/human | raw/ai |
|---|---|---|---|---|---|
| high | 0 | 0 | 0 | 0 | 0 |
| medium | 1 | 0 | 0 | 0 | 1 |
| low | 0 | 0 | 0 | 0 | 3 |

- `ready / ai` 1 件: `ISSUES/util/medium/issue-review-rewrite-verification.md`（util 単体消化不能で継続持ち越し、ver6.0 以来）
- `raw / ai` 4 件:
  - `ISSUES/util/medium/imple-plan-four-file-yaml-sync-check.md`（ver15.0 scout 起票、4 ファイル同期チェックの SKILL 本文追記提案）
  - `ISSUES/util/low/readme-workflow-yaml-table-missing-scout.md`（ver15.0 scout 起票、README ファイル一覧に scout YAML 未掲載）
  - `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md`（ver14.0 観察持越し）
  - `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md`（ver14.0 観察持越し）

## 選定結果

### 着手対象

**PHASE7.1 §2: `QUESTIONS/` ディレクトリと調査専用 `question` workflow の新設**（`docs/util/MASTER_PLAN/PHASE7.1.md` §2 を一次資料とする）。

### 選定理由

1. **`ready / ai` 1 件は util 単体で消化不能**: `issue-review-rewrite-verification.md` は `app` / `infra` カテゴリ起動時の目視確認を要求する性質上、util カテゴリ内の `/imple_plan` / `/quick_impl` では実動作確認できない。ver6.0 以来「util で拾える ready/ai が実質ゼロ」という状態が続いており、本バージョンも継続持ち越しとする。
2. **MASTER_PLAN PHASE7.1 は §1 のみ完了の未完走**: §2〜§4 が残っており、本バージョンでは次節（§2）に着手するのが PHASE 構造上自然。ver15.0 `/retrospective` §3 でも「(B) PHASE7.1 §2〜§3 の本体実装を ver15.1 or ver15.2 で着手」と推奨されている。
3. **scout 挙動確認済（ver15.1）**: §1 scout workflow は ver15.1 smoke test で 3 軸全クリア（上限遵守 / 重複検出 / frontmatter 完全性）。§2 設計へのフィードバックは特になく、§2 着手の前提条件を充足している。
4. **§2 と §3 のうち §2 を優先**: §2（QUESTIONS + question workflow）は新規 queue + 新規 SKILL の独立追加で add-only 構造。§3（ROUGH_PLAN / PLAN_HANDOFF 分離）は既存 SKILL 本文（`issue_plan` / `split_plan` / `quick_impl`）の改訂を伴い、version flow 全体に影響する破壊性が相対的に高い。本バージョンは add-only の §2 に絞り、§3 は ver15.3 以降に分離する。

### 除外理由

- **PHASE7.1 §3（ROUGH_PLAN.md / PLAN_HANDOFF.md 分離）**: §2 と同時着手すると「新 queue 導入」と「既存 plan 文書の分割改訂」が混在し、workflow: full 1 本で扱うにはスコープが広すぎる。§3 単独でも `.claude/skills/issue_plan` / `split_plan` / `quick_impl` / `.claude/plans/VERSION_FLOW.md` の改訂を伴うため、独立バージョン（ver15.3 想定）に分離。
- **PHASE7.1 §4（run 単位通知）**: PHASE7.1.md 表で ver15.2 想定とされているが、§2 と §4 は独立領域（queue vs 通知）であり、1 版に詰め込むと scope が膨らむ。§4 は ver15.4 以降に回す。
- **新 PHASE8.0 骨子作成**: PHASE7.1 が §1 のみ完了の未完走のため不要（ver15.0 RETRO §1 / §3 の判断を継承）。
- **`issue-review-rewrite-verification.md`**: 前述のとおり util 単体では消化不能。`app` / `infra` 起動まで継続持ち越し。
- **他 `raw / ai` 3 件**: ver14.0 持越し 2 件は観察継続。`imple-plan-four-file-yaml-sync-check.md` / `readme-workflow-yaml-table-missing-scout.md` は §2 で新 YAML / README 編集を行う際に**付随対応の余地あり**（後述「付随的に触れる ISSUE」で扱い方を明記）。

### 付随的に触れる ISSUE（参考情報、本バージョンでは明示消化しない）

§2 実装で `scripts/claude_loop_question.yaml` を新規追加する際、以下 2 件が物理的に触れる可能性が高い:

- `imple-plan-four-file-yaml-sync-check.md`（raw / ai / medium）: §2 は新 YAML 追加のため「YAML 増減時に rule / docs の同期対象リストを更新する」チェックを今回発生させたい操作そのもの。`/imple_plan` 側でこのチェック追記を §2 の実装タスクに組み込むかどうかは後続 `/split_plan` で判断する。ROUGH_PLAN 段階では「§2 本体スコープのみ」に留め、ISSUE 昇格判断は `/split_plan` へ委ねる。
- `readme-workflow-yaml-table-missing-scout.md`（raw / ai / low）: §2 は `scripts/README.md` を改訂するため、同じ編集タイミングで scout YAML 行の追加も合流消化できる。同様に `/split_plan` で判断。

これらは本バージョンの主スコープには含めないが、後続 `/split_plan` / `/imple_plan` で「主スコープと同じファイルに触るなら合流消化可」「別ファイルになるなら別バージョンに分離」の判断材料として残す。

## スコープ

### 実施する（PHASE7.1 §2 完了条件に対応）

1. **`QUESTIONS/` ディレクトリの新設**
   - `QUESTIONS/{category}/{high,medium,low}/` 配下に Question を置く運用を開始する
   - Question の frontmatter 仕様（`status`: `raw` | `ready` | `need_human_action`、`assigned`: `human` | `ai`、`priority`: `high` | `medium` | `low`）を定義する
   - 完了後は `QUESTIONS/{category}/done/` へ移動するライフサイクルを採用する
   - `QUESTIONS/README.md` で上記を一次資料化する

2. **調査専用 `question` workflow の新設**
   - `ready / ai` の Question を 1 件選び、調査のみを行い、コード実装には進まない 1〜2 ステップの軽量 workflow を追加する
   - 調査結果は `docs/{category}/questions/{slug}.md` に報告書として出力する。報告書には「問い」「確認した証拠」「結論」「不確実性」「次アクション候補」の 5 項目を含める
   - 調査結果、実装課題が明確になった場合はその場で実装せず、新規 ISSUE を起票して既存 flow へ引き渡す
   - 人間の追加情報が必要な場合は Question を `need_human_action / human` へ戻し、本文末尾に確認事項を追記する

3. **`--workflow question` エントリポイントの追加**
   - `scripts/claude_loop.py` が新 workflow YAML（`scripts/claude_loop_question.yaml`）を `--workflow question` で起動できるようにする
   - 既存 `auto` / `full` / `quick` / `scout` の挙動は変更しない（`question` は opt-in 専用、`auto` に自動混入させない）
   - `--workflow auto` は引き続き `ISSUES/` のみを参照する。`QUESTIONS/` は `question` workflow 専属の queue とする

4. **Question 管理ユーティリティの整備**
   - `scripts/question_status.py`（分布表示、`issue_status.py` と同等の機能）を追加する
   - `scripts/question_worklist.py`（AI 向け着手候補抽出、`issue_worklist.py` と同等の機能）を追加する
   - 共通化できる関数は `scripts/claude_loop_lib/questions.py` に集約する

5. **SKILL ファイルの新規追加**
   - `.claude/skills/question_research/SKILL.md` を新規作成し、調査報告書の作成手順・粒度・出力先を定義する
   - 既存 `.claude/skills/issue_plan/SKILL.md` には「`QUESTIONS/` は本 SKILL の対象外」と明記（最小追記）

6. **docs 整合**
   - `scripts/README.md`・`scripts/USAGE.md` に `question` workflow の起動方法と `QUESTIONS/` / `ISSUES/` の境界を追記
   - `docs/util/MASTER_PLAN/PHASE7.1.md` の進捗表で §2 を「実装済み（ver15.2）」に更新（本バージョン `/wrap_up` または `/write_current` 段階で行う）

### 実施しない（本バージョンでは対象外）

- PHASE7.1 §3（`ROUGH_PLAN.md` / `PLAN_HANDOFF.md` 分離）— ver15.3 以降で扱う
- PHASE7.1 §4（run 単位通知）— ver15.4 以降で扱う
- 既存 `auto` / `full` / `quick` / `scout` workflow の挙動変更（`question` は完全 opt-in で共存）
- `QUESTIONS/` 配下への初期 Question 投入（別タスク・初回実運用は後続バージョンまたは人間起票で発生）
- `issue-review-rewrite-verification.md` の消化（`app` / `infra` 起動まで持ち越し）
- ver14.0 持越し 2 件（`rules-paths-frontmatter-autoload-verification.md` / `scripts-readme-usage-boundary-clarification.md`）の観察 / 消化
- 外部通知（Slack / Discord）との連携（PHASE7.1 §2 の対象外、§4 以降でも扱わない）

## 成果物（想定）

| 成果物 | 種別 | 概要 |
|---|---|---|
| `QUESTIONS/README.md` | 新規 | Question の frontmatter・ライフサイクル・報告書配置を定義 |
| `scripts/claude_loop_question.yaml` | 新規 | 調査専用 workflow 定義 |
| `scripts/claude_loop_lib/questions.py` | 新規 | Question 共通処理（frontmatter 解析 / 一覧取得 / archive 等） |
| `scripts/question_status.py` | 新規 | 分布表示 |
| `scripts/question_worklist.py` | 新規 | 着手候補抽出 |
| `scripts/claude_loop.py` / `workflow.py` 等 | 変更 | `--workflow question` 入口追加 |
| `scripts/README.md` / `scripts/USAGE.md` | 変更 | `question` workflow・`QUESTIONS/` 境界追記 |
| `.claude/skills/question_research/SKILL.md` | 新規 | 調査報告書作成手順 |
| `.claude/skills/issue_plan/SKILL.md` | 変更（最小） | `QUESTIONS/` 非対象の明記 |
| `docs/util/MASTER_PLAN/PHASE7.1.md` | 変更 | §2 進捗「実装済み（ver15.2）」 |
| `docs/util/ver15.2/IMPLEMENT.md` / `MEMO.md` / `CHANGES.md` / `RETROSPECTIVE.md` | 新規 | full workflow 成果物（後続 step で生成） |

コード変更は既存 workflow の挙動に影響しない add-only 構造。既存テスト（105 件）は全件グリーンを維持する。新規機能用のテストを Python テスト側に追加する（`scripts/tests/` 配下、件数見込み 5〜10 件）。

## 関連 ISSUE / ドキュメント

- `docs/util/MASTER_PLAN/PHASE7.1.md` — §2 の一次資料（期待挙動 / 完了条件 / ファイル変更一覧 / リスク）
- `docs/util/ver15.0/CURRENT.md` — PHASE7.1 §1 完了時点のコード現況（scout workflow）
- `docs/util/ver15.0/IMPLEMENT.md` — §1 実装計画。§2 の実装様式（add-only / 新 YAML / 新 SKILL）の参考モデル
- `docs/util/ver15.0/RETROSPECTIVE.md` §3「次バージョン種別推奨」— §2 優先着手方針の出典
- `docs/util/ver15.1/ROUGH_PLAN.md` — §1 smoke test 完了を受けて §2 着手前提が揃った旨の確認
- `docs/util/ver15.1/MEMO.md` §後続バージョンへの引き継ぎ — 「PHASE7.1 §2（路線 B）: scout の挙動を確認済みのため着手可能。ver15.2 で /issue_plan → 適切なワークフロー選択」
- `ISSUES/util/medium/imple-plan-four-file-yaml-sync-check.md` — §2 付随対応候補（`/split_plan` で合流判断）
- `ISSUES/util/low/readme-workflow-yaml-table-missing-scout.md` — §2 README 改訂時の合流候補
- `.claude/skills/issue_scout/SKILL.md` — §1 で新設した SKILL、§2 の SKILL 記法の参考
- `scripts/claude_loop_scout.yaml` — §2 新 YAML の参考モデル
- `scripts/issue_status.py` / `scripts/issue_worklist.py` — §2 の `question_status.py` / `question_worklist.py` の雛形

## ワークフロー選択の根拠（`workflow: full`）

- 選定対象は MASTER_PLAN 新項目（PHASE7.1 §2）に着手する → SKILL 規則により **必ず `full`**
- 新規 SKILL 追加（`question_research/SKILL.md`）を伴う → **必ず `full`**
- 変更対象見込みは 10 ファイル以上（新規 7 件 + 変更 3〜5 件）・合計 300 行以上 → `quick`（3 ファイル以下 / 100 行以下）の条件を大幅に超過
- add-only 構造ではあるが新 queue 導入という**概念的拡張**を含む → 安全側で `full`

したがって `workflow: full`（`/issue_plan` → `/split_plan` → `/imple_plan` → `/wrap_up` → `/write_current` → `/retrospective`）を採用する。

## バージョン種別の判定

**マイナー（ver15.2）**。以下根拠:

- MASTER_PLAN 新項目への着手ではあるが、**PHASE7.1 内の継続節**（§2）であり、新 PHASE の骨子作成や新規カテゴリ追加ではない。ver15.0 `/retrospective` §3 でも「PHASE7.1 内の継続節なのでマイナーバージョンで扱うのが PHASE 構造上自然」と明記。
- アーキテクチャ変更なし（既存 workflow runtime を変更せず新 queue + 新入口を add-only 追加）。
- 新規外部ライブラリ導入なし。
- 破壊的変更なし（既存 `auto` / `full` / `quick` / `scout` は挙動不変）。

メジャー昇格（ver16.0）は PHASE7.1 全節完了時点で PHASE8.0 骨子の要否を判定する。本バージョン時点では時期尚早。

## 事前リファクタリング要否

**事前リファクタリング不要**。§2 は add-only（新 YAML / 新 SKILL / 新 Python スクリプト / 新 `QUESTIONS/` ディレクトリの追加）で、既存 `issue_status.py` / `issue_worklist.py` / `claude_loop_lib/issues.py` の構造に触らず、`question_status.py` / `question_worklist.py` / `claude_loop_lib/questions.py` として並列に追加するため（ver15.0 scout 実装と同型の add-only 方針を継承）。`claude_loop.py` / `workflow.py` への編集も ver15.0 で scout を追加したときと同じ経路への分岐追加のみで、リファクタ対象となる構造的な負債は現時点で検出できない。

## 後続 `/split_plan` への引き継ぎメモ

- **主入力**: `docs/util/MASTER_PLAN/PHASE7.1.md` §2（役割 / 期待挙動 / 完了条件が体系的に定義されている）。本 `ROUGH_PLAN.md` は選定経緯と除外理由の提供に留め、実装方式（API 設計・関数シグネチャ・データ構造）は `/split_plan` 側で決定すること。
- **参考モデル**: `docs/util/ver15.0/IMPLEMENT.md`（PHASE7.1 §1 実装計画）が add-only / 新 YAML / 新 SKILL という同型の構造を持つ。リスク表の立て方・ファイル変更粒度・テスト追加方針の参考として必ず読むこと。
- **付随 ISSUE の合流判断**: 上記「付随的に触れる ISSUE」2 件について、§2 実装と同じファイルを触るなら合流消化を検討してよい。ただし本 ROUGH_PLAN 上はスコープ外扱いのため、合流する場合は `IMPLEMENT.md` の成果物一覧と `CHANGES.md` に明記すること（ISSUE 側も `done/` 移動または `ready / ai` 昇格を適切に処理する）。
- **Question report の配置**: PHASE7.1.md §2-2 で `docs/{category}/questions/{slug}.md` と指定されている。`docs/util/questions/` は未存在のため、`QUESTIONS/README.md` と `question_research/SKILL.md` のどちらに配置規約を書くか、`/split_plan` で判断する（PHASE7.1.md は両方の可能性を許容する記述）。
- **`auto` への非混入契約**: `question` workflow を `--workflow auto` に含めない点は PHASE7.1 §2-2 で明示されている。`workflow.py` の `resolve_workflow` 実装修正時、scout と同様に「明示指定時のみ起動」となるよう分岐を追加する必要がある。テストで回帰防止する。
- **既存テストへの影響**: 新 workflow 追加で `scripts/tests/test_workflow.py` 等の既存テストが壊れないこと（`SCOUT_YAML_FILENAME` 追加時と同型の回帰リスク）。`/imple_plan` 実行前に既存テストを走らせて現状緑を確認するのが安全。
- **`imple-plan-four-file-yaml-sync-check.md` の扱い**: §2 で 5 ファイル目の YAML を追加するため、同 ISSUE が指摘する「YAML 増減時の rule / docs 同期」が今回まさに発生する。`/split_plan` で本 ISSUE を ready/ai に昇格させて §2 実装に組み込むか、あるいは §2 作業中に自然に同期して ISSUE を `done/` 化するか、どちらでもよい。判断を `IMPLEMENT.md` で明示すること。
