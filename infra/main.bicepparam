// Bicep 파라미터 파일
// 기존 Container Registry 사용 설정
// 
// 사용 방법:
// 1. 이 파일을 복사하여 실제 파라미터 파일 생성
// 2. acrName에 실제 ACR 이름 설정
// 3. az deployment group create --resource-group <RG> --template-file main.bicep --parameters @main.bicepparam
//
using './main.bicep'

param location = 'koreacentral'
param environmentName = 'dev'
param appName = 'showmethemoney'

// 필수: 기존 ACR 이름 - GitHub Secrets의 ACR_NAME 값과 동일하게 설정
// 아래 주석을 해제하고 실제 ACR 이름으로 변경하세요
// param acrName = 'acrshowmethemoney'

// 선택: 기존 ACR이 다른 리소스 그룹에 있는 경우 해당 리소스 그룹 이름 지정
// param acrResourceGroup = 'rg-shared-acr'
