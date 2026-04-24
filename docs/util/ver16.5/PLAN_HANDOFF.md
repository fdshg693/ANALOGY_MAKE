---
workflow: full
source: issues
---

# ver16.5 PLAN_HANDOFF — 後続 step 引き継ぎ

`full` workflow の PLAN_HANDOFF は必須 5 節で運用する。

## ISSUE レビュー結果

- ready/ai に遷移: 0
- need_human_action/human に遷移: 0
- 追記した `## AI からの依頼`: 0

本版 review フェーズでは対象ゼロ（util カテゴリに `status: review / ai` の ISSUE が 0 件）。書き換え操作は一切発生していない。`ISSUES/util/` 配下の frontmatter に対する diff は本 `/issue_plan` 実行時点で生じていない前提。

## ISSUE 状態サマリ

| status / assigned | 件数 | 内訳 |
|---|---|---|
| ready / ai | 4 | medium=2, low=2 |
| review / ai | 0 | — |
| need_human_action / human | 0 | — |
| raw / human | 0 | — |
| raw / ai | 2 | low=2（いずれも 2026-04-24 起票） |

出典: `python scripts/issue_status.py util`。ver16.4 closeout 時点から変動なし。

`ready / ai` 4 件の内訳と「長期持ち越し度合い」（本版が実装する再判定ルートの発火想定）:

| ISSUE パス | priority | 初出 version 推定 | reviewed_at | 長期持ち越し度合い |
|---|---|---|---|---|
| `ISSUES/util/medium/issue-review-rewrite-verification.md` | medium | ver6.0 | 2026-04-23 | 極大（ver6.0 以来 ~10 版） |
| `ISSUES/util/medium/deferred-resume-twice-verification.md` | medium | ver16.2 | 2026-04-24 | 小（3 版） |
| `ISSUES/util/low/issue-review-long-carryover-redemotion.md` | low | ver16.3 | 2026-04-25 | 極小（本版の主眼・消化対象） |
| `ISSUES/util/low/toast-persistence-verification.md` | low | ver15.4 | 2026-04-24 | 大（5 版前後） |

本表は IMPLEMENT.md で「N バージョン以上前」の N 既定値（5 を第一候補）を決める際の根拠資料として参照できる。

## 選定理由・除外理由

### 選定: `issue-review-long-carryover-redemotion`（本版主眼）

- ver16.4 MEMO §後続版引き継ぎ で「次 minor の主眼候補」と明示。ver16.4 ROUGH_PLAN §やらないこと §4 で「SKILL 本体書き換えを伴うため本版と並行せず将来版（ver16.5 以降）に委ねる」と明示されており、本版がその受け皿
- ISSUE 本文 §対応方針 で「初回実装は最小構成（スキャン対象拡張 + 5 バージョン『要再判定』警告のみ）」と既に推奨が書かれており、スコープ選択に迷いが生じない
- `## AI からの依頼（ver16.3 RETROSPECTIVE 追記）` で「昇格後の実装版で、最小構成から着手する案を推奨」と明示支持あり
- 本 ISSUE が解決する構造問題（`ready/ai` 長期持ち越しの検出欠如）は、他 3 件の ready/ai ISSUE を 2026-04-25 現在も留め置いている原因そのもの。消化すれば将来の issue_plan の精度が向上する meta 改善

### 除外: `issue-review-rewrite-verification`（medium, ver6.0 持ち越し）

- 着手条件が「他カテゴリ（app / infra）で `review / ai` の ISSUE が発生した `/split_plan` / `/quick_plan` の実走時に目視確認する」であり、util カテゴリ単独の AI self-consume では検証経路が成立しない
- 本版で主眼となる「長期持ち越し再判定ルート」実装後、当該 ISSUE は次回の review フェーズで「再判定推奨」フラグの第一号として自然に取り上げられる見込み。待機が妥当

### 除外: `deferred-resume-twice-verification`（medium, ver16.2 持ち越し）

- 着手には nested `claude -p` の実走測定が必要で、`experiments/deferred-execution/resume-twice/README.md` 草稿手順に従う隔離実測が前提
- 本 ISSUE を消化するなら `research` workflow 採用が筋であり、ver16.5 の `full`（SKILL 仕様追補）との同居に合理性がない
- ver16.3 §3.5 A-4（deferred 3 kind 分離）の実機観察待ちとも連動しており、次 deferred 発火 run 以降にまとめて扱うのが効率的

### 除外: `toast-persistence-verification`（low, ver15.4 持ち越し）

- ISSUE 本文 §人間追記 で「テスト用の薄いスクリプトを切り出して。そのスクリプトを実行して結果を私がここに記述します」と明示要求されており、**人間実機目視が本質的に必要**な性質。AI self-consume では完結しない
- 長期持ち越し再判定ルート実装後、「実機検証を要する → `need_human_action / human` に降格」の判別ルート §3 に該当する典型例となる。ただし本版では判別自動化を実装しないため、テンプレート提示に留まり実際の降格は人間判断を待つ
- 別版で「薄いスクリプト切り出し」タスクとして単独起票する案も handoff しておく（`toast-test-script-extraction` 等）

