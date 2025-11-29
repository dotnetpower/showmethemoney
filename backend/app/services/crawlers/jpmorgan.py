"""JPMorgan ETF 크롤러"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx
from app.models.etf import ETF
from app.services.crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)


class JPMorganCrawler(BaseCrawler):
    """JPMorgan ETF 데이터를 크롤링하는 클래스"""
    
    BASE_URL = "https://am.jpmorgan.com/FundsMarketingHandler/fund-explorer"
    
    # API 파라미터
    PARAMS = {
        "country": "us",
        "role": "adv",
        "userLoggedIn": "false",
        "language": "en",
        "fundType": "etf",
        "version": "8.22.1_1763825820"
    }
    
    def get_provider_name(self) -> str:
        """공급자 이름 반환"""
        return "JPMorgan"
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """
        날짜 문자열을 date 객체로 변환합니다.
        
        Args:
            date_str: ISO 형식 날짜 문자열 (YYYY-MM-DD)
            
        Returns:
            date 객체 또는 None
        """
        if not date_str:
            return None
        
        try:
            # ISO 형식: "2020-05-20"
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse date: {date_str} - {e}")
            return None
    
    def _extract_return_value(self, performance_data: Optional[Dict], key: str) -> Optional[Decimal]:
        """
        성과 데이터에서 수익률 값을 추출합니다.
        
        Args:
            performance_data: 성과 데이터 딕셔너리
            key: 추출할 키 (예: 'ytd', 'yr1', 'yr3')
            
        Returns:
            Decimal 수익률 또는 None
        """
        if not performance_data:
            return None
        
        value = performance_data.get(key)
        if value is None:
            return None
        
        try:
            # 소수로 표현된 수익률을 백분율로 변환 후 반올림 (0.0528 -> 5.28)
            return Decimal(str(round(value * 100, 2)))
        except (ValueError, TypeError):
            return None
    
    def _extract_etf_data(self, fund: Dict) -> Optional[ETF]:
        """
        API 응답의 펀드 객체에서 ETF 데이터를 추출합니다.
        
        Args:
            fund: API 응답의 개별 펀드 데이터
            
        Returns:
            ETF 모델 또는 None
        """
        ticker = fund.get('ticker', '').strip()
        if not ticker:
            return None
        
        # 기본 정보
        fund_name = fund.get('name', '')
        
        # identifier는 CUSIP 형식
        cusip = fund.get('identifier', 'N/A')
        isin = 'N/A'  # API에서 ISIN 제공 안 함
        
        # 날짜 정보
        inception_date = self._parse_date(fund.get('fundInceptionDate'))
        
        # NAV 정보
        nav = fund.get('nav')
        try:
            nav_amount = Decimal(str(nav)) if nav is not None else Decimal("0.00")
        except (ValueError, TypeError, Exception):
            logger.warning(f"Invalid NAV for {ticker}: {nav}")
            nav_amount = Decimal("0.00")
        
        # NAV 날짜
        nav_date_str = fund.get('navDate')
        if nav_date_str:
            nav_as_of = self._parse_date(nav_date_str)
            if nav_as_of is None:
                nav_as_of = datetime.now().date()
        else:
            nav_as_of = datetime.now().date()
        
        # Expense ratio는 API에서 직접 제공하지 않음
        # SEC yield를 대신 사용하거나 0으로 설정
        sec_yield = fund.get('secYield')
        try:
            expense_ratio = Decimal(str(sec_yield * 100)) if sec_yield is not None else Decimal("0.00")
        except (ValueError, TypeError):
            expense_ratio = Decimal("0.00")
        
        # 성과 데이터 (atNavPerformanceReturn 사용)
        performance = fund.get('atNavPerformanceReturn', {})
        ytd_return = self._extract_return_value(performance, 'ytd')
        one_year_return = self._extract_return_value(performance, 'yr1')
        three_year_return = self._extract_return_value(performance, 'yr3')
        five_year_return = self._extract_return_value(performance, 'yr5')
        ten_year_return = self._extract_return_value(performance, 'yr10')
        since_inception_return = self._extract_return_value(performance, 'inception')
        
        # 자산 분류
        asset_class = fund.get('assetClass', 'Unknown')
        
        # 지역 추정 (JPMorgan은 글로벌)
        region = "North America"
        market_type = "Developed"
        
        # Distribution yield (secYield 사용)
        distribution_yield = None
        if sec_yield is not None:
            try:
                distribution_yield = Decimal(str(sec_yield * 100))
            except (ValueError, TypeError):
                pass
        
        # URL
        display_id = fund.get('displayId', ticker.lower())
        product_page_url = f"https://am.jpmorgan.com/us/en/asset-management/adv/products/etfs/{display_id}"
        
        try:
            return ETF(
                ticker=ticker,
                fund_name=fund_name,
                isin=isin,
                cusip=cusip,
                inception_date=inception_date,
                nav_amount=nav_amount,
                nav_as_of=nav_as_of,
                expense_ratio=expense_ratio,
                ytd_return=ytd_return,
                one_year_return=one_year_return,
                three_year_return=three_year_return,
                five_year_return=five_year_return,
                ten_year_return=ten_year_return,
                since_inception_return=since_inception_return,
                asset_class=asset_class,
                region=region,
                market_type=market_type,
                distribution_yield=distribution_yield,
                product_page_url=product_page_url,
                detail_page_url=product_page_url
            )
        except Exception as e:
            logger.error(f"Failed to create ETF object for {ticker}: {e}")
            return None
    
    async def fetch_data(self) -> Any:
        """
        JPMorgan API에서 ETF 데이터를 가져옵니다.
        
        Returns:
            API 응답 데이터 (리스트)
        """
        logger.info(f"Fetching data from {self.BASE_URL}")
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(self.BASE_URL, params=self.PARAMS)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Fetched {len(data) if isinstance(data, list) else 'unknown'} ETFs from JPMorgan")
            return data
    
    async def parse_data(self, raw_data: Any) -> List[ETF]:
        """
        JPMorgan JSON 데이터를 ETF 모델 리스트로 변환합니다.
        
        Args:
            raw_data: API에서 받은 원시 데이터 (리스트)
            
        Returns:
            ETF 모델 리스트
        """
        if not isinstance(raw_data, list):
            logger.warning(f"Expected list but got {type(raw_data)}")
            return []
        
        etf_list = []
        for fund in raw_data:
            etf = self._extract_etf_data(fund)
            if etf:
                etf_list.append(etf)
        
        logger.info(f"Successfully parsed {len(etf_list)} ETFs from JPMorgan")
        return etf_list
