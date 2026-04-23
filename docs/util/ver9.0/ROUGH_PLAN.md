---
workflow: full
source: master_plan
---

# ver9.0 ROUGH_PLAN — PHASE6.0 §3 + §5（`--workflow auto` 導入）と `/issue_plan` 単独 YAML 新設

## ISSUE レビュー結果

- 遷移対象件数: **0 件**（util カテゴリに `status: review` かつ `assigned: ai` の ISSUE は存在しない）
- `review / ai` → `ready / ai` 遷移: なし
- `review / ai` → `need_human_action / human` 遷移: なし

今回はレビューフェーズで書き換えるべき ISSUE がなかったため、`issue_review` SKILL の書き換えロジックは動作せず。`ISSUES/util/medium/issue-review-rewrite-verification.md` の検証機会は依然として app/infra ワークフロー起動待ち（本 ver9.0 スコープ外）。

## ISSUE 状態サマリ（util, ver9.0 開始時点）

| status \ assigned | ai | human |
|---|---|---|
| raw | 0 | 0 |
| review | 0 | — |
| ready | 4 | — |
| need_human_action | — | 0 |

内訳（`python scripts/issue_worklist.py --format json` 結果より）:

| path | priority | status | assigned |
|---|---|---|---|
| `ISSUES/util/medium/issue-plan-split-plan-handoff-verification.md` | medium | ready | ai |
| `ISSUES/util/medium/issue-review-rewrite-verification.md` | medium | ready | ai |
| `ISSUES/util/low/issue-plan-standalone-yaml.md` | low | ready | ai |
| `ISSUES/util/low/issue-worklist-json-context-bloat.md` | low | ready | ai |

## 今回のスコープ

### 対応対象

**MASTER_PLAN PHASE6.0 §3 +（§5 の `--workflow auto` 関連テスト）+ `ISSUES/util/low/issue-plan-standalone-yaml.md`**

`scripts/claude_loop.py` に `--workflow auto | full | quick | <path>` を導入し、`auto`（新デフォルト）時は `/issue_plan` を単独実行 → 出力された `ROUGH_PLAN.md` の `workflow:` frontmatter 値に応じて `full` / `quick` ワークフローを自動選択できるようにする。同時に、`auto` モードの第 1 段で使う `scripts/claude_loop_issue_plan.yaml`（1 ステップ YAML）を新設する。

### この 3 件を 1 バージョンに束ねる理由

- `--workflow auto` の内部ステップとして「`/issue_plan` 単独実行 YAML」が必須。両者は論理的密結合であり、別バージョンに割ると中間状態が意味を成さない
- §5 のテストは §3 の実装と一体で書かないと、仕様書き下ろしと分岐実装の食い違いを検出する機会を失う
- `ISSUES/util/low/issue-plan-standalone-yaml.md` は §3 の前提物そのもの。独立 ISSUE として別バージョンに切り出しても単独では効用が小さい

### スコープ外（意図的に除外）

以下の 3 件の `ready / ai` ISSUE は ver9.0 では取り上げない。除外理由を明示しておく（後続 `/split_plan` が範囲判断するときに迷わないため）:

- `ISSUES/util/medium/issue-plan-split-plan-handoff-verification.md`
  - 除外理由: 実ワークフローを回すことで観察される性質の検証課題。ver9.0 自体がそのワークフローを 1 回回すため、ver9.0 実行中に**自然観察される**。専用の作業項目は発生しない。観察結果は `docs/util/ver9.0/MEMO.md` / RETROSPECTIVE に記録する運用で足りる
- `ISSUES/util/medium/issue-review-rewrite-verification.md`
  - 除外理由: util 単体では `review / ai` な ISSUE が存在しないため実動作確認不能。app / infra ワークフロー起動を待つ持ち越し ISSUE。ver9.0 スコープで消化する手段がない
- `ISSUES/util/low/issue-worklist-json-context-bloat.md`
  - 除外理由: 閾値未到達（util 4 件 / app 6 件）。現時点での実装は YAGNI。件数が増えた段階で拾う

## 提供する機能・ユーザー体験の変化

### 変化 1: `claude_loop.py` のデフォルト起動が ISSUE 駆動でワークフローを自動選択する

**Before（ver8.0 現状）**:

```bash
python scripts/claude_loop.py                                    # full が走る
python scripts/claude_loop.py -w scripts/claude_loop_quick.yaml  # quick を明示指定
```

利用者はその日着手する ISSUE が quick で足りるか full が必要かを **事前に** 判断し、`-w` を付け替える必要がある。

**After（ver9.0）**:

```bash
python scripts/claude_loop.py                       # = --workflow auto（新デフォルト）
python scripts/claude_loop.py --workflow full       # 明示 full
python scripts/claude_loop.py --workflow quick      # 明示 quick
python scripts/claude_loop.py --workflow scripts/claude_loop_custom.yaml  # 従来互換のパス指定
```

`auto` モードでは:

1. まず `/issue_plan` 単独を実行して `docs/{cat}/ver{next}/ROUGH_PLAN.md` を作る
2. その frontmatter の `workflow: quick | full` を読む
3. 続きのステップ（`quick` なら quick_impl → quick_doc、`full` なら split_plan → imple_plan → wrap_up → write_current → retrospective）を実行する

利用者は「今日は full か quick か」を事前判断する必要がなくなる。判断は `/issue_plan` の SKILL ルール（`review` 含む / MASTER_PLAN 新項目 / 新ライブラリ / 変更規模）に委ねられる。

### 変化 2: `/issue_plan` を単独で反復実行できる

**Before**: `/issue_plan` を単独で試すには `claude_loop.yaml` を `--max-step-runs 1` で中断する必要があった。SKILL 挙動調整や ISSUE レビュー状態を定期的に更新したい運用では煩雑。

**After**: `python scripts/claude_loop.py --workflow scripts/claude_loop_issue_plan.yaml` で 1 ステップだけ実行できる。`--workflow auto` の内部でも同じ YAML を使うため、動作は一致する。

### 変化 3: `--auto`（無人実行）と `--workflow auto`（ワークフロー自動選択）が併存する

既存の `--auto` は「確認プロンプトを出さず自動承認する実行モード」（`AUTO` モード）であり、ワークフロー選択とは無関係。今回の `--workflow auto` は別の概念。両者は混同しやすいため、CLI ヘルプ / `scripts/README.md` で明示的に区別する。

組み合わせ例: `python scripts/claude_loop.py --auto --workflow auto` は「無人モードでワークフローを自動選択」を意味する。

### 変化 4: frontmatter 破損時のフォールバック

`ROUGH_PLAN.md` の `workflow:` が未記載・不正値（`quick | full` 以外）の場合は **`full` にフォールバック**して後続を実行する（安全側に倒す）。ユーザーは `logs/workflow/*.log` で警告を確認できる。

## 判断経緯（選定理由・除外理由の要約、後続 `/split_plan` への引き継ぎ）

### なぜ MASTER_PLAN の新項目を取るのか

- `ready / ai` の ISSUE は 4 件あるが、util カテゴリ単独で完結して大きな価値が出せるものが乏しい:
  - `issue-plan-split-plan-handoff-verification.md` は観察課題（実装タスクではない）
  - `issue-review-rewrite-verification.md` は他カテゴリ依存
  - `issue-worklist-json-context-bloat.md` は YAGNI
  - `issue-plan-standalone-yaml.md` は単独で取るより PHASE6.0 §3 と一体で取るのが合理的（RETROSPECTIVE §3-3 判定済み）
- 一方 PHASE6.0 §3 は ver8.0 で §2 が完了した時点で残っていた主要項目。`/issue_plan` frontmatter 書き込みは実装済みで、受け皿 `claude_loop.py` 側を整える段階

### なぜ ver9.0（メジャー）なのか

- `claude_loop.py` に新引数 `--workflow` の予約値処理（`auto | full | quick | <path>`）を追加する挙動変更
- 新規 YAML `scripts/claude_loop_issue_plan.yaml` の追加
- デフォルト挙動の変更（`-w` 省略時の既定ワークフローが固定 YAML から `auto` 分岐へ）
- ユニットテスト追加
- CLAUDE.md「メジャー = MASTER_PLAN 新項目・アーキテクチャ変更」に合致

ver8.0 RETROSPECTIVE §3-3 も同結論（ver9.0 メジャー推奨）。

### ワークフロー種別の判定

**`workflow: full`** を選択。根拠:

- MASTER_PLAN 新項目の着手（PHASE6.0 §3）
- `claude_loop.py` 本体のアーキテクチャ変更（デフォルト挙動の変更 + 新引数解決ロジック）
- 変更ファイル 6 本以上を想定（下記「関連ファイル」参照）
- テスト追加あり

`/issue_plan` SKILL のルール「MASTER_PLAN 新項目・アーキテクチャ変更・新規ライブラリ導入を含む場合 → 必ず `full`」に合致。

### `source: master_plan`

着手の出所は MASTER_PLAN PHASE6.0 §3 + §5。`ISSUES/util/low/issue-plan-standalone-yaml.md` は同スコープに同乗する形で消化される（PHASE6.0 §3 の前提物）ため副次的で、主出所は MASTER_PLAN と判定。

## 関連ファイル（`/split_plan` への引き継ぎ用）

### 変更・新規作成が想定されるファイル

