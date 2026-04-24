---
workflow: quick
---

# ver16.6 CHANGES

前バージョン: ver16.5

## 変更ファイル一覧

| 変更種別 | ファイル | 概要 |
|---|---|---|
| 移動 | `ISSUES/util/low/issue-review-llm-date-calc-observation.md` → `done/` | F-3 ISSUE 消化・完了 |
| 移動 | `FEEDBACKS/handoff_ver16.5_to_next.md` → `done/` | ver16.5 handoff フィードバック消費完了 |
| 追加 | `docs/util/ver16.6/ROUGH_PLAN.md` | 本版計画書 |
| 追加 | `docs/util/ver16.6/PLAN_HANDOFF.md` | 後続ステップへの handoff 情報 |
| 追加 | `docs/util/ver16.6/IMPLEMENT.md` | 実装記録 |

## 変更内容の詳細

### F-3 ISSUE 消化（`issue-review-llm-date-calc-observation`）

ver16.5 で `issue_review` SKILL §1.5 / §5 第 3 ブロックとして追加した「`ready/ai` 長期持ち越し ISSUE の再判定推奨ルート」の初回実走を本版で実施。

- `ROUGH_PLAN.md` の `## 再判定推奨 ISSUE` ブロックが §5「該当ゼロ版」テンプレート（見出し + 「該当なし〜」1 行）と一致していることを確認
- 書式確認 OK により、F-3 完了条件を充足と判定
- `git mv` で `ISSUES/util/low/done/` へ移動

### §1.5 予測 vs 実績の整合性確認

- **予測**（ver16.5 RETROSPECTIVE §3.5）: ready/ai 5 件すべて `reviewed_at < 7 日` → 「該当なし」出力
- **実績**: 該当ゼロ、「該当なし」1 行出力
- **判定**: 一致。LLM による日付計算が SKILL の期待動作通りに機能することを初回実走で確認

### コード変更

なし。コード / SKILL / YAML / テスト いずれも変更なし。

## 技術的判断

- ver16.5 handoff で「raw/ai 2 件は 3 ループ停滞で昇格ルート整備を検討」としていたが、本版時点で既に 4 ループ目（ver16.3〜16.6）。ver16.7 の `/issue_plan` では `raw/ai` 長期停滞向け review 昇格ルートの優先度を一段上げて検討予定
