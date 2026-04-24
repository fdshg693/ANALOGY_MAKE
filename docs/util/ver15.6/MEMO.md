---
workflow: quick
source: issues
---

# ver15.6 MEMO — PLAN_HANDOFF.md 運用観察 2 件の判定結果

## 判定基準（観察開始前に確定）

PLAN_HANDOFF.md §3 の指示に従い、判定基準を観察実施前に以下の通り固めた。

### drift 側（ISSUE: plan-handoff-frontmatter-drift.md）

- **発生率ゼロ判定基準**: ver15.3 / ver15.4 / ver15.5 の全 3 バージョンで `workflow:` / `source:` が `ROUGH_PLAN.md` と `PLAN_HANDOFF.md` で完全一致 → `done/`
- **非ゼロ判定基準**: 1 件でも不一致があれば非ゼロ扱い → follow-up ISSUE 起票

### omission 側（ISSUE: plan-handoff-omission-tracking.md）

- **乱発なし判定基準**: quick バージョンでの `PLAN_HANDOFF.md` 省略比率 50% 未満、かつ省略宣言の有無と本文引き継ぎの実在が整合 → `done/`（選択肢 A を採用）
- **乱発判定基準**: 省略比率 50% 以上または省略宣言と本文の不整合 → follow-up ISSUE 起票

PLAN_HANDOFF.md §3 の注記通り、quick 母数 1 件（ver15.5 のみ）であることを認識した上で **選択肢 A** を採用する。ver15.5 が省略していない実証実績を「兆候なし」の弱い根拠として採用し `done/` に倒す判断。

---

## 観察結果（frontmatter 機械的確認）

### ver15.3（workflow: full）

| ファイル | workflow | source | 存在 |
|---|---|---|---|
| `ROUGH_PLAN.md` | `full` | `master_plan` | 有 |
| `PLAN_HANDOFF.md` | `full` | `master_plan` | 有 |

一致: ✓ drift なし

### ver15.4（workflow: full）

| ファイル | workflow | source | 存在 |
|---|---|---|---|
| `ROUGH_PLAN.md` | `full` | `master_plan` | 有 |
| `PLAN_HANDOFF.md` | `full` | `master_plan` | 有 |

一致: ✓ drift なし

### ver15.5（workflow: quick）

| ファイル | workflow | source | 存在 |
|---|---|---|---|
| `ROUGH_PLAN.md` | `quick` | `issues` | 有 |
| `PLAN_HANDOFF.md` | `quick` | `issues` | 有 |

一致: ✓ drift なし

---

## 判定結果

### drift 側

| バージョン | ROUGH_PLAN frontmatter | PLAN_HANDOFF frontmatter | 一致 | PLAN_HANDOFF 省略 |
|---|---|---|---|---|
| ver15.3 | `full` / `master_plan` | `full` / `master_plan` | ✓ | なし |
| ver15.4 | `full` / `master_plan` | `full` / `master_plan` | ✓ | なし |
| ver15.5 | `quick` / `issues` | `quick` / `issues` | ✓ | なし |

**drift 発生率: 0件 / 3バージョン = 0%**

→ **判定: 発生率ゼロ** → `ISSUES/util/low/plan-handoff-frontmatter-drift.md` を `done/` へ移動

### omission 側

| バージョン | workflow | PLAN_HANDOFF 存在 | 省略宣言 | 本文引き継ぎ実在 |
|---|---|---|---|---|
| ver15.3 | full | 有 | なし | 有（ISSUE レビュー結果 / 判断経緯 / 関連資料 / 後続注意点を含む） |
| ver15.4 | full | 有 | なし | 有（ISSUE レビュー結果 / 推奨根拠 / 後続注意点を含む） |
| ver15.5 | quick | 有 | なし | 有（関連 ISSUE / 関連ファイル / 後続 step 注意点を含む） |

**省略比率: 0件 / 3バージョン = 0%**（全て PLAN_HANDOFF.md を実際に作成）

**quick 母数: 1件（ver15.5）**（PLAN_HANDOFF.md §3 で指摘の通り）

→ **判定: 乱発なし（選択肢 A 採用）** → `ISSUES/util/low/plan-handoff-omission-tracking.md` を `done/` へ移動

---

## 考察

### drift リスクの評価

観察期間 3 バージョンで drift 発生率ゼロだった要因として、`/issue_plan` SKILL が `PLAN_HANDOFF.md` 作成時に「frontmatter は `ROUGH_PLAN.md` と同値で重複保持」を明示しているため、AI が自然に同値をコピーする運用が定着していると推測される。

runtime 影響は現状ゼロ（`--workflow auto` は `ROUGH_PLAN.md` 側のみを参照）であり、後続 step が `PLAN_HANDOFF.md` frontmatter を独立参照するよう拡張されない限り、本 ISSUE のリスクは顕在化しない。観察継続の必要性は低いと判断し `done/` に移動した。

### omission リスクの評価

quick 母数が 1 件（ver15.5）と少ないため、「乱発なし」の根拠は弱い（PLAN_HANDOFF.md §3 の懸念通り）。ただし ver15.5 の `PLAN_HANDOFF.md` は最小記載粒度（関連 ISSUE / 関連ファイル / 後続 step 注意点）を満たしており、quality 劣化は観測されなかった。

選択肢 A（兆候なしとして `done/` に倒す）を採用した根拠:
1. 省略比率 0% は基準値（50% 未満）を大幅に下回る
2. ver15.5 の quick `PLAN_HANDOFF.md` が「本バージョン（ver15.6）」で実際に `quick_impl` の判断材料として機能した（§1 注意点の遵守 / §3 の選択肢 A/B が判断根拠として直接参照できた）ことが、quick 版 PLAN_HANDOFF.md の存在価値を実証している
3. 仮に今後 quick バージョンで省略乱発が観測された場合は、その時点で新規 ISSUE を起票すればよく、監視継続のコストが判断を留保する便益を上回らない

---

## 計画との乖離

なし。`ROUGH_PLAN.md` の想定通りに 2 件を `done/` へ移動した。follow-up ISSUE の起票は不要（観察結果がいずれもゼロ判定に倒れたため）。
