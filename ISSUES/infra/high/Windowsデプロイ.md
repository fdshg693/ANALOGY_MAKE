# Windows環境でjustコマンドでデプロイした場合のエラー

Azure App Service 503エラー: better-sqlite3 ネイティブバイナリ不一致

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

## 理想的な対処方法

- 可能な限りWindowsでデプロイできるようにしたい
  - Docker等を利用するのはOK