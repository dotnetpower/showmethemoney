# 초기 데이터 로드 가이드

배포 후 처음 사용할 때는 ETF 데이터가 비어있습니다. 다음 방법 중 하나를 선택하여 초기 데이터를 로드하세요.

## 방법 1: Swagger UI를 통한 데이터 로드 (권장)

1. 백엔드 API Swagger 페이지 접속:
   ```
   https://ca-showmethemoney-backend-dev.bravewater-46e243b4.koreacentral.azurecontainerapps.io/docs
   ```

2. **POST /api/v1/etf/update** 엔드포인트 찾기

3. "Try it out" 버튼 클릭

4. "Execute" 버튼 클릭

5. 모든 운용사의 ETF 데이터 크롤링이 시작됩니다 (약 10-20분 소요)

## 방법 2: curl 명령어 사용

```bash
curl -X POST "https://ca-showmethemoney-backend-dev.bravewater-46e243b4.koreacentral.azurecontainerapps.io/api/v1/etf/update"
```

## 방법 3: 특정 운용사만 먼저 로드

빠른 테스트를 위해 특정 운용사만 먼저 로드할 수 있습니다:

### Roundhill (소규모, 빠름)
```bash
curl -X POST "https://ca-showmethemoney-backend-dev.bravewater-46e243b4.koreacentral.azurecontainerapps.io/api/v1/etf/update/roundhill"
```

### iShares (대규모, 느림)
```bash
curl -X POST "https://ca-showmethemoney-backend-dev.bravewater-46e243b4.koreacentral.azurecontainerapps.io/api/v1/etf/update/ishares"
```

## 지원되는 운용사 목록

- ishares
- roundhill
- vanguard
- spdr
- invesco
- jpmorgan
- dimensional fund advisors
- firsttrust
- fidelity
- franklintempleton
- vaneck
- wisdomtree
- globalx
- direxion
- pimco
- graniteshares
- alphaarchitect
- pacer advisors
- goldmansachs
- yieldmax

## 데이터 로드 확인

데이터가 로드되었는지 확인:

```bash
curl "https://ca-showmethemoney-backend-dev.bravewater-46e243b4.koreacentral.azurecontainerapps.io/api/v1/etf/all" | jq 'length'
```

## 자동 업데이트

초기 데이터 로드 후, 스케줄러가 매일 미국 동부시간 오후 6시에 자동으로 데이터를 업데이트합니다.

스케줄러 상태 확인:
```bash
curl "https://ca-showmethemoney-backend-dev.bravewater-46e243b4.koreacontainerapps.io/api/v1/etf/scheduler/status"
```

## 주의사항

⚠️ **첫 번째 전체 데이터 로드는 시간이 오래 걸립니다 (10-20분)**

- 20개의 운용사를 병렬로 크롤링
- 3,600개 이상의 ETF 데이터 수집
- 네트워크 상태에 따라 시간이 더 걸릴 수 있음

⚠️ **Container App의 타임아웃 설정 확인**

Container App에 타임아웃이 설정되어 있다면, 전체 업데이트가 완료되기 전에 요청이 끊길 수 있습니다.
이 경우 백그라운드에서 계속 실행되므로, 몇 분 후 `/api/v1/etf/all` 엔드포인트를 확인하여 데이터가 로드되었는지 확인하세요.

## 트러블슈팅

### 데이터가 로드되지 않는 경우

1. **백엔드 로그 확인**:
   ```bash
   az containerapp logs show \
     --name ca-showmethemoney-backend-dev \
     --resource-group rg-showmethemoney \
     --follow
   ```

2. **GitHub Token 확인**: 
   데이터를 GitHub repo에 저장하므로 GITHUB_TOKEN 환경변수가 올바르게 설정되어야 합니다.

3. **메모리/CPU 확인**:
   Container App의 리소스가 부족하면 크롤링이 실패할 수 있습니다.

### 일부 운용사만 실패하는 경우

특정 웹사이트의 구조가 변경되었거나 네트워크 문제일 수 있습니다.
다른 운용사는 정상적으로 로드되므로 나중에 다시 시도하세요.
