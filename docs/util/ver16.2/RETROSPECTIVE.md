# ver16.2 RETROSPECTIVE — PHASE8.0 §3 token/cost 計測 完走

本版は `research` workflow **2 回目の self-apply**。PHASE8.0 §3（cost 計測）を 8 step で完走し、PHASE8.0 全 3 節（§1 research / §2 deferred / §3 cost）が揃った。テスト 322 全 PASS、計画乖離 3 件はいずれも MEMO.md / CHANGES.md §技術的判断 に根拠付きで記録済み。ただし **cost tracking 実装の実機検証は本版では行われていない**（詳細は §8 末尾）。

---

## §1 ドキュメント構成

### MASTER_PLAN

- `docs/util/MASTER_PLAN/PHASE8.0.md` は §3 ✅ 追記済み、PHASE8.0 完走宣言も済。
- **新 PHASE 骨子の必要性: 据え置き**。PHASE8.0 完走によって「次 PHASE 検討」のトリガーは立ったが、既存 ready/ai 3 件の観察系 ISSUE と「cost tracking 実機突合」の消化が先。PHASE9.0 骨子作成は `/issue_plan` 次ループ判断に委ねる。

### CLAUDE.md

- ver16.2 では `experiments/` 説明文（tsx → 「tsx または Python」）の軽微更新のみ。分割不要。

### docs カテゴリ別

- minor のため `CURRENT.md` 新規作成なし、`CHANGES.md` のみ生成。
- `RESEARCH.md` / `EXPERIMENT.md` は 4 節必須構造を遵守。RESEARCH は一次資料 23 引用で SDK / pricing を spec レベル確定。EXPERIMENT は **6 仮説中 §U7 のみ実走・5 件は「未検証」扱い**で再開手順草稿を `experiments/cost-usage-capture/{slug}/README.md` に残した。ver16.1 と同じ「nested `claude` 禁止」ガードが機能。

### ISSUES

- 本版で新規追加・削除なし。ver16.1 で起票した `deferred-resume-twice-verification.md` を `raw/ai` → `ready/ai` に昇格（判定 3/3 クリア）。

---

## §2 バージョン作成の流れ（research workflow 2 回目評価）

### 全体評価

8 step `research` workflow は計画通り完走。良く機能した点:

- **RESEARCH.md の方針転換力**: 計画段階（IMPLEMENT §1-1）では「PRICE_BOOK を自前保持し `calculate_cost` で primary 計算」としていたが、`/research_context` が公式 SDK docs から「`total_cost_usd` / `modelUsage[*].costUSD` が CLI 出力にそのまま含まれる」と発見し、primary を raw 記録に切替・PRICE_BOOK を fallback に格下げする方針転換を安全に実施できた。**事前調査の投資が実装重量を減らした典型例**。
- **EXPERIMENT の先送り判断**: `/experiment_test` は nested `claude` 制約（ver16.1 retrospective で SKILL 化済のガード）に従い 5 仮説を「未検証」扱いに明示・再開手順を残した。本 run 後の本番 run で自然採取される見込みを根拠に、専用 ISSUE 起票も回避。
- **計画乖離の記録品質**: 3 件の乖離（primary source / `DeferredOutcome` 型拡張 / validation 見送り）をいずれも CHANGES.md §技術的判断 に理由付きで残した。

### 改善候補（観察メモ、次ループで判断）

- **`research` workflow の実効性と EXPERIMENT 先送り率**: 本版 EXPERIMENT は 6 仮説中 5 件が「nested `claude` が必要 → 先送り」で、`research` workflow の価値の半分（実機検証）が自動消化できない構造。今後も「公式 docs 読解 + 本番 run での自然採取」の組合せで済むテーマでは、`research` を選ぶより `full` で進めて retrospective 突合に回すほうが効率的なケースがある。ただし本版では primary 方針転換（PRICE_BOOK fallback 化）が RESEARCH 無しでは発生しえなかった可能性が高く、`research` 採用は正味プラス判定。次バージョンで `research` / `full` の cost sidecar 実データを比較し、採用基準を絞るかを判断。
- **cost tracking の実機検証遅延**: 本 run は ver16.1 完走時点（commit `80455c3`）の `claude_loop.py` process で起動したため、本 run 自体では **cost tracking が動作していない**（`logs/workflow/*.costs.json` 未生成）。初めて cost tracking 付きで走るのは次 run であり、§U1-a / §U1-b / §U6-a / R2 の実機突合は次バージョンの `/issue_plan` 冒頭 or 本版外の手動 smoke で行う必要がある。
- **YAML sync 契約**: ver16.2 も sync 踏まずに済んだ（`build_command` 内 hardcode）。累計 2 バージョン連続踏み外しできているのは設計勝利。

