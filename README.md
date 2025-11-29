# show-me-the-money

FastAPI + React 대시보드 프로젝트의 기본 뼈대를 구성했습니다. 깃허브 리포지토리를 데이터 저장소로 사용하며, Application Insights 계측을 위한 훅도 포함되어 있습니다.

## 구조

```
showmethemoney/
├── backend/
│   ├── app/
│   │   ├── api/         # 버전별 FastAPI 라우터
│   │   ├── core/        # 설정, 보안, 로깅
│   │   ├── db/          # GitHub 파일시스템을 DB처럼 활용하는 헬퍼
│   │   ├── models/      # Pydantic 모델
│   │   ├── services/    # 비즈니스 로직
│   │   └── main.py      # FastAPI 엔트리포인트
│   ├── tests/           # pytest 예시
│   ├── pyproject.toml   # uv 기반 Python 의존성
│   └── Dockerfile
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── context/
│   ├── package.json
│   └── Dockerfile
├── data/                # 레포지토리 기반 JSON 저장소
├── docker-compose.yml   # 로컬 통합 실행
└── README.md
```

## 빠른 시작

### 백엔드

```bash
uv venv --python 3.13 .venv
source .venv/bin/activate
cd backend
uv sync
uvicorn app.main:app --reload
```

**Swagger UI 접속**: 서버 실행 후 http://localhost:8000/docs

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

### 도커 컴포즈

```bash
docker compose up --build
```

## 데이터 저장 전략

- `data/` 디렉터리가 깃허브 저장소를 DB처럼 사용하기 위한 진입점입니다.
- 기본적으로 JSON을 사용하되 운영 시 MessagePack으로 변환할 수 있습니다.
- 단일 파일 4MB 제한을 넘는 경우 파일을 분할하고 메타데이터를 별도 파일로 관리하세요.

## 모니터링

- `.env` 파일에 `APPLICATION_INSIGHTS_CONNECTION_STRING` 값을 정의하면 Application Insights로 트레이스를 보낼 수 있습니다.
- FastAPI와 HTTPX에 대해 OpenTelemetry 인스트루멘테이션이 기본 적용되어 있습니다.

## API 문서 (Swagger)

서버 실행 후 다음 URL에서 대화형 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### 주요 API 엔드포인트:

- `GET /api/v1/etf/all` - 전체 ETF 조회 (3,600개 이상)
- `GET /api/v1/etf/list/{provider}` - 특정 운용사 ETF 조회
- `GET /api/v1/etf/list` - 운용사별 ETF 목록
- `POST /api/v1/etf/update` - 전체 데이터 업데이트
- `GET /api/v1/etf/scheduler/status` - 스케줄러 상태 조회
- `GET /health` - 헬스 체크

## 테스트

```bash
source .venv/bin/activate
cd backend
pytest -v
```

## ETF 크롤러 상태

### ✅ 정상 작동 (14개 운용사)

총 **3,666개 ETF** 데이터 수집 중

- **IShares** (513)
- **FirstTrust** (1,572)
- **Direxion** (484)
- **Invesco** (240)
- **SPDR** (176)
- **GlobalX** (204)
- **Vanguard** (102)
- **Franklin Templeton** (95)
- **JPMorgan** (68)
- **Pacer Advisors** (47)
- **Roundhill** (45)
- **Dimensional Fund Advisors** (41)
- **PIMCO** (23)
- **Goldman Sachs** (48)
- **Alpha Architect** (8)

### ⚠️ TODO: 수정 필요 (5개 운용사)

1. **Fidelity**: 웹사이트 구조 변경, React/JS 동적 렌더링 필요
2. **GraniteShares**: 크롤러 로직 점검 필요
3. **VanEck**: 크롤러 로직 점검 필요
4. **WisdomTree**: 403 Forbidden (접근 차단) - User-Agent 및 헤더 조정 필요
5. **Yieldmax**: JavaScript 렌더링 필요 (Playwright/Selenium 또는 API 엔드포인트 탐색)

## 다음 단계

1. ~~ETF/주식 실데이터 수집기 구현~~ ✅ 완료 (14/19 운용사)
2. 나머지 5개 운용사 크롤러 수정
3. MessagePack 직렬화 및 분할 저장 전략 강화
4. React 컴포넌트에 실제 API 연동 및 시각화 보완