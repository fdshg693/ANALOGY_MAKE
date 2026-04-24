---
workflow: full
source: issues
---

# ver16.3 ROUGH_PLAN — cost tracking 初回実機突合 + 長期持ち越し ready/ai 再判定手順の ISSUE 起票

ver16.2 で PHASE8.0 §3（token/cost 計測）を完走し、PHASE8.0 全 3 節（§1 research / §2 deferred / §3 cost）が揃った。本 ver16.3 は次の 2 点に絞ったマイナー版:

1. **cost tracking の初回本番突合**（観察・評価系）— ver16.2 で先送りした §U1-a / §U1-b / §U6-a / R1 / R2 / R4 を `/retrospective §3.5 相当` で実機突合する
2. **長期持ち越し ready/ai 4 件の再判定手順** に関する新規 ISSUE 起票（実装系） — `issue_review` SKILL 側に「5 バージョン連続持ち越しの再判定ルート」を追加する設計提案を ISSUE として書き起こす

PHASE9.0 の骨子作成は依然として時期尚早のため見送り、本版は既存 ISSUES 消化 + cost tracking 実機検証に限定する。

## ISSUE 状態サマリ

| status / assigned | 件数 |
|---|---|
| ready / ai | 3 |
| review / ai | 0 |
| need_human_action / human | 0 |
| raw / human | 0 |
| raw / ai | 2 |

出典: `python scripts/issue_status.py` util カテゴリ。util 以外の 3 カテゴリ（app / infra / cicd）は本 SKILL の対象外（`.claude/CURRENT_CATEGORY` が `util`）。

## ISSUE レビュー結果

- ready/ai に遷移: 0（util 配下に `review / ai` が 0 件のため、本ループでのレビュー作業は発生しない）
- need_human_action/human に遷移: 0
- 追記した `## AI からの依頼`: 0

**補足**: `ready / ai` 3 件のうち `issue-review-rewrite-verification` と `toast-persistence-verification` は 5 バージョン連続持ち越し。本 SKILL の仕様では `ready/ai` を `need_human_action/human` に降格できないため、本版で別途「再判定手順の ISSUE 起票」でこの構造問題に対処する（後述 §着手スコープ §B）。

## バージョン種別の判定

**マイナー（ver16.3）**。根拠:

- MASTER_PLAN 新項目（PHASE9.0 骨子）には着手しない（ver16.2 RETROSPECTIVE §1 / §3 と handoff で「時期尚早」と判定済み）
- アーキテクチャ変更・新規外部ライブラリ導入・破壊的変更いずれも無し
- 実装スコープは「新規 ISSUE 1 件作成」と「retrospective での観察突合」で完結

## ワークフロー選択

**`full`（6 step）**。根拠:

- `ISSUES/` 由来・全 `ready` だが、`/retrospective §3.5 相当` の cost tracking 初回突合を正式な step として回す必要があるため、`quick`（3 step、`/retrospective` 非含）では不十分
- `quick` は変更 3 ファイル以下・100 行以下の閾値内に収まるが、本版の主眼の半分は「観察・評価」であり `/retrospective` 必須
- `research` に該当する 4 条件（外部仕様確認 / 実装方式実験 / 長時間検証 / 隔離環境試行）はいずれも該当しない。cost tracking 仕様調査は ver16.2 RESEARCH.md で完了済み、残るは実機突合のみ
- 判断に迷う場合は `full` 優先の原則にも合致

## 着手スコープ

### §A. cost tracking 初回本番突合（観察・評価系、実装変更なし）

本 run が `claude_loop.py` の cost tracking 有効版（ver16.2 commit `cb2d87a` 以降）で起動した**初回の本番 run**。ver16.2 EXPERIMENT で実機確認できなかった 6 項目を `/retrospective §3.5 相当` のセクションで突合する:

- **R1 / §U6-a**: `--output-format json` による live stdout サイレント化の実害度（`--- stdout/stderr ---` 区間の空白度）— 本 run の log 可読性で評価
- **R2 / §U1-a / §U1-b**: `SDKResultMessage` 型と実機 JSON の key / 型突合（`modelUsage` の key 名が kebab-case Anthropic model ID か、`total_cost_usd` が取れるか）— 本 run 生成 `logs/workflow/*.costs.json` の key set で評価
- **R4**: deferred execution の cost 3 kind 別 record（`"claude"` / `"deferred_resume"` / `"deferred_external"`）— 本版で deferred 発火があれば自然採取。無ければ「次回 deferred 発火 run で再観察」と明示

