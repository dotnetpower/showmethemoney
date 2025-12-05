# 프로젝트 개요
이 프로젝트는 ETF 및 주식 종목 데이터를 수집, 저장, 시각화하는 대시보드 애플리케이션을 개발하는 것을 목표로 합니다. FastAPI를 사용하여 API 서버를 구축하고, github repo 자체를 DB로써 활용하여 데이터를 관리합니다. React를 사용하여 사용자 친화적인 대시보드를 구현하며, Application Insights를 통해 애플리케이션의 성능과 상태를 모니터링합니다.

# 주요 기능
- 배당 정보
  - 요일별 배당금 지급 종목 조회
  - 월별 배당금 지급 종목 조회
- Total Return ETF 정보
  - Total Return ETF 종목 조회
  - Total Return ETF 상세 정보 조회
- 운용사별 ETF 정보
  - 운용사별 ETF 종목 조회

# 핵심 규칙
- 프로젝트명: show-me-the-money
- FastAPI를 사용하여 API 서버 구축
- github repo 자체를 DB로써 활용하여 데이터 저장 및 관리
- React를 사용하여 대시보드 구축 
- Application Insights를 사용하여 애플리케이션 모니터링 및 로깅
- ETF 및 주식 종목 데이터를 주기적으로 가져와 github repo에 저장
- 대시보드를 통해 ETF 데이터를 시각화 및 분석
- 모바일 및 데스크탑 환경 모두에서 최적화된 UI 제공
- 실행시 반드시 가상환경 활성화 후 실행
- 이미 실행중인 포트가 있을수 있으므로 기존 포트 사용여부 확인 필요

## github repo as DB
- github repo의 파일 시스템을 데이터 저장소로 활용
- 데이터는 JSON 형식으로 사용하지만 MessagePack 형태로 압축 가능(개발은 JSON, 운영은 MessagePack 권장)
- 단일 데이터의 최대 크기는 4MB로 제한
  - 대용량 데이터는 여러 파일로 분할 저장
  - 분할 정보를 별도 파일로 관리
- 데이터 변경 시 branch를 활용하여 git 커밋 및 푸시후 PR을 통해 Merge
- 데이터 조회는 startup 시점에 로드하거나 API 요청 시 동적으로 로드
- 데이터 동기화 및 충돌 방지를 위한 optimistic concurrency control 전략 활용

## UI 구성
- 대시보드에는 다음과 같은 섹션이 포함되어야 함
  - 전체 ETF 종목 목록(티커, 가격, 배당율, 시가총액 등)
  - 배당금 지급 일정 및 내역
    - 요일별 배당금 지급 종목
    - 월별 배당금 지급 종목
  - Total Return ETF 종목 및 성과 지표
  - 개별 주식 종목 상세 정보 (가격, 거래량, 뉴스 등)
  - 데이터 시각화 (차트, 그래프 등)

## Agents 구성
- Microsoft Agent Framework (agent-framework) 활용
- 주요 Agents:
  - Data Ingestion Agent: ETF 및 주식 종목 데이터를 주기적으로 수집
    - 운용사별 ETF 데이터 수집
    - 배당금 지급 종목 데이터 수집
    - Total Return ETF 데이터 수집(예: ETFDB, totalreturnetf.com 등)
  - Data Processing Agent: 수집된 데이터를 정제 및 변환
    - 중복 제거
    - 형식 변환(JSON, MessagePack)
    - 유효성 검사
  - Data Storage Agent: 데이터를 github repo에 저장 및 관리
  - API Agent: FastAPI 서버를 통해 데이터 제공
  - Monitoring Agent: Application Insights를 통해 애플리케이션 상태 모니터링
  - /backend/app/agents 디렉토리에 각 Agent별 코드 구현
    - 각 Agent는 독립적으로 실행 가능하며, 필요시 상호작용 가능
    - 검증을 위해 각 Agent별 테스트 케이스 작성
  - Agent Tools
    - Web Search 를 위해서는 HostedWebSearchTool 사용

## 개발환경
- Python 3.13 이상
- uv 로 패키지 관리
- 필요한 환경변수는 .env 파일에 정의
- FastAPI
- github repo 자체를 DB로써 활용
- Application Insights
    - 필요한 패키지 목록:
        - opentelemetry-api
        - opentelemetry-sdk
        - azure-core-tracing-opentelemetry
        - azure-monitor-opentelemetry
        - azure-monitor-opentelemetry-exporter
        - opentelemetry-instrumentation-httpx
        - opentelemetry-instrumentation-fastapi
        - opentelemetry-instrumentation-openai
        - agent-framework
        - agent-framework-ag-ui
- React (대시보드 프론트엔드)
- 폴더 구조:
    ```
showmethemoney/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── api/             # API 라우터 (엔드포인트)
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   └── users.py
│   │   │   └── __init__.py
│   │   ├── core/            # 설정, 환경변수, 보안, 로깅 등
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── logger.py
│   │   ├── models/          # Pydantic 모델
│   │   │   └── user.py
│   │   ├── services/        # 비즈니스 로직
│   │   │   └── user_service.py
│   │   ├── db/              # DB 연결, ORM(SQLAlchemy 등)
│   │   │   ├── session.py
│   │   │   └── models.py
│   │   ├── main.py          # FastAPI 엔트리포인트
│   │   └── __init__.py
│   ├── tests/
│   │   └── test_users.py
│   ├── requirements.txt or pyproject.toml
│   └── Dockerfile
│
├── frontend/                # React 프론트엔드
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/        # API 연동 axios/fetch 모듈
│   │   │   └── userApi.ts
│   │   ├── context/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts or webpack.config.js
│
├── docker-compose.yml        # 전체 서비스 로컬 개발/배포
├── README.md
└── .gitignore

    ```



## 가상환경
- .venv 디렉토리가 가상환경이다. 실행전에 반드시 활성화 해야한다.
- 가상환경을 위해서는 다음 스크립트를 사용한다.
    ```
    # Ubuntu
    uv venv --python 3.13 .venv
    source .venv/bin/activate
    uv python pin 3.13
    uv sync
    ```

## 대화 규칙
- 반드시 한국어만 사용
- 이모지 최소화
- 완료시 "완료" 라고 대답



