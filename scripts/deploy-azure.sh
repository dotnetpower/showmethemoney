#!/bin/bash

# Azure Container Apps 초기 배포 스크립트
# az CLI를 사용하여 인프라를 배포합니다.

set -e

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 환경 변수
RESOURCE_GROUP=${RESOURCE_GROUP:-"rg-showmethemoney"}
LOCATION=${LOCATION:-"koreacentral"}
ENVIRONMENT=${ENVIRONMENT:-"dev"}
APP_NAME="showmethemoney"

# 리소스 이름
ACR_NAME="acr${APP_NAME}$(echo $RANDOM | md5sum | head -c 8)"
LOG_WORKSPACE_NAME="log-${APP_NAME}-${ENVIRONMENT}"
APPINSIGHTS_NAME="appi-${APP_NAME}-${ENVIRONMENT}"
CONTAINERAPP_ENV_NAME="cae-${APP_NAME}-${ENVIRONMENT}"
BACKEND_APP_NAME="ca-${APP_NAME}-backend-${ENVIRONMENT}"
FRONTEND_APP_NAME="ca-${APP_NAME}-frontend-${ENVIRONMENT}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Azure Container Apps 배포 스크립트${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Azure CLI 설치 확인
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI가 설치되어 있지 않습니다.${NC}"
    echo "https://docs.microsoft.com/cli/azure/install-azure-cli 에서 설치하세요."
    exit 1
fi

# containerapp extension 설치 확인
echo -e "${YELLOW}Container Apps extension 확인 중...${NC}"
if ! az extension show --name containerapp &> /dev/null; then
    echo -e "${YELLOW}Container Apps extension 설치 중...${NC}"
    az extension add --name containerapp --upgrade
fi

# Azure 로그인 확인
echo -e "${YELLOW}Azure 로그인 상태 확인 중...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}Azure에 로그인해주세요.${NC}"
    az login
fi

# 구독 정보 표시
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
echo -e "${GREEN}현재 구독: ${SUBSCRIPTION_NAME} (${SUBSCRIPTION_ID})${NC}"

# 환경 변수 입력
echo ""
echo -e "${YELLOW}배포 설정:${NC}"
echo "  리소스 그룹: ${RESOURCE_GROUP}"
echo "  위치: ${LOCATION}"
echo "  환경: ${ENVIRONMENT}"
echo "  ACR 이름: ${ACR_NAME}"
echo ""

read -p "계속하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}배포가 취소되었습니다.${NC}"
    exit 0
fi

# GitHub Token 입력
echo ""
read -sp "GitHub Personal Access Token: " GITHUB_TOKEN
echo ""

if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}Error: GitHub Token이 필요합니다.${NC}"
    exit 1
fi

# 리소스 그룹 생성
echo ""
echo -e "${YELLOW}1. 리소스 그룹 생성 중...${NC}"
if az group exists --name $RESOURCE_GROUP | grep -q "true"; then
    echo -e "${GREEN}리소스 그룹이 이미 존재합니다: ${RESOURCE_GROUP}${NC}"
else
    az group create \
        --name $RESOURCE_GROUP \
        --location $LOCATION
    echo -e "${GREEN}리소스 그룹 생성 완료${NC}"
fi

# Container Registry 생성
echo ""
echo -e "${YELLOW}2. Container Registry 생성 중...${NC}"
ACR_EXISTS=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP 2>/dev/null || echo "")
if [ -z "$ACR_EXISTS" ]; then
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $ACR_NAME \
        --sku Basic \
        --admin-enabled true \
        --location $LOCATION
    echo -e "${GREEN}Container Registry 생성 완료${NC}"
else
    echo -e "${GREEN}Container Registry가 이미 존재합니다${NC}"
fi

ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer -o tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query passwords[0].value -o tsv)

# Log Analytics Workspace 생성
echo ""
echo -e "${YELLOW}3. Log Analytics Workspace 생성 중...${NC}"
LOG_EXISTS=$(az monitor log-analytics workspace show --resource-group $RESOURCE_GROUP --workspace-name $LOG_WORKSPACE_NAME 2>/dev/null || echo "")
if [ -z "$LOG_EXISTS" ]; then
    az monitor log-analytics workspace create \
        --resource-group $RESOURCE_GROUP \
        --workspace-name $LOG_WORKSPACE_NAME \
        --location $LOCATION
    echo -e "${GREEN}Log Analytics Workspace 생성 완료${NC}"
else
    echo -e "${GREEN}Log Analytics Workspace가 이미 존재합니다${NC}"
fi

LOG_CUSTOMER_ID=$(az monitor log-analytics workspace show --resource-group $RESOURCE_GROUP --workspace-name $LOG_WORKSPACE_NAME --query customerId -o tsv)
LOG_SHARED_KEY=$(az monitor log-analytics workspace get-shared-keys --resource-group $RESOURCE_GROUP --workspace-name $LOG_WORKSPACE_NAME --query primarySharedKey -o tsv)

