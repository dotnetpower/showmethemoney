"""기본 크롤러 인터페이스"""
from abc import ABC, abstractmethod
from inspect import isawaitable
from typing import Any, List

from app.models.etf import ETF


class BaseCrawler(ABC):
    """모든 ETF 크롤러의 기본 인터페이스"""
    
    def __init__(self):
        self.provider_name: str = self.__class__.__name__.replace("Crawler", "")
    
    @abstractmethod
    async def fetch_data(self) -> Any:
        """
        원본 데이터를 가져옵니다.
        
        Returns:
            원본 데이터 (CSV, JSON 등 운용사별 형식)
        """
        pass
    
    @abstractmethod
    async def parse_data(self, raw_data: Any) -> List[ETF]:
        """
        원본 데이터를 ETF 모델 리스트로 변환합니다.
        
        Args:
            raw_data: fetch_data()에서 가져온 원본 데이터
            
        Returns:
            ETF 모델 리스트
        """
        pass
    
    async def crawl(self) -> List[ETF]:
        """
        전체 크롤링 프로세스를 실행합니다.
        
        Returns:
            ETF 모델 리스트
        """
        raw_data = await self.fetch_data()
        parsed = self.parse_data(raw_data)
        if isawaitable(parsed):
            parsed = await parsed
        return parsed
    
    def get_provider_name(self) -> str:
        """운용사 이름을 반환합니다."""
        return self.provider_name
