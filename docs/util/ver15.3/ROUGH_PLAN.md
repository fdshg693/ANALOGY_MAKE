---
workflow: full
source: master_plan
---

# ver15.3 ROUGH_PLAN

PHASE7.1 §3（`ROUGH_PLAN.md` と `PLAN_HANDOFF.md` の役割分離）を実装するマイナーバージョン。PHASE7.1 §1（ver15.0 `issue_scout` workflow） / §2（ver15.2 `QUESTIONS/` + `question_research` workflow）に続く 3 番目の節。既存 SKILL 3 本（`issue_plan` / `split_plan` / `quick_impl`）と `.claude/plans/VERSION_FLOW.md` の改訂を伴う、破壊性中〜高の plan 文書責務分割。

## ISSUE レビュー結果

`ISSUES/util/{high,medium,low}/` を走査したが、`status: review` かつ `assigned: ai` の ISSUE は **0 件**。遷移対象なし（書き換え実施なし）。

## ISSUE 状態サマリ

util カテゴリの `status × assigned` 分布（`python scripts/issue_status.py util` 実行結果、ver15.3 `/issue_plan` 起動時点）:

| priority | ready/ai | review/ai | need_human_action/human | raw/human | raw/ai |
|---|---|---|---|---|---|
| high | 0 | 0 | 0 | 0 | 0 |
| medium | 1 | 0 | 0 | 0 | 0 |
| low | 0 | 0 | 0 | 0 | 2 |

- `ready / ai` 1 件: `ISSUES/util/medium/issue-review-rewrite-verification.md`（util 単体消化不能で継続持ち越し、ver6.0 以来）
- `raw / ai` 2 件（ver14.0 観察持越し）:
  - `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md`
  - `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md`

## 選定結果

### 着手対象

**PHASE7.1 §3: `ROUGH_PLAN.md` と `PLAN_HANDOFF.md` の役割分離**（`docs/util/MASTER_PLAN/PHASE7.1.md` §3 を一次資料とする）。

### 選定理由

1. **`ready / ai` 1 件は util 単体で消化不能**: `issue-review-rewrite-verification.md` は `app` / `infra` カテゴリ起動時の目視確認を要求する性質上、util カテゴリ内の `/imple_plan` / `/quick_impl` では実動作確認できない。ver6.0 以来「util で拾える ready/ai が実質ゼロ」という状態が続いており、本バージョンも継続持ち越しとする。
2. **MASTER_PLAN PHASE7.1 は §1 / §2 完了の未完走**: §3 / §4 が残っており、本バージョンでは次節（§3）に着手するのが PHASE 構造上自然。ver15.2 `/retrospective` §3 でも「次バージョン ver15.3（マイナー）、PHASE7.1 §3 に着手」と明示推奨されている。
3. **§3 の前提条件は既に揃っている**: ver15.2 retrospective §2 に記載された drift-guard テスト（`RESERVED_WORKFLOW_VALUES` / `resolve_workflow_value` 同期を機械的に守る仕組み）は §3 で新 workflow が増えた場合もそのまま回帰防止として機能する。§3 着手に対する技術的ブロッカは検出できない。
4. **§3 と §4 のうち §3 を優先**: §3（plan 文書責務分割）は既存 SKILL 本文と成果物フォーマットの改訂、§4（run 単位通知）は通知実装と OS 制約対応で領域が独立。1 版に詰め込むと scope 過大（ver15.2 ROUGH_PLAN §除外理由と同型）のため、§3 を単独で扱い §4 は ver15.4 以降に分離する。
5. **add-only 原則との整合**: 新規 `PLAN_HANDOFF.md` ファイル種別追加（add）・既存 SKILL 本文の責務分割（rewrite）・過去 docs 改変なし（add-only 原則踏襲）という構成で、既存 ver15.2 以前の ROUGH_PLAN.md 群は touch しない。

### 除外理由

