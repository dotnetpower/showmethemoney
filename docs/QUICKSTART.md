# Azure Container Apps 배포 빠른 시작 가이드

show-me-the-money 애플리케이션을 Azure Container Apps에 배포하기 위한 단계별 가이드입니다.

## 📋 사전 요구사항

- Azure 구독 (무료 계정도 가능)
- GitHub 계정
- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli) 설치
- [GitHub CLI](https://cli.github.com/) 설치 (선택사항)
- Docker 설치 (로컬 테스트용, 선택사항)

## 🚀 배포 방법

### 옵션 1: GitHub Actions를 통한 자동 배포 (권장)

#### 1단계: Azure 서비스 주체 생성

```bash
# Azure CLI로 로그인
az login

# 서비스 주체 생성 (구독 ID를 실제 값으로 변경)
az ad sp create-for-rbac \
  --name "github-actions-showmethemoney" \
  --role contributor \
  --scopes /subscriptions/{YOUR_SUBSCRIPTION_ID}/resourceGroups/rg-showmethemoney \
  --sdk-auth > azure-credentials.json
```

#### 2단계: GitHub Secrets 설정

수동으로 설정하거나 스크립트를 사용하세요:

**방법 A: 스크립트 사용 (간편)**

```bash
./scripts/setup-github-secrets.sh
```

**방법 B: 수동 설정**

GitHub 리포지토리 → Settings → Secrets and variables → Actions에서 다음 secrets 추가:

1. `AZURE_CREDENTIALS`: `azure-credentials.json` 파일 내용 전체
2. `AZURE_SUBSCRIPTION_ID`: Azure 구독 ID
3. `GH_TOKEN`: GitHub Personal Access Token (repo, read:packages, write:packages 권한)
4. `APPLICATIONINSIGHTS_CONNECTION_STRING`: (선택사항, 없으면 자동 생성)

#### 3단계: 배포 실행

**자동 배포**: main 브랜치에 코드를 push하면 자동으로 배포됩니다.

```bash
git push origin main
```

**수동 배포**: GitHub Actions 탭에서 "Deploy to Azure Container Apps" 워크플로우를 수동 실행합니다.

### 옵션 2: 로컬에서 수동 배포

#### 1단계: Azure 인프라 배포

```bash
# 배포 스크립트 실행
./scripts/deploy-azure.sh
```

또는 수동으로:

```bash
# Azure 로그인
az login

# 리소스 그룹 생성
az group create \
  --name rg-showmethemoney \
  --location koreacentral

# Bicep 배포
az deployment group create \
  --resource-group rg-showmethemoney \
  --template-file infra/main.bicep \
  --parameters infra/main.bicepparam \
  --parameters githubToken='your-github-token' \
  --name initial-deployment
```

#### 2단계: Docker 이미지 빌드 및 푸시

```bash
# ACR 이름 가져오기
ACR_NAME=$(az deployment group show \
  --resource-group rg-showmethemoney \
  --name initial-deployment \
  --query properties.outputs.acrName.value -o tsv)

# ACR 로그인
az acr login --name $ACR_NAME

# Backend 이미지 빌드 및 푸시
docker build -t $ACR_NAME.azurecr.io/backend:latest -f backend/Dockerfile ./backend
docker push $ACR_NAME.azurecr.io/backend:latest

# Frontend 이미지 빌드 및 푸시
docker build -t $ACR_NAME.azurecr.io/frontend:latest -f frontend/Dockerfile ./frontend
docker push $ACR_NAME.azurecr.io/frontend:latest
```

#### 3단계: Container Apps 재시작

```bash
# Backend 재시작
az containerapp revision restart \
  --name ca-showmethemoney-backend-dev \
  --resource-group rg-showmethemoney

# Frontend 재시작
az containerapp revision restart \
  --name ca-showmethemoney-frontend-dev \
  --resource-group rg-showmethemoney
```

## 📊 배포 확인

### 애플리케이션 URL 확인

```bash
# Backend URL
az containerapp show \
  --name ca-showmethemoney-backend-dev \
  --resource-group rg-showmethemoney \
  --query properties.configuration.ingress.fqdn -o tsv

# Frontend URL
az containerapp show \
  --name ca-showmethemoney-frontend-dev \
  --resource-group rg-showmethemoney \
  --query properties.configuration.ingress.fqdn -o tsv
```

### 로그 확인

```bash
# Backend 로그 실시간 확인
az containerapp logs show \
  --name ca-showmethemoney-backend-dev \
  --resource-group rg-showmethemoney \
  --follow

# Frontend 로그 실시간 확인
az containerapp logs show \
  --name ca-showmethemoney-frontend-dev \
  --resource-group rg-showmethemoney \
  --follow
```

## 🏗️ 배포된 리소스

배포 완료 후 다음 리소스가 생성됩니다:

- **Resource Group**: `rg-showmethemoney`
  - **Container Registry**: ACR (Docker 이미지 저장소)
  - **Log Analytics Workspace**: 로그 및 메트릭 수집
  - **Application Insights**: 애플리케이션 모니터링
  - **Container Apps Environment**: Container Apps 실행 환경
  - **Backend Container App**: FastAPI 백엔드 애플리케이션
  - **Frontend Container App**: React 프론트엔드 애플리케이션

## 🔧 트러블슈팅

### 배포 실패

1. GitHub Actions 로그 확인
2. Azure Portal에서 배포 로그 확인
3. Container App 로그 확인

### 이미지 푸시 실패

```bash
# ACR 로그인 다시 시도
az acr login --name $ACR_NAME

# 자격증명 확인
az acr credential show --name $ACR_NAME
```

### 애플리케이션이 시작되지 않음

```bash
# Container App 상태 확인
az containerapp show \
  --name ca-showmethemoney-backend-dev \
  --resource-group rg-showmethemoney \
  --query properties.runningStatus

# 최근 revision 확인
az containerapp revision list \
  --name ca-showmethemoney-backend-dev \
  --resource-group rg-showmethemoney \
  --output table
```

## 🧹 리소스 정리

더 이상 사용하지 않을 때:

```bash
az group delete --name rg-showmethemoney --yes --no-wait
```

## 📚 추가 정보

- 상세한 배포 가이드: [docs/DEPLOYMENT.md](./DEPLOYMENT.md)
- GitHub Actions 워크플로우: [.github/workflows/deploy-azure.yml](../.github/workflows/deploy-azure.yml)
- Bicep 인프라 코드: [infra/main.bicep](../infra/main.bicep)

## 💡 팁

- 개발 환경에서는 Container Apps의 스케일을 최소화하여 비용 절감
- Application Insights를 활용하여 성능 모니터링
- GitHub Actions 캐싱을 활용하여 빌드 시간 단축
- 프로덕션 환경에서는 별도의 환경 구성 권장
