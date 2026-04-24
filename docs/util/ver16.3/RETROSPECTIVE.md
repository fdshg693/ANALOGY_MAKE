# ver16.3 RETROSPECTIVE — cost tracking 初回実機突合 + 長期持ち越し ready/ai 再判定 ISSUE 起票

本版は PHASE8.0 完走直後の minor 版。主眼は 2 点:

1. **§A cost tracking 初回本番突合**（観察）— ver16.2 で先送りした 6 観点（R1 / R2 / R4 / §U1-a / §U1-b / §U6-a）を本 run の `logs/workflow/20260424_231449_*` 系 artifact で突合
2. **§B 長期持ち越し ready/ai 再判定手順 ISSUE 起票**（実装 1 件のみ）

実装は ISSUE 1 件追加のみ・コード変更なし・322 tests 触らず。本版の本体は §A の観察結果であり、§3.5 相当としてここに集約する。

---

## §1 ドキュメント構成

### MASTER_PLAN

- `docs/util/MASTER_PLAN/PHASE8.0.md` 全 3 節 (§1 research / §2 deferred / §3 cost) 完走済。`docs/util/MASTER_PLAN.md` のサマリ行も ver16.3 で「**実装済み（全 3 節完了）**」に補正完了（ver16.2 write_current 更新漏れの後追い修正）。
- **PHASE9.0 骨子作成: 据え置き**。既存 ISSUES（`ready/ai` 3 件 + `raw/ai` 3 件）で吸収可能なうちは次 PHASE を立てない方針を継続。§A で発見した costs.py 軽微バグ（後述）も ver16.4 の minor で十分吸収できる規模。

### CLAUDE.md

- 分割不要。本版で CLAUDE.md への変更なし。

### docs カテゴリ別

- minor のため `CURRENT.md` 新規作成なし、`CHANGES.md` のみ。PLAN_HANDOFF.md は handoff 情報量が多かったため作成維持（判断は後続 step に委ねた結果）。
- RESEARCH/EXPERIMENT は本版で無し（`full` workflow）。

### ISSUES

- 新規 1 件（`ISSUES/util/low/issue-review-long-carryover-redemotion.md`）、`raw/ai` で triage 待ち。次回 `/issue_plan` で `review/ai` 経由 `ready/ai` 昇格予定。

---

## §2 バージョン作成の流れ

### `full` workflow 6 step 全評価

| step | duration | cost | 計画乖離 | 評価 |
|---|---|---|---|---|
| issue_plan | 6m46s | $2.17 | なし | ROUGH_PLAN + PLAN_HANDOFF が明示的に §A/§B を指定、後続 step の迷いを最小化 |
| split_plan | 4m54s | $1.34 | なし | IMPLEMENT.md が論点 2 点に絞れており plan_review_agent も承認 |
| imple_plan | 4m30s | $1.25 | なし | ISSUE 1 件作成のみ、`issue_status.py` による自動確認で完結 |
| wrap_up | 1m47s | $0.42 | なし | 残課題 3 項目を「対応不要」判定、MEMO 追記のみ |
| write_current | 2m38s | $0.43 | MASTER_PLAN.md の PHASE8.0 サマリ補正を追加 | 計画外だが正しい補完。評価 ◎ |
| retrospective | - | - | 本 step | §A 突合を本文化 |

**合計概算 $5.6 + retrospective**。minor 版としてはやや重いが、§A の観察 step が実装変更なしでも 1〜2 step 相当の cost を消費している（cost tracking 評価は full workflow の retrospective 内で自然に吸収できた）。

### 良く機能した点

- **PLAN_HANDOFF.md の情報密度**: `/split_plan` と `/retrospective` への注意点を事前固定したおかげで、本 retrospective が `logs/workflow/*.costs.json` を「何を見るか」から考え直す必要がなかった。A-1〜A-6 のチェックリスト化が効いた。
- **「観察だけで 1 minor 版」の再現性**: 「cost tracking 実機突合」という実装変更ゼロの観察テーマを minor 版として成立させられた。ver16.2 RETROSPECTIVE で「次 run で突合」と handoff した設計どおりに進行。
- **MASTER_PLAN 補正の副次効果**: `/write_current` が ver16.2 の更新漏れを自発的に補正した。`full` workflow では write_current が最後の「総決算」として MASTER_PLAN を見直す運用が定着しつつある。

