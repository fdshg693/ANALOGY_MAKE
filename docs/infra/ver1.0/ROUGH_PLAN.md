# ver1.0: Azure App Service Free への初回デプロイ

## 対応元

MASTER_PLAN PHASE1.0「Azure App Service Free への初回デプロイ」

## 概要

ANALOGY_MAKE を Azure App Service Free (F1, Linux) にデプロイし、ブラウザからアクセスして動作する状態にする。

現在のアプリはローカル開発専用の構成になっており、デプロイに必要な以下の要素がすべて未整備:

- Nitro ビルドプリセット（node-server）
- SQLite データベースパスの本番環境向け切り替え
- CI/CD パイプライン（GitHub Actions）
- 運用補助スクリプト（Justfile）

## ユーザー体験の変化

- **Before**: ローカルの `pnpm dev` でのみアクセス可能
- **After**: `https://{app-name}.azurewebsites.net` からブラウザでアクセスでき、チャット・スレッド管理・会話履歴の永続化がすべて動作する

## スコープ

### 含むもの

1. **Nuxt ビルド設定の調整** — Nitro preset を `node-server` に設定し、App Service で起動可能にする
2. **SQLite パスの環境ベース切り替え** — 開発環境は `./data/`、本番は `/home/data/`（App Service 永続ストレージ）を使用する
3. **better-sqlite3 のクロスプラットフォーム対応** — ローカル（Windows）と App Service（Linux）の差異を GitHub Actions の Linux ビルドで吸収する
4. **GitHub Actions ワークフロー** — `main` ブランチ push 時に自動ビルド＋デプロイするパイプラインを構築する
5. **Justfile** — Azure CLI 操作（ログ確認・再起動・環境変数一覧・SSH接続など）をコマンドランナーでラップする
6. **動作確認チェックリスト** — デプロイ後に確認すべき項目を文書化する

### 含まないもの

- Azure リソースの実際の作成（手動で az CLI を実行。手順は PHASE1.0 に記載済み）
- 環境変数の実際の設定（手動で az CLI を実行）
- GitHub Actions の認証設定（Publish Profile の取得・Secrets への登録は手動操作）
- カスタムドメイン・SSL・監視・バックアップ
- 認証・ユーザー管理

## 備考

- CLAUDE.md の「やらないこと」に「本番デプロイ」が記載されているが、これは app カテゴリの方針。infra カテゴリの MASTER_PLAN で明示的にデプロイが計画されているため、矛盾しない
- Azure リソース名 `analogy-make` は `*.azurewebsites.net` で一意である必要があり、実際の作成時に調整が必要
- Free プラン (F1) のコールドスタート（数秒〜十数秒）は個人利用として許容する
