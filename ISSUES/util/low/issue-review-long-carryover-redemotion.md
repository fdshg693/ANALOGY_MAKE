---
status: raw
assigned: ai
priority: low
reviewed_at: "2026-04-24"
---

# ready/ai 長期持ち越し ISSUE の再判定ルートを issue_review SKILL に追加

## 概要

`issue_review` SKILL は現状 `status: review / ai` のみをレビュー対象にしているため、`ready / ai` の ISSUE が複数バージョンに渡り着手されないまま持ち越される構造問題を検出できない。本 ISSUE では、`ready / ai` かつ `reviewed_at` が N バージョン以上前の ISSUE を検出・再判定する「長期持ち越し再判定ルート」を `issue_review` SKILL に追加する設計提案を記す。本 ISSUE 自体は設計提案の書き起こし段階であり、次回 `/issue_plan` の review フェーズで `review / ai` 経由 `ready / ai` に昇格させ、その先の版で SKILL 本体を拡張する 3 ステップ運用を想定する。

## 背景（ver16.3 handoff 経由）

ver16.2 → ver16.3 の handoff（`docs/util/ver16.2/` retrospective および FEEDBACKS）で、`/issue_plan` SKILL のレビューフェーズは `review / ai` のみを対象にし、`ready / ai` の長期停滞を検出・降格できない仕様が構造問題として明示された。実例として util カテゴリには 5 バージョン連続持ち越しとなっている次の 2 件が存在する:

- `ISSUES/util/medium/issue-review-rewrite-verification.md` — ver6.0 以来、util 単独の AI self-consume では `review / ai` の ISSUE を用意できず書き換えロジックの実動作確認が止まっている
- `ISSUES/util/low/toast-persistence-verification.md` — Windows 実機目視必須で AI self-consume 不能

さらに ver16.3 ROUGH_PLAN.md §ISSUE 状態サマリでは `ready / ai` 3 件中 2 件が長期持ち越しと記録されており、本 ISSUE 起票は handoff の「`issue_review` SKILL 側で拡張する ISSUE 起票を次ループで検討する」指示への応答となる。

## 対応方針（設計提案）

本 ISSUE が解決経路の布石となる SKILL 拡張の設計提案を 3 要素に分けて記す。実装は別版で行う。

### 1. スキャン対象の拡張

現 `issue_review` SKILL は `status: review / ai` のみを走査する。拡張後は「`status: ready / ai` かつ `reviewed_at` が N バージョン以上前」も検出対象に含める。`reviewed_at` は ISO 日付（`YYYY-MM-DD`）で記録されているため、カレントバージョンの着手日との差を「バージョン数」相当に換算するか、あるいは「連続して `/issue_plan` の候補に挙がったが着手されなかった回数」をカウントするメタ情報の追加を検討する。

### 2. しきい値の 2 段階

- **5 バージョン連続持ち越し** = 「要再判定」警告フラグ。SKILL は当該 ISSUE の frontmatter には手を入れず、`/issue_plan` の出力サマリに「再判定推奨」欄を追加して人間 / AI に判断を促す
- **10 バージョン連続持ち越し** = 「強制降格」アクション。SKILL は当該 ISSUE を `need_human_action / human` に降格し、`## 降格理由（自動）` セクションを追記する

段階化により、持ち越し初期は運用判断に委ね、極端な放置状態のみ機械的に降格させる設計とする。

### 3. 判定ルート

「実装着手されていない理由」を 2 系統で判別する:

- **実機検証を要する** → `need_human_action / human` に降格する。対象例: `toast-persistence-verification`（Windows 実機目視必須）
- **AI 作業で消化可能** → `ready / ai` を維持し、`## AI からの依頼` セクションに「なぜ着手されなかったか」の追加ヒント（前提条件の発生待ち等）を残す。対象例: `issue-review-rewrite-verification`（他カテゴリでの `review / ai` 発生待ち）

判別の自動化は難しいため、初回実装は「持ち越し理由の候補を列挙するテンプレート」を `/issue_plan` 出力に含めるだけに留め、最終判断は人間または `/issue_plan` の LLM 判断に委ねる設計が現実的。

## 影響範囲

SKILL 拡張時（将来版）に触れるファイル:

- `.claude/skills/issue_review/SKILL.md` — 本体拡張。スキャン対象・しきい値・判定ルートの 3 要素を追記
- `.claude/skills/issue_plan/SKILL.md` — `issue_review` SKILL をインライン展開している箇所（SKILL.md 末尾「呼び出し元との同期」節の原則により、`issue_review` 側の拡張と同期が必須）
- `ISSUES/README.md` — ライフサイクル節に「長期持ち越し再判定」フロー図 / 説明を追加

本 ISSUE 起票時点（本版）では上記いずれにも変更を加えない。

## 関連資料

- `docs/util/ver16.3/ROUGH_PLAN.md` §B（長期持ち越し ready/ai 再判定手順の新規 ISSUE 起票）
- `docs/util/ver16.3/PLAN_HANDOFF.md` §「`/split_plan`」（ISSUE の節立て指定）
- `docs/util/ver16.2/FEEDBACKS/` 該当 handoff（handoff 発端元）
- `ISSUES/util/medium/issue-review-rewrite-verification.md`（5 バージョン連続持ち越しの代表例）
- `ISSUES/util/low/toast-persistence-verification.md`（5 バージョン連続持ち越しの代表例）
