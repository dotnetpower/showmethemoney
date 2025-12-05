# Agents - Microsoft Agent Framework 기반

이 디렉토리는 Microsoft Agent Framework를 활용하여 구현된 다양한 AI Agent들을 포함합니다.

## 구조

### BaseAgent
모든 Agent의 기본 클래스로, Microsoft Agent Framework의 `ChatAgent`를 래핑합니다.

```python
from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
```

### Agent 목록

#### 1. DataIngestionAgent
ETF 및 주식 종목 데이터를 수집하는 Agent

**주요 기능:**
- 운용사별 ETF 데이터 수집
- 배당금 지급 종목 데이터 수집
- Total Return ETF 데이터 수집

**Tools:**
- `fetch_web_data`: 웹 페이지에서 데이터 가져오기
- `parse_html`: HTML 파싱

**사용 예시:**
```python
agent = DataIngestionAgent(config={
    "providers": ["ishares", "vanguard"],
    "openai_api_key": "your-api-key"
})

result = await agent.fetch_provider_data("ishares")
```

#### 2. DataProcessingAgent
수집된 데이터를 정제 및 변환하는 Agent

**주요 기능:**
- 데이터 정제 (null 값 제거, 타입 정규화)
- 형식 변환 (JSON, MessagePack)
- 유효성 검사
- 중복 제거

**Tools:**
- `clean_data_item`: 개별 데이터 아이템 정제
- `validate_data_structure`: 데이터 구조 유효성 검사
- `remove_duplicates`: 중복 데이터 제거

**사용 예시:**
```python
agent = DataProcessingAgent(config={
    "use_msgpack": False,
    "openai_api_key": "your-api-key"
})

result = await agent.clean(raw_data)
```

#### 3. DataStorageAgent
데이터를 GitHub Repository에 저장 및 관리하는 Agent

**주요 기능:**
- JSON 파일로 데이터 저장
- 대용량 데이터 분할 저장 (4MB 제한)
- Git commit 및 push
- 데이터 로드 및 삭제

**Tools:**
- `save_json_file`: JSON 파일 저장
- `load_json_file`: JSON 파일 로드
- `delete_file`: 파일 삭제
- `git_commit_push`: Git 커밋 및 푸시

**사용 예시:**
```python
agent = DataStorageAgent(config={
    "data_dir": "data",
    "max_file_size": 4 * 1024 * 1024,
    "use_branches": True,
    "openai_api_key": "your-api-key"
})

result = await agent.save(
    data=etf_list,
    path="ishares/etf_list.json",
    commit_message="Update iShares ETF list"
)
```

#### 4. APIAgent
FastAPI를 통해 데이터를 제공하는 Agent

**주요 기능:**
- API 엔드포인트별 데이터 처리
- 캐싱을 통한 성능 최적화
- 데이터 검증 및 에러 처리

**사용 예시:**
```python
agent = APIAgent(config={
    "cache_ttl": 300,
    "openai_api_key": "your-api-key"
})
```

#### 5. MonitoringAgent
Application Insights를 통해 애플리케이션 상태를 모니터링하는 Agent

**주요 기능:**
- API 요청 및 성능 메트릭 추적
- 에러 모니터링
- 애플리케이션 상태 확인

**Tools:**
- `track_metric_data`: 메트릭 데이터 추적

**사용 예시:**
```python
agent = MonitoringAgent(config={
    "connection_string": "InstrumentationKey=...",
    "openai_api_key": "your-api-key"
})
```

## 환경 설정

각 Agent를 사용하려면 다음 환경 변수가 필요합니다:

```bash
# OpenAI API 키
OPENAI_API_KEY=your-api-key

# Azure Monitor (선택사항)
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...
```

## 설정 파일 예시

```python
config = {
    "openai_api_key": os.getenv("OPENAI_API_KEY"),
    "model": "gpt-4",
    "data_dir": "data",
    "max_file_size": 4 * 1024 * 1024,
    "use_branches": True,
    "cache_ttl": 300,
    "providers": ["ishares", "vanguard", "spdr"],
    "connection_string": os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
}
```

## Agent 실행 예시

```python
import asyncio
from backend.app.agents import (
    DataIngestionAgent,
    DataProcessingAgent,
    DataStorageAgent
)

async def main():
    # 1. 데이터 수집
    ingestion_agent = DataIngestionAgent(config)
    raw_data = await ingestion_agent.fetch_provider_data("ishares")
    
    # 2. 데이터 정제
    processing_agent = DataProcessingAgent(config)
    cleaned_data = await processing_agent.clean(raw_data["data"])
    
    # 3. 데이터 저장
    storage_agent = DataStorageAgent(config)
    await storage_agent.save(
        data=cleaned_data["data"],
        path="ishares/etf_list.json",
        commit_message="Update iShares ETF list"
    )

if __name__ == "__main__":
    asyncio.run(main())
```

## 참고사항

- 모든 Agent는 비동기(`async/await`)로 동작합니다
- Agent는 OpenAI ChatClient를 사용하므로 API 키가 필요합니다
- Tools는 Agent가 작업을 수행하는 데 사용하는 함수들입니다
- Agent의 `run()` 메서드로 자연어 작업 지시가 가능합니다

## 추가 정보

Microsoft Agent Framework 문서: https://github.com/microsoft/agent-framework
