# GitHub Secrets 설정 스크립트
# GitHub CLI를 사용하여 필요한 secrets를 설정합니다.

#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GitHub Secrets 설정 스크립트${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# GitHub CLI 확인
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI가 설치되어 있지 않습니다.${NC}"
    echo "https://cli.github.com/ 에서 설치하세요."
    exit 1
fi

# GitHub 로그인 확인
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}GitHub에 로그인해주세요.${NC}"
    gh auth login
fi

echo -e "${GREEN}현재 리포지토리:${NC}"
gh repo view --json nameWithOwner -q .nameWithOwner
echo ""

# 1. AZURE_CREDENTIALS
echo -e "${YELLOW}1. AZURE_CREDENTIALS 설정${NC}"
echo "Azure 서비스 주체를 생성하고 JSON을 파일로 저장하세요:"
echo ""
echo "az ad sp create-for-rbac \\"
echo "  --name \"github-actions-showmethemoney\" \\"
echo "  --role contributor \\"
echo "  --scopes /subscriptions/{subscription-id}/resourceGroups/rg-showmethemoney \\"
echo "  --sdk-auth > azure-credentials.json"
echo ""
read -p "azure-credentials.json 파일이 준비되었나요? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "azure-credentials.json" ]; then
        gh secret set AZURE_CREDENTIALS < azure-credentials.json
        echo -e "${GREEN}✓ AZURE_CREDENTIALS 설정 완료${NC}"
        rm azure-credentials.json
    else
        echo -e "${RED}azure-credentials.json 파일을 찾을 수 없습니다.${NC}"
    fi
else
    echo -e "${YELLOW}건너뛰기${NC}"
fi

# 2. AZURE_SUBSCRIPTION_ID
echo ""
echo -e "${YELLOW}2. AZURE_SUBSCRIPTION_ID 설정${NC}"
if command -v az &> /dev/null; then
    SUBSCRIPTION_ID=$(az account show --query id -o tsv 2>/dev/null || echo "")
    if [ ! -z "$SUBSCRIPTION_ID" ]; then
        echo "현재 Azure 구독 ID: ${SUBSCRIPTION_ID}"
        read -p "이 구독 ID를 사용하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            gh secret set AZURE_SUBSCRIPTION_ID --body "$SUBSCRIPTION_ID"
            echo -e "${GREEN}✓ AZURE_SUBSCRIPTION_ID 설정 완료${NC}"
        else
            read -p "구독 ID를 입력하세요: " MANUAL_SUB_ID
            gh secret set AZURE_SUBSCRIPTION_ID --body "$MANUAL_SUB_ID"
            echo -e "${GREEN}✓ AZURE_SUBSCRIPTION_ID 설정 완료${NC}"
        fi
    else
        read -p "Azure 구독 ID를 입력하세요: " MANUAL_SUB_ID
        gh secret set AZURE_SUBSCRIPTION_ID --body "$MANUAL_SUB_ID"
        echo -e "${GREEN}✓ AZURE_SUBSCRIPTION_ID 설정 완료${NC}"
    fi
else
    read -p "Azure 구독 ID를 입력하세요: " MANUAL_SUB_ID
    gh secret set AZURE_SUBSCRIPTION_ID --body "$MANUAL_SUB_ID"
    echo -e "${GREEN}✓ AZURE_SUBSCRIPTION_ID 설정 완료${NC}"
fi

# 3. APPLICATIONINSIGHTS_CONNECTION_STRING
echo ""
echo -e "${YELLOW}3. APPLICATIONINSIGHTS_CONNECTION_STRING 설정${NC}"
echo "Application Insights가 이미 있다면 연결 문자열을 입력하세요."
echo "(없으면 Enter를 눌러 건너뛰세요 - 배포 시 자동 생성됩니다)"
read -p "Connection String: " APPINSIGHTS_CS
if [ ! -z "$APPINSIGHTS_CS" ]; then
    gh secret set APPLICATIONINSIGHTS_CONNECTION_STRING --body "$APPINSIGHTS_CS"
    echo -e "${GREEN}✓ APPLICATIONINSIGHTS_CONNECTION_STRING 설정 완료${NC}"
else
    echo -e "${YELLOW}건너뛰기 (배포 시 자동 생성됨)${NC}"
fi

# 4. GH_TOKEN
echo ""
echo -e "${YELLOW}4. GH_TOKEN 설정${NC}"
echo "GitHub Personal Access Token이 필요합니다."
echo "권한: repo (전체), read:packages, write:packages"
echo "https://github.com/settings/tokens/new 에서 생성하세요."
read -sp "GitHub Token: " GH_TOKEN
echo ""
if [ ! -z "$GH_TOKEN" ]; then
    gh secret set GH_TOKEN --body "$GH_TOKEN"
    echo -e "${GREEN}✓ GH_TOKEN 설정 완료${NC}"
else
    echo -e "${YELLOW}건너뛰기${NC}"
fi

# 완료
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Secrets 설정 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "설정된 secrets 확인:"
gh secret list
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo "1. .github/workflows/deploy-azure.yml 워크플로우 확인"
echo "2. main 브랜치에 push하거나 Actions 탭에서 수동 실행"
echo "3. 배포 완료 후 애플리케이션 URL 확인"
