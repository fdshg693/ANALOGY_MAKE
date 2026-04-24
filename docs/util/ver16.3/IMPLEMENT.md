---
workflow: full
source: issues
---

# ver16.3 IMPLEMENT — cost tracking 初回突合 + 長期持ち越し ready/ai 再判定手順の ISSUE 起票

## §0. 論点整理（最小限）

本版は minor かつ観察・評価半分 + ISSUE 1 件起票半分のため、論点は 2 つのみ。

### 論点 1: §B の ISSUE 本文に盛り込む設計要素

`ISSUES/util/low/issue-review-long-carryover-redemotion.md` に以下 5 要素を必ず含める（PLAN_HANDOFF §「`/split_plan`」で既に節立てが指定されている）:

- **スキャン対象拡張**: 現 `issue_review` SKILL は `status: review / ai` のみ走査。拡張後は「`status: ready / ai` かつ `reviewed_at` が N バージョン以上前」も検出対象に含める
- **しきい値の 2 段階**: 5 バージョン連続持ち越し = 「要再判定」警告、10 バージョン連続持ち越し = 「強制降格」アクション
- **判定ルート**: 「実装着手されていない理由」を判別し、実機検証を要するものは `need_human_action / human` に降格、AI 作業で消化可能なら `ready / ai` を維持し `## AI からの依頼` で追加ヒントを残す
- **影響範囲**: `issue_review` SKILL 本体 + `issue_plan` SKILL のインライン展開部（「呼び出し元との同期」原則）+ `ISSUES/README.md` のライフサイクル節
- **本版では実装しない根拠**: 設計合意なしに SKILL 本体を書き換えると quick スコープ超過 + `plan_review_agent` 側の再承認コストが発生するため、ISSUE 起票 → 次版レビュー昇格 → 実装版の 3 ステップに分ける

### 論点 2: §A の突合観点リスト（`/retrospective` が消費）

`/retrospective §3.5 相当` で突合する 6 観点を、本 IMPLEMENT.md の §A にチェックリスト形式で固定する。これにより `/retrospective` 着手時に「何を見るか」を `logs/workflow/*.costs.json` 読み直しで再構築する必要がなくなる。

## §A. cost tracking 初回本番突合（観察・評価、実装変更なし）

### 対象 artifact

- `logs/workflow/{stem}.costs.json` — 各 step 終了時に書き出される sidecar
- `logs/workflow/{stem}.log` — live stdout（`--output-format json` 付与時の空白度評価用）
- 本 step 実行時点で `/issue_plan` の sidecar が 1 件生成済（`20260424_231449_claude_loop_issue_plan.costs.json`）— 初期観察は既に可能だが、**本格突合は `/retrospective` で全 step の sidecar が出揃ってから実施**する

### 突合観点チェックリスト（`/retrospective` 用）

| # | 観点 | 確認方法 | 判定 |
|---|------|----------|------|
| A-1 | `modelUsage` の key 名が kebab-case Anthropic model ID か（ver16.2 §U1-b 仮説） | 各 sidecar の `steps[].model` を列挙し、`claude-opus-4-*` / `claude-haiku-4-*` 等の正規 ID 形式か確認 | `/retrospective` で記録 |
| A-2 | `total_cost_usd` が各 step で取れているか / `cost_source` 分布 | 全 sidecar を走査し、`cost_source` の値を `"cli"` / `"fallback_price_book"` / その他で集計 | `/retrospective` で記録 |
| A-3 | `status="unavailable"` の発生率と理由 | sidecar の `steps[].status` を集計。`"unavailable"` が大量なら cost_source 未解決を示す signal | `/retrospective` で記録 |
| A-4 | deferred 発火時の `kind="deferred_resume"` / `"deferred_external"` record | 本版で deferred 発火があった場合のみ観察。無ければ「次回 deferred 発火 run で再観察」と明示 | `/retrospective` で記録 |
| A-5 | `--output-format json` による live stdout サイレント化の実害度（R1 / §U6-a） | 本 run の log ファイルの `--- stdout/stderr ---` 区間空白度を目視評価 | `/retrospective` で記録 |
| A-6 | `SDKResultMessage` 型と実機 JSON の key / 型突合（R2 / §U1-a） | sidecar の top-level key を列挙し、ver16.2 RESEARCH.md §A の期待 key と突合 | `/retrospective` で記録 |

### 初期観察（本 step 実行時点での先行所見、正式判定は `/retrospective`）

本 `/split_plan` step で `20260424_231449_claude_loop_issue_plan.costs.json` を参考程度に一読した範囲での先行所見（**`/retrospective` がゼロから sidecar を読み直す前提なので、以下は参考情報とし IMPLEMENT.md に固定**）:

- 観察 1: `steps[].model` に `"claude-haiku-4-5-20251001"` が記録されている（A-1 候補: kebab-case Anthropic model ID フォーマット ✓）
- 観察 2: top-level に `"modelUsage"` key は存在せず、代わりに各 step の `cache_creation_input_tokens` / `cache_read_input_tokens` / `input_tokens` / `output_tokens` がフラットに並ぶ（A-6: ver16.2 RESEARCH の期待 schema とのズレ候補）
- 観察 3: `cost_source: "cli"` / `cost_usd: 2.1731...` が取れており、`"fallback_price_book"` には落ちていない（A-2 候補）
- 観察 4: 起動コマンドには `--model opus` が指定されていたのに sidecar では `claude-haiku-4-5-20251001` が記録されている — これは「実際に使われた model を正確に記録」した結果か、または「model 引数解決のズレ」か `/retrospective` で判別要

