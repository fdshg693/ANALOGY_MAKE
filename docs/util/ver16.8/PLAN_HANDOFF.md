---
workflow: quick
source: issues
---

# ver16.8 PLAN_HANDOFF

## 関連 ISSUE / 関連ファイル

### 関連 ISSUE

- `ISSUES/util/low/issue-review-7day-threshold-observation.md` — **本版で `done/` 移動**（2 版経過後も §1.5 未発火の完了条件に到達）
- `ISSUES/util/low/issue-review-7day-threshold-adjustment.md` — **本版で新規起票**（`status: raw`, `assigned: ai`, `priority: low`, `reviewed_at: "2026-04-25"`）。7 日閾値の短縮案（5 日）の検討 ISSUE
- `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md` — §1.6 による将来の triage 推奨対象。本版では参照のみで触らない
- `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md` — 同上

### 関連ファイル（本版で編集 / 新規作成）

- `.claude/skills/issue_review/SKILL.md` — **編集**。§1.6（raw/ai 長期停滞検出）追加、§5 第 4 ブロック「## triage 推奨 raw/ai ISSUE」追加、該当あり/該当なしのテンプレ両方を §1.5 と揃えて定義
- `.claude/skills/issue_plan/SKILL.md` — **編集**（同期更新）。「準備」節の ISSUE レビューフェーズ記載に「(c) raw/ai 長期停滞検出（14 日閾値）」を追記し、ROUGH_PLAN 冒頭見出し列に `## triage 推奨 raw/ai ISSUE` を加える
- `ISSUES/util/low/done/issue-review-7day-threshold-observation.md` — `git mv` で `done/` 配下に移動
- `ISSUES/util/low/issue-review-7day-threshold-adjustment.md` — 新規作成（~30 行）

### 関連ファイル（参照のみ、本版は編集なし）

- `docs/util/ver16.5/IMPLEMENT.md` §F-1 — 7 日閾値の算出根拠と「後続 2 版で経過観察」の明記箇所
- `docs/util/ver16.7/PLAN_HANDOFF.md` §raw/ai 2 件の停滞観察 — 5 ループ連続据え置き観察記録、本版の §1.6 新設動機の直接根拠
- `docs/util/ver16.7/PLAN_HANDOFF.md` §§1.5 予測 vs 実績の整合性記録 — F-1 閾値調整 ISSUE 起票の期限到達を明記
- `.claude/skills/issue_review/SKILL.md` §1.5 / §5 第 3 ブロック — §1.6 実装の template（構造 / 文言 / テンプレの 2 パターン出し分けをそのまま流用）

## 後続 step への注意点

### /quick_impl

- **`.claude/` 配下の編集手順に注意**: CLI `-p` モードでは `.claude/` 直下を編集できない（`.claude/rules/claude_edit.md` 記載の制約）。手順:
  1. `python scripts/claude_sync.py export` — `.claude/` → `.claude_sync/` コピー
  2. `.claude_sync/` 配下のファイルを `Edit` / `Write` ツールで編集
  3. `python scripts/claude_sync.py import` — 書き戻し
- **§1.6 の文言は §1.5 を template に揃える**:
  - §1.5 の「§1 と並行して…」「閾値 7 日は SKILL 内の既定値…」「注: 本ルートで検出した ISSUE の frontmatter は一切書き換えない」のパラグラフ構造を踏襲
  - 差分は (a) 対象 status が `raw`、(b) 閾値 14 日、(c) 出力ブロック名称が「## triage 推奨 raw/ai ISSUE」、(d) `reviewed_at` 欠落時は対象外（§1.5 と同じ扱い）の 4 点のみ
  - `reviewed_at` の意味論補足（§1.5 で記述済みの「直近 N 日間誰も triage していない」相当）も §1.6 向けに書き直す
- **§5 第 4 ブロックのテンプレ出し分け**:
  - 該当あり: `- {path} — reviewed_at: {YYYY-MM-DD}（{N} 日経過）` + `- 候補理由 A: 内容が triage 可能な具体性を持つ → review/ai 昇格候補` + `- 候補理由 B: 外部情報（公式 docs / issue tracker）待ち → raw/ai 継続 + 情報源を追記` を固定文として提示
  - 該当なし: `該当なし（raw/ai で 14 日以上 triage されていない ISSUE はない）` 1 行
- **`issue_plan/SKILL.md` の同期更新**:
  - 「準備」節の ISSUE レビューフェーズ記述（現状「(a) review/ai → ready/ai..、(b) ready/ai で reviewed_at が 7 日以上前の ISSUE を再判定推奨として検出する」）に「(c) raw/ai で reviewed_at が 14 日以上前の ISSUE を triage 推奨として検出する」を追加
  - ROUGH_PLAN 冒頭 3 ブロック列挙箇所（`## ISSUE レビュー結果` / `## ISSUE 状態サマリ` / `## 再判定推奨 ISSUE`）に 4 番目として `## triage 推奨 raw/ai ISSUE` を追加
