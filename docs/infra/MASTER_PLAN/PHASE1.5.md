# PHASE1.5: Bicep による Azure インフラの IaC 管理

## 概要

PHASE1.0 で手動作成していた Azure リソースを、Bicep テンプレートで宣言的に管理する。
Azure リソースは未作成の状態から始め、`just deploy-infra` 一発でインフラを構築できるようにする。

## 動機

- 手動作成では構成の再現性がなく、見通しが悪い
- Bicep で宣言的に管理することで、構成の全体像をコードとして把握できる
- 環境の再作成・破棄がコマンド一発で行える

## 前提条件

- Azure アカウント（無料枠利用）
- Azure CLI インストール済み（`az bicep` サブコマンドが利用可能）
- just コマンドランナーインストール済み
- `az login` 済み

## やること

### 1. Bicep テンプレートの作成

`infra/` ディレクトリに Bicep ファイルを配置する。

```
infra/
├── main.bicep          # エントリポイント（モジュール呼び出し）
├── main.bicepparam     # パラメータファイル
└── modules/
    ├── app-service-plan.bicep   # App Service Plan
    └── web-app.bicep            # Web App + 設定
```

#### `infra/main.bicep`（エントリポイント）

```bicep
targetScope = 'subscription'

param location string = 'japaneast'
param resourceGroupName string = 'rg-analogy-make'
param appServicePlanName string = 'plan-analogy-make'
param webAppName string = 'analogy-make'

@secure()
param openaiApiKey string
@secure()
param tavilyApiKey string

// Resource Group
resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
}

// App Service Plan
module plan 'modules/app-service-plan.bicep' = {
  scope: rg
  name: 'app-service-plan'
  params: {
    name: appServicePlanName
    location: location
  }
}

// Web App
module app 'modules/web-app.bicep' = {
  scope: rg
  name: 'web-app'
  params: {
    name: webAppName
    location: location
    appServicePlanId: plan.outputs.id
    openaiApiKey: openaiApiKey
    tavilyApiKey: tavilyApiKey
  }
}

output webAppUrl string = app.outputs.url
```

#### `infra/modules/app-service-plan.bicep`

```bicep
param name string
param location string

resource plan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: name
  location: location
  kind: 'linux'
  sku: {
    name: 'F1'
    tier: 'Free'
  }
  properties: {
    reserved: true  // Linux の場合 true 必須
  }
}

output id string = plan.id
```

#### `infra/modules/web-app.bicep`

```bicep
param name string
param location string
param appServicePlanId string

@secure()
param openaiApiKey string
@secure()
param tavilyApiKey string

resource app 'Microsoft.Web/sites@2024-04-01' = {
  name: name
  location: location
  properties: {
    serverFarmId: appServicePlanId
    siteConfig: {
      linuxFxVersion: 'NODE|22-lts'
      appCommandLine: 'node server/index.mjs'
      appSettings: [
        { name: 'NUXT_OPENAI_API_KEY', value: openaiApiKey }
        { name: 'NUXT_TAVILY_API_KEY', value: tavilyApiKey }
        { name: 'NODE_ENV', value: 'production' }
        // F1 プランでは Always On 非対応のため設定しない
      ]
    }
  }
}

output url string = 'https://${app.properties.defaultHostName}'
```

#### `infra/main.bicepparam`

```bicepparam
using './main.bicep'

param location = 'japaneast'
param resourceGroupName = 'rg-analogy-make'
param appServicePlanName = 'plan-analogy-make'
param webAppName = 'analogy-make'

// シークレットはデプロイ時にプロンプトで入力（ファイルに書かない）
```

### 2. Justfile へのインフラコマンド追加

既存の Justfile にインフラ管理コマンドを追加する。

```justfile
# --- インフラ管理 (Bicep) ---

# インフラのデプロイ（初回作成 / 更新）
deploy-infra:
    az deployment sub create \
      --location japaneast \
      --template-file infra/main.bicep \
      --parameters infra/main.bicepparam

# インフラの変更プレビュー（what-if）
preview-infra:
    az deployment sub what-if \
      --location japaneast \
      --template-file infra/main.bicep \
      --parameters infra/main.bicepparam

# インフラの削除（Resource Group ごと）
destroy-infra:
    az group delete --name rg-analogy-make --yes

# Publish Profile の取得（GitHub Actions 用）
get-publish-profile:
    az webapp deployment list-publishing-profiles \
      --name analogy-make \
      --resource-group rg-analogy-make \
      --xml
```

### 3. GitHub Actions ワークフローとの連携

- **アプリのデプロイ** (`deploy.yml`): 既存のまま変更なし（Publish Profile 方式）
- **インフラのデプロイ**: ローカルから `just deploy-infra` で手動実行
  - 個人プロジェクトであり、インフラ変更は頻度が低いため CI/CD 化は不要
  - 将来的に必要になれば PHASE2 以降で対応

### 4. セットアップ手順（初回）

以下の順序で実行する:

```bash
# 1. Azure にログイン
az login

# 2. インフラのデプロイ（APIキーの入力を求められる）
just deploy-infra

# 3. Publish Profile を取得
just get-publish-profile

# 4. GitHub リポジトリの Secrets に登録
#    Settings → Secrets → AZURE_WEBAPP_PUBLISH_PROFILE に貼り付け

# 5. main ブランチに push → GitHub Actions が自動デプロイ
git push origin main
```

### 5. 動作確認

- `just deploy-infra` でリソースが作成される
- `just preview-infra` で変更差分が表示される（初回は全リソースが「作成」）
- `just destroy-infra` でリソースが削除される
- リソース作成後、PHASE1.0 と同じ動作確認ができる:
  - `https://analogy-make.azurewebsites.net` にアクセスしてチャットUIが表示される
  - メッセージ送信 → AI応答が動作する
  - SQLite 永続化が動作する

## 技術的な注意点

### シークレットの管理

- `openaiApiKey` / `tavilyApiKey` は `@secure()` パラメータとして定義
- `.bicepparam` ファイルにはシークレットを記載しない
- デプロイ時に Azure CLI がプロンプトで入力を求める
- Azure 側では App Settings に保存され、Portal 上でもマスクされる

### べき等性

- Bicep デプロイはべき等（何度実行しても同じ結果）
- リソースが既に存在する場合は差分のみ適用される
- `just preview-infra`（what-if）で事前に変更内容を確認できる

### F1 プランの制約（PHASE1.0 から引き継ぎ）

- Always On 非対応（コールドスタートあり）
- カスタムドメイン・SSL は `*.azurewebsites.net` のデフォルトを利用
- `/home` ディレクトリが永続ストレージ（SQLite の配置先）

## ファイル変更一覧

| ファイル | 操作 | 内容 |
|---|---|---|
| `infra/main.bicep` | 新規作成 | エントリポイント |
| `infra/main.bicepparam` | 新規作成 | パラメータ定義 |
| `infra/modules/app-service-plan.bicep` | 新規作成 | App Service Plan |
| `infra/modules/web-app.bicep` | 新規作成 | Web App + 設定 |
| `Justfile` | 追記 | インフラ管理コマンド追加 |

## やらないこと

- Key Vault によるシークレット管理（F1 プランでは過剰）
- 複数環境（staging / production）の管理
- 監視・アラート・バックアップの設定
