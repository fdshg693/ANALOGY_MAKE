---
workflow: full
source: issues
---

# ver11.0 ROUGH_PLAN — `tests/test_claude_loop.py` 肥大化解消と scripts 専用テスト配置

## ISSUE レビュー結果

- ready/ai に遷移: 2 件
  - `ISSUES/util/high/pythonテスト肥大化.md`
  - `ISSUES/util/medium/scripts構成改善.md`
- need_human_action/human に遷移: 0 件
- 追記した `## AI からの依頼`: 0 件

review/ai 2 件はいずれも「期待動作」「影響範囲」が明文化されており、判定基準（再現手順 / 期待動作 / 影響範囲の 3 点中 2 点以上）を満たしたため `ready / ai` に遷移。両件とも `reviewed_at: "2026-04-23"` を追加済み。

## ISSUE 状態サマリ

| status / assigned | 件数 |
|---|---|
| ready / ai | 3 |
| review / ai | 0 |
| need_human_action / human | 0 |
| raw / human | 0 |
| raw / ai | 3 |

（内訳 — ready/ai: `pythonテスト肥大化`(high) / `issue-review-rewrite-verification`(medium) / `scripts構成改善`(medium) 。raw/ai: `cli-flag-compatibility-system-prompt` / `test-issue-worklist-limit-omitted-returns-all` / `system-prompt-replacement-behavior-risk`）

## 今回のスコープ

本バージョンでは **`ISSUES/util/high/pythonテスト肥大化.md`** のみを対象とする。

### なぜこの ISSUE を選ぶか

1. **優先度**: util カテゴリで唯一の `high` 優先度 ISSUE。`/issue_plan` の優先度順選定ルール（high → medium → low）に従えば、medium の 2 件（`issue-review-rewrite-verification` / `scripts構成改善`）より先に着手する。
2. **ベースライン健全性**: 現状 `tests/test_claude_loop.py` は 1881 行 41 クラスで、1 ファイルで全ての `claude_loop_lib/` モジュール（`commands.py` / `feedbacks.py` / `frontmatter.py` / `git_utils.py` / `issues.py` / `logging_utils.py` / `notify.py` / `workflow.py`）のテストを抱えている。PHASE7.0 §2（起動前 validation）以降で大量のテスト追加が想定されており、着手前にテスト配置を整えておくことで以降の追加作業が一貫した構造に載る。
3. **ver10.0 retrospective の前提との整合**: retrospective は「ver10.1 で `test_limit_omitted_returns_all` を quick 消化 → ver11.0 で PHASE7.0 §2 着手」を推奨していたが、その後追加された `pythonテスト肥大化` (high) はテストファイル自体の再構成であり、pre-existing test 失敗と同じ領域に入る。テスト再構成を先に行うことで、`test_limit_omitted_returns_all` の調査・修正も再構成後の新しい配置で素直に扱えるため、順序を入れ替えて本 ISSUE を先に処理する。
4. **アーキテクチャ寄りの変更**: テストディレクトリ構成の変更（`tests/` → `scripts/tests/` 等）と単一ファイルの分割は破壊的変更を伴うリファクタリングであり、CLAUDE.md の**メジャーバージョン条件**に該当する。

### なぜ他 ISSUE を含めないか

- `issue-review-rewrite-verification.md` (medium): util 単体消化不能（`app` / `infra` カテゴリでの `/split_plan` 起動が必要）。ver6.0 から持ち越し中の継続案件であり、本バージョンのスコープ外。
- `scripts構成改善.md` (medium): 同じ `scripts/` 配下に触れる ISSUE だが、内容は「ワークフロー関連コードとその他コードの分離」「`scripts/README.md` の分割」「README への運用注記追加」であり、テストファイル分割とは独立。まとめるとスコープが広がり、リスク評価・review 負荷が跳ねるため別バージョンに切り出す（ver11.1 以降で消化想定）。
- `cli-flag-compatibility-system-prompt.md` / `system-prompt-replacement-behavior-risk.md` (raw/ai): PHASE7.0 §2 起動前 validation と束ねる方針（ver10.0 retrospective §3-2 で決定済み）。
- `test-issue-worklist-limit-omitted-returns-all.md` (raw/ai): 本バージョンの再構成作業中に触れざるを得ない可能性は高いが、**本 ISSUE のスコープは「ファイル構成変更」に限定**し、個別テストの失敗調査は別枠とする。再構成時に該当テストは新配置にそのまま移送し、失敗状態を保全する。

### なぜ `workflow: full` か

