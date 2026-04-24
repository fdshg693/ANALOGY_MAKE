# ver15.3 CHANGES

PHASE7.1 §3（`ROUGH_PLAN.md` と `PLAN_HANDOFF.md` の役割分離）の実装。ver15.2 からの変更差分。

## 変更ファイル一覧

| ファイル | 種別 | 概要 |
|---|---|---|
| `.claude/SKILLS/issue_plan/SKILL.md` | 変更 | `ROUGH_PLAN.md` + `PLAN_HANDOFF.md` 二ファイル生成に対応。仕分け方針 table / quick・full 記載粒度 table / 省略条件を新節として追加 |
| `.claude/SKILLS/split_plan/SKILL.md` | 変更 | 主入力を `ROUGH_PLAN.md` 単体 → `ROUGH_PLAN.md` + `PLAN_HANDOFF.md` の両方に更新 |
| `.claude/SKILLS/quick_impl/SKILL.md` | 変更 | 同上（quick workflow も両ファイルを読む記述へ） |
| `.claude/SKILLS/meta_judge/WORKFLOW.md` | 変更 | step 説明の文言を `PLAN_HANDOFF.md` 生成に言及する形に軽微改訂。frontmatter one source of truth の注記追加 |
| `.claude/SKILLS/retrospective/SKILL.md` | 変更 | step 番号付きリストの `ROUGH_PLAN.md` 言及を `ROUGH_PLAN.md と PLAN_HANDOFF.md` に更新。§4.5 に `PLAN_HANDOFF.md` との役割差分を 1 文追記 |
| `.claude/plans/VERSION_FLOW.md` | 変更 | After ブロックのバージョンフォルダ構成リストに `PLAN_HANDOFF.md` を 1 行追加（Before 側は add-only 原則により据え置き） |
| `CLAUDE.md`（プロジェクトルート） | 変更 | 「各バージョンフォルダの構成」に `PLAN_HANDOFF.md` を 1 行追加 |
| `docs/util/ver15.3/PLAN_HANDOFF.md` | 新規 | ver15.3 自身の自己適用サンプル（新ファイル種別の初回実例） |
| `docs/util/MASTER_PLAN/PHASE7.1.md` | 変更 | §3 の状態を「未着手」→「実装済み（ver15.3）」に更新 |
| `FEEDBACKS/handoff_ver15.2_to_next.md` | 移動 | `FEEDBACKS/done/` へ消費済み移動 |
| `ISSUES/util/medium/plan-handoff-generation-followup.md` | 新規 | 次 `/issue_plan` で PLAN_HANDOFF.md が実際に生成されるか観察する follow-up |
| `ISSUES/util/low/plan-handoff-frontmatter-drift.md` | 新規 | frontmatter (`workflow:` / `source:`) の乖離監視（ver15.4 以降観察） |
| `ISSUES/util/low/plan-handoff-omission-tracking.md` | 新規 | quick 版で PLAN_HANDOFF.md 省略が乱発されないか観察 |

## 変更内容の詳細

### PLAN_HANDOFF.md 新ファイル種別の導入

`docs/{category}/ver{X.Y}/` 配下に `ROUGH_PLAN.md` の姉妹ファイルとして `PLAN_HANDOFF.md` を新設。役割分担は以下の通り:

- **ROUGH_PLAN.md**: 「このバージョンで何をやるか」のスコープ定義書。着手対象・スコープ・成果物・workflow 選択根拠・バージョン種別判定・事前リファクタリング要否の結論を保持する
- **PLAN_HANDOFF.md**: 「なぜこれを選んだか」と「後続 step への引き継ぎ」。ISSUE レビュー結果・状態サマリ・選定理由・除外理由・関連 ISSUE パス・後続 step への注意点を担う

#### full 版必須節（5 節）

1. `## ISSUE レビュー結果`
2. `## ISSUE 状態サマリ`
3. `## 選定理由・除外理由`
4. `## 関連 ISSUE / 関連ファイル / 前提条件`
5. `## 後続 step への注意点`

#### quick 版必須節（2 節）