突合結果のうち「実装 bug / 仕様乖離の兆候」が発見された場合のみ、本版内で即時修正を検討する（`imple_plan` step の判断）。軽微な観察・判断事項のみなら `/retrospective` への記録で完了とし、修正は ver16.4 以降に委ねる。

### §B. 長期持ち越し ready/ai 再判定手順の新規 ISSUE 起票（実装系）

新規 ISSUE を 1 件作成する:

- **配置**: `ISSUES/util/low/issue-review-long-carryover-redemotion.md`
- **status**: `raw`、**assigned**: `ai`（triage 待ち扱い。本 ISSUE 自体は次回 `/issue_plan` で review → ready 昇格を経る）
- **目的**: 「`ready/ai` のまま 5 バージョン以上連続で着手されていない ISSUE」を `issue_review` SKILL 側で検出し、再判定（維持 / `need_human_action/human` へ降格 / 削除）を促すルートを追加する設計提案
- **想定する SKILL 側拡張**（本 ISSUE 本文に設計を記述、実装は別版）:
  - スキャン対象の拡張: `status: review / ai` に加え「`status: ready / ai` かつ `reviewed_at` が N バージョン以上前」を検出対象に含める
  - 判定ルート: 「実装着手されていない理由」を判別し、実機検証を要するものは `need_human_action / human` に降格、AI 作業で消化可能なら `ready / ai` を維持し `## AI からの依頼` で追加ヒントを残す
  - しきい値: 連続持ち越し 5 バージョンで検知・要再判定フラグ、10 バージョンで強制降格の 2 段階
- **本版内での実装は行わない**: ISSUE 本文に設計提案のみを残し、具体実装は将来版に委ねる。本 ISSUE 自体が handoff で言及された「`issue_review` SKILL 側で拡張する ISSUE 起票を次ループで検討する」への応答

### やらないこと（本版スコープ外）

- `issue_review` SKILL 本体の実装拡張（§B の ISSUE 起票のみ、拡張実装は将来版）
- `deferred-resume-twice-verification` / `issue-review-rewrite-verification` / `toast-persistence-verification` の個別消化（`ready/ai` 据え置き）
- PHASE9.0 骨子作成
- `experiment_test` / `research_context` の effort / model 調整（sample 不足、据え置き）
- `write_current` effort high の他 YAML 波及議論

## 成果物（想定）

- `docs/util/ver16.3/ROUGH_PLAN.md` — 本ファイル
- `docs/util/ver16.3/PLAN_HANDOFF.md` — 選定理由・関連ファイル・後続 step への注意点
- `docs/util/ver16.3/REFACTOR.md` — `/split_plan` 生成（`full` workflow 必須）。本版は事前リファクタリング不要のため「不要」を明示する想定
- `docs/util/ver16.3/IMPLEMENT.md` — `/split_plan` 生成。実装 step は「新規 ISSUE 1 件作成」のみの想定
- `docs/util/ver16.3/MEMO.md` — `/imple_plan` / `/wrap_up` の実装メモ・残課題
- `docs/util/ver16.3/CHANGES.md` — minor 版につき diff 記録（主に ISSUE 1 件追加 + retrospective 突合結果）
- `docs/util/ver16.3/RETROSPECTIVE.md` — **cost tracking 初回実機突合を §3.5 相当で記録**（本版の主要観察出力）
- `ISSUES/util/low/issue-review-long-carryover-redemotion.md` — 新規 ISSUE（§B）

`RESEARCH.md` / `EXPERIMENT.md` / `CURRENT.md` / `PLAN_HANDOFF.md` の省略判断は後続 step に委ねる（`PLAN_HANDOFF.md` は handoff 情報量が多いため本版でも作成する）。

## 事前リファクタリング要否

**不要**。根拠は `PLAN_HANDOFF.md` §後続 step への注意点に記載。