- **PHASE7.1 §4（run 単位通知）**: §3 と同時着手は scope 過大（上記 4 の通り）。§4 は ver15.4 以降に回す。
- **新 PHASE8.0 骨子作成**: PHASE7.1 が §1 / §2 完了のみの未完走のため不要（ver15.2 RETRO §3 の判断を継承）。
- **`issue-review-rewrite-verification.md`**: util 単体では消化不能。`app` / `infra` 起動まで継続持ち越し。
- **ver14.0 持越し 2 件**（`rules-paths-frontmatter-autoload-verification.md` / `scripts-readme-usage-boundary-clarification.md`）: 運用中に問題が顕在化するまで観察継続（ver15.2 RETRO §3 判定を継承）。
- **過去 ROUGH_PLAN.md の遡及的フォーマット統一**: ver15.0 / ver15.1 / ver15.2 の ROUGH_PLAN.md は既存フォーマットのまま残す。add-only 原則に従い、`PLAN_HANDOFF.md` 分離は **ver15.3 以降の新規バージョンにのみ適用**する。これにより過去 docs への破壊的変更を回避し、git history の safety を保つ。
- **`questions.py` / `issues.py` 重複の共通基盤化**: 3rd queue が登場するまで R7 トリガー条件に該当せず、ver15.3 スコープ外（ver15.2 handoff §保留事項を継承）。

## スコープ

### 実施する（PHASE7.1 §3 完了条件に対応）

1. **`PLAN_HANDOFF.md` の新設と役割定義**
   - 新ファイル種別 `PLAN_HANDOFF.md` を `docs/{category}/ver{X.Y}/` 配下に追加する
   - `ROUGH_PLAN.md` は「このバージョンで何をやるか」（スコープ定義書）へ責務を戻す
   - `PLAN_HANDOFF.md` は「判断経緯 / 除外候補 / 関連 ISSUE パス / 関連ファイル / 前提条件 / 後続 step への注意点」を担う
   - 両ファイルは `/issue_plan` が version 作成時に生成する
   - 後続 `/split_plan` / `/quick_impl` は両方を読む（実装方式決定の補助線として `PLAN_HANDOFF.md` を活用）

2. **ROUGH_PLAN.md / PLAN_HANDOFF.md の仕分け方針の明確化**
   - `ROUGH_PLAN.md` に残すもの: `workflow` / `source` frontmatter、バージョン種別判定、着手対象、スコープ（実施する / 実施しない）、成果物、ワークフロー選択根拠
   - `PLAN_HANDOFF.md` に逃がすもの: ISSUE レビュー結果、ISSUE 状態サマリ、選定理由・除外理由、付随的に触れる ISSUE、関連 ISSUE / ドキュメント、後続 `/split_plan` への引き継ぎメモ、事前リファクタリング要否の根拠記述
   - 注意: 本 ver15.3 自身の ROUGH_PLAN.md は**既存フォーマット**で書かれている（仕分け方針を定義する前の段階で書かれた文書であるため）。仕分け方針の実施開始は ver15.4 以降（`/split_plan` で `IMPLEMENT.md` 作成時に切り替えタイミングを決定する）

3. **既存 SKILL 3 本の改訂**
   - `.claude/skills/issue_plan/SKILL.md`: `ROUGH_PLAN.md` 作成手順を「スコープ定義のみ」に絞り、`PLAN_HANDOFF.md` 生成手順を新設する。`## ROUGH_PLAN.md の作成` 節と `## 準備` 節の改訂が主。frontmatter 記録（`workflow` / `source`）は `ROUGH_PLAN.md` 側に残す
   - `.claude/skills/split_plan/SKILL.md`: `ROUGH_PLAN.md` を主入力とする記述を「`ROUGH_PLAN.md` + `PLAN_HANDOFF.md` を両方読む」に改訂。frontmatter consistency チェック（`workflow: full` 確認）は `ROUGH_PLAN.md` 側で継続
   - `.claude/skills/quick_impl/SKILL.md`: 同様に「`ROUGH_PLAN.md` の変更方針 + `PLAN_HANDOFF.md` の handoff メモ」を両方読む記述へ改訂。quick は plan_review_agent を経由しないため、`PLAN_HANDOFF.md` の「後続 step への注意点」節が実装時の判断材料として直接機能する

