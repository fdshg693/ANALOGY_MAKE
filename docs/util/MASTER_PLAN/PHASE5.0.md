# PHASE5.0: ISSUE ステータス管理

## 概要

`ISSUES/{category}/{priority}/{issue}.md` のフロントマターで状態を管理し、「人間が書きかけ」「AI による詳細化待ち」「情報不足」「着手可能」を明示する。`/split_plan` / `/quick_plan` の冒頭で `status: review` の ISSUE を拾って詳細化・追加情報要求を行い、`ready` のものだけを着手対象として扱う。

## 動機

- 現状、ISSUE はファイル名と本文のみで管理されており、「書きかけ」「完成」「要追加調査」の区別がない
- 人間が雑にメモした ISSUE をそのまま plan ステップが拾うと、情報不足のまま実装方針が決まってしまう
- 逆に、完成度の高い ISSUE と走り書きが同じ優先度フォルダに並ぶため、着手対象の選定が難しい
- AI による詳細化フェーズを挟むことで、人間は雑にメモし、AI が必要な問い返しと構造化を行う、という分業を実現したい

## 前提条件

- PHASE3.0 が実装済み（`/split_plan` / `/quick_plan` が存在）
- PHASE4.0 の実装有無は問わない（独立に進められる）

## ステータス遷移

```
（新規作成、frontmatter なし）
          │
          ▼
        raw ────────── 人間が書きかけ（デフォルト）
          │
          │ 人間が手動で review に書き換え
          ▼
        review ─────── AI による詳細化待ち
          │
   ┌──────┴───────┐
   │              │
   ▼              ▼
 ready          need_info
 着手可能       AIが追加情報を要求中
                  │
                  │ 人間が追記して review に戻す
                  ▼
                review（再度 AI が評価）
```

- `status` フィールドなし or `raw`: 人間が作成中。plan ステップは一切触れない
- `status: review`: plan ステップの冒頭で AI が評価・詳細化し、`ready` か `need_info` に遷移させる
- `status: need_info`: AI が追加情報を要求中。ファイル末尾に `## AI からの質問` セクションが追記されている。人間が回答を追記し `status: review` に手動で戻すことで再評価される
- `status: ready`: 着手対象。plan ステップが ISSUE 選定時に参照する
- ステータスを `review` に進めるのは常に人間の手動操作（AI は勝手に raw → review しない）

## フロントマター仕様

```yaml
---
status: ready            # raw | review | ready | need_info
priority: high           # high | medium | low（ファイル配置と冗長だが、移動検知のために記録）
reviewed_at: 2026-04-22  # 最後に AI が評価した日付（review 以降で記録、任意）
---

# ISSUE タイトル

本文...

## AI からの質問   ← need_info 時のみ、AI が追記
- 〇〇の想定利用頻度は？
- △△の既存実装はあるか？
```

- `status` のみ必須。他フィールドは任意
- フロントマターなしのファイルは `status: raw` として扱う（完全後方互換）

## やること

### 1. `/split_plan` / `/quick_plan` 冒頭への組み込み

両 SKILL の「現状把握」ステップの前に、以下のフェーズを追加する:

#### 1-1. ISSUE スキャン

- `ISSUES/{category}/{high,medium,low}/*.md` を走査し、frontmatter をパース
- `status: review` のファイル一覧を取得

#### 1-2. review 対象の詳細化

`status: review` のファイルごとに、以下のいずれかを実施:

- **問題なし → `ready` へ遷移**: ISSUE の記述が具体的で、再現手順・期待動作・影響範囲が読み取れる場合
  - frontmatter を `status: ready`, `reviewed_at: {今日}` に書き換え
  - 必要に応じて本文を構造化（見出し追加・箇条書き整理）
- **情報不足 → `need_info` へ遷移**: 再現手順不明、影響範囲不明、そもそも何がしたいか曖昧など
  - frontmatter を `status: need_info`, `reviewed_at: {今日}` に書き換え
  - 本文末尾に `## AI からの質問` セクションを追記し、具体的な質問を列挙
  - **質問粒度**: 答えれば詳細化可能なレベルまで具体化する（「もう少し詳しく」は NG）

#### 1-3. 結果のサマリ報告

review フェーズの結果をサマリ出力する:

```
[ISSUE レビュー結果]
- ready に遷移: 2 件（ISSUES/util/high/foo.md, ISSUES/app/medium/bar.md）
- need_info に遷移: 1 件（ISSUES/app/low/baz.md — 3 件の質問を追記）
```

#### 1-4. ready な ISSUE のみから着手対象を選定

既存の「ISSUES/{カテゴリ}/high/ を優先的に参照」ロジックを、**`status: ready` のもののみを対象**とするように変更:

- `high/` に `ready` があれば優先
- `high/` に `ready` がなければ `medium/` の `ready` を対象
- `ready` がどこにも無い場合のみ MASTER_PLAN の次項目に進む
- `review` / `need_info` / `raw` は着手対象外（サマリでは触れるが選定しない）

### 2. レビューロジックの共通化

`/split_plan` と `/quick_plan` で重複が生じるため、共通 SKILL として切り出す:

`.claude/SKILLS/issue_review/SKILL.md`:
- 入力: カテゴリ名
- 処理: 上記 1-1〜1-3 を実行
- 出力: ready/need_info の件数と対象ファイル一覧

`/split_plan` / `/quick_plan` はこの SKILL を冒頭で呼び出す形に変更する。

### 3. ヘルパースクリプト（任意）

人間が ISSUE を大量にレビューに回したいとき用に、一括で `raw` → `review` に進めるスクリプトは **用意しない**（手動編集を徹底したほうが意図せぬレビュー開始を防げる）。

代わりに、現在のステータス分布を確認するスクリプトのみ用意する:

`scripts/issue_status.py`:
- カテゴリ指定で `ISSUES/{category}/` 配下の全 ISSUE のステータス分布を出力
- 例:
  ```
  util:
    high:    ready=1, review=0, need_info=0, raw=2
    medium:  ready=0, review=1, need_info=1, raw=0
    low:     ready=0, review=0, need_info=0, raw=3
  ```

### 4. 既存 ISSUE のマイグレーション

現存する ISSUE ファイル（`ISSUES/**/*.md`）にはフロントマターが無い。移行方針:

- **既存ファイルは触らない**: フロントマター無し = `status: raw` 扱いなので、着手対象外になる
- ユーザーが手動で各 ISSUE を確認し、完成しているものは `status: ready` を付ける
- 雑なメモは `status: review` を付けて AI にレビューさせる

マイグレーションガイドを `docs/util/ver5.0/MIGRATION.md` として別途用意する。

### 5. ドキュメント整備

- `.claude/SKILLS/split_plan/SKILL.md`: 冒頭 ISSUE レビューフェーズの説明を追記
- `.claude/SKILLS/quick_plan/SKILL.md`: 同上
- `.claude/SKILLS/issue_review/SKILL.md`: 新規作成
- プロジェクト直下 `ISSUES/README.md`: フロントマター仕様・ステータス遷移の説明を新規作成

## ファイル変更一覧

| ファイル | 操作 | 内容 |
|---|---|---|
| `.claude/SKILLS/issue_review/SKILL.md` | 新規作成 | ISSUE レビュー共通 SKILL |
| `.claude/SKILLS/split_plan/SKILL.md` | 変更 | 冒頭で `/issue_review` 呼び出し・ready 絞り込み |
| `.claude/SKILLS/quick_plan/SKILL.md` | 変更 | 同上 |
| `ISSUES/README.md` | 新規作成 | フロントマター仕様書 |
| `scripts/issue_status.py` | 新規作成 | ステータス分布確認スクリプト |
| `docs/util/ver5.0/MIGRATION.md` | 新規作成 | 既存 ISSUE の手動移行ガイド |
| `docs/util/ver5.0/` | 新規作成 | ROUGH_PLAN / IMPLEMENT / CURRENT / MEMO |

## リスク・不確実性

- **フロントマターパースの揺れ**: YAML パーサの差異でエラーになる可能性。`python scripts/issue_status.py` では `yaml.safe_load` を使い、失敗時は `raw` 扱いにフォールバック
- **SKILL 内でのファイル編集**: `/split_plan` は SKILL 実行 = AI 主導のため、frontmatter 書き換えを AI が正しく行えるかは実装後に検証が必要。誤書き換え防止のため、書き換え前に対象ファイルを全件 Read で読んでから Edit する手順を SKILL 内に明記する
- **need_info ループ**: AI の質問が的外れだと、人間が回答しても再度 need_info に戻される可能性。SKILL 内で「質問は最大 5 件まで、同じ観点の質問を繰り返さない」などのガードを明記する

## やらないこと

- ステータスの自動遷移（`raw` → `review` は必ず人間の手動操作）
- CI での ISSUE フォーマットチェック（ローカル運用のみ、GitHub Actions での検査は対象外）
- 過去 ISSUE の一括マイグレーション（ユーザーが個別に `ready` を付ける運用）
- ステータス以外のメタデータ拡張（`assignee` や `estimated_hours` などは対象外）
- `done/` への自動移動（解決済み ISSUE の削除は従来どおり `quick_doc` / `wrap_up` が担当）
