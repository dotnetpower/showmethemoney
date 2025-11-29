"""FastAPI entrypoint for show-me-the-money."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from observability import (TracingMiddleware, initialize_metrics,
                           setup_telemetry)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from .api import api_router
from .core.config import get_settings
from .core.logger import configure_tracing, logger
from .services.scheduler import scheduler

# 설정 가져오기
settings = get_settings()

# Swagger/OpenAPI 메타데이터
app = FastAPI(
    title="Show Me The Money API",
    description="""
    ETF 및 주식 종목 데이터를 수집, 저장, 조회하는 API입니다.
    
    ## 주요 기능
    
    * **ETF 데이터 조회**: 14개 이상의 운용사에서 3,600개 이상의 ETF 데이터 제공
    * **배당 정보**: 요일별/월별 배당금 지급 종목 조회
    * **Total Return ETF**: Total Return ETF 종목 및 상세 정보
    * **데이터 업데이트**: 자동 스케줄링을 통한 정기 데이터 갱신
    
    ## 지원 운용사
    
    iShares, FirstTrust, Direxion, Invesco, SPDR, GlobalX, Vanguard, 
    Franklin Templeton, JPMorgan, Pacer Advisors, Roundhill, 
    Dimensional Fund Advisors, PIMCO, Goldman Sachs, Alpha Architect 등
    """,
    version="1.0.0",
    contact={
        "name": "Show Me The Money Team",
        "url": "https://github.com/dotnetpower/showmethemoney",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json",
)
setup_telemetry(app)

# 로깅 설정 (텔레메트리 설정 이후)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True  # 기존 핸들러를 유지하면서 설정 적용
)
logger = logging.getLogger(__name__)
app.include_router(api_router, prefix="/api")

# CORS 설정: 환경 변수 CORS_ORIGINS에서 허용 도메인을 로드
# 예: CORS_ORIGINS="https://example.com,https://api.example.com"
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# 커스텀 메트릭 초기화 (Live Metrics용)
initialize_metrics(service_name=app.title)

# Tracing 미들웨어 추가 (Live Metrics 데이터 수집)
app.add_middleware(TracingMiddleware)

@app.on_event("startup")
async def startup_event() -> None:
    settings = get_settings()
    configure_tracing(settings.application_insights_connection_string, settings.app_name)
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    logger.info("show-me-the-money API started")
    
    # 데이터 디렉토리 확인
    logger.info(f"Data directory: {settings.github_data_dir}")
    logger.info(f"Data directory exists: {settings.github_data_dir.exists()}")
    if settings.github_data_dir.exists():
        import os
        subdirs = [d for d in os.listdir(settings.github_data_dir) if os.path.isdir(settings.github_data_dir / d)]
        logger.info(f"Subdirectories in data: {len(subdirs)} - {subdirs[:5]}")
    
    # 초기 데이터 로드 확인
    from .services.etf_updater import ETFUpdater
    etf_updater = ETFUpdater()
    
    try:
        all_etfs = await etf_updater.get_all_etfs()
        total_etfs = sum(len(etfs) for etfs in all_etfs.values())
        logger.info(f"Loaded {total_etfs} ETFs from {len(all_etfs)} providers")
        
        # 데이터가 없으면 경고
        if total_etfs == 0:
            logger.warning("No ETF data found. Please run initial data collection using /api/v1/etf/update endpoint")
            logger.warning("You can trigger it manually or wait for the scheduled update")
    except Exception as e:
        logger.error(f"Error checking initial data: {e}", exc_info=True)
    
    # 데이터 업데이트 스케줄러 시작 (매일 미국 동부시간 오후 6시)
    scheduler.start(hour=18, minute=0, timezone="America/New_York")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """애플리케이션 종료 시 스케줄러 중지"""
    scheduler.stop()
    logger.info("show-me-the-money API stopped")


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok"}
