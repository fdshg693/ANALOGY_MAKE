---
workflow: full
source: master_plan
---

# ver14.0 ROUGH_PLAN — PHASE7.0 §6+§7+§8 一括着手（retrospective 強化 × rules 整備）

## ISSUE レビュー結果

- 遷移件数: 0 件（`status: review` かつ `assigned: ai` の ISSUE は util カテゴリ内に存在せず）
- 対象パス: なし
- 書き換え対象なしのため `issue_review` SKILL による frontmatter 書き換えは発生しない

## ISSUE 状態サマリ（util カテゴリ、`done/` 除外）

| status × assigned | 件数 | ファイル |
|---|---|---|
| `ready / ai` | 1 | `ISSUES/util/medium/issue-review-rewrite-verification.md`（util 単体消化不能、ver6.0 から 9 バージョン連続持ち越し） |
| `raw / ai` | 2 | `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md`, `ISSUES/util/low/system-prompt-replacement-behavior-risk.md` |
| `review / ai` | 0 | — |
| `need_human_action / human` | 0 | — |
| `ready / human` | 0 | — |

計 3 件（ready 1 / raw 2）。

## 着手判断

### 選定結果

**ver14.0（メジャー、full）で PHASE7.0 §6+§7+§8 を一括着手する。ISSUE 消化は行わない。**

- `source: master_plan`
- `workflow: full`（MASTER_PLAN 新項目着手のため必ず full）

### 判断経緯

1. **`ready / ai` ISSUE の除外**: 唯一の `ready / ai` である `issue-review-rewrite-verification.md` は「util カテゴリ単体では消化不能（実動作確認のため app / infra カテゴリで `/split_plan` / `/quick_plan` 起動が必要）」という構造的制約があり、ver6.0 以来 9 バージョン連続で持ち越されている。今回も util カテゴリで動かすため、引き続き持ち越し。
2. **`raw / ai` ISSUE の除外**: 2 件とも「ver14.0 §7 rules 整備 / §8 prompt・model 評価と合わせて再評価予定」（ver13.0 RETROSPECTIVE §3-2 / §4-1）に位置づけられており、ver14.0 の本作業と密接に関連する。ver14.0 の成果を踏まえて次バージョン以降で `ready` 昇格を判断するのが合理的で、`raw` のまま据え置く。
3. **MASTER_PLAN の状態**: PHASE7.0 §1〜§5 完了、§6〜§8 未着手。PHASE 未完走のため新 PHASE 骨子作成は不要。§6〜§8 は ver13.0 RETROSPECTIVE §3-2 で「3 節いずれも `/retrospective` SKILL と `.claude/rules/` を同時に触るため、別バージョンに分けると同ファイルを複数回レビューすることになる」と明示的に一括推奨されている。
4. **メジャーバージョン昇格の妥当性**: §7 の `.claude/rules/scripts.md` 新規作成は既存 CLAUDE.md / SKILL 群の stable 規約を rules 側へ移動するアーキテクチャ変更を含む。§6・§8 は `/retrospective` SKILL の責務拡張（コード成果 → コード成果 + workflow 自身の prompt / model 評価 + 次ループ FEEDBACK 書出し）を伴い、SKILL 構造の刷新に該当。CLAUDE.md バージョン管理規則に照らしメジャー（X.0）昇格が妥当。
5. **「MASTER_PLAN 全フェーズ完了時ガイドライン」は不適用**: PHASE7.0 §6〜§8 が未着手のため、このガイドラインの前提（全 PHASE 完了）を満たさない。

## 本バージョンのスコープ

PHASE7.0 §6 + §7 + §8 の 3 節を一括で消化する。目的は「ループ間 handoff / stable 規約 / workflow 設計評価」の 3 軸を `/retrospective` SKILL と `.claude/rules` の 2 つの拠点に集約し、ループ改善を定常作業化すること。

### §6. `/retrospective` から次ループ向け FEEDBACK を書き出す handoff

