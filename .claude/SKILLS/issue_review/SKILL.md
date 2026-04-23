---
name: issue_review
description: plan ステップの冒頭で ISSUES/{カテゴリ}/ の review/ai 課題を走査し、ready/ai または need_human_action/human に振り分ける
disable-model-invocation: true
user-invocable: true
---

## 位置づけ

- `/issue_plan` の「準備」節で呼ばれる共通手順の**一次資料**
- 実運用上は `issue_plan/SKILL.md` に手順をインライン展開して組み込む（SKILL チェーン起動の不確実性を避けるため）
- 本ファイルは仕様書として保守し、呼び出し元と同期させること

## コンテキスト

- カテゴリ: !`cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app`
- 今日の日付: !`date +%Y-%m-%d`

## 処理

### 1. スキャン

対象: `ISSUES/{カテゴリ}/{high,medium,low}/*.md`

各ファイルの frontmatter を読み、以下で分類する:

- frontmatter 無し / YAML パース失敗 → `raw / human`（後方互換扱い、書き換えない）
- 既定値外の `status` / `assigned` → そのまま保持し、stderr に警告相当の注記
- `status: review` かつ `assigned: ai` → **レビュー対象**

### 2. 個別レビュー

レビュー対象のファイルを 1 件ずつ開き、**必ず Read で全文取得してから Edit する**。

判定基準:

| ケース | 判定条件 | 遷移先 |
|---|---|---|
| 記述が具体的 | 再現手順 / 期待動作 / 影響範囲の 3 点のうち 2 点以上が読み取れる | `status: ready`, `assigned: ai` |
| 人間対応が必要 | 再現確認 / 秘密値取得 / 仕様確認 / 外部サービスへのログイン等を伴う | `status: need_human_action`, `assigned: human` |
| 記述が粗すぎる | 本文が数行のメモで、何を検証すべきか曖昧 | `status: need_human_action`, `assigned: human` |

どのケースでも `reviewed_at: "{本日}"` を追加する（**文字列クオート推奨**。`yaml.safe_load` が `datetime.date` に変換するのを避けるため。集計側は `str()` で吸収するが、将来の互換性のためクオート運用とする）。

### 3. 書き換えのガード

- 書き換え前に必ず `Read` で全文取得し、改行コード（CRLF/LF）と frontmatter 境界 (`---`) を確認する
- `Edit` の `old_string` は frontmatter ブロック全体（`---` から `---` まで）を含める。`new_string` も同じ改行で組み立てる
- 1 セッション内で同じファイルを 2 回以上書き換えない
- `## AI からの依頼` セクションは、既存であれば置換、無ければ本文末尾に追記
- git にコミット済みの状態から書き換える前提。誤変更は `git checkout -- <path>` で復旧

### 4. `## AI からの依頼` の書式

`need_human_action / human` に遷移させた場合、本文末尾に以下を追記または置換する:

```markdown
## AI からの依頼

- {具体的な依頼 1}
- {具体的な依頼 2}
- …（最大 5 件）
```

- 依頼は最大 5 件まで
- 同一観点の依頼を繰り返さない
- 前回も `need_human_action` に戻された履歴がある場合は、依頼の表現を質的に変える（同じ文言を再掲しない）

### 5. サマリ報告

plan 本文に以下の 2 ブロックを `##` 見出しとして残す:

```markdown
## ISSUE レビュー結果

- ready/ai に遷移: {件数}（{対象パス一覧}）
- need_human_action/human に遷移: {件数}（{対象パス一覧}）
- 追記した `## AI からの依頼`: {件数}

## ISSUE 状態サマリ

| status / assigned | 件数 |
|---|---|
| ready / ai | {n} |
| review / ai | {n} |
| need_human_action / human | {n} |
| raw / human | {n} |
| raw / ai | {n} |
```

分布は `python scripts/issue_status.py {カテゴリ}` の出力を基にするか、スキャン結果から直接集計する。

## 呼び出し元との同期

本 SKILL の仕様変更時は、以下 1 箇所もあわせて更新すること:

- `.claude/skills/issue_plan/SKILL.md` — 「準備」セクション末尾の ISSUE レビューフェーズ手順

同 SKILL には「仕様の詳細は `.claude/skills/issue_review/SKILL.md` を参照」の一文を添え、同期を促す。
