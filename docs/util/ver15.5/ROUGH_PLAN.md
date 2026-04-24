---
workflow: quick
source: issues
---

# ver15.5 ROUGH_PLAN — ver15.4 通知改修の後始末（low ×2 束ね消化）

## バージョン種別

**マイナー（ver15.5）**。MASTER_PLAN 新項目への着手・アーキテクチャ変更・新規ライブラリ導入はいずれもなし。ver15.4 で意図的に先送りした follow-up 2 件を束ねて消化する。

## ISSUE 状態サマリ（util カテゴリ）

| priority | ready/ai | review/ai | need_human_action/human | raw/ai | raw/human |
|---|---|---|---|---|---|
| high | 0 | 0 | 0 | 0 | 0 |
| medium | 1 | 0 | 0 | 0 | 0 |
| low | 5 | 0 | 0 | 2 | 0 |

`review/ai` が 0 件のため、本ループの ISSUE レビューフェーズは no-op（state 遷移なし）。

## ISSUE レビュー結果

- 走査対象: util カテゴリ全件
- `review/ai` 件数: 0
- 状態遷移: なし（`ready/ai` への昇格 0 件、`need_human_action/human` への振り分け 0 件）

## 着手対象（スコープ）

ver15.4 通知改修の直接の後始末となる low ×2 件を束ねて消化する。両者とも ver15.4 で触ったファイル（`scripts/claude_loop_lib/notify.py` / `scripts/claude_loop.py`）に閉じる。

### 実施する

1. **`ISSUES/util/low/notify-beep-print-violation.md`** — `_notify_beep` の `print()` 直接呼び出しを排除し、`.claude/rules/scripts.md` §5（`logging_utils` 経由）違反を解消する。`logging_utils` に「TeeWriter コンテキスト外で使える stderr 出力ヘルパ」を新設し、それを fallback 通知経路から呼び出す形に置き換える。
2. **`ISSUES/util/low/auto-loop-count-semantics.md`** — `_run_auto` の `RunStats` 合算で phase1（issue_plan の 1 step）の `completed_loops` を加算しない方針に変更し、`auto` 実行時の通知本文「N loops」が phase2（full/quick）の loop 数のみを反映するようにする。`completed_steps` 側は両 phase 合算のまま据え置く。

ユーザーから見た変化:
- (1) は外面挙動に変化なし（出力先が stdout → stderr に変わるのみ。挙動規約整備）
- (2) は `--workflow auto --max-loops 1` 実行時の通知本文が「2 loops / 7 steps」→「1 loop / 7 steps」に補正される

### 実施しない

- `toast-persistence-verification.md`（low）— 副次候補として handoff に挙がっていたが、Windows 実機での目視検証であり quick ワークフローのヘッドレス前提では完結しない。本バージョンスコープからは除外し、開発者の対面セッションで別途消化する判断。
- `issue-review-rewrite-verification.md`（medium）— util 単体で消化不能（`app` / `infra` カテゴリの起動待ち）。継続持ち越し。
- `plan-handoff-frontmatter-drift.md` / `plan-handoff-omission-tracking.md` / `rules-paths-frontmatter-autoload-verification.md` / `scripts-readme-usage-boundary-clarification.md` — 観察系または raw のため本バージョンでは未着手。
- PHASE8.0 骨子作成 — 既定 PHASE は完走済だが、PHASE 規模の未解決テーマが util カテゴリに浮上していないため見送り（ver15.4 RETROSPECTIVE §3 推奨に従う）。

## 想定成果物

- `scripts/claude_loop_lib/logging_utils.py` — TeeWriter 非依存の stderr 出力ヘルパ追加（数行）
- `scripts/claude_loop_lib/notify.py` — `_notify_beep` 内 `print()` 4 行を新ヘルパ経由に差し替え
- `scripts/claude_loop.py` — `_run_auto` の `RunStats` 合算ロジック修正（`completed_loops` のみ phase1 を除外）
- `scripts/tests/test_notify.py` — fallback テストで stderr 出力先のアサート追加・修正
- `scripts/tests/test_claude_loop_integration.py` — auto モードで `loops_completed` が phase2 のみを反映するアサート追加

## ワークフロー選択根拠

**`workflow: quick`** を選択。

- 全件 `status: ready` であり `review` を含まない（quick の前提条件 1 を満たす）
- 変更対象は本体 3 ファイル（`logging_utils.py` / `notify.py` / `claude_loop.py`）+ テスト 2 ファイルで、合計差分は 100 行以内に収まる見込み（ヘルパ追加数行・置換数行・合算ロジック数行・テストアサート数行）
- ver15.4 で同ファイル群を編集済で文脈が新鮮、設計判断の余地が小さく `/split_plan` での詳細分解を要さない
- handoff（`FEEDBACKS/handoff_ver15.4_to_next.md`）も明示的に「quick ワークフローで消化できる粒度の見込み」と記載

## 事前リファクタリング要否

**不要**。`logging_utils.py` への stderr ヘルパ追加は新規追加であり既存コード差し替えを伴わない。`_notify_beep` / `_run_auto` の修正は局所的で先行整理対象なし。

PLAN_HANDOFF.md は別ファイルで作成（quick 必須節: 関連ファイル / 後続 step 注意点の 2 節）。