4. **`.claude/plans/VERSION_FLOW.md` の改訂**
   - `docs/{category}/ver{X.Y}/` 配下のファイル構成説明に `PLAN_HANDOFF.md` を追加する
   - 「いつ作成するか」「誰が読むか」「ROUGH_PLAN.md との違い」を定義する

5. **プロジェクト CLAUDE.md の更新**
   - 「バージョン管理規則」節の「各バージョンフォルダの構成」リストに `PLAN_HANDOFF.md` を追加
   - 最小追記（1 行追加）に留める

6. **SKILL 間整合性の回帰防止**
   - `meta_judge/WORKFLOW.md` の step 記述（「`/issue_plan` が ROUGH_PLAN.md を作成」等）で `PLAN_HANDOFF.md` 生成にも言及するか確認
   - `retrospective/SKILL.md` のステップ番号付きリスト（`1. /issue_plan — ... ROUGH_PLAN.md 作成 ...` 等）で `PLAN_HANDOFF.md` 言及追加の要否を判断

7. **quick workflow の最小記載粒度定義**
   - PHASE7.1.md §3 リスク節で「quick タスクでは冗長に見える可能性があり、最小記載粒度を決めておく必要がある」と指摘されているため、`PLAN_HANDOFF.md` の quick 版最小粒度（例: 「関連 ISSUE パス」「後続 step への注意点」の 2 節のみ必須）を定義し、`issue_plan/SKILL.md` に記載する

8. **docs 整合**
   - `docs/util/MASTER_PLAN/PHASE7.1.md` の進捗表で §3 を「実装済み（ver15.3）」に更新（本バージョン `/wrap_up` または `/write_current` 段階で行う）

### 実施しない（本バージョンでは対象外）

- PHASE7.1 §4（run 単位通知）— ver15.4 以降で扱う
- **過去 ROUGH_PLAN.md の遡及的フォーマット統一**（ver15.0 / ver15.1 / ver15.2）— add-only 原則を踏襲、過去 docs は touch しない
- **本 ver15.3 自身の ROUGH_PLAN.md の仕分け方針適用** — ver15.3 ROUGH_PLAN.md 自体は既存フォーマットで書かれている（新仕分け方針を定義する前の段階の文書であるため）。実適用開始は ver15.4 以降
- `questions.py` / `issues.py` の共通基盤化（R7 トリガー条件、ver15.3 スコープ外）
- workflow YAML の model / effort 調整（ver15.2 時点で品質良好、handoff §保留事項を継承）
- 既存 `auto` / `full` / `quick` / `scout` / `question` workflow の runtime 挙動変更（SKILL 本文と plan 成果物のフォーマット変更に留める）
- `issue-review-rewrite-verification.md` の消化（`app` / `infra` 起動まで持ち越し）
- ver14.0 持越し 2 件の観察 / 消化
- 外部通知（Slack / Discord）との連携

## 成果物（想定）

