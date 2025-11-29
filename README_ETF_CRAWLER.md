# ETF 데이터 크롤링 시스템

## 개요

ETF 데이터를 주기적으로 수집하고 GitHub repository를 데이터베이스로 활용하는 시스템입니다.

## 아키텍처

```
backend/
├── app/
│   ├── models/
│   │   └── etf.py                    # ETF 데이터 모델
│   ├── services/
│   │   ├── crawlers/                 # 크롤러 모듈
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # 기본 크롤러 인터페이스
│   │   │   ├── ishares.py           # iShares 크롤러
│   │   │   └── roundhill.py         # Roundhill 크롤러
│   │   ├── data_manager.py          # GitHub repo 데이터 관리
│   │   ├── etf_updater.py           # ETF 데이터 업데이트 서비스
│   │   └── scheduler.py             # 주기적 업데이트 스케줄러
│   └── api/
│       └── v1/
│           └── etf.py                # ETF API 엔드포인트
└── scripts/
    └── manual_update.py              # 수동 업데이트 스크립트
```

## 데이터 저장 구조

```
data/
├── ishares/
│   ├── etf_list.json                 # ETF 목록 (개발)
│   ├── etf_list.msgpack              # ETF 목록 (운영, 압축)
│   ├── etf_list_metadata.json        # 메타데이터
│   ├── etf_list_part0.json           # 분할된 데이터 (4MB 초과 시)
│   └── etf_list_part1.json
├── roundhill/
│   └── ...
└── schwab/
    └── ...
```

## 주요 컴포넌트

### 1. BaseCrawler (기본 크롤러 인터페이스)

모든 운용사 크롤러가 구현해야 하는 기본 인터페이스:

```python
class BaseCrawler(ABC):
    async def fetch_data(self) -> Any:
        """원본 데이터 가져오기"""
        pass
    
    async def parse_data(self, raw_data: Any) -> List[ETF]:
        """데이터 파싱"""
        pass
    
    async def crawl(self) -> List[ETF]:
        """전체 크롤링 프로세스"""
        pass
```

### 2. DataManager (데이터 관리)

GitHub repo를 DB로 사용하는 데이터 관리자:

- 자동 데이터 분할 (4MB 초과 시)
- JSON/MessagePack 선택 가능
- 메타데이터 관리

```python
manager = DataManager()

# 데이터 저장
metadata = await manager.save_data(
    provider_name="ishares",
    data_type="etf_list",
    data=etf_list,
    use_msgpack=False  # 개발: False, 운영: True
)

# 데이터 로드
data = await manager.load_data("ishares", "etf_list")
```

### 3. ETFUpdater (업데이트 서비스)

모든 크롤러를 관리하고 데이터 업데이트를 수행:

```python
updater = ETFUpdater()

# 단일 운용사 업데이트
result = await updater.update_single_provider(crawler)

# 모든 운용사 업데이트
summary = await updater.update_all_providers()

# 저장된 데이터 조회
etf_list = await updater.get_etf_list("ishares")
```

### 4. DataUpdateScheduler (스케줄러)

주기적인 데이터 업데이트 스케줄링:

```python
scheduler = DataUpdateScheduler()

# 매일 미국 동부시간 오후 6시에 실행
scheduler.start(hour=18, minute=0, timezone="America/New_York")

# 즉시 실행
scheduler.run_now()

# 중지
scheduler.stop()
```

## API 엔드포인트

### ETF 데이터 조회

```bash
# 특정 운용사 ETF 목록
GET /api/v1/etf/list/{provider}

# 모든 운용사 ETF 목록
GET /api/v1/etf/list
```

### 데이터 업데이트

```bash
# 특정 운용사 데이터 업데이트
POST /api/v1/etf/update/{provider}

# 모든 운용사 데이터 업데이트
POST /api/v1/etf/update
```

### 스케줄러 관리

```bash
# 스케줄러 상태 확인
GET /api/v1/etf/scheduler/status

# 즉시 실행
POST /api/v1/etf/scheduler/run-now
```

## 사용 방법

### 1. 수동 데이터 업데이트

```bash
# 스크립트 실행
cd backend
source ../.venv/bin/activate
python scripts/manual_update.py
```

### 2. API를 통한 업데이트

```bash
# 모든 운용사 데이터 업데이트
curl -X POST http://localhost:8000/api/v1/etf/update

# iShares만 업데이트
curl -X POST http://localhost:8000/api/v1/etf/update/ishares
```

### 3. 자동 스케줄링

FastAPI 서버 시작 시 자동으로 스케줄러가 시작됩니다:

```bash
uvicorn app.main:app --reload
```

## 새로운 운용사 크롤러 추가하기

1. **크롤러 클래스 생성** (`app/services/crawlers/newprovider.py`):

```python
from .base import BaseCrawler
from app.models.etf import ETF

class NewProviderCrawler(BaseCrawler):
    async def fetch_data(self) -> Any:
        # 데이터 수집 로직
        pass
    
    async def parse_data(self, raw_data: Any) -> List[ETF]:
        # 데이터 파싱 로직
        pass
```

2. **크롤러 등록** (`app/services/crawlers/__init__.py`):

```python
from .newprovider import NewProviderCrawler

__all__ = [
    "BaseCrawler",
    "ISharesCrawler",
    "RoundhillCrawler",
    "NewProviderCrawler",  # 추가
]
```

3. **ETFUpdater에 등록** (`app/services/etf_updater.py`):

```python
self.crawlers: List[BaseCrawler] = [
    ISharesCrawler(),
    RoundhillCrawler(),
    NewProviderCrawler(),  # 추가
]
```

## 데이터 포맷

### JSON (개발 환경)
- 가독성 좋음
- 디버깅 용이
- 파일 크기 큼

### MessagePack (운영 환경)
- 바이너리 포맷
- 압축률 높음 (약 30-50% 감소)
- 성능 우수

## 모니터링

### 메타데이터 확인

```python
metadata = await manager.get_metadata("ishares", "etf_list")
print(f"Last updated: {metadata['updated_at']}")
print(f"Total count: {metadata['total_count']}")
print(f"Total size: {metadata['total_size']} bytes")
print(f"Chunked: {metadata['chunked']}")
```

### 로그 확인

모든 크롤링 작업은 콘솔에 로그를 출력합니다:

```
[iShares] Starting data crawl...
[iShares] Crawled 450 ETFs
[iShares] Saved data: 450 ETFs, 2.3 MB, chunked: False
```

## 주의사항

1. **API Rate Limiting**: 각 운용사 API에 적절한 요청 제한 적용
2. **데이터 크기**: 4MB 초과 시 자동 분할
3. **타임존**: 스케줄러는 미국 동부시간 기준
4. **에러 처리**: 개별 크롤러 실패 시 다른 크롤러는 계속 진행

## 향후 개선사항

- [ ] Git commit/push 자동화 (GitHub Actions)
- [ ] 데이터 변경 이력 관리
- [ ] 배당 정보 크롤링
- [ ] 실시간 가격 업데이트
- [ ] 크롤링 실패 알림 (Slack, Email)
- [ ] 데이터 검증 및 품질 체크
