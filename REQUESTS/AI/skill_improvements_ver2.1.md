# スキル改善提案（ver2.1 retrospective より）

retrospective で2つのスキル改善を特定しましたが、`.claude/skills/` への書き込み権限がなかったため、ここに提案を記録します。

## 1. write_current/SKILL.md — git diff 検証ステップの追加

**問題**: CHANGES.md が `REFACTOR.md`・`IMPLEMENT.md`・`MEMO.md` のみを変更把握のソースとしているため、split_plan 前の調査・修正で行われた計画外の変更が記載漏れする（ver2.1 で Justfile、.gitignore、bicepparam の変更が漏れた）

**追加内容**: ファイル末尾に以下のセクションを追加

```markdown
## git diff による検証（CURRENT.md / CHANGES.md 共通）

ドキュメント作成後、以下の手順で記載漏れがないか検証する:

1. 前バージョンの retrospective コミットから現在の HEAD までの `git diff --name-status` を実行
2. diff に含まれるコード変更ファイル（`docs/` や `ISSUES/` を除く）が、CURRENT.md または CHANGES.md に記載されているか確認
3. 未記載のファイルがあれば追記する（split_plan 前の調査・修正で行われた計画外の変更も含む）
```

## 2. wrap_up/SKILL.md — 既存 ISSUES のステータス更新ガイダンス

**問題**: 修正が適用済みだが未検証の ISSUES について、ステータスが更新されない。ISSUES ファイルを読んだだけでは修正が適用済みであることが分からない

**追加内容**: 「### 進め方」セクションの手順3を以下に差し替え

```markdown
3. ISSUES整理
   - 解決された `ISSUES/{カテゴリ}` フォルダ配下の課題をファイルごと削除
   - 修正適用済みだが外部検証待ち（デプロイ後の確認等）の ISSUES には、ファイル末尾に `## ステータス` セクションを追記して現状を記録する（例: `修正適用済み（ver2.1）、デプロイ検証待ち`）
   - `ISSUES/{カテゴリ}` フォルダに追加する内容をユーザーに提案して、ユーザーの指示に従って追加する
```
