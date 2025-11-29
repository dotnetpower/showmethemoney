# Azure Container Apps 배포 가이드 (az CLI 사용)

이 가이드는 az CLI를 사용하여 Azure Container Apps에 show-me-the-money 애플리케이션을 배포하는 방법을 설명합니다.

## 사전 요구사항

1. Azure 구독
2. GitHub 계정
3. Azure CLI 설치 (로컬 테스트용)
4. Container Apps CLI extension

## Container Apps Extension 설치

```bash
az extension add --name containerapp --upgrade
```

## GitHub Secrets 설정

다음 secrets를 GitHub 리포지토리에 추가해야 합니다:

### 1. AZURE_CREDENTIALS

Azure 서비스 주체(Service Principal) 생성:

```bash
# Azure CLI로 로그인
az login

# 서비스 주체 생성
az ad sp create-for-rbac \
  --name "github-actions-showmethemoney" \
  --role contributor \
  --scopes /subscriptions/b052302c-4c8d-49a4-aa2f-9d60a7301a80/resourceGroups/rg-showmethemoney \
  --sdk-auth
```

출력된 JSON 전체를 GitHub Secret `AZURE_CREDENTIALS`에 저장합니다.

### 2. AZURE_SUBSCRIPTION_ID

```bash
az account show --query id -o tsv
```

### 3. GH_TOKEN

GitHub Personal Access Token을 생성하여 저장합니다 (repo, read:packages, write:packages 권한 필요).

### 4. ACR_NAME (선택사항)

특정 ACR 이름을 사용하려면 설정합니다. 설정하지 않으면 자동으로 생성됩니다.

## 로컬에서 인프라 배포

### 자동 스크립트 사용

```bash
# 배포 스크립트 실행
./scripts/deploy-azure.sh
```

스크립트는 다음을 자동으로 수행합니다:

1. 리소스 그룹 생성
2. Container Registry 생성
3. Log Analytics Workspace 생성
4. Application Insights 생성
5. Container Apps Environment 생성
6. Backend Container App 생성
7. Frontend Container App 생성

### 수동 단계별 배포

#### 1. 리소스 그룹 생성

```bash
export RESOURCE_GROUP="rg-showmethemoney"
export LOCATION="koreacentral"
export ENVIRONMENT="dev"
export APP_NAME="showmethemoney"

az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

#### 2. Container Registry 생성

```bash
export ACR_NAME="acrshowmethemoney$(openssl rand -hex 4)"

az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true \
  --location $LOCATION
```

#### 3. Log Analytics Workspace 생성

```bash
export LOG_WORKSPACE_NAME="log-${APP_NAME}-${ENVIRONMENT}"

az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_WORKSPACE_NAME \
  --location $LOCATION
```

#### 4. Application Insights 생성

```bash
export APPINSIGHTS_NAME="appi-${APP_NAME}-${ENVIRONMENT}"

az monitor app-insights component create \
  --app $APPINSIGHTS_NAME \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  # 워크스페이스에 연결하지 않는 클래식 Application Insights
```

#### 5. Container Apps Environment 생성

```bash
export CONTAINERAPP_ENV_NAME="cae-${APP_NAME}-${ENVIRONMENT}"

LOG_CUSTOMER_ID=$(az monitor log-analytics workspace show \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_WORKSPACE_NAME \
  --query customerId -o tsv)

LOG_SHARED_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group $RESOURCE_GROUP \
  --workspace-name $LOG_WORKSPACE_NAME \
  --query primarySharedKey -o tsv)

az containerapp env create \
  --name $CONTAINERAPP_ENV_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --logs-workspace-id $LOG_CUSTOMER_ID \
  --logs-workspace-key $LOG_SHARED_KEY
```

#### 6. ACR 자격증명 가져오기

```bash
ACR_LOGIN_SERVER=$(az acr show \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --query loginServer -o tsv)

ACR_USERNAME=$(az acr credential show \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --query username -o tsv)

ACR_PASSWORD=$(az acr credential show \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --query passwords[0].value -o tsv)
```

#### 7. Application Insights Connection String 가져오기

```bash
APPINSIGHTS_CONNECTION_STRING=$(az monitor app-insights component show \
  --app $APPINSIGHTS_NAME \
  --resource-group $RESOURCE_GROUP \
  --query connectionString -o tsv)
