"""ETF API 엔드포인트"""

from decimal import Decimal
from typing import Dict, List, Union
import logging
import re
from app.models.etf import (
    ETF, 
    DividendSimulationRequest, 
    DividendSimulationResult
)
from app.services.etf_updater import ETFUpdater
from app.services.scheduler import scheduler
from fastapi import APIRouter, HTTPException, Path

logger = logging.getLogger(__name__)


def to_decimal(value: Union[str, int, float, Decimal]) -> Decimal:
    """Convert various types to Decimal safely."""
    return Decimal(str(value))


router = APIRouter(
    prefix="/etf",
    tags=["ETF"],
)
etf_updater = ETFUpdater()

# 허용된 문자 패턴 (영문자/숫자로 시작, 이후 영문, 숫자, 하이픈, 언더스코어 허용)
SAFE_PROVIDER_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_ -]*$')


def validate_provider_name(provider: str) -> str:
    """
    Provider 이름을 검증합니다.
    
    Args:
        provider: 검증할 provider 이름
        
    Returns:
        검증된 provider 이름
        
    Raises:
        HTTPException: 유효하지 않은 provider 이름인 경우
    """
    if not provider or len(provider) > 100:
        raise HTTPException(
            status_code=400,
            detail="Invalid provider name: must be 1-100 characters"
        )
    
    if not SAFE_PROVIDER_PATTERN.match(provider):
        raise HTTPException(
            status_code=400,
            detail="Invalid provider name: contains disallowed characters"
        )
    
    return provider.strip()


@router.get(
    "/list/{provider}",
    response_model=List[ETF],
    summary="특정 운용사 ETF 목록 조회",
    description="""
    지정된 운용사의 모든 ETF 목록을 조회합니다.
    
    **지원 운용사**: ishares, firsttrust, direxion, invesco, spdr, globalx, vanguard,
    franklin templeton, jpmorgan, pacer advisors, roundhill, dimensional fund advisors,
    pimco, goldmansachs, alpha architect
    """,
)
async def get_etf_list(
    provider: str = Path(
        ...,
        description="운용사 이름 (예: ishares, vanguard, goldmansachs)",
        examples=["ishares"]
    )
) -> List[ETF]:
    """특정 운용사의 ETF 목록을 조회합니다."""
    try:
        # Provider 이름 검증
        safe_provider = validate_provider_name(provider)
        
        etf_list = await etf_updater.get_etf_list(safe_provider)
        if not etf_list:
            raise HTTPException(
                status_code=404, 
                detail=f"Provider '{safe_provider}' not found or has no data"
            )
        return etf_list
    except HTTPException:
        raise
    except ValueError as e:
        # 입력 유효성 검사 오류는 400으로 반환
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 내부 오류는 로깅하고 일반적인 메시지만 반환
        logger.error(f"Error getting ETF list for provider {provider}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/list",
    response_model=Dict[str, List[ETF]],
    summary="전체 운용사 ETF 목록 조회",
    description="모든 운용사의 ETF 목록을 운용사별로 그룹화하여 조회합니다.",
)
async def get_all_etf_lists() -> Dict[str, List[ETF]]:
    """모든 운용사의 ETF 목록을 조회합니다."""
    try:
        return await etf_updater.get_all_etfs()
    except Exception as e:
        logger.error(f"Error getting all ETF lists: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/all",
    response_model=List[ETF],
    summary="전체 ETF 통합 조회",
    description="모든 운용사의 ETF를 하나의 리스트로 통합하여 조회합니다. 총 3,600개 이상의 ETF 데이터를 제공합니다.",
)
async def get_all_etfs_combined() -> List[ETF]:
    """모든 운용사의 ETF를 하나의 리스트로 통합하여 조회합니다."""
    try:
        all_etfs = await etf_updater.get_all_etfs()
        combined_list = []
        for provider_etfs in all_etfs.values():
            combined_list.extend(provider_etfs)
        return combined_list
    except Exception as e:
        logger.error(f"Error getting combined ETF list: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/update/{provider}",
    summary="특정 운용사 데이터 업데이트",
    description="지정된 운용사의 ETF 데이터를 즉시 크롤링하여 업데이트합니다.",
    tags=["ETF", "Admin"],
)
async def update_provider_data(
    provider: str = Path(
        ...,
        description="업데이트할 운용사 이름",
        examples=["ishares"]
    )
) -> Dict:
    """특정 운용사의 데이터를 즉시 업데이트합니다."""
    try:
        # Provider 이름 검증
        safe_provider = validate_provider_name(provider)
        
        # 해당 provider의 crawler 찾기
        crawler = next(
            (c for c in etf_updater.crawlers if c.get_provider_name().lower() == safe_provider.lower()),
            None
        )
        
        if not crawler:
            raise HTTPException(status_code=404, detail=f"Provider '{safe_provider}' not found")
        
        result = await etf_updater.update_single_provider(crawler)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating provider {provider}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/update",
    summary="전체 데이터 업데이트",
    description="모든 운용사의 ETF 데이터를 즉시 크롤링하여 업데이트합니다. 시간이 오래 걸릴 수 있습니다.",
    tags=["ETF", "Admin"],
)
async def update_all_data() -> Dict:
    """모든 운용사의 데이터를 즉시 업데이트합니다."""
    try:
        return await etf_updater.update_all_providers()
    except Exception as e:
        logger.error(f"Error updating all providers: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/scheduler/status",
    summary="스케줄러 상태 조회",
    description="자동 업데이트 스케줄러의 현재 상태와 다음 실행 시간을 조회합니다.",
    tags=["ETF", "Admin"],
)
async def get_scheduler_status() -> Dict:
    """스케줄러 상태를 조회합니다."""
    next_run = scheduler.get_next_run_time()
    return {
        "running": scheduler._is_running,
        "next_run": next_run.isoformat() if next_run else None,
        "timezone": "America/New_York",
        "scheduled_time": "18:00 (6:00 PM EST)"
    }


