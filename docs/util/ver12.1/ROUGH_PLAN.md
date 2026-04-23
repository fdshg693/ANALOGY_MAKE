---
workflow: quick
source: issues
---

# ver12.1 ROUGH_PLAN — `test_limit_omitted_returns_all` 消化

## ISSUE レビュー結果

- **遷移件数**: 0 件（util カテゴリに `status: review / assigned: ai` の ISSUE は存在しない）
- **対象パス**: なし
- **備考**: 今回は ISSUE レビューフェーズの書き換え作業は発生しない

## ISSUE 状態サマリ（util カテゴリ, ver12.1 着手時点）

| status × assigned | high | medium | low |
|---|---|---|---|
| `ready / ai` | 0 | 1 | 0 |
| `review / ai` | 0 | 0 | 0 |
| `need_human_action / human` | 0 | 0 | 0 |
| `raw / ai` | 0 | 2 | 1 |
| `raw / human` | 0 | 0 | 0 |

対象 ISSUE 一覧（medium）:

- `ISSUES/util/medium/issue-review-rewrite-verification.md` — `ready / ai`（util 単体で消化不能、持ち越し継続）
- `ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md` — `raw / ai`（**本バージョンで消化**）
- `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md` — `raw / ai`（ver13.0 §3 と合わせて処理予定）
- `ISSUES/util/low/system-prompt-replacement-behavior-risk.md` — `raw / ai`（ver13.0 以降で再評価）

## 着手対象の決定

### 選定

**対象**: `ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md`

### 選定理由

1. **ユーザー明示指示**: `FEEDBACKS/NEXT.md` で本 ISSUE 消化が指示されている。通常は `status: ready / assigned: ai` のみを着手対象とするが、ユーザー明示指示により `raw / ai` を先行して処理する（`/issue_plan` SKILL の判断基準末尾に「ユーザーから明示的な指示がある場合はそちらに従う」の定めあり）
2. **ver12.0 RETROSPECTIVE での方針**: §3-2「ver12.1（quick, マイナー）で `test_limit_omitted_returns_all` を消化」と §4-4 で次バージョン引き継ぎが明文化されている
3. **3 バージョン連続持ち越し解消**: ver10.0 / ver11.0 / ver12.0 と 3 バージョン連続で先送りされた pre-existing テスト失敗。baseline 健全性の観点でこれ以上の持ち越しは許容しない

### 除外した候補と理由

- `issue-review-rewrite-verification.md`（`ready / ai`）: util カテゴリでは `review / ai` の ISSUE が存在せず、実動作確認の場が util 内に無い。次回以降 `app` / `infra` カテゴリの plan 起動時に実施する方針のまま持ち越し継続
- `cli-flag-compatibility-system-prompt.md`（`raw / ai`）: PHASE7.0 §3 `legacy --auto 撤去` と合わせて CLI 整理時に同時処理する候補。ver13.0 のメジャーで扱うほうが関連変更と一括レビュー可能
- `system-prompt-replacement-behavior-risk.md`（`raw / ai`, low）: ver13.0 以降の運用整理で再評価する方針のため着手見送り
- **MASTER_PLAN 新項目（PHASE7.0 §3〜§8）**: ready/ai が存在し、かつユーザー明示指示で本 ISSUE 消化が優先されるため、MASTER_PLAN 新項目には着手しない

## バージョン種別の判定

**マイナーバージョンアップ (ver12.1)** として扱う。

根拠:

- ISSUES の解消（pre-existing テスト失敗 1 件のバグ修正）に該当
- アーキテクチャ変更・新規外部ライブラリ導入・破壊的変更は伴わない
- MASTER_PLAN 新項目への着手なし
- 変更対象は `scripts/claude_loop_lib/issues.py` ないしは `scripts/issue_worklist.py` + `scripts/tests/test_issue_worklist.py` の 2 ファイル程度、想定変更行数は数十行以内

## ワークフロー選択

**`workflow: quick`** を採用。

根拠:

- 選定 ISSUE はすべて `raw` 状態で、`review / ai` の書き換えは含まない（→ `full` 強制条件に非該当）
- MASTER_PLAN 新項目 / アーキテクチャ変更 / 新規ライブラリ導入を伴わない
- 変更対象は 3 ファイル以下（実装 1 + テスト 1 + ISSUE ファイル移動で合計 3 未満見込み）かつ 100 行以下の見込み
- ver12.0 RETROSPECTIVE §3-2 でも quick 適合性を確認済み

## タスクの内容（提供される挙動変更）

### スコープ

`python scripts/issue_worklist.py` の JSON 出力仕様を確定し、`--limit` 省略時と指定時で payload 形状を切り分ける:

- `--limit` 省略時: payload には `category`・`filter`・`items` のみを含め、`total` / `truncated` / `limit` は出力しない（全件返却されるためページング関連メタ情報は不要）
- `--limit` 指定時: 現状どおり `total` / `truncated` / `limit` を出力する（切り詰め有無の判断材料として必要）

これにより `scripts/tests/test_issue_worklist.py::TestIssueWorklist::test_limit_omitted_returns_all` の `assert "total" not in payload` が成立し、既知の pre-existing 失敗 1 件が解消される。

### 出所となる設計意図

`docs/util/ver9.2/MEMO.md` および `docs/util/ver9.2/CHANGES.md` で ver9.2 時点の設計意図として「`--limit` 未指定時は `total` / `truncated` / `limit` フィールドを省略（後方互換）」が明記されている。すなわち今回の仕様確定は「ver9.2 での設計意図に実装を揃える」ものであり、新規設計判断ではない。

### ユーザー体験の変化

- 直接の利用者は `/issue_plan` / `/split_plan` / `/quick_plan` など plan 系 SKILL が内部で起動する `issue_worklist.py` の出力を読む AI（= Claude）のみ
- `--limit` 省略時の出力からページング情報が消えるが、items 配列は全件含まれるため参照側で困ることはない
- `/issue_plan` SKILL のコンテキスト注入では現状 `--limit 20` 指定で呼び出されるため、SKILL 挙動への影響はない

## 関連ファイル・関連 ISSUE

### 変更対象想定ファイル

- `scripts/issue_worklist.py` — `main()` 内で `format_json()` へ `total` / `limit` を渡す条件分岐、または `format_json()` 側のガード条件を見直す（どちらで実装するかは IMPLEMENT.md もしくは quick_impl で確定）
- `scripts/tests/test_issue_worklist.py` — `test_limit_omitted_returns_all` の期待値は既に「`total` not in payload」として書かれており、変更不要の見込み。ただし実装を修正した結果、`test_limit_returns_top_n_in_priority_order` / `test_limit_exceeds_count_no_truncation` など既存の `--limit` 指定系テストに regression が出ないことを必ず確認する

### 変更対象候補（状況次第）

- `scripts/claude_loop_lib/issues.py` — `extract_status_assigned` など共通ヘルパーのみで、`issue_worklist` の limit 制御ロジック自体は `scripts/issue_worklist.py` に存在する。FEEDBACKS/NEXT.md では `claude_loop_lib/issues.py` が想定対象として挙がっているが、現行コードでは `issue_worklist` 関数は `scripts/issue_worklist.py` 側に配置されているため、実際の変更点は後者で確定する見込み。quick_impl 冒頭で現状を再確認のうえ、変更箇所を確定する

### 非変更対象（regression guard）

- `scripts/claude_loop_lib/validation.py` / `scripts/tests/test_validation.py` — ver12.0 で追加した `validate_startup()` は `issue_worklist` を呼び出さないため、validation regression 懸念なし
- `TestValidateStartupExistingYamls` — 引き続き通過することを quick_impl の最終テスト実行で確認

### 関連 ISSUE

- **消化対象**: `ISSUES/util/medium/test-issue-worklist-limit-omitted-returns-all.md` — 消化完了時に `ISSUES/util/done/` へ移動
- **持ち越し（未変更）**: `issue-review-rewrite-verification.md` / `cli-flag-compatibility-system-prompt.md` / `system-prompt-replacement-behavior-risk.md`

### 関連ドキュメント

- `docs/util/ver9.2/MEMO.md` §format_json 挙動 — 「`--limit` 未指定時は省略（後方互換）」の設計意図記載
- `docs/util/ver9.2/CHANGES.md` §format_json シグネチャ — 同上
- `docs/util/ver12.0/RETROSPECTIVE.md` §3-2 / §4-4 — ver12.1 スコープ推奨と引き継ぎ注意点
- `FEEDBACKS/NEXT.md` — ユーザー明示指示（quick_impl 完了時点で `FEEDBACKS/done/` へ移動する想定）

## 想定外対応（quick_impl で逸脱した場合の扱い）

- 想定 2 ファイル以上への変更波及が判明した場合、または 100 行を超える見込みが立った場合は quick から full への切り替えをユーザーに確認する（AUTO モード下では `REQUESTS/AI/` に方向性確認リクエストを書き出す）
- `test_issue_worklist.py` 内の他テストに regression が出た場合、`--limit` 指定時の payload 形状（`total` / `truncated` / `limit` 出力）は現行仕様を維持する方向で修正する（`--limit` 省略時のみ省略、指定時は従来通り）