| ファイル | 操作 | 概要 |
|---|---|---|
| `scripts/claude_loop.py` | 変更 | `--workflow` の予約値解決・`auto` モード分岐（2 段実行）・デフォルト値を `auto` に |
| `scripts/claude_loop_lib/workflow.py` | 変更の可能性 | 予約値解決を共通ヘルパ化する場合 |
| `scripts/claude_loop_issue_plan.yaml` | 新規作成 | 1 ステップ YAML（`/issue_plan` のみ） |
| `scripts/claude_loop.yaml` | 要確認 | 既に `/issue_plan` が先頭に入っているため ver8.0 時点で整備済み。`auto` から呼ばれた際にステップ 1 をスキップするかの取り扱いを検討 |
| `scripts/claude_loop_quick.yaml` | 要確認 | 同上 |
| `scripts/README.md` | 変更 | `--workflow auto | full | quick | <path>` の説明・`--auto` との違い・`claude_loop_issue_plan.yaml` のクイックスタート例 |
| `tests/test_claude_loop.py` | 変更 | `--workflow` 予約値解決・`auto` 分岐・frontmatter 読み取り・フォールバック挙動のテスト追加 |
| `.claude/skills/meta_judge/WORKFLOW.md` | 変更の可能性 | 全体図に `auto` 選択フローを反映 |
| `ISSUES/util/low/issue-plan-standalone-yaml.md` | 移動 | ver9.0 完了時に `ISSUES/util/low/done/` へ移動（`/wrap_up` or `/retrospective` ステージで処理） |

### 参照のみ（読む必要あり、変更しない）

- `docs/util/MASTER_PLAN/PHASE6.0.md` — §3 の仕様（CLI 仕様・`auto` 実行フロー・リスク）
- `docs/util/ver8.0/IMPLEMENT.md` §11 / §9 R6 — 持ち越しの経緯
- `docs/util/ver8.0/RETROSPECTIVE.md` §4-4 — ver9.0 引き継ぎ注意点 5 項目
- `.claude/skills/issue_plan/SKILL.md` — frontmatter 書き込みの仕様
- `scripts/claude_loop_lib/workflow.py` — 既存の YAML ロード・ステップ解決ロジック

### 後続 `/split_plan` が必ず確認すべき点（ver8.0 RETROSPECTIVE §4-4 より）

1. **`workflow` フィールド未記載・不正値時のフォールバック挙動**（`full` に倒す）をテストで明示カバー
2. **既存 `-w` / `--workflow <path>` との排他関係**: `auto | full | quick` 予約値とパス直指定を両立させる設計（排他にしない）
3. **`--start` / `--max-step-runs` との整合**: `--workflow auto` での再開は初期実装では `--start 1` のみ許可するなどの制約を検討
4. **`claude_sync.py` 運用の継続**: `.claude/` 配下の編集がある場合は `export → 編集 → import` フローを imple_plan 冒頭で明示
5. **`/issue_plan` → 後続 YAML 切替の実走検証**: `auto` モードで `/issue_plan` 実行後に選択された YAML が正しく後続ステップを起動するかを確認（`issue-plan-split-plan-handoff-verification.md` の観察とも連動）

## 事前リファクタリング

**不要**。`claude_loop.py` の `main()` / `_run_steps` / `workflow.resolve_*` の現構造で二段実行（`/issue_plan` → 後続 YAML の step[1:]）は吸収可能。`--workflow` の型変更（Path → str）も argparse の `type=` 差し替えで十分であり、事前の共通化は過剰抽象。

## 成果物

- `docs/util/ver9.0/IMPLEMENT.md`（`/split_plan` で作成）
- `docs/util/ver9.0/MEMO.md`（実装中の残課題メモ、`/issue_plan` → `/split_plan` 引き継ぎ観察結果もここに記録）
- `docs/util/ver9.0/CURRENT.md` + `CURRENT_scripts.md` / `CURRENT_skills.md` / `CURRENT_tests.md`（`/write_current` で ver8.0 から差分追加）
- `docs/util/ver9.0/RETROSPECTIVE.md`（`/retrospective` で作成）

## このバージョンで **やらないこと**

- `--workflow auto` の実装以外の PHASE6.0 拡張（例: カテゴリ横断 ISSUE 選定、第 3 ワークフロー追加）
- `issue_worklist.py` の `--limit` 追加（`issue-worklist-json-context-bloat.md` 除外理由参照）
- `issue_review` SKILL の実動作確認（app/infra ワークフロー起動待ち）
- `/issue_plan` SKILL 自身のロジック変更（ver8.0 で確定、frontmatter 書込のみ活用）
- `quick_plan` 関連処理の追加変更（ver8.0 で削除済み）
