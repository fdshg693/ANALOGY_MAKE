---
status: raw
assigned: ai
priority: low
reviewed_at: "2026-04-24"
---

# scripts/README.md の「ワークフロー実行」ファイル一覧表に scout YAML が載っていない

## 症状

`scripts/README.md` L17-25 の「ワークフロー実行（`claude_loop` 系）」ファイル一覧テーブルには以下 3 つの YAML のみが列挙されている:

- `claude_loop.yaml`
- `claude_loop_quick.yaml`
- `claude_loop_issue_plan.yaml`

ver15.0 で追加された `claude_loop_scout.yaml` はこの一覧に入っていない。scout は同じ README の L98-112「scout（能動探索）」節で独立セクションとして紹介されているが、ファイル一覧テーブルだけを見ると「ワークフロー YAML は 3 本だけ」に読めてしまう。

一方、`scripts/USAGE.md` L137 の 4 ファイル同期契約記述や、L141-144 のサンプル YAML 一覧では scout が明示的に 4 つ目として扱われており、README とのあいだに一貫性のズレがある。

## 影響

- 新規参入者が README L17-25 を見て「ワークフロー YAML は 3 本」と早合点するリスク
- `.claude/rules/scripts.md` §3 が「4 ファイル間で同一内容を保つ」と明記している契約と、README の一覧が齟齬している（rule 違反ではないが見通しが悪い）
- README と USAGE で YAML 数の見え方が違う（README: 3 / USAGE: 4）と整合性監査が迷走する

## なぜ今見る価値があるか

- 修正は README L17-25 のテーブルに `claude_loop_scout.yaml` 行を 1 行追記するだけで、3 ファイル / 100 行枠を大きく下回る軽微な修正
- ただし `raw / ai` 保持理由: より本質的な READ ME/USAGE 責務境界整理 ISSUE（`scripts-readme-usage-boundary-clarification.md`、ver14.0 持越し）と一緒にまとめて処理するのが合理的で、単独昇格すると個別作業単位が細かくなりすぎる
- USAGE.md L137 / L141-144 との対照で検証しやすい（乖離具体例が明確）

## 想定修正方向（任意）

1. `scripts/README.md` L17-25 のテーブルに下記行を追加:
   `| claude_loop_scout.yaml | 能動探索ワークフロー（1 ステップ、ver15.0 追加、opt-in） |`
2. `scripts-readme-usage-boundary-clarification.md` の消化タイミング（別バージョン予定）に合流させる選択肢あり
3. 独立消化する場合は `/quick_impl` で 1 行追記のみ

## 参照

- `scripts/README.md` L17-25（ファイル一覧テーブル）
- `scripts/README.md` L98-112（scout 節の独立セクション）
- `scripts/USAGE.md` L137 / L141-144（4 ファイル前提の docs 記述）
- `scripts/claude_loop_lib/workflow.py` L15（`SCOUT_YAML_FILENAME` 定数）
- `ISSUES/util/low/scripts-readme-usage-boundary-clarification.md`（関連既存 ISSUE）