- メジャーバージョン（ver11.0）に該当。
- アーキテクチャ寄りの破壊的変更（既存 `tests/test_claude_loop.py` の分割 + ディレクトリ移動）。
- 変更ファイル数が多い（テストクラス 41 件を 7〜10 ファイル程度に再分割する想定）。
- インポートパス・CI / 手動テスト実行コマンド・`scripts/README.md` の記述など、周辺ドキュメントへの波及がある。
- CLAUDE.md 版管理規則「メジャー = アーキテクチャ変更・破壊的リファクタリング」および `/issue_plan` の「判断に迷う場合は安全側で full」双方に合致。

### なぜ `source: issues` か

着手対象は `ISSUES/util/high/pythonテスト肥大化.md`。MASTER_PLAN の新 PHASE には踏み込まず、既存 ISSUE の消化に限定する。

## 提供する機能 / 成果物の全体像

**目的**: `tests/test_claude_loop.py`（1881 行・41 クラス）の単一巨大ファイル構造を解消し、拡張性ある配置に整える。

### ユーザー / 開発体験の変化

変更前:
- `claude_loop` 関連のテストは **すべて** `tests/test_claude_loop.py` に集約されており、1 ファイルで 1881 行・41 クラスを抱える。
- `tests/` 配下には Nuxt アプリ本体のテスト（`tests/composables/` / `tests/server/` / `tests/utils/` / `tests/fixtures/`）と Python スクリプトのテストが同居しており、Vitest と unittest の両方が同じ親ディレクトリから実行される。
- 該当テストの追加・変更時、1 ファイル内でクラス数・行数が増え続け、レビュー・git diff・IDE のアウトラインのいずれの観点でも見通しが悪い。

変更後:
- Python スクリプト（`scripts/claude_loop.py` / `scripts/claude_loop_lib/` / `scripts/issue_worklist.py` / `scripts/issue_status.py` / `scripts/claude_sync.py`）のテストは、**アプリ本体テストと物理的に分離**した場所（例: `scripts/tests/` あるいは同等の新配置）に置かれる。
- 巨大単一ファイルは **テスト対象モジュールに対応する複数ファイル** に分割される（例: `test_commands.py` / `test_feedbacks.py` / `test_frontmatter.py` / `test_issues.py` / `test_workflow.py` / `test_logging_utils.py` / `test_notify.py` / `test_git_utils.py` / `test_claude_loop_cli.py` / `test_integration.py` 程度の粒度を想定）。実際の分割境界は IMPLEMENT.md で決定する。
- テスト実行コマンドは `scripts/README.md` に一本化して記載し、ユーザー / AI どちらも迷わない形にする。
- 既存のテスト件数・アサーション内容は**基本的に保全**する（再構成であって挙動変更ではない）。pre-existing 失敗（`test_limit_omitted_returns_all`）は再構成後も同じく失敗する状態で保全し、別 ISSUE で扱う。

### 非スコープ（本バージョンではやらない）

- テスト本体のアサーション修正・追加・削除（構造変更のみ）
- `test_limit_omitted_returns_all` の修正（別 ISSUE）
- `scripts/README.md` の分割・運用注記追加（`scripts構成改善.md` の別 ISSUE として次バージョン以降）
- PHASE7.0 §2 起動前 validation の実装
- `pytest` への移行 / テストランナー変更（`unittest` のまま）

## 事前リファクタリング

事前リファクタリング不要 — 本バージョンは既存テストファイルの分割・移動のみであり、プロダクションコード（`scripts/claude_loop.py` / `scripts/claude_loop_lib/`）には一切触れない。事前に均しておくべき別領域のコードも発見されなかったため、REFACTOR.md は作成しない。

## IMPLEMENT.md に委ねる判断事項（後続ステップへの引き継ぎ）

以下は本バージョンで解決すべき設計判断だが、ROUGH_PLAN ではあえて詳細化せず `/split_plan` → `/imple_plan` に委ねる:

