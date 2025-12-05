"""
Data Ingestion Agent
ETF 및 주식 종목 데이터를 주기적으로 수집하는 Agent
Microsoft Agent Framework 기반
"""

from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup
from pydantic import Field

from .base_agent import BaseAgent


def fetch_web_data(url: Annotated[str, Field(description="웹 페이지 URL")]) -> str:
    """웹 페이지에서 데이터 가져오기"""
    # 동기 함수로 구현 (agent-framework tools는 동기/비동기 모두 지원)
    import httpx
    response = httpx.get(url, timeout=30.0)
    return response.text


def parse_html(
    html: Annotated[str, Field(description="파싱할 HTML 문자열")],
    selector: Annotated[str, Field(description="CSS 선택자")] = "table"
) -> str:
    """HTML에서 특정 요소 파싱"""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    elements = soup.select(selector)
    return str([str(el) for el in elements])


class DataIngestionAgent(BaseAgent):
    """데이터 수집 Agent"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        instructions = """
        당신은 ETF 및 주식 데이터를 수집하는 전문 Agent입니다.
        
        주요 역할:
        1. 운용사 웹사이트에서 ETF 목록 데이터 수집
        2. 배당금 지급 종목 데이터 수집
        3. Total Return ETF 데이터 수집
        
        데이터 수집 시:
        - 웹페이지에서 HTML을 가져오고 파싱
        - 필요한 정보를 추출하여 구조화된 형태로 반환
        - 에러 발생 시 상세한 로그 기록
        """
        
        tools = [fetch_web_data, parse_html]
        
        super().__init__(
            name="DataIngestion",
            instructions=instructions,
            tools=tools,
            config=config
        )
        
        self.providers = config.get("providers", [])
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """
        데이터 수집 작업 실행
        
        Args:
            operation: 작업 타입 (fetch_provider, fetch_dividend, fetch_total_return)
            **kwargs: 작업별 파라미터
            
        Returns:
            작업 결과
        """
        try:
            self.log_info(f"데이터 수집 작업 시작: {operation}")
            
            if not await self.validate(operation=operation, **kwargs):
                raise ValueError("유효하지 않은 작업")
            
            if operation == "fetch_provider":
                result = await self.fetch_provider_data(**kwargs)
            elif operation == "fetch_dividend":
                result = await self.fetch_dividend_data()
            elif operation == "fetch_total_return":
                result = await self.fetch_total_return_etf_data()
            else:
                raise ValueError(f"지원하지 않는 작업: {operation}")
            
            self.log_info(f"데이터 수집 작업 완료: {operation}")
            return result
            
        except Exception as e:
            self.log_error(f"데이터 수집 작업 실패: {operation}", exc_info=e)
            return {
                "operation": operation,
                "status": "error",
                "error": str(e)
            }
    
    async def validate(self, operation: str, **kwargs) -> bool:
        """
        작업 검증
        
        Args:
            operation: 작업 타입
            **kwargs: 작업 파라미터
            
        Returns:
            유효성 여부
        """
        valid_operations = ["fetch_provider", "fetch_dividend", "fetch_total_return"]
        if operation not in valid_operations:
            return False
        
        if operation == "fetch_provider":
            if "provider" not in kwargs:
                return False
        
        return True
        
    async def fetch_provider_data(self, provider: str) -> Dict[str, Any]:
        """
        특정 운용사의 ETF 데이터 수집
        
        Args:
            provider: 운용사 이름
            
        Returns:
            수집된 데이터
        """
        try:
            self.log_info(f"데이터 수집 시작: {provider}")
            
            # Agent에게 작업 요청
            task = f"""
            {provider} 운용사의 ETF 목록 데이터를 수집해주세요.
            
            1. 해당 운용사의 웹사이트에서 ETF 목록 페이지 접근
            2. HTML 파싱하여 ETF 정보 추출
            3. 티커, 이름, 가격, 배당률 등의 정보 수집
            
            결과를 JSON 형태로 반환해주세요.
            """
            
            result = await self.run(task)
            
            return {
                "provider": provider,
                "data": result,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            self.log_error(f"데이터 수집 실패: {provider}", exc_info=e)
            return {
                "provider": provider,
                "data": [],
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    async def fetch_dividend_data(self) -> Dict[str, Any]:
        """
        배당금 지급 종목 데이터 수집
        
        Returns:
            배당 데이터
        """
        try:
            self.log_info("배당 데이터 수집 시작")
            
            task = """
            배당금 지급 종목 데이터를 수집해주세요.
            
            요일별, 월별로 배당금을 지급하는 ETF 및 주식 종목을 찾아
            티커, 배당금, 지급일, 배당률 정보를 JSON 형태로 반환해주세요.
            """
            
            result = await self.run(task)
            
            return {
                "type": "dividend",
                "data": result,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            self.log_error("배당 데이터 수집 실패", exc_info=e)
            return {
                "type": "dividend",
                "data": [],
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    async def fetch_total_return_etf_data(self) -> Dict[str, Any]:
        """
        Total Return ETF 데이터 수집
        
        Returns:
            Total Return ETF 데이터
        """
        try:
            self.log_info("Total Return ETF 데이터 수집 시작")
            
            task = """
            Total Return ETF 데이터를 ETFDB, totalreturnetf.com 등에서 수집해주세요.
            
            각 ETF의 티커, 이름, 총 수익률, 배당률, 시가총액 등을 
            JSON 형태로 반환해주세요.
            """
            
            result = await self.run(task)
            
            return {
                "type": "total_return",
                "data": result,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            self.log_error("Total Return ETF 데이터 수집 실패", exc_info=e)
            return {
                "type": "total_return",
                "data": [],
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    async def close(self):
        """리소스 정리"""
        await self.client.aclose()
