# ISSUES ディレクトリ運用ガイド

このディレクトリは、アプリ本体・インフラ・CI/CD・ユーティリティ横断で発生した課題（バグ・改善要望・調査メモ）を保管する場所です。
plan ステップ（`/issue_plan`）は、ここに置かれた ISSUE のうち **「着手可能」と判定されたもの** だけを拾い上げて実装計画に取り込みます。そのための成熟度ラベルとしてフロントマターを使います。

## REQUESTS からの移行経緯（ver13.0）

ver12.x 以前は `REQUESTS/AI/` / `REQUESTS/HUMAN/` ディレクトリで「ワークフローから人間への依頼」や「人間から AI への依頼」を扱っていましたが、ver13.0 で本ディレクトリに集約しました。

- **AI から人間への依頼**（旧 `REQUESTS/AI/`） → `ISSUES/{カテゴリ}/{優先度}/*.md` を新規作成し、frontmatter に `assigned: human` / `status: need_human_action` を指定する
- **人間から AI への依頼**（旧 `REQUESTS/HUMAN/`） → 従来通り frontmatter に `assigned: ai` / `status: ready` を付与する（`raw` で書き始めて `review` → `ready` と成熟させる運用も同じ）

これにより「依頼の置き場所」が ISSUES 1 系統に統一され、`issue_status.py` / `issue_worklist.py` で担当別に一覧できるようになります。

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

**`issue_scout`（`--workflow scout`）による能動起票の既定値**（ver15.0 追加）:

- **原則 `raw / ai`** で起票する（ノイズ抑制のため）
- 以下 3 点をすべて満たす小粒のみ `ready / ai` への昇格を許可:
  - 症状の再現条件がファイルパス + 具体操作で書ける
  - 影響範囲が 3 ファイル / 100 行以内で見積もれる
  - 修正方向が `IMPLEMENT.md` なしで 1 段落で書ける
- 起票件数は 1 run あたり最大 3 件（価値ある候補がなければゼロ起票で終了）

### 長期持ち越し再判定（ver16.5 追加）

`status: ready / ai` のまま長期間（既定 7 日）着手されない ISSUE を `issue_review` SKILL が「再判定推奨」として検出します。検出条件と挙動:

- 検出条件: `reviewed_at` フィールドが本日から 7 日以上前
- 検出時の挙動: `/issue_plan` の出力に「## 再判定推奨 ISSUE」ブロックが追加される。frontmatter は書き換えられない
- 想定される人間 / AI の対応:
  - 実機検証が必要なものは手動で `need_human_action / human` に降格する
  - 前提条件待ち（他カテゴリでの `review/ai` 発生待ち等）のものは `ready/ai` を維持しつつ `## AI からの依頼` に補足を追記する
  - 状況が変わって再判断したい場合は手動で `review/ai` に戻し、次回 `/issue_plan` で再評価させる
- 詳細仕様は `.claude/skills/issue_review/SKILL.md` §1.5 / §5 を参照

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
