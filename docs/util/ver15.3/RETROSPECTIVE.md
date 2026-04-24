# ver15.3 RETROSPECTIVE

PHASE7.1 §3（`ROUGH_PLAN.md` と `PLAN_HANDOFF.md` の役割分離）を実装したマイナーバージョン ver15.3 の振り返り。

## §1. ドキュメント構成整理

### MASTER_PLAN の現況

- `docs/util/MASTER_PLAN/PHASE7.1.md` は §1 / §2 / §3 実装済み、**§4（run 単位通知）のみ未着手**
- 現行 PHASE は未完走のため、新 PHASE（PHASE8.0）骨子作成の要否判断は時期尚早（§4 完了後に再判定）
- 次バージョンは PHASE7.1 §4 着手（ver15.4 候補）もしくは ver15.3 follow-up ISSUES の消化のどちらに寄せるかを §3 で判定する

### CLAUDE.md / VERSION_FLOW.md

- 本バージョンで `CLAUDE.md` に `PLAN_HANDOFF.md` 1 行追記、`.claude/plans/VERSION_FLOW.md` に `PLAN_HANDOFF.md` 追記を反映済み
- CLAUDE.md 全体は現時点で肥大化していない（サブフォルダ別分割の必要性は検出できない）

### ISSUES 整理

本バージョンで新規起票した follow-up ISSUES 3 件はすべて「次 1〜2 バージョンで観察を継続」が役割のため、**いずれも削除せず持ち越す**:

- `ISSUES/util/medium/plan-handoff-generation-followup.md` — 次 `/issue_plan` で PLAN_HANDOFF.md が実際に生成されるか観察
- `ISSUES/util/low/plan-handoff-frontmatter-drift.md` — frontmatter drift の運用観察
- `ISSUES/util/low/plan-handoff-omission-tracking.md` — quick 版省略乱発の観察

ver6.0 以来の持ち越し `ISSUES/util/medium/issue-review-rewrite-verification.md` も **継続持ち越し**（util 単体では消化不能、`app` / `infra` カテゴリ起動待ち）。

## §2. バージョン作成の流れの検討

### 6 ステップの効果評価

| step | 効果 | コメント |
|---|---|---|
| 1. `/issue_plan` | 良好 | ROUGH_PLAN / PLAN_HANDOFF 分離の選定理由・除外理由・影響範囲棚卸しを十分に書けていた。choice A（自己適用）判断も含め後続 step が直接活用 |
| 2. `/split_plan` | 良好 | IMPLEMENT.md §7 タイムラインで 7-1〜7-7 の順序を決め、7 リスク項目を事前列挙。plan_review_agent のレビューで choice A の工数リスクが適切に押し返された形跡は MEMO に見られない（review 指摘の記録は MEMO §計画との乖離が「乖離なし」で淡白） |
| 3. `/imple_plan` | 良好 | 計画との乖離は軽微（`issue_plan/SKILL.md` を「1 節集約」から「複数節分割」に変更）。1 コミット束ね方針通り実施。先送り 3 リスクは独立 ISSUE 化して MEMO 埋没を回避 |
| 4. `/wrap_up` | 良好 | PHASE7.1.md §3 進捗表の 1 行更新のみで簡潔 |
| 5. `/write_current` | 効果確認できず | CHANGES.md のみ生成（マイナー版なので CURRENT.md は作成対象外）。CLAUDE.md 更新の必要性は検出されていない |
| 6. `/retrospective` | （本 step） | — |

### プロセス改善の所感

- **`/split_plan` の plan_review_agent レビュー記録の薄さ**: MEMO.md には「plan_review_agent による IMPLEMENT.md レビュー結果」が明示されていない。ver15.3 のように choice A / B の選択肢提示がある場合、review 結果を MEMO か IMPLEMENT 末尾に要約として残すと後のバージョンの参考になる。ただし本件はバージョン内で問題なく解決できており、恒久的なルール化よりは次ループでの観察継続で十分
- **自己適用（choice A）の運用**: 新ファイル種別を本バージョン内で自己適用する choice A は、RETROSPECTIVE §3 で「読めば動くか」を検証できる点で価値があった。`docs/util/ver15.3/PLAN_HANDOFF.md` は full 版 5 節を満たし、後続 step が参照すべき情報をほぼ取り出せる。ただし ROUGH_PLAN.md と PLAN_HANDOFF.md で「選定理由」「除外理由」「ISSUE 状態サマリ」が **ほぼそのまま重複** している。次ループでは ROUGH_PLAN.md からこれらを除去し、PLAN_HANDOFF.md にのみ残す運用を定着させるべき（`issue_plan/SKILL.md` の仕分け方針 table が既にそう定義しているが、ver15.3 自身の ROUGH_PLAN.md には旧節が残っている移行期の揺らぎ）

### SKILL ファイルへの変更提案

- 新規の即時適用提案は **なし**。ver15.3 で `issue_plan/SKILL.md` に仕分け方針 table・quick/full 粒度 table・省略条件を追加済みで、次ループの実地適用を待つ段階
- 3 件の follow-up ISSUE（generation / drift / omission）が次バージョンで検証される形になっており、SKILL 改訂の次の契機はその観察結果ベース

## §3. 次バージョンの種別推奨

### 3 点突き合わせ

