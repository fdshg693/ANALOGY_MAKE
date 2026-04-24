---
name: research_context
description: research workflow の実装前調査 step。RESEARCH.md を生成（--workflow research でのみ起動）
disable-model-invocation: true
user-invocable: true
---

## コンテキスト

- カテゴリ: !`cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app`
- 最新バージョン番号: !`bash .claude/scripts/get_latest_version.sh`
- 今日の日付: !`date +%Y-%m-%d`

## 役割

`research` workflow の 3 step 目。`/split_plan` が作成した `REFACTOR.md` / `IMPLEMENT.md` と `PLAN_HANDOFF.md` を読み、**実装に進む前に必要な外部調査**（公式 docs 確認 / 仕様の裏取り / 類似事例調査）を行い、成果を `docs/{カテゴリ}/ver{X.Y}/RESEARCH.md` に残す。

### `question_research` との責務境界

| 観点 | `question` (`QUESTIONS/`) | `research` (`docs/{cat}/ver{X.Y}/RESEARCH.md`) |
|---|---|---|
| (a) 最終成果物 | 報告書のみ（`docs/{cat}/questions/{slug}.md`） | **コード変更**（`RESEARCH.md` は中間成果物） |
| (b) 入力キュー | `QUESTIONS/{cat}/{priority}/` | `ISSUES/{cat}/{priority}/` または MASTER_PLAN |
| (c) workflow | 調査→報告書で終了（実装に進まない） | 調査→実験→実装→retrospective まで 8 step 完走 |

### やらないこと

- コード変更 / テスト追加 / 実装
- `experiments/` 配下でのスクリプト実行（それは `/experiment_test` の責務）
- 新規 ISSUE 起票（必要なら `IMPLEMENT.md` に追記するにとどめる）

## 手順（3 段階）

### 1. 入力読み込み

以下を確認する:

- `docs/{cat}/ver{X.Y}/ROUGH_PLAN.md`
- `docs/{cat}/ver{X.Y}/PLAN_HANDOFF.md`（存在すれば）
- `docs/{cat}/ver{X.Y}/REFACTOR.md`（存在すれば）
- `docs/{cat}/ver{X.Y}/IMPLEMENT.md`（特に「## リスク・不確実性」節）

### 2. 外部調査（`use-tavily` SKILL 前提）

- 公式 docs / GitHub README / API リファレンスに当たる
- 複数ソース（3 箇所以上）で裏取りした事実のみ「確定」、それ以外は「未確定」として残す
- 証拠は **URL + 参照日** の形で記録（曖昧な「どこかにある」表現は避ける）

### 3. `RESEARCH.md` 出力

出力先: `docs/{カテゴリ}/ver{X.Y}/RESEARCH.md`

以下 4 節を必ず含める（節見出しは固定）:

```markdown
# ver{X.Y} RESEARCH — {短い主題}

## 問い

- `IMPLEMENT.md` の論点から抽出、箇条書き

## 収集した証拠

- URL + 参照日 + 要約の 3 点セット
- 引用元が一次情報か二次情報かを明示

## 結論

- 各問いに対する「確定 / 部分的 / 未確定」
- 「確定」は 3 ソース以上で裏取りしたもののみ

## 未解決点

- 実験（`/experiment_test`）で確かめる必要がある項目
- `EXPERIMENT.md` で検証する仮説を列挙
```

## Git コミット

- `git add docs/{cat}/ver{X.Y}/RESEARCH.md`
- コミットメッセージ: `docs(ver{X.Y}): research_context 完了`
- **プッシュはしない**（後続 step でまとめて push）
