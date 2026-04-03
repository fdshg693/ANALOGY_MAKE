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
