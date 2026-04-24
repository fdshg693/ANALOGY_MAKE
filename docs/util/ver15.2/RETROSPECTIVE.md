# ver15.2 RETROSPECTIVE

PHASE7.1 §2（`QUESTIONS/` queue + `question_research` workflow）add-only 実装の振り返り。full workflow 全 6 ステップ完走。

## §1 ドキュメント構成整理

### MASTER_PLAN

- `docs/util/MASTER_PLAN/PHASE7.1.md` — §1 / §2 実装済、§3 / §4 未着手。**現行 PHASE 未完走**のため新 PHASE 骨子作成は不要。
- §3（`ROUGH_PLAN.md` / `PLAN_HANDOFF.md` 分離）は ver15.3 で着手予定、§4（run 単位通知）は ver15.4 以降で扱う想定。
- MASTER_PLAN 側のファイル分割・再構成は不要（PHASE7.1.md は単一ファイルで収まっている）。

### CLAUDE.md

- プロジェクト CLAUDE.md / `.claude/CLAUDE.md` / ROLE.md は肥大化兆候なし。`scripts/` 詳細は `.claude/rules/scripts.md` 側に既に分離済み。追加分割不要。
- ver15.2 で追加した `QUESTIONS/` / `question_research` / `question_status.py` / `question_worklist.py` の記述は既に CLAUDE.md のディレクトリ構成節に反映済み（`/write_current` 成果物）。

### ISSUES / QUESTIONS

- `ISSUES/util/` 残存 3 件（`issue-review-rewrite-verification.md` / `rules-paths-frontmatter-autoload-verification.md` / `scripts-readme-usage-boundary-clarification.md`）は全て **持ち越し中**（削除対象なし）。理由は §3 でも再掲する。
- 付随消化 2 件（`imple-plan-four-file-yaml-sync-check.md` / `readme-workflow-yaml-table-missing-scout.md`）は ver15.2 中に `done/` 化済み。
- `QUESTIONS/util/` は骨格のみで初期 Question 投入なし。これは PHASE7.1 §2 の対象外であり想定通り。

## §2 バージョン作成の流れの検討

本バージョンは `workflow: full` を選定し、6 ステップを完走した。各 step の効果:

| step | 効果 | 備考 |
|---|---|---|
| issue_plan | 良好 | ROUGH_PLAN.md で §2 選定・除外 ISSUE・付随 ISSUE を体系的に切り分け。`/split_plan` 向け handoff 節が後工程の判断を簡潔にした |
| split_plan | 良好 | IMPLEMENT.md のリスク表 R1〜R10 が MEMO.md の検証結果テーブルに 1:1 で対応。drift-guard テスト（R1）は `RESERVED_WORKFLOW_VALUES` 追加運用の安全性を機械的に担保 |
| imple_plan | 良好 | 計画との乖離なし。テスト 236→252 件全件 green。付随 ISSUE 2 件を同一バージョン内で合流消化できた |
| wrap_up | 良好 | MEMO.md §4 の対応表で「検証済/先送り根拠/ISSUE 起票要否」を明示 |
| write_current | 良好 | `CURRENT_scripts.md` / `CURRENT_skills.md` への追記は 5 ファイル同期契約への更新を含めて齟齬なし |
| retrospective | 本ステップ | — |

### 気づき（改善材料）

1. **付随 ISSUE の合流消化パターンが成立**: ver15.2 では ROUGH_PLAN §「付随的に触れる ISSUE」→ IMPLEMENT.md での合流判断 → `done/` 化、の流れが機能。同パターンは今後の add-only 系バージョンでも有効。`/split_plan` SKILL の合流判断手順は暗黙知のまま運用できており、現状追記不要。
2. **`review` ステータス不在は明示的な設計判断**: `questions.py` が `review` を持たない点は `.claude/rules/scripts.md` §4 に記載済。rule 本文で「`issues.py` と異なり review 不在」と注意書きがあり、後続の Question queue 利用者が誤解しにくい。
3. **drift-guard テストの有用性**: `RESERVED_WORKFLOW_VALUES` と `resolve_workflow_value` の if-chain 同期をテストで守る仕組みは、今後 workflow が増えた場合にも回帰防止として効く。PHASE7.1 §3 で新 workflow 追加が発生する場合も同パターンで守れる。

### SKILL / scripts への即時改善提案

本バージョンの流れで SKILL 側を修正すべき新規事象は発生しなかった（`.claude/skills/imple_plan/SKILL.md` / `quick_impl/SKILL.md` への「YAML 同期チェック」追記は既に ver15.2 本体で実施済）。**本 retrospective ステップでの `.claude/` 追加編集は行わない**。

## §3 次バージョンの種別推奨

### 判断材料 3 点

