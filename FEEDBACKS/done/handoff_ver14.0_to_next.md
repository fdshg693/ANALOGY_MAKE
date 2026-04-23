---
step: issue_plan
---

## 背景

ver14.0 で PHASE7.0 §6+§7+§8 を一括完了（retrospective の FEEDBACK handoff / `.claude/rules/scripts.md` 新設 / workflow prompt・model 評価節の追加）。PHASE7.0 は全節実装済となったが、PHASE8.0 骨子作成は ver14.0 成果を 1〜2 ループ観察してからにする判断を ver14.0 RETROSPECTIVE §1 で下した。

したがって ver14.1 は **ISSUES 消化に寄せた軽量ループ** を推奨する。

## 次ループで試すこと

1. **`ISSUES/util/medium/cli-flag-compatibility-system-prompt.md`（`raw/ai`）の再評価**
   - ver14.0 §7 で `.claude/rules/scripts.md` §3（CLI 引数処理）に CLI flag 追加時の作法を集約済。
   - ISSUE 本文の懸念（CLI flag 変更時に system prompt / 仕様ドキュメント間で不整合が残る）が rules §3 で網羅できているかを実動作レベルで確認する。
   - **判定**: 吸収済 → `done/` へ移動。残論点 → `ready` 昇格して ver14.1 で消化。

2. **`ISSUES/util/low/system-prompt-replacement-behavior-risk.md`（`raw/ai`）の再評価**
   - ver14.0 §8 で `/retrospective` SKILL §3.5 に「workflow prompt / model 評価」を追加済。
   - ISSUE の懸念（system prompt を差し替えた際の挙動検証不足）が §3.5 評価観点として織り込めているか確認。
   - **判定**: 織り込み済 → `done/`。不十分 → 評価テンプレへの追記でカバーするか ready 昇格で消化するか判断。

3. **ver14.1 は quick ワークフロー候補**
   - 上記 1〜2 件が `done` 化のみで完結するなら軽量。昇格消化を含めても 3 ファイル / 100 行閾値内に収まる見込み。
   - 閾値を超える場合は full へエスカレーション（`/issue_plan` で判断）。

4. **PHASE7.0 ver14.0 成果の運用観察ポイント（§3.5 評価時に意識する）**
   - §4.5 handoff: 本ファイルが次ループで実際に 1 回消費されて `FEEDBACKS/done/` へ移動する挙動を確認
   - `.claude/rules/scripts.md` の `paths: scripts/**/*` frontmatter が agents にどう解釈されたか（ver14.0 MEMO §リスク 6 の先送り事項）
   - §3.5 評価が形骸化していないか（差分評価基準で不要な step まで評価していないか）

## 保留事項

- **PHASE8.0 骨子作成**: ver14.0 成果の運用観察が 1〜2 ループ分溜まるまで先送り。早くて ver14.2 or ver15.0 の `/issue_plan` で判断。
- **`issue-review-rewrite-verification.md`**: util 単体消化不能のため ver6.0 以来継続持ち越し。app / infra カテゴリで `/issue_plan` を動かす機会まで待つ（ver14.1 でも触らない）。
- **`rules-paths-frontmatter-autoload-verification.md` / `scripts-readme-usage-boundary-clarification.md`**: ver14.0 で新規作成。ver14.1 では観察対象として保持し、着手判断は後続ループに委ねる。
- **`.claude/rules/README.md` 新設**: 現状 2 ファイルで過剰設計。3 ファイル目追加時まで保留。
