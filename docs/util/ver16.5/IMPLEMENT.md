---
workflow: full
source: issues
---

# ver16.5 IMPLEMENT — `issue_review` SKILL に `ready/ai` 長期持ち越し再判定ルートを追加

## §0. 設計判断（IMPLEMENT で確定する論点）

PLAN_HANDOFF §「`/imple_plan` への注意」§1〜§5 で示された 5 論点を本節で確定する。後続 `/imple_impl` は本節を改めて開かず、§A〜§D の編集仕様に直接従ってよい（`/imple_plan` step は §0 / §A〜§D を主参照、§F リスク節は実装中の判断材料として参照）。

### 論点 1: 「N バージョン以上前」の測定指標

**採用: `reviewed_at` 日付差分方式（PLAN_HANDOFF §1 第一候補）。**

- 既定指標: `reviewed_at` フィールド（ISO `YYYY-MM-DD` 文字列）と本日日付の差分（**日数**）
- 採用根拠:
  - 追加 frontmatter フィールドが不要で、既存 ISSUE すべてに即適用可能（第二候補 `carryover_count` は侵襲的なため不採用）
  - SKILL.md 内の自然言語手順だけで完結し、scripts/ 側のロジック追加が不要（PLAN_HANDOFF §「前提条件」と整合）
  - LLM が日付差分を計算する処理は単純で、`/issue_plan` 実行時の `今日の日付` コンテキスト（既に SKILL.md に存在）と組み合わせて確定的に判定できる
- 不採用となった候補:
  - **第二候補（`carryover_count` 追加）**: frontmatter 書き換えを発生させない制約に反する（PLAN_HANDOFF §3）
  - **第三候補（git log 初出日）**: SKILL.md 内で `git log --diff-filter=A --follow --format=%aI -- <path> | tail -1` を LLM に実行させる手順は不確実性が高い（リネーム履歴・空白挙動）。また「ファイル年齢」と「ready/ai 滞留時間」は別概念
- **`reviewed_at` の意味論ガード**（SKILL.md §1 に明示する）:
  - `reviewed_at` は review フェーズが走った日に更新される。`ready/ai` に昇格後は `issue_review` の対象外となるため、再昇格しない限り日付は固定される
  - したがって「`reviewed_at` が古い」=「直近の review 以来 N 日 `ready/ai` で停滞している」と読める（厳密には「ファイル全体の最終 review 日からの日数」）
  - 一度 `need_human_action` → `review/ai` に戻して再昇格すると `reviewed_at` がリフレッシュされ、本ルートからは外れる（=「人間 / AI が積極的に再判断した」シグナルと見なし、カウンタリセット相当として扱う仕様）
  - `reviewed_at` 欠落 ISSUE の扱い: 「未判定」として本ルートの対象外（false positive 防止）。SKILL.md §1 にこの除外条件を明示する

### 論点 2: しきい値 N の既定値

**採用: `7 日`。**

- 換算根拠: ver14〜ver16 の version bump 実績で 1 minor ≒ 1〜2 日サイクル、5 バージョン ≒ 5〜10 日。中央値の 7 日を取る
- ISSUE 本文 §2 の「5 バージョン」推奨と整合する
- SKILL.md §1 では「閾値は環境に応じて調整可能」と注記し、定数を 1 箇所（§1 内）に集約する（マジックナンバー散逸を防ぐ）
- **既知の限界**: 本ルート初導入時の本日（2026-04-25）時点では、util カテゴリ ready/ai 4 件中、`reviewed_at` が 7 日以上前のものは 0 件（最古でも 2026-04-23、2 日前）。これは正常で、`/retrospective` での「初回実装が動作確認できる前提」を支えるものではない（=「再判定推奨欄が空 = ルート未発火」と「ルート未実装 = 出力に欄なし」の区別が retrospective 側で必要。詳細は §C で扱う）

### 論点 3: frontmatter 書き換えを発生させない制約の表現

