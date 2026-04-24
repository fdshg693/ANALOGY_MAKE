---
workflow: full
source: issues
---

# ver16.3 PLAN_HANDOFF — 後続 step 向け引き継ぎ

## 選定理由・除外理由

### 着手対象 §A（cost tracking 初回実機突合）の選定理由

- ver16.2 RETROSPECTIVE §8 および `FEEDBACKS/handoff_ver16.2_to_next.md` が「次 run が cost tracking 付きの初回本番 run。`/retrospective §3.5 相当` で突合」と明示している
- 本 run は ver16.2 の `cb2d87a`（PHASE8.0 §3 実装コミット）以降で起動する初 run のはず（ver16.2 `/issue_plan` 時点の process は ver16.1 完走コミット `80455c3` のものだったため、cost tracking 実機観察は未実施）
- `logs/workflow/*.costs.json` が生成される想定。本 `/issue_plan` 実行時点では未生成（run 完了時に書き出される実装と想定）のため、本 step では突合そのものは行わず `/retrospective` に引き継ぐ
- 突合観点は 6 項目（R1 / R2 / R4 / §U1-a / §U1-b / §U6-a）で、いずれも RESEARCH.md / EXPERIMENT.md 本文で既に先送り理由が整理されている

### 着手対象 §B（長期持ち越し ready/ai 再判定手順の新規 ISSUE 起票）の選定理由

- handoff §「次ループで試すこと」末尾で明示的に「ISSUE 起票を次ループで検討する」と指示されている
- 構造問題: `/issue_plan` SKILL のレビューフェーズは `review / ai` のみを対象にし、`ready / ai` の長期停滞を検出・降格できない仕様（実際に util では `issue-review-rewrite-verification` / `toast-persistence-verification` が 5 バージョン連続持ち越し）
- 本版で SKILL 本体を拡張実装するまで踏み込むと `quick` スコープを超え、設計合意のないまま書き始めるリスクあり。まず ISSUE 起票で設計提案を明文化し、実装は将来版に委ねる方針が安全

### 除外候補と除外理由

| 候補 | 除外理由 |
|---|---|
| `ISSUES/util/medium/deferred-resume-twice-verification.md`（`ready/ai`） | cost tracking 実走中の deferred 発火経路で自然観察される見込み。独立した実装 step を切らず `/retrospective` 内の観察対象として合流させる（handoff §「次ループで試すこと」の方針） |
| `ISSUES/util/medium/issue-review-rewrite-verification.md`（`ready/ai`） | util 単独 AI 自走困難。§B の新規 ISSUE（SKILL 側拡張）が解決経路の布石になるため、本版では触らない |
| `ISSUES/util/low/toast-persistence-verification.md`（`ready/ai`） | Windows 実機目視必須で AI self-consume 不能。§B の ISSUE が将来「強制降格」ルートを整えた後に降格候補になる |
| `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md`（`raw/ai`） | triage 未済。本版スコープ外 |
| `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md`（`raw/ai`） | triage 未済。本版スコープ外 |
| PHASE9.0 骨子作成 | ver16.2 RETROSPECTIVE §1 / §3 および handoff §保留事項で「時期尚早」と明示。既存 ISSUES 消化優先 |
| `issue_review` SKILL 本体の拡張実装 | §B の設計合意が先。ISSUE 起票 → レビュー昇格 → 実装の順で進める |
| `experiment_test` effort / model 下げ | 2 サンプルのみで判断材料不足（handoff §保留事項） |

## 関連 ISSUE / 関連ファイル / 前提条件

### §A（cost tracking 突合）関連

- `scripts/claude_loop_lib/costs.py` — token/cost 計測実装本体
- `scripts/claude_loop.py::_run_step` / `_process_deferred` — cost 記録の呼び出し元
- `logs/workflow/*.costs.json` — 本 run で生成される sidecar（**本 step 実行時点では未生成**、run 完了時に書き出される想定）
- `docs/util/ver16.2/RESEARCH.md` — 突合の一次資料（§A1〜§A6 の SDK / pricing spec）
- `docs/util/ver16.2/EXPERIMENT.md` — 先送り 5 仮説の再開手順と「未検証」マーキング
- `docs/util/ver16.2/IMPLEMENT.md` — primary source を `total_cost_usd` に切替えた根拠
- `experiments/cost-usage-capture/{slug}/README.md` — ver16.2 で残した再開手順草稿

### §B（ISSUE 起票）関連

- `.claude/skills/issue_review/SKILL.md` — 拡張対象 SKILL。現状 `review / ai` のみを対象にする仕様
- `.claude/skills/issue_plan/SKILL.md` — 上記 SKILL をインライン展開している箇所。将来拡張時は同期必須（SKILL.md 末尾「呼び出し元との同期」節）
- `ISSUES/README.md` — frontmatter 仕様（`status` / `assigned` / `reviewed_at`）
- `ISSUES/util/medium/issue-review-rewrite-verification.md` — 5 バージョン連続持ち越しの代表例
- `ISSUES/util/low/toast-persistence-verification.md` — 5 バージョン連続持ち越しの代表例

