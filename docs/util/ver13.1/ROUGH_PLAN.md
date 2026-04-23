---
workflow: quick
source: issues
---

# ver13.1 ROUGH_PLAN — FEEDBACK 異常終了温存の integration テスト追加

## ISSUE レビュー結果

今回の `/issue_plan` では `status: review / assigned: ai` の ISSUE は 0 件だった（レビュー対象なし）。

ただし FEEDBACK (`FEEDBACKS/NEXT.md`) の指示に従い、以下 1 件の raw → ready 昇格のみを行った:

| ファイル | 遷移 | 理由 |
|---|---|---|
| `ISSUES/util/medium/feedback-abnormal-exit-integration-test.md` | `raw / ai` → `ready / ai`（`reviewed_at: 2026-04-23` は既に最新で据え置き） | ver13.0 RETROSPECTIVE §4-3 で「ver13.1 `/issue_plan` 冒頭で raw → ready 昇格」と引き継がれた対象。FEEDBACK でも明示指示あり |

## ISSUE 状態サマリ（util カテゴリ、昇格後）

| status × assigned | 件数 | ファイル |
|---|---|---|
| `ready / ai` | 2 | `medium/issue-review-rewrite-verification.md`（util 単体消化不能のまま持ち越し）／`medium/feedback-abnormal-exit-integration-test.md`（今回の着手対象） |
| `raw / ai` | 2 | `medium/cli-flag-compatibility-system-prompt.md`（ver14.0 §7 で再評価）／`low/system-prompt-replacement-behavior-risk.md`（ver14.0 §8 で再評価） |
| `review / ai` | 0 | — |
| `need_human_action / human` | 0 | — |
| `raw / human` | 0 | — |

## 対象・スコープ

### 着手対象 ISSUE

- `ISSUES/util/medium/feedback-abnormal-exit-integration-test.md`（今回昇格した `ready / ai`）

### 扱わない対象

- `ISSUES/util/medium/issue-review-rewrite-verification.md` — util 単体消化不能のまま持ち越し（ver6.0 から 8 バージョン連続）。ver13.0 RETROSPECTIVE §3-2 で「app / infra で `/issue_plan` / `/split_plan` を動かす機会に消化」と方針確定済
- `raw / ai` の 2 件 — ver13.0 RETROSPECTIVE §3-2 / §4-1 で「ver14.0 §7 / §8 と合わせて再評価」と割り当て済
- MASTER_PLAN の新項目（PHASE7.0 §6〜§8） — ver13.0 RETROSPECTIVE §3-2 で「ver14.0（full）で §6+§7+§8 一括着手」と決定済のため、今回は触らない

## 今回提供する機能

`claude_loop.py` が **ステップ非ゼロ exit / 例外 / Ctrl-C で打ち切られた場合、`FEEDBACKS/` 直下のフィードバックが温存され、次回 run で再度 system prompt に注入される** という不変条件を CI で検知できる integration テストを追加する。

ver13.0 では `scripts/claude_loop.py` の `_run_steps()` 内 L544〜L562（失敗時に `return exit_code`）と L564〜L565（成功時のみ `consume_feedbacks` 呼び出し）で挙動として担保されているが、テストは README / USAGE / docstring / PR レビューのみで、コード変更で invariant が壊れても緑のまま通過する。今回のテスト追加により、以後 `_run_steps()` を変更した際も「失敗時は FEEDBACK を消さない」制約が自動検証される。

ユーザー体験への変化:

- 直接的な変化なし（テスト追加のみ）
- 間接的に、将来の `_run_steps()` リファクタで FEEDBACK 温存が壊れる回帰を防止する

## スコープ境界

### 含まれるもの

- `scripts/tests/test_claude_loop_integration.py` への新規テストクラス追加
  - 異常終了ケース（step が非ゼロ exit）: `FEEDBACKS/` 直下にダミーファイルを事前配置 → subprocess 起動 → 非ゼロ exit 確認 → `FEEDBACKS/` にダミーが残り `done/` は作成されていない／空であることを assert
  - 対照ケース（正常終了）: 同じ配置で step を `exit 0` 相当にした場合は `FEEDBACKS/done/` に移動していることを assert（ISSUE 対応方針 3）
