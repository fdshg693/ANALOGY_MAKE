---
name: issue_review
description: plan ステップの冒頭で ISSUES/{カテゴリ}/ の review/ai 課題を振り分け、ready/ai 長期持ち越し ISSUE を再判定推奨として一覧する
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

### 1.5. 長期持ち越し ready/ai の検出（追加スキャン）

§1 と並行して、`status: ready` かつ `assigned: ai` のファイルも走査し、以下条件を満たすものを「再判定推奨」として §5 第 3 ブロックに列挙する:

- `reviewed_at` フィールドが存在し、かつ本日日付との差分が **7 日以上**
- `reviewed_at` 欠落 ISSUE は対象外（未判定として除外）
- 閾値 7 日は SKILL 内の既定値。運用観察で過敏 / 過鈍と判断された場合のみ後続版で調整

**注: 本ルートで検出した ISSUE の frontmatter は一切書き換えない。サマリ報告（§5 第 3 ブロック）への追記のみ。**

`reviewed_at` の意味論補足:
- `reviewed_at` は §2 個別レビュー時に更新される。`ready/ai` に昇格後は §1 の「review/ai 検出」対象から外れるため、再度 `review/ai` に戻して再判定するまで `reviewed_at` は固定される
- したがって「`reviewed_at` が 7 日以上前」=「直近 7 日間、`ready/ai` で誰も再判断していない」と読める
- 持ち越し ISSUE を再判断したい場合は人間 / AI が `ready/ai` → `review/ai` に戻し（または `need_human_action` に降格し）、次回 `/issue_plan` で再評価させる運用となる

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
- **長期持ち越し ISSUE の frontmatter は書き換えない**: §1.5 で検出した `ready/ai` 長期持ち越し ISSUE は、§5 第 3 ブロックに列挙するのみで `status` / `assigned` / `reviewed_at` の書き換えを発生させない。降格 / 再判定の最終操作は人間 / AI の手動判断に委ねる

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

plan 本文末尾に以下の第 3 ブロックを追加する:

```markdown
## 再判定推奨 ISSUE

長期持ち越し閾値（既定 7 日）を超えた `ready/ai` ISSUE。frontmatter 未変更、判断は人間 / AI に委ねる:

- `{path}` — reviewed_at: {YYYY-MM-DD}（{N} 日経過）
  - 候補理由 A: 実機検証が必要 → `need_human_action / human` に降格を検討
  - 候補理由 B: 前提条件待ち（他カテゴリでの review/ai 発生待ち等）→ `ready/ai` のまま `## AI からの依頼` に補足追記を検討
```

該当ゼロの場合は以下 1 行で済ませる:

```markdown
## 再判定推奨 ISSUE

該当なし（`ready/ai` で 7 日以上停滞している ISSUE はない）。
```

候補理由 A / B はテンプレート固定文。判別自動化は本 SKILL では行わず、最終判断は人間 / `/issue_plan` 側の LLM に委ねる。

分布は `python scripts/issue_status.py {カテゴリ}` の出力を基にするか、スキャン結果から直接集計する。

## 呼び出し元との同期

本 SKILL の仕様変更時は、以下 1 箇所もあわせて更新すること:

- `.claude/skills/issue_plan/SKILL.md` — 「準備」セクション末尾の ISSUE レビューフェーズ手順

同 SKILL には「仕様の詳細は `.claude/skills/issue_review/SKILL.md` を参照」の一文を添え、同期を促す。