- **新規 ISSUE `issue-review-7day-threshold-adjustment.md` の内容骨子**:
  - 概要: ver16.5 で導入した §1.5 閾値 7 日が ver16.6 / ver16.7 / ver16.8 の 3 版連続で未発火。7 日は過鈍の可能性があり、5 日への短縮を検討
  - 対応方針: (1) ready/ai ISSUE の `reviewed_at` 更新頻度と stale 判定の感度を再評価、(2) 5 日閾値での再試行、(3) さらに未発火が続く場合は閾値ロジックそのもの（日数ベース vs 版数ベース）を再考
  - 完了条件: 閾値調整案の採否を `/issue_plan` で判定し、採用時は §1.5 の `7 日` を変更
  - 影響範囲: `issue_review/SKILL.md` §1.5 のみ
  - 参照: `docs/util/ver16.5/IMPLEMENT.md` §F-1 / `docs/util/ver16.7/PLAN_HANDOFF.md` §§1.5 予測 vs 実績の整合性記録
- **ISSUE `done/` 移動は最後に実施**: `git mv ISSUES/util/low/issue-review-7day-threshold-observation.md ISSUES/util/low/done/` の直前に、移動前のファイル内容を一度 `Read` で確認し、完了条件到達の注記を末尾に 1〜2 行追記してから移動する（done/ 配下のファイルは遡って読まれる可能性を残すため、移動理由を本文内に残す）
- **§1.6 新設後の出力確認**: 本版実装完了時点で util raw/ai 2 件は reviewed_at=2026-04-24（1 日経過）。初回出力は「該当なし」枠になるのが期待動作。これを ROUGH_PLAN の §1.6 予測と対照し、§5 第 4 ブロックが仕様どおり「該当なし」1 行で出力されることを /issue_plan 次回起動時に目視確認する旨を MEMO.md に残す
- **`imple_plan effort 下げ試行` は対象外**: 本版 quick のため、次に `full` 実装量小の版で handoff 再消費

### /write_current

- CHANGES.md のみ作成（minor）
- 必須記載:
  - (a) `.claude/skills/issue_review/SKILL.md` への §1.6 + §5 第 4 ブロック追加、`.claude/skills/issue_plan/SKILL.md` 同期更新
  - (b) `ISSUES/util/low/issue-review-7day-threshold-observation.md` を `done/` 移動、`ISSUES/util/low/issue-review-7day-threshold-adjustment.md` 新規起票
  - (c) コード（`scripts/` / `server/` / `app/`）変更ゼロ
  - (d) 既存 ready/ai 4 件（ver16.7 持ち越し分）の状態変化: `issue-review-7day-threshold-observation` は `done/` 移動で ready/ai から除外、他 3 件は状態不変
  - (e) raw/ai 2 件（`rules-paths-frontmatter-autoload-verification` / `scripts-readme-usage-boundary-clarification`）は本版の §1.6 による将来検出対象であり、本版時点で frontmatter 変更なし
- 前版 ver16.7 との差分は「SKILL 2 ファイル編集 + ISSUE 2 ファイル操作（移動 + 新規）」

### /wrap_up

- MEMO.md は任意。書くなら以下を記録:
  - **§1.6 初回発火予測**: 2026-05-08 以降（raw/ai 2 件の 14 日到達）。次版以降で発火観察が出るか継続確認
  - **F-1 閾値観察の後続**: 本版で起票した `issue-review-7day-threshold-adjustment` が raw/ai に入るため、§1.6 の 14 日閾値観察対象にも加わる。§1.5 と §1.6 双方の閾値妥当性が交差観察可能になる
  - **medium ready/ai 2 件の据え置き継続**: `deferred-resume-twice-verification` は人手実測待ち、`issue-review-rewrite-verification` は他カテゴリ `review/ai` 発生待ち。次版以降でも同様の handoff を継続
  - **raw/ai 2 件の 6 ループ目据え置き**: §1.6 の新設により今後 triage 推奨として可視化されるため、次版以降で human / AI が直接 triage するトリガーになる見込み
  - **§1.5 と §1.6 の閾値関係**: §1.5 = 7 日 / §1.6 = 14 日（§1.5 の 2 倍）の既定値は「raw は triage 判断そのものに時間がかかる（情報収集 / 公式 docs 確認 等）」前提。運用で過鈍 / 過敏と判断された場合のみ後続版で調整
- `imple_plan effort 下げ試行` は本版 quick のため対象外。次版以降 full 実装量小ケース出現時に再試行
