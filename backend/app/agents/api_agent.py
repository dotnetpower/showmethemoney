"""
API Agent
FastAPI 서버를 통해 데이터를 제공하는 Agent
Microsoft Agent Framework 기반
"""

from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from fastapi import HTTPException
from pydantic import Field

from .base_agent import BaseAgent
from .data_storage_agent import DataStorageAgent


def get_cached_data(cache_key: Annotated[str, Field(description="캐시 키")]) -> Optional[Any]:
    """캐시에서 데이터 조회"""
    # 실제 구현은 외부 캐시 시스템 연동
    return None


class APIAgent(BaseAgent):
    """API 서비스 Agent"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        instructions = """
        당신은 FastAPI를 통해 데이터를 제공하는 API 서비스 Agent입니다.
        
        주요 역할:
        1. API 엔드포인트별 데이터 처리
        2. 캐싱을 통한 성능 최적화
        3. 데이터 검증 및 에러 처리
        
        지원하는 엔드포인트:
        - /etf/list: ETF 목록 조회
        - /etf/detail: ETF 상세 정보
        - /dividend/daily: 일별 배당 정보
        - /dividend/monthly: 월별 배당 정보
        - /total-return/list: Total Return ETF 목록
        - /provider/list: 운용사 목록
        """
        
        tools = [get_cached_data]
        
        super().__init__(
            name="API",
            instructions=instructions,
            tools=tools,
            config=config
        )
        
        self.storage_agent = DataStorageAgent(config)
        self.cache = {}
        self.cache_ttl = config.get("cache_ttl", 300)
        
    async def execute(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        API 요청 처리
        
        Args:
            endpoint: API 엔드포인트
            **kwargs: 요청 파라미터
            
        Returns:
            API 응답
        """
        try:
            self.log_info(f"API 요청 처리: {endpoint}")
            
            if not await self.validate(endpoint=endpoint, **kwargs):
                raise ValueError("유효하지 않은 API 요청")
            
            # 캐시 확인
            cache_key = f"{endpoint}:{str(kwargs)}"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if (datetime.utcnow() - cached_time).seconds < self.cache_ttl:
                    self.log_info(f"캐시 사용: {endpoint}")
                    return {
                        "endpoint": endpoint,
                        "data": cached_data,
                        "cached": True,
                        "status": "success"
                    }
            
            # 엔드포인트별 처리
            if endpoint == "/etf/list":
                result = await self._get_etf_list(**kwargs)
            elif endpoint == "/etf/detail":
                result = await self._get_etf_detail(**kwargs)
            elif endpoint == "/dividend/daily":
                result = await self._get_dividend_daily(**kwargs)
            elif endpoint == "/dividend/monthly":
                result = await self._get_dividend_monthly(**kwargs)
            elif endpoint == "/total-return/list":
                result = await self._get_total_return_list(**kwargs)
            elif endpoint == "/provider/list":
                result = await self._get_provider_list(**kwargs)
            else:
                raise ValueError(f"지원하지 않는 엔드포인트: {endpoint}")
            
            # 캐시 저장
            self.cache[cache_key] = (result, datetime.utcnow())
            
            self.log_info(f"API 응답 완료: {endpoint}")
            return {
                "endpoint": endpoint,
                "data": result,
                "cached": False,
                "status": "success"
            }
            
        except Exception as e:
            self.log_error(f"API 요청 실패: {endpoint}", exc_info=e)
            return {
                "endpoint": endpoint,
                "data": None,
                "status": "error",
                "error": str(e)
            }
    
    async def validate(self, endpoint: str, **kwargs) -> bool:
        """
        API 요청 검증
        
        Args:
            endpoint: 엔드포인트
            **kwargs: 요청 파라미터
            
        Returns:
            유효성 여부
        """
        valid_endpoints = [
            "/etf/list",
            "/etf/detail",
            "/dividend/daily",
            "/dividend/monthly",
            "/total-return/list",
            "/provider/list"
        ]
        
        if endpoint not in valid_endpoints:
            return False
        
        # 엔드포인트별 필수 파라미터 검증
        if endpoint == "/etf/detail":
            if "ticker" not in kwargs:
                return False
        
        return True
    
    async def _get_etf_list(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        ETF 목록 조회
        
        Args:
            provider: 운용사 필터 (선택)
            
        Returns:
            ETF 목록
        """
        if provider:
            # 특정 운용사 ETF
            result = await self.storage_agent.load(
                path=f"{provider.lower()}/etf_list.json"
            )
        else:
            # 전체 ETF (여러 운용사 데이터 통합)
            all_etfs = []
            providers = await self._get_provider_list()
            
            for provider_info in providers:
                provider_name = provider_info["name"]
                try:
                    provider_result = await self.storage_agent.load(
                        path=f"{provider_name}/etf_list.json"
                    )
                    provider_data = provider_result.get("data", [])
                    if isinstance(provider_data, list):
                        all_etfs.extend(provider_data)
                except Exception as e:
                    self.log_warning(f"Failed to load data for {provider_name}: {e}")
            
            return all_etfs
        
        return result.get("data", [])
    
    async def _get_etf_detail(self, ticker: str) -> Dict[str, Any]:
        """
        ETF 상세 정보 조회
        
        Args:
            ticker: ETF 티커
            
        Returns:
            ETF 상세 정보
        """
        # 여러 운용사 데이터에서 검색
        providers = await self._get_provider_list()
        
        for provider_info in providers:
            provider_name = provider_info["name"]
            try:
                result = await self.storage_agent.load(
                    path=f"{provider_name}/etf_list.json"
                )
                etf_list = result.get("data", [])
                
                # ticker로 검색
                for etf in etf_list:
                    if isinstance(etf, dict) and etf.get("ticker", "").upper() == ticker.upper():
                        return {
                            "ticker": ticker,
                            "name": etf.get("name", ""),
                            "provider": provider_name,
                            "details": etf
                        }
            except Exception as e:
                self.log_warning(f"Failed to search in {provider_name}: {e}")
        
        # 찾지 못한 경우
        return {
            "ticker": ticker,
            "name": "",
            "provider": "",
            "details": {},
            "error": "ETF not found"
        }
    
    async def _get_dividend_daily(self, day_of_week: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        요일별 배당금 지급 종목 조회
        
        Args:
            day_of_week: 요일 (Monday, Tuesday, ...)
            
        Returns:
            배당금 지급 종목 목록
        """
        try:
            result = await self.storage_agent.load(
                path="dividend/daily.json"
            )
            
            data = result.get("data", [])
            
            if day_of_week:
                data = [item for item in data if item.get("day") == day_of_week]
            
            return data
        except Exception as e:
            self.log_error(f"배당 데이터 로드 실패: {e}")
            return []
    
    async def _get_dividend_monthly(self, month: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        월별 배당금 지급 종목 조회
        
        Args:
            month: 월 (1-12)
            
        Returns:
            배당금 지급 종목 목록
        """
        try:
            result = await self.storage_agent.load(
                path="dividends/monthly.json"
            )
            
            data = result.get("data", [])
            
            if month:
                data = [item for item in data if item.get("month") == month]
            
            return data
        except Exception as e:
            self.log_error(f"배당 데이터 로드 실패: {e}")
            return []
    
    async def _get_total_return_list(self) -> List[Dict[str, Any]]:
        """
        Total Return ETF 목록 조회
        
        Returns:
            Total Return ETF 목록
        """
        try:
            result = await self.storage_agent.load(
                path="total_return/etf_list.json"
            )
            
            return result.get("data", [])
        except Exception as e:
            self.log_error(f"Total Return ETF 데이터 로드 실패: {e}")
            return []
    
    async def _get_provider_list(self) -> List[Dict[str, str]]:
        """
        운용사 목록 조회
        
        Returns:
            운용사 목록
        """
        from pathlib import Path
        
        data_dir = self.storage_agent.data_dir
        providers = []
        
        if data_dir.exists():
            for item in data_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('_'):
                    # etf_list.json 파일이 있는지 확인
                    etf_list_file = item / "etf_list.json"
                    if etf_list_file.exists():
                        providers.append({
                            "name": item.name,
                            "display_name": item.name.replace('_', ' ').title()
                        })
        
        return sorted(providers, key=lambda x: x["display_name"])
    
    def clear_cache(self):
        """캐시 초기화"""
        self.cache.clear()
        self.log_info("캐시 초기화 완료")
