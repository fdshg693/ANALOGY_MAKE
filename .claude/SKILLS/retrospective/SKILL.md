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

各バージョンは以下の5ステップで作成される。本スキルはステップ5に相当する:

1. `/split_plan` — `ROUGH_PLAN.md` ・ `REFACTOR.md` ・ `IMPLEMENT.md` を作成して、計画を立てた
2. `/imple_plan` — 計画に基づいて実装し、`MEMO.md` に実装メモを記載した
3. `/wrap_up` — `MEMO.md` の各項目に対応し、細かい改善を行った
4. `/write_current` — `CURRENT.md` ・ `CLAUDE.md` の作成・更新を行った
5. `/retrospective` — **（本ステップ）** 振り返りを行い、次バージョンへの改善点を整理する

## 3. 次バージョンの種別推奨

次に予定されるタスク（MASTER_PLAN の次項目、未解決 ISSUES）を踏まえて、次バージョンがメジャー・マイナーのどちらが適切かを推奨する。

- 次のマイナーバージョン候補: !`bash .claude/scripts/get_latest_version.sh next-minor`
- 次のメジャーバージョン候補: !`bash .claude/scripts/get_latest_version.sh next-major`

## 4. Git にコミットする
- 今回の変更内容を元にコミットメッセージを作成して、コミット・プッシュを行ってください
