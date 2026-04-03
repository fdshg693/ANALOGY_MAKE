# ver2.0 コード現況

## Bicep インフラ定義

### infra/main.bicep（40行）

サブスクリプションスコープのエントリポイント。Resource Group を作成し、モジュールを呼び出す。

- `targetScope = 'subscription'` — Resource Group の作成もテンプレートに含めるため
- パラメータ: `location`（default: `japaneast`）、`resourceGroupName`（default: `rg-analogy-make`）、`appServicePlanName`（default: `plan-analogy-make`）、`webAppName`（default: `analogy-make`）
- `@secure()` パラメータ: `openaiApiKey`、`tavilyApiKey` — ファイルに記載せず、デプロイ時にプロンプトで入力
- リソース: `Microsoft.Resources/resourceGroups@2024-03-01`
- モジュール呼び出し: `modules/app-service-plan.bicep`（`scope: rg`）、`modules/web-app.bicep`（`scope: rg`）
- 出力: `webAppUrl`（Web App の HTTPS URL）

### infra/main.bicepparam（10行）

パラメータファイル。`using './main.bicep'` で main.bicep を参照。

- 非シークレットパラメータの値を定義（location, resourceGroupName, appServicePlanName, webAppName）
- `openaiApiKey`・`tavilyApiKey` は `@secure()` のため記載しない（デプロイ時に Azure CLI がプロンプトで入力を求める）

### infra/modules/app-service-plan.bicep（18行）

App Service Plan モジュール。

- パラメータ: `name`、`location`
- リソース: `Microsoft.Web/serverfarms@2024-04-01`
- 設定: `kind: 'linux'`、SKU `F1`（Free）、`reserved: true`（Linux 必須）
- 出力: `id`（App Service Plan のリソース ID、Web App モジュールが参照）

### infra/modules/web-app.bicep（28行）

Web App + 設定モジュール。

- パラメータ: `name`、`location`、`appServicePlanId`、`@secure() openaiApiKey`、`@secure() tavilyApiKey`
- リソース: `Microsoft.Web/sites@2024-04-01`
- 設定:
  - `linuxFxVersion: 'NODE|22-lts'`
  - `appCommandLine: 'node server/index.mjs'` — deploy.yml が `.output/` の中身を wwwroot にデプロイするため、wwwroot 基準のパス
  - `appSettings`: `NUXT_OPENAI_API_KEY`、`NUXT_TAVILY_API_KEY`、`NODE_ENV=production`
- F1 プランでは Always On 非対応のため `alwaysOn` は設定しない
- 出力: `url`（`https://${app.properties.defaultHostName}`）

## DB パス管理

### server/utils/db-config.ts（11行）

DB パスとディレクトリ初期化を一元管理するモジュール。

- `NODE_ENV === 'production'` の場合: `/home/data/langgraph-checkpoints.db`（Azure App Service 永続ストレージ）
- それ以外: `./data/langgraph-checkpoints.db`（ローカル開発）
- モジュール読み込み時に `mkdirSync(DB_DIR, { recursive: true })` でディレクトリを自動作成
- `DB_PATH` を named export し、`analogy-agent.ts` と `thread-store.ts` から参照される

### server/utils/analogy-agent.ts（DB 関連部分）

- `import { DB_PATH } from "./db-config"` で DB パスを取得
- `SqliteSaver.fromConnString(DB_PATH)` で LangGraph チェックポイントを永続化
- 起動時に `console.log` で DB パスをログ出力

### server/utils/thread-store.ts（DB 関連部分）

- `import { DB_PATH } from './db-config'` で DB パスを取得
- `new Database(DB_PATH)` で better-sqlite3 の接続を初期化
- WAL モード有効化済み

## Nuxt ビルド設定

### nuxt.config.ts（16行）

- `compatibilityDate: '2025-07-15'`
- `devtools: { enabled: true }`
- `runtimeConfig.openaiApiKey` / `runtimeConfig.tavilyApiKey` — 環境変数経由で注入
- `nitro.preset: 'node-server'` — Azure App Service 向けの Node.js サーバーモード
- `nitro.externals.external: ['better-sqlite3']` — ネイティブモジュールをバンドル対象から除外
- ビルド成果物: `.output/server/index.mjs`（App Service の起動コマンドに使用）

## CI/CD

### .github/workflows/deploy.yml

GitHub Actions ワークフロー。`main` ブランチへの push 時に自動実行。

| ステップ | 内容 |
|---|---|
| checkout | `actions/checkout@v4` |
| pnpm セットアップ | `pnpm/action-setup@v4`（`package.json` の `packageManager` フィールドからバージョン検出） |
| Node.js セットアップ | `actions/setup-node@v4`（Node 22、pnpm キャッシュ有効） |
| 依存インストール | `pnpm install --frozen-lockfile` |
| ビルド | `pnpm build` |
| デプロイ | `azure/webapps-deploy@v3`（Publish Profile 認証、`.output/` をデプロイ） |

