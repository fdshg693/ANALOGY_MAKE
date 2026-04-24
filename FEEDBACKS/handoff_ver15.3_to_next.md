---
step: issue_plan
---

## 背景

ver15.3 で PHASE7.1 §3（`ROUGH_PLAN.md` と `PLAN_HANDOFF.md` の役割分離）を実装完了。PHASE7.1 で未着手節は §4（Python スクリプト終了時の run 単位永続通知）のみ。util カテゴリの `ready/ai` は 4 件（3 件は ver15.3 起票の観察型 follow-up、1 件は util 単体消化不能）で、専用バージョンで消化する価値のある ISSUE は不在。

## 次ループで試すこと

- **着手推奨**: PHASE7.1 §4（run 単位通知）。ver15.4（マイナー）として扱う。`scripts/claude_loop_lib/notify.py` と `scripts/claude_loop.py` の通知呼び出し位置整理が主戦場。RETROSPECTIVE §3 参照
- **自己観察**: `/issue_plan` 実行時に新フォーマット（`ROUGH_PLAN.md` + `PLAN_HANDOFF.md`）が実際に 2 ファイル生成される動作を確認する。`ISSUES/util/medium/plan-handoff-generation-followup.md` の消化判断材料になる
- **仕分け方針の遵守**: ver15.4 の `ROUGH_PLAN.md` には「ISSUE 状態サマリ」「選定理由・除外理由」を **書かない**。それらは `PLAN_HANDOFF.md` 側にのみ残す（ver15.3 自身の ROUGH_PLAN.md では重複が残る移行期の揺らぎがあったため、意識して除去する）

## 保留事項

- `ISSUES/util/medium/issue-review-rewrite-verification.md`: util 単体では消化不能（`app` / `infra` 起動まで持ち越し）
- `ISSUES/util/low/plan-handoff-frontmatter-drift.md` / `plan-handoff-omission-tracking.md`: 1〜2 バージョン運用観察後に `validation.py` への静的チェック追加を検討
- ver14.0 持越し `raw/ai` 2 件: 運用中に問題顕在化するまで観察継続
- PHASE8.0 骨子作成: PHASE7.1 §4 完了後に再判定
