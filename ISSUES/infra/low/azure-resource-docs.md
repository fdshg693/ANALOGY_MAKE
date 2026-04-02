# Azure リソース作成手順のドキュメント化

## 概要

Azure リソース（リソースグループ・App Service）の作成手順を `docs/infra/` に独立ドキュメントとして整備する。

## 背景

- 現在は `docs/infra/ver1.0/PHASE1.0.md` に az CLI コマンドが最低限記載されている
- 初回セットアップや別環境への展開時に、まとまった手順書があると便利
- ver1.0 のスコープ外のため先送り

## 含めるべき内容

- リソースグループの作成
- App Service プランの作成
- Web App の作成
- 環境変数の設定（`NUXT_OPENAI_API_KEY`, `NUXT_TAVILY_API_KEY`）
- 起動コマンドの設定
- GitHub Secrets の設定手順