```

#### 8. Backend Container App 생성

```bash
export BACKEND_APP_NAME="ca-${APP_NAME}-backend-${ENVIRONMENT}"
export GITHUB_TOKEN="your-github-token"

az containerapp create \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINERAPP_ENV_NAME \
  --image mcr.microsoft.com/azuredocs/containerapps-helloworld:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --secrets \
    appinsights-connection-string="$APPINSIGHTS_CONNECTION_STRING" \
    github-token="$GITHUB_TOKEN" \
  --env-vars \
    APPLICATIONINSIGHTS_CONNECTION_STRING=secretref:appinsights-connection-string \
    GITHUB_TOKEN=secretref:github-token \
    GITHUB_REPO_OWNER=dotnetpower \
    GITHUB_REPO_NAME=showmethemoney \
  --cpu 0.5 \
  --memory 1Gi \
  --min-replicas 1 \
  --max-replicas 3
```

#### 9. Frontend Container App 생성

```bash
export FRONTEND_APP_NAME="ca-${APP_NAME}-frontend-${ENVIRONMENT}"

BACKEND_FQDN=$(az containerapp show \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv)

az containerapp create \
  --name $FRONTEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINERAPP_ENV_NAME \
  --image mcr.microsoft.com/azuredocs/containerapps-helloworld:latest \
  --target-port 80 \
  --ingress external \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --env-vars \
    REACT_APP_API_URL="https://${BACKEND_FQDN}" \
  --cpu 0.5 \
  --memory 1Gi \
  --min-replicas 1 \
  --max-replicas 5
```

## Docker 이미지 빌드 및 배포

### 1. ACR 로그인

```bash
az acr login --name $ACR_NAME
```

### 2. Backend 이미지 빌드 및 푸시

```bash
docker build -t ${ACR_LOGIN_SERVER}/backend:latest -f backend/Dockerfile ./backend
docker push ${ACR_LOGIN_SERVER}/backend:latest
```

### 3. Frontend 이미지 빌드 및 푸시

```bash
docker build -t ${ACR_LOGIN_SERVER}/frontend:latest -f frontend/Dockerfile ./frontend
docker push ${ACR_LOGIN_SERVER}/frontend:latest
```

### 4. Container Apps 업데이트

```bash
# Backend 업데이트
az containerapp update \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --image ${ACR_LOGIN_SERVER}/backend:latest

# Frontend 업데이트
az containerapp update \
  --name $FRONTEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --image ${ACR_LOGIN_SERVER}/frontend:latest
```

## 배포 확인

### 애플리케이션 URL 가져오기

```bash
# Backend URL
BACKEND_URL=$(az containerapp show \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv)
echo "Backend: https://${BACKEND_URL}"

# Frontend URL
FRONTEND_URL=$(az containerapp show \
  --name $FRONTEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv)
echo "Frontend: https://${FRONTEND_URL}"
```

### 로그 확인

```bash
# Backend 로그
az containerapp logs show \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --follow

# Frontend 로그
az containerapp logs show \
  --name $FRONTEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --follow
```

## GitHub Actions 배포

main 브랜치에 코드를 push하면 자동으로 배포됩니다:

```bash
git push origin main
```

또는 GitHub Actions 탭에서 "Deploy to Azure Container Apps" 워크플로우를 수동으로 실행할 수 있습니다.

## 리소스 정리

```bash
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

## 추가 관리 명령

### Container App 재시작

```bash
az containerapp revision restart \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP
```

### 스케일 조정

```bash
az containerapp update \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --min-replicas 2 \
  --max-replicas 5
```

### 환경 변수 업데이트

```bash
az containerapp update \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars "NEW_VAR=value"
```

### Revision 목록 확인

```bash
az containerapp revision list \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output table
```

## 트러블슈팅

### Container App이 시작되지 않을 때

```bash
# 상태 확인
az containerapp show \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.runningStatus

# 최근 로그 확인
az containerapp logs show \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --tail 100
```

### ACR 연결 문제

```bash
# ACR 자격증명 재확인
az acr credential show --name $ACR_NAME

# Container App에 레지스트리 재설정
az containerapp registry set \
  --name $BACKEND_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --server $ACR_LOGIN_SERVER \
  --username $ACR_USERNAME \
  --password $ACR_PASSWORD
```