1. `## 関連 ISSUE / 関連ファイル`
2. `## 後続 step への注意点`

quick では ISSUE レビュー結果・状態サマリ・選定理由・除外理由は `ROUGH_PLAN.md` 本文側に残す（`/split_plan` が挟まらないため分離メリットが薄い）。

#### 省略条件

後続 step に渡す handoff 情報が全てゼロの場合のみ省略可（空ファイル作成は禁止）。省略した場合は `ROUGH_PLAN.md` 末尾に「PLAN_HANDOFF.md 省略（handoff 情報なし）」の 1 行を残す。

#### frontmatter の重複保持

`workflow:` / `source:` は `ROUGH_PLAN.md` と `PLAN_HANDOFF.md` の両方に同値で保持する（後続 step が `PLAN_HANDOFF.md` 単体でも意味を取れるようにするための冗長化。`workflow:` の one source of truth は `ROUGH_PLAN.md` 側で、`claude_loop.py` はそちらのみを読む）。

### issue_plan SKILL の責務分割

`issue_plan/SKILL.md` を最も大きく改訂した。変更点:

- 役割節: `ROUGH_PLAN.md を作成する` → `ROUGH_PLAN.md と PLAN_HANDOFF.md を作成する`
- `## ROUGH_PLAN.md の作成` 節を `## ROUGH_PLAN.md と PLAN_HANDOFF.md の作成` に改題し、`### ROUGH_PLAN.md に書く内容` サブ節と `### 仕分け方針（full / quick 共通）` table を追加
- `## PLAN_HANDOFF.md の quick / full 記載粒度` を新設（必須節 table・省略条件・後続情報引き継ぎの手順を記載）
- コミット節: `ROUGH_PLAN.md をコミット` → `ROUGH_PLAN.md と PLAN_HANDOFF.md をコミット`

### split_plan / quick_impl の入力拡張

両 SKILL の役割節とステップ 1 の記述を「ROUGH_PLAN.md + PLAN_HANDOFF.md の両方を読む」に更新。`PLAN_HANDOFF.md` が存在しない（= handoff 情報ゼロと判定して省略）場合は `ROUGH_PLAN.md` のみで進めてよい旨を明記。

### 自己適用サンプル（ver15.3 PLAN_HANDOFF.md）

ver15.3 自身の `docs/util/ver15.3/PLAN_HANDOFF.md` を本バージョン内で作成（選択肢 A 採用）。新フォーマットが「読めば動く」レベルで書けているかを RETROSPECTIVE §3 で検証するための試金石。`ROUGH_PLAN.md` は一切改変せず、別ファイルとして情報を再構成した（add-only 原則踏襲）。

### PHASE7.1.md 進捗更新

`docs/util/MASTER_PLAN/PHASE7.1.md` L11 の §3 行を「未着手」→「実装済み（ver15.3）」に更新。§4（Python スクリプト終了時通知）は未着手のまま ver15.4 以降に持ち越し。

## 技術的判断

### validation.py への PLAN_HANDOFF.md 存在チェック追加は見送り（ver15.3）

ROUGH_PLAN.md §1.2 / §1.3 で quick / full とも「handoff 情報ゼロなら省略可」という抜け道を定義したため、存在必須の静的チェックを早期に入れると正当に省略したケースを false positive 判定するリスクがある。1〜2 バージョン運用観察してから設計する方針とし、フォローアップ ISSUE を 3 件起票して観察を継続する。

### 既存 ROUGH_PLAN.md（ver15.2 以前）の遡及変更は行わない

add-only 原則を踏襲。`PLAN_HANDOFF.md` の分離は ver15.3 以降の新規バージョンにのみ適用する。過去 docs は git 履歴の安全性保持のため一切 touch しない。

### Python / YAML 変更なし

`claude_loop.py` は `ROUGH_PLAN.md` の `workflow:` frontmatter のみを読む実装であり、`PLAN_HANDOFF.md` を読まない設計のため Python 変更は発生しない。既存テスト 252 件全 pass（回帰なし）。
