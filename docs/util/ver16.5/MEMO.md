---
workflow: full
source: issues
---

# ver16.5 MEMO — 実装メモ

## 実施内容サマリ

IMPLEMENT.md §A〜§D の全編集を反映した。

- §A `.claude/skills/issue_review/SKILL.md`
  - A-1 description 文字列を再判定推奨ルート言及に更新
  - A-2 §1 末尾に §1.5「長期持ち越し ready/ai の検出」ブロックを追加
  - A-3 §3 書き換えガードに第 6 項目「長期持ち越し ISSUE の frontmatter は書き換えない」を追加
  - A-4 §5 サマリ報告に第 3 ブロック「## 再判定推奨 ISSUE」書式を 2 例（該当あり / 該当なし）＋補足注で追加
- §B `.claude/skills/issue_plan/SKILL.md`
  - B-1 「準備」節 ISSUE レビューフェーズ手順を (a)/(b) 2 系統に再構成し、ROUGH_PLAN 出力ブロック見出しを 3 本に拡張
- §C `ISSUES/README.md`
  - C-1 §ライフサイクル節末尾に「長期持ち越し再判定（ver16.5 追加）」サブセクションを追加
- §D `ISSUES/util/low/issue-review-long-carryover-redemotion.md` を `done/` へ `git mv`

## 計画との乖離

### D-1: A-4 の外側コードフェンス記法を 4 連 → 3 連に変更

IMPLEMENT.md §A-4 は「外側を 4 連バッククォートで囲む」と指示していたが、実際には内側の 3 連バッククォートサンプルと同一コード内に並ぶだけで**相互にネストしない**（「plan 本文末尾に以下の第 3 ブロックを追加する:」という説明文が独立したプロースとして表示される必要がある）。4 連で囲むと全体が 1 個の巨大な code block になり、説明文が rendered text として機能しなくなる。既存 §5 の第 1・第 2 ブロックも 3 連バッククォートで書かれているため、**記述スタイルの一貫性のため 3 連に揃えた**。意味論は変わらず、`## 再判定推奨 ISSUE` サンプルは正しく fenced code として展開される。

### D-2: §D-1 done/ 移動時の「## AI からの依頼」セクション扱い

IMPLEMENT.md §F-5 の判断時点ガイドに従い、`ISSUES/*/*/*/done/` 配下を grep したところ `## AI からの依頼` セクションを持つ done/ ISSUE は全カテゴリで 0 件（= 慣行として「残っている例が観測されない」が、過去の done/ 移動対象はそもそも `ready/ai` 経由が大半で当該セクション自体を持たなかった可能性が高く、慣行と呼べるほどのサンプルサイズではない）。情報損失を避ける方針で **本文セクションを削除せずそのまま移動**した（ver16.3 RETROSPECTIVE 追記という歴史的文脈があるため）。将来 done/ ISSUE の整理慣行が確立された場合は別 ISSUE で統一方針を検討する。

## リスク・不確実性の顛末（IMPLEMENT.md §F 対応）

### F-1: `reviewed_at` 7 日閾値の妥当性 — **検証先送り**

- 本日（2026-04-25）時点で util カテゴリ ready/ai 4 件の `reviewed_at` は全て 7 日以内（最古 2026-04-23、2 日前）。現時点で発火しないのは想定通りで、初回発火を観察するには 1〜2 版の経過が必要。
- 本版実装直後の `/retrospective` では「## 再判定推奨 ISSUE: 該当なし」が出るか書式確認のみ可能。
- **先送り対応方針**: 後続 2 版（ver16.6, ver16.7）で発火観察。発火がない場合、または過敏と感じられた場合は閾値調整 ISSUE を起票する。
- **本番発生時の兆候と対応**: 7 日経過 ISSUE が 0 件のまま 2 版以上経過 → 閾値を 5 日に下げる検討。逆にノイズが多い場合は 10〜14 日に上げる検討。
- ISSUES/util/low/ へ独立 ISSUE ファイル化: **不要**（「先送り」自体が本版の設計意図であり、IMPLEMENT.md §F-1 に明記されている時間差観察が計画通りの動線のため、別 ISSUE を立てると冗長）。

### F-2: `reviewed_at` 欠落 ISSUE の取り扱い — **検証済み（除外で確定）**

- 現行 util カテゴリ ready/ai 4 件すべてに `reviewed_at` が付いていることを PLAN_HANDOFF §ISSUE 状態サマリで確認済。他カテゴリ（app / infra / cicd）の ready/ai 件数が少ないため、false positive 防止優先の「除外」方針で本版確定。
- SKILL.md §1.5 に「`reviewed_at` 欠落 ISSUE は対象外（未判定として除外）」を明記済。