認証方式: Publish Profile（`secrets.AZURE_WEBAPP_PUBLISH_PROFILE` に登録が必要）

## 運用ツール

### Justfile（53行）

Azure CLI 操作をラップするコマンドランナー。`az login` 済みが前提。

変数定義: `app_name := "analogy-make"`、`resource_group := "rg-analogy-make"`

#### App Service 運用コマンド

| コマンド | 説明 |
|---|---|
| `just logs` | Azure App Service のリアルタイムログ出力 |
| `just restart` | App Service の再起動 |
| `just env-list` | App Service の環境変数一覧をテーブル表示 |
| `just ssh` | App Service コンテナへの SSH 接続 |
| `just preview` | ローカルビルド + `node .output/server/index.mjs` で本番相当のプレビュー |

#### インフラ管理コマンド（Bicep）

| コマンド | 説明 |
|---|---|
| `just deploy-infra` | `az deployment sub create` でインフラのデプロイ（初回作成 / 更新） |
| `just preview-infra` | `az deployment sub what-if` で変更のプレビュー |
| `just destroy-infra` | `az group delete` で Resource Group ごと削除（`--yes` 付き） |
| `just get-publish-profile` | Publish Profile の XML を取得（GitHub Actions 用） |

- `deploy-infra`・`preview-infra` は `--location japaneast` をリテラル指定（Bicep パラメータファイルと一致）
- `destroy-infra`・`get-publish-profile` は既存変数 `app_name`・`resource_group` を使用

## Azure 環境の設定状況

### 初回セットアップ手順

Bicep テンプレートにより、以下の手順で環境構築が可能:

1. `az login` — Azure にログイン
2. `just deploy-infra` — インフラのデプロイ（API キーのプロンプト入力あり）
3. `just get-publish-profile` — Publish Profile を取得
4. GitHub リポジトリの Secrets に `AZURE_WEBAPP_PUBLISH_PROFILE` として登録
5. `git push origin main` — GitHub Actions が自動デプロイ

### Bicep で管理されるリソース

| リソース | 名前 | 設定 |
|---|---|---|
| Resource Group | `rg-analogy-make` | `japaneast` |
| App Service Plan | `plan-analogy-make` | F1 (Free), Linux |
| Web App | `analogy-make` | Node.js 22 LTS, 起動コマンド `node server/index.mjs` |

### Bicep で管理されない項目

- GitHub Secrets の登録（手動操作）
- `az login`（ローカル認証）

## 未解決の課題

| ISSUE | 優先度 | 内容 |
|---|---|---|
| `ISSUES/infra/medium/verify-output-dir-azure.md` | Medium | `.output/` ディレクトリが Azure App Service と互換性があるか、初回デプロイ時に要検証 |

※ `ISSUES/infra/low/azure-resource-docs.md` は ver2.0 の Bicep テンプレートで代替されたためクローズ済み

## 技術的判断

### Nitro preset に `node-server` を採用

Azure App Service は Node.js ランタイムを直接実行するため、`node-server` プリセットが最適。Nuxt の SPA モードやスタティック生成は SSR + API Routes の要件に合わないため不採用。

### DB パスの環境切り替えに `NODE_ENV` を使用

Nuxt は本番ビルド時に `NODE_ENV=production` を設定するため、追加の環境変数なしでパスを切り替えられる。Azure App Service の `/home/data/` はデプロイで上書きされない永続ストレージであり、DB ファイルの安全な配置先となる。

### Publish Profile 認証を採用

Service Principal や OIDC と比較して設定が最もシンプル。個人プロジェクトの Free プランでは十分。Azure Portal からダウンロード → GitHub Secrets に登録するだけで完了。

### Justfile に `deploy` コマンドを含めない

デプロイは GitHub Actions で自動化されているため、手動デプロイコマンドの二重管理を避けた。`just preview` でローカルでの本番ビルド確認は可能。

### Bicep でサブスクリプションスコープを採用

`targetScope = 'subscription'` により、Resource Group の作成もテンプレートに含めた。これにより `just deploy-infra` 一発で全リソースを構築できる。

### モジュール分割（App Service Plan / Web App）

リソースの責務を分離し、各モジュールの可読性を確保。将来的なリソース追加時にもモジュール単位で管理しやすい。

### @secure() パラメータで API キーを管理

`.bicepparam` にシークレットを記載せず、デプロイ時にプロンプトで入力する設計。Key Vault は F1 プランでは過剰なため不採用。フォールバックとして `--parameters openaiApiKey=xxx tavilyApiKey=yyy` のインライン指定も可能。

### インフラ CI/CD は不要

個人プロジェクトでインフラ変更は低頻度のため、ローカルからの `just deploy-infra` 手動実行で十分。将来的に必要になれば別途対応。