### 除外: `raw/ai` 2 件（`rules-paths-frontmatter-autoload-verification` / `scripts-readme-usage-boundary-clarification`）

- いずれも `status: raw` のため現行 `issue_review` SKILL のスキャン対象外（`review / ai` のみ）
- 本版で追加する「`ready/ai` 長期持ち越し再判定」ルートとも別軸（raw → review の昇格ルートは本版拡張の対象外）
- ISSUE 起票者（過去ループでの AI）が次段階遷移を決めかねている状態であり、本版では据え置き

### 除外: MASTER_PLAN PHASE9.0 骨子作成

- PHASE8.0 まで全フェーズ実装済だが、SKILL ガイドライン §MASTER_PLAN 全フェーズ完了時の判断 の優先順位①「既存 ISSUES の消化を優先」に該当（`ready/ai` が 4 件あり、かつ本版で消化する 1 件で区切りが良い）
- 加えて handoff（ver16.3 RETROSPECTIVE）で「PHASE9.0 骨子作成は時期尚早」と判定済

## 関連 ISSUE / 関連ファイル / 前提条件

### 選定 ISSUE

- `ISSUES/util/low/issue-review-long-carryover-redemotion.md` — 本版の単一主眼。ver16.3 起票、ver16.4 で `ready/ai` に昇格、本版で消化

### 修正対象ファイル（後続 step が触る範囲）

- `.claude/skills/issue_review/SKILL.md`
  - §1 スキャン: 対象条件に OR 追加（`ready/ai` かつ N バージョン以上持ち越し）
  - §5 サマリ報告: 「再判定推奨」第 3 ブロック書式を追加
  - 冒頭 `description` 文言の調整（走査対象が拡大する旨を反映）
- `.claude/skills/issue_plan/SKILL.md`
  - 「準備」節の ISSUE レビューフェーズ手順（`issue_review` SKILL インライン展開部）を同期
  - 「## ISSUE レビュー結果」「## ISSUE 状態サマリ」に加え第 3 ブロック「## 再判定推奨 ISSUE」をサマリ書式に追記
- `ISSUES/README.md`
  - ライフサイクル節に「長期持ち越し再判定」フロー 1 節を追加（メインの状態遷移図との整合を確認）

### 参考資料（読み直す価値あり）

- `ISSUES/util/low/issue-review-long-carryover-redemotion.md` — ISSUE 本文の設計提案 3 要素と §AI からの依頼を一次資料として参照
- `docs/util/ver16.3/RETROSPECTIVE.md` §A（本 ISSUE 起票に至った観察記録）
- `docs/util/ver16.4/MEMO.md` §後続版引き継ぎ（本版を「次 minor の主眼候補」と明示した handoff）
- `docs/util/ver16.4/PLAN_HANDOFF.md` §後続版引き継ぎ候補 #1（同上、繰り返し）
- `.claude/skills/issue_review/SKILL.md` 現行仕様（§1〜§5）
- `.claude/skills/issue_plan/SKILL.md` 「準備」節（インライン展開の現状形）

### 前提条件

- `.claude/` 配下の編集には `scripts/claude_sync.py` 経由（export → 編集 → import）が必要（`.claude/rules/claude_edit.md` 規約）。`/imple_impl` step はこの手順を前提に進めること
- 本版のスコープでは scripts 側（`scripts/issue_worklist.py` / `scripts/issue_status.py` / `claude_loop_lib/issues.py`）の Python コード変更は含めない。「N バージョン以上持ち越し」の判定ロジックは SKILL.md 内の自然言語手順で LLM に実行させる方式を想定（既存 `reviewed_at` 日付と本日日付の差分で判定）
- 既存 ready/ai 4 件中、本版で `done/` 移動するのは `issue-review-long-carryover-redemotion` のみ。他 3 件は ready/ai のまま据え置き

## 後続 step への注意点

### `/split_plan` への注意

1. **`full` 確定済**: ROUGH_PLAN frontmatter `workflow: full` / `source: issues` を尊重し、quick / research への再切替は行わない
2. **事前リファクタリング不要の判定根拠**: `issue_review` SKILL は §1〜§5 の節構成が既に追補に適した形（§1 スキャン・§5 サマリ報告の独立性が高い）で、追補対象が局所的。`issue_plan` SKILL 側のインライン展開箇所も現行で分離されているため、分割・統合を要する責務の集中はない。`REFACTOR.md` は「事前リファクタ不要」の結論のみで足りる見込み
3. **ISSUE 節立て**: 本版は単一 ISSUE 消化のため、`/imple_plan` で生成する IMPLEMENT.md の節は 1 本（主眼のみ）。サブタスク分割は SKILL 追補箇所ごと（§1 / §5 / plan SKILL 同期 / README 同期）で 4 サブステップ程度が妥当

### `/imple_plan` への注意