- **提供する機能**: `/retrospective` SKILL に「次ループで読ませたい入力を `FEEDBACKS/` 直下に書き出す」能力を追加する。handoff 対象は「次に着手すべき ISSUE の候補」「注意点」「保留判断」「workflow 設定（prompt / model / temperature）見直しメモ」。
- **ユーザー体験の変化**: 今までは retrospective 成果が `docs/{カテゴリ}/ver{N.M}/RETROSPECTIVE.md` に閉じ、次ループの `/issue_plan` は docs を読み直すしかなかった。ver14.0 以降は retrospective が必要と判断した補助入力を `FEEDBACKS/` 経由で次ループに 1 回だけ自動注入できる。
- **運用境界**: handoff は「次ループを少し有利にする補助線」であって「状態 DB / 恒久メモリ」ではない。書き出された FEEDBACK は §4（ver13.0 完了）のルールに従い、次ループで 1 回読まれた後に `FEEDBACKS/done/` へ移動する。
- **何を書かないか**: retrospective が毎回 FEEDBACK を出す必要はない。書き出しは「書くべき内容がある場合のみ」とし、空の handoff は禁止（次ループの FEEDBACK 消費を無駄にしないため）。

### §7. `.claude/rules` の整備と `scripts` 向け stable rule file 追加

- **提供する機能**: `scripts/**/*` を対象にした新規 rule file `.claude/rules/scripts.md` を追加し、scripts 系で毎回守るべき stable な規約（pathlib 利用・CLI 引数処理・ログ出力・frontmatter / YAML 更新時の作法など）を 1 箇所に集約する。既存 CLAUDE.md / SKILL 文書内で重複している stable 規約を rules 側へ寄せる。
- **ユーザー体験の変化**: 今までは scripts 系を編集する際、規約が docs（`scripts/README.md`・`scripts/USAGE.md`）と SKILL 指示と CLAUDE.md に散在していた。ver14.0 以降は `.claude/rules/scripts.md` を一次資料にすることで、agents が毎回同じ前提で動ける。
- **規約の責務分離**: volatile（PHASE ごとの進行状況・一時的な注意点・ロードマップ）は docs 側に残し、stable（書き方・呼び出し方・ファイル作法）は rules 側に寄せる。境界が曖昧なものは rules に書かない（`.claude/rules` は「毎回必ず守るべき」のみ）。
- **適用範囲の明示**: `paths:` frontmatter で適用対象を `scripts/**/*` に限定し、既存 `claude_edit.md` と同方式で運用する。
- **何を書かないか**: PHASE 固有の進捗メモや頻繁に変わる運用ログは rules に書かない（`やらないこと` §）。

### §8. `/retrospective` で workflow prompt / model 利用も評価対象にする

- **提供する機能**: `/retrospective` SKILL に「各 step の system prompt / model / temperature / max_tokens が役割に合っていたか、長すぎないか、指示重複がないか、品質・速度・コストに見合っていたか」を評価する節を追加する。評価結果は「維持 / 調整 / 削除候補」の 3 分類で記録する。
- **ユーザー体験の変化**: 今までは retrospective がコード成果（実装差分・テスト結果・計画乖離）の振り返り中心で、workflow 設計そのもの（prompt / model 配置）は人手の記憶頼みだった。ver14.0 以降は step 別 override 機構（PHASE7.0 §1 / ver10.0〜ver12.0 で整備済）に基づき、評価結果を次ループの YAML 修正指示へ具体的に落とし込める。
- **§6 との接続**: §8 の評価結果のうち「次ループで試すべき調整」は §6 の FEEDBACK handoff で書き出し、次ループの `/issue_plan` や YAML 編集作業に持ち越す。
- **何を書かないか**: prompt / model 評価は retrospective の必須項目ではなく、評価材料がないループでは省略可能とする（毎ループで形骸的な評価を要求しない）。

## 関連ファイル・関連 ISSUE

### 変更想定ファイル（`/split_plan` で詳細化）

- `.claude/skills/retrospective/SKILL.md` — §6 handoff 指示・§8 prompt / model 評価指示の追加（現状 84 行）
- `.claude/skills/issue_plan/SKILL.md` — §6 で retrospective が書いた FEEDBACK を `/issue_plan` 側で参照する流れの明示
- `.claude/rules/scripts.md` — §7 新規作成（stable な scripts 規約、`paths: scripts/**/*` フロントマター）
- `.claude/rules/claude_edit.md` — §7 で既存 rule と重複する規約がある場合の整理（現状 12 行）
- `CLAUDE.md` / `scripts/README.md` / `scripts/USAGE.md` — §7 で rules へ移した規約の重複を削除（stable/volatile 責務分離）
- `.claude/SKILLS/meta_judge/WORKFLOW.md`（存在するなら）— §6 handoff の WORKFLOW 記述反映

