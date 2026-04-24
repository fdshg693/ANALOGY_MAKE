# QUESTIONS ディレクトリ運用ガイド

このディレクトリは、**実装ではなく調査**を依頼する Question を保管する場所です。`question_research` SKILL（`--workflow question`）の専属 queue として動作し、`auto` / `full` / `quick` / `scout` 等の他ワークフローからは走査されません。

「実装してほしい依頼」は引き続き `ISSUES/` に置いてください。**成果物が報告書（`docs/{category}/questions/{slug}.md`）になるもの** だけを QUESTIONS/ に置きます。

## 配置ルール

```
QUESTIONS/
├── {category}/               # app | infra | cicd | util
│   ├── high/
│   ├── medium/
│   ├── low/
│   └── done/                 # 完了 Question の退避先
└── README.md                 # 本ファイル
```

- `{category}` は `.claude/CURRENT_CATEGORY` と同じ区分
- `high` / `medium` / `low` のサブディレクトリで優先度を区別する
- 調査が完了したら `done/` 配下へ移動する（`question_research` SKILL の後処理ルール参照）

## frontmatter 仕様

各 Question ファイルの先頭に YAML frontmatter を置きます。

```markdown
---
status: ready
assigned: ai
priority: medium
reviewed_at: "2026-04-24"
---
# タイトル

問いの内容…
```

### フィールド定義

| フィールド | 必須 | 値 | 意味 |
|---|---|---|---|
| `status` | ✅ | `raw` / `ready` / `need_human_action` | Question の成熟度（**`review` は持たない** — `ISSUES/` との差分） |
| `assigned` | ✅ | `human` / `ai` | 次アクションの担当 |
| `priority` | 任意 | `high` / `medium` / `low` | ディレクトリと一致させる |
| `reviewed_at` | 任意 | `"YYYY-MM-DD"` 形式の文字列 | 直近のレビュー日 / AI ready 化日。**Question の "調査完了日" ではない**（調査完了日は報告書側に記載する） |

### 許可される `status × assigned` の組み合わせ

| 組み合わせ | 意味 | 誰が付ける |
|---|---|---|
| `raw / human` | 人間の書きかけ Question | 人間 |
| `raw / ai` | AI 側の未整理 Question | AI |
| `ready / ai` | 調査可能。`question_research` の拾い上げ対象 | 人間 / AI |
| `need_human_action / human` | 調査続行に人間の追加情報 / 権限が必要 | AI（調査結果として） |

不正な組み合わせ（例: `ready / human`, `need_human_action / ai`）は使わない。`question_status.py` は不正な組み合わせを検出したら警告を出します。

## ISSUES との境界

| 種別 | 置き場所 | 成果物 | ワークフロー |
|---|---|---|---|
| 実装依頼 | `ISSUES/` | コード変更 / docs 更新 | `auto` / `full` / `quick` / `issue_plan` |
| 調査依頼 | `QUESTIONS/` | 報告書（`docs/{category}/questions/{slug}.md`） | `question`（opt-in） |

判定フロー:

1. 「実装」が必要 → `ISSUES/` に置く
2. 「調査」が必要で、結論が出せれば良い → `QUESTIONS/` に置く
3. 調査の結論として実装が必要になった場合は、`question_research` SKILL が新規 ISSUE を `ISSUES/` に起票し、Question 本文末尾にリンクを残す

`auto` / `full` / `quick` / `scout` は `QUESTIONS/` を **読まない**。`question_research` のみが `QUESTIONS/` を走査します。`question` workflow は `--workflow auto` に自動混入しません（opt-in 専用）。

## 報告書の配置

調査結果は次のパスに Markdown で出力します。

```
docs/{category}/questions/{slug}.md
```

- `{slug}` は Question 本体のファイル名（拡張子なし）と一致させる
- 報告書は固定の 5 セクションで構成する: **問い** / **確認した証拠** / **結論** / **不確実性** / **次アクション候補**
- 詳細書式は `.claude/skills/question_research/SKILL.md` を一次資料とする

## 分布の確認

カテゴリごと・優先度ごとの `status × assigned` 件数は次のコマンドで確認できます。

```bash
python scripts/question_status.py            # 全カテゴリ
python scripts/question_status.py util       # カテゴリ指定
```

着手候補（`ready / ai`）の一覧:

```bash
python scripts/question_worklist.py --category util
python scripts/question_worklist.py --category util --format json
```

## 運用上の注意

- `raw / ai` は放置するとノイズ化します。定期的に `python scripts/question_status.py` で分布を眺めてください
- `reviewed_at` は文字列としてクオート推奨（`"2026-04-24"`）
- 結論不確実なケース（情報不足で判断保留 / 追加調査に外部権限が必要 等）は `done/` に移動せず、Question を `need_human_action / human` に戻して queue に残します（詳細は `question_research` SKILL）
