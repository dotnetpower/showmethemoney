# Azure Container Apps 배포 가이드

이 가이드는 GitHub Actions를 통해 Azure Container Apps에 show-me-the-money 애플리케이션을 배포하는 방법을 설명합니다.

## 사전 요구사항

1. Azure 구독
2. GitHub 계정
3. Azure CLI 설치 (로컬 테스트용)

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
  --scopes /subscriptions/{subscription-id}/resourceGroups/rg-showmethemoney \
  --sdk-auth
```

출력된 JSON 전체를 GitHub Secret `AZURE_CREDENTIALS`에 저장합니다:

```json
{
  "clientId": "<GUID>",
  "clientSecret": "<STRING>",
  "subscriptionId": "<GUID>",
  "tenantId": "<GUID>",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

### 2. AZURE_SUBSCRIPTION_ID

Azure 구독 ID를 가져옵니다:

```bash
az account show --query id -o tsv
```

이 값을 GitHub Secret `AZURE_SUBSCRIPTION_ID`에 저장합니다.

### 3. APPLICATIONINSIGHTS_CONNECTION_STRING

Application Insights가 이미 존재하는 경우 연결 문자열을 가져옵니다:

```bash
az monitor app-insights component show \
  --app appi-showmethemoney-dev \
  --resource-group rg-showmethemoney \
  --query connectionString -o tsv
```

이 값을 GitHub Secret `APPLICATIONINSIGHTS_CONNECTION_STRING`에 저장합니다.

> 참고: 이 secret이 없으면 Bicep 배포 시 자동으로 새 Application Insights가 생성됩니다.

### 4. GH_TOKEN

GitHub Personal Access Token을 생성합니다:

1. GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" 클릭
3. 권한 선택:
   - `repo` (전체)
   - `read:packages`
   - `write:packages`
4. 생성된 토큰을 GitHub Secret `GH_TOKEN`에 저장

## GitHub Secrets 설정 방법

### GitHub UI에서 설정

1. GitHub 리포지토리로 이동
2. Settings → Secrets and variables → Actions
3. "New repository secret" 클릭
4. Name과 Value를 입력하고 "Add secret" 클릭

### GitHub CLI로 설정 (선택사항)

```bash
# GitHub CLI 설치 및 로그인
gh auth login

# Secrets 설정
gh secret set AZURE_CREDENTIALS < azure-credentials.json
gh secret set AZURE_SUBSCRIPTION_ID --body "your-subscription-id"
gh secret set APPLICATIONINSIGHTS_CONNECTION_STRING --body "your-connection-string"
gh secret set GH_TOKEN --body "your-github-token"
```

## 로컬에서 인프라 배포 테스트

배포 전에 로컬에서 테스트할 수 있습니다:

```bash
# Azure CLI로 로그인
az login

# 리소스 그룹 생성
az group create \
  --name rg-showmethemoney \
  --location koreacentral

# Bicep 배포 미리보기 (실제 배포 안 함)
az deployment group what-if \
  --resource-group rg-showmethemoney \
  --template-file infra/main.bicep \
  --parameters infra/main.bicepparam \
  --parameters appInsightsConnectionString="InstrumentationKey=..." \
  --parameters githubToken="ghp_..."

# 실제 배포
az deployment group create \
  --resource-group rg-showmethemoney \
  --template-file infra/main.bicep \
  --parameters infra/main.bicepparam \
  --parameters appInsightsConnectionString="InstrumentationKey=..." \
  --parameters githubToken="ghp_..." \
  --name initial-deployment
```

## 배포 프로세스

GitHub Actions 워크플로우는 다음 단계로 진행됩니다:

1. **setup-infrastructure**: Azure 리소스 그룹 및 인프라 생성
   - Container Registry (ACR)
   - Log Analytics Workspace
   - Application Insights
   - Container Apps Environment
   - Backend Container App
   - Frontend Container App

2. **build-and-push-backend**: 백엔드 Docker 이미지 빌드 및 ACR에 푸시

3. **build-and-push-frontend**: 프론트엔드 Docker 이미지 빌드 및 ACR에 푸시

4. **deploy-backend**: 백엔드 Container App 업데이트

5. **deploy-frontend**: 프론트엔드 Container App 업데이트

6. **verify-deployment**: 배포 검증 및 헬스 체크

## 수동 배포 트리거

main 브랜치로 푸시하지 않고 수동으로 배포하려면:

1. GitHub 리포지토리의 Actions 탭으로 이동
2. "Deploy to Azure Container Apps" 워크플로우 선택
3. "Run workflow" 버튼 클릭
4. 브랜치 선택 후 "Run workflow" 실행

## 배포된 애플리케이션 확인

배포 완료 후 GitHub Actions 로그에서 다음 정보를 확인할 수 있습니다:

- Backend URL: `https://ca-showmethemoney-backend-dev.{region}.azurecontainerapps.io`
- Frontend URL: `https://ca-showmethemoney-frontend-dev.{region}.azurecontainerapps.io`
- Azure Portal 링크

## 환경 변수

### Backend Container App

- `APPLICATIONINSIGHTS_CONNECTION_STRING`: Application Insights 연결 문자열
- `GITHUB_TOKEN`: GitHub API 접근용 토큰
- `GITHUB_REPO_OWNER`: `dotnetpower`
- `GITHUB_REPO_NAME`: `showmethemoney`

### Frontend Container App

- `REACT_APP_API_URL`: 백엔드 API URL (자동 설정)

## 리소스 정리

더 이상 필요하지 않을 때 리소스를 삭제합니다:

```bash
az group delete --name rg-showmethemoney --yes --no-wait
```

## 트러블슈팅

### 배포 실패 시

1. GitHub Actions 로그 확인
2. Azure Portal에서 Container App 로그 확인:
   ```bash
   az containerapp logs show \
     --name ca-showmethemoney-backend-dev \
     --resource-group rg-showmethemoney \
     --follow
   ```

### ACR 인증 문제

ACR 자격증명 확인:
```bash
az acr credential show --name acrshowmethemoney{suffix}
```

### Container App 상태 확인

```bash
# Backend 상태
az containerapp show \
  --name ca-showmethemoney-backend-dev \
  --resource-group rg-showmethemoney \
  --query properties.runningStatus

# Frontend 상태
az containerapp show \
  --name ca-showmethemoney-frontend-dev \
  --resource-group rg-showmethemoney \
  --query properties.runningStatus
```

## 추가 설정

### 커스텀 도메인 설정

```bash
az containerapp hostname add \
  --name ca-showmethemoney-frontend-dev \
  --resource-group rg-showmethemoney \
  --hostname www.example.com
```

### 스케일링 규칙 조정

Bicep 파일의 `scale` 섹션을 수정하여 스케일링 규칙을 변경할 수 있습니다.

### 환경별 배포

다른 환경(staging, prod)으로 배포하려면:

1. `infra/main.bicepparam` 파일 복사 (예: `main.staging.bicepparam`)
2. `environmentName` 파라미터를 변경
3. GitHub Actions 워크플로우에 환경별 job 추가

## 참고 자료

- [Azure Container Apps 문서](https://learn.microsoft.com/azure/container-apps/)
- [GitHub Actions 문서](https://docs.github.com/actions)
- [Bicep 문서](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