# Application Insights 생성
echo ""
echo -e "${YELLOW}4. Application Insights 생성 중...${NC}"
APPINSIGHTS_EXISTS=$(az monitor app-insights component show --app $APPINSIGHTS_NAME --resource-group $RESOURCE_GROUP 2>/dev/null || echo "")
if [ -z "$APPINSIGHTS_EXISTS" ]; then
    az monitor app-insights component create \
        --app $APPINSIGHTS_NAME \
        --location $LOCATION \
        --resource-group $RESOURCE_GROUP
    echo -e "${GREEN}Application Insights 생성 완료${NC}"
else
    echo -e "${GREEN}Application Insights가 이미 존재합니다${NC}"
fi

APPINSIGHTS_CONNECTION_STRING=$(az monitor app-insights component show --app $APPINSIGHTS_NAME --resource-group $RESOURCE_GROUP --query connectionString -o tsv)

# Container Apps Environment 생성
echo ""
echo -e "${YELLOW}5. Container Apps Environment 생성 중...${NC}"
ENV_EXISTS=$(az containerapp env show --name $CONTAINERAPP_ENV_NAME --resource-group $RESOURCE_GROUP 2>/dev/null || echo "")
if [ -z "$ENV_EXISTS" ]; then
    az containerapp env create \
        --name $CONTAINERAPP_ENV_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --logs-workspace-id $LOG_CUSTOMER_ID \
        --logs-workspace-key $LOG_SHARED_KEY
    echo -e "${GREEN}Container Apps Environment 생성 완료${NC}"
else
    echo -e "${GREEN}Container Apps Environment가 이미 존재합니다${NC}"
fi

# Backend Container App 생성
echo ""
echo -e "${YELLOW}6. Backend Container App 생성 중...${NC}"
BACKEND_EXISTS=$(az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP 2>/dev/null || echo "")
if [ -z "$BACKEND_EXISTS" ]; then
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
    echo -e "${GREEN}Backend Container App 생성 완료${NC}"
else
    echo -e "${GREEN}Backend Container App이 이미 존재합니다${NC}"
fi

BACKEND_FQDN=$(az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)
BACKEND_URL="https://${BACKEND_FQDN}"

# Frontend Container App 생성
echo ""
echo -e "${YELLOW}7. Frontend Container App 생성 중...${NC}"
FRONTEND_EXISTS=$(az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP 2>/dev/null || echo "")
if [ -z "$FRONTEND_EXISTS" ]; then
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
            REACT_APP_API_URL="$BACKEND_URL" \
        --cpu 0.5 \
        --memory 1Gi \
        --min-replicas 1 \
        --max-replicas 5
    echo -e "${GREEN}Frontend Container App 생성 완료${NC}"
else
    echo -e "${GREEN}Frontend Container App이 이미 존재합니다${NC}"
fi

FRONTEND_FQDN=$(az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)
FRONTEND_URL="https://${FRONTEND_FQDN}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}배포 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Container Registry:${NC}"
echo "  Name: ${ACR_NAME}"
echo "  Login Server: ${ACR_LOGIN_SERVER}"
echo ""
echo -e "${GREEN}Application URLs (초기 이미지 푸시 후 접근 가능):${NC}"
echo "  Backend:  ${BACKEND_URL}"
echo "  Frontend: ${FRONTEND_URL}"
echo ""
echo -e "${GREEN}Azure Portal:${NC}"
echo "  https://portal.azure.com/#@/resource/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/overview"
echo ""

# Docker 이미지 빌드 및 푸시 안내
echo -e "${YELLOW}다음 단계:${NC}"
echo "1. ACR에 로그인:"
echo "   az acr login --name ${ACR_NAME}"
echo ""
echo "2. Backend 이미지 빌드 및 푸시:"
echo "   docker build -t ${ACR_LOGIN_SERVER}/backend:latest -f backend/Dockerfile ./backend"
echo "   docker push ${ACR_LOGIN_SERVER}/backend:latest"
echo ""
echo "3. Frontend 이미지 빌드 및 푸시:"
echo "   docker build -t ${ACR_LOGIN_SERVER}/frontend:latest -f frontend/Dockerfile ./frontend"
echo "   docker push ${ACR_LOGIN_SERVER}/frontend:latest"
echo ""
echo "4. Container Apps 업데이트:"
echo "   az containerapp update --name ${BACKEND_APP_NAME} --resource-group ${RESOURCE_GROUP} --image ${ACR_LOGIN_SERVER}/backend:latest"
echo "   az containerapp update --name ${FRONTEND_APP_NAME} --resource-group ${RESOURCE_GROUP} --image ${ACR_LOGIN_SERVER}/frontend:latest"
echo ""
echo -e "${GREEN}또는 GitHub Actions를 통해 자동 배포하려면 다음 Secrets를 설정하세요:${NC}"
echo "  AZURE_CREDENTIALS"
echo "  AZURE_SUBSCRIPTION_ID: ${SUBSCRIPTION_ID}"
echo "  APPLICATIONINSIGHTS_CONNECTION_STRING: ${APPINSIGHTS_CONNECTION_STRING}"
echo "  GH_TOKEN"
echo "  ACR_NAME: ${ACR_NAME}"
echo ""
echo "자세한 내용은 docs/DEPLOYMENT.md를 참조하세요."