---

## §3 次バージョン推奨

### 材料

1. **ISSUE 状況**: `ready/ai` 3 件（`issue-review-rewrite-verification` / `toast-persistence-verification` / `deferred-resume-twice-verification`）は全て観察/実機検証系で util 単独 AI 自走は依然困難。`raw/ai` 2 件は triage 待ち。
2. **MASTER_PLAN 次項目**: PHASE8.0 **完走**。次 PHASE（PHASE9.0）の骨子は未作成・テーマ未確定。
3. **現行 PHASE 完走状態**: §1+§2+§3 全節 ✅。

### 推奨

**ver16.3（マイナー）**。理由:

- PHASE8.0 完走直後のため「新 PHASE 骨子作成を焦らない」観点から、まず **本版 cost tracking の実機突合**（R1 live silent / R2 SDK 型突合 / R4 deferred 分離の初回観察）を次 run の `/retrospective` 突合観点として走らせる。この突合自体が「§U1-a / §U1-b / §U6-a の事後裏取り」になり、ver16.2 先送り分の借金返済として機能する。
- **既存 ready/ai 3 件の triage**: cost tracking 実走後に `deferred-resume-twice-verification` の観察が自然進行する。残る 2 件は本版でも消化不能だが、`need_human_action/human` への振り直し是非を `issue_review` SKILL 側で拡張する ISSUE 起票を検討（本版では見送り、次ループに委任）。
- **PHASE9.0 骨子作成は時期尚早**: 既存 ISSUES 消化で当面吸収できる。`/retrospective` SKILL §2 の「PHASE 新設を焦らず既存 ISSUES 消化を明示」に該当。
- メジャー（ver17.0）は PHASE 境界 or アーキテクチャ変更を伴う着手時まで保留。

---

## §3.5 workflow prompt / model 評価

### 評価対象: ver16.2（`claude_loop_research.yaml`、2 回目 self-apply）

ver16.1 と同じ 8 step・同じ model/effort 構成で走らせたため、**差分評価の対象は各 step の artifact 品質（2 サンプル目）と、新規に追加した `costs.py` 関連 step の挙動**のみ。

| step | model | effort | 分類 | 理由・次ループ案 |
|---|---|---|---|---|
| issue_plan | opus | high | 維持 | handoff + MASTER_PLAN 明示割当 + `deferred-resume-twice-verification` 昇格の triage がクリアに機能。effort 維持 |
| split_plan | opus | high | 維持 | IMPLEMENT.md §0 に 6 論点整理、`plan_review_agent` の 6 指摘を全反映。effort high の価値継続 |
| research_context | opus | high | 維持 | 一次資料 23 引用で primary 方針転換（PRICE_BOOK fallback 化）を導出。2 サンプル目でも精度落ちなし。**model 下げは引き続き見送り**（判断材料として依然 2 サンプルしかない） |
| experiment_test | opus | high | 調整検討 | 6 仮説中 1 件のみ実走・5 件先送りで artifact の実負荷は軽かった。ただし SKILL 側で「nested `claude` 制約」の構造判定と再開手順生成は高精度で行われた。**次ループで `research` を 3 回目採用する際、effort: high → medium に下げて品質劣化が出るか観察**（現時点では維持） |
| imple_plan | opus | high | 維持 | 計画乖離 3 件を MEMO / CHANGES に根拠付きで残し、322 tests pass。effort 下げる余地なし |
| wrap_up | sonnet | medium | 維持 | リスク判定表 5 件と MEMO.md 追記のみ。粒度妥当 |
| write_current | sonnet | high | 維持 | CHANGES.md 147 行 + 技術的判断 4 件。effort high の効果確認 2 回目。`claude_loop.yaml` / `claude_loop_quick.yaml` への波及は本版でも見送り（minor で CHANGES のみのケースで high が必要か未検証） |
| retrospective | opus | medium | 維持 | 本 step |

