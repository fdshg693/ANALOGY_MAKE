---
name: retrospective
disable-model-invocation: true
user-invocable: true
---

# 役割

あなたは、最新のバージョンアップの結果・結果が出るまでの過程を振り返り、次のバージョンアップに向けて改善点を洗い出す役割を担います。
実装結果は直前のGitコミットとの差分で表されるものとします。

## 1. ドキュメント構成整理
- `docs\{カテゴリ}\MASTER_PLAN.md` への追加・ファイル分割・再構成が必要かの検討・提案
  - `ISSUES` が肥大化しだした場合、ほぼマスタープランが実装済などの場合は、新たなバージョン・構成のマスタープランの作成が有効な可能性があります
- **現行 PHASE 完走時の対応**: `docs/{カテゴリ}/MASTER_PLAN/PHASE{N}.md` の最新 PHASE が「すべて実装済」となった場合、次 PHASE の骨子（`PHASE{N+1}.md`）作成の要否を検討する
  - 新 PHASE の具体化作業（骨子の執筆）は `/retrospective` の責務外。次 `/issue_plan` で判断させる
  - 既存 ISSUES で当面吸収できる場合は、PHASE 新設を焦らず本 RETROSPECTIVE §3 で「次バージョンは ISSUES 消化」と明示する
  - 既存 ISSUES で吸収できない規模のテーマが見えている場合のみ、本 RETROSPECTIVE に PHASE 新設の方向性メモを残す
- `CLAUDE.md` の分割検討・提案
  - 肥大化しないように、サブフォルダ固有の内容はサブフォルダ内の `CLAUDE.md` に分割するなどの方法が考えられます

## 2. バージョン作成の流れの検討

以下のバージョン作成の流れが、どれほど効果的だったかを振り返る。
そのうえで、改善点が考えられる場合は、提案すること。
バージョン作成で活用されている `.claude` 配下のスキル等のファイルをどのように変更することが必要かも提案すること。

### バージョン作成の流れ
- カテゴリ: !`cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app`
- 最新バージョン番号: !`bash .claude/scripts/get_latest_version.sh`
- 最新のバージョン作成の結果が `docs/{カテゴリ}/ver{最新バージョン番号}/` に記載されている

各バージョンは以下の6ステップで作成される（フルワークフロー）。本スキルはステップ6に相当する:

1. `/issue_plan` — 現状把握・ISSUE レビュー・`ROUGH_PLAN.md` 作成（frontmatter に `workflow: quick | full` / `source: issues | master_plan` を記録）を行った
2. `/split_plan` — `ROUGH_PLAN.md` を受けて `REFACTOR.md` ・ `IMPLEMENT.md` を作成し、plan_review_agent で実装計画の review を行った
3. `/imple_plan` — 計画に基づいて実装し、`MEMO.md` に実装メモを記載した
4. `/wrap_up` — `MEMO.md` の各項目に対応し、細かい改善を行った
5. `/write_current` — `CURRENT.md` ・ `CLAUDE.md` の作成・更新を行った
6. `/retrospective` — **（本ステップ）** 振り返りを行い、次バージョンへの改善点を整理する

（軽量ワークフロー quick は `/issue_plan → /quick_impl → /quick_doc` の 3 ステップ構成。本スキルは quick には含まれない）

## 3. 次バージョンの種別推奨

次バージョン判定の材料は以下 3 点。どれか一つだけで決めず、3 点を突き合わせて判断する:

1. **ISSUE 状況**（`issue_worklist.py` 結果）: `ready / ai` の件数・優先度・性質
2. **MASTER_PLAN の次項目**: 現行 PHASE に未実装の節が残っているか
3. **現行 PHASE 完走状態**: 最新 PHASE の全節が実装済なら、次 PHASE 骨子作成 or 既存 ISSUES 消化のどちらに寄せるかを明示する

次バージョンの方針を決める前に、AI が着手可能・レビュー待ちの ISSUE を把握する:

- 現在カテゴリの着手候補: !`python scripts/issue_worklist.py`
- 機械可読形式: !`python scripts/issue_worklist.py --format json`

次に予定されるタスク（MASTER_PLAN の次項目、未解決 ISSUES）を踏まえて、次バージョンがメジャー・マイナーのどちらが適切かを推奨する。

- 次のマイナーバージョン候補: !`bash .claude/scripts/get_latest_version.sh next-minor`
- 次のメジャーバージョン候補: !`bash .claude/scripts/get_latest_version.sh next-major`

## 4. 振り返り結果の記録

- 振り返り結果を `docs/{カテゴリ}/ver{最新バージョン番号}/RETROSPECTIVE.md` に記録する
- スキルへの改善提案がある場合は、提案だけでなく本ステップ内で `.claude/skills/` 配下のファイルを直接編集して即時適用する（次バージョンへの持ち越しを防ぐ）
  - **即時適用してよい変更**: SKILL 内の文言修正・手順追記・判断基準の追加・既存ガイドラインの明確化・SKILL の新規作成・ワークフローステップの追加/削除・エージェント定義の変更など、ほとんど全ての`.claude`配下ファイルや、ワークフロースクリプトの設定ファイル
  - **ユーザー確認が必要な変更**: リスクのあるスクリプトのワークフローへの組み込み、過度に大量の既存ファイルの変更を伴うもの（目安: 計500行以上）、新規追加に関してはユーザー確認は不要
- ISSUES ファイルの整理（PHASE5.0 以降のステータス対応）:
  - **対応済み（実装が完了し、ISSUE の目的を果たした）** → 削除する
  - **持ち越し中（`status: ready / ai` で残してある、`status: need_human_action / human` で人間対応待ち、または明示的に次バージョン以降に先送り宣言したもの）** → 削除しない。MEMO.md / 当 RETROSPECTIVE.md に持ち越し理由を記載
  - frontmatter 無し（`raw / human` 扱い）→ 触らない
- `REQUESTS/AI/` の整理（当バージョンで消費済みのリクエストを片付ける）:
  - `REQUESTS/AI/*.md` を走査し、当バージョン固有の用済みファイル（ファイル名やサブタイトルに `ver{X.Y}` を含み、そのバージョン完了をもって役目を終えるもの、および本文に「本バージョン完了後に削除してください」等の自己削除指示があるもの）を削除する
  - 継続対応が必要なリクエスト（後続バージョンでも参照されるもの）は残す
  - 削除したファイルは本 RETROSPECTIVE.md §「即時適用したスキル変更」または §「対応済み」欄に列挙する

## 5. Git にコミットする

### 即時適用の検証

コミット前に、本ステップで即時適用したスキル変更が実際にステージングに含まれていることを確認する:

1. `git add` で変更をステージングする
2. `git diff --cached --name-only` を実行し、即時適用対象のファイルが含まれていることを確認する
3. 含まれていない場合は、適用漏れの変更を再度実施してからステージングする

### コミット・プッシュ

- 今回の変更内容を元にコミットメッセージを作成して、コミット・プッシュを行ってください
