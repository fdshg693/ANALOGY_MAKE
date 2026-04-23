# ver14.0 RETROSPECTIVE

PHASE7.0 §6+§7+§8 一括着手バージョン。`/retrospective` SKILL 自身を拡張したため、本振り返りは「§3.5 workflow prompt/model 評価」「§4.5 handoff」を**初適用**するループでもある。

## §1 ドキュメント構成整理

### MASTER_PLAN 状態

- `docs/util/MASTER_PLAN/PHASE7.0.md` は §1〜§8 全節実装済（`MASTER_PLAN.md` も ver14.0 で更新済）。
- **PHASE8.0 骨子作成**: 現時点では**不要**。理由は次の 3 点:
  1. ver14.0 で整備した handoff / rules / prompt 評価の 3 軸は、複数ループ回してはじめて運用課題が顕在化する性質のもの（§4.5 handoff の空振り率、§3.5 評価の形骸化、`paths:` frontmatter の実動作など）。観察のために最低 1〜2 ループ稼働させたい。
  2. 残 ISSUE が util 単体で 5 件（`ready/ai` 1、`raw/ai` 4）ある。このうち §7 で rules 化した内容と関連する `cli-flag-compatibility-system-prompt.md` / `system-prompt-replacement-behavior-risk.md` は「rules §3 に吸収済か」を実運用で確認したうえで `ready` 昇格 or `done` 化を判断する筋道が MEMO.md に明記されている。PHASE 新設より先に ISSUE 消化と観察に時間を割くのが合理的。
  3. 次 PHASE のテーマ候補（handoff を state DB 化する / rules を category 単位に拡張する / workflow prompt 自動調整を導入する 等）は ver14.0 の稼働結果を 1〜2 回観察してから形にした方が筋が良い。今焦って書いても空想的になる。
- したがって **次バージョン以降しばらくは「既存 ISSUE 消化 + ver14.0 成果の実運用観察」に寄せる** 方針を明示する。PHASE8.0 骨子作成の判断は早くて ver14.2 or ver15.0 の `/issue_plan` に委ねる。

### CLAUDE.md / docs 構成

- ルート `CLAUDE.md` / `.claude/CLAUDE.md` 共に肥大化の兆しなし。分割は不要。
- `.claude/rules/` は現時点 2 ファイル（`claude_edit.md` / `scripts.md`）で、MEMO.md §「将来のリファクタ」にあるとおり 3 ファイル目追加時に `README.md` 集約を検討する（本ループでは過剰設計なので触らない）。
- `scripts/README.md` と `scripts/USAGE.md` の境界曖昧性は `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md` で別途 ISSUE 化済み。

## §2 バージョン作成の流れの評価

### 各ステップ振り返り

| ステップ | 評価 | コメント |
|---|---|---|
| `/issue_plan` | 良 | `source: master_plan` / `workflow: full` の選定ロジックが機能。PHASE7.0 残 3 節の一括着手判断根拠が ROUGH_PLAN.md に十分記録されている |
| `/split_plan` | 良 | IMPLEMENT.md §6 リスク表（6 項目）が MEMO.md §リスク検証結果と 1:1 対応しており、リスク列挙 → 検証のサイクルが機能 |
| `/imple_plan` | 良 | §7 rules 先行 → §6/§8 SKILL 拡張 → docs 整合の順序が計画通り。`claude_sync export → edit → import` 手順も踏襲 |
| `/wrap_up` | 良 | `.claude/rules/README.md` 新設 / `scripts/README.md`・`USAGE.md` 境界整理は「3 ファイル目で再検討」「別 ISSUE 化」と過剰設計を避ける判断を明示 |
| `/write_current` | 良 | `CURRENT.md` を親ファイル + 3 つの子ファイル（scripts / skills / tests）に分割する構造を採用。1 ファイル肥大化を回避しており次バージョン以降も踏襲したい |
| `/retrospective`（本ステップ） | 要観察 | §3.5 / §4.5 の初適用。次バージョンで空振り／形骸化がないかを観察 |

### プロセス上の改善点

特記事項なし。PHASE7.0 実装パターン（リスク列挙 → MEMO 検証マトリクス / plan_review_agent レビュー / `claude_sync export-import`）は ver10.0 以降 5 バージョン連続で機能している。

## §3 次バージョンの種別推奨

### 判定材料

1. **ISSUE 状況**: util カテゴリの worklist は `ready/ai` 1 件（`issue-review-rewrite-verification.md`、util 単体消化不能のため実質保留）。`raw/ai` は 4 件で、うち 2 件（`cli-flag-compatibility-system-prompt.md` / `system-prompt-replacement-behavior-risk.md`）は ver14.0 成果の確認で `ready` 昇格判断可能な状態に近づいた。残 2 件（`rules-paths-frontmatter-autoload-verification.md` / `scripts-readme-usage-boundary-clarification.md`）は ver14.0 で新規作成した記録系 ISSUE。
2. **MASTER_PLAN の次項目**: PHASE7.0 全節実装済。PHASE8.0 は未着手（上述のとおり骨子作成は時期尚早）。
3. **現行 PHASE 完走状態**: PHASE7.0 は ver14.0 で完走。§1「PHASE8.0 骨子作成」判断のとおり、ISSUES 消化 + 観察に寄せる。

