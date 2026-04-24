---
workflow: full
source: issues
---

# ver16.5 RETROSPECTIVE — `issue_review` SKILL に `ready/ai` 長期持ち越し再判定ルート追加

本版は PHASE8.0 完走後 2 本目の minor 版。`issue-review-long-carryover-redemotion` を単一主眼として、`issue_review` SKILL §1.5 / §5 第 3 ブロックを追補し、`issue_plan` SKILL 側も同期した。コード変更ゼロ・仕様書のみの追補。

---

## §1 ドキュメント構成

### MASTER_PLAN

- `docs/util/MASTER_PLAN/PHASE8.0.md` 全 3 節は ver16.3 で完走済、本版で touch なし
- **PHASE9.0 骨子作成: 据え置き継続**。本版で ready/ai が 4→3 件に減るはずが、wrap_up で F-1/F-3 観察 ISSUE を 2 件起票したため **ready/ai=5 件に増加**。既存 ISSUES による吸収余地はむしろ拡大しており、次 PHASE 骨子の必要性は依然なし
- 次ループの `/issue_plan` で PHASE9.0 骨子作成を検討する材料は生じていない

### CLAUDE.md

- 分割不要。本版で CLAUDE.md への変更なし

### docs カテゴリ別

- minor のため `CURRENT.md` 新規作成なし、`CHANGES.md` のみ
- PLAN_HANDOFF.md は 5 節構成で手厚く書いたが、後続 step は実際に (1) 測定指標の第一候補、(2) 閾値 7 日、(3) frontmatter 不変ガード、(4) 第 3 ブロック書式を全て踏襲しており、情報のうち「選定理由」節は後続 step 実行時点ではほぼ参照不要だった。ただし retrospective 時点で除外理由を見返す価値は残るため削減は不要

### ISSUES

- 消化 1 件（`issue-review-long-carryover-redemotion` → `done/`）
- 新規起票 2 件（wrap_up で `F-1: issue-review-7day-threshold-observation` / `F-3: issue-review-llm-date-calc-observation` を low/ready/ai として起票）
- 正味 `ready/ai` = 4 − 1 + 2 = **5 件**に増加

---

## §2 バージョン作成の流れ

### `full` workflow 6 step 評価

| step | 所要 / cost (概算) | 計画乖離 | 評価 |
|---|---|---|---|
| issue_plan | 6m46s / $2.17 (推定、前版同規模) | なし | 単一 ISSUE 主眼を明確抽出、PLAN_HANDOFF 5 節が後続の迷いを最小化 |
| split_plan | ~5m / ~$1.3 | なし | REFACTOR は事前リファクタ不要で 1 行結論。IMPLEMENT.md を §A〜§D + §F（リスク 5 項目）で論点固定 |
| imple_plan | ~4m30s / ~$1.25 | D-1 (コードフェンス記法調整) | IMPLEMENT.md 指示の「4 連バッククォート外側」が実際にはネストせず既存書式との一貫性を損なうため、3 連に修正（実装時の合理的判断） |
| wrap_up | ~2m / ~$0.4 | F-1/F-3 を「対応不要」ではなく「ISSUES 起票」に分類 | F-1 閾値妥当性・F-3 LLM 日付計算確認の先送り項目を明示 ISSUE 化。**次版 `/issue_plan` から §1.5 判定ルート上で自然に拾われる運用導線**を作った点は◎ |
| write_current | ~2m / ~$0.4 | CHANGES.md のみ作成（minor） | 変更 7 ファイル + 技術判断 3 節を明快に記載 |
| retrospective | 本 step | — | §1.5 の初回書式確認を本 step で実施（下記 §3.5） |

### 良く機能した点

- **PLAN_HANDOFF §後続 step への注意点** に「測定指標 3 案」「閾値 N の既定値」「frontmatter 不変ガード」「第 3 ブロック書式案」を事前列挙したことで、`/imple_plan` が論点選択に時間を使わずに済んだ。ver16.3 からの運用定着を再確認
- **wrap_up での観察 ISSUE 起票**: F-1/F-3 をローカル MEMO 記述のみで留めず独立 ISSUE 化した判断が良好。本版が導入した §1.5 判定ルート自体でその後観察できる状態を作った（自己言及的な検証経路）
- **実装時の書式一貫性判断**: IMPLEMENT.md の指示より既存 SKILL 書式の一貫性を優先した D-1 判断は、後続 step での差し戻しコストを回避できた

### 改善候補

- **PLAN_HANDOFF §選定理由・除外理由 の情報重複**: ROUGH_PLAN.md にも類似内容があり、ver16.5 は ready/ai 4 件の内訳表が PLAN_HANDOFF のみに存在するという形で差別化できていた。今後も「内訳表は PLAN_HANDOFF、要約は ROUGH」の分担を維持したい
- **wrap_up での観察 ISSUE 起票ルール化**: 今回は MEMO §F リスクの「検証先送り」項目を wrap_up が自然に ISSUE 化したが、これは実装者の良識依存で SKILL 文言には定まっていない。次回類似ケースで同じ運用が再現されるか要観察（2 サンプル目を待ってから SKILL 化判断）