| 成果物 | 種別 | 概要 |
|---|---|---|
| `docs/util/ver15.3/PLAN_HANDOFF.md` | 新規 | ver15.3 自身の handoff（新規生成の試金石として本バージョンで最初の 1 ファイル目を書く。ROUGH_PLAN.md との切り分け運用を自己適用する初回サンプル） |
| `.claude/skills/issue_plan/SKILL.md` | 変更 | `ROUGH_PLAN.md` 作成手順をスコープ定義のみに絞り、`PLAN_HANDOFF.md` 生成手順を新設。quick 版の最小記載粒度を定義 |
| `.claude/skills/split_plan/SKILL.md` | 変更 | 主入力を `ROUGH_PLAN.md` + `PLAN_HANDOFF.md` 両方に更新 |
| `.claude/skills/quick_impl/SKILL.md` | 変更 | 主入力を `ROUGH_PLAN.md` + `PLAN_HANDOFF.md` 両方に更新 |
| `.claude/plans/VERSION_FLOW.md` | 変更 | バージョン構成ファイルリストに `PLAN_HANDOFF.md` を追加 |
| `CLAUDE.md`（プロジェクトルート） | 変更 | 「各バージョンフォルダの構成」に `PLAN_HANDOFF.md` を 1 行追加 |
| `.claude/skills/meta_judge/WORKFLOW.md` | 変更候補 | step 記述で `PLAN_HANDOFF.md` 生成に言及（必要性を `/split_plan` で判断） |
| `.claude/skills/retrospective/SKILL.md` | 変更候補 | step 番号付きリストの記述更新（必要性を `/split_plan` で判断） |
| `docs/util/MASTER_PLAN/PHASE7.1.md` | 変更 | §3 進捗「実装済み（ver15.3）」 |
| `docs/util/ver15.3/IMPLEMENT.md` / `MEMO.md` / `CHANGES.md` / `RETROSPECTIVE.md` | 新規 | full workflow 成果物（後続 step で生成） |

コード（Python / YAML）の実装変更は**発生しない想定**。変更は SKILL 本文（Markdown）・docs（Markdown）・新ファイル種別の追加のみ。既存テスト（ver15.2 時点 252 件）は全件グリーンを維持する。新規テスト追加は原則不要だが、「`PLAN_HANDOFF.md` の存在検証を `/split_plan` / `/quick_impl` 起動時に行うか」を `/split_plan` で判断し、必要なら validation.py に軽量チェックを追加する（要否は IMPLEMENT.md で決定）。

## 影響範囲の先出し（既存 SKILL 本文で ROUGH_PLAN.md を主入力として読んでいる箇所の棚卸し）

ver15.3 で改訂対象となる既存 SKILL 本文中の `ROUGH_PLAN.md` 参照箇所（`grep "ROUGH_PLAN\.md" .claude/` 結果を根拠とする）:

| ファイル | 箇所 | 改訂方針 |
|---|---|---|
| `.claude/plans/VERSION_FLOW.md` L88, L104 | バージョンフォルダ構成説明（Before / After ブロックの両方） | `PLAN_HANDOFF.md` を 1 行追加 |
| `.claude/SKILLS/split_plan/SKILL.md` L15, L17, L19, L23, L25, L27, L29 | 役割節・ステップ 1 全体 | 主入力を「ROUGH_PLAN.md」→「ROUGH_PLAN.md + PLAN_HANDOFF.md」に更新。「事前リファクタリング不要」の 1 行記載先を `PLAN_HANDOFF.md` に変更するかは `/split_plan` で判断（本 ROUGH_PLAN では既存フォーマット踏襲） |
| `.claude/SKILLS/quick_impl/SKILL.md` L15, L18, L25 | 実装節・MEMO 節 | 主入力を両方参照に更新 |
| `.claude/SKILLS/issue_plan/SKILL.md` L26, L27, L75, L86, L88, L98, L102 | 役割節・workflow 選択節・ROUGH_PLAN.md 作成節・コミット節 | 「`ROUGH_PLAN.md` を作成する」→「`ROUGH_PLAN.md` と `PLAN_HANDOFF.md` を作成する」に更新。仕分け方針を新節「## PLAN_HANDOFF.md の作成」として追加。コミット対象に `PLAN_HANDOFF.md` 追加 |
| `.claude/SKILLS/retrospective/SKILL.md` L35, L36, L94 | 「/issue_plan は ROUGH_PLAN.md を作成」等の step 記述 | step 記述の文言更新（軽微） |
| `.claude/SKILLS/meta_judge/WORKFLOW.md` L8, L9, L19, L48, L49 | workflow 系譜説明 | step 記述の文言更新（軽微） |

上記 6 ファイルが本 §3 改訂の影響範囲。`scripts/` 配下（Python / YAML）には `ROUGH_PLAN.md` 参照箇所なし（`--workflow auto` の frontmatter 読みは `resolve_workflow_value` に集約されており、`workflow:` key の読み方自体は不変のため）。