1. **「N バージョン以上前」の測定指標の確定が必須**: IMPLEMENT.md 内で以下 3 案のどれを採用するか記録する
   - 第一候補: `reviewed_at` 日付と本日日付の差分が M 日以上（M = 7 日前後で概ね 5 版相当と想定、実運用の version bump 頻度に依存）
   - 第二候補: 「同一ファイルが `/issue_plan` サマリに連続登場した回数」メタ情報を追加（frontmatter に `carryover_count` を追加）
   - 第三候補: ISSUE ファイルの git log から初出コミット日を取得し、本日日付との差分
   - 推奨は**第一候補**（追加 frontmatter なし・SKILL 内で完結・LLM が容易に判定可能）。ただし `reviewed_at` は review フェーズが走るたびに更新される仕様のため、ready/ai に昇格後は更新されないことを SKILL 側で明示する必要あり
2. **しきい値 N の既定値**: ISSUE 本文推奨は「5 バージョン」。`reviewed_at` 日付差分方式なら「7 日以上」を目安値として SKILL.md に記載
3. **frontmatter 書き換えを発生させない制約**: 本版の警告フラグは**出力サマリへの追記のみ**。対象 ISSUE の frontmatter（`status`・`assigned`・`reviewed_at`）は一切書き換えない。SKILL.md §3 書き換えガード節の既存記述と衝突しない旨を明記
4. **サマリ書式の第 3 ブロック**: `## 再判定推奨 ISSUE` を既存 `## ISSUE レビュー結果` / `## ISSUE 状態サマリ` の後に配置。書式案:
   ```markdown
   ## 再判定推奨 ISSUE

   長期持ち越し閾値を超えた `ready/ai` ISSUE（frontmatter 未変更、判断は人間 / AI に委ねる）:

   - `{path}` — reviewed_at: {YYYY-MM-DD}（{N} 日経過）: {持ち越し理由の候補テンプレート}
   ```
5. **「持ち越し理由の候補テンプレート」**: ISSUE 本文 §3 判定ルートの 2 系統（実機検証要 / AI 作業で消化可能）を含むテンプレート 2〜3 行を SKILL.md に常備する。判別自動化は本版でやらない
6. **`claude_sync.py` フロー**: `.claude/` 編集時の export → 編集 → import を IMPLEMENT.md に手順として明記

### `/imple_impl` への注意

- 編集対象は仕様書（SKILL.md × 2 + README.md × 1）のみ。Python コード追加・テスト追加は発生しない
- 編集後の挙動確認は「次回 `/issue_plan` 実行時に新しいサマリブロックが出力されるか」を RETROSPECTIVE で目視確認する。unit test 追加は本版スコープ外
- `ISSUES/util/low/issue-review-long-carryover-redemotion.md` を `ISSUES/util/low/done/` へ移動する最終操作を忘れない（consumed ISSUE の closeout）

### `/imple_doc` への注意

- `CHANGES.md` に記録すべき差分:
  - SKILL 仕様拡張（`issue_review` §1 / §5 追補、`issue_plan` 準備節の同期追補）
  - `ISSUES/README.md` ライフサイクル節追補
  - ISSUE 消化: `issue-review-long-carryover-redemotion` → `done/`
  - ISSUE 状態サマリ変化: ready/ai=4→3, raw/ai=2（不変）, review/ai=0（不変）
- `MASTER_PLAN.md` の PHASE サマリ行は触らない（本版は PHASE 完了後の meta 改善 minor）
- `CURRENT.md` は minor につき作成しない

### `/retrospective` への注意

- 本版の主眼効果（再判定推奨フラグの運用）は**本 `/retrospective` step 内で初回観察可能**。その場で「手元 util カテゴリ ready/ai 3 件に再判定フラグが立つか」を目視確認し、§A 観察節に記録する
- 次版（ver16.6 以降）への handoff 候補:
  - 10 バージョン強制降格ルールの実装要否判断（本版の警告フラグ運用を 1〜2 版観察してから）
  - `raw/ai` → `review/ai` 昇格ルートの整備（本版の対象外だったが、長期停滞が類似問題として存在）
  - `deferred-resume-twice-verification` / `toast-persistence-verification` の消化経路再検討（前者は research workflow、後者は「薄いスクリプト切り出し」単独 ISSUE 化）

### 後続版（ver16.6 以降）への引き継ぎ候補

- 10 バージョン強制降格ルールの実装（本 ISSUE 設計提案 §2 後半部分）
- `raw/ai` 長期停滞 ISSUE 向けレビュー経路の整備
- `toast-persistence-verification` 用テストスクリプトの切り出し（人間フィードバック反映）
- `deferred-resume-twice-verification` の消化（次 deferred 発火 run と連動）
- `imple_plan` / `experiment_test` の effort 下げ判断（引き続き sample 蓄積待ち）
- ver16.2 EXPERIMENT.md 「未検証」マーク解除の物理更新（次 research workflow 採用時）
- ver16.4 `extract_model_name` 修正の sidecar 反映確認（次 full / quick run の `*.costs.json` で自然採取）
