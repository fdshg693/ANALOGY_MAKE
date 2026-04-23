# ISSUES ディレクトリ運用ガイド

このディレクトリは、アプリ本体・インフラ・CI/CD・ユーティリティ横断で発生した課題（バグ・改善要望・調査メモ）を保管する場所です。
plan ステップ（`/split_plan` / `/quick_plan`）は、ここに置かれた ISSUE のうち **「着手可能」と判定されたもの** だけを拾い上げて実装計画に取り込みます。そのための成熟度ラベルとしてフロントマターを使います。

## ディレクトリ構造

```
ISSUES/
├── {category}/               # app | infra | cicd | util
│   ├── high/
│   ├── medium/
│   └── low/
└── README.md                 # 本ファイル
```

- `{category}` は `.claude/CURRENT_CATEGORY` と同じ区分
- `high` / `medium` / `low` のサブディレクトリで優先度を区別する
- 対応済み ISSUE は `wrap_up` / `quick_doc` 時に `done/` 配下へ移動する（自動化は ver6.0 スコープ外）

## フロントマター仕様

各 ISSUE ファイルの先頭に YAML frontmatter を置きます。

```markdown
---
status: ready
assigned: ai
priority: medium
reviewed_at: "2026-04-23"
---
# タイトル

本文…
```

### フィールド定義

| フィールド | 必須 | 値 | 意味 |
|---|---|---|---|
| `status` | ✅ | `raw` / `review` / `ready` / `need_human_action` | ISSUE の成熟度 |
| `assigned` | ✅ | `human` / `ai` | 次アクションの担当 |
| `priority` | 任意 | `high` / `medium` / `low` | ディレクトリと一致させる（冗長情報だが読解補助） |
| `reviewed_at` | 任意 | `"YYYY-MM-DD"` 形式の文字列 | 直近のレビュー日。**文字列としてクオート推奨**（YAML の date 自動変換を避けるため） |

### 許可される `status × assigned` の組み合わせ

| 組み合わせ | 意味 | 誰が付ける |
|---|---|---|
| `raw / human` | 人間の書きかけメモ。plan ステップは拾わない | 人間 |
| `raw / ai` | AI 側の未整理メモ（深掘り前のラフ起票） | AI |
| `review / ai` | 人間 → AI へのレビュー依頼。次回 plan 冒頭で `issue_review` が処理する | 人間 |
| `ready / ai` | 着手可能。plan ステップの拾い上げ対象 | 人間 / AI |
| `need_human_action / human` | AI では判断不能 / 対応不能。人間の情報提供・操作を待つ | AI（レビュー結果として） |

不正組み合わせ（例: `need_human_action / ai`, `review / human`, `ready / human`）は使わない。`issue_status.py` は不正な組み合わせを検出したら警告を出します。

## ライフサイクル

### 人間が起票するパス

1. ざっくりメモとして `raw / human` で置く（または frontmatter 無し。後者は後方互換として `raw / human` 扱い）
2. AI の整理を借りたくなったら `review / ai` に書き換えて次回 plan 起動を待つ
3. `issue_review` SKILL が `review / ai` を走査し、以下のいずれかに遷移させる
   - 記述が具体的 → `ready / ai`（着手可能）
   - 情報不足 / 人間対応必要 → `need_human_action / human`（本文末尾に `## AI からの依頼` を追記）
4. 人間が `need_human_action / human` に回答 → 再度 `review / ai` に戻して次サイクルへ
5. 実装が完了したら `done/` へ移動

### AI が起票するパス

AI は `raw | ready | need_human_action` のいずれかのみを付けます。**`review` は AI からは付けない**（`review` は人間 → AI のレビュー依頼専用に予約されている）。

| シーン | 付けるラベル |
|---|---|
| 調査中に拾った粗い観察 | `raw / ai` |
| 実装方針まで自力で確定できた小タスク | `ready / ai` |
| 人間の情報提供が必須 | `need_human_action / human` |

## 人間への依頼セクション

`need_human_action` の ISSUE は、本文末尾に以下のセクションが追記されます。

```markdown
## AI からの依頼

- ✅ 再現手順を教えてください: 具体的な操作ステップ / 期待と実際の差分
- ✅ 秘密値が必要です: `XXX_API_KEY` を `.env.local` に追加してください
- ✅ 仕様確認: この挙動は意図通りですか？
```

- 依頼は最大 5 件まで
- 同一観点の繰り返し依頼は避ける
- 人間対応済みの回答を得たら `review / ai` に戻して再レビューへ

## 新規 ISSUE テンプレート

### 人間起票（書きかけメモ）

```markdown
---
status: raw
assigned: human
priority: low
---
# 〈タイトル〉

〈本文〉
```

### 人間起票（AI にレビューしてほしい）

```markdown
---
status: review
assigned: ai
priority: medium
---
# 〈タイトル〉

〈本文〉
```

### AI 起票（着手可能）

```markdown
---
status: ready
assigned: ai
priority: low
reviewed_at: "2026-04-23"
---
# 〈タイトル〉

〈本文〉
```

## 分布の確認

カテゴリごと・優先度ごとの `status × assigned` 件数は次のコマンドで確認できます。

```bash
python scripts/issue_status.py            # 全カテゴリ
python scripts/issue_status.py app        # カテゴリ指定
```

## 運用上の注意

- `raw / ai` は AI 側の未整理メモのため、放置するとノイズ化します。定期的に `python scripts/issue_status.py` で分布を眺め、長期滞留している `raw / ai` は再整理するか削除してください
- `reviewed_at` は文字列としてクオート推奨（`"2026-04-23"`）。クオートしないと YAML パース時に `datetime.date` になり、一部ツールで扱いが変わります（`issue_status.py` 側では `str()` で吸収していますが、将来の拡張を楽にするためクオート運用を推奨）
- 本ファイルの仕様と `.claude/skills/issue_review/SKILL.md` の判定基準は常に同期させること