1. **ISSUE 状況**: `ready / ai` 1 件のみ（`issue-review-rewrite-verification.md`、util 単体消化不能）。AI が util で消化できる ready ISSUE は実質ゼロ。
2. **MASTER_PLAN 次項目**: PHASE7.1 §3（`ROUGH_PLAN.md` / `PLAN_HANDOFF.md` 分離）と §4（run 単位通知）が未着手。§3 は既存 SKILL 3 本（`issue_plan` / `split_plan` / `quick_impl`）と VERSION_FLOW.md の改訂を伴う**既存 plan 文書の分割改訂**で、破壊性が中〜高。
3. **現行 PHASE 完走状態**: PHASE7.1 は §1 / §2 完了で全 4 節中 2 節済。**未完走**のため、新 PHASE8.0 骨子作成は不要。

### 推奨

**次バージョンは ver15.3（マイナー）、PHASE7.1 §3 に着手**。

根拠:

- MASTER_PLAN 内の継続節 → マイナー扱いが自然（ver15.2 選定基準と同型）
- アーキテクチャ変更なし（既存 SKILL 本文と `ROUGH_PLAN.md` 成果物の責務分割であり、workflow runtime の変更ではない）
- §3 単独で扱う（§4 は更に後送り、§2 と §4 の同時着手は scope 過大という ver15.2 ROUGH_PLAN §除外理由と同じ）
- `issue-review-rewrite-verification.md` は util 単体消化不能のため引き続き持ち越し。`app` / `infra` カテゴリ起動時まで保留

### メジャー昇格条件

ver16.0 は **PHASE7.1 §3 / §4 完了 → 次 PHASE（PHASE8.0）骨子要否判断** の時点で検討。本バージョン時点では時期尚早。

### 持ち越し ISSUE の扱い

| path | 判定 | 理由 |
|---|---|---|
| `ISSUES/util/medium/issue-review-rewrite-verification.md` | 持ち越し（削除しない） | util 単体消化不能（ver6.0 以来）。`app` / `infra` 起動時に消化判断 |
| `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md` | 持ち越し（削除しない） | ver14.0 観察継続。運用中に問題が顕在化するまで保留 |
| `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md` | 持ち越し（削除しない） | ver14.0 観察継続。READM/USAGE の境界検討は §3 とは独立 |

## §3.5 workflow prompt / model 評価

### 省略判断

ver15.2 では `scripts/claude_loop.yaml` 等の `command` / `defaults` / `steps` に対して **model / effort / prompt の変更は行っていない**（変更は `claude_loop_question.yaml` 新規追加と、既存 4 ファイルの NOTE コメント相互参照のみ）。

「差分評価（直前バージョンから変えた step のみ再評価）を基本姿勢とする」の原則に従い、本節は形骸的な全 step 評価を**省略**する。

### 1 点観察メモ（次ループへは持ち越さない）

- `issue_plan`（opus / high）: ver15.2 で ROUGH_PLAN.md の「ISSUE 選定 × MASTER_PLAN 次項目 × 付随 ISSUE 合流判断」を 1 step で扱いきれており、現設定は過剰ではない。PHASE7.1 §3 が「既存 SKILL 本文改訂」という判断系タスクになるため、同じ effort を維持する想定。
- `split_plan`（opus / high）: IMPLEMENT.md のリスク表（R1〜R10）が実装後の MEMO.md 検証と 1:1 対応している。現設定で十分。

上記いずれも「次 1 ループ以内に試す具体的調整」ではないため、§4.5 handoff には転記しない。

## §4 振り返り結果の記録

- 本ファイル `docs/util/ver15.2/RETROSPECTIVE.md` が成果物。
- `.claude/skills/` 配下の追加編集は本ステップでは行わない（§2 で述べた通り、改修対象となる新規事象が発生していない）。
- ISSUES 整理: 削除対象なし。持ち越し 3 件は §3 の表で理由を明記。

## §4.5 次ループへの FEEDBACK handoff

次ループ `/issue_plan` に 1 回だけ渡したい補助線は以下:

1. 次バージョン ver15.3 は PHASE7.1 §3 着手が自然
2. §3 は既存 SKILL 3 本 + VERSION_FLOW.md の改訂を伴う破壊性中〜高の変更であり、ROUGH_PLAN 段階で**影響範囲の棚卸し**を明示することが後工程の品質に直結する

上記は `FEEDBACKS/handoff_ver15.2_to_next.md` に書き出す（本ステップで実施）。

## §5 コミット方針

- `docs/util/ver15.2/RETROSPECTIVE.md` 新規追加
- `FEEDBACKS/handoff_ver15.2_to_next.md` 新規追加

上記 2 ファイルをステージングしてコミット・プッシュする。
