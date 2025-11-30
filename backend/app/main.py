"""FastAPI entrypoint for show-me-the-money."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from observability import (TracingMiddleware, initialize_metrics,
                           setup_telemetry)

from .api import api_router
from .core.config import get_settings
from .services.scheduler import scheduler

# 설정 가져오기
settings = get_settings()

# 로거 초기화
logger = logging.getLogger(__name__)

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

# Application Insights 텔레메트리 설정 (app 전달로 자동 instrumentation)
setup_telemetry(app)

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
    logger.info("=" * 60)
    logger.info("show-me-the-money API starting...")
    logger.info("=" * 60)
    
    # 환경 정보 로깅
    import os
    logger.info(f"[Startup] DATA_DIR env: {os.environ.get('DATA_DIR', 'NOT SET')}")
    logger.info(f"[Startup] Current working directory: {os.getcwd()}")
    
    # 현재 디렉토리 내용 로깅
    try:
        cwd_contents = os.listdir(os.getcwd())
        logger.info(f"[Startup] CWD contents: {cwd_contents[:10]}")
        if len(cwd_contents) > 10:
            logger.info(f"[Startup]   ... and {len(cwd_contents) - 10} more items")
    except Exception as e:
        logger.error(f"[Startup] Error listing CWD: {e}")
    
    # /app 디렉토리 확인 (Docker 환경)
    app_dir = "/app"
    if os.path.exists(app_dir):
        try:
            app_contents = os.listdir(app_dir)
            logger.info(f"[Startup] /app directory contents: {app_contents}")
        except Exception as e:
            logger.error(f"[Startup] Error listing /app: {e}")
    
    # /app/data 디렉토리 확인
    app_data_dir = "/app/data"
    logger.info(f"[Startup] /app/data exists: {os.path.exists(app_data_dir)}")
    if os.path.exists(app_data_dir):
        try:
            data_contents = os.listdir(app_data_dir)
            logger.info(f"[Startup] /app/data contents count: {len(data_contents)}")
            logger.info(f"[Startup] /app/data contents (first 10): {data_contents[:10]}")
        except Exception as e:
            logger.error(f"[Startup] Error listing /app/data: {e}")
    
    # 데이터 디렉토리 확인
    data_dir = settings.github_data_dir
    logger.info(f"[Startup] Configured data directory: {data_dir}")
    logger.info(f"[Startup] Data directory exists: {data_dir.exists()}")
    logger.info(f"[Startup] Data directory is_dir: {data_dir.is_dir() if data_dir.exists() else 'N/A'}")
    
    if data_dir.exists():
        try:
            subdirs = [d for d in os.listdir(data_dir) if os.path.isdir(data_dir / d)]
            files = [f for f in os.listdir(data_dir) if os.path.isfile(data_dir / f)]
            logger.info(f"[Startup] Data directory has {len(subdirs)} subdirs, {len(files)} files")
            logger.info(f"[Startup] Subdirectories (first 10): {subdirs[:10]}")
            if len(subdirs) > 10:
                logger.info(f"[Startup]   ... and {len(subdirs) - 10} more subdirs")
        except PermissionError as e:
            logger.error(f"[Startup] Permission error reading data directory: {e}")
        except Exception as e:
            logger.error(f"[Startup] Error reading data directory: {e}")
    else:
        logger.warning(f"[Startup] Data directory does not exist: {data_dir}")
        # 상위 디렉토리 확인
        parent_dir = data_dir.parent
        logger.info(f"[Startup] Parent directory: {parent_dir}")
        logger.info(f"[Startup] Parent exists: {parent_dir.exists()}")
        if parent_dir.exists():
            try:
                parent_contents = os.listdir(parent_dir)
                logger.info(f"[Startup] Parent contents: {parent_contents}")
            except Exception as e:
                logger.error(f"[Startup] Error listing parent: {e}")
    
    # 초기 데이터 로드 확인
    from .services.etf_updater import ETFUpdater
    logger.info("[Startup] Creating ETFUpdater instance...")
    etf_updater = ETFUpdater()
    
    try:
        logger.info("[Startup] Loading all ETFs...")
        all_etfs = await etf_updater.get_all_etfs()
        total_etfs = sum(len(etfs) for etfs in all_etfs.values())
        logger.info(f"[Startup] Loaded {total_etfs} ETFs from {len(all_etfs)} providers")
        
        # 각 프로바이더별 ETF 수 로깅
        for provider, etfs in all_etfs.items():
            logger.info(f"[Startup]   - {provider}: {len(etfs)} ETFs")
        
        # 데이터가 없으면 경고
        if total_etfs == 0:
            logger.warning("[Startup] No ETF data found. Please run initial data collection using /api/v1/etf/update endpoint")
            logger.warning("[Startup] You can trigger it manually or wait for the scheduled update")
    except Exception as e:
        logger.error(f"[Startup] Error checking initial data: {e}", exc_info=True)
    
    # 데이터 업데이트 스케줄러 시작 (매일 미국 동부시간 오후 6시)
    scheduler.start(hour=18, minute=0, timezone="America/New_York")
    
    logger.info("=" * 60)
    logger.info("show-me-the-money API started successfully")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """애플리케이션 종료 시 스케줄러 중지"""
    scheduler.stop()
    logger.info("show-me-the-money API stopped")


@app.get("/health", tags=["system"])
async def health_check():
    """기본 헬스 체크"""
    return {"status": "ok"}


@app.get("/health/detailed", tags=["system"])
async def detailed_health_check():
    """
    상세 헬스 체크 - 데이터 디렉토리 상태 및 ETF 데이터 정보 포함
    
    디버깅 목적으로 사용됩니다.
    """
    import os
    from .services.etf_updater import ETFUpdater
    
    data_dir = settings.github_data_dir
    
    # 데이터 디렉토리 상태
    data_dir_info = {
        "path": str(data_dir),
        "exists": data_dir.exists(),
        "is_dir": data_dir.is_dir() if data_dir.exists() else None,
    }
    
    # 디렉토리 내용
    if data_dir.exists() and data_dir.is_dir():
        try:
            items = list(data_dir.iterdir())
            subdirs = [item.name for item in items if item.is_dir()]
            files = [item.name for item in items if item.is_file()]
            data_dir_info["subdirs_count"] = len(subdirs)
            data_dir_info["files_count"] = len(files)
            data_dir_info["subdirs"] = subdirs[:20]  # 처음 20개만
        except Exception as e:
            data_dir_info["error"] = str(e)
    
    # 환경 정보
    env_info = {
        "DATA_DIR": os.environ.get("DATA_DIR", "NOT SET"),
        "cwd": os.getcwd(),
    }
    
    # ETF 데이터 로드 확인
    etf_info = {}
    try:
        etf_updater = ETFUpdater()
        all_etfs = await etf_updater.get_all_etfs()
        total_etfs = sum(len(etfs) for etfs in all_etfs.values())
        etf_info = {
            "total_etfs": total_etfs,
            "providers_count": len(all_etfs),
            "providers": {provider: len(etfs) for provider, etfs in all_etfs.items()}
        }
    except Exception as e:
        etf_info["error"] = str(e)
    
    return {
        "status": "ok",
        "data_directory": data_dir_info,
        "environment": env_info,
        "etf_data": etf_info
    }