@router.post(
    "/scheduler/run-now",
    summary="스케줄러 즉시 실행",
    description="예약된 자동 업데이트 작업을 즉시 실행합니다.",
    tags=["ETF", "Admin"],
)
async def run_scheduler_now() -> Dict:
    """스케줄러를 즉시 실행합니다."""
    scheduler.run_now()
    return {"message": "Update job started", "status": "running"}


@router.post(
    "/simulate-dividend",
    response_model=DividendSimulationResult,
    summary="배당금 시뮬레이션",
    description="""
    특정 ETF에 대한 배당금 시뮬레이션을 수행합니다.
    투자 금액과 보유 기간을 입력하면 예상 배당금을 계산합니다.
    """,
)
async def simulate_dividend(
    request: DividendSimulationRequest
) -> DividendSimulationResult:
    """배당금 시뮬레이션을 수행합니다."""
    try:
        # 모든 ETF에서 해당 티커 찾기
        all_etfs = await etf_updater.get_all_etfs()
        target_etf = None
        
        for provider_etfs in all_etfs.values():
            for etf in provider_etfs:
                if etf.ticker.upper() == request.ticker.upper():
                    target_etf = etf
                    break
            if target_etf:
                break
        
        if not target_etf:
            raise HTTPException(
                status_code=404, 
                detail=f"ETF '{request.ticker}' not found"
            )
        
        # 배당 수익률이 없는 경우
        if not target_etf.distribution_yield:
            raise HTTPException(
                status_code=400, 
                detail=f"ETF '{request.ticker}' does not have distribution yield data"
            )
        
        # 시뮬레이션 계산
        nav = to_decimal(target_etf.nav_amount)
        yield_rate = to_decimal(target_etf.distribution_yield) / to_decimal(100)
        investment = to_decimal(request.investment_amount)
        
        shares = investment / nav
        annual_dividend = investment * yield_rate
        monthly_dividend = annual_dividend / to_decimal(12)
        total_dividend = monthly_dividend * to_decimal(request.holding_period_months)
        
        return DividendSimulationResult(
            ticker=target_etf.ticker,
            fund_name=target_etf.fund_name,
            investment_amount=investment,
            shares_purchased=shares.quantize(to_decimal("0.01")),
            current_price=nav,
            distribution_yield=target_etf.distribution_yield,
            annual_dividend_estimate=annual_dividend.quantize(to_decimal("0.01")),
            monthly_dividend_estimate=monthly_dividend.quantize(to_decimal("0.01")),
            holding_period_months=request.holding_period_months,
            total_dividend_estimate=total_dividend.quantize(to_decimal("0.01"))
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