### 保留メモ

- `experiment_test` effort 下げの判断材料: 本版は実走 1 件のみだったため「高 effort でも軽い artifact で済む → 下げても問題ない」仮説が立つが、**実走仮説が多い回で同様に品質を保てるか**の検証はまだできていない。3 サンプル目（`research` 3 回目採用）で判断。
- `write_current` effort high の他 YAML 波及: 依然保留。minor で `CHANGES.md` のみ・140 行前後に収まるケースは medium で十分な可能性も残る。

---

## §4 ISSUES 整理

### 新規追加・変更

- 新規: なし
- 変更: `ISSUES/util/medium/deferred-resume-twice-verification.md` を `raw/ai` → `ready/ai`（ver16.2 `/issue_plan` で昇格済、本 retrospective 時点で据え置き）

### 持ち越し（削除せず据え置き）

- `ISSUES/util/medium/issue-review-rewrite-verification.md`（`ready/ai`、util 単独消化不能）— 5 バージョン連続持ち越し
- `ISSUES/util/low/toast-persistence-verification.md`（`ready/ai`、Windows 実機必須）— 5 バージョン連続持ち越し
- `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md`（`raw/ai`、triage 待ち）
- `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md`（`raw/ai`、triage 待ち）
- `ISSUES/util/medium/deferred-resume-twice-verification.md`（`ready/ai`、cost tracking 実機検証と合流可能）

### 削除対象

なし（本版で解決した ISSUE は 0 件）。

### レトロスペクティブでの追記

なし。次ループ handoff で「長期持ち越し ready/ai の `issue_review` SKILL 側での再判定手順追加」を継続課題として引き継ぐ。

---

## §5 即時適用したスキル変更

**なし**（本版観察結果の多くは「次ループ以降で判断」「実機突合が先」タイプで、即 SKILL に書き起こせるルール化は発生しなかった）。

ver16.1 で `.claude/skills/experiment_test/SKILL.md` に追加した「nested `claude` 禁止」ガードは本版でも期待通り機能し、`research` workflow の安全弁としての価値を再確認。ver16.2 でのガード追加は不要。

---

## §6 次ループ handoff

`FEEDBACKS/handoff_ver16.2_to_next.md` を別途作成。次ループ `/issue_plan` への補助入力として渡すのは:

- PHASE8.0 完走後の次バージョン種別（`ver16.3` minor 推奨、PHASE9.0 骨子作成は時期尚早）
- **cost tracking 初回本番観察の突合観点**: 次 run が cost tracking 付きの初回 run になるため、`logs/workflow/*.costs.json` を `/retrospective` 突合する具体観点（R1 / R2 / R4 と §U1-a / §U1-b / §U6-a の合流）
- `experiment_test` effort 下げ判断は 3 サンプル目（次の `research` 採用時）に持ち越し
- 長期持ち越し ready/ai 4 件の扱い（`issue_review` SKILL 拡張の ISSUE 起票検討）

---

## §8 補足: 本版で実機検証されなかった事項

本 retrospective 時点で **以下はいずれも未検証**。いずれも次 run の `/retrospective` で突合予定:

| 項目 | 検証先 |
|---|---|
| R1: `--output-format json` による live stdout サイレント化の実害度 | 次 run の log 可読性観察 |
| R2: SDKResultMessage 型と実機 JSON の key / 型突合 | 次 run の `*.costs.json` 内 key set |
| R4: deferred execution の cost 3 kind 別 record | 次の deferred 発火 run |
| §U1-a: `--output-format json` の実出力 sample | 同上 |
| §U1-b: `modelUsage` の key 名（kebab-case model ID） | 同上 |
| §U6-a: live stream 挙動の A/B/C 判定 | 同上 |

**重要**: 本 run は ver16.1 完走コミット（`80455c3`）の `claude_loop.py` process で起動しており、cost tracking は動作していない（`logs/workflow/20260424_184939_claude_loop_issue_plan.costs.json` は生成されない）。初回本番観察は次 run に委ねる。
