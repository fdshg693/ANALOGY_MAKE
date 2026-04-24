---
workflow: full
source: master_plan
---

# ver15.3 PLAN_HANDOFF

PHASE7.1 §3（`ROUGH_PLAN.md` と `PLAN_HANDOFF.md` の役割分離）に着手する ver15.3 バージョンの plan 段階 handoff。ROUGH_PLAN.md から「スコープ定義」以外の判断ログ・関連資料・後続 step への注意点を抽出した自己適用の試金石（選択肢 A 採用、IMPLEMENT.md §1.5 / §5 参照）。

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

## 選定理由・除外理由

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

## 関連 ISSUE / 関連ファイル / 前提条件

### 一次資料・関連ドキュメント

- `docs/util/MASTER_PLAN/PHASE7.1.md` §3 — 一次資料（役割分担 / 完了条件 / ファイル変更一覧 / リスク）
- `docs/util/ver15.2/ROUGH_PLAN.md` — §3 を除外スコープとして扱った直前バージョンの記録（§3 を「既存 SKILL 本文の改訂を伴い、version flow 全体に影響する破壊性が相対的に高い」と評価）
- `docs/util/ver15.2/RETROSPECTIVE.md` §3 — 「次バージョンは ver15.3（マイナー）、PHASE7.1 §3 に着手」の一次推奨根拠
- `FEEDBACKS/handoff_ver15.2_to_next.md` — ver15.2 retrospective が次ループ向けに書き出した補助線（本 handoff の直接インプット）
- `docs/util/ver15.0/IMPLEMENT.md` — add-only 構造の実装計画参考モデル（§1 scout）
- `docs/util/ver15.2/IMPLEMENT.md` — add-only 構造の実装計画参考モデル（§2 QUESTIONS）

### 改訂対象ファイル（SKILL 本文・docs）

`grep "ROUGH_PLAN\.md" .claude/` 結果に基づき、ver15.3 で改訂対象となる既存 SKILL 本文中の `ROUGH_PLAN.md` 参照箇所:

| ファイル | 改訂方針 |
|---|---|
| `.claude/plans/VERSION_FLOW.md`（L104 付近） | バージョンフォルダ構成説明（After ブロック）に `PLAN_HANDOFF.md` を 1 行追加。Before 側は add-only 原則により触らない |
| `.claude/skills/split_plan/SKILL.md` | 主入力を「ROUGH_PLAN.md」→「ROUGH_PLAN.md + PLAN_HANDOFF.md」に更新 |
| `.claude/skills/quick_impl/SKILL.md` | 主入力を両方参照に更新 |
| `.claude/skills/issue_plan/SKILL.md` | 作成対象に PLAN_HANDOFF.md 追加、仕分け方針 table と quick 版最小粒度を新節として追加 |
| `.claude/skills/retrospective/SKILL.md` | step 記述の文言更新（軽微）+ §4.5 に役割の差分を 1 文追記 |
| `.claude/skills/meta_judge/WORKFLOW.md` | step 記述の文言更新（軽微）+ frontmatter one source of truth の明記 |
| `CLAUDE.md`（プロジェクトルート） | 「各バージョンフォルダの構成」に `PLAN_HANDOFF.md` を 1 行追加 |

### 前提条件

- `scripts/claude_loop.py` は `ROUGH_PLAN.md` の `workflow:` frontmatter のみを読む（`PLAN_HANDOFF.md` は読まない）→ Python 変更は**発生しない**
- 既存テスト 252 件（ver15.2 時点）は全件グリーン継続を前提とする
- `.claude/` 編集は `scripts/claude_sync.py` 経由（export → edit → import）で行う

## 後続 step への注意点

- **主入力**: `docs/util/MASTER_PLAN/PHASE7.1.md` §3（役割分担 / 完了条件 / ファイル変更一覧 / リスクが体系的に定義されている）。`ROUGH_PLAN.md` は選定経緯・影響範囲の棚卸し・add-only 原則の適用方針を提供する役割に留め、改訂後の SKILL 本文の具体記述（章立て・例示文・移行期の記述）は `/split_plan` 側で決定すること。
- **参考モデル**: ver15.0 / ver15.2 の `IMPLEMENT.md` が add-only / 新ファイル種別追加の同型構造を持つ。ただし本件は「新ファイル種別追加」+「既存 SKILL 本文の責務分割（rewrite）」のハイブリッドで、純粋 add-only ではない点が異なる。リスク表では「既存 SKILL 本文改訂による既存運用への影響」を独立リスクとして立てること。
- **自己適用の判断**: 本 ver15.3 自身の `PLAN_HANDOFF.md` を**本バージョン内で作成する**（IMPLEMENT.md §1.5 で選択肢 (A) 採用確定）。自己適用により ver15.3 RETROSPECTIVE で仕分け方針の妥当性を検証できる。
- **仕分け方針の機械検証**: 新 `PLAN_HANDOFF.md` が「最低限これを含むべき」という項目リスト（例: 「関連 ISSUE パス」「後続 step への注意点」）の存在チェックを `validation.py` に追加するかは **本バージョンでは見送り**（IMPLEMENT.md §8.3 結論）。省略ケースの頻度・誤省略の発生率を 1〜2 バージョン観察してから動的チェックを設計する。
- **過去 docs 不可侵の徹底**: ver15.0 / ver15.1 / ver15.2 の既存 ROUGH_PLAN.md は**一切改変しない**。SKILL 本文で過去 ROUGH_PLAN.md を参照するサンプル記述がある場合も、ver15.3 以降の新規 version で例示する形に書き換える（過去 docs への breadcrumb 書き戻しを避ける）。
- **quick 版の最小粒度定義**: PHASE7.1.md §3 リスクで「quick タスクで冗長に見える」懸念があるため、`PLAN_HANDOFF.md` の quick 版最小必須項目を `issue_plan/SKILL.md` で明示する（full 版 5 節 / quick 版 2 節の table を新節として追加）。
- **drift-guard テスト設計の継承**: ver15.2 で導入した `RESERVED_WORKFLOW_VALUES` と `resolve_workflow_value` 同期テスト設計は、§3 で新 workflow 追加が発生しない（SKILL 本文改訂のみ）ため本バージョンでは直接の追加契機はない。将来 §4 で workflow YAML を触る際の前例として `/imple_plan` 段階で参照すること。
- **既存テストへの影響**: SKILL 本文改訂は Python テストに影響しない想定。`scripts/tests/test_claude_loop_*.py` の `ROUGH_PLAN.md` 参照は全て `workflow:` frontmatter 検出の文脈で、`PLAN_HANDOFF.md` の有無に依存しない。新規テスト追加は不要。
- **コミット境界**: SKILL 5 本 + VERSION_FLOW.md + CLAUDE.md + `PLAN_HANDOFF.md` 自己適用は論理的に 1 まとまりの変更。IMPLEMENT.md §7 タイムラインで **1 コミットに束ねる** 方針を推奨（SKILL 改訂とサンプル PLAN_HANDOFF.md を同コミットで review 時に検証可能にするため）。`/wrap_up` で PHASE7.1.md 進捗更新が発生する場合、それは別コミットで自然に分離される。
