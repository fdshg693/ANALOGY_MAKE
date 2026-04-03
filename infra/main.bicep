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
