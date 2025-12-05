# Agent 구성 가이드

## 개요
Microsoft Agent Framework를 활용하여 구현된 5개의 Agent로 ETF 데이터 수집, 처리, 저장, 제공, 모니터링을 수행합니다.

## Agent 구조

### 1. Data Ingestion Agent
**목적**: ETF 및 주식 종목 데이터를 주기적으로 수집

**주요 기능**:
- 운용사별 ETF 데이터 수집
- 배당금 지급 종목 데이터 수집
- Total Return ETF 데이터 수집

**사용 예시**:
```python
from backend.app.agents import DataIngestionAgent

agent = DataIngestionAgent(config={
    "providers": ["ishares", "vanguard", "spdr"]
})

# 특정 운용사 데이터 수집
result = await agent.execute(provider="ishares")

# 배당 데이터 수집
dividend_data = await agent.fetch_dividend_data()

# Total Return ETF 데이터 수집
tr_data = await agent.fetch_total_return_etf_data()
```

### 2. Data Processing Agent
**목적**: 수집된 데이터를 정제 및 변환

**주요 기능**:
- 데이터 정제 (null 값 제거, 필드 정규화)
- 중복 제거
- 형식 변환 (JSON, MessagePack)
- 유효성 검사

**사용 예시**:
```python
from backend.app.agents import DataProcessingAgent

agent = DataProcessingAgent(config={"use_msgpack": False})

# 데이터 정제
cleaned = await agent.execute(data=raw_data, operation="clean")

# 중복 제거
unique = await agent.execute(data=raw_data, operation="deduplicate")

# JSON 변환
json_data = await agent.execute(data=raw_data, operation="transform", format="json")

# MessagePack 압축
compressed = await agent.compress_data(raw_data)
```

### 3. Data Storage Agent
**목적**: 데이터를 GitHub Repository에 저장 및 관리

**주요 기능**:
- GitHub Repo를 DB로 활용
- 단일/분할 파일 저장 (최대 4MB)
- 메타데이터 관리
- Git 브랜치를 통한 버전 관리

**사용 예시**:
```python
from backend.app.agents import DataStorageAgent

agent = DataStorageAgent(config={
    "data_dir": "data",
    "max_file_size": 4 * 1024 * 1024,
    "use_branches": True
})

# 데이터 저장
await agent.execute(
    operation="save",
    data=etf_data,
    path="ishares/etf_list.json",
    branch="update-ishares-data",
    commit_message="Update iShares ETF list"
)

# 데이터 로드
result = await agent.execute(operation="load", path="ishares/etf_list.json")

# 데이터 삭제
await agent.execute(operation="delete", path="old_data.json")
```

### 4. API Agent
**목적**: FastAPI 서버를 통해 데이터 제공

**주요 기능**:
- ETF 목록/상세 정보 제공
- 배당금 정보 제공 (요일별/월별)
- Total Return ETF 정보 제공
- 캐시 관리

**사용 예시**:
```python
from backend.app.agents import APIAgent

agent = APIAgent(config={"cache_ttl": 300})

# ETF 목록 조회
etf_list = await agent.execute(endpoint="/etf/list", provider="ishares")

# ETF 상세 정보
etf_detail = await agent.execute(endpoint="/etf/detail", ticker="SPY")

# 요일별 배당 종목
dividends = await agent.execute(endpoint="/dividend/daily", day_of_week="Friday")

# 운용사 목록
providers = await agent.execute(endpoint="/provider/list")

# 캐시 초기화
agent.clear_cache()
```

### 5. Monitoring Agent
**목적**: Application Insights를 통해 애플리케이션 상태 모니터링

**주요 기능**:
- API 요청 추적
- 에러 추적
- 커스텀 메트릭 기록
- 헬스 체크

**사용 예시**:
```python
from backend.app.agents import MonitoringAgent

agent = MonitoringAgent(config={
    "connection_string": "InstrumentationKey=..."
})

# API 요청 추적
await agent.execute(
    operation="track_request",
    name="get_etf_list",
    duration=125.5,
    success=True
)

# 에러 추적
await agent.execute(
    operation="track_error",
    error_type="ValueError",
    message="Invalid ticker"
)

# 커스텀 메트릭
await agent.execute(
    operation="track_metric",
    name="etf_count",
    value=150.0
)

# 헬스 체크
health = await agent.execute(operation="get_health")
```

## Agent 통합 워크플로우

```python
from backend.app.agents import (
    DataIngestionAgent,
    DataProcessingAgent,
    DataStorageAgent,
    APIAgent,
    MonitoringAgent
)

# Agent 초기화
ingestion = DataIngestionAgent(config={"providers": ["ishares"]})
processing = DataProcessingAgent()
storage = DataStorageAgent(config={"data_dir": "data"})
api = APIAgent()
monitoring = MonitoringAgent()

# 1. 데이터 수집
with monitoring.start_trace("data_ingestion"):
    raw_data = await ingestion.execute(provider="ishares")

# 2. 데이터 처리
with monitoring.start_trace("data_processing"):
    cleaned_data = await processing.execute(data=raw_data["data"], operation="clean")
    unique_data = await processing.execute(data=cleaned_data["data"], operation="deduplicate")

# 3. 데이터 저장
with monitoring.start_trace("data_storage"):
    await storage.execute(
        operation="save",
        data=unique_data["data"],
        path="ishares/etf_list.json"
    )

# 4. API를 통한 데이터 제공
result = await api.execute(endpoint="/etf/list", provider="ishares")

# 5. 모니터링
await monitoring.execute(
    operation="track_metric",
    name="etf_processed",
    value=len(unique_data["data"])
)
```

## 테스트 실행

```bash
# 가상환경 활성화
source .venv/bin/activate

# 모든 Agent 테스트 실행
pytest backend/tests/agents/ -v

# 특정 Agent 테스트
pytest backend/tests/agents/test_data_ingestion_agent.py -v
pytest backend/tests/agents/test_data_processing_agent.py -v
pytest backend/tests/agents/test_data_storage_agent.py -v
pytest backend/tests/agents/test_api_agent.py -v
pytest backend/tests/agents/test_monitoring_agent.py -v
```

## 의존성 설치

```bash
# 가상환경에서 의존성 설치
source .venv/bin/activate
uv sync
```

## 주요 의존성
- `azure-identity>=1.19.0`: Azure 인증
- `opentelemetry-*`: Application Insights 통합
- `httpx`: 비동기 HTTP 클라이언트
- `msgpack`: 데이터 압축
- `beautifulsoup4`: 웹 스크래핑

**참고**: Microsoft Agent Framework는 현재 패키지 레지스트리에서 사용할 수 없어 기본 Agent 패턴을 직접 구현했습니다.

## 다음 단계
1. 기존 크롤러와 Data Ingestion Agent 연동
2. FastAPI 라우터에 API Agent 통합
3. 스케줄러를 통한 주기적 데이터 수집
4. Application Insights 연결 설정