1. **配置先ディレクトリ**: `scripts/tests/` か `tests/scripts/` か、または別名（例: `tests_scripts/`）。`scripts/` 配下にテストを置く場合、pnpm/Vitest からの glob 影響範囲、pytest/unittest の discover パス、`sys.path` 組み立てを確認して決定する。
2. **ファイル分割粒度**: `claude_loop_lib/` の 8 モジュールに 1:1 で割り付ける方式か、CLI テスト / ユニットテスト / 統合テストの階層分けを採るか、あるいはハイブリッドにするか。41 クラスを 1 ファイル平均 4〜6 クラスに収める目安（1 ファイル 200〜400 行）で設計する。
3. **共通ヘルパの切り出し**: 既存 `tests/test_claude_loop.py` 内で複数クラスから参照されるヘルパ（例: `_make_tmp_issue` 的なもの）があれば、`conftest.py` 風の共通モジュールに切り出すか各ファイルにコピーするかを判定。
4. **テスト実行コマンドの集約**: 現状 `python -m unittest tests.test_claude_loop` で走らせている箇所（`scripts/README.md` / `Justfile` / CI 相当の手順）を漏れなく新コマンドに置換。CI は GitHub Actions `.github/workflows/deploy.yml` を確認。
5. **`__init__.py` / `sys.path` 設計**: Python パッケージ境界を明示するか namespace のまま走らせるか。Windows / Linux 両対応で壊れない構成にする。
6. **`tests/` 配下の既存非-Python テストへの影響**: `tests/composables/` / `tests/server/` 等は Vitest 側で動作しているため、移動対象外として保全する旨を明示する。
7. **移行手順**: 一括書き換え（1 コミット）か、段階的移行（分割 → 移動 → インポート修正 → 削除）か。破壊的変更のため、テストが常に通る中間状態を確保する設計が望ましい。

## 関連ファイル

### 再構成対象
- `tests/test_claude_loop.py` （1881 行・41 クラス、分割元）

### 参照のみ（テスト対象 — 本バージョンで変更しない）
- `scripts/claude_loop.py`
- `scripts/claude_loop_lib/` （`commands.py` / `feedbacks.py` / `frontmatter.py` / `git_utils.py` / `issues.py` / `logging_utils.py` / `notify.py` / `workflow.py`）
- `scripts/issue_worklist.py`
- `scripts/issue_status.py`
- `scripts/claude_sync.py`

### 波及更新が想定されるファイル
- `scripts/README.md` （テスト実行コマンド記載箇所の更新）
- `Justfile` （テスト系レシピがあれば更新）
- `.github/workflows/deploy.yml` （CI で Python テストを回しているかを確認し、必要なら更新）
- `tests/fixtures/` （新配置から参照する場合はパス調整、不要なら据え置き）

### 保全対象（移動対象外）
- `tests/composables/` / `tests/server/` / `tests/utils/` （Nuxt 側 Vitest テスト）
- `tests/fixtures/` （Nuxt 側で参照している場合）

## 関連 ISSUE

- 着手対象: [`ISSUES/util/high/pythonテスト肥大化.md`](../../../ISSUES/util/high/pythonテスト肥大化.md)
- 隣接で同時処理しない ISSUE（将来対応）:
  - [`ISSUES/util/medium/scripts構成改善.md`](../../../ISSUES/util/medium/scripts構成改善.md)（`scripts/README.md` 分割・運用注記追記。ver11.1 以降想定）
  - [`ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md`](../../../ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md)（pre-existing テスト失敗。再構成後の新ファイル配置で別途扱う）
  - [`ISSUES/util/medium/cli-flag-compatibility-system-prompt.md`](../../../ISSUES/util/medium/cli-flag-compatibility-system-prompt.md)（PHASE7.0 §2 で吸収）
  - [`ISSUES/util/low/system-prompt-replacement-behavior-risk.md`](../../../ISSUES/util/low/system-prompt-replacement-behavior-risk.md)（PHASE7.0 §2 で吸収）
- 持ち越し継続: [`ISSUES/util/medium/issue-review-rewrite-verification.md`](../../../ISSUES/util/medium/issue-review-rewrite-verification.md)（util 単体消化不能）

## 参照ドキュメント

- [`docs/util/ver10.0/CURRENT.md`](../ver10.0/CURRENT.md) — util 現況（ワークフロー体系・ISSUES 管理・非同期コミュニケーション）
- [`docs/util/ver10.0/CURRENT_tests.md`](../ver10.0/CURRENT_tests.md) — 既存テスト構成
- [`docs/util/ver10.0/CURRENT_scripts.md`](../ver10.0/CURRENT_scripts.md) — `scripts/` 配下構成
- [`docs/util/ver10.0/RETROSPECTIVE.md`](../ver10.0/RETROSPECTIVE.md) — ver10.0 振り返り（§3-2 次バージョン推奨、§4-4 引き継ぎ事項）
- [`docs/util/MASTER_PLAN.md`](../MASTER_PLAN.md) / [`docs/util/MASTER_PLAN/PHASE7.0.md`](../MASTER_PLAN/PHASE7.0.md) — PHASE7.0 は §1 一部実装、§2〜§8 未着手（本バージョンでは踏み込まない）
