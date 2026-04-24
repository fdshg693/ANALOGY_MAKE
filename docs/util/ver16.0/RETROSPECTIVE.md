# ver16.0 RETROSPECTIVE — PHASE8.0 §1 `research` workflow 新設

## §1 ドキュメント構成

### MASTER_PLAN

- `docs/util/MASTER_PLAN/PHASE8.0.md` は ver16.0 で §1 に ✅ 追記済み。§2（deferred execution）・§3（step 単位 token/cost 計測）は未着手で残る
- 新 PHASE 骨子の必要性: **現時点で不要**。PHASE8.0 は 3 節構成のうち §1 のみ完走、§2 / §3 が ver16.1〜16.2 で消化予定。次ループで次 PHASE（PHASE9.0 等）新設を検討する必要はない

### CLAUDE.md

- ver16.0 で `RESEARCH.md` / `EXPERIMENT.md` の説明が追記され、プロジェクト直下 `CLAUDE.md` の `## バージョン管理規則` が肥大化しつつある（research workflow 限定の 4 節説明が入った）
- ただし分割するほどの規模ではない（1 セクション内の箇条書き追加にとどまる）。**当面分割不要**、PHASE8.0 §2 / §3 で追加の workflow 仕様が入ったら再評価

### docs カテゴリ別

- `docs/util/ver16.0/` に `CURRENT.md` / `CURRENT_scripts.md` / `CURRENT_skills.md` が分割で生成済。メジャー版の標準形に沿う
- `RESEARCH.md` / `EXPERIMENT.md` は **本版では生成されていない**（本版自体は `workflow: full` で走り `research` の成果物対象外）。自己適用は ver16.1 以降の検討事項

## §2 バージョン作成の流れ

### 全体評価

6 step full workflow は **計画通りに完走**。以下が良く機能した:

- `/issue_plan` が「ready/ai プールが構造的カリオーバーで塞がっている」ことを根拠に PHASE8.0 着手を正しく判断
- `PLAN_HANDOFF.md` §5「未解決論点」（4 条件、artifact 命名、8 step 固定、mock vs 実 CLI）が `/split_plan` の `IMPLEMENT.md` §0 で一括確定された。**handoff の役割が明確に効いた好例**
- `/imple_plan` の MEMO.md §「リスク・不確実性の対応記録」が `IMPLEMENT.md` §1 の各項目と 1:1 で書かれていて検証の追跡性が高い
- 計画との乖離ゼロ、テスト 276→280 全 green、pre-existing 警告のみ

### 改善候補

- **YAML sync 契約が 6 ファイルに拡大**: `claude_loop*.yaml` の `command` / `defaults` セクションを 6 ファイル間で手で同期する運用は、PHASE8.0 §2 / §3 で更に YAML が増えた場合に破綻する。ver16.1 で §2 着手時に「共通部分を 1 箇所から生成する」簡易スクリプト（もしくは 起動時 validation での diff 検出）の導入余地あり。本版では ver16.0 スコープ外として対応せず
- **`IMPLEMENT.md` が 566 行と肥大**: 新規 SKILL 2 件・新 YAML 1 件・既存 SKILL 複数変更が同居するため必然。`split_plan` SKILL 側で「IMPLEMENT.md が 400 行超える場合は分割検討」のガイドを追記するほどの頻度ではない（メジャー PHASE 着手時のみ）

## §3 次バージョン推奨

### 材料

1. **ISSUE 状況**: `ready/ai` 2 件はどちらも構造的カリオーバー（`issue-review-rewrite-verification` / `toast-persistence-verification`）で util 単独では消化不能
2. **MASTER_PLAN 次項目**: PHASE8.0 §2（deferred execution）が ver16.1 に明示的に割り当てられている
3. **現行 PHASE 完走状態**: PHASE8.0 は §1 のみ完了。§2 / §3 が残るため次 PHASE 骨子作成は不要

### 推奨

**ver16.1 メジャー**。理由:

- PHASE8.0 §2（deferred execution）着手。新モジュール `deferred_commands.py` 新規・`claude_loop.py` の実行ライフサイクル変更・新テスト追加を伴い、`quick` 条件（3 ファイル・100 行）を大幅超過
- §2 自体が「事前調査・試行を挟む価値が高い」と PHASE8.0 §1 本文で明言されており、ver16.0 で新設した **`research` workflow の初の本格利用ケース**として最適
- マイナー（ver16.1）ではなくメジャー（**ver17.0**）の余地もあるが、**PHASE8.0 §2 は PHASE8.0 骨子の一節**であり新 PHASE ではないため、ver16.x のマイナー枠が妥当

（`/issue_plan` 側では **ver17.0** にはしない。PHASE8.0 の続きの節なのでメジャー相当の差分量ではあるが、PHASE 単位で major を切る運用のため ver16.1 扱い）

**ISSUE 消化を次ループで試みるか**: 試みない。`ready/ai` 2 件は本バージョンでも述べたとおり util 単独消化不能で、次ループに倒しても同じ判断が再現される。次メジャーワーク（PHASE8.0 §2）に集中する

## §3.5 workflow prompt / model 評価

### 評価対象: ver16.0（`claude_loop.yaml`、6 step full workflow）

直前バージョン ver15.6 は `quick` 走行、ver15.5 以前は PHASE7.1 系の別テーマ。ver16.0 は full workflow を走らせた久々のメジャー版のため、本節で差分評価する。

| step | model | effort | 分類 | 理由・次ループ案 |
|---|---|---|---|---|
| issue_plan | opus | high | 維持 | ready/ai プールの構造的カリオーバー判定 → PHASE8.0 §1 着手判断が的確。effort 下げるとこの判断を落とす恐れ |
| split_plan | opus | high | 維持 | `IMPLEMENT.md` §0 で handoff §5 未解決論点 4 件を全部クローズ。effort 高の価値を出している |
| imple_plan | opus | high | 維持 | 計画乖離ゼロ・テスト追加 4 件・6 YAML 同時編集をミスなく完走。effort 下げる余地なし |
| wrap_up | sonnet | medium | 維持 | 完了条件 5 項目の ✅ 付与とフロントマター更新のみ。opus 不要、現状で十分 |
| write_current | sonnet | medium | 調整候補 | メジャー版 `CURRENT.md` 分割（3 ファイル）を正しく生成したが、次の PHASE8.0 §2 以降で `CURRENT.md` 複雑度が上がる見込み。ver16.1 で **effort: medium → high** を試す（model 変更は不要） |
| retrospective | opus | medium | 維持 | 本 step。現状で議論粒度は妥当 |

### 保留メモ

- `research` workflow の 8 step（`claude_loop_research.yaml`）は本版で新設されたが実走していない。ver16.1 で self-apply する場合が初実行となるため、**次ループ後の retrospective でまとめて評価**。本節では事前評価しない（差分評価の原則）

## §4 ISSUES 整理

ver16.0 で解決した ISSUE は **ゼロ**（本版は MASTER_PLAN driven の PHASE 着手）。削除・移動対象なし。

持ち越し 4 件は既存状態のまま据え置く:
- `ISSUES/util/medium/issue-review-rewrite-verification.md`（ready/ai、util 単独消化不能）
- `ISSUES/util/low/toast-persistence-verification.md`（ready/ai、Windows 実機必須）
- `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md`（raw/ai、triage 待ち）
- `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md`（raw/ai、triage 待ち）

## §5 即時適用したスキル変更

本版では SKILL 編集の即時適用は **なし**。理由:

- ver16.0 のメジャーワーク自体が `.claude/skills/` に `research_context` / `experiment_test` 新設 + 既存 SKILL 4 件（`issue_plan` / `split_plan` / `imple_plan` / `meta_judge/WORKFLOW.md`）更新で、既に `/imple_plan` step で反映済み
- retrospective step 時点で追加で気付いた SKILL 文言改善は発生していない（バージョン作成の流れ自体が計画通り完走したため）
