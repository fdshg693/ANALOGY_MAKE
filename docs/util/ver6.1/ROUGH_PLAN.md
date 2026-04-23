# ver6.1 ROUGH_PLAN — YAML frontmatter パース関数の共通化

## ISSUE レビュー結果

util カテゴリの `status: review / assigned: ai` ISSUE を走査した。該当なし（書き換え対象 0 件）。

| 対象 | 結果 |
|---|---|
| `ISSUES/util/high/*.md` | 0 件 |
| `ISSUES/util/medium/*.md` | `issue-review-rewrite-verification.md` 1 件（`ready / ai` のため対象外） |
| `ISSUES/util/low/*.md` | `parse-frontmatter-shared-util.md` 1 件（`ready / ai` のため対象外） |

書き換え件数: 0 件（`ready / ai` のみで、`review / ai` は存在しない）。

## ISSUE 状態サマリ

| 組み合わせ | high | medium | low |
|---|---|---|---|
| ready / ai | 0 | 1 | 1 |
| review / ai | 0 | 0 | 0 |
| need_human_action / human | 0 | 0 | 0 |
| raw / human | 0 | 0 | 0 |
| raw / ai | 0 | 0 | 0 |

## バージョン種別

**マイナー (6.1)** — ISSUES 解消（既存スクリプトのリファクタリング、外部 API 変更なし）。

`ver6.0 RETROSPECTIVE §3` は PHASE6.0（ver7.0 メジャー）を推奨していたが、次の理由で本バージョンは先に低優先 ISSUE を 1 件消化する:

- PHASE6.0 で新設予定の `scripts/issue_worklist.py` も frontmatter パースを必要とする。先に共通ユーティリティを切り出しておくことで、PHASE6.0 で 3 個目の重複実装を防げる
- util カテゴリの `ready / ai` ISSUE が 2 件残っており、スキルの判定基準（`ready / ai` 優先）に合致
- 同じく `ready / ai` の `issue-review-rewrite-verification.md`（medium）は実行条件が「app / infra カテゴリでの `/split_plan` 起動時の目視確認」で util からは消化不能。このため util 内で消化可能な `parse-frontmatter-shared-util.md`（low）を選択

## 対象 ISSUE

`ISSUES/util/low/parse-frontmatter-shared-util.md`

## やること

`scripts/issue_status.py` と `scripts/claude_loop_lib/feedbacks.py` に重複して存在する YAML frontmatter パースロジックを、`scripts/claude_loop_lib/frontmatter.py` に共通関数として切り出す。両呼び出し元を共通関数経由に書き換える。

### 機能面でのユーザー体験

- 外部から見た挙動変更なし（純粋なリファクタリング）
- `python scripts/issue_status.py` の出力も、`claude_loop.py` のフィードバック消費挙動も、従来通り
- 既存テスト（`tests/test_claude_loop.py`）は壊れない

### 含むもの

- 共通関数 `parse_frontmatter(text: str) -> dict | None` の新設
- `issue_status.py` / `feedbacks.py` の両呼び出し元を共通関数へ差し替え
- 既存テスト（feedback 関連）が通り続けること

### 含まないもの（後続タスクへ持ち越し）

- PHASE6.0 本体（`/issue_plan` 分離、`scripts/issue_worklist.py` 追加、`--workflow auto` 導入）
- `issue-review-rewrite-verification.md` の消化（app / infra カテゴリ起動が必要）
- frontmatter に関する追加バリデーション・スキーマ検証
- `parse_feedback_frontmatter` の高水準ロジック（step フィールドの型解釈）そのものの共通化 — 本 ISSUE のスコープは frontmatter ブロックの「抽出・YAML パース」部分の共通化に限定する

## 成否判定基準

- `scripts/issue_status.py` / `scripts/claude_loop_lib/feedbacks.py` 内で `"---"` を境界にした手動 split が消える
- `python scripts/issue_status.py util` の出力が従来と完全一致
- `pnpm exec vitest` 相当のテスト（本件では `pytest tests/test_claude_loop.py` 等 Python 側のユニットテスト）が従来通り通る
- PHASE6.0 側で `issue_worklist.py` 実装時に、同じ共通関数を追加変更なしで再利用できる形になっている

## 小規模タスク判定

以下の条件をすべて満たすため **小規模タスク**:

- 変更対象ファイル: 3 つ（`issue_status.py` / `feedbacks.py` / 新規 `frontmatter.py`）+ 任意でテスト 1 ファイル
- 追加行: 50 行未満の見込み
- 新規ファイル作成: 1 ファイル（`scripts/claude_loop_lib/frontmatter.py`）のみで既存モジュール配下への配置

→ `REFACTOR.md` は作成しない（本 ROUGH_PLAN に「事前リファクタリング不要」と明示）。
→ `IMPLEMENT.md` は作成するが、簡潔化ルール（コード変更量の 2〜3 倍程度）に従う。
→ quick ワークフローへの切り替え提案は `REQUESTS/AI/quick-workflow-suggestion-ver6.1.md` に別途記録（AUTO モード運用のため自動中断はしない）。

## 事前リファクタリング

不要。今回の作業自体がリファクタリングのため、下敷きの整地は発生しない。