### 推奨

**次バージョンは ver14.1（マイナー）。ISSUES 消化に寄せた軽量ループを推奨。**

具体候補（`/issue_plan` で再判定する前提の下書き）:

- 最有力: `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md` を `raw → ready` 再評価し、rules §3 に吸収済なら `done`、残論点があれば ver14.1 で消化。ver13.0 以前の `CLI flag 変更時に system prompt と不整合` 問題に関連するため、実際に rules §3 で網羅されているかを実動作確認する価値が高い。
- 次点: `ISSUES/util/low/system-prompt-replacement-behavior-risk.md` を §3.5 評価観点に織り込めたか確認して `done` 判定。

消化対象が見つからなければ quick ワークフローで 1〜2 ISSUE まとめて片付ける。quick で 3 ファイル / 100 行以下に収まらない場合は full にエスカレーション。

メジャー（ver15.0）昇格は「PHASE8.0 骨子作成」or「handoff / rules の運用課題が溜まりきって再設計が要るタイミング」まで先送り。現時点で昇格すべき理由はない。

## §4 ISSUES 整理

PHASE5.0 以降のステータス分類に沿って整理する:

- **削除対象（対応済み）**: なし。ver14.0 で直接完了した ISSUE はゼロ。
- **持ち越し**:
  - `ISSUES/util/medium/issue-review-rewrite-verification.md` — util 単体消化不能のため ver6.0 以来継続持ち越し。app / infra カテゴリで `/issue_plan` を動かすタイミングを待つ（判断変更なし）。
  - `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md` — 次バージョン（ver14.1）で `ready` 昇格判定対象。本ループでは触らない。
  - `ISSUES/util/low/system-prompt-replacement-behavior-risk.md` — 同上。§3.5 評価観点への織り込みを確認後に `done` 判定。
  - `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md` — ver14.0 で新規作成したリスク §6 先送り記録。次ループの §3.5 評価で観察対象。
  - `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md` — ver14.0 `/wrap_up` で新規作成。別バージョンで境界整理を検討する前提で raw 保持。
- **frontmatter 無し**: util カテゴリには該当なし。

## §4.5 次ループへの handoff

次ループ（ver14.1 の `/issue_plan`）に渡したい内容は `FEEDBACKS/handoff_ver14.0_to_next.md` に書き出す。

## §8 workflow prompt / model 評価（初適用）

ver14.0 では `scripts/claude_loop.yaml` に変更なし（defaults: `sonnet` / `medium`、issue_plan / split_plan / imple_plan は `opus` / `high`、retrospective は `opus`）。初適用のため差分評価は成立しないが、実際に動かした直後の所感として 1 巡目のベースラインを残す:

| step | model | effort | 分類 | 理由・次ループ案 |
|---|---|---|---|---|
| issue_plan | opus | high | 維持 | `source: master_plan / workflow: full` の判断精度問題なし。3 つの判定材料を ROUGH_PLAN.md に漏れなく列挙できていた |
| split_plan | opus | high | 維持 | リスク 6 項目列挙 + plan_review_agent レビューで IMPLEMENT.md 品質十分。effort を落とす余地は見えない |
| imple_plan | opus | high | 維持 | `claude_sync export → edit → import` 含む複合手順を計画通り完走。§7 rules 先行 → §6/§8 SKILL 拡張の依存順序も崩れず |
| wrap_up | sonnet (default) | medium (default) | 維持 | 新設 ISSUE 化 + 過剰設計回避の判断が適切。`continue: true` で imple_plan のセッションを引き継いでおり、文脈切り替えコストなし |
| write_current | sonnet (default) | medium (default) | 維持 | CURRENT.md を 4 ファイルに分割する構造変更を sonnet/medium で捌けた。品質問題なし |
| retrospective | opus | medium (default) | 要観察 | 本ループで §3.5 / §4.5 初適用。次バージョンで「評価の形骸化」「handoff 空振り」が出るかを観察してから effort 調整を検討 |

**次ループで試す調整**: なし。ver14.1 ではまず現行設定でもう 1 周回し、§3.5 / §4.5 が実運用で機能するかを観察する。形骸化が見えたら §3.5 の差分評価基準を厳格化するなどの対応を ver14.2 以降で検討。

## まとめ

- PHASE7.0 全節完走。MASTER_PLAN も更新済。
- 次バージョンは **ver14.1（マイナー / ISSUES 消化）** を推奨。メジャー昇格は時期尚早。
- PHASE8.0 骨子作成は ver14.0 成果を 1〜2 ループ観察してから判断する（§1 参照）。
- handoff は `FEEDBACKS/handoff_ver14.0_to_next.md` に書き出す。
