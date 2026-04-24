# ver15.3 MEMO

`/imple_plan` 実施メモ。`/split_plan` の IMPLEMENT.md §7 タイムラインに従って SKILL 5 本 + VERSION_FLOW.md + 根 CLAUDE.md + `PLAN_HANDOFF.md` 自己適用を 1 コミットに束ねた記録。

## 計画との乖離

乖離なし。IMPLEMENT.md §7 step 7-1〜7-7 の順序どおり実施:

- 7-1 `python scripts/claude_sync.py export`
- 7-2 SKILL 5 本（`issue_plan` / `split_plan` / `quick_impl` / `meta_judge/WORKFLOW` / `retrospective`）を `.claude_sync/` 配下で編集
- 7-3 `python scripts/claude_sync.py import`
- 7-4 `.claude/plans/VERSION_FLOW.md` 改訂（ステップ 7-2 と併せて claude_sync.py 経由で同期処理、import は 7-3 で一括）
- 7-5 `CLAUDE.md`（プロジェクトルート）改訂
- 7-6 `docs/util/ver15.3/PLAN_HANDOFF.md` 新規作成（自己適用 / 選択肢 A）

`issue_plan/SKILL.md` の改訂は当初想定した「L86-L103 の節タイトル改題」を超えて、「仕分け方針 table + quick/full 記載粒度 table + 省略条件 + 情報引き継ぎ」を新節として束ねる構成に変更した（IMPLEMENT §2.1 で新規追加節として予定されていたものと実質的に等価だが、文書構造としては 1 節ではなく複数節に分けたほうが読みやすいため分割）。計画と矛盾するものではないので MEMO のみに記録。

## リスク・不確実性の検証結果

IMPLEMENT.md §9 の 7 リスク項目について、本バージョン内での検証結果を記録する:

| リスク | 対応 | 結果 |
|---|---|---|
| SKILL 改訂後に次回 `/issue_plan` が PLAN_HANDOFF.md 生成を忘れる | 検証先送り（次ループ ver15.4 `/issue_plan` 実地確認）| ISSUE 起票済: `ISSUES/util/medium/plan-handoff-generation-followup.md` |
| quick 版の最小粒度が曖昧で毎回違う構造になる | 検証済（`issue_plan/SKILL.md` に粒度 table を埋め込み、single source of truth を SKILL 本文に集約）| 受理：次 quick バージョンで実地観察 |
| frontmatter が ROUGH_PLAN.md と PLAN_HANDOFF.md で乖離 | 検証先送り（目視確認のみ、validation.py 追加は ver15.4 以降）| ISSUE 起票済: `ISSUES/util/low/plan-handoff-frontmatter-drift.md` |
| SKILL 本文の文字列を直接参照するテストが壊れる | 検証済（`python -m unittest discover` 252 件全 pass）| 受理：影響なし |
| 過去 docs (ver15.0〜ver15.2) 遡及改変の誘惑 | 検証済（本バージョン内で過去 ROUGH_PLAN.md は一切 touch せず）| 受理：add-only 原則遵守 |
| quick で PLAN_HANDOFF.md 省略乱発 | 検証先送り（1〜2 バージョン運用観察）| ISSUE 起票済: `ISSUES/util/low/plan-handoff-omission-tracking.md` |
| `claude_sync.py` 往復 import 忘れ | 検証済（post-import で再 export → diff 差分ゼロを目視確認）| 受理：手順通り |

3 件の先送りリスクは独立 ISSUE ファイルとして切り出し、MEMO 内に埋もれないようにした（`/imple_plan` SKILL の動作確認 §4 要件）。

## 動作確認結果

- `python -m unittest discover -s scripts/tests -t scripts`: **Ran 252 tests in 0.626s — OK**（ver15.2 と同じ 252 件、回帰なし）
- `npx nuxi typecheck`: 既知の vue-router volar 関連警告のみ（CLAUDE.md 記載の既知事項、ビルド・実行に影響なし）。本バージョンはコード変更を伴わない（Markdown/docs のみ）ため typecheck の挙動はベースラインから変化しない
- `grep -r "PLAN_HANDOFF" .claude/skills/ .claude/plans/ CLAUDE.md`: 各ファイルに追記が反映されていることを目視確認
- `python scripts/claude_sync.py export` 再実行 → `.claude_sync/` 再生成済み

## リファクタリングの必要性を感じた点

- 特になし。本バージョンはコード変更を伴わないため。

## 更新が必要そうなドキュメントと更新内容の案

- `/wrap_up` / `/write_current` 段階で `docs/util/MASTER_PLAN/PHASE7.1.md` L11 の §3 行を「実装済み（ver15.3）」に更新する必要あり（IMPLEMENT.md §6 参照）
- 新フォーマット（仕分け方針 table）が全て SKILL 本文の `issue_plan/SKILL.md` に集約されたため、`CURRENT_skills.md` の `issue_plan` 節を ver15.3 完了時に更新する（`/write_current` タイミング）

## 古くて削除が推奨されるコード・ドキュメントの提案

- 特になし。VERSION_FLOW.md Before 側（L88）は add-only 原則により touch せず残置（過去の移行記録として保持）。
