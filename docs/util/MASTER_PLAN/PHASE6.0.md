# PHASE6.0: ISSUE 起点プランニングの分割とワークフロー自動選択

## 実装進捗

| 節 | 内容 | 状態 | バージョン |
|---|---|---|---|
| §1 | `issue_worklist.py` 追加 + `claude_loop_lib/issues.py` 共通化 | ✅ 完了 | ver7.0 |
| §2 | `/issue_plan` SKILL 新設、`/split_plan` 責務縮小、`/quick_plan` 削除 | ✅ 完了 | ver8.0 |
| §3 | `--workflow auto` 導入 | ⏳ 未着手 | ver8.1 想定 |
| §4 | `/retrospective` での `issue_worklist.py` 利用手順追記 | ✅ 完了 | ver7.0 |
| §5 | ドキュメント・テスト整備（部分完了） | 🔄 一部完了 | ver7.0〜 |

§5 詳細（ver7.0 時点）:
- `scripts/README.md` への `issue_worklist.py` 説明追記 → ✅
- `.claude/SKILLS/retrospective/SKILL.md` への手順追記 → ✅
- その他（`/issue_plan` SKILL、`/split_plan` 責務縮小、`meta_judge/WORKFLOW.md` 等）→ §2/§3 と一体で後続バージョン

## 概要

`/split_plan` の前半責務（関連 ISSUE の取得、対象選定、`ROUGH_PLAN.md` 作成）を新規 `/issue_plan` に切り出し、既存 `/split_plan` は review 付きの詳細実装計画作成に専念させる。`scripts/issue_worklist.py` を追加し、`status: ready | review` かつ `assigned` が指定主体に一致する ISSUE だけを抽出できるようにする。`scripts/claude_loop.py` の `--workflow` には `auto` を追加し、これをデフォルトにして、`/issue_plan` が `quick` / `full` のどちらに進むかを確定する。

## 動機

- 現状の `/split_plan` は現状把握、ISSUE 選定、`ROUGH_PLAN.md` 作成、実装計画、review までを 1 ステップに抱え込み、コンテキストが肥大化しやすい
- PHASE5.0 で `status` / `assigned` を導入しても、AI が「今の自分に関係ある ISSUE だけ」を素早く取れないと活用しにくい
- quick / full の選択が現状は実行前の人間判断 or YAML 指定に寄っており、毎回 `-w` を意識する必要がある
- `/retrospective` でも次に触るべき `ready` / `review` ISSUE を絞って見たい
- PHASE3.0 では「ワークフローの自動選択」はやらないことにしていたが、ISSUE ステータスと共通前半ステップが揃えば、ここで再導入する価値が高い

## 前提条件

- PHASE5.0 の `status` / `assigned` 仕様が実装済み、または少なくとも `ISSUES/**/*.md` から frontmatter を読める状態であること
- PHASE3.0 の `full` / `quick` ワークフローが存在すること
- PHASE4.0 の `scripts/claude_loop.py` モジュール分割・CLI 基盤が利用可能であること

## やること

### 1. 関連 ISSUE 抽出スクリプトの追加

`scripts/issue_worklist.py` を新規作成する。

#### 1-1. 役割

- `ISSUES/{category}/{high,medium,low}/*.md` を走査し、frontmatter の `status` / `assigned` を読む
- `status in {ready, review}` かつ `assigned == <指定値>` の ISSUE だけを返す
- 既定では `.claude/CURRENT_CATEGORY` のカテゴリ、`assigned: ai`、`status: ready,review` を対象にする
- 出力は人間が読みやすい `text` と、他スクリプトや SKILL が扱いやすい `json` の両方をサポートする

#### 1-2. 想定 CLI

```bash
# 現在カテゴリの AI 向け ready/review ISSUE 一覧
python scripts/issue_worklist.py

# human 向けに切り替え
python scripts/issue_worklist.py --assigned human

# JSON で取得
python scripts/issue_worklist.py --format json

# カテゴリを明示
python scripts/issue_worklist.py --category util --assigned ai --status ready,review
```

#### 1-3. 出力項目

各 ISSUE について最低限以下を返す:

- `path`
- `title`
- `priority`
- `status`
- `assigned`
- `reviewed_at`（あれば）
- 先頭数行の要約 or 先頭見出し

`text` 出力例:

```text
[util]
- high   | ready  | ai | ISSUES/util/high/foo.md   | タイトル...
- medium | review | ai | ISSUES/util/medium/bar.md | タイトル...
```

#### 1-4. フォールバック

- frontmatter なし、または YAML パース失敗時は `raw / human` 扱いとして除外する
- `status` / `assigned` が不正な場合は警告を出しつつ除外する
- `priority` はディレクトリ名を優先し、frontmatter と不一致なら警告のみ出す