**採用: SKILL.md §1 と §5 双方で明示し、§3 書き換えガードに第 4 項目を追加。**

- §1: スキャン対象に追加するブロックの末尾に「**注: 本ルートで検出した ISSUE の frontmatter は一切書き換えない。サマリ報告（§5）への追記のみ。**」を 1 文挿入
- §5: 「再判定推奨」第 3 ブロック書式の冒頭に「frontmatter 未変更、判断は人間 / AI に委ねる」の注記を含める
- §3: 既存の 5 項目に「**長期持ち越し ISSUE の frontmatter は書き換えない**（§5 の第 3 ブロックに列挙のみ）」を 1 項目追加
- これにより「scan 対象として検出する」≠「書き換える」が SKILL.md 全体で一貫する

### 論点 4: サマリ書式の第 3 ブロック

**採用: 以下書式を SKILL.md §5 末尾に追加。**

```markdown
## 再判定推奨 ISSUE

長期持ち越し閾値（既定 7 日）を超えた `ready/ai` ISSUE。frontmatter 未変更、判断は人間 / AI に委ねる:

- `{path}` — reviewed_at: {YYYY-MM-DD}（{N} 日経過）
  - 候補理由 A: 実機検証が必要 → `need_human_action / human` に降格を検討
  - 候補理由 B: 前提条件待ち（他カテゴリでの review/ai 発生待ち等）→ `ready/ai` のまま `## AI からの依頼` に補足追記を検討
```

- 該当 0 件の場合は「該当なし（`ready/ai` で {N} 日以上停滞している ISSUE はない）」の 1 行で済ませる
- 配置: 既存「## ISSUE 状態サマリ」の直後（つまり §5 全体は 3 ブロック構成になる）
- 候補理由 A / B はテンプレート固定文。判別自動化は行わず、人間 / AI が選ぶ前提

### 論点 5: 持ち越し理由の候補テンプレート

**採用: 上記論点 4 の書式に「候補理由 A」「候補理由 B」として常備する 2 行のみ。**

- ISSUE 本文 §3 判定ルートの 2 系統に対応:
  - A 系（実機検証要） → 降格候補
  - B 系（AI 作業で消化可能だが前提待ち） → 維持候補
- 3 つ目以降の候補は判別が難しいため、本版では追加しない（後続版での観察結果次第で拡張）
- LLM が ISSUE 本文を一読して A/B のどちらが妥当か "推測" する手順は本版でやらない（PLAN_HANDOFF §「`/imple_plan`」§5 の方針: 「判別自動化は本版でやらない」を尊重）

## §A. `.claude/skills/issue_review/SKILL.md` の編集

### 既存ファイル確認結果

`.claude/skills/issue_review/SKILL.md` 全 100 行（読込済）。§1 スキャン / §2 個別レビュー / §3 書き換えガード / §4 `## AI からの依頼` 書式 / §5 サマリ報告 の 5 節構成。本版の追補は §1 / §3 / §5 と冒頭 description の計 4 箇所。

### A-1. 冒頭 description の調整

**変更前**（L3）:
```yaml
description: plan ステップの冒頭で ISSUES/{カテゴリ}/ の review/ai 課題を走査し、ready/ai または need_human_action/human に振り分ける
```

**変更後**:
```yaml
description: plan ステップの冒頭で ISSUES/{カテゴリ}/ の review/ai 課題を振り分け、ready/ai 長期持ち越し ISSUE を再判定推奨として一覧する
```

### A-2. §1 スキャンへの追補

**追補位置**: §1 スキャン節末尾（既存 4 分類リストの直後、§2 個別レビュー見出しの直前）。

**追補ブロック**:

```markdown
### 1.5. 長期持ち越し ready/ai の検出（追加スキャン）

§1 と並行して、`status: ready` かつ `assigned: ai` のファイルも走査し、以下条件を満たすものを「再判定推奨」として §5 第 3 ブロックに列挙する:

- `reviewed_at` フィールドが存在し、かつ本日日付との差分が **7 日以上**
- `reviewed_at` 欠落 ISSUE は対象外（未判定として除外）
- 閾値 7 日は SKILL 内の既定値。運用観察で過敏 / 過鈍と判断された場合のみ後続版で調整

**注: 本ルートで検出した ISSUE の frontmatter は一切書き換えない。サマリ報告（§5 第 3 ブロック）への追記のみ。**

`reviewed_at` の意味論補足:
- `reviewed_at` は §2 個別レビュー時に更新される。`ready/ai` に昇格後は §1 の「review/ai 検出」対象から外れるため、再度 `review/ai` に戻して再判定するまで `reviewed_at` は固定される
- したがって「`reviewed_at` が 7 日以上前」=「直近 7 日間、`ready/ai` で誰も再判断していない」と読める
- 持ち越し ISSUE を再判断したい場合は人間 / AI が `ready/ai` → `review/ai` に戻し（または `need_human_action` に降格し）、次回 `/issue_plan` で再評価させる運用となる
```

### A-3. §3 書き換えガードへの追補

**追補位置**: §3 既存 5 項目の末尾。

**追補項目**:

```markdown
- **長期持ち越し ISSUE の frontmatter は書き換えない**: §1.5 で検出した `ready/ai` 長期持ち越し ISSUE は、§5 第 3 ブロックに列挙するのみで `status` / `assigned` / `reviewed_at` の書き換えを発生させない。降格 / 再判定の最終操作は人間 / AI の手動判断に委ねる
```

### A-4. §5 サマリ報告への追補

**追補位置**: SKILL.md §5 内の既存 markdown サンプルブロック（` ``` ` 閉じ記号、現行 L89）の直後、L91 の説明文（`分布は python scripts/issue_status.py {カテゴリ} の出力を基にするか...`）の直前に挿入する。挿入後の §5 は「[既存サンプル `## ISSUE レビュー結果` + `## ISSUE 状態サマリ`] → [新規サンプル `## 再判定推奨 ISSUE`] → [既存説明文 `分布は...`]」の順序になる。

**追補ブロック**（外側を 4 連バッククォートで囲み、内側の 3 連バッククォート markdown サンプルがそのまま展開される形で SKILL.md に書く）:

````markdown
plan 本文末尾に以下の第 3 ブロックを追加する:

```markdown
## 再判定推奨 ISSUE

長期持ち越し閾値（既定 7 日）を超えた `ready/ai` ISSUE。frontmatter 未変更、判断は人間 / AI に委ねる:

- `{path}` — reviewed_at: {YYYY-MM-DD}（{N} 日経過）
  - 候補理由 A: 実機検証が必要 → `need_human_action / human` に降格を検討
  - 候補理由 B: 前提条件待ち（他カテゴリでの review/ai 発生待ち等）→ `ready/ai` のまま `## AI からの依頼` に補足追記を検討
```

該当ゼロの場合は以下 1 行で済ませる:

```markdown
## 再判定推奨 ISSUE

該当なし（`ready/ai` で 7 日以上停滞している ISSUE はない）。
```

候補理由 A / B はテンプレート固定文。判別自動化は本 SKILL では行わず、最終判断は人間 / `/issue_plan` 側の LLM に委ねる。
````

### A-5. 編集後の §節構成

| 節 | 既存 | 本版で変更 |
|---|---|---|
| §1 スキャン | 4 分類リスト | §1.5 追加（長期持ち越し検出） |
| §2 個別レビュー | 表 + reviewed_at 規則 | 変更なし |
| §3 書き換えガード | 5 項目 | 第 6 項目追加 |
| §4 `## AI からの依頼` 書式 | テンプレート | 変更なし |
| §5 サマリ報告 | 2 ブロック | 第 3 ブロック追加 |

## §B. `.claude/skills/issue_plan/SKILL.md` の編集

### 既存ファイル確認結果

