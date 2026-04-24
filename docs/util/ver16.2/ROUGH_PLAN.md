---
workflow: research
source: master_plan
---

# ver16.2 ROUGH_PLAN — PHASE8.0 §3 token/cost 計測

## バージョン種別

**マイナー（ver16.1 → ver16.2）**。PHASE8.0 §3 着手だが、`costs.py` 新規 + `logging_utils.py` 拡張 + テスト追加が中心で、新ライフサイクル導入や破壊的変更を伴わない。`CHANGES.md` を生成、`CURRENT_*.md` は §3 完了後の差分次第で `wrap_up` / `write_current` 側が判断する。

## ISSUE レビュー結果

- ready/ai に遷移: 0 件（`review/ai` の対象 ISSUE なし）
- need_human_action/human に遷移: 0 件
- 追記した `## AI からの依頼`: 0 件
- 別途 triage: `ISSUES/util/medium/deferred-resume-twice-verification.md` を `raw/ai` → `ready/ai` に昇格（FEEDBACKS handoff §次ループで試すこと §3 の指示。ver16.1 RETROSPECTIVE §4 起票時から再現手順 / 期待動作 / 影響範囲 / 関連資料がすべて埋まっており `issue_review` 判定基準 3/3 を満たす。実機検証自体は外部 `claude` CLI 起動を要するが、ver16.1 で実装済の deferred execution 機構を経由すれば AI 自走可能なので `assigned: ai` を維持）

## ISSUE 状態サマリ

| status / assigned | 件数 |
|---|---|
| ready / ai | 3 |
| review / ai | 0 |
| need_human_action / human | 0 |
| raw / human | 0 |
| raw / ai | 2 |

内訳:

- ready/ai 3 件: `issue-review-rewrite-verification` / `toast-persistence-verification` / `deferred-resume-twice-verification`（本版で昇格）
- raw/ai 2 件: `rules-paths-frontmatter-autoload-verification` / `scripts-readme-usage-boundary-clarification`（共に観察 trigger 待ち、本版スコープ外）

## 着手対象 / スコープ

### 実施する

PHASE8.0 §3「step 単位の token/cost 計測と workflow 比較ログ」を完走させる。これにより PHASE8.0 全 3 節（§1 research workflow / §2 deferred execution / §3 cost 計測）が揃い、PHASE8.0 が完走する。

提供する機能の全体像:

- **step 別 cost 計測**: 各 Claude 実行 step ごとに、workflow 種別・step 名・model・session ID・開始/終了時刻・duration・input/output token 数・cache read/write 相当量・金額換算値を記録する
- **取得経路**: Claude CLI の usage 系出力（または準ずる経路）を一次ソースとし、ログ本文の文字数や推定式での代替は採用しない
- **二重保存**: 人間が読む workflow log にサマリを残しつつ、後から集計可能な machine-readable sidecar（JSON 等）にも保存する
- **price book 運用**: 単価テーブルと価格改定への追随方法を決め、「どの価格表で計算した cost か」が後から特定できる形にする
- **run total / step 明細**: `quick` / `full` / `research` を比較できるよう、run 全体の合計と step 別の明細を両方残す
- **欠測表現**: usage が取得できなかった step は「未取得」+ 理由を明示し、ゼロ扱いで誤魔化さない
- **deferred 実行と分離**: deferred execution の外部コマンド待機時間は token cost と混同せず、duration と cost を別軸で残す（ver16.1 §2 成果と整合）

ユーザー体験の変化:

- 1 run 終了時に「合計 cost」と「step 別 cost 明細」が確認でき、`quick` / `full` / `research` の費用対効果を `/retrospective` §3.5 で根拠ある比較ができるようになる
- §1 で導入した `research` workflow の追加 step（`research_context` / `experiment_test`）が手戻り削減 vs. 追加 cost のどちらに寄ったかを後から判定できる材料が揃う

### 実施しない

- §3 と独立な ISSUE の消化（持ち越し ready/ai 3 件は本版スコープ外）
- 価格表を不変の請求正本として扱う設計（運用記録としての価格スナップショットに留める）
- workflow 自己テストの常時 CI 組み込み（PHASE8.0 §2-2 の指示どおり試行に留める）
- `claude_loop.yaml` / `claude_loop_quick.yaml` の `write_current` effort 引上げ波及（FEEDBACKS handoff §保留事項 1 点目より、§3 完走後の品質を見て後続バージョンで判断）
- `research_context` / `experiment_test` の model 下げ（同 §保留事項 3 点目より、本版で `research` を再採用したサンプルが取れた後の判断材料に回す）

