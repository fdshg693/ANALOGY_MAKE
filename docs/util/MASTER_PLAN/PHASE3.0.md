# PHASE3.0: ワークフロー種別の拡張（軽量ワークフローの導入）

## 概要

現在の 5 ステップフルワークフロー（split_plan → imple_plan → wrap_up → write_current → retrospective）に加えて、小規模タスク向けの軽量ワークフローを導入する。
YAML 定義で複数のワークフローを切り替え可能にし、タスクの規模に応じた適切な開発フローを選択できるようにする。

## 動機

- 現状の 5 ステップワークフローは、小規模な修正（ISSUES の 1 件対応、typo 修正等）に対してオーバーキル
- split_plan の「小規模タスク判定」で REFACTOR.md を省略できるが、ワークフロー自体のステップ数は変わらない
- SKILL 実行 1 回あたりのコンテキスト読み込み・計画確認のオーバーヘッドが、修正量に対して大きすぎるケースがある
- 5 ステップすべてを回すと、1 バージョンあたり 30 分〜1 時間以上かかることがあり、簡単な修正には不釣り合い

## 前提条件

- PHASE2.0 が実装済み（ログ・モード設定の基盤が利用可能であること）
- 既存の 5 ステップワークフローは変更しない（新ワークフローを追加する形）

## やること

### 1. ワークフロー種別の定義

#### フルワークフロー（既存: `full`）

```
/split_plan → /imple_plan → /wrap_up → /write_current → /retrospective
```

**適用**: メジャーバージョンアップ、複数ファイルにまたがる変更、新機能追加

#### 軽量ワークフロー（新規: `quick`）

```
/quick_plan → /quick_impl → /quick_doc
```

**適用**: マイナーバージョンアップ、単一 ISSUE 対応、3 ファイル以下の変更

**ステップ詳細**:

| ステップ | 役割 | 出力 |
|---|---|---|
| `/quick_plan` | ISSUE 選定 + 簡潔な計画（ROUGH_PLAN.md のみ） | `ROUGH_PLAN.md`（簡潔版） |
| `/quick_impl` | 実装 + MEMO + typecheck + コミット | コード変更, `MEMO.md`, git commit |
| `/quick_doc` | CHANGES.md 作成 + CLAUDE.md 更新 + ISSUES 整理 + コミット | `CHANGES.md`, git commit |

**フルワークフローとの差分**:
- `REFACTOR.md` / `IMPLEMENT.md` を作成しない（ROUGH_PLAN.md に実装方針を簡潔に記載）
- plan_review_agent による承認を省略
- wrap_up を quick_impl に統合（MEMO 項目が少ないため）
- retrospective を省略（軽量タスクでフロー改善の知見は得にくい）
- CURRENT.md は作成しない（マイナーバージョン専用のため CHANGES.md のみ）

### 2. YAML による複数ワークフロー定義

`scripts/` 配下にワークフロー種別ごとの YAML を配置する:

```
scripts/
├── claude_loop.py
├── claude_loop.yaml          # フルワークフロー（既存、リネームなし）
└── claude_loop_quick.yaml    # 軽量ワークフロー
```

#### `scripts/claude_loop_quick.yaml`

```yaml
mode:
  auto: false

command:
  executable: claude
  prompt_flag: -p
  args:
    - --dangerously-skip-permissions
  auto_args:
    - --disallowedTools "AskUserQuestion"
    - >-
      --append-system-prompt "you cannot ask questions to the user. ..."

steps:
  - name: quick_plan
    prompt: /quick_plan

  - name: quick_impl
    prompt: /quick_impl

  - name: quick_doc
    prompt: /quick_doc
```

#### 実行方法

```bash
# フルワークフロー（デフォルト）
python scripts/claude_loop.py

# 軽量ワークフロー
python scripts/claude_loop.py -w scripts/claude_loop_quick.yaml
```

### 3. 軽量ワークフロー用 SKILL の作成

#### `/quick_plan`

`.claude/SKILLS/quick_plan/SKILL.md`:

- 最新バージョン情報・ISSUES の参照（split_plan と同様）
- **マイナーバージョンのみ**（メジャーが必要と判断した場合はユーザーに報告してフルワークフローへの切り替えを推奨）
- `ROUGH_PLAN.md` に以下を記載:
  - 対応する ISSUE（1〜2 件）
  - 変更対象ファイル（3 つ以下）
  - 変更方針（5〜10 行程度の簡潔な記述）
- plan_review_agent は起動しない

#### `/quick_impl`

`.claude/SKILLS/quick_impl/SKILL.md`:

- `ROUGH_PLAN.md` の変更方針に基づいて実装
- typecheck 実施（最低 1 回）
- `MEMO.md` に実装メモ（ある場合のみ）
- MEMO 項目がある場合はその場で対応（wrap_up 相当を統合）
- git コミット

#### `/quick_doc`

`.claude/SKILLS/quick_doc/SKILL.md`:

- `CHANGES.md` の作成（git diff ベースで記載漏れ検証）
- `CLAUDE.md` の更新確認
- `MASTER_PLAN.md` の更新（該当する場合）
- 解決した ISSUES ファイルの削除
- git コミット

### 4. ワークフロー選択ガイドライン

SKILL ドキュメントや WORKFLOW.md に、どちらのワークフローを選ぶべきかのガイドラインを追記する:

| 条件 | 推奨ワークフロー |
|---|---|
| MASTER_PLAN の新項目着手 | `full` |
| アーキテクチャ変更 | `full` |
| 新規外部ライブラリ導入 | `full` |
| 変更ファイル 4 つ以上 | `full` |
| ISSUES/high の対応（複雑） | `full` |
| ISSUES の 1 件対応（単純） | `quick` |
| バグ修正（原因特定済み） | `quick` |
| 既存機能の微調整 | `quick` |
| ドキュメント・テスト追加 | `quick` |
| 変更ファイル 3 つ以下 | `quick` |

## ファイル変更一覧

| ファイル | 操作 | 内容 |
|---|---|---|
| `.claude/SKILLS/quick_plan/SKILL.md` | 新規作成 | 軽量版計画ステップ |
| `.claude/SKILLS/quick_impl/SKILL.md` | 新規作成 | 軽量版実装ステップ |
| `.claude/SKILLS/quick_doc/SKILL.md` | 新規作成 | 軽量版ドキュメントステップ |
| `scripts/claude_loop_quick.yaml` | 新規作成 | 軽量ワークフロー定義 |
| `.claude/SKILLS/meta_judge/WORKFLOW.md` | 変更 | ワークフロー種別の説明を追記 |

## やらないこと

- ワークフローの自動選択（タスク内容から full/quick を AI が判定する機能）
- 2 種以外のワークフロー追加（当面は full と quick の 2 種で十分）
- 既存の full ワークフローの変更（追加のみ）
- quick ワークフローでの retrospective（軽量タスクではフロー改善の知見が少ないため省略）