## 関連 ISSUE / ドキュメント

- `docs/util/MASTER_PLAN/PHASE7.1.md` §3 — 一次資料（役割分担 / 完了条件 / ファイル変更一覧 / リスク）
- `docs/util/ver15.2/ROUGH_PLAN.md` — §3 を除外スコープとして扱った直前バージョンの記録（ver15.2 ROUGH_PLAN §除外理由で §3 を「既存 SKILL 本文の改訂を伴い、version flow 全体に影響する破壊性が相対的に高い」と評価）
- `docs/util/ver15.2/RETROSPECTIVE.md` §3 — 「次バージョンは ver15.3（マイナー）、PHASE7.1 §3 に着手」の一次推奨根拠
- `FEEDBACKS/handoff_ver15.2_to_next.md` — ver15.2 retrospective が次ループ向けに書き出した補助線（本 ROUGH_PLAN で明示した 3 項目の直接のインプット）
- `docs/util/ver15.0/IMPLEMENT.md` — add-only 構造の実装計画参考モデル（§1 scout）
- `docs/util/ver15.2/IMPLEMENT.md` — add-only 構造の実装計画参考モデル（§2 QUESTIONS）
- `.claude/SKILLS/issue_plan/SKILL.md` / `split_plan/SKILL.md` / `quick_impl/SKILL.md` — 改訂対象の既存 SKILL 本文
- `.claude/plans/VERSION_FLOW.md` — 改訂対象のバージョン管理規則文書
- `.claude/SKILLS/meta_judge/WORKFLOW.md` / `retrospective/SKILL.md` — 軽微改訂候補

## ワークフロー選択の根拠（`workflow: full`）

- PHASE7.1 §3 は MASTER_PLAN 新項目着手の継続 → SKILL 規則により **必ず `full`**
- 既存 SKILL 3 本（`issue_plan` / `split_plan` / `quick_impl`）と VERSION_FLOW.md を跨ぐ改訂で破壊性中〜高 → `quick` の条件（3 ファイル以下 / 100 行以下）を大幅に超過
- plan 成果物のフォーマット変更は後続 step へ直接影響し、plan_review_agent による設計レビューが必須 → `full`（quick には review がない）
- 判断に迷う場合は安全側で `full`（本件は明確に `full`）

したがって `workflow: full`（`/issue_plan` → `/split_plan` → `/imple_plan` → `/wrap_up` → `/write_current` → `/retrospective`）を採用する。

## バージョン種別の判定

**マイナー（ver15.3）**。以下根拠:

- MASTER_PLAN 新項目への着手ではあるが、**PHASE7.1 内の継続節**（§3）であり、新 PHASE の骨子作成や新規カテゴリ追加ではない（ver15.0 / ver15.2 の判定と同型）
- アーキテクチャ変更なし（runtime 変更はなく、SKILL 本文と成果物フォーマットの責務分割のみ）
- 新規外部ライブラリ導入なし
- 破壊的変更なし（既存 version ディレクトリ（ver15.2 以前）は touch せず、新 `PLAN_HANDOFF.md` は add-only で ver15.3 以降に適用）

メジャー昇格（ver16.0）は PHASE7.1 全節（§4 まで）完了時点で PHASE8.0 骨子の要否を判定する。本バージョン時点では時期尚早。

## 事前リファクタリング要否

**事前リファクタリング不要**。§3 は既存 SKILL 本文の責務分割（rewrite）と新 `PLAN_HANDOFF.md` ファイル種別追加（add）で、コード側の構造には触らない。Python / YAML への変更が発生しないため、リファクタ対象となる構造的な負債は検出できない。SKILL 本文の改訂は機械的な文言書き換えが中心で、複数の抽象化層を跨ぐ変更も発生しない。

## 後続 `/split_plan` への引き継ぎメモ

