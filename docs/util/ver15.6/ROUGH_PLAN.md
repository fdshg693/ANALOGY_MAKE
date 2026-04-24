---
workflow: quick
source: issues
---

# ver15.6 ROUGH_PLAN — PLAN_HANDOFF.md 運用観察 2 件の判定クローズ

## バージョン種別

**マイナー（ver15.6）**。MASTER_PLAN 新項目への着手・アーキテクチャ変更・新規ライブラリ導入はいずれもなし。ver15.3 で新設した `PLAN_HANDOFF.md` 運用の観察期間が満了したため、観察系 low ISSUE を 2 件束ねて判定・クローズする。

## ISSUE 状態サマリ（util カテゴリ）

| priority | ready/ai | review/ai | need_human_action/human | raw/ai | raw/human |
|---|---|---|---|---|---|
| high | 0 | 0 | 0 | 0 | 0 |
| medium | 1 | 0 | 0 | 0 | 0 |
| low | 3 | 0 | 0 | 2 | 0 |

`review/ai` が 0 件のため、本ループの ISSUE レビューフェーズは no-op（state 遷移なし）。

## ISSUE レビュー結果

- 走査対象: util カテゴリ全件
- `review/ai` 件数: 0
- 状態遷移: なし（`ready/ai` への昇格 0 件、`need_human_action/human` への振り分け 0 件）

## 着手対象（スコープ）

ver15.3 で新設した `PLAN_HANDOFF.md` 運用に紐づく観察系 ISSUE 2 件を束ねて判定する。どちらも ver15.4〜15.5 / 15.6 の観察期間を満たした時点で `done` or 是正アクションを決める設計になっており、本バージョンが観察期間の満了点となる。

### 実施する

1. **`ISSUES/util/low/plan-handoff-frontmatter-drift.md`** — ver15.3 / ver15.4 / ver15.5 の 3 バージョン分の `ROUGH_PLAN.md` と `PLAN_HANDOFF.md` の frontmatter（`workflow:` / `source:`）を機械的に比較し、drift の実発生率を確定させる。発生率ゼロなら ISSUE を `done/` へ移動、非ゼロなら `scripts/claude_loop_lib/validation.py` に軽量チェックを追加する ISSUE へ書き換える（本バージョンではチェック実装までは踏み込まない）。

2. **`ISSUES/util/low/plan-handoff-omission-tracking.md`** — ver15.3 / ver15.4 / ver15.5 の 3 バージョンで `PLAN_HANDOFF.md` の存在有無と省略宣言の有無を確認し、quick バージョンでの省略乱発（= 引き継ぎ情報が `ROUGH_PLAN.md` 本文にも欠落する状態）が観測されているかを確定させる。乱発なしなら ISSUE を `done/` へ移動、乱発ありなら `issue_plan/SKILL.md` の省略条件を締める follow-up ISSUE を起票する（本バージョンでは SKILL 改訂までは踏み込まない）。

ユーザーから見た変化:
- いずれも外部挙動変化なし。ISSUES/ 配下のファイル整理と（必要に応じて）follow-up ISSUE 起票のみ
- `PLAN_HANDOFF.md` 運用について「観察期間が切れた」ことを明確化し、以降の観察負債を閉じる

### 実施しない

- `toast-persistence-verification.md`（low）— Windows 実機での目視検証が必須であり、`--workflow auto` / quick のヘッドレス前提では完結しない。ver15.5 に続き継続持ち越し。
- `issue-review-rewrite-verification.md`（medium）— util 単体で消化不能（`app` / `infra` カテゴリの `/split_plan` or `/quick_plan` 起動待ち）。継続持ち越し。
- `rules-paths-frontmatter-autoload-verification.md` / `scripts-readme-usage-boundary-clarification.md` — `raw/ai` のためレビューフェーズ通過前。本バージョンでは未着手。
- `validation.py` への drift 検出チェック実装 / `issue_plan/SKILL.md` の省略条件締め込み — 観察結果が「非ゼロ」に倒れた場合のみ必要になる後続作業であり、本バージョンスコープからは切り離す。
- PHASE8.0 骨子作成 — 既定 PHASE は完走済だが、PHASE 規模の未解決テーマが util カテゴリに浮上していないため見送り（ver15.4 RETROSPECTIVE §3 推奨を継続適用）。

## 想定成果物

- `ISSUES/util/low/plan-handoff-frontmatter-drift.md` — 判定結果に基づき `done/` へ移動 or 内容更新
- `ISSUES/util/low/plan-handoff-omission-tracking.md` — 判定結果に基づき `done/` へ移動 or 内容更新
- （観察結果によって）`ISSUES/util/low/` 配下に follow-up ISSUE 1〜2 件を新規起票する可能性あり
- `docs/util/ver15.6/MEMO.md` — 観察結果（3 バージョン分の frontmatter / 省略状況の一覧表）

## ワークフロー選択根拠

**`workflow: quick`** を選択。

- 全件 `status: ready` であり `review` を含まない（quick の前提条件 1 を満たす）
- 変更対象は主に `ISSUES/util/low/*.md` の 2 ファイル（frontmatter 書き換え / ファイル移動）+ 観察結果を残す `MEMO.md` 1 ファイル。いずれも観察報告系で合計差分は 50 行以内の見込み
- コード変更を伴う follow-up（validation.py 追加 / SKILL 改訂）は**このバージョンには含めない**設計（観察結果次第で別バージョンに切り出す）ため、設計判断の余地が小さく `/split_plan` での詳細分解を要さない

## 事前リファクタリング要否

**不要**。観察と ISSUE 状態整理のみで、コード本体の先行整理対象はない。

PLAN_HANDOFF.md は別ファイルで作成（quick 必須節: 関連 ISSUE / 関連ファイル / 後続 step 注意点）。