**注意**: 上記観察はあくまで `/split_plan` 側の参考。正式な突合判定と「未検証」マーク解除判断は `/retrospective` が全 sidecar を走査した結果として記録する。本版の `/wrap_up` / `/write_current` では costs.json を参照しない（handoff §共通の指示どおり）。

### 実装変更の発生条件

突合の結果「実装 bug / 仕様乖離の兆候」が見つかった場合のみ、本版内での即時修正を検討する。具体的には:

- `cost_source="unavailable"` が全 step に発生 → `scripts/claude_loop_lib/costs.py` の CLI 解析 bug の疑い
- `total_cost_usd` が常に `null` / `0` → SDK 型定義との乖離
- `modelUsage` 等の top-level key が ver16.2 RESEARCH と完全乖離 → schema 前提の書き換えが必要

いずれも `/retrospective` が発見後に `/imple_plan` / `/wrap_up` に差し戻す想定（本 `/split_plan` 時点で前倒し実装はしない）。軽微な観察事項のみなら ver16.4 以降に委ねる。

## §B. 長期持ち越し ready/ai 再判定手順の新規 ISSUE 起票（実装系、1 step）

### 作成ファイル

- **パス**: `ISSUES/util/low/issue-review-long-carryover-redemotion.md`
- **frontmatter**:
  ```yaml
  ---
  status: raw
  assigned: ai
  priority: low
  reviewed_at: "2026-04-24"
  ---
  ```
  - `status: raw` とする根拠: 本 ISSUE は「設計提案の書き起こし」段階であり、次回 `/issue_plan` の review フェーズで `review / ai` 経由 `ready / ai` に昇格させる想定（ISSUES/README.md の AI 起票パス §「調査中に拾った粗い観察」に該当）
  - `reviewed_at` を付けるのは、本版でレビュー済み（AI が本文を書き下ろした日）であることを示すため

### 本文構成（5 節）

PLAN_HANDOFF.md §「`/split_plan`」で指定された節立てに従う:

1. **`## 概要`** — 3〜5 行で「ready/ai の長期持ち越しを検出・再判定するルートを `issue_review` SKILL に追加する提案」を要約
2. **`## 背景（ver16.3 handoff 経由）`** — ver16.2 → ver16.3 handoff で提起された構造問題（`/issue_plan` のレビューフェーズは `review / ai` のみ対象で `ready / ai` の長期停滞を検出できない仕様）を記述。実例として 5 バージョン連続持ち越しの `issue-review-rewrite-verification` / `toast-persistence-verification` を挙げる
3. **`## 対応方針（設計提案）`** — 論点 1 で列挙した 3 要素（スキャン対象拡張 / しきい値 2 段階 / 判定ルート）を設計提案として記述
4. **`## 影響範囲`** — `.claude/skills/issue_review/SKILL.md` / `.claude/skills/issue_plan/SKILL.md`（インライン展開部）/ `ISSUES/README.md` の 3 箇所を影響ファイルとして挙げる
5. **`## 関連資料`** — `docs/util/ver16.3/ROUGH_PLAN.md` §B, `docs/util/ver16.3/PLAN_HANDOFF.md` §「`/split_plan`」, `docs/util/ver16.2/FEEDBACKS/` 該当 handoff, `ISSUES/util/medium/issue-review-rewrite-verification.md`, `ISSUES/util/low/toast-persistence-verification.md` の 5 点

### 実装手順（`/imple_plan` 向け）

1. 上記パスに Write ツールで新規ファイル作成（既存ファイルではないので Edit 不要）
2. frontmatter と 5 節を上記構成どおり記述
3. `python scripts/issue_status.py util` を実行して新規 ISSUE が `raw / ai` として集計されることを確認
4. 322 tests は触らない（scripts/ に変更なし）

## §C. 事前リファクタリング要否

**不要**。根拠は `ROUGH_PLAN.md` §事前リファクタリング要否と `PLAN_HANDOFF.md` §事前リファクタリング要否（根拠）に記載のとおり:

- 実装変更は「新規 ISSUE 1 件追加」のみで、scripts/ や .claude/ の既存ファイルには触らない
- §A は観察であり、発見された bug への対応を除き実装変更は発生しない
- cost tracking 関連コンポーネントは ver16.2 で骨格が安定しており、本版で触れるコンポーネントは存在しない

REFACTOR.md は作成しない（`/issue_plan` が作成した ROUGH_PLAN.md に「事前リファクタリング不要」が明記されており、本 SKILL の規約に従いファイル作成を省略）。

## §D. 成果物サマリ

本 `/split_plan` step で追加される成果物:

- `docs/util/ver16.3/IMPLEMENT.md` — 本ファイル

後続 step で追加される成果物（参考、本 step では作成しない）:

- `ISSUES/util/low/issue-review-long-carryover-redemotion.md` — `/imple_plan` が §B 実装手順に従って作成
- `docs/util/ver16.3/MEMO.md` — `/imple_plan` / `/wrap_up` が作成
- `docs/util/ver16.3/CHANGES.md` — `/write_current` が作成
- `docs/util/ver16.3/RETROSPECTIVE.md` — `/retrospective` が §A 突合結果を §3.5 相当で記録（本版の主要観察出力）

## §E. やらないこと（本版スコープ外、再掲）

- `issue_review` SKILL 本体の実装拡張（§B の ISSUE 起票のみ、拡張実装は将来版）
- `deferred-resume-twice-verification` / `issue-review-rewrite-verification` / `toast-persistence-verification` の個別消化
- PHASE9.0 骨子作成
- `experiment_test` / `research_context` の effort / model 調整
- `write_current` effort high の他 YAML 波及議論
- 322 tests への変更（実装変更なしのため）