### 改善候補（次ループ判断）

- **「ISSUE 1 件起票だけなら quick でいいのでは」の再検討**: 本版は §A（観察）の存在で `full` を選んだが、§A の実体は「retrospective 内で costs.json を読むだけ」で、計算上は quick + retrospective 単独でも足りた可能性がある。ただし handoff → 観察結果 → 次ループ handoff のリレーを保証するには retrospective step が不可欠なので、現状の判断（full）は妥当。**今後「観察テーマ + 微小実装」の組合せが再度発生したら、quick workflow に retrospective step を追加する YAML を検討する価値あり**（今回は即時判断せず、2 サンプル目を待つ）。

---

## §3 次バージョン推奨

### 材料

1. **ISSUE 状況**: `ready/ai` 3 件（据え置き、5 バージョン連続持ち越し 2 件含む）、`raw/ai` 3 件（本版で 1 件追加、triage 待ち）。util 単独での AI 自走可能な新着はほぼなし。
2. **MASTER_PLAN**: PHASE8.0 完走、PHASE9.0 未定義。
3. **現行 PHASE 完走状態**: 全 3 節 ✅。

### 推奨

**ver16.4（マイナー）**。理由:

- §A で検出した **costs.py `extract_model_name` バグ**（後述 §3.5 A-6 参照）が軽微かつ局所的で、1 minor 版で消化可能。これを次バージョンの主眼に据える。
- 本版で起票した `issue-review-long-carryover-redemotion` を `/issue_plan` レビューで `ready/ai` に昇格させ、SKILL 拡張実装の着手判断を行う（もう 1 本の minor 候補）。
- **PHASE9.0 骨子作成は依然として時期尚早**: 本版 §A で PHASE8.0 実装の仕上げ課題（costs.py 表示バグ）が顕在化したため、PHASE8.0 周辺の「仕上げ minor 1〜2 版」でまだ十分に吸収できる。

次バージョン候補:
- 次マイナー: **ver16.4**
- 次メジャー: ver17.0（PHASE9.0 着手 or アーキ変更時まで保留）

---

## §3.5 cost tracking 初回本番突合（§A 本体）

本節が本版の主要出力。ver16.2 で先送りした 6 観点を `logs/workflow/20260424_231449_*` で突合した結果を記録する。

### 観察 artifact

- `logs/workflow/20260424_231449_claude_loop_issue_plan.costs.json` — issue_plan 単一 step の sidecar（1 件）
- `logs/workflow/20260424_231449_claude_loop_issue_plan.log` — 全 6 step の live log。`--output-format json` 由来の JSON result がそのまま記録されている

**注意**: 本 retrospective 実行時点で `*.costs.json` は `issue_plan` 単一 step 分のみ存在。ver16.3 本体 (split_plan 以降) の sidecar は本 step 完了後に書き出される想定（確認は次ループ冒頭）。

### 判定結果

| # | 観点 | 判定 | 所見 |
|---|------|------|------|
| **A-1** | `modelUsage` の key 名が kebab-case Anthropic model ID か（§U1-b） | ✅ 仮説成立 | log 内の stdout JSON に `claude-opus-4-7` / `claude-haiku-4-5-20251001` / `claude-sonnet-4-6` が出現。いずれも kebab-case。ver16.2 RESEARCH の想定どおり |
| **A-2** | `total_cost_usd` 取得率 / `cost_source` 分布 | ✅ 100% `cli` | issue_plan sidecar: `cost_source: "cli"`, `total_cost_usd: 2.1731965`。log 内の全 5 step 分 stdout JSON でも `total_cost_usd` が非 null で取得済。**`fallback_price_book` には一度も落ちていない** |
| **A-3** | `status="unavailable"` 発生率 | ✅ 0% | sidecar 内 `status: "ok"`、全 step の result JSON が `is_error: false` |
| **A-4** | deferred 発火時の kind 分離 | ⏭️ 本 run で deferred 未発火 | `kind: "claude"` のみ出現。deferred_resume / deferred_external の record は次回 deferred 発火 run で再観察が必要（ver16.1 の resume 経路が静観状態） |
| **A-5** | `--output-format json` による live stdout サイレント化（R1 / §U6-a） | ✅ 許容範囲 | live stream 中は `--- stdout/stderr ---` 区間が step 実行中ほぼ無出力（4〜6 分無応答）だが、step 完了時に 1 行の完全な JSON result が書き出される。`total_cost_usd` / `modelUsage` / `result` 本文が全て含まれており、後追い突合としては十分。**stream-json B 案への切替は不要** |
| **A-6** | SDKResultMessage 型と実機 JSON の key 突合（R2 / §U1-a） | ⚠️ **軽微バグ発見** | 詳細下記 |

