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