### 前提条件

- `.claude/` 配下を直接編集する場合は `scripts/claude_sync.py` 経由（`.claude/rules/claude_edit.md`）。ただし本版の §B は `ISSUES/` 配下のみを編集するため `claude_sync.py` は **不要**
- util 以外のカテゴリ（app / infra / cicd）には触らない（`.claude/CURRENT_CATEGORY = util`）
- テストは現行 322 件 PASS 想定。本版の ISSUE 追加では実装変更なしのため追加テストは不要

## 後続 step への注意点

### 共通

- **本版は minor かつ `full` workflow**。`split_plan` は必須だが、成果物は「REFACTOR.md = 不要を明示」「IMPLEMENT.md = ISSUE 1 件作成の 1 step のみ」になる想定。通常の `full` のように 5〜8 論点整理を無理に膨らませない
- `plan_review_agent` の指摘が「スコープが薄すぎる」方向で出た場合、§A（observational）の重みを根拠に反論する（§A は ver16.2 から明示持ち越しのため割愛できない）
- **cost tracking 実機観察は `/retrospective` で集約**。`split_plan` / `imple_plan` / `wrap_up` / `write_current` では costs.json を参照しない（観察結果を早期に本文化すると `/retrospective §3.5` と重複する）

### `/split_plan`

- `IMPLEMENT.md §0` の論点整理は最小限で可（「§B の ISSUE 本文に含める設計要素」「§A の突合観点リスト確認」の 2 論点程度）
- 新規 ISSUE の frontmatter は `status: raw`, `assigned: ai`, `priority: low`, `reviewed_at: "2026-04-24"` を想定
- 新規 ISSUE 本文の節立て提案: `## 概要` / `## 背景（ver16.3 handoff 経由）` / `## 対応方針（設計提案）` / `## 影響範囲` / `## 関連資料`

### `/imple_plan`

- 実装 step は「新規 ISSUE 1 件の作成」のみ。1 step で完了するはず
- 322 tests は触らない実装なので変更なし想定。実行確認はスキップしてよい（diff に scripts/ の変更が含まれないことを確認するだけで十分）
- 計画乖離が発生した場合（例: `/retrospective` を待たずに cost tracking の明白な bug を発見して即時修正する判断）は `MEMO.md` に根拠付きで記録する

### `/wrap_up`

- リスク判定: 「新規 ISSUE 追加のみで production 影響ゼロ」と判定するだけで済む
- MEMO.md 追記は最小限で可

### `/write_current`

- minor 版なので `CHANGES.md` のみ（`CURRENT.md` 新規作成不要）
- CHANGES.md に記載する変更は (1) 新規 ISSUE 1 件追加、(2) docs/util/ver16.3/ 配下の新規ファイル 6〜7 件の 2 系統

### `/retrospective`

- **§3.5 相当の cost tracking 突合が本版の主眼**。以下を必ず含める:
  - `logs/workflow/*.costs.json` が実在するか（無い場合は「cost tracking が本 run で動作しなかった」signal として扱い、原因調査を次ループ handoff に書く）
  - `modelUsage` の key 名（kebab-case Anthropic model ID か）
  - `total_cost_usd` が各 step で取れているか、`cost_source` 分布（`"cli"` 比率 vs `"fallback_price_book"` 比率）
  - `status="unavailable"` の発生率と理由
  - deferred 発火があった場合の `kind="deferred_resume"` / `"deferred_external"` record の出現
  - live stdout サイレント化（`--- stdout/stderr ---` 区間の空白度）の運用耐久度
  - 耐えがたい場合の次版対応方針（`stream-json` 切替の検討など）
- §U1-a / §U1-b / §U6-a の「未検証」マーク解除判定も含める
- 本版で新規起票した `issue-review-long-carryover-redemotion` の実装版推奨タイミングも handoff に書く
- `experiment_test` effort 下げ判断 / model 下げ判断 は本版では `research` workflow を使わないため 3 サンプル目が採取されない。ver16.4 以降に据え置きを改めて記録

## 事前リファクタリング要否（根拠）

**不要**。根拠:

- 本版の実装変更は「新規 ISSUE 1 件追加」のみで、scripts/ や .claude/ の既存ファイルには触らない
- cost tracking 突合は観察であり、発見された bug への対応を除き実装変更は発生しない
- ver16.2 までで PHASE8.0 §1〜§3 の骨格は安定しており、本版で触れるコンポーネントは存在しないため技術的負債の先行解消も不要

## PLAN_HANDOFF.md 省略判断

省略しない。根拠: 選定理由・除外理由が複数件あり、後続 step（特に `/split_plan` と `/retrospective`）への注意点が 5 区分以上あるため、ROUGH_PLAN.md 本文内に集約すると読みにくくなる。