- **主入力**: `docs/util/MASTER_PLAN/PHASE7.1.md` §3（役割分担 / 完了条件 / ファイル変更一覧 / リスクが体系的に定義されている）。本 `ROUGH_PLAN.md` は選定経緯・影響範囲の棚卸し・add-only 原則の適用方針を提供する役割に留め、改訂後の SKILL 本文の具体記述（章立て・例示文・移行期の記述）は `/split_plan` 側で決定すること。
- **参考モデル**: ver15.0 / ver15.2 の `IMPLEMENT.md` が add-only / 新ファイル種別追加の同型構造を持つ。ただし本件は「新ファイル種別追加」+「既存 SKILL 本文の責務分割（rewrite）」のハイブリッドで、純粋 add-only ではない点が異なる。リスク表では「既存 SKILL 本文改訂による既存運用への影響」を独立リスクとして立てること。
- **自己適用の判断**: 本 ver15.3 自身の `PLAN_HANDOFF.md` を**本バージョン内で作成するかどうか**は `/split_plan` で判断する。選択肢は 2 つ:
  - (A) ver15.3 で初回 `PLAN_HANDOFF.md` を作成し、自己適用の試金石とする（IMPLEMENT.md 作成時に本 ROUGH_PLAN.md から handoff 情報を抽出）
  - (B) ver15.3 は SKILL 本文改訂のみに留め、`PLAN_HANDOFF.md` の実作成は ver15.4 以降の `/issue_plan` 実行時から開始する
  - 推奨: **(A)**（自己適用により ver15.3 RETROSPECTIVE で仕分け方針の妥当性を検証できる）。ただし IMPLEMENT.md で手戻りリスク・工数増を見積もって最終判断する。
- **仕分け方針の機械検証**: 新 `PLAN_HANDOFF.md` が「最低限これを含むべき」という項目リスト（例: 「関連 ISSUE パス」「後続 step への注意点」）を定義する場合、validation.py に軽量な存在チェックを追加するかは `/split_plan` で判断。ver15.0 で追加した `validate_startup()` と同系統の静的検査で十分な想定。
- **過去 docs 不可侵の徹底**: ver15.0 / ver15.1 / ver15.2 の既存 ROUGH_PLAN.md は**一切改変しない**。SKILL 本文で過去 ROUGH_PLAN.md を参照するサンプル記述がある場合も、ver15.3 以降の新規 version で例示する形に書き換える（過去 docs への breadcrumb 書き戻しを避ける）。
- **quick 版の最小粒度定義**: PHASE7.1.md §3 リスクで「quick タスクで冗長に見える」懸念があるため、`PLAN_HANDOFF.md` の quick 版最小必須項目を `issue_plan/SKILL.md` で明示すること。full 版との差分が一目で分かる table 形式が望ましい。
- **drift-guard テスト設計の継承**: ver15.2 で導入した `RESERVED_WORKFLOW_VALUES` と `resolve_workflow_value` 同期テスト設計は、§3 で新 workflow 追加が発生しない（SKILL 本文改訂のみ）ため本バージョンでは直接の追加契機はない。ただし将来 §4 で workflow YAML を触る際の前例として `/imple_plan` 段階で参照すること。
- **既存テストへの影響**: SKILL 本文改訂は Python テストに影響しない想定。ただし SKILL 本文の静的検査（例: `ROUGH_PLAN.md` 必須節の検証スクリプトがある場合）が走っていれば、そちらの期待値更新が必要。`/split_plan` で `scripts/tests/` 配下の test_skills*.py 等を grep して影響を棚卸しする。
- **コミット境界**: SKILL 3 本 + VERSION_FLOW.md + CLAUDE.md の改訂は論理的に 1 まとまりの変更。`/imple_plan` では複数コミットに分けず 1 コミットでまとめる方針を推奨（`docs(ver15.3): imple_plan完了` で一括）。ただし `PLAN_HANDOFF.md` 自己適用（選択肢 A）を採用する場合は、SKILL 本文改訂コミットと `PLAN_HANDOFF.md` 作成コミットを分離するかを `/imple_plan` で判断。
