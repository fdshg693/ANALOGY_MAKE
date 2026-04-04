---
name: quick_doc
description: 軽量ワークフロー用のドキュメントステップ（CHANGES.md + ISSUES整理）
disable-model-invocation: true
user-invocable: true
---

## コンテキスト

- カテゴリ: !`cat .claude/CURRENT_CATEGORY 2>/dev/null || echo app`
- 最新バージョン番号: !`bash .claude/scripts/get_latest_version.sh`

## ドキュメント作成

### CHANGES.md の作成

最新バージョンフォルダ配下に `CHANGES.md` を作成する。

1. `git diff --name-status` で前バージョンからの変更ファイルを確認する
2. 以下のセクションで構成する:
   - `## 変更ファイル一覧` — 変更・追加・削除されたファイルとその概要
   - `## 変更内容の詳細` — 各変更の技術的な説明（なぜ・何を・どう変えたか）
   - `## API変更` — APIの追加・変更がある場合のみ
   - `## 技術的判断` — 新たな技術的判断があった場合のみ

### git diff による検証

ドキュメント作成後、以下の手順で記載漏れがないか検証する:

1. 前バージョンのコミットから現在の HEAD までの `git diff --name-status` を実行
2. diff に含まれるコード変更ファイル（`docs/` や `ISSUES/` を除く）が `CHANGES.md` に記載されているか確認
3. 未記載のファイルがあれば追記する

## 更新確認

### CLAUDE.md の更新

プロジェクトルートの `CLAUDE.md` を確認し、以下の情報が最新であることを確認する:
- 技術スタック（バージョン番号、新規ライブラリ追加など）
- ディレクトリ構成（新規フォルダ・ファイルが追加された場合）
- 開発上の注意（新たに発覚した注意点）

変更が必要な場合のみ更新を提案する。

### MASTER_PLAN.md の更新

`docs/{カテゴリ}/MASTER_PLAN.md` に該当する項目があれば、ステータスを更新する。

### ISSUES の整理

今回のバージョンで解決した `ISSUES/{カテゴリ}` 配下のファイルがあれば削除する。

## Git にコミットする
- コミットメッセージ: `docs(ver{バージョン番号}): quick_doc完了`
- **プッシュする**（quick ワークフローの最終ステップのため）
