# ver6.0 IMPLEMENT: ISSUE ステータス・担当管理

ROUGH_PLAN.md（PHASE5.0）に基づく実装設計。

## 既存状態の事前確認

### ISSUE ファイルの現状（分類把握の前提）

ver6.0 着手時点で `ISSUES/**/*.md` 配下の全 8 ファイルが、すでに本実装で採用する frontmatter 形式（`status` / `assigned` / `priority`）を保持している:

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

含意:
- 「既存 ISSUE を触らない」「既存ファイルは `raw / human` 扱いのまま残す」という後方互換ルールは、**実際に影響するファイルは無い**。後方互換コードパスは将来の frontmatter 無しファイルへの防御として実装する
- `util` カテゴリには ISSUE が存在しない（`.gitkeep` のみ）。ver6.0 の動作確認では、実 ISSUE を持つ `app` / `infra` カテゴリで `issue_status.py` の実行結果を確認する
- `review / ai` のファイルが既に複数あるため、`issue_review` SKILL の動作を別カテゴリで検証できる（ただし `util` ワークフロー中には直接レビューは発生しない）

### 既存 SKILL の構造

- `.claude/skills/split_plan/SKILL.md` — 準備パート（現状把握 / プラン把握）→ 分割パート（ステップ1: ROUGH_PLAN.md + plan_review_agent、ステップ2: IMPLEMENT.md + plan_review_agent）→ ステップ3: コミット、という章立て。「`ISSUES/{カテゴリ}/high/` に未解決の課題が存在する場合はISSUES対応を優先」というロジックが ROUGH_PLAN 作成指示の中に埋め込まれている
- `.claude/skills/quick_plan/SKILL.md` — 準備パート → 計画パート（ROUGH_PLAN.md 作成）→ コミット。`ISSUES/{カテゴリ}/high/` を優先するロジックが `ROUGH_PLAN.md の作成` の「対応する ISSUE」箇条書き中に存在
- 両 SKILL とも、「ISSUE 選定」の記述は数行に収まっている

### Python 環境

- `scripts/claude_loop_lib/feedbacks.py` 既に `yaml.safe_load` を使って frontmatter をパース済み。YAML 解析の実装パターンは流用可
- Python 3 ＋ `PyYAML 6.0.2` 利用可能

### 変更対象ファイルの事前読み込み済みリスト

- `.claude/skills/split_plan/SKILL.md` ✅
- `.claude/skills/quick_plan/SKILL.md` ✅
- `scripts/claude_loop_lib/feedbacks.py` ✅（参考実装）
- `docs/util/MASTER_PLAN/PHASE5.0.md` ✅（フェーズ原典。ファイルパス typo 2 箇所を ROUGH_PLAN レビューで修正済み）

## 実装順序と成果物

### ステップ 1. フロントマター仕様書 `ISSUES/README.md`

PHASE5.0.md §フロントマター仕様・ステータス遷移を素直に転記する位置づけの文書。

記載項目:

- なぜこの仕組みがあるか（plan ステップが着手対象を絞るため）
- `status` / `assigned` の定義と許可される組み合わせ
- 人間起票時のライフサイクル（raw → review → ready / need_human_action → review …）
- AI 起票時の作法（`raw | ready | need_human_action` のみ、`review` は AI が付けない）
- `need_human_action` の ISSUE に追記される `## AI からの依頼` セクションの書式
- `priority` / `reviewed_at` は任意
- フロントマター無し = `raw / human` 扱い（後方互換）
- 新規 ISSUE のテンプレート例
- **AI raw の滞留に関する運用上の注意**: `raw / assigned: ai` は AI 側の未整理メモでノイズ化しうる。定期的に `python scripts/issue_status.py` で分布を確認し、長期滞留している AI raw は再整理するか削除する旨の一行ガイド（PHASE5.0 リスク §AI raw の滞留 への対応）

分量目安: 80〜120 行。

### ステップ 2. `scripts/issue_status.py`

`status × assigned` のカテゴリ別・優先度別分布を表示する読み取り専用スクリプト。

#### 仕様

- 入力: コマンドライン引数 `[category]`（省略時は全カテゴリ）
- 走査対象: `ISSUES/{category}/{high,medium,low}/*.md`
- パース: 先頭 `---` 〜 `---` の YAML を `yaml.safe_load`
- 出力: カテゴリ → 優先度 → `status/assigned=件数` の表

#### 集計ロジック（フォールバック含む）

各ファイルごとに:

1. frontmatter 無し → `status=raw`, `assigned=human` として集計
2. YAML パース失敗 → 同上（標準エラーに警告一行）
3. `status` が既定値外（`raw` / `review` / `ready` / `need_human_action` 以外）→ そのまま集計しつつ標準エラーに警告
4. `assigned` が既定値外（`human` / `ai` 以外）→ 同上
5. `status` と `assigned` の組み合わせが仕様上不正（例: `need_human_action / ai`, `review / human`）→ 集計はするが標準エラーに警告

終了コード: 常に 0。警告は stderr のみ。CI での使用は想定せず、観測用途に限定。

#### 出力例（必須フォーマット）

```
util:
  high:    ready/ai=0, review/ai=0, need_human_action/human=0, raw/human=0, raw/ai=0
  medium:  ready/ai=0, review/ai=0, need_human_action/human=0, raw/human=0, raw/ai=0
  low:     ready/ai=0, review/ai=0, need_human_action/human=0, raw/human=0, raw/ai=0
app:
  high:    ...
  ...
```

優先度が `high` / `medium` / `low` 以外のサブディレクトリは無視する（想定外構造）。

**0 件時の表示**: 該当カテゴリ / 優先度に ISSUE が 1 件も無くても、5 区分（`ready/ai` / `review/ai` / `need_human_action/human` / `raw/human` / `raw/ai`）すべてを `=0` で出力する。カテゴリ自体が存在しない場合のみ、そのカテゴリブロックをスキップする。

#### 実装規模

`feedbacks.py` のパースを雛形に、200 行以内で収まる。

### ステップ 3. 新規 SKILL `.claude/skills/issue_review/SKILL.md`

`/split_plan` と `/quick_plan` の両方から呼び出される共通 SKILL。

#### 入力

- 現在のカテゴリ名（呼び出し元の SKILL 内に既出の仕組みで取得）

#### 処理

1. **スキャン**: `ISSUES/{カテゴリ}/{high,medium,low}/*.md` を読み、各ファイルの frontmatter をパース。frontmatter 無し / パース失敗は `raw / human` として扱う
2. **review 対象の抽出**: `status: review` かつ `assigned: ai` のファイルをリストアップ
3. **個別レビュー**: 対象ファイルごとに本文と frontmatter を読み、以下のいずれかを判断して frontmatter を書き換える
    - **記述が具体的**（再現手順 / 期待動作 / 影響範囲が読み取れる）→ `status: ready`, `assigned: ai`, `reviewed_at: {本日}`
    - **人間対応が必要**（再現確認 / 秘密値取得 / 仕様確認 / 外部サービスへのログインなど）→ `status: need_human_action`, `assigned: human`, `reviewed_at: {本日}` に書き換え、本文末尾に `## AI からの依頼` セクションを追記し、具体的な依頼（最大 5 件）を箇条書きで列挙
    - **記述が粗すぎる**（本文が数行のメモのみ等）→ `need_human_action / human` 側に倒し、`## AI からの依頼` で必要な情報を人間に求める
4. **サマリ報告**: 以下の 2 ブロックを出力
    - 遷移の結果（`ready / ai` に遷移した件数と対象、`need_human_action / human` に遷移した件数と対象、追記した依頼件数）
    - 全体分布（`status × assigned` の件数。`raw / human`, `raw / ai`, `review / ai`, `ready / ai`, `need_human_action / human` の 5 区分）

#### 出力形式（呼び出し元が後段で参照するための構造化）

Markdown 見出し `## ISSUE レビュー結果` / `## ISSUE 状態サマリ` として plan 本文に残す。plan_review_agent への説明時に可視化される。

#### 書き換え時のガード

- 書き換え前に必ず対象ファイル全文を Read で読んでから Edit する（PHASE5.0 リスク §SKILL 内でのファイル編集）
- 1 セッション内で同じファイルを 2 回以上書き換えない
- `## AI からの依頼` セクションは既存であれば置換、無ければ末尾に追記
- `reviewed_at` はサーバ側の今日の日付（`date +%Y-%m-%d` 相当）を使用

### ステップ 4. `split_plan` / `quick_plan` への組み込み

#### 共通の変更

両 SKILL の「準備」セクションの末尾に、以下のフェーズを追加:

> - **ISSUE レビューフェーズ**: `issue_review` SKILL を実行し、`status: review` の ISSUE を `ready` / `need_human_action` に振り分ける。結果サマリを ROUGH_PLAN の冒頭（または本文中）に残す。

「ROUGH_PLAN.md の作成」内の ISSUE 選定ロジックを以下のように置換:

- **置換前（split_plan 現行）**: 「`ISSUES/{カテゴリ}/high/` に未解決の課題が存在する場合はISSUES対応を優先する」
- **置換後**: 「`ISSUES/{カテゴリ}/` から `status: ready` かつ `assigned: ai` の ISSUE を優先度順（high → medium → low）で抽出する。`review` / `need_human_action` / `raw` は着手対象外（直前のレビューフェーズでレビュー対象となる）。`ready / ai` が無い場合のみ MASTER_PLAN の次項目に進む」

同じ書き換えを `quick_plan/SKILL.md` の「対応する ISSUE」箇条書きに施す（`quick_plan` は現状 `high/` 優先のみが記述されている。これを「`status: ready` かつ `assigned: ai` の ISSUE を優先度順（high → medium → low）で抽出する」に差し替える）。

#### 具体的な記述例（split_plan の最終形）

```md
## 準備

上記の最新バージョン番号に基づいて、現在の状況を把握して。

- 現状を把握して
  - （既存の記述）
  - `ISSUES/{カテゴリ}` フォルダ配下に優先度の高い課題があれば参照して、把握する（ `high`・`medium`・`low`フォルダに分かれている）
  - 直前バージョンの `RETROSPECTIVE.md` が存在する場合は確認し、未実施の改善提案がないか確認する
  - **ISSUE レビューフェーズ**: `issue_review` SKILL を起動し、`status: review` かつ `assigned: ai` の ISSUE を `ready` / `need_human_action` に振り分ける。レビュー結果と状態サマリをコンテキストとして保持する
```

### ステップ 5. `docs/util/ver6.0/MIGRATION.md`

既存 ISSUE の移行ガイド。ver6.0 着手時点で `ISSUES/**/*.md` の 8 ファイルは既に移行済みであることを明記した上で、将来 frontmatter 無しファイルが増えた場合のために手順を残す。

記載項目:

- 移行状況の現状（8 ファイル全て移行済み）
- frontmatter 無しファイルが登場した場合の手動移行手順
  - 記述が具体的で着手可能 → `status: ready`, `assigned: ai` を付与
  - 情報が足りないが AI の手を借りて整理したい → `status: review`, `assigned: ai` を付与
  - 放置してよい書きかけ → そのまま（= raw / human 扱いで着手対象外になる）
- AI が新規 ISSUE を起票するときのテンプレート（`raw / ai`, `ready / ai`, `need_human_action / human`）

分量目安: 50 行程度。

### ステップ 6. 動作確認

以下をマニュアル実行で確認する:

1. `python scripts/issue_status.py` — 全カテゴリで 8 件の ISSUE が期待する分布で出力される
2. `python scripts/issue_status.py util` — util は全 0 で出力される
3. `python scripts/issue_status.py nonexistent` — エラーにならず、空または警告のみ
4. frontmatter 無し相当の挙動確認 — 一時的にテスト用ファイルを作成し `raw / human` に分類されることを確認して削除（あるいは単体テストではなく、今回は手動で現物を一時退避 / 復元）
5. `.claude/skills/split_plan/SKILL.md` / `quick_plan/SKILL.md` の Markdown 構造が壊れていないことを確認

実機での `/split_plan` 実行確認は ver6.1 以降のワークフロー起動時に初めて行われる（ver5.0 → ver5.1 で継続機能を確認したのと同じ運用）。したがって ver6.0 の imple_plan ステップでは **SKILL の Markdown / スクリプトの単体動作のみを確認し、ワークフロー組み込みの正常性はユーザーの次回セッション観測に委ねる** 方針とする。

**frontmatter 書き換えパスの実動作確認**: `util` カテゴリには `review / ai` の ISSUE が無いため、ver6.0 の imple_plan では書き換えロジックを実行しない。書き換えの最初の実運用は、次回 `app` または `infra` カテゴリで `/split_plan` / `/quick_plan` を起動した際に `review / ai` の 5 件が順次通過するタイミングとなる。誤書き換えが発生しても `git checkout -- <path>` で復旧できるため、この持ち越しは許容する。

## リスク・不確実性

### R1. YAML frontmatter パースの不整合

**不確実性**: `yaml.safe_load` は一部の入力で予期せぬ型を返す（例: 値が `yes` / `no` だと bool になる、日付っぽい文字列が `date` オブジェクトになる）。`reviewed_at` を `2026-04-23` で書き込むと `date` として復元される可能性がある。

**緩和**: `issue_status.py` 側では `str()` で強制文字列化してから集計。`issue_review` SKILL 側では `reviewed_at` を文字列として扱うよう明記し、`"2026-04-23"` のようにクオートせずとも集計には影響しないことを文書化する。