### A-6 詳細: sidecar の `model` 記録が実質 misleading

**現象**: `issue_plan` step の sidecar が `model: "claude-haiku-4-5-20251001"` を記録している。しかし同 step の実コスト内訳は:
- `claude-opus-4-7`: $2.1728 (99.98%)
- `claude-haiku-4-5-20251001`: $0.00041 (0.02%)

つまり **primary model は opus であるにもかかわらず、sidecar は haiku を「代表 model」として記録している**。log 側の 1 行サマリも同様にミスリーディング:

```
Cost: $2.1732 (... model: claude-haiku-4-5-20251001)
```

**原因**: `scripts/claude_loop_lib/costs.py::extract_model_name` が `modelUsage` dict の **最初の key** を返す実装（L149-156）。Python dict は挿入順保持なので、CLI が `claude-haiku-4-5-...` を先に挿入するとそれが拾われる。`Task` ツール等が一瞬だけ別 model を呼ぶと「代表 model」が実態と乖離する。

**影響度**: 低（cost 総額・token 集計は正確、表示される「model」名のみ誤解を招く）。ただし retrospective で「どの step でどの model を使ったか」を sidecar から見る運用が成立しない。

**提案修正**: `extract_model_name` を「`modelUsage` 中 `costUSD` が最大の key を返す」に変更。全 5 sub-step 分の stdout JSON で opus が primary と取れる（今回のケースで haiku が記録される問題が消える）。1 関数 5 行程度の修正で済むため ver16.4 minor 1 件で十分対応可能。

**ver16.3 ではコード変更なし**。ver16.4 で `ISSUES/util/low/costs-representative-model-by-max-cost.md` として正式 ISSUE 化し着手する（handoff へ転記）。

### §U1-a / §U1-b / §U6-a の「未検証」マーク解除判定

| 項目 | 判定 | 根拠 |
|---|---|---|
| §U1-a `--output-format json` の実出力 sample | ✅ 解除可 | ver16.3 log に全 5 step 分の完全な JSON result が記録済 |
| §U1-b `modelUsage` の key 名（kebab-case） | ✅ 解除可 | A-1 で確認 |
| §U6-a live stream 挙動の A/B/C 判定 | ✅ 解除可（運用上許容: **C 案で確定**）| A-5 のとおり step 完了時の JSON 一括出力で retrospective は機能する。stream-json への切替は不要 |

ver16.2 EXPERIMENT.md の「未検証」マークは、次回 `/experiment_test` を走らせる機会があれば削除してよい。本版では EXPERIMENT.md を touch しない（§B 実装と無関係なため）。

### R1 / R2 / R4 継続観察

- **R1 (live silent)**: A-5 判定どおり許容。次回大規模 full run で改めて評価。
- **R2 (SDK 型突合)**: A-6 で軽微バグを発見、ver16.4 で修正予定。
- **R4 (deferred 3 kind 分離)**: 本 run deferred 未発火のため継続観察。`ISSUES/util/medium/deferred-resume-twice-verification.md` 消化時に自然採取されるはず。

---

## §4 ISSUES 整理

### 新規追加

- `ISSUES/util/low/issue-review-long-carryover-redemotion.md`（`raw/ai`、priority: low、reviewed_at: 2026-04-24）

### レトロスペクティブで追記すべきと判断したもの