### 2. `/split_plan` の前半を `/issue_plan` に分離

#### 2-1. 新規 `/issue_plan`

`/split_plan` の前半責務を新しい共通ステップ `/issue_plan` に切り出す。

役割:

- 現状把握に必要な `CURRENT.md` / 直前 `RETROSPECTIVE.md` / `MASTER_PLAN.md` を読む
- `python scripts/issue_worklist.py --format json` を使って、現在の AI に関係ある `ready` / `review` ISSUE を取得する
- 取得した ISSUE から今回取り組む候補を 1〜2 件に絞る
- `docs/{category}/ver{次バージョン}/ROUGH_PLAN.md` を作成する
- `ROUGH_PLAN.md` の先頭 frontmatter に `workflow: quick | full` を記録する
- **review は行わない**
- **plan_review_agent も起動しない**

`ROUGH_PLAN.md` の先頭例:

```yaml
---
workflow: quick   # quick | full
source: issues    # issues | master_plan
---
```

ワークフロー選択ルール:

- 選定 ISSUE に `status: review` が 1 件でも含まれる場合は **必ず `full`**
- 対応対象が MASTER_PLAN 新項目、アーキテクチャ変更、新規ライブラリ導入を含む場合は **必ず `full`**
- 選定 ISSUE がすべて `ready` で、小規模変更（既存 quick 判定基準相当）なら `quick`
- 判断に迷う場合は安全側で `full`

#### 2-2. 後半 `/split_plan` の責務整理

既存 `/split_plan` は「詳細実装計画 + review あり」の後半ステップに縮小する。

新しい責務:

- `ROUGH_PLAN.md` を読み、対象タスクを固定する
- 選定 ISSUE に `review` が含まれる場合は、この段階で詳細化 review を実施する
- review の結果、`ready` になった内容だけを `IMPLEMENT.md` / `REFACTOR.md` に落とし込む
- `need_human_action` になった場合は、違うISSUEまたはマスタープランの解決に移る
- **plan_review_agent はここでのみ起動する**

これにより:

- 前半 `/issue_plan`: 「何をやるか」と「quick/full の選択」を決める
- 後半 `/split_plan`: 「どう実装するか」を review 付きで固める

#### 2-3. `/quick_plan` の扱い

`quick_plan` は責務が `/issue_plan` と重複するため、以下のどちらかで整理する:

- **推奨**: `claude_loop_quick.yaml` からは `quick_plan` を外し、`/issue_plan` を使う
- 後方互換のため、`/quick_plan` 自体は `/issue_plan` を呼ぶ薄いラッパー or deprecated 案内にする

### 3. `scripts/claude_loop.py` に `--workflow auto` を導入

#### 3-1. `--workflow` の新仕様

`--workflow` は YAML パス直指定だけでなく、予約値も受け取れるようにする:

- `auto` — **新規、デフォルト**
- `full` — フルワークフロー
- `quick` — 軽量ワークフロー
- `<path/to/workflow.yaml>` — 明示的な YAML パス（従来互換）

利用例:

```bash
# デフォルト（= --workflow auto）
python scripts/claude_loop.py

python scripts/claude_loop.py --workflow auto
python scripts/claude_loop.py --workflow full
python scripts/claude_loop.py --workflow quick
python scripts/claude_loop.py --workflow scripts/custom_workflow.yaml
```

**注意**: 既存の `--auto` フラグは「無人実行モード」の意味で残す。`--workflow auto` とは別物なので、README では必ず両者の違いを明記する。

#### 3-2. `auto` の実行フロー

`--workflow auto` では、まず `/issue_plan` だけを実行し、その結果を見て後続ワークフローを切り替える。

```text
issue_plan
  ├─ workflow: quick -> quick_impl -> quick_doc
  └─ workflow: full  -> split_plan -> imple_plan -> wrap_up -> write_current -> retrospective
```

実装方式:

1. `issue_plan` 単独実行用のワークフロー（例: `scripts/claude_loop_issue_plan.yaml`）を用意
2. `claude_loop.py --workflow auto` は最初にそれを実行
3. 生成された `ROUGH_PLAN.md` frontmatter の `workflow` を読む
4. `quick` なら `claude_loop_quick.yaml` の 2 ステップ目以降へ、`full` なら `claude_loop.yaml` の 2 ステップ目以降へ進む

#### 3-3. YAML の更新

`full`:

```text
/issue_plan -> /split_plan -> /imple_plan -> /wrap_up -> /write_current -> /retrospective
```

`quick`:

```text
/issue_plan -> /quick_impl -> /quick_doc
```