**検証方法**: imple_plan ステップ中に Python ワンライナーで `yaml.safe_load('status: review\nassigned: ai\nreviewed_at: 2026-04-23\n')` の型を確認し、MEMO.md に記録。

### R2. frontmatter 書き換え時の本文破壊

**不確実性**: SKILL 内での Edit 操作で、frontmatter の区切り `---` の位置や改行コードを誤ると、YAML 本体が壊れたり本文が巻き込まれたりする可能性がある。Windows 改行 (CRLF) と Unix 改行 (LF) の混在も要注意。

**緩和**:
- 書き換え前に必ず Read で全文を取得して、改行コードと frontmatter の境界を確認
- Edit の `old_string` は `---\nstatus: review\nassigned: ai\n...\n---` 全体を含め、`new_string` 側も同じ改行で組み立てる
- SKILL.md に「frontmatter ブロックを丸ごと置換する Edit を使う」という方針を明記
- git にコミット済みの状態から書き換えるため、失敗しても `git checkout -- <path>` で復旧可能

**検証方法**: ver6.0 の imple_plan では書き換えを実行しない（util カテゴリに review ISSUE が無いため）。将来の ver6.1 以降で初めて実運用される。したがって ver6.0 では挙動仕様を SKILL 内に明記するに留め、実動作確認は持ち越す。

### R3. `issue_review` SKILL が `/split_plan` から自動起動されない可能性

**不確実性**: 既存 SKILL から他の user-invocable SKILL を呼び出す仕組みが、現行の `claude_loop.py` / SKILL 定義でどの程度堅牢か不明。`disable-model-invocation: true` の SKILL は slash コマンド経由でしか起動できない可能性がある。

**緩和**:
- `issue_review` SKILL は `disable-model-invocation: true` / `user-invocable: true` を他 SKILL と揃える
- **決定: インライン化（手順を直接記述）を採用**。`issue_review/SKILL.md` は「仕様書」として残し、`split_plan/SKILL.md` / `quick_plan/SKILL.md` では ISSUE レビューフェーズの手順を直接 Markdown 本文として記述する（参照記法でのインクルードは使わない。SKILL チェーンに依存しないため）
- **重複管理の明示**: `split_plan` / `quick_plan` の両方に同等の手順が存在するため、仕様変更時は 2 箇所を同期修正する必要がある。`issue_review/SKILL.md` を一次資料として位置づけ、両 SKILL 側には「仕様の詳細は `.claude/skills/issue_review/SKILL.md` を参照」という一文を添えて同期を促す

**検証方法**: `split_plan/SKILL.md` のプレビューを人間が読み、`issue_review` を起動しなくても一連の流れが追えるかを確認。

### R4. review → need_human_action 無限ループ

**不確実性**: AI の依頼が的外れだと人間が対応しても解決せず、再度 `need_human_action` に戻されるループが発生しうる。

**緩和**: SKILL 内に以下のガードを明記:
- 依頼は最大 5 件まで
- 1 回のレビューで同一観点の依頼を繰り返さない
- 人間から対応済み回答を得たあとに再評価した結果、再度 `need_human_action` になる場合は、依頼内容を質的に変える（同じ表現を使わない）

運用で監視する性質のリスクであり、コードでの自動検出はしない。

### R5. `reviewed_at` の粒度

**不確実性**: 同日内に複数回レビューすると `reviewed_at` が上書きされ、前回との差分が追えない。

**判断**: 履歴は git log で追える。`reviewed_at` は最新状態のみ保持する。履歴機能は ver6.0 のスコープ外。

## 変更ファイル一覧

| ファイル | 操作 | 目安行数 |
|---|---|---|
| `ISSUES/README.md` | 新規 | 100 行前後 |
| `.claude/skills/issue_review/SKILL.md` | 新規 | 80 行前後 |
| `.claude/skills/split_plan/SKILL.md` | 変更 | 差分 +10 / −3 程度 |
| `.claude/skills/quick_plan/SKILL.md` | 変更 | 差分 +10 / −3 程度 |
| `scripts/issue_status.py` | 新規 | 150 行前後 |
| `docs/util/ver6.0/MIGRATION.md` | 新規 | 50 行前後 |
| `docs/util/ver6.0/MEMO.md` | 新規 | imple_plan 中に追記 |

合計新規約 400 行 + 既存 2 SKILL に対する小変更。

## 本バージョンで対応しないこと（再掲）

- ステータスの自動遷移
- `raw → review` 一括移行ヘルパー
- CI フォーマット検査
- 既存 ISSUE の一括自動マイグレーション（= 現時点で 8 ファイル全て手動移行済みのため対応不要）
- `done/` 自動移動
- 履歴メタデータ拡張
