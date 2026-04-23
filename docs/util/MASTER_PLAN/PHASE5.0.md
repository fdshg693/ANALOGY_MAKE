# PHASE5.0: ISSUE ステータス・担当管理

## 概要

`ISSUES/{category}/{priority}/{issue}.md` のフロントマターで `status` と `assigned` を管理し、人間起票 / AI 起票のどちらでも「ISSUE の成熟度」と「次にボールを持つ主体」を明示する。`/split_plan` / `/quick_plan` の冒頭では `status: review` の ISSUE を AI が詳細化し、`ready` のものだけを着手対象として扱う。AI が新規 ISSUE を起票する場合は、起票時点で `raw` / `ready` / `need_human_action` のいずれかを付与する。

## 動機

- 現状、ISSUE はファイル名と本文のみで管理されており、「書きかけ」「完成」「追加対応待ち」の区別がない
- 人間が雑にメモした ISSUE をそのまま plan ステップが拾うと、情報不足のまま実装方針が決まってしまう
- AI が ISSUE を起票したい場面（不具合仮説、改善候補、要人手確認事項）を現行フローでは表現しにくい
- AI による詳細化フェーズと `assigned` による担当明示を導入し、人間と AI の受け渡しを明確にしたい

## 前提条件

- PHASE3.0 が実装済み（`/split_plan` / `/quick_plan` が存在）
- PHASE4.0 の実装有無は問わない（独立に進められる）

## ステータスと担当の意味

- `status`: ISSUE の成熟度、またはブロック理由を表す
- `assigned`: 現在その ISSUE に対して次のアクションを取るべき主体を表す
- `assigned` の値は `human` または `ai` のみ
- フロントマターなしの既存 ISSUE は `status: raw` かつ `assigned: human` として扱う

各状態の基本ルール:

- `raw`
  - まだ情報が粗い状態
  - `assigned: human`: 人間が書きかけ
  - `assigned: ai`: AI が気づきをメモしたが、まだ十分に整理できていない
- `review`
  - AI によるレビュー / 詳細化待ち
  - 常に `assigned: ai`
- `ready`
  - 着手可能
  - 原則 `assigned: ai`（次のアクションは plan / 実装フロー側）
- `need_human_action`
  - 人間にしかできない確認・回答・操作が必要
  - 常に `assigned: human`
  - 旧 `need_info` を置き換える。追加質問だけでなく、実機確認・秘密値取得・外部環境確認も含む

## ステータス遷移

### 人間が ISSUE を起票する場合

```
（新規作成、frontmatter なし）
         │
         ▼
raw / assigned: human
         │
         │ 人間が AI にレビューを依頼
         ▼
review / assigned: ai
         │
  ┌──────┴─────────────┐
  │                    │
  ▼                    ▼
ready / assigned: ai   need_human_action / assigned: human
着手可能               人間に追加対応が必要
                            │
                            │ 人間が対応し、再レビューに戻す
                            ▼
                      review / assigned: ai
```

### AI が ISSUE を起票する場合

AI は新規 ISSUE 作成時に、必ず次のいずれかで起票する:

```
AI が新規 ISSUE を作成
  ├─ raw / assigned: ai
  │    まだ仮説段階。AI 側で再整理が必要
  ├─ ready / assigned: ai
  │    そのまま着手候補にできる
  └─ need_human_action / assigned: human
       人間の確認・操作が必要
```

- AI 起票時に `review` では作成しない。`review` は「再レビュー依頼キュー」として使う
- AI 起票の `raw / assigned: ai` は未整理の仮説メモであり、着手対象ではない
- `need_human_action / assigned: human` に対して人間が対応した後、再評価が必要なら `review / assigned: ai` に戻す

## フロントマター仕様

```yaml
---
status: need_human_action  # raw | review | ready | need_human_action
assigned: human            # human | ai
priority: high             # high | medium | low（ファイル配置と冗長だが、移動検知のために記録）
reviewed_at: 2026-04-22    # 最後に AI が状態を確定 / 更新した日付（任意）
---

# ISSUE タイトル

本文...

## AI からの依頼   ← need_human_action 時のみ、AI が追記
- `pnpm dev` で対象画面を開き、期待どおり再現するか確認する
- `EXTERNAL_API_KEY` を取得できるか確認する
- 期待動作が A / B のどちらかを回答する
```

