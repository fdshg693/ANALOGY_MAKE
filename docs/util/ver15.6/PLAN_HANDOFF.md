---
workflow: quick
source: issues
---

# ver15.6 PLAN_HANDOFF — `/quick_impl` 向け引き継ぎ

## 関連 ISSUE / 関連ファイル

### 着手対象 ISSUE（2 件）

- `ISSUES/util/low/plan-handoff-frontmatter-drift.md` — frontmatter drift 観察。対応方針 §1（ver15.4〜15.5 運用観察）が本バージョン時点で満了。
- `ISSUES/util/low/plan-handoff-omission-tracking.md` — 省略乱発観察。対応方針 §1（ver15.4〜15.6 運用観察）が本バージョン時点で満了（観察期間 3 版のうち 3 版が埋まる）。

### 観察対象ファイル（3 バージョン）

- `docs/util/ver15.3/ROUGH_PLAN.md` / `docs/util/ver15.3/PLAN_HANDOFF.md`
- `docs/util/ver15.4/ROUGH_PLAN.md` / `docs/util/ver15.4/PLAN_HANDOFF.md`
- `docs/util/ver15.5/ROUGH_PLAN.md` / `docs/util/ver15.5/PLAN_HANDOFF.md`

### 参照ドキュメント

- `.claude/skills/issue_plan/SKILL.md` — 「frontmatter は `ROUGH_PLAN.md` と同値で重複保持する」/ 「PLAN_HANDOFF.md の省略条件」の規定
- `docs/util/MASTER_PLAN/PHASE7.1.md` §3 — リスク節「quick タスクで冗長に見える」の原文脈
- `docs/util/ver15.3/IMPLEMENT.md` §8.3 / §9 — validation.py 先送り結論・リスク表

## 後続 step への注意点

### 1. 観察結果の判定基準を先に固める

`/quick_impl` で観察を実施する前に、以下のどちらに倒すかの基準を MEMO に明示してから判定に入ること（事後に基準を後付けしない）:

- **drift 側の「発生率ゼロ」判定**: 3 バージョン全てで `workflow:` / `source:` が `ROUGH_PLAN.md` と `PLAN_HANDOFF.md` で完全一致 → `done/`。1 件でも不一致があれば非ゼロ扱い。
- **omission 側の「乱発なし」判定**: quick バージョンにおける `PLAN_HANDOFF.md` 省略比率が 50% 未満、かつ省略宣言の有無と本文引き継ぎの実在が整合している → `done/`。乱発の目安は ISSUE 本文 §「quick バージョンで `PLAN_HANDOFF.md` が常に省略されている」を援用。

### 2. 予備観察の共有（issue_plan 段階で済ませた差分）

`/issue_plan` 段階で 3 バージョンの frontmatter は目視で一次確認済。結果は以下:

| バージョン | ROUGH_PLAN frontmatter | PLAN_HANDOFF frontmatter | PLAN_HANDOFF 存在 |
|---|---|---|---|
| ver15.3 | `workflow: full` / `source: master_plan` | `workflow: full` / `source: master_plan` | 有 |
| ver15.4 | `workflow: full` / `source: master_plan` | `workflow: full` / `source: master_plan` | 有 |
| ver15.5 | `workflow: quick` / `source: issues` | `workflow: quick` / `source: issues` | 有 |

この一次観察だけで判断を確定させず、`/quick_impl` 側で機械的に再確認すること（目視の見落としを排除する手順を踏むこと自体が本 ISSUE の検証価値）。

### 3. quick バージョンの母数が 1 件しかない点に注意

観察期間 3 版のうち quick workflow は ver15.5 の 1 件のみで、他 2 件は full。omission-tracking ISSUE の本旨は「quick での省略乱発」のため、母数 1 で「乱発なし」と断ずるには議論の余地が残る。以下 2 択で判断を明示すること:

- **A**: quick 母数 1 でも ver15.5 が省略していない（PLAN_HANDOFF.md を実際に作成している）ことを「兆候なし」の弱い根拠として採用し `done/` に倒す。
- **B**: 母数 1 では観察不十分とし、本 ISSUE の対応方針 §1 を「ver15.4〜15.7 の 4 版観察」に延長する方向で内容更新する（`done/` には倒さない）。

実装者の判断で A / B を選んだ上で MEMO.md にその理由を残すこと。PLAN_HANDOFF では A を推奨するが、強制はしない。

### 4. follow-up ISSUE 起票のルール

観察結果が「非ゼロ」に倒れた場合は、本バージョンでは**コード変更・SKILL 改訂に踏み込まない**（ROUGH_PLAN のスコープ外）。代わりに以下の形で follow-up ISSUE を起票する:

- drift 非ゼロ → `ISSUES/util/low/plan-handoff-drift-validation.md`（仮）新規起票。frontmatter `status: raw`, `assigned: ai`。観察結果の件数・具体例・validation.py への差分案を記載
- omission 乱発 → `ISSUES/util/low/plan-handoff-omission-tighten.md`（仮）新規起票。同上の frontmatter。乱発の具体例・SKILL §省略条件の締め込み案を記載

### 5. スコープ境界（やってはいけないこと）

- `scripts/claude_loop_lib/validation.py` への実コード追加は**行わない**
- `.claude/skills/issue_plan/SKILL.md` の書き換えは**行わない**
- 他 util low ISSUE（`toast-persistence-verification.md` / `rules-paths-*` / `scripts-readme-usage-*`）や medium ISSUE（`issue-review-rewrite-verification.md`）には触れない
- 観察対象バージョンを ver15.3〜15.5 の 3 版に限定し、それ以前（ver15.2 以下）や未来版への拡大はしない