`.claude/skills/issue_plan/SKILL.md`（読込済）。本版で触る箇所は「準備」節 L39 の ISSUE レビューフェーズ手順のみ。

### B-1. ISSUE レビューフェーズ手順の同期追補

**変更前**（L39 該当行、ISSUE レビューフェーズの説明文）:
```markdown
- **ISSUE レビューフェーズ**: `ISSUES/{カテゴリ}/{high,medium,low}/*.md` を走査し、`status: review` かつ `assigned: ai` の ISSUE を 1 件ずつ Read → 判定 → frontmatter を `ready / ai` または `need_human_action / human` に書き換える。判定基準・書き換え手順・`## AI からの依頼` 追記の書式は `.claude/skills/issue_review/SKILL.md` を一次資料とする。レビュー結果サマリ（遷移件数・対象パス）と状態分布（`status × assigned` の 5 区分）を ROUGH_PLAN 本文冒頭に `## ISSUE レビュー結果` / `## ISSUE 状態サマリ` の見出しで残す
```

**変更後**:
```markdown
- **ISSUE レビューフェーズ**: `ISSUES/{カテゴリ}/{high,medium,low}/*.md` を走査し、(a) `status: review` かつ `assigned: ai` の ISSUE を 1 件ずつ Read → 判定 → frontmatter を `ready / ai` または `need_human_action / human` に書き換える、(b) `status: ready` かつ `assigned: ai` のうち `reviewed_at` が 7 日以上前の ISSUE を「再判定推奨」として検出する（frontmatter 書き換えなし）。判定基準・書き換え手順・`## AI からの依頼` 追記の書式・長期持ち越し検出ルールは `.claude/skills/issue_review/SKILL.md` を一次資料とする。レビュー結果サマリ・状態分布・再判定推奨 ISSUE 一覧の 3 ブロックを ROUGH_PLAN 本文冒頭に `## ISSUE レビュー結果` / `## ISSUE 状態サマリ` / `## 再判定推奨 ISSUE` の見出しで残す
```

### B-2. ROUGH_PLAN.md 内サマリの同期

`/issue_plan` SKILL は ROUGH_PLAN.md 冒頭にサマリブロックを残す。本版以降、`/issue_plan` 実行時には第 3 ブロック「## 再判定推奨 ISSUE」も必ず ROUGH_PLAN.md に出力する（該当 0 件でも見出しと「該当なし」1 行は残す）。書式は §A-4 と同一。

## §C. `ISSUES/README.md` の編集

### 既存ファイル確認結果

`ISSUES/README.md`（読込済、170 行）。§ライフサイクル（L67〜97）に「人間が起票するパス」「AI が起票するパス」の 2 サブセクションがある。本版は同節に「長期持ち越し再判定」サブセクションを 1 つ追加。

### C-1. 長期持ち越し再判定サブセクション追加

**追補位置**: §ライフサイクル節の末尾（「`issue_scout`（`--workflow scout`）による能動起票の既定値」サブセクションの直後、§人間への依頼セクションの直前）。

**追補ブロック**:

```markdown
### 長期持ち越し再判定（ver16.5 追加）

`status: ready / ai` のまま長期間（既定 7 日）着手されない ISSUE を `issue_review` SKILL が「再判定推奨」として検出します。検出条件と挙動:

- 検出条件: `reviewed_at` フィールドが本日から 7 日以上前
- 検出時の挙動: `/issue_plan` の出力に「## 再判定推奨 ISSUE」ブロックが追加される。frontmatter は書き換えられない
- 想定される人間 / AI の対応:
  - 実機検証が必要なものは手動で `need_human_action / human` に降格する
  - 前提条件待ち（他カテゴリでの `review/ai` 発生待ち等）のものは `ready/ai` を維持しつつ `## AI からの依頼` に補足を追記する
  - 状況が変わって再判断したい場合は手動で `review/ai` に戻し、次回 `/issue_plan` で再評価させる
- 詳細仕様は `.claude/skills/issue_review/SKILL.md` §1.5 / §5 を参照
```

## §D. ISSUE 消化処理（最終操作）

### D-1. ISSUE ファイルの `done/` 移動

**対象**: `ISSUES/util/low/issue-review-long-carryover-redemotion.md`

**操作**: `git mv ISSUES/util/low/issue-review-long-carryover-redemotion.md ISSUES/util/low/done/issue-review-long-carryover-redemotion.md`

**前提**: `ISSUES/util/low/done/` ディレクトリの存在を確認（無ければ `mkdir` で作成、`.gitkeep` 設置の慣行があるか他カテゴリの done/ 構成を参照）。

**timing**: SKILL.md / README.md 編集が完了し、それらのコミットが入った後、最終ステップとして実施。

## §E. 編集フロー（`.claude/` 編集の手順）

`.claude/` 配下のファイルは CLI `-p` モードで直接編集できないため、以下の手順を厳守する（`.claude/rules/claude_edit.md` 規約）:

```bash
# 1. export
python scripts/claude_sync.py export

# 2. 編集（.claude_sync/ 配下の以下 2 ファイル）
#    - .claude_sync/skills/issue_review/SKILL.md
#    - .claude_sync/skills/issue_plan/SKILL.md

# 3. import
python scripts/claude_sync.py import
```

`ISSUES/README.md` は `.claude/` 配下ではないため、通常の Edit ツールで直接編集してよい。

### CRLF / LF 整合性

`scripts/claude_sync.py` は改行コードを保持して往復する想定だが、Windows 環境では CRLF と LF の混在に注意（`issue_review` SKILL §3 が「Read → Edit の old_string で改行を完全一致させる」を要求しているのと同じ理由）。import 後に `git diff` で予期しない改行差分が出ていないか確認すること。

## §F. リスク・不確実性

`workflow: full` だが新規ライブラリ・未使用 API は扱わない。リスクは仕様 / 運用設計レベルに集中する。

### F-1. `reviewed_at` 7 日閾値の妥当性

- **何を**: 閾値 7 日が「長期持ち越し」の意味として過敏 / 過鈍でないか
- **どのソースで**: `/retrospective` 時点での util カテゴリ ready/ai 4 件の `reviewed_at` 分布を再確認
- **どう確認するか**: 本日（2026-04-25）時点では 4 件すべて 7 日以内（最古 2026-04-23）。本版実装後の `/issue_plan` で「該当なし」が出力されることを RETROSPECTIVE で確認し、後続版（ver16.6+）の経過観察期間（1〜2 版）を経て初発火を待つ。初発火が 1 版以内に発生しない場合（ありえる）、閾値を 5 日に下げる調整を後続版 ISSUE として起票する

### F-2. `reviewed_at` 欠落 ISSUE の取り扱い

- **何を**: `reviewed_at` 欠落 ISSUE を「対象外（未判定）」と扱う設計の妥当性
- **どのソースで**: 現行 `ISSUES/util/` 配下の ready/ai 4 件すべてに `reviewed_at` が付いていることは確認済（PLAN_HANDOFF §ISSUE 状態サマリ表）
- **どう確認するか**: 本版では「対象外」で確定。`reviewed_at` 欠落かつ ready/ai が将来発生した場合は別 ISSUE として警告すべきか、後続版で観察判断（false positive 防止優先で本版は除外）

### F-3. SKILL.md 内の自然言語ロジックを LLM が確実に実行できるか

- **何を**: 「reviewed_at と本日日付の差分計算」を LLM が確定的に実行するか
- **どのソースで**: `/issue_plan` SKILL コンテキスト L11「今日の日付: !`date +%Y-%m-%d`」相当の絶対日付が `issue_review` SKILL にも既にある（L17）
- **どう確認するか**: 本版実装後の最初の `/issue_plan` run（=本版の `/retrospective` step に先行する次版の `/issue_plan`）で、ROUGH_PLAN.md に「## 再判定推奨 ISSUE」ブロックが正しい書式で出力されているかを目視確認。出力されていない / 書式が崩れた場合は SKILL.md §5 の例示を増やすか、scripts/ 側の補助スクリプトを後続版で起票

### F-4. `claude_sync.py` 往復での意図せぬ差分

- **何を**: export → 編集 → import の往復で SKILL.md の他箇所に意図しない差分が出るか
- **どのソースで**: `git diff .claude/` の出力
- **どう確認するか**: import 後に必ず `git diff .claude/skills/issue_review/SKILL.md` と `git diff .claude/skills/issue_plan/SKILL.md` を確認し、本版で意図した変更箇所のみが diff に出ていることを検証する。意図せぬ差分（改行・末尾空白）が出た場合は手動で revert

### F-5. ISSUE 本文の §AI からの依頼セクション扱い

- **何を**: 消化対象 `issue-review-long-carryover-redemotion.md` を `done/` 移動する際、本文末尾の「## AI からの依頼（ver16.3 RETROSPECTIVE 追記）」セクションを残したまま移動するか削除するか
- **どのソースで**: 他 done/ ISSUE の慣行を `ISSUES/{カテゴリ}/{priority}/done/` 配下で確認
- **どう確認するか**: 既存の done/ 配下サンプル ISSUE を読み、AI からの依頼セクションが残されているのが慣行ならそのまま、削除されているなら本版でも削除する。**timing**: `/imple_impl` step 開始時に done/ 慣行を確認し、§D-1 の git mv 直前に方針を確定する

## §G. 成果物サマリ

本 `/split_plan` step で追加される成果物:

- `docs/util/ver16.5/IMPLEMENT.md` — 本ファイル

後続 step で生成 / 編集される成果物（参考）:

- `.claude/skills/issue_review/SKILL.md` — §A の編集（後続 `/imple_plan` / `/imple_impl`）
- `.claude/skills/issue_plan/SKILL.md` — §B の編集（同上）
- `ISSUES/README.md` — §C の編集（同上）
- `ISSUES/util/low/done/issue-review-long-carryover-redemotion.md` — §D の git mv（最終 step）
- `docs/util/ver16.5/MEMO.md` — 実装メモ
- `docs/util/ver16.5/CHANGES.md` — 前版（ver16.4）からの変更差分
- `docs/util/ver16.5/RETROSPECTIVE.md` — `/retrospective` step が初回出力（本版主眼の動作確認 = §F-1 / F-3 含む）

REFACTOR.md は作成しない（ROUGH_PLAN.md §事前リファクタリング要否で「不要」と確定済）。

## §H. やらないこと（再掲、ROUGH_PLAN §やらないこと と整合）

- 10 バージョン強制降格ルールの実装（後続 ver16.6+）
- `carryover_count` 等の新 frontmatter フィールド追加
- 持ち越し理由の自動判別（A/B のどちらに該当するかの推測）
- Python スクリプト新設 / 既存スクリプト改修（`scripts/issue_worklist.py` / `scripts/issue_status.py` / `claude_loop_lib/issues.py` への変更なし）
- 他カテゴリ（app / infra / cicd）での発火観察（仕様変更は全カテゴリ横断で有効化されるが、観察は handoff 委ね）
- 他 3 件の ready/ai ISSUE の個別消化
- PHASE9.0 骨子作成
- ver16.4 RETROSPECTIVE 相当のループ観察課題（後続版 / 自然採取に委ねる、ROUGH_PLAN §やらないこと L78〜83 と整合）:
  - ver16.3 §3.5 A-4（deferred 3 kind 分離）の実機観察 → 次 deferred 発火 run で継続
  - `imple_plan` / `experiment_test` の effort 下げ判断 → sample 蓄積待ち
  - ver16.2 EXPERIMENT.md 「未検証」マーク解除 → 次 research workflow 採用時
  - `extract_model_name` 修正の sidecar 反映確認 → 次 full / quick run の `*.costs.json` で自然採取
