# ver2.1 タスク概要

小規模タスクのため REFACTOR 省略

## 対象 ISSUE

`ISSUES/infra/high/Actionデプロイ.md` — GitHub Actions デプロイ後、Azure App Service でランタイムエラーが発生しアプリが動作しない

## 現象

GitHub Actions で `pnpm build` → `.output/` を Azure にデプロイした後、全ページで HTTP 500 エラー:

```
Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'hookable'
imported from /home/site/wwwroot/server/node_modules/unhead/dist/server.mjs
```

## 根本原因

pnpm は `node_modules` 内でシンボリックリンクを使って依存関係を管理する。Nitro の `node-server` プリセットは一部のパッケージを外部化（externalize）し、`.output/server/node_modules/` に配置するが、この中の依存ツリーも pnpm のシンボリックリンク構造になっている。

Azure App Service へのデプロイ時（`azure/webapps-deploy@v3`）にシンボリックリンクが正しく転送されず、`unhead` → `hookable` の解決チェーンが壊れる。

## 目標

GitHub Actions 経由のデプロイで、Azure App Service 上でアプリが正常に起動・動作するようにする。

## スコープ

- GitHub Actions ワークフロー（`.github/workflows/deploy.yml`）の修正
- 必要に応じて Nuxt/Nitro ビルド設定（`nuxt.config.ts`）の調整
- 対象 ISSUE のクローズ
- 関連する medium ISSUE（`verify-output-dir-azure.md`）の検証結果反映

## スコープ外

- Windows ローカルデプロイの問題（`Windowsデプロイ.md`）は別バージョンで対応
- Node.js 20 非推奨警告（`action_warning.md`）は別バージョンで対応