| 材料 | 状況 |
|---|---|
| 1. ISSUE 状況 | `ready/ai` 4 件（うち 1 件 util 単体消化不能、3 件は ver15.3 起票の観察型 follow-up）。高優先度 `ready/ai` なし |
| 2. MASTER_PLAN の次項目 | PHASE7.1 §4（Python スクリプト終了時の run 単位永続通知）が唯一の未着手節 |
| 3. 現行 PHASE 完走状態 | PHASE7.1 は §4 が残り未完走。PHASE8.0 骨子作成は時期尚早 |

### 推奨: **ver15.4（マイナー）、PHASE7.1 §4 に着手**

根拠:

1. **§4 が PHASE7.1 唯一の未完走節**: ここを消化すれば PHASE7.1 全体が完走し、次に PHASE8.0 骨子検討へ進める。残す理由がない
2. **follow-up ISSUE 3 件は「§4 と並走して観察」で十分**: generation / drift / omission はいずれも「次 `/issue_plan` が実際に PLAN_HANDOFF.md を生成するか」「quick 版で省略が乱発するか」を観察するもので、§4 実装のために専用バージョンを割く必要はない。§4 のバージョン内で自然に観察材料が得られる
3. **マイナー適合**: §4 は通知実装（`scripts/claude_loop_lib/notify.py` 変更）と OS 制約対応で領域が独立。新 PHASE 骨子作成・アーキテクチャ変更・新規カテゴリ追加のいずれにも該当しない → マイナー（ver15.4）
4. **`issue-review-rewrite-verification.md` は継続持ち越し**: util 単体では消化不能の制約は ver15.3 から変わらず

### 代替案（非推奨）

- **ver15.4 を ISSUES 消化専用に使う**: follow-up 3 件は観察型で、実地観察のために専用バージョンを割くのは非効率。却下
- **ver16.0（メジャー）で PHASE7.1 完走 + PHASE8.0 骨子を一括**: §4 は実装が独立しており、PHASE8.0 骨子作成と同時着手は scope 過大になる。却下

## §3.5 workflow prompt / model 評価

### 評価対象バージョン: ver15.3

ver15.3 では **workflow YAML / step の prompt / model / effort に変更なし**。ver15.2 時点の設定（defaults: sonnet / medium、issue_plan / split_plan / imple_plan / retrospective: opus / high）を継続使用。

### 差分評価（変更した step のみ）

変更なしのため **本節は省略可** だが、ver15.3 の実運用観察で得た所感のみ簡潔に記録:

| step | model | effort | 分類 | 根拠 |
|---|---|---|---|---|
| issue_plan | opus | high | 維持 | ROUGH_PLAN.md / PLAN_HANDOFF.md 両生成を含む設計判断で、選定理由・除外理由の精度・影響範囲棚卸しの網羅性ともに良好 |
| split_plan | opus | high | 維持 | IMPLEMENT.md §7 タイムライン + §9 リスク 7 項目の品質が必要水準に達していた |
| imple_plan | opus | high | 維持 | SKILL 5 本 + VERSION_FLOW + CLAUDE.md + 自己適用 PLAN_HANDOFF.md の 8 改訂を 1 コミットで破綻なく実施 |
| retrospective | opus | — | 維持 | （本 step の評価は次ループに委ねる） |

### 次ループで試す具体的調整

現時点で **試すべき調整はなし**（§4.5 に書き出さない）。次バージョン ver15.4 は通知実装が主眼で SKILL 本文の大規模改訂を伴わないため、model / effort 変更の観察機会としては不向き。ver15.5 以降で SKILL 改訂のあるバージョンで再評価する。

## §4. ISSUES 整理の結果

| ISSUE | 対応 |
|---|---|
| `ISSUES/util/medium/plan-handoff-generation-followup.md` | 持ち越し（次 `/issue_plan` 観察） |
| `ISSUES/util/low/plan-handoff-frontmatter-drift.md` | 持ち越し（1〜2 バージョン運用観察） |
| `ISSUES/util/low/plan-handoff-omission-tracking.md` | 持ち越し（quick 版で観察） |
| `ISSUES/util/medium/issue-review-rewrite-verification.md` | 持ち越し（`app` / `infra` 起動まで） |
| ver14.0 持越し 2 件（`raw/ai`） | 触らない（frontmatter は有るが `raw` のため運用中問題顕在化を待つ） |

削除対象 **なし**。

## §4.5 次ループへの FEEDBACK handoff

別ファイル `FEEDBACKS/handoff_ver15.3_to_next.md` に書き出し済み。内容は次 `/issue_plan`（ver15.4）向け:

1. 推奨着手: PHASE7.1 §4（run 単位通知）
2. 観察項目: ver15.4 の `/issue_plan` 実行時に `PLAN_HANDOFF.md` が実際に新フォーマット通り生成されるかを確認（`plan-handoff-generation-followup.md` ISSUE の消化判断材料）
3. 自己適用 choice A の教訓: ROUGH_PLAN.md から「選定理由」「除外理由」「ISSUE 状態サマリ」を PLAN_HANDOFF.md 側にのみ残すよう意識する（ver15.3 自身の ROUGH_PLAN.md では重複が残った）

## §5. Git commit

コミットメッセージ案: `docs(ver15.3): retrospective完了 — 次ver15.4でPHASE7.1§4(run単位通知)着手推奨`

変更対象:
- `docs/util/ver15.3/RETROSPECTIVE.md`（新規）
- `FEEDBACKS/handoff_ver15.3_to_next.md`（新規）
