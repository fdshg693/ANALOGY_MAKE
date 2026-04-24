# ver15.3 IMPLEMENT.md

PHASE7.1 §3（`ROUGH_PLAN.md` と `PLAN_HANDOFF.md` の役割分離）の実装案。ROUGH_PLAN.md のスコープを前提に、章立て・例示文・移行期の記述・コミット境界まで踏み込んで確定する。

## 0. 前提確認（既存ファイル状況の再確認結果）

以下は本 IMPLEMENT 作成時に `Read` / `Grep` で確認した現状。計画の二重適用や「既に対応済みの機能を重複計上する」ミスを避けるための備忘録。

| 確認対象 | 現状 | 備考 |
|---|---|---|
| `docs/util/ver15.3/` | `ROUGH_PLAN.md` のみ存在 | `/issue_plan` コミット `6bfcfb6` で作成済み |
| `docs/util/ver15.4/` | 存在しない | `/split_plan` 起動時のコンテキストで「次のマイナー 15.4」と出ているが、実際の in-progress は ver15.3。以後本書では一貫して **ver15.3** と呼ぶ |
| `.claude/skills/issue_plan/SKILL.md` | 「`ROUGH_PLAN.md` を作成する」単一成果物前提 | L26, L75, L86, L88, L98, L102-L103 が改訂対象 |
| `.claude/skills/split_plan/SKILL.md` | 主入力 `ROUGH_PLAN.md` のみ | L15, L23 が改訂対象（`## 役割` + ステップ1冒頭） |
| `.claude/skills/quick_impl/SKILL.md` | 主入力 `ROUGH_PLAN.md` のみ | L15, L18 が改訂対象 |
| `.claude/skills/meta_judge/WORKFLOW.md` | step 記述で「ROUGH_PLAN.md 作成」のみ | L8, L19 が軽微改訂対象 |
| `.claude/skills/retrospective/SKILL.md` | step 番号付きリストで ROUGH_PLAN.md のみ言及 | L35-L36 が軽微改訂対象（§3.5 template / §4.5 handoff は無改訂） |
| `.claude/plans/VERSION_FLOW.md` | L88 (Before) / L104 (After) に version folder 構成リスト | L104 に `PLAN_HANDOFF.md` を 1 行追加（L88 の Before 側は「移行前の過去記録」として触らない） |
| `CLAUDE.md`（project root）L52-L57 | version folder 構成リスト | L52 (`ROUGH_PLAN.md`) の直後に `PLAN_HANDOFF.md` を 1 行追加 |
| `scripts/claude_loop.py` | `ROUGH_PLAN.md` は `workflow:` frontmatter 読み出しのみ | `PLAN_HANDOFF.md` は読まない。Python 変更は**発生しない** |
| `scripts/tests/test_claude_loop_*.py` | `ROUGH_PLAN.md` の workflow frontmatter 生成・検出を検証 | `PLAN_HANDOFF.md` 追加は既存テストに影響なし（新規テスト不要） |
| `scripts/README.md` / `scripts/USAGE.md` | `ROUGH_PLAN.md` 参照箇所はいずれも workflow frontmatter 文脈 | 本バージョンでは**改訂しない**（ROUGH_PLAN スコープ通り） |
| `.claude/skills/issue_scout/SKILL.md` | ROUGH_PLAN.md 生成を行わない探索専用 | 影響なし（scout は `ISSUES/` 起票のみ） |
| `.claude/skills/question_research/SKILL.md` | QUESTIONS の調査専用 | 影響なし |
| `scripts/claude_loop_lib/validation.py` | `validate_startup()` は YAML / CWD / カテゴリを検査 | `PLAN_HANDOFF.md` 存在検証の追加要否は本書 §7 で決定 |

## 1. `PLAN_HANDOFF.md` の役割定義と記載フォーマット

### 1.1 位置づけ

`PLAN_HANDOFF.md` は **ROUGH_PLAN.md の姉妹ファイル**として `docs/{category}/ver{X.Y}/` に置き、以下 2 つの読み手を想定する:

1. **後続 `/split_plan` / `/quick_impl`**: 実装方式決定の補助線。選定理由・除外理由・事前条件・注意点を参照する
2. **後続バージョンの `/issue_plan`**: 直前バージョンの判断経緯・保留事項を引き継ぐ情報源（retrospective の `RETROSPECTIVE.md` とは別レーンで残る「plan 段階の判断ログ」）

### 1.2 節構成（full 版・標準）

以下 5 節を必須とする。各節の位置付けと「ROUGH_PLAN.md には書かなくなるもの」を明示する。

```markdown
---
workflow: full
source: issues | master_plan
---

# ver{X.Y} PLAN_HANDOFF

## ISSUE レビュー結果
{review / ai → ready / ai または need_human_action / human への遷移サマリ。件数と対象パスを残す}

## ISSUE 状態サマリ
{issue_status.py の status × assigned 分布、ver{X.Y} /issue_plan 起動時点のスナップショット}

## 選定理由・除外理由
{ROUGH_PLAN.md の「### 着手対象」を選んだ根拠と、同列候補を落とした理由}

## 関連 ISSUE / 関連ファイル / 前提条件
{一次資料（MASTER_PLAN / PHASE / 直前 RETRO / handoff FEEDBACK）、改訂対象 SKILL / docs のパスリスト、成立前提}

## 後続 step への注意点
{/split_plan に向けた引き継ぎメモ、参考モデル、判断委ねポイント、コミット境界の推奨}
```

**frontmatter**: `workflow` と `source` は `ROUGH_PLAN.md` と**同一値を重複保持**する（後続 step が `PLAN_HANDOFF.md` 単体でも意味を取れるようにするため。片方を消し忘れた場合に誤読を避ける冗長化）。値の同期は次項 §6 の drift-guard で段階的に守る（本バージョンでは目視確認）。

### 1.3 節構成（quick 版・最小）

quick workflow では冗長化リスクが指摘されている（PHASE7.1.md §3 リスク）ため、以下 2 節のみ**必須**とする:

```markdown
---
workflow: quick
source: issues | master_plan
---

# ver{X.Y} PLAN_HANDOFF

## 関連 ISSUE / 関連ファイル
{`ISSUES/{cat}/{pri}/*.md` の着手対象パス、変更対象ファイルの想定リスト}

## 後続 step への注意点
{/quick_impl に向けた実装方針メモ、避けるべき拡張、コミット粒度の推奨}
```

「ISSUE レビュー結果」「ISSUE 状態サマリ」「選定理由・除外理由」は **ROUGH_PLAN.md の本文側に残す**（quick では `/split_plan` が挟まらないため分離メリットが薄い）。この差分は `issue_plan/SKILL.md` の改訂時に table で明示する。

### 1.4 ROUGH_PLAN.md / PLAN_HANDOFF.md の仕分け方針（確定版）

| 節 / 内容 | full 版: 書く先 | quick 版: 書く先 |
|---|---|---|
| `workflow` / `source` frontmatter | 両方（同期） | 両方（同期） |
| バージョン種別の判定 | ROUGH_PLAN.md | ROUGH_PLAN.md |
| 着手対象 / スコープ（実施する / 実施しない） | ROUGH_PLAN.md | ROUGH_PLAN.md |
| 成果物（想定一覧） | ROUGH_PLAN.md | ROUGH_PLAN.md |
| ワークフロー選択根拠 | ROUGH_PLAN.md | ROUGH_PLAN.md |
| 事前リファクタリング要否（の結論） | ROUGH_PLAN.md | ROUGH_PLAN.md |
| ISSUE レビュー結果・状態サマリ | **PLAN_HANDOFF.md** | ROUGH_PLAN.md（quick は分離しない） |
| 選定理由・除外理由 | **PLAN_HANDOFF.md** | ROUGH_PLAN.md（quick は分離しない） |
| 関連 ISSUE / 関連ファイル / 前提条件 | **PLAN_HANDOFF.md** | **PLAN_HANDOFF.md** |
| 後続 step への注意点・引き継ぎメモ | **PLAN_HANDOFF.md** | **PLAN_HANDOFF.md** |
| 事前リファクタリング要否の**根拠記述** | **PLAN_HANDOFF.md** | ROUGH_PLAN.md に 1 行で統合可 |

### 1.5 自己適用（ver15.3 自身の PLAN_HANDOFF.md）

ROUGH_PLAN.md §後続引き継ぎメモ §選択肢 (A) / (B) のうち **(A) 採用**。`docs/util/ver15.3/PLAN_HANDOFF.md` を本バージョンの成果物として `/imple_plan` 段階で作成する（本書 §5 に記載）。

- 採用理由: (a) 自己適用により §2 の SKILL 本文改訂が「読めば動く」レベルで書けているか RETROSPECTIVE §3 で検証可能、(b) ver15.4 以降で毎回 `/issue_plan` が生成する前に「最初の 1 ファイル目」を試作する意義が大きい、(c) ROUGH_PLAN.md §後続引き継ぎメモに並んでいる項目をそのまま PLAN_HANDOFF.md に転記するだけで原型が作れるため工数増は軽微（見積り 30 分以内）
- 注意点: 本 ver15.3 の `ROUGH_PLAN.md` は既存フォーマット（handoff 情報が本文に混在）で書かれているため、「ver15.3 ROUGH_PLAN.md の一部を PLAN_HANDOFF.md に機械的に再配置」するのではなく、**新規に「ver15.3 の PLAN_HANDOFF.md として見返すと何が残るか」を抽出する形**で書く。ROUGH_PLAN.md の本文改変は行わない（add-only）

## 2. 既存 SKILL 3 本の改訂方針（確定版）

全 SKILL 改訂は `python scripts/claude_sync.py export` → `.claude_sync/` 配下で編集 → `python scripts/claude_sync.py import` の手順（`.claude/rules/claude_edit.md`）で行う。

### 2.1 `.claude/skills/issue_plan/SKILL.md`

| 変更箇所 | 現行（抜粋） | 改訂後方針 |
|---|---|---|
| L26 (役割節) | `docs/{カテゴリ}/ver{次バージョン}/ROUGH_PLAN.md を作成する` | `... の ROUGH_PLAN.md と PLAN_HANDOFF.md を作成する` |
| L27 (役割節) | frontmatter 記録の説明 | **据え置き**（`workflow` / `source` は ROUGH_PLAN.md 側に残る旨を補足: 「両ファイル frontmatter は同値で同期する」の 1 文追加） |
| L75 (`## バージョン種別の判定` 末尾) | `新しい空の docs/... フォルダを作成` | 据え置き |
| L86-L103 (`## ROUGH_PLAN.md の作成`) | 節タイトル / 本文 | 節タイトルを `## ROUGH_PLAN.md と PLAN_HANDOFF.md の作成` に改題。本文を「ROUGH_PLAN.md に書く内容」「PLAN_HANDOFF.md に書く内容」の 2 小節に分割。§1.4 の仕分け table をそのまま転載（single source of truth は SKILL 本文側） |
| L98 (粒度注意) | 「ROUGH_PLAN の粒度に注意」 | 据え置き（スコープ記述の粒度注意は引き続き ROUGH_PLAN.md に効く） |
| L99 (「後続 /split_plan への情報引き継ぎ」箇条書き) | 判断経緯・関連ファイル等を ROUGH_PLAN.md に漏れなく記載 | 「漏れなく記載」先を **PLAN_HANDOFF.md に変更**。ROUGH_PLAN.md 側ではスコープ変更と整合しない場合にのみ注記 |
| L102-L103 (コミット節) | `作成した ROUGH_PLAN.md をコミット` | `作成した ROUGH_PLAN.md と PLAN_HANDOFF.md をコミット`。`PLAN_HANDOFF.md` が省略される（= 特記事項ゼロ）ケースの判断基準を 1 行追加: 「handoff 情報が全てスコープ定義側に吸収でき、注意点もない場合は quick/full を問わず PLAN_HANDOFF.md 作成を省略してよい」 |

**新規追加節**: `## PLAN_HANDOFF.md の quick / full 記載粒度`（L98 と L102 の間に差し込み）

```markdown
## PLAN_HANDOFF.md の quick / full 記載粒度

PLAN_HANDOFF.md は full / quick の 2 粒度で運用する。下表の必須節を満たすこと（IMPLEMENT 側の §1 仕分け方針に基づく固定フォーマット）:

| workflow | 必須節 |
|---|---|
| full | `## ISSUE レビュー結果` / `## ISSUE 状態サマリ` / `## 選定理由・除外理由` / `## 関連 ISSUE / 関連ファイル / 前提条件` / `## 後続 step への注意点` の 5 節 |
| quick | `## 関連 ISSUE / 関連ファイル` / `## 後続 step への注意点` の 2 節 |

frontmatter は ROUGH_PLAN.md と同値（`workflow:` / `source:`）で重複保持する。

**省略条件**: 後続 step に渡す handoff 情報が全てゼロの場合のみ PLAN_HANDOFF.md 作成を省略してよい
（空ファイル作成は禁止）。「全てゼロ」の判定基準は以下をすべて満たすこと:
- 選定理由・除外理由が自明（ROUGH_PLAN.md スコープで完結しており、代替候補の検討が発生していない）
- 関連 ISSUE パスが ROUGH_PLAN.md 本文内で全て列挙済み
- 後続 step（`/split_plan` or `/quick_impl`）に渡す注意点が 1 件もない

省略した場合は ROUGH_PLAN.md 末尾に「PLAN_HANDOFF.md 省略（handoff 情報なし）」の 1 行を残す。
```

（SKILL 本文側の `§1.3` という節番号は自己参照になるため、上記追加節ではテキストを自己完結化した。IMPLEMENT.md §1.3 の table を single source of truth とし、SKILL 本文では再掲する形を取る。）

### 2.2 `.claude/skills/split_plan/SKILL.md`

| 変更箇所 | 現行（抜粋） | 改訂後方針 |
|---|---|---|
| L15 (役割節) | `/issue_plan が作成した ROUGH_PLAN.md を起点に` | `/issue_plan が作成した ROUGH_PLAN.md と PLAN_HANDOFF.md を起点に` |
| L17 | 現状把握・ISSUE レビュー・ROUGH_PLAN.md 作成は `/issue_plan` の責務 | `ROUGH_PLAN.md 作成` → `ROUGH_PLAN.md と PLAN_HANDOFF.md 作成`（他は据え置き） |
| L23 (ステップ1冒頭) | `ROUGH_PLAN.md を読み、対象タスクを固定する` | `ROUGH_PLAN.md（スコープ定義）と PLAN_HANDOFF.md（選定理由・注意点・関連 ISSUE パス）の両方を読み、対象タスクを固定する。PLAN_HANDOFF.md が存在しない（= /issue_plan で handoff 情報ゼロと判定）場合は ROUGH_PLAN.md のみで進めてよい` |
| L25 (frontmatter consistency) | `ROUGH_PLAN.md frontmatter に workflow: full` | 据え置き（`workflow:` の one source of truth は ROUGH_PLAN.md 側） |

### 2.3 `.claude/skills/quick_impl/SKILL.md`

| 変更箇所 | 現行（抜粋） | 改訂後方針 |
|---|---|---|
| L15 (実装節冒頭) | `ROUGH_PLAN.md の変更方針に基づいて実装を行う` | `ROUGH_PLAN.md（変更方針）と PLAN_HANDOFF.md（後続 step への注意点・関連 ISSUE パス）に基づいて実装を行う。PLAN_HANDOFF.md が存在しない場合は ROUGH_PLAN.md のみで進めてよい` |
| L18 (乖離時の MEMO 記載) | `ROUGH_PLAN.md の計画と異なる判断` | 据え置き（スコープとの乖離は ROUGH_PLAN.md 基準） |
| L25 (品質確認) | `ROUGH_PLAN.md でテスト方針が指定されている場合` | 据え置き（テスト方針はスコープ定義側の属性） |

### 2.4 `.claude/skills/meta_judge/WORKFLOW.md`

| 変更箇所 | 現行 | 改訂後方針 |
|---|---|---|
| L8 (step 1 説明) | `/issue_plan — ... ROUGH_PLAN.md 作成 + workflow 判定` | `/issue_plan — ... ROUGH_PLAN.md と PLAN_HANDOFF.md 作成 + workflow 判定` |
| L9 (step 2 説明) | `/split_plan — ROUGH_PLAN.md を起点に ...` | `/split_plan — ROUGH_PLAN.md と PLAN_HANDOFF.md を起点に ...` |
| L19 (quick step 1 説明) | `/issue_plan — ... ROUGH_PLAN.md 作成（workflow=quick）` | `/issue_plan — ... ROUGH_PLAN.md と（必要なら）PLAN_HANDOFF.md 作成（workflow=quick）` |
| L48-L49 (保守上の注意) | workflow YAML 同期 + `ROUGH_PLAN.md 冒頭の workflow: ... で分岐材料` | `workflow: / source:` の one source of truth は ROUGH_PLAN.md 側に保つ旨を 1 文追記 |

### 2.5 `.claude/skills/retrospective/SKILL.md`

| 変更箇所 | 現行 | 改訂後方針 |
|---|---|---|
| L35 (step 1 説明) | `/issue_plan — 現状把握・ISSUE レビュー・ROUGH_PLAN.md 作成（frontmatter に ...）を行った` | `/issue_plan — 現状把握・ISSUE レビュー・ROUGH_PLAN.md と PLAN_HANDOFF.md 作成（frontmatter に ...）を行った` |
| L36 (step 2 説明) | `/split_plan — ROUGH_PLAN.md を受けて REFACTOR.md・IMPLEMENT.md を作成` | `/split_plan — ROUGH_PLAN.md と PLAN_HANDOFF.md を受けて REFACTOR.md・IMPLEMENT.md を作成` |

§3.5 (`workflow prompt / model 評価`) / §4.5 (handoff FEEDBACK) は `PLAN_HANDOFF.md` と役割が重複しないことを RETRO で明示するため、§4.5 の冒頭に 1 文追記:

```markdown
（`PLAN_HANDOFF.md` は plan 段階の判断ログとして同バージョン内に残り、本節 `FEEDBACKS/handoff_*.md` は次ループへの 1 回限りの補助入力。役割が異なるため二重管理にはならない）
```

## 3. `.claude/plans/VERSION_FLOW.md` の改訂

L103-L110（`#### After` ブロック）の version folder 構成リストに `PLAN_HANDOFF.md` を 1 行追加する。位置は `ROUGH_PLAN.md` の直後。

```diff
 各バージョンフォルダ `docs/{category}/ver{X.Y}/` の構成:
 - `ROUGH_PLAN.md` — タスク概要
+- `PLAN_HANDOFF.md` — 選定理由・除外理由・関連 ISSUE パス・後続 step への注意点（handoff 情報ゼロなら省略可）
 - `REFACTOR.md` — リファクタリング計画
 - `IMPLEMENT.md` — 実装計画
 - `MEMO.md` — 実装メモ・残課題
 - `CURRENT.md` — **メジャーバージョンのみ**: コード現況の完全版（CLAUDE.md と重複しない内容のみ）
 - `CHANGES.md` — **マイナーバージョンのみ**: 前バージョンからの変更差分
```

L88 (`#### Before` ブロック) は「移行前の過去記録」なので**触らない**（add-only 原則）。

## 4. プロジェクト CLAUDE.md の改訂

L52-L57 の version folder 構成リストに 1 行追加:

```diff
 各バージョンフォルダ `docs/{category}/ver{X.Y}/` の構成:
 - `ROUGH_PLAN.md` — タスク概要
+- `PLAN_HANDOFF.md` — 選定理由・除外理由・後続 step への注意点（handoff 情報ゼロなら省略可）
 - `REFACTOR.md` — リファクタリング計画
 - `IMPLEMENT.md` — 実装計画
 - `MEMO.md` — 実装メモ・残課題
 - `CURRENT.md` — **メジャーバージョンのみ**: コード現況の完全版（CLAUDE.md と重複しない内容のみ）
 - `CHANGES.md` — **マイナーバージョンのみ**: 前バージョンからの変更差分
```

`.claude/CLAUDE.md` は「`ROLE.md` への参照のみ」のため**触らない**（ROLE.md にもバージョン管理規則の記述はない）。

## 5. ver15.3 自身の `PLAN_HANDOFF.md`（自己適用 / 選択肢 A）

`docs/util/ver15.3/PLAN_HANDOFF.md` を新規作成する。frontmatter は `workflow: full` / `source: master_plan`（ROUGH_PLAN.md と同値）。本文は `ROUGH_PLAN.md` から以下の情報を抽出して再構成する:

- `## ISSUE レビュー結果` ← ROUGH_PLAN.md L10-L12 を転記
- `## ISSUE 状態サマリ` ← ROUGH_PLAN.md L14-L28 を転記
- `## 選定理由・除外理由` ← ROUGH_PLAN.md L29-L50（選定結果・選定理由・除外理由）を転記
- `## 関連 ISSUE / 関連ファイル / 前提条件` ← ROUGH_PLAN.md L135-L146（関連 ISSUE / ドキュメント）を転記、+ 影響範囲の先出し table (L120-L133) を要約して追加
- `## 後続 step への注意点` ← ROUGH_PLAN.md L171-L184（後続 `/split_plan` への引き継ぎメモ）を転記

**重要**: ROUGH_PLAN.md 自体は**一切改変しない**（add-only）。PLAN_HANDOFF.md は「これらの情報を今後どこに書くか」の試金石として独立に存在する。本バージョン RETROSPECTIVE.md §3 で「新仕分け方針の自己適用が機能したか」を評価する材料になる。

## 6. PHASE7.1.md 進捗表の更新

`docs/util/MASTER_PLAN/PHASE7.1.md` L11 の §3 行を更新:

```diff
-| §3 | `ROUGH_PLAN.md` と `PLAN_HANDOFF.md` の役割分離 | 未着手 | ver15.1 |
+| §3 | `ROUGH_PLAN.md` と `PLAN_HANDOFF.md` の役割分離 | 実装済み（ver15.3） | ver15.1 |
```

「想定バージョン」列の `ver15.1` は**据え置き**（当初想定の記録として残す。実際のバージョンは「状態」列で示す）。

※ この更新は `/wrap_up` または `/write_current` 段階で行う（本 IMPLEMENT の §7 タイムライン参照）。

## 7. 実装タイムライン（/imple_plan 以降で回す順序）

| step | 対象 | 内容 | コミット |
|---|---|---|---|
| 7-1 | `.claude_sync/` export | `python scripts/claude_sync.py export` | なし |
| 7-2 | SKILL 3 本 + meta_judge + retrospective 改訂 | §2.1〜§2.5 を `.claude_sync/` 配下で編集 | なし |
| 7-3 | `.claude_sync/` import | `python scripts/claude_sync.py import` | なし |
| 7-4 | `.claude/plans/VERSION_FLOW.md` 改訂 | §3 の 1 行追加（`claude_sync.py` は `.claude/` 全体を `shutil.copytree` で同期するため `.claude/plans/` も 7-2 と同じ export → edit → import で一括処理可能） | なし |
| 7-5 | `CLAUDE.md` (project root) 改訂 | §4 の 1 行追加 | なし |
| 7-6 | `docs/util/ver15.3/PLAN_HANDOFF.md` 新規作成 | §5 の自己適用 | なし |
| 7-7 | コミット 1 発目 | 7-2〜7-6 を 1 コミットで `feat(ver15.3): PLAN_HANDOFF.md 導入と SKILL 本文の責務分割` | ✅ |
| 7-8 | `docs/util/MASTER_PLAN/PHASE7.1.md` 進捗更新 | §6（`/wrap_up` で実施） | /wrap_up コミットに含める |

**コミット境界の判断**: ROUGH_PLAN.md 後続引き継ぎメモでは「SKILL 本文改訂コミットと PLAN_HANDOFF.md 作成コミットを分離するかを /imple_plan で判断」とあった。本 IMPLEMENT では **1 コミットに束ねる** を推奨する。理由:

1. SKILL 本文改訂のみ先行すると、「新ルールを定義したが最初のサンプル PLAN_HANDOFF.md がない」状態が一時的に git 履歴に残り、revert が難しくなる
2. PLAN_HANDOFF.md の自己適用サンプルを同時に入れることで、review 時に「ルールとサンプルが一致しているか」を 1 つのコミットで検証できる
3. 変更行数は合計 200 行程度と見積もり、単一論理変更として十分追える粒度

`/wrap_up` で PHASE7.1.md 進捗更新が発生する場合、それは本コミットとは別にしてよい（`/wrap_up` が別 step として走るため自然に分離される）。

## 8. テスト方針

### 8.1 既存テストへの影響

`scripts/tests/test_claude_loop_*.py` の `ROUGH_PLAN.md` 参照箇所（全 10 箇所、§0 確認済）はすべて `workflow:` frontmatter 検出の文脈で、`PLAN_HANDOFF.md` の有無に依存しない。**新規テスト追加は不要**。pytest 全 252 件グリーンの維持を `/imple_plan` step 末尾で確認する。

### 8.2 SKILL 本文の静的検査

`scripts/tests/` 配下に SKILL の内容を静的検査するテストは**存在しない**（`Grep "SKILL\.md" scripts/tests/` 結果で確認済）。SKILL 本文改訂は CI で機械的に検出される対象外のため、テスト期待値の更新は発生しない。

### 8.3 validation.py への追加チェック（結論: 本バージョンでは追加しない）

ROUGH_PLAN.md §後続引き継ぎメモ §仕分け方針の機械検証で保留されていた「`PLAN_HANDOFF.md` 存在検証を validation.py に追加するか」の判断:

**結論: 本 ver15.3 では追加しない**。理由:
- ROUGH_PLAN.md §1.2 / §1.3 で quick / full とも「handoff 情報ゼロなら省略可」という抜け道を定義したため、「存在必須」の静的チェックは早期に入れると false negative が出る（PLAN_HANDOFF.md が**正当に**省略されたケースを壊す）
- `validate_startup()` は YAML / CWD / カテゴリ整合の保証が主責務であり、docs 配下の成果物検証は責務が異なる（関心の分離）
- 運用を 1〜2 バージョン回し、省略ケースの頻度・誤省略の発生率を観察してから動的チェックを設計するのが安全

ver15.4 以降で「省略判断がぶれる」「PLAN_HANDOFF.md を書き忘れて後続 step が情報不足」が観察された場合、`ISSUES/util/medium/plan-handoff-validation-followup.md` を起票して別バージョンで扱う。本バージョンでは **RETROSPECTIVE.md に観察ポイントとして記録**する。

### 8.4 手動動作確認

`/imple_plan` 実行後に以下を手動確認:

1. `cat docs/util/ver15.3/PLAN_HANDOFF.md` で §5 の 5 節が揃っているか
2. `grep -r "PLAN_HANDOFF" .claude/skills/ .claude/plans/ CLAUDE.md` で追記が各ファイルに反映されているか
3. `python scripts/claude_sync.py export` を再実行し、`.claude_sync/` と `.claude/` に差分がゼロであること（import 忘れ防止）
4. `pnpm test` / `pytest scripts/tests/ -q` いずれもグリーン

## 9. リスク・不確実性

本バージョンは新規ライブラリ・未使用 API を扱わないため型定義・ドキュメント不足由来のリスクは小さいが、「新運用フォーマットの初回導入」特有のリスクを列挙する。

| リスク | 影響度 | 対策 |
|---|---|---|
| SKILL 本文改訂後、次回 `/issue_plan` が PLAN_HANDOFF.md 生成を忘れる | 中 | §2.1 で `issue_plan/SKILL.md` のコミット節本文にも `PLAN_HANDOFF.md` を明示列挙。ver15.4 `/issue_plan` 実行時に ROUGH_PLAN.md だけでなく PLAN_HANDOFF.md も生成されるかを実地確認（RETRO §3 で評価） |
| quick 版の最小粒度が曖昧で毎回違う構造の PLAN_HANDOFF.md が生まれる | 中 | §1.3 で quick 版必須 2 節を明示。さらに `issue_plan/SKILL.md` に記載粒度 table を転載（single source of truth は SKILL 本文側） |
| frontmatter の `workflow:` / `source:` が ROUGH_PLAN.md と PLAN_HANDOFF.md で乖離する | 低 | 本バージョンでは目視確認のみ（drift-guard テストは ver15.2 で導入した `RESERVED_WORKFLOW_VALUES` / `resolve_workflow_value` 同期テストが間接的に機能）。ver15.4 以降で頻発したら validation.py に軽量チェック追加を検討（§8.3 の観察メモ経路） |
| 既存テスト 252 件中、SKILL 本文の文字列を直接参照するテストが存在し、文言変更でfail する | 低 | §8.1 で確認済み（ROUGH_PLAN.md 文字列参照は全て workflow frontmatter 文脈で、SKILL 本文の文言には依存しない）。`/imple_plan` 末尾で pytest 実行により最終確認 |
| 過去 docs (ver15.0〜ver15.2) の ROUGH_PLAN.md を遡及改変したくなる誘惑（例: 「ver15.2 ROUGH_PLAN.md に PLAN_HANDOFF 的な節があるので移す」など） | 中 | ROUGH_PLAN.md §実施しない で明示的に禁止。IMPLEMENT 本書でも §5 冒頭で「add-only」を明記。ver15.3 ROUGH_PLAN.md 自体も改変しない（§5 重要注記） |
| `PLAN_HANDOFF.md` が quick で冗長に感じられ、運用者が省略乱発する | 中 | §1.3 / §2.1 で「省略時は ROUGH_PLAN.md 末尾に 1 行記録」を必須化。省略頻度は RETRO §3 で計測 |
| `.claude/` 編集の `claude_sync.py` 往復で import 忘れが発生 | 低 | §8.4 手動確認 (3) で post-import 差分ゼロを確認 |

## 10. スコープ外（本 IMPLEMENT では触らない）

ROUGH_PLAN.md §実施しない を踏襲。特に以下を再掲:

- PHASE7.1 §4（run 単位通知） — ver15.4 以降
- 過去 ROUGH_PLAN.md（ver15.0 / ver15.1 / ver15.2）の遡及フォーマット統一
- 本 ver15.3 ROUGH_PLAN.md の分離書き直し（自己適用は「別ファイル PLAN_HANDOFF.md の新規作成」のみ）
- `questions.py` / `issues.py` 共通基盤化
- workflow YAML の model / effort 調整
- 既存 `auto` / `full` / `quick` / `scout` / `question` workflow の runtime 挙動変更
- `scripts/README.md` / `scripts/USAGE.md` の改訂（§0 で確認した通り workflow frontmatter 文脈の ROUGH_PLAN.md 参照のみで、PLAN_HANDOFF.md 追加に伴う記述変更は不要）
- `validate_startup()` への PLAN_HANDOFF.md 存在チェック追加（§8.3 の結論で先送り）
- `QUESTIONS/README.md` / `ISSUES/README.md` の改訂（両 queue は PLAN_HANDOFF.md を読まないため）