---

## §3 次バージョン推奨

### 材料

1. **ISSUE 状況**: 本版消化後の `ready/ai` = **5 件**（medium=2, low=3）。うち 2 件（F-1 / F-3）は本版由来の観察 ISSUE で、次 `/issue_plan` 時点では `reviewed_at < 7 日` のため §1.5 判定対象外
2. **MASTER_PLAN**: PHASE8.0 完走済、PHASE9.0 未定義（据え置き）
3. **現行 PHASE 完走状態**: 全 3 節 ✅（ver16.3 から変化なし）

### ready/ai 5 件の AI 着手可能性評価

| ISSUE | 持ち越し日数 | AI self-consume 可能性 |
|---|---|---|
| `issue-review-rewrite-verification` (medium) | 2 日 | ❌ 他カテゴリで `review/ai` ISSUE 発生時の観察が前提 |
| `deferred-resume-twice-verification` (medium) | 1 日 | △ research workflow 必要（`experiments/` 実測） |
| `toast-persistence-verification` (low) | 1 日 | ❌ Windows 実機目視必須（人間作業） |
| `issue-review-7day-threshold-observation` (low) | 0 日 | △ 本版由来、次 `/issue_plan` での §1.5 発火観察が本体 |
| `issue-review-llm-date-calc-observation` (low) | 0 日 | ✅ 次 `/issue_plan` の出力サマリ目視で検証可能 |

### 推奨

**ver16.6（マイナー）**。理由:

- AI self-consume 可能な ISSUE が実質「F-3 LLM 日付計算確認」のみで、しかも検証対象が **次 `/issue_plan` の出力そのもの**。`/issue_plan` step 実行 → ROUGH_PLAN.md §再判定推奨 ISSUE ブロックの書式確認 → F-3 ISSUE 消化、という 1 ループで完結可能
- F-1 閾値妥当性は 5 日以上の経過待ちで本版時点では観察不能。本質的に時間差観察であり、ver16.6〜16.8 の自然進行で採取される
- `raw/ai` 2 件（`rules-paths-frontmatter-autoload-verification` / `scripts-readme-usage-boundary-clarification`）を review/ai に昇格判定する選択肢もあるが、ver16.5 の `/issue_plan` review フェーズでは据え置きされており、次ループでも同判定になる可能性が高い
- アーキテクチャ変更・新規外部依存・破壊的変更なし、次 PHASE 着手材料もなし → メジャー昇格の根拠なし

### 次バージョン候補

- **次マイナー: ver16.6**（F-3 ISSUE 消化 + §1.5 初回発火観察）
- 次メジャー: ver17.0（PHASE9.0 着手 or アーキ変更まで保留）

---

## §3.5 §1.5 判定ルートの初回書式確認（本版主眼の動作確認）

本 retrospective 実行時点で util カテゴリ ready/ai 5 件を §1.5 判定ルートで手動チェック:

| ISSUE | reviewed_at | 経過日数 | §1.5 対象? |
|---|---|---|---|
| `issue-review-rewrite-verification` | 2026-04-23 | 2 日 | No |
| `deferred-resume-twice-verification` | 2026-04-24 | 1 日 | No |
| `toast-persistence-verification` | 2026-04-24 | 1 日 | No |
| `issue-review-7day-threshold-observation` | 2026-04-25 | 0 日 | No |
| `issue-review-llm-date-calc-observation` | 2026-04-25 | 0 日 | No |

→ 想定通り「## 再判定推奨 ISSUE: 該当なし」出力となる。初回発火予測: 最早 `issue-review-rewrite-verification` が 2026-04-30 以降（閾値 7 日経過）。ただし途中で `review/ai` に戻されて `reviewed_at` が更新されると起点がずれる。

**観察上の気づき**: ISSUE の初出 version（ver6.0 起票）と `reviewed_at`（2026-04-23）の実経過は実カレンダー 2 日分しか離れていない（ver6.0 コミット日 2026-04-23 を `git show` で確認）。本プロジェクトの version bump 速度は 1 日あたり 3〜5 minor に達することがあり、「ver6.0 持ち越し = 長期停滞」という直感と実カレンダー経過は一致しない。閾値 7 日は「5 バージョン ≒ 5〜10 日」という設計前提よりも**速い bump 速度**で運用される可能性があり、F-1 観察時に「5 日でも過鈍」と判断される余地が出てくる。F-1 観察時にはこの速度ギャップも併せて記録すること。

---

## §4 ISSUES 整理

### 削除（消化完了 → done/ 移動）

- `ISSUES/util/low/issue-review-long-carryover-redemotion.md` → `ISSUES/util/low/done/` （ver16.5 主眼として消化、git mv 済）

### 持ち越し（削除せず）

