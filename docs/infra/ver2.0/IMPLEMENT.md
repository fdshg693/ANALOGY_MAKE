# ver2.0 実装計画: Bicep による Azure インフラの IaC 管理

## 変更ファイル一覧

| ファイル | 操作 | 内容 |
|---|---|---|
| `infra/main.bicep` | 新規作成 | エントリポイント（サブスクリプションスコープ） |
| `infra/main.bicepparam` | 新規作成 | パラメータ定義 |
| `infra/modules/app-service-plan.bicep` | 新規作成 | App Service Plan モジュール |
| `infra/modules/web-app.bicep` | 新規作成 | Web App + 設定モジュール |
| `Justfile` | 追記 | インフラ管理コマンド4件追加 |

計5ファイル（新規4 + 既存変更1）。

## 実装詳細

### T1: infra/ ディレクトリ構造の作成

```
infra/
├── main.bicep
├── main.bicepparam
└── modules/
    ├── app-service-plan.bicep
    └── web-app.bicep
```

### T2: infra/main.bicep

サブスクリプションスコープのエントリポイント。Resource Group を作成し、モジュールを呼び出す。

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

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
}

module plan 'modules/app-service-plan.bicep' = {
  scope: rg
  name: 'app-service-plan'
  params: {
    name: appServicePlanName
    location: location
  }
}

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

**設計判断:**
- `targetScope = 'subscription'` — Resource Group の作成もテンプレートに含めるため
- `@secure()` パラメータ — API キーをファイルに記載しない。デプロイ時にプロンプトで入力
- モジュール分割 — App Service Plan と Web App を分離し、各リソースの責務を明確化

### T3: infra/main.bicepparam

```bicepparam
using './main.bicep'

param location = 'japaneast'
param resourceGroupName = 'rg-analogy-make'
param appServicePlanName = 'plan-analogy-make'
param webAppName = 'analogy-make'

// openaiApiKey, tavilyApiKey は @secure() のためここに記載しない
// デプロイ時に Azure CLI がプロンプトで入力を求める
```

### T4: infra/modules/app-service-plan.bicep

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

### T5: infra/modules/web-app.bicep

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
      ]
    }
  }
}

output url string = 'https://${app.properties.defaultHostName}'
```

**設計判断:**
- `appCommandLine: 'node server/index.mjs'` — deploy.yml が `package: .output/` で `.output/` の中身を wwwroot にデプロイするため、wwwroot 基準でのパスは `server/index.mjs`（`.output/` プレフィックスなし）
- F1 プランでは Always On 非対応のため `alwaysOn` は設定しない

### T6: Justfile へのインフラコマンド追加

既存の Justfile 末尾に以下を追記:

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
    az group delete --name {{resource_group}} --yes

# Publish Profile の取得（GitHub Actions 用）
get-publish-profile:
    az webapp deployment list-publishing-profiles \
      --name {{app_name}} \
      --resource-group {{resource_group}} \
      --xml
```

**設計判断:**
- `az deployment sub create` — `targetScope = 'subscription'` に対応するサブスクリプションレベルデプロイ
- `destroy-infra`・`get-publish-profile` — 既存の Justfile 変数 `{{app_name}}`・`{{resource_group}}` を使用し、ハードコードを避ける
- `deploy-infra`・`preview-infra` — `--location` は既存変数に該当しないためリテラル指定（Bicep パラメータファイルと一致させる）
- `destroy-infra` に `--yes` — 確認プロンプトをスキップ（Justfile は意図的に実行するため）

## 実装順序

1. T1: ディレクトリ構造の作成
2. T4: app-service-plan.bicep（依存なし）
3. T5: web-app.bicep（依存なし）
4. T2: main.bicep（T4, T5 のモジュールを参照）
5. T3: main.bicepparam（T2 のパラメータに対応）
6. T6: Justfile 追記

T4 と T5 は独立しており並行作成可能。T2 は T4・T5 のモジュールパスを参照するため後。

## リスク・不確実性

### Bicep API バージョンの互換性

- `Microsoft.Resources/resourceGroups@2024-03-01`、`Microsoft.Web/serverfarms@2024-04-01`、`Microsoft.Web/sites@2024-04-01` を使用
- これらは PHASE1.5.md で指定されたバージョン。Azure CLI の `az bicep` が対応しているか、デプロイ時に検証が必要
- **対策**: `just preview-infra`（what-if）で事前に構文・API バージョンの検証が可能

### appCommandLine のパス

- `node server/index.mjs` を指定しているが、deploy.yml の `package: .output/` でデプロイされた場合の実際のディレクトリ構造は初回デプロイまで確認できない
- CURRENT.md（ver1.0）では `node .output/server/index.mjs` と記載されている箇所があり、矛盾の可能性
- **対策**: 初回デプロイ後に App Service のログ（`just logs`）で起動コマンドの成否を確認。必要に応じて修正

### @secure() パラメータのプロンプト入力

- `.bicepparam` に `@secure()` パラメータの値を記載しない設計のため、`az deployment sub create` 実行時にプロンプトで入力が求められる想定
- この動作が正しく機能するか実デプロイ時に確認が必要
- **対策**: `--parameters openaiApiKey=xxx tavilyApiKey=yyy` のインライン指定でもフォールバック可能

## 動作確認

### ローカル検証（コード実行なし）

- [ ] `infra/` 以下の4ファイルが正しいパスに作成されている
- [ ] Justfile に4つの新コマンドが追加されている
- [ ] Bicep ファイルの構文に明らかなエラーがない（インデント、括弧の対応等）

### デプロイ検証（手動、ver2.0 完了後に実施）

- [ ] `just preview-infra` で what-if が実行され、作成予定のリソースが表示される
- [ ] `just deploy-infra` でリソースが作成される（API キーのプロンプト入力あり）
- [ ] `just get-publish-profile` で XML が出力される
- [ ] `just destroy-infra` でリソースが削除される

※ デプロイ検証は Azure アカウントと `az login` が前提。コード変更としての ver2.0 はローカル検証で完了とする。
