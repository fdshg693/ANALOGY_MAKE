# ROUGH_PLAN: util ver3.0

## バージョン種別

**メジャーバージョン (3.0)** — MASTER_PLAN PHASE3.0 の新項目に着手。新規 SKILL 3 個・新規 YAML 定義・CLI フラグ追加を含む。

## 対応内容

**MASTER_PLAN PHASE3.0: 軽量ワークフロー `quick` の導入**

## 背景

現在の 5 ステップフルワークフロー（split_plan → imple_plan → wrap_up → write_current → retrospective）は、小規模な修正（ISSUES 1 件対応、バグ修正等）に対してオーバーキル。ver2.2 RETROSPECTIVE でも「変更ファイル 2 つ・追加行 91 行に対して 5 ステップは重い」と指摘されている。

## 提供する機能

### 軽量ワークフロー `quick`（3 ステップ）

既存のフルワークフローに加えて、小規模タスク向けの 3 ステップワークフローを新設する:

```
/quick_plan → /quick_impl → /quick_doc
```

- **quick_plan**: ISSUE 選定 + 簡潔な計画（ROUGH_PLAN.md のみ。REFACTOR/IMPLEMENT 不要、plan_review_agent 省略）
- **quick_impl**: 実装 + MEMO + typecheck + wrap_up 統合 + コミット
- **quick_doc**: CHANGES.md 作成 + CLAUDE.md 更新確認 + ISSUES 整理 + コミット

### ワークフロー選択の仕組み

`claude_loop.py` に `-w` フラグを追加し、ワークフロー YAML ファイルを切り替えられるようにする:

```bash
# フルワークフロー（デフォルト、従来通り）
python scripts/claude_loop.py

# 軽量ワークフロー
python scripts/claude_loop.py -w scripts/claude_loop_quick.yaml
```

### ワークフロー選択ガイドライン

どちらのワークフローを使うべきかの判断基準を WORKFLOW.md に追記する。基本方針:
- **full**: メジャーバージョン、アーキテクチャ変更、4 ファイル以上の変更
- **quick**: マイナーバージョン、単一 ISSUE 対応、3 ファイル以下の変更

## スコープ

- 既存のフルワークフロー（5 ステップ）は一切変更しない
- ワークフローの自動選択（AI 判定）は行わない
- quick ワークフローでの retrospective は省略（軽量タスクではフロー改善の知見が少ないため）