- フロントマターを持つ ISSUE では `status` と `assigned` をセットで必須とする
- `priority` と `reviewed_at` は任意
- フロントマターなしのファイルは `status: raw`, `assigned: human` として扱う（完全後方互換）
- `need_human_action` の本文追記セクション名は `## AI からの依頼` に統一する

## やること

### 1. `/split_plan` / `/quick_plan` 冒頭への組み込み

両 SKILL の「現状把握」ステップの前に、以下のフェーズを追加する:

#### 1-1. ISSUE スキャン

- `ISSUES/{category}/{high,medium,low}/*.md` を走査し、frontmatter をパース
- `status` と `assigned` の組み合わせを集計する
- `status: review` かつ `assigned: ai` のファイル一覧を取得する

#### 1-2. review 対象の詳細化

`status: review` のファイルごとに、以下のいずれかを実施:

- **問題なし → `ready / assigned: ai` へ遷移**: ISSUE の記述が具体的で、再現手順・期待動作・影響範囲が読み取れる場合
  - frontmatter を `status: ready`, `assigned: ai`, `reviewed_at: {今日}` に書き換え
  - 必要に応じて本文を構造化（見出し追加・箇条書き整理）
- **人間対応が必要 → `need_human_action / assigned: human` へ遷移**: 再現確認が必要、外部サービスへのログインが必要、秘密値が必要、期待仕様の確認が必要など
  - frontmatter を `status: need_human_action`, `assigned: human`, `reviewed_at: {今日}` に書き換え
  - 本文末尾に `## AI からの依頼` セクションを追記し、具体的な依頼内容を列挙
  - **依頼粒度**: 人間がそのまま実行できる粒度まで具体化する（「確認しておいて」は NG）

#### 1-3. AI 起票 ISSUE の扱い

- AI は ISSUE 新規作成時に `raw / ready / need_human_action` のいずれかを選ぶ
- `raw / assigned: ai` の ISSUE は「AI 側の未整理メモ」として扱い、review 対象にも着手対象にも含めない
- `ready / assigned: ai` の ISSUE は通常の ready ISSUE と同様に着手候補に含める
- `need_human_action / assigned: human` の ISSUE は人間待ちとして扱い、着手対象に含めない

#### 1-4. 結果のサマリ報告

review フェーズと全体分布をサマリ出力する:

```
[ISSUE レビュー結果]
- ready / assigned: ai に遷移: 2 件（ISSUES/util/high/foo.md, ISSUES/app/medium/bar.md）
- need_human_action / assigned: human に遷移: 1 件（ISSUES/app/low/baz.md — 3 件の依頼を追記）

[ISSUE 状態サマリ]
- raw / assigned: human: 2 件
- raw / assigned: ai: 1 件
- review / assigned: ai: 0 件
- ready / assigned: ai: 3 件
- need_human_action / assigned: human: 1 件
```

#### 1-5. ready な ISSUE のみから着手対象を選定

既存の「ISSUES/{カテゴリ}/high/ を優先的に参照」ロジックを、**`status: ready` かつ `assigned: ai` のもののみを対象**とするように変更:

- `high/` に `ready / assigned: ai` があれば優先
- `high/` に `ready / assigned: ai` がなければ `medium/` の `ready / assigned: ai` を対象
- `ready / assigned: ai` がどこにも無い場合のみ MASTER_PLAN の次項目に進む
- `review` / `need_human_action` / `raw` は着手対象外（サマリでは触れるが選定しない）

### 2. レビューロジックの共通化

`/split_plan` と `/quick_plan` で重複が生じるため、共通 SKILL として切り出す:

`.claude/SKILLS/issue_review/SKILL.md`:
- 入力: カテゴリ名
- 処理: 上記 1-1〜1-4 を実行
- 出力: review 処理結果と、状態 × 担当の集計結果

`/split_plan` / `/quick_plan` はこの SKILL を冒頭で呼び出す形に変更する。

### 3. ヘルパースクリプト（任意）

人間が ISSUE を大量にレビューに回したいとき用に、一括で `raw` → `review` に進めるスクリプトは **用意しない**（手動編集を徹底したほうが意図せぬレビュー開始を防げる）。

代わりに、現在の状態分布を確認するスクリプトのみ用意する:

`scripts/issue_status.py`:
- カテゴリ指定で `ISSUES/{category}/` 配下の全 ISSUE の `status × assigned` 分布を出力
- 例:
  ```
  util:
    high:    ready/ai=1, review/ai=0, need_human_action/human=0, raw/human=2, raw/ai=1
    medium:  ready/ai=0, review/ai=1, need_human_action/human=1, raw/human=0, raw/ai=0
    low:     ready/ai=0, review/ai=0, need_human_action/human=0, raw/human=3, raw/ai=0
  ```

### 4. 既存 ISSUE のマイグレーション

現存する ISSUE ファイル（`ISSUES/**/*.md`）にはフロントマターが無い。移行方針:

- **既存ファイルは触らない**: フロントマター無し = `status: raw`, `assigned: human` 扱いなので、着手対象外になる
- ユーザーが手動で各 ISSUE を確認し、完成しているものは `status: ready`, `assigned: ai` を付ける
- 雑なメモは `status: review`, `assigned: ai` を付けて AI にレビューさせる
- AI が新規 ISSUE を作る場合は、作成時点で必ず `status` と `assigned` を両方付与する

マイグレーションガイドを `docs/util/ver6.0/MIGRATION.md` として別途用意する。

### 5. ドキュメント整備

- `.claude/SKILLS/split_plan/SKILL.md`: 冒頭 ISSUE レビューフェーズと `assigned` の解釈を追記
- `.claude/SKILLS/quick_plan/SKILL.md`: 同上
- `.claude/SKILLS/issue_review/SKILL.md`: 新規作成
- プロジェクト直下 `ISSUES/README.md`: フロントマター仕様・状態遷移・`assigned` の説明を新規作成

## ファイル変更一覧

| ファイル | 操作 | 内容 |
|---|---|---|
| `.claude/SKILLS/issue_review/SKILL.md` | 新規作成 | ISSUE レビュー共通 SKILL |
| `.claude/SKILLS/split_plan/SKILL.md` | 変更 | 冒頭で `/issue_review` 呼び出し・`ready / assigned: ai` 絞り込み |
| `.claude/SKILLS/quick_plan/SKILL.md` | 変更 | 同上 |
| `ISSUES/README.md` | 新規作成 | フロントマター仕様書（`status` + `assigned`） |
| `scripts/issue_status.py` | 新規作成 | 状態 × 担当の分布確認スクリプト |
| `docs/util/ver6.0/MIGRATION.md` | 新規作成 | 既存 ISSUE の手動移行ガイド |
| `docs/util/ver6.0/` | 新規作成 | ROUGH_PLAN / IMPLEMENT / CURRENT / MEMO |

## リスク・不確実性

- **フロントマターパースの揺れ**: YAML パーサの差異でエラーになる可能性。`python scripts/issue_status.py` では `yaml.safe_load` を使い、失敗時は `status: raw`, `assigned: human` 扱いにフォールバック
- **`status` と `assigned` の不整合**: 例えば `need_human_action / assigned: ai` のような矛盾した組み合わせが入りうる。`ISSUES/README.md` と SKILL 内で許可組み合わせを明記し、異常値はサマリで警告する
- **SKILL 内でのファイル編集**: `/split_plan` は SKILL 実行 = AI 主導のため、frontmatter 書き換えを AI が正しく行えるかは実装後に検証が必要。誤書き換え防止のため、書き換え前に対象ファイルを全件 Read で読んでから Edit する手順を SKILL 内に明記する
- **need_human_action ループ**: AI の依頼が的外れだと、人間が対応しても再度 `need_human_action` に戻される可能性。SKILL 内で「依頼は最大 5 件まで、同じ観点を繰り返さない」などのガードを明記する
- **AI raw の滞留**: `raw / assigned: ai` が溜まるとノイズになる可能性がある。一定期間見直されていない AI raw を可視化する運用が必要

## やらないこと

- ステータスの自動遷移（`raw` → `review` は必ず人間または AI の明示的な更新で行う）
- CI での ISSUE フォーマットチェック（ローカル運用のみ、GitHub Actions での検査は対象外）
- 過去 ISSUE の一括マイグレーション（ユーザーが個別に `ready` や `review` を付ける運用）
- `assigned` を超える追加メタデータ拡張（`estimated_hours` や `team` などは対象外）
- `done/` への自動移動（解決済み ISSUE の削除は従来どおり `quick_doc` / `wrap_up` が担当）