- `ISSUES/util/medium/issue-review-rewrite-verification.md`（`ready/ai`、着手条件未成立）
- `ISSUES/util/medium/deferred-resume-twice-verification.md`（`ready/ai`、research workflow 待ち）
- `ISSUES/util/low/toast-persistence-verification.md`（`ready/ai`、人間実機目視必須）
- `ISSUES/util/low/issue-review-7day-threshold-observation.md`（`ready/ai`、本版由来、時間経過観察）
- `ISSUES/util/low/issue-review-llm-date-calc-observation.md`（`ready/ai`、本版由来、次版 `/issue_plan` で観察可）
- `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md`（`raw/ai`、triage 据え置き）
- `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md`（`raw/ai`、triage 据え置き）

### レトロスペクティブで追記すべきと判断したもの

なし。F-1/F-3 は wrap_up で独立 ISSUE 化済。

---

## §5 即時適用したスキル変更

**なし**。本版で `issue_review` SKILL / `issue_plan` SKILL を大規模に追補した直後であり、運用観察前に追加変更を重ねるのは SKILL の設計意図（段階的拡張）に反する。§3.5 の気づき（bump 速度と閾値のギャップ）も 1 サンプルでは SKILL 変更に踏み込む根拠に足りない。F-1 観察結果が出た後続版で判断する。

---

## §6 次ループ handoff

`FEEDBACKS/handoff_ver16.5_to_next.md` を作成する。要点:

- **次版主眼候補**: F-3 `issue-review-llm-date-calc-observation` の消化（次 `/issue_plan` ROUGH_PLAN.md §再判定推奨 ISSUE の書式目視）
- **副次観察**: §1.5 判定ルートの書式崩れ / 誤検出 / 漏れを retrospective でチェック
- F-1 閾値妥当性は自然な時間経過で採取継続（ver16.7〜16.8 頃に初回発火想定）
- `raw/ai` 2 件は次ループでも据え置き判定になる可能性が高いが、3 ループ目（ver16.7 以降）では triage ルート自体の設計見直しを検討する価値あり

---

## §8 workflow prompt / model 評価（差分評価）

本版は `scripts/claude_loop.yaml` 全 step の YAML 設定を前版から変えずに運用（差分ゼロ）。直前 ver16.3 RETROSPECTIVE §8 から観察継続の項目のみ再評価する。

| step | model | effort | 分類 | 理由・次ループ案 |
|---|---|---|---|---|
| issue_plan | opus | high | 維持 | ROUGH_PLAN + PLAN_HANDOFF 5 節を明快に生成、単一 ISSUE 消化 + SKILL 設計判断に十分な粒度 |
| split_plan | opus | high | 維持 | IMPLEMENT.md に §F リスク 5 項目を事前明記、plan_review_agent 承認 |
| imple_plan | opus | high | **調整候補（継続観察）**| 実装量が SKILL.md × 2 + README × 1 の計 ~90 行追補で小規模。ver16.3 §8 と同種ケースで 2 サンプル目。`/split_plan` で生成される IMPLEMENT.md の総行数 / 推定 edit 箇所数で effort を自動分岐させる案を **ver16.6 以降** で試す価値が出始めた。ただし判断コスト自体が発生するため、次ループ 1 回分は `--effort medium` で手動試行して品質差を sample 化したい |
| wrap_up | sonnet | medium | 維持 | 残課題 7 項目を適切に分類（4 完了 / 2 ISSUE 化 / 残は不要判定）、cost 低め |
| write_current | sonnet | high | 維持 | CHANGES.md 7 ファイル一覧 + 技術判断 3 節を構造化、MASTER_PLAN は触らず適切 |
| retrospective | opus | medium | 維持 | 本 step。§3.5 動作確認 + §8 評価で medium は妥当 |

**特記**:

- ver16.3 §8 の imple_plan 「実装量小ケースで effort 下げ」候補は本版で 2 サンプル目が溜まった。次ループで FEEDBACK 経由で 1 回試行を handoff する（§4.5 参照）
- モデル運用としては「opus-high」集中偏重が継続しており、wrap_up / retrospective のみ sonnet / opus-medium に下げている運用が安定。これは維持

---

## 総括

- 単一 ISSUE 主眼の minor 版として `issue_review` SKILL §1.5 / §5 第 3 ブロック追加を完遂。scripts/ 変更ゼロ・テスト無影響で SKILL 層に閉じた拡張
- §1.5 判定ルートは本 retrospective 時点で「該当なし」出力が想定通り得られ、書式レベルの破綻なし
- **副産物**: wrap_up が F-1/F-3 観察を独立 ISSUE 化し、本版導入機能そのものを次版で検証する自己言及的な運用導線を作った
- F-1 観察時には実経過日数と version bump 速度のギャップも記録する方針を §3.5 で明文化
- imple_plan effort 下げ候補が 2 サンプル目に達した。次ループで 1 回試行を handoff
