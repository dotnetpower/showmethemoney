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

## 테스트

```bash
source .venv/bin/activate
cd backend
pytest -v
```

## 다음 단계

1. ETF/주식 실데이터 수집기 구현
2. MessagePack 직렬화 및 분할 저장 전략 강화
3. React 컴포넌트에 실제 API 연동 및 시각화 보완