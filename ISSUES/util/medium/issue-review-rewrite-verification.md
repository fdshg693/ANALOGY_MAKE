---
status: ready
assigned: ai
priority: medium
reviewed_at: "2026-04-23"
---
# issue_review SKILL の書き換えロジック実動作確認（ver6.0 持ち越し）

## 概要

ver6.0 で導入した `issue_review` SKILL の frontmatter 書き換えロジック（`review / ai` → `ready / ai` または `need_human_action / human`）は、util カテゴリに `review / ai` の ISSUE が存在しなかったため、ver6.0 imple_plan 中に実動作確認できていない。初回実運用は次回 `app` / `infra` カテゴリで `/split_plan` / `/quick_plan` を起動したタイミングに持ち越しとなる。

## 本番発生時の兆候

- ISSUE ファイルの frontmatter が壊れる（`---` 境界の崩れ / YAML パース不能）
- 本文の一部が frontmatter 側に巻き込まれる
- CRLF / LF の混在で Edit の `old_string` マッチに失敗する
- `## AI からの依頼` セクションが重複追記される

## 対応方針

1. 次回 `app` または `infra` カテゴリで `/split_plan` / `/quick_plan` を起動した際、ISSUE レビューフェーズの挙動を目視確認する（サマリ出力 + `git diff ISSUES/` を確認）
2. 書き換え対象のファイル（`ISSUES/app/medium/*.md` の `review / ai` 3 件 + `ISSUES/infra/high/Windowsデプロイ.md` 1 件）
3. 異常が見つかった場合は `git checkout -- <path>` で復旧し、`issue_review/SKILL.md` のガード条項を強化
4. 実動作確認が無事通過したら、本 ISSUE を `done/` へ移動

## 影響範囲

`ISSUES/` 配下のファイルのみ。アプリ本体・インフラには波及しない。git 管理下のため失敗しても復旧可能。

## 参考

- `docs/util/ver6.0/MEMO.md` §R2
- `.claude/skills/issue_review/SKILL.md` §3 書き換えのガード
- `docs/util/MASTER_PLAN/PHASE5.0.md` リスク §SKILL 内でのファイル編集
