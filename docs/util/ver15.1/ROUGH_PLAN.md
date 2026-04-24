---
workflow: quick
source: issues
---

# ver15.1 ROUGH_PLAN

ver15.0 で新設した `/issue_scout`（`--workflow scout`）の**初回 smoke test 実施とリスク R1/R2 の観察クローズ**を行うマイナーバージョン。handoff（`FEEDBACKS/handoff_ver15.0_to_next.md`）の路線 A に該当する。

## ISSUE レビュー結果

`ISSUES/util/{high,medium,low}/` を走査したが、`status: review` かつ `assigned: ai` の ISSUE は **0 件**。遷移対象なし（書き換え実施なし）。

## ISSUE 状態サマリ

util カテゴリの `status × assigned` 分布（`python scripts/issue_status.py util` 実行結果、ver15.1 `/issue_plan` 起動時点）:

| priority | ready/ai | review/ai | need_human_action/human | raw/human | raw/ai |
|---|---|---|---|---|---|
| high | 0 | 0 | 0 | 0 | 0 |
| medium | 1 | 0 | 0 | 0 | 1 |
| low | 0 | 0 | 0 | 0 | 2 |

- `ready / ai` 1 件: `ISSUES/util/medium/issue-review-rewrite-verification.md`（util 単体消化不能で継続持ち越し、ver6.0 以来）
- `raw / ai` 3 件:
  - `ISSUES/util/medium/issue-scout-noise-risk.md`（ver15.0 新規、scout R1/R2 検証先送り分）← **本バージョンのトラッキング対象**
  - `ISSUES/util/low/rules-paths-frontmatter-autoload-verification.md`（ver14.0 観察持越し）
  - `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md`（同上）

## 選定結果

### 着手対象

**`ISSUES/util/medium/issue-scout-noise-risk.md` のクローズ判定**（現状は `raw / ai`、本バージョンで観察結果に基づき `done/` 化 or `ready / ai` 昇格のいずれかに遷移させる）。

### 選定理由

- `FEEDBACKS/handoff_ver15.0_to_next.md` が路線 A として **scout smoke test 実施 → `issue-scout-noise-risk.md` 消化**を優先路線に指名している（判断基準: scout の実挙動が PHASE7.1 §2 設計にフィードバックされ得るため、§2 着手前に観察を完了させるのが合理的）。
- `ready / ai` に該当する `issue-review-rewrite-verification.md` は util 単体で消化不能（`app` / `infra` カテゴリでの `/split_plan` / `/quick_plan` 起動待ち）のため、util カテゴリ単体での ver15.1 ではスコープ外。

### 除外理由

- **路線 B（PHASE7.1 §2 `QUESTIONS/` + `question` workflow 着手）**: handoff で順序固定されており、路線 A 完了後の ver15.1 or ver15.2 に回す。本バージョンでは扱わない。
- **MASTER_PLAN 新 PHASE 骨子作成**: PHASE7.1 は §1 のみ完了の**未完走**のため、PHASE8.0 骨子作成は不要。
- **他 `raw / ai` 2 件（low 優先度）**: ver14.0 観察持越し分で本バージョンの観察対象外。継続保持。

## スコープ

### 実施する

1. **scout smoke test の手動実行**: `python scripts/claude_loop.py --workflow scout --category util --max-loops 1` を 1 回起動し、`/issue_scout` SKILL が実際に ISSUE を起票する挙動を初回観察する。
2. **観察ポイント 3 軸の評価**（`issue-scout-noise-risk.md` §本番発生時の兆候・handoff §路線 A の観察ポイントに基づく）:
   - **上限遵守**: 起票件数が 0〜3 件の範囲に収まるか
   - **重複検出**: 起票内容が既存 `ISSUES/util/`・`ISSUES/util/done/` と重複していないか（過検出/取りこぼしの判定）
   - **frontmatter 完全性**: 起票された全 ISSUE に `status: raw` / `assigned: ai` / `priority` / `reviewed_at` の 4 フィールドが付与されているか
3. **観察結果に基づくクローズ判定**:
   - 3 軸すべてクリア → `issue-scout-noise-risk.md` を `ISSUES/util/done/` に移動
   - いずれかで問題検出 → `issue-scout-noise-risk.md` を `ready / ai` に昇格し、ver15.2 で SKILL.md 側の閾値/件数上限を調整
4. **ヒューリスティック微調整（問題検出時のみ）**: 過検出なら Jaccard 閾値を 0.5 → 0.4、取りこぼしなら 0.5 → 0.6 or 本文冒頭 50 文字 → 100 文字への緩和/強化を `.claude/skills/issue_scout/SKILL.md` に反映。件数上限を 3 → 2 に下げる選択肢も含む。

