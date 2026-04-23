# ver6.0 MIGRATION: ISSUE フロントマター移行ガイド

ver6.0 で導入した `status` / `assigned` フロントマター仕様（詳細は `ISSUES/README.md`）に対する、既存 ISSUE ファイルの移行指針。

## 移行状況（ver6.0 着手時点）

`ISSUES/**/*.md` 配下の全 8 ファイルは、**既に本仕様の frontmatter を保持済み**。追加の一括マイグレーションは不要。

| ファイル | status | assigned |
|---|---|---|
| `ISSUES/app/low/db-connection-refactor.md` | ready | ai |
| `ISSUES/app/low/syntax-highlight.md` | ready | ai |
| `ISSUES/app/low/vitest-nuxt-test-utils.md` | ready | ai |
| `ISSUES/app/medium/additional-kwargs-sqlite.md` | review | ai |
| `ISSUES/app/medium/fork-checkpoint-verification.md` | review | ai |
| `ISSUES/app/medium/getState-timing.md` | review | ai |
| `ISSUES/infra/high/Windowsデプロイ.md` | review | ai |
| `ISSUES/infra/low/action_warning.md` | ready | ai |

`util` / `cicd` カテゴリには ISSUE が存在しない（`.gitkeep` のみ）。

## 将来 frontmatter 無しファイルが登場した場合の手順

ver6.0 では後方互換として、frontmatter 無しファイルは `raw / human` 扱いで plan ステップの着手対象外となる。意図的にそのまま残したい場合は何もしなくてよい。整理したい場合は以下のいずれかを付与する。

### パターン1: 着手可能と判断できる

記述が具体的（再現手順 / 期待動作 / 影響範囲が読み取れる）で、AI が単独で計画に落とし込める。

```markdown
---
status: ready
assigned: ai
priority: low   # ディレクトリと一致させる
---
```

### パターン2: AI に整理・判断を任せたい

情報はあるが粒度がまちまちで、AI 側の判断で `ready` / `need_human_action` に振り分けてほしい。

```markdown
---
status: review
assigned: ai
priority: medium
---
```

次回 `/split_plan` または `/quick_plan` 起動時の **ISSUE レビューフェーズ** で自動的に処理される。

### パターン3: 書きかけメモとして温存

結論を出せる段階ではないが、着想として残しておきたい。

- 何もしない（frontmatter 無しのまま）= `raw / human` 扱い、着手対象外
- 明示的にラベルしたい場合は `status: raw`, `assigned: human` を付与

## AI が新規 ISSUE を起票する際のテンプレート

### AI raw（調査中の観察メモ）

```markdown
---
status: raw
assigned: ai
priority: low
---
# 〈観察タイトル〉

〈未整理メモ〉
```

### AI ready（着手可能まで整理済み）

```markdown
---
status: ready
assigned: ai
priority: low
reviewed_at: "2026-04-23"
---
# 〈タイトル〉

## 概要

## 本番発生時の兆候

## 対応方針

## 影響範囲
```

### AI → human（人間の対応待ち）

```markdown
---
status: need_human_action
assigned: human
priority: medium
reviewed_at: "2026-04-23"
---
# 〈タイトル〉

〈本文〉

## AI からの依頼

- 〈具体的な依頼〉
```

## 参考

- 仕様詳細: `ISSUES/README.md`
- レビュー手順: `.claude/skills/issue_review/SKILL.md`
- 分布確認: `python scripts/issue_status.py [category]`