### F-3: SKILL.md 内の自然言語ロジックを LLM が確実に実行できるか — **検証先送り**

- 本版の `/imple_plan` step では `/issue_plan` を呼ばないため、実際に LLM が 7 日差分を計算して ROUGH_PLAN に「## 再判定推奨 ISSUE」ブロックを出力する挙動は次版 `/issue_plan` run で初めて観察可能。
- **先送り対応方針**: 次版 `/issue_plan` の ROUGH_PLAN.md に「## 再判定推奨 ISSUE」ブロックが正しい書式で出力されているかを目視確認。崩れた場合は SKILL.md §5 の例示を増やす or scripts/ 側の補助スクリプトを後続版で起票。
- **本番発生時の兆候と対応**: ROUGH_PLAN.md に見出しが出ない or 書式崩れ → SKILL.md §1.5 / §5 に「今日の日付との差分を Python で計算してから列挙する」旨の明示手順を追加し、計算例を inline で示す。
- ISSUES/util/low/ へ独立 ISSUE ファイル化: **不要**（次版 `/issue_plan` の自然実行で即座に挙動確認でき、先送り期間が 1 版 = 1〜2 日と短いため、専用 ISSUE を立てるコストが観察コストを上回る）。

### F-4: `claude_sync.py` 往復での意図せぬ差分 — **検証済み**

- import 後の `git diff --stat .claude/` で変更ファイルが意図した 2 ファイル（`skills/issue_review/SKILL.md` / `skills/issue_plan/SKILL.md`）のみ、かつ差分規模が事前見積（+40 / +2 行）と一致することを確認済。改行コード由来の意図せぬ差分は git の `LF will be replaced by CRLF` 警告のみで、実ファイルには差分を作っていない（warning は次回書き換え時の予告）。

### F-5: ISSUE 本文の §AI からの依頼セクション扱い — **検証済み（保持で確定）**

- 上記「計画との乖離 D-2」に記載。done/ 配下慣行が確立されていないため、情報損失を避ける保持方針で確定。

## 動作確認結果

- `npx nuxi typecheck`: exit 0（既知の vue-router volar 警告のみ。CLAUDE.md 記載通り実行に影響なし）
- `pnpm test`: 15 files / 145 tests 全 pass（既存テスト影響なし）
- ISSUE 消化: `git mv` 成功、`ISSUES/util/low/done/issue-review-long-carryover-redemotion.md` の存在確認済

## 残課題・後続版への引き継ぎ

- F-1 / F-3 の観察を後続 2 版（ver16.6, ver16.7）の `/issue_plan` / `/retrospective` で継続
- 他カテゴリ（app / infra / cicd）での再判定推奨ルート発火は自然観察に委ねる
- ROUGH_PLAN.md 第 3 ブロック（「## 再判定推奨 ISSUE」）の出力サンプル観察後、必要に応じて SKILL.md §5 の書式を調整

## ドキュメント更新提案

- なし（`CURRENT.md` は ver16.0 に存在するがマイナー版では更新しない規約。`CHANGES.md` は `/retrospective` step で生成される）

## wrap_up 対応結果

| 項目 | 対応 | 内容 |
|---|---|---|
| D-1 コードフェンス 4連→3連 | ⏭️ 対応不要 | 実装時に合理的判断で確定済、追加変更なし |
| D-2 done/ 移動時セクション保持 | ⏭️ 対応不要 | git mv 済、情報保持の判断は確定済 |
| F-1 閾値妥当性（先送り） | 📋 ISSUES 起票 | `ISSUES/util/low/issue-review-7day-threshold-observation.md` を起票 |
| F-2 `reviewed_at` 欠落扱い | ✅ 対応完了 | 実装時に検証・明記済 |
| F-3 LLM 日付計算確認（先送り） | 📋 ISSUES 起票 | `ISSUES/util/low/issue-review-llm-date-calc-observation.md` を起票 |
| F-4 claude_sync 往復差分 | ✅ 対応完了 | git diff で 2 ファイルのみ確認済 |
| F-5 AI からの依頼セクション扱い | ✅ 対応完了 | done/ 移動時に保持（D-2 と同一） |
| 残課題・ドキュメント更新 | ⏭️ 対応不要 | CHANGES.md は /retrospective step で生成。観察は後続版で継続 |
