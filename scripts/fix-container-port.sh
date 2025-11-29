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

echo -e "${YELLOW}=== Container App Ingress 포트 수정 ===${NC}"
echo ""

BACKEND_APP_NAME="ca-$APP_NAME-backend-$ENVIRONMENT"
FRONTEND_APP_NAME="ca-$APP_NAME-frontend-$ENVIRONMENT"

# Backend Container App Ingress 수정
echo "1. Backend Container App Ingress 설정 확인 및 수정..."
if az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
  CURRENT_PORT=$(az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.targetPort -o tsv)
  echo "  현재 Target Port: $CURRENT_PORT"
  
  if [ "$CURRENT_PORT" != "8000" ]; then
    echo "  Target Port를 8000으로 변경 중..."
    az containerapp ingress update \
      --name $BACKEND_APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --target-port 8000 \
      --type external
    echo -e "${GREEN}✓ Backend Target Port가 8000으로 변경되었습니다.${NC}"
  else
    echo -e "${GREEN}✓ Backend Target Port가 이미 8000입니다.${NC}"
  fi
  
  # 컨테이너 재시작
  echo "  컨테이너 revision 재시작 중..."
  az containerapp revision restart \
    --name $BACKEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --revision $(az containerapp revision list --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv)
  echo -e "${GREEN}✓ Backend 컨테이너가 재시작되었습니다.${NC}"
else
  echo -e "${RED}❌ Backend Container App을 찾을 수 없습니다.${NC}"
fi

echo ""

# Frontend Container App Ingress 수정
echo "2. Frontend Container App Ingress 설정 확인 및 수정..."
if az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
  CURRENT_PORT=$(az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.targetPort -o tsv)
  echo "  현재 Target Port: $CURRENT_PORT"
  
  if [ "$CURRENT_PORT" != "80" ]; then
    echo "  Target Port를 80으로 변경 중..."
    az containerapp ingress update \
      --name $FRONTEND_APP_NAME \
      --resource-group $RESOURCE_GROUP \
      --target-port 80 \
      --type external
    echo -e "${GREEN}✓ Frontend Target Port가 80으로 변경되었습니다.${NC}"
  else
    echo -e "${GREEN}✓ Frontend Target Port가 이미 80입니다.${NC}"
  fi
  
  # 컨테이너 재시작
  echo "  컨테이너 revision 재시작 중..."
  az containerapp revision restart \
    --name $FRONTEND_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --revision $(az containerapp revision list --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv)
  echo -e "${GREEN}✓ Frontend 컨테이너가 재시작되었습니다.${NC}"
else
  echo -e "${RED}❌ Frontend Container App을 찾을 수 없습니다.${NC}"
fi

echo ""
echo -e "${GREEN}=== 완료! ===${NC}"
echo ""
echo "다음 명령으로 상태를 확인하세요:"
echo ""
echo -e "${YELLOW}az containerapp show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --query properties.runningStatus -o tsv${NC}"
echo -e "${YELLOW}az containerapp show --name $FRONTEND_APP_NAME --resource-group $RESOURCE_GROUP --query properties.runningStatus -o tsv${NC}"
