#!/bin/bash
set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 환경 변수
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-showmethemoney}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
APP_NAME="${APP_NAME:-showmethemoney}"

echo -e "${YELLOW}=== ACR 권한 수정 스크립트 ===${NC}"
echo ""

# ACR 이름 가져오기
echo "ACR 정보 조회 중..."
ACR_NAME=$(az acr list --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv 2>/dev/null || echo "")

if [ -z "$ACR_NAME" ]; then
  echo -e "${RED}❌ ACR을 찾을 수 없습니다.${NC}"
  exit 1
fi

echo -e "${GREEN}✓ ACR 이름: $ACR_NAME${NC}"

# 1. ACR admin user 비활성화
echo ""
echo "1. ACR admin 사용자 비활성화 중..."
az acr update --name $ACR_NAME --admin-enabled false
echo -e "${GREEN}✓ ACR admin 사용자가 비활성화되었습니다.${NC}"

# 2. Backend Container App에 AcrPull 권한 부여
echo ""
echo "2. Backend Container App에 AcrPull 권한 부여 중..."
BACKEND_APP_NAME="ca-$APP_NAME-backend-$ENVIRONMENT"

if az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
  # Managed Identity가 활성화되어 있는지 확인
  IDENTITY_TYPE=$(az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query identity.type -o tsv)
  
  if [ "$IDENTITY_TYPE" != "SystemAssigned" ]; then
    echo "  Managed Identity 활성화 중..."
    az containerapp identity assign \
      --name $BACKEND_APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --system-assigned
  fi
  
  # Principal ID 가져오기
  PRINCIPAL_ID=$(az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query identity.principalId -o tsv)
  ACR_ID=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query id -o tsv)
  
  # AcrPull 역할 할당
  echo "  Principal ID: $PRINCIPAL_ID"
  if az role assignment create --assignee $PRINCIPAL_ID --role AcrPull --scope $ACR_ID 2>/dev/null; then
    echo -e "${GREEN}✓ Backend에 AcrPull 권한이 부여되었습니다.${NC}"
  else
    echo -e "${YELLOW}⚠ AcrPull 권한이 이미 존재합니다.${NC}"
  fi
else
  echo -e "${YELLOW}⚠ Backend Container App을 찾을 수 없습니다.${NC}"
fi

# 3. Frontend Container App에 AcrPull 권한 부여
echo ""
echo "3. Frontend Container App에 AcrPull 권한 부여 중..."
FRONTEND_APP_NAME="ca-$APP_NAME-frontend-$ENVIRONMENT"

if az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
  # Managed Identity가 활성화되어 있는지 확인
  IDENTITY_TYPE=$(az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query identity.type -o tsv)
  
  if [ "$IDENTITY_TYPE" != "SystemAssigned" ]; then
    echo "  Managed Identity 활성화 중..."
    az containerapp identity assign \
      --name $FRONTEND_APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --system-assigned
  fi
  
  # Principal ID 가져오기
  PRINCIPAL_ID=$(az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query identity.principalId -o tsv)
  ACR_ID=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query id -o tsv)
  
  # AcrPull 역할 할당
  echo "  Principal ID: $PRINCIPAL_ID"
  if az role assignment create --assignee $PRINCIPAL_ID --role AcrPull --scope $ACR_ID 2>/dev/null; then
    echo -e "${GREEN}✓ Frontend에 AcrPull 권한이 부여되었습니다.${NC}"
  else
    echo -e "${YELLOW}⚠ AcrPull 권한이 이미 존재합니다.${NC}"
  fi
else
  echo -e "${YELLOW}⚠ Frontend Container App을 찾을 수 없습니다.${NC}"
fi

# 4. Container App 레지스트리 설정 업데이트
echo ""
echo "4. Container App 레지스트리 설정 업데이트 중..."
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer -o tsv)

# Backend 업데이트
if az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
  echo "  Backend Container App 레지스트리 설정 업데이트 중..."
  az containerapp registry set \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --server $ACR_LOGIN_SERVER \
    --identity system 2>/dev/null || echo -e "${YELLOW}  ⚠ Backend 레지스트리 설정 업데이트 실패 (수동 확인 필요)${NC}"
fi

# Frontend 업데이트
if az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
  echo "  Frontend Container App 레지스트리 설정 업데이트 중..."
  az containerapp registry set \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --server $ACR_LOGIN_SERVER \
    --identity system 2>/dev/null || echo -e "${YELLOW}  ⚠ Frontend 레지스트리 설정 업데이트 실패 (수동 확인 필요)${NC}"
fi

echo ""
echo -e "${GREEN}=== 완료! ===${NC}"
echo ""
echo "다음 명령으로 Container App을 업데이트하세요:"
echo ""
echo -e "${YELLOW}az containerapp update \\"
echo "  --name $BACKEND_APP_NAME \\"
echo "  --resource-group $RESOURCE_GROUP \\"
echo "  --image $ACR_LOGIN_SERVER/backend:latest${NC}"
echo ""
echo -e "${YELLOW}az containerapp update \\"
echo "  --name $FRONTEND_APP_NAME \\"
echo "  --resource-group $RESOURCE_GROUP \\"
echo "  --image $ACR_LOGIN_SERVER/frontend:latest${NC}"
