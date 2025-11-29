// Azure Container Apps 인프라 구성
// FastAPI 백엔드와 React 프론트엔드를 위한 Container Apps 배포
// 기존 Container Registry 사용
targetScope = 'resourceGroup'

@description('리소스의 위치')
param location string = resourceGroup().location

@description('환경 이름 (dev, staging, prod)')
param environmentName string = 'dev'

@description('애플리케이션 이름')
param appName string = 'showmethemoney'

@description('기존 Container Registry 이름 (필수, 5-50자, 영숫자만)')
@minLength(5)
@maxLength(50)
param acrName string

@description('기존 Container Registry가 속한 리소스 그룹 (현재 리소스 그룹과 다른 경우 지정)')
param acrResourceGroup string = resourceGroup().name

@description('Container Apps 환경 이름')
param containerAppsEnvironmentName string = 'cae-${appName}-${environmentName}'

@description('Log Analytics 워크스페이스 이름')
param logAnalyticsWorkspaceName string = 'log-${appName}-${environmentName}'

@description('Application Insights 이름')
param appInsightsName string = 'appi-${appName}-${environmentName}'

@description('백엔드 Container App 이름')
param backendAppName string = 'ca-${appName}-backend-${environmentName}'

@description('프론트엔드 Container App 이름')
param frontendAppName string = 'ca-${appName}-frontend-${environmentName}'

@description('백엔드 Docker 이미지')
param backendImage string = '${acrName}.azurecr.io/backend:latest'

@description('프론트엔드 Docker 이미지')
param frontendImage string = '${acrName}.azurecr.io/frontend:latest'

@description('Application Insights Connection String')
@secure()
param appInsightsConnectionString string = ''

@description('GitHub Token')
@secure()
param githubToken string = ''

// 기존 Container Registry 참조
resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: acrName
  scope: resourceGroup(acrResourceGroup)
}

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Container Apps Environment
resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerAppsEnvironmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

// Backend Container App
resource backendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: backendAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: [
        {
          server: acr.properties.loginServer
          username: acr.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: acr.listCredentials().passwords[0].value
        }
        {
          name: 'appinsights-connection-string'
          value: !empty(appInsightsConnectionString) ? appInsightsConnectionString : appInsights.properties.ConnectionString
        }
        {
          name: 'github-token'
          value: githubToken
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: backendImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              secretRef: 'appinsights-connection-string'
            }
            {
              name: 'GITHUB_TOKEN'
              secretRef: 'github-token'
            }
            {
              name: 'GITHUB_REPO_OWNER'
              value: 'dotnetpower'
            }
            {
              name: 'GITHUB_REPO_NAME'
              value: 'showmethemoney'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http-rule'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// Frontend Container App
resource frontendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: frontendAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 80
        transport: 'auto'
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: [
        {
          server: acr.properties.loginServer
          username: acr.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: acr.listCredentials().passwords[0].value
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: frontendImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'REACT_APP_API_URL'
              value: 'https://${backendApp.properties.configuration.ingress.fqdn}'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-rule'
            http: {
              metadata: {
                concurrentRequests: '20'
              }
            }
          }
        ]
      }
    }
  }
}

// Outputs
output acrName string = acr.name
output acrLoginServer string = acr.properties.loginServer
output backendUrl string = 'https://${backendApp.properties.configuration.ingress.fqdn}'
output frontendUrl string = 'https://${frontendApp.properties.configuration.ingress.fqdn}'
output containerAppsEnvironmentId string = containerAppsEnvironment.id
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