### 関連 ISSUE（持ち越し・再評価候補）

- `ISSUES/util/medium/cli-flag-compatibility-system-prompt.md`（`raw/ai`）— §7 で scripts 系 CLI flag 規約を rules 化する中で再評価する。本バージョンでは着手しない。
- `ISSUES/util/low/system-prompt-replacement-behavior-risk.md`（`raw/ai`）— §8 prompt / model 評価の評価観点として議論されうる。本バージョンでは着手しない。
- `ISSUES/util/medium/issue-review-rewrite-verification.md`（`ready/ai`）— util 単体消化不能のため持ち越し継続（app / infra カテゴリで `/issue_plan` を動かすタイミングを待つ）。

### 関連 docs

- `docs/util/MASTER_PLAN/PHASE7.0.md` — §6・§7・§8 の仕様根拠（本計画の一次資料）
- `docs/util/ver13.0/RETROSPECTIVE.md` §3-2 / §4-4 — ver14.0 一括着手の推奨根拠・事前メモ
- `docs/util/ver13.1/MEMO.md` — 直前バージョンの整合（FEEDBACKS 異常終了 invariant の CI 化完了、本バージョンの §4 運用ルールへの影響なし）

## 事前リファクタリング

事前リファクタリング不要（変更対象は SKILL 2 本 + rule file 新規 1 本 + docs 側の重複規約削除に限られ、Python コード側の構造変更は発生しない。`.claude/rules/scripts.md` の新設と既存 docs からの規約移設は同一コミット内で完結できる自然な順序があり、前段で別途リファクタリングする必要はない）。

## ワークフロー選定根拠（`workflow: full`）

- **MASTER_PLAN 新項目着手**: PHASE7.0 §6+§7+§8 を一括で進める → 「MASTER_PLAN 新項目 / アーキテクチャ変更 / 新規ライブラリ導入を含む場合 → 必ず full」ルールに該当
- **ファイル数の見込み**: SKILL 2 本 + rules 新規 1 本 + 既存 rules / docs の重複整理を含めると、quick 閾値（3 ファイル以下かつ 100 行以下）を明確に超える
- **plan_review_agent によるレビューが有益**: §7 の rules 責務分離は「何を stable とみなすか」の判断材料が設計依存で、第三者レビューで境界の妥当性を検証する価値が高い

## `/split_plan` への引き継ぎ要点

1. **IMPLEMENT.md 策定時の優先順**: §7（rules 新設・責務整理）を先に固め、その上で §6・§8 の SKILL 拡張を載せる順序が自然。rules 側に規約が揃った状態で SKILL を編集すると、SKILL 本文から規約記述を rules へのポインタに置換できる。
2. **`.claude/` 編集手順の踏襲**: ver13.0 で確認済の `claude_sync export → edit → import` 手順を `/split_plan` / `/imple_plan` のどちらで要求するか、IMPLEMENT.md §4「実装順序」で明記すること。
3. **テスト戦略**: §6〜§8 はいずれも SKILL / rules 中心で Python コード変更は最小想定。既存 233 件の回帰通過を担保する程度で良いが、§6 の「retrospective が書いた FEEDBACK が次ループで 1 回だけ消費される」挙動は §4 の integration test（ver13.1 で追加済の `TestFeedbackInvariant`）で暗黙的にカバーされることを確認する。新規テスト要否は `/split_plan` で判断。
4. **リスク列挙 → MEMO 検証マトリクスの継続**: ver10.0 以降 4 バージョン連続で有効性が示されている運用パターンで、ver14.0 でも踏襲する。特に §7 の「rules と docs の責務分離を中途半端にすると stable convention が二重管理になる」（PHASE7.0 リスク §6）は事前リスクとして IMPLEMENT.md に明記すること。
5. **`raw/ai` ISSUE の扱い方針の明記**: `cli-flag-compatibility-system-prompt.md` / `system-prompt-replacement-behavior-risk.md` について、ver14.0 完了後の retrospective で `ready` 昇格 / `done` / 継続保留のどれに振るかを判断する旨を IMPLEMENT.md または MEMO.md に記載。
