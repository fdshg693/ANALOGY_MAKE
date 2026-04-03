using './main.bicep'

param location = 'japaneast'
param resourceGroupName = 'rg-analogy-make'
param appServicePlanName = 'plan-analogy-make'
param webAppName = 'analogy-make'

// openaiApiKey, tavilyApiKey は @secure() のためここに記載しない
// デプロイ時に Azure CLI がプロンプトで入力を求める