- 必要なら軽量テスト YAML fixture を同テスト内で temp dir に生成（独立ファイル化はせず、既存 `TestYamlIntegration` / `TestAutoWorkflowIntegration` と同様に各テスト内で文字列書き出し）
- cwd 依存は ver12.0 RETROSPECTIVE §2-2-b の教訓どおり `tempfile.TemporaryDirectory` ＋ `--cwd` で分離（既存 `TestAutoWorkflowIntegration._setup_cwd` / `_run_main_auto` パターンを踏襲）
- テスト内の assertion は ver13.0 で常時注入になった `--append-system-prompt`（unattended prompt）の存在を前提にする（ver13.0 MEMO.md §「計画からの乖離」/「commands.py `--append-system-prompt` 常時注入に伴うテストの副作用」参照）

### 含まれないもの

- プロダクションコード（`scripts/claude_loop.py` 本体 / `claude_loop_lib/feedbacks.py` 等）への変更 — ISSUE 本文「影響範囲」で「テスト追加のみで、プロダクションコードには手を入れない」と明記
- 例外 / Ctrl-C 経路の検証 — ISSUE 本文「対応方針 1」は非ゼロ exit のみ明記。例外 / Ctrl-C は現状の `_run_steps()` では別 code path（例外は try/except がなく上位に伝播、Ctrl-C は `KeyboardInterrupt`）だが、両者とも「`consume_feedbacks` に到達する前に関数を抜ける」点は同じ。非ゼロ exit ケースでカバーされる invariant の本質は同一なので、今回は非ゼロ exit のみで十分（例外 / Ctrl-C 経路の明示検証は将来必要になれば別 ISSUE 化）
- FEEDBACKS の整形・バリデーション変更、`consume_feedbacks` の挙動変更
- 新しいワークフロー YAML の追加

## 規模見込み

- 変更ファイル: 1 ファイル（`scripts/tests/test_claude_loop_integration.py`）
- 追加行数: 概ね 50〜80 行（テストクラス 1 つ、テストメソッド 2 つ＋ヘルパ 1〜2 個）
- 既存テストへの影響: なし（純粋追加）

quick 適合性: 変更ファイル 1、概ね 100 行以内、テスト追加のみでプロダクションコード無変更。quick ワークフロー（`/issue_plan → /quick_impl → /quick_doc`）で完結する。

## 後続タスク（今回スコープ外）

- ver14.0（full, メジャー）: PHASE7.0 §6（`/retrospective` → 次ループ FEEDBACK handoff）／§7（`.claude/rules/scripts.md` 新規作成）／§8（`/retrospective` での step prompt/model 評価）を一括着手。詳細は ver13.0 RETROSPECTIVE §3-2 / §4-4 に記載
- `cli-flag-compatibility-system-prompt.md` / `system-prompt-replacement-behavior-risk.md` — ver14.0 §7 / §8 と合わせて再評価

## 参照ファイル・関連 ISSUE

- 着手対象 ISSUE: `ISSUES/util/medium/feedback-abnormal-exit-integration-test.md`
- 関連コード: `scripts/claude_loop.py` L544〜L565（`_run_steps()` の失敗 return と `consume_feedbacks` 呼び出し）
- 関連テスト（流用するパターン）: `scripts/tests/test_claude_loop_integration.py::TestAutoWorkflowIntegration`（特に `_setup_cwd` / `_run_main_auto` の cwd 分離パターン）
- 関連ドキュメント:
  - `docs/util/ver13.0/CURRENT.md`（FEEDBACKS 運用ルール）
  - `docs/util/ver13.0/MEMO.md` §6-4（本 ISSUE の先送り経緯）／§「計画からの乖離」（`--append-system-prompt` 常時注入のテスト影響）
  - `docs/util/ver13.0/RETROSPECTIVE.md` §3-2 / §4-3（ver13.1 への引き継ぎ注意点 5 項目）
- 関連 FEEDBACK: `FEEDBACKS/NEXT.md`（今回の直接起点。5 項目の注意点あり）