### 実施しない

- PHASE7.1 §2（`QUESTIONS/` + `question` workflow 新設）— 路線 B は本バージョン対象外。
- PHASE7.1 §3（`ROUGH_PLAN.md` / `PLAN_HANDOFF.md` 分離）— 路線 B 以降。
- PHASE7.1 §4（run 単位通知）— ver15.2 想定。
- `issue-review-rewrite-verification.md` 本体の消化 — `app` / `infra` 起動時まで持ち越し。
- `low` 優先度 `raw / ai` 2 件（ver14.0 持越し）の観察/消化。

## 成果物（想定）

3 軸すべてクリアの場合:
- `ISSUES/util/medium/issue-scout-noise-risk.md` → `ISSUES/util/done/` に移動（1 ファイル）
- scout 起票により新規 `ISSUES/util/{priority}/*.md` が 0〜3 件追加される可能性あり（scout の副産物。内容レビューは次回 `/issue_plan` で実施）
- `docs/util/ver15.1/` に `CHANGES.md`（マイナー）および観察結果メモを記録
- コード変更は原則発生しない

問題検出の場合:
- `ISSUES/util/medium/issue-scout-noise-risk.md` の frontmatter を `status: ready` に昇格（本文に観察結果と推奨する閾値/件数を追記）
- `.claude/skills/issue_scout/SKILL.md` の閾値/件数上限を微調整（ただし本格的な調整は ver15.2 に回す選択肢もあり、本バージョンでは昇格のみで留める判断も可）

## 関連 ISSUE / ドキュメント

- `FEEDBACKS/handoff_ver15.0_to_next.md` — 本バージョンの路線指名元（1 回消費で `FEEDBACKS/done/` へ移動する）
- `ISSUES/util/medium/issue-scout-noise-risk.md` — 本バージョンのクローズ対象トラッキング ISSUE
- `docs/util/ver15.0/IMPLEMENT.md` §リスク R1, R2 — scout workflow の元リスク定義
- `docs/util/ver15.0/MEMO.md` §リスク検証結果 R1, R2 — R1/R2 の先送り経緯
- `docs/util/ver15.0/RETROSPECTIVE.md` §3 〜 §4.5 — 次バージョン種別推奨・handoff 書き出し元
- `docs/util/MASTER_PLAN/PHASE7.1.md` — §1（実装済・ver15.0）/ §2〜§4（未着手）
- `.claude/skills/issue_scout/SKILL.md` — smoke test 対象 SKILL 本文・ヒューリスティック定義の一次資料

## ワークフロー選択の根拠（`workflow: quick`）

- 選定 ISSUE に `status: review` は含まれない（review/ai は 0 件）。
- MASTER_PLAN 新項目 / アーキテクチャ変更 / 新規ライブラリ導入なし。
- 変更対象見込みは `ISSUES/util/medium/issue-scout-noise-risk.md` の移動/昇格 1 ファイル（+ 問題検出時のみ `.claude/skills/issue_scout/SKILL.md` 1 ファイル）で計 1〜2 ファイル・合計 100 行未満。
- したがって `workflow: quick`（`/issue_plan` → `/quick_impl` → `/quick_doc`）を採用する。

## バージョン種別の判定

**マイナー（ver15.1）**。以下根拠:
- MASTER_PLAN 新項目への着手なし（PHASE7.1 §1 完了分の観察クローズ）。
- アーキテクチャ変更なし・新規外部ライブラリ導入なし・破壊的変更なし。
- 既存 ISSUE（`issue-scout-noise-risk.md`）の消化 + 必要に応じた SKILL 閾値微調整のみ。

## 後続 `/quick_impl` への引き継ぎメモ

- smoke test 起動コマンドは `python scripts/claude_loop.py --workflow scout --category util --max-loops 1` で固定。unattended 実行中は別プロセスを立てないので、`/quick_impl` 実装ステップ内で Bash 経由起動 → ログ収集 → 観察評価 → ファイル遷移という順序になる。
- scout が新規起票する ISSUE は本バージョンではレビューせず `raw / ai` のまま残置する（次回 `/issue_plan` の review フェーズで通常処理）。
- 問題検出時の SKILL.md 閾値調整は**最小限**に留め、大幅な書き直しは ver15.2 に分離する。`/quick_impl` の範疇を逸脱しそうなら `/quick_impl` 側で判断して ver15.1 を「昇格のみ」に縮退させ、調整本体を ver15.2 に回す。
