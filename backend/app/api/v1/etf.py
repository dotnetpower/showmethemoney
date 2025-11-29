"""ETF API 엔드포인트"""
from typing import Dict, List

from app.models.etf import ETF
from app.services.etf_updater import ETFUpdater
from app.services.scheduler import scheduler
from fastapi import APIRouter, HTTPException

router = APIRouter()
etf_updater = ETFUpdater()


@router.get("/list/{provider}")
async def get_etf_list(provider: str) -> List[ETF]:
    """
    특정 운용사의 ETF 목록을 조회합니다.
    
    Args:
        provider: 운용사 이름 (ishares, roundhill 등)
    """
    try:
        etf_list = await etf_updater.get_etf_list(provider)
        return etf_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def get_all_etf_lists() -> Dict[str, List[ETF]]:
    """
    모든 운용사의 ETF 목록을 조회합니다.
    """
    try:
        return await etf_updater.get_all_etfs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
async def get_all_etfs_combined() -> List[ETF]:
    """
    모든 운용사의 ETF를 하나의 리스트로 통합하여 조회합니다.
    """
    try:
        all_etfs = await etf_updater.get_all_etfs()
        combined_list = []
        for provider_etfs in all_etfs.values():
            combined_list.extend(provider_etfs)
        return combined_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update/{provider}")
async def update_provider_data(provider: str) -> Dict:
    """
    특정 운용사의 데이터를 즉시 업데이트합니다.
    
    Args:
        provider: 운용사 이름
    """
    try:
        # 해당 provider의 crawler 찾기
        crawler = next(
            (c for c in etf_updater.crawlers if c.get_provider_name().lower() == provider.lower()),
            None
        )
        
        if not crawler:
            raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")
        
        result = await etf_updater.update_single_provider(crawler)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update")
async def update_all_data() -> Dict:
    """
    모든 운용사의 데이터를 즉시 업데이트합니다.
    """
    try:
        return await etf_updater.update_all_providers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler/status")
async def get_scheduler_status() -> Dict:
    """
    스케줄러 상태를 조회합니다.
    """
    next_run = scheduler.get_next_run_time()
    return {
        "running": scheduler._is_running,
        "next_run": next_run.isoformat() if next_run else None
    }


@router.post("/scheduler/run-now")
async def run_scheduler_now() -> Dict:
    """
    스케줄러를 즉시 실행합니다.
    """
    scheduler.run_now()
    return {"message": "Update job started"}
