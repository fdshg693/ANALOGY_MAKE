---
step: issue_plan
---

## 背景

ver15.4 で PHASE7.1 §4（run 単位・永続通知）を実装し、PHASE7.1 全 4 節が完走した。util カテゴリの MASTER_PLAN 既定ロードマップはこれで消化済。一方で ver15.4 の wrap_up で意図的に先送りした 2 件（いずれも ver15.4 通知改修の直接の後始末）が `ISSUES/util/low/` に新規起票されている。

## 次ループで試すこと

### バージョン種別: マイナー（ver15.5）で ISSUES 消化

PHASE8.0 骨子作成は見送り、既存 ISSUES を優先消化する方針を推奨する。判断材料の詳細は `docs/util/ver15.4/RETROSPECTIVE.md` §3 参照。

### 優先着手候補（関連性が高い 2 件を束ねる）

1. `ISSUES/util/low/notify-beep-print-violation.md` — `logging_utils` に stderr ヘルパを追加し、`_notify_beep` の `print()` 直接呼び出しを差し替える（ver15.4 通知改修の `.claude/rules/scripts.md` §5 違反を解消）
2. `ISSUES/util/low/auto-loop-count-semantics.md` — `_run_auto` の loop 数合算ロジックを phase2 のみ採用する方針に変更（ver15.4 で通知本文に「2 loops」と過大表示される余地を塞ぐ）

両者は ver15.4 で触ったファイル（`scripts/claude_loop_lib/notify.py` / `scripts/claude_loop.py`）に閉じており、quick ワークフローで消化できる粒度の見込み。

### 副次候補（スコープに余裕があれば）

- `ISSUES/util/low/toast-persistence-verification.md` — 開発者実機での目視検証。本来は quick で閉じないが、判定結果のみ記録する運用なら手数は小さい

## 保留事項

- PHASE8.0 骨子の必要性は本ループでは判定しない。ver15.5〜ver15.7 で ISSUES を消化しながら util カテゴリ固有の PHASE 規模テーマが浮上するか観察
- `ISSUES/util/medium/issue-review-rewrite-verification.md` は util 単体で消化不能（`app` / `infra` カテゴリの起動待ち）。本ループでも継続持ち越し
- `plan-handoff-*` 系 3 件は観察対象。ver15.4 で新たな問題は検出されなかったが、quick ワークフロー採用時の省略判断トラッキング（`plan-handoff-omission-tracking.md`）はまだ観察機会なし