**`ISSUES/util/low/issue-review-long-carryover-redemotion.md` に `## AI からの依頼` を追記**: ver16.3 §A 観察の結果、`/issue_plan` のレビューフェーズが `ready/ai` 長期持ち越しを検出できない仕様は実運用上やはり問題（本版でも 3 件据え置き継続）であることが裏付けられた、との判断を追記する（本 retrospective 内で実行）。

### 持ち越し（削除せず）

- `ISSUES/util/medium/issue-review-rewrite-verification.md`（`ready/ai`、5 バージョン連続、本版 §B 新 ISSUE が降格経路の布石）
- `ISSUES/util/medium/deferred-resume-twice-verification.md`（`ready/ai`、次 deferred 発火で自然消化見込み）
- `ISSUES/util/low/toast-persistence-verification.md`（`ready/ai`、Windows 実機目視必須、5 バージョン連続）
- `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md`（`raw/ai`、triage 待ち）
- `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md`（`raw/ai`、triage 待ち）

### 削除対象

なし（本版で解決 ISSUE は 0 件、§B は将来版布石なので現 ISSUE も据え置き）。

---

## §5 即時適用したスキル変更

**なし**。理由:

- §A の cost tracking 評価結果は「特定の関数のバグ」であり、SKILL への一般化には不向き（個別 ISSUE で処理）
- §2 の改善候補（quick + retrospective 混成 YAML）は 2 サンプル目が必要で即時 SKILL 変更に踏み込まない

ver16.1 SKILL 化済みの `experiment_test` nested claude ガードは本版 `full` workflow では出番なし（期待どおり）。

---

## §6 次ループ handoff

`FEEDBACKS/handoff_ver16.3_to_next.md` を別途作成。次 `/issue_plan` 向け:

- **ver16.4 の主眼候補**: (1) `extract_model_name` を「最大 cost の model」ベースに修正、(2) `issue-review-long-carryover-redemotion` を `ready/ai` へ昇格判定
- A-4 deferred 3 kind 分離は次 deferred 発火 run まで継続観察
- EXPERIMENT.md 「未検証」マーク解除は次 `research` workflow 採用時に回収
- `experiment_test` effort 下げ判断は依然 2 サンプルのまま（3 サンプル目を待つ）

---

## §8 workflow prompt / model 評価（差分評価）

ver16.2 と同一 yaml 設定（`full` workflow）を運用。モデル変更なしのため差分評価のみ。

| step | model | effort | 分類 | 理由 |
|---|---|---|---|---|
| issue_plan | opus | high | 維持 | ROUGH/HANDOFF 両方を明確生成、§A/§B の分離が成功 |
| split_plan | opus | high | 維持 | 論点 2 点に絞り plan_review_agent 承認 |
| imple_plan | opus | high | **調整候補** | ISSUE 1 件作成のみで opus-high は過剰。実装量が閾値未満の場合は sonnet / medium に下げる条件を SKILL 側に追加する価値あり。ただし判断オーバーヘッド回避のため本ループでは維持、次 ループでも実装量小ケースが来たら再評価 |
| wrap_up | sonnet | medium | 維持 | 残課題 3 項目の「対応不要」判定が適切、cost $0.42 で妥当 |
| write_current | sonnet | high | 維持 | MASTER_PLAN 補正を自発的に検出。effort high の効果あり |
| retrospective | opus | medium | 維持 | 本 step、§A 突合に耐えうる effort |

**特記**: imple_plan の「実装量小ケースで effort 下げ」判断は恒久ルール化すべき兆候が出始めたが、**次ループで同種ケースが再度来たら FEEDBACK で試す**（今回即時変更はしない）。

---

## 総括

- PHASE8.0 完走後の初の minor 版として、cost tracking の実機評価（§A）と長期持ち越し再判定の布石（§B）を成立させた
- 実装変更ゼロのまま、ver16.2 先送り 5 項目のうち 3 項目（§U1-a / §U1-b / §U6-a）を検証完了扱いに昇格できた
- **costs.py `extract_model_name` の軽微バグ**を発見、ver16.4 minor で対応予定
- 5 バージョン連続持ち越し問題は §B 新規 ISSUE で将来解消経路を明文化済