## 成果物（想定一覧）

| ファイル | 操作 | 内容 |
|---|---|---|
| `scripts/claude_loop_lib/costs.py` | 新規作成予定 | Claude usage/cost 情報の取得、価格計算、run 集計 |
| `scripts/claude_loop_lib/logging_utils.py` | 変更予定 | token cost / run summary のログ整形（deferred result 整形と並列で追記） |
| `scripts/claude_loop.py` | 変更予定 | step 終了時の cost 集計フック、run 終了時の合計出力 |
| `scripts/claude_loop_lib/validation.py` | 変更予定 | cost 設定キー（価格表参照、出力先など）の検証（追加が発生する場合のみ） |
| `scripts/tests/test_costs.py` | 新規作成予定 | usage 取得・単価適用・欠測時フォールバックの単体テスト |
| `scripts/tests/test_logging_utils.py` | 変更予定 | cost summary 出力フォーマットの assertion 追加 |
| `scripts/tests/test_claude_loop_integration.py` | 変更予定（必要なら） | run 全体の cost sidecar が生成されることを検証 |
| `scripts/README.md` | 変更予定 | cost log / price book / sidecar 仕様の記載 |
| `scripts/USAGE.md` | 変更予定 | cost sidecar の場所と読み方を追記 |
| `docs/util/ver16.2/RESEARCH.md` | 新規作成予定 | Claude CLI usage/billing 取得経路の調査結果 |
| `docs/util/ver16.2/EXPERIMENT.md` | 新規作成予定 | usage 抽出の再現実験結果 |
| `docs/util/ver16.2/REFACTOR.md` / `IMPLEMENT.md` / `MEMO.md` / `CHANGES.md` | 新規作成予定 | 各 step が標準どおり生成 |
| `docs/util/MASTER_PLAN/PHASE8.0.md` | 変更予定 | §3 ✅ 追記、PHASE8.0 完走宣言 |
| `.claude/rules/scripts.md` | 変更予定（必要なら） | cost log / sidecar の stable rule 化（§3 完了時に判断） |

ファイル変更一覧の最終確定は `IMPLEMENT.md` に委ねる。本ファイルは全体像把握用。

## ワークフロー選択根拠

**`research` を採用**。`/issue_plan` SKILL §選定条件 4 条件のうち以下 2 点を満たす:

1. **外部仕様・公式 docs の確認が主要成果に影響する** ✅ — Claude CLI が usage / cost を CLI invocation ごとにどの形式（stdout JSON / stderr / sidecar / API 経由）で emit するか、cache read/write をどう区別表示するか、`--output-format json` で `usage` フィールドが安定して得られるか、は `costs.py` の取得経路 / parse 戦略を**根本から決める**。事前確認なしに実装すると `costs.py` を書き直す risk が大きい
2. **軽い隔離環境（`experiments/` 配下）での試行が前提** ✅ — usage 抽出の検証は短い prompt の `claude -p` を `experiments/cost-usage-capture/` 配下で実行し、JSON 構造のサンプルを採取する想定

`full` で十分とする選択肢もあったが（FEEDBACKS handoff §次ループで試すこと §2 で指摘）、上記 1 が「主要成果に影響」レベルの不確実性を持つため、`research` の追加 step（`research_context` / `experiment_test`）の cost を払うほうが、後段 `imple_plan` / 実装での手戻り risk を下げる。判断境界が微妙な選択（ver16.1 RETROSPECTIVE §3.5 保留メモでも「初走 1 サンプル」だった `research_context` / `experiment_test` の差分観察素材にもなる）であることは PLAN_HANDOFF にも記す。

## 事前リファクタリング要否

**不要**（PLAN_HANDOFF.md §後続 step への注意点 で根拠を補足）。`logging_utils.py` の現状構造に cost 関連の整形 API を追加していく自然増分で済み、既存 deferred execution / workflow 分岐との整合は付く見込み。事前 REFACTOR は走らせず、`/split_plan` 段階で `REFACTOR.md` 判定（必要なら最小手）に委ねる。