### 4. `/retrospective` での再利用

`/retrospective` でも `python scripts/issue_worklist.py --format json` を呼び、次に AI が処理しうる `ready` / `review` ISSUE を把握してから、次バージョンの推奨を行う。

使い方:

- `ready` が多い -> 次も ISSUES 対応を優先しやすい
- `review` が多い -> full ワークフロー前提の課題が溜まっていると判断できる
- 対象が空 -> MASTER_PLAN 側に寄せる判断がしやすい

### 5. ドキュメント・テスト整備

- `scripts/README.md`
  - `--workflow auto | full | quick | <path>` の説明を追記
  - `--auto` フラグとの違いを明記
  - `issue_worklist.py` の使い方を追記
- `.claude/SKILLS/meta_judge/WORKFLOW.md`
  - 新しい共通入口 `/issue_plan` と `auto` 選択フローを追記
- `.claude/SKILLS/issue_plan/SKILL.md`
  - 新規作成
- `.claude/SKILLS/split_plan/SKILL.md`
  - 後半ステップ用に責務を縮小
- `.claude/SKILLS/quick_plan/SKILL.md`
  - deprecated 案内 or `/issue_plan` ラッパーに変更
- `.claude/SKILLS/retrospective/SKILL.md`
  - `issue_worklist.py` 利用手順を追記
- `tests/test_claude_loop.py`
  - `--workflow auto` の解決、`auto` 分岐、予約値とパスの両立を追加テスト

## ファイル変更一覧

| ファイル | 操作 | 内容 |
|---|---|---|
| `scripts/issue_worklist.py` | 新規作成 | `assigned` と `status: ready/review` で ISSUE を絞るヘルパースクリプト |
| `scripts/claude_loop.py` | 変更 | `--workflow auto` 既定化・予約値解決・`issue_plan` 実行後の分岐 |
| `scripts/claude_loop.yaml` | 変更 | 先頭ステップを `/issue_plan` に差し替え |
| `scripts/claude_loop_quick.yaml` | 変更 | 先頭ステップを `/issue_plan` に差し替え |
| `scripts/claude_loop_issue_plan.yaml` | 新規作成 | `issue_plan` 単独実行用ワークフロー |
| `scripts/README.md` | 変更 | 新 CLI 仕様と `issue_worklist.py` の説明 |
| `.claude/SKILLS/issue_plan/SKILL.md` | 新規作成 | ISSUE 選定 + `ROUGH_PLAN.md` 作成 + workflow 選択 |
| `.claude/SKILLS/split_plan/SKILL.md` | 変更 | 後半ステップ（review あり）のみに責務を限定 |
| `.claude/SKILLS/quick_plan/SKILL.md` | 変更 | 後方互換ラッパー or deprecated 案内 |
| `.claude/SKILLS/retrospective/SKILL.md` | 変更 | `issue_worklist.py` を使った ISSUE 状況確認 |
| `.claude/SKILLS/meta_judge/WORKFLOW.md` | 変更 | 新ワークフロー全体図へ更新 |
| `tests/test_claude_loop.py` | 変更 | `auto` 分岐と `--workflow` 予約値のテスト追加 |
| `docs/util/ver6.0/` | 新規作成 | `ROUGH_PLAN.md` / `IMPLEMENT.md` / `CURRENT.md` / `MEMO.md` |

## リスク・不確実性

- **`--auto` と `--workflow auto` の混同**: 既存 `--auto` は無人実行モードなので、CLI ヘルプと README で強く区別する必要がある
- **`auto` 分岐と `--start` / `--max-step-runs` の整合**: 途中再開時の意味が複雑になる。初期実装では `--workflow auto` 時の `--start` は `1` のみ許可するなどの制約が必要かもしれない
- **`ROUGH_PLAN.md` frontmatter の機械読取**: frontmatter 破損時に後続分岐できなくなる。`workflow` 未記載時は `full` にフォールバックする安全策を入れる
- **review ISSUE と quick の相性**: `review` ISSUE を quick に流すと review 工程が抜ける。`/issue_plan` 側で強制的に `full` を選ぶガードが必須
- **`issue_worklist.py` の出力安定性**: `/retrospective` と `/issue_plan` の両方が依存するため、`text/json` の出力仕様を README とテストで固定する必要がある

## やらないこと

- `quick` / `full` 以外の第 3 ワークフロー追加
- `/issue_plan` 段階での ISSUE 状態書き換え（review 結果の反映は後半 `/split_plan` で行う）
- 全ステータスの汎用検索ツール化（当面は `ready` / `review` に限定）
- カテゴリ横断での一括 ISSUE 選定
- custom YAML パス指定機能の廃止（明示パス実行は引き続き残す）
