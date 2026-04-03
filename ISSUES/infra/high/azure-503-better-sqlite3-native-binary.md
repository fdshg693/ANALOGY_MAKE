# Azure App Service 503エラー: better-sqlite3 ネイティブバイナリ不一致

## 現象

- `https://analogy-make.azurewebsites.net/` にアクセスすると、約65秒後に **HTTP 503** が返る
- `az webapp show` では `State: Running` だが、コンテナが起動に失敗している
- SCM (Kudu) も 502 を返し、ログ取得不可
- ログテール (`az webapp log tail`) も出力なし

## 原因

`.output/server/node_modules/better-sqlite3/build/Release/better_sqlite3.node` が **Windows PE (DLL) x86-64** 形式になっている。

Azure App Service は **Linux (NODE|22-lts)** で動作するため、Windows 用ネイティブバイナリはロードできず、Node.js プロセスが即座にクラッシュする。

### なぜ Windows バイナリが含まれるか

初回デプロイ時に **Windows ローカル環境から `just preview` 等でビルドした `.output/` をそのまま Azure にデプロイした**ため。`pnpm build` が Windows 上で実行され、`better-sqlite3` の Windows 用ネイティブバイナリ (PE DLL) が `.output/` に含まれた状態でデプロイされた。

## 考えられる対処方法

### 1. GitHub Actions を手動トリガーして再デプロイ

アプリコードに軽微な変更（空行追加等）を加えて main に push し、GitHub Actions でのビルド・デプロイを再実行する。Ubuntu 上でビルドされれば Linux 用バイナリが含まれる。

### 2. GitHub Actions に手動トリガーを追加

```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:  # 手動トリガー追加
```

これにより、コード変更なしでも再デプロイ可能になる。

### 3. Bicep デプロイ時の appSettings 競合を確認

`infra/modules/web-app.bicep` の `appSettings` は配列で定義されているため、`az deployment sub create` 実行時に GitHub Actions が設定した環境変数（`WEBSITE_HTTPLOGGING_RETENTION_DAYS` 等）が上書き・消去される可能性がある。Bicep とアプリデプロイの設定管理を分離する検討が必要。

### 4. スタートアップコマンドの確認

現在の `appCommandLine` は `node server/index.mjs`。デプロイパッケージが `.output/` の場合、Azure 上のパスは `/home/site/wwwroot/server/index.mjs` になるため正しいが、パッケージ構造が想定通りか SSH またはログで確認する価値がある。
