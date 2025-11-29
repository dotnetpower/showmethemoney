"""Dimensional Fund Advisors ETF 크롤러"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx
from app.models.etf import ETF
from app.services.crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)


class DimensionalCrawler(BaseCrawler):
    """Dimensional Fund Advisors ETF 데이터를 크롤링하는 클래스"""
    
    BASE_URL = "https://etf.dimensional.com/public/v2/fundcenter"
    
    # API 파라미터
    PARAMS = {
        "allowMorningstarFixedIncome": "true"
    }
    
    # 필수 헤더
    HEADERS = {
        "X-Selected-Country": "US"
    }
    
    def get_provider_name(self) -> str:
        """공급자 이름 반환"""
        return "Dimensional Fund Advisors"
    
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
            # ISO 형식: "2023-09-12"
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse date: {date_str} - {e}")
            return None
    
    def _extract_identifier(self, identifiers: List[Dict], slug: str) -> str:
        """
        identifiers 리스트에서 특정 slug의 값을 추출합니다.
        
        Args:
            identifiers: identifier 딕셔너리 리스트
            slug: 추출할 identifier의 slug
            
        Returns:
            identifier 값 또는 'N/A'
        """
        for identifier in identifiers:
            if identifier.get('slug') == slug:
                return identifier.get('value', 'N/A')
        return 'N/A'
    
    def _extract_return_value(self, returns_data: Optional[Dict], key: str) -> Optional[Decimal]:
        """
        수익률 데이터에서 값을 추출합니다.
        
        Args:
            returns_data: 수익률 데이터 딕셔너리
            key: 추출할 키
            
        Returns:
            Decimal 수익률 또는 None
        """
        if not returns_data:
            return None
        
        value_obj = returns_data.get(key)
        if not value_obj:
            return None
        
        value = value_obj.get('value')
        if value is None:
            return None
        
        try:
            # 소수로 표현된 수익률을 백분율로 변환 (0.1723 -> 17.23)
            return Decimal(str(round(value * 100, 2)))
        except (ValueError, TypeError):
            return None
    
    def _extract_fee_value(self, fees: List[Dict], slug: str) -> Decimal:
        """
        fees 리스트에서 특정 slug의 값을 추출합니다.
        
        Args:
            fees: fee 딕셔너리 리스트
            slug: 추출할 fee의 slug
            
        Returns:
            Decimal 수수료 값 (백분율)
        """
        for fee in fees:
            if fee.get('slug') == slug:
                value_obj = fee.get('value', {})
                value = value_obj.get('value')
                if value is not None:
                    try:
                        # 소수를 백분율로 변환 (0.0014 -> 0.14)
                        return Decimal(str(round(value * 100, 2)))
                    except (ValueError, TypeError):
                        pass
        return Decimal("0.00")
    
    def _extract_etf_data(self, portfolio: Dict) -> Optional[ETF]:
        """
        API 응답의 포트폴리오 객체에서 ETF 데이터를 추출합니다.
        
        Args:
            portfolio: API 응답의 개별 포트폴리오 데이터
            
        Returns:
            ETF 모델 또는 None
        """
        meta = portfolio.get('meta', {})
        
        # ETF만 처리
        if not meta.get('isEtf', False):
            return None
        
        # 기본 정보
        identifiers = meta.get('identifiers', [])
        ticker = self._extract_identifier(identifiers, 'ticker')
        
        if not ticker or ticker == 'N/A':
            return None
        
        fund_name = f"Dimensional {meta.get('marketingName', '')}"
        isin = self._extract_identifier(identifiers, 'isin')
        cusip = self._extract_identifier(identifiers, 'cusip')
        
        # 날짜 정보
        inception_date_obj = meta.get('inceptionDate', {})
        inception_date = self._parse_date(inception_date_obj.get('value'))
        
        # NAV 정보
        prices = portfolio.get('prices', [])
        nav_amount = Decimal("0.00")
        nav_as_of = datetime.now().date()
        
        if prices and len(prices) > 0:
            latest_price = prices[0]
            nav_obj = latest_price.get('nav', {})
            nav_value = nav_obj.get('value')
            
            if nav_value is not None:
                try:
                    nav_amount = Decimal(str(nav_value))
                except (ValueError, TypeError):
                    nav_amount = Decimal("0.00")
            
            price_date_obj = latest_price.get('date', {})
            price_date = self._parse_date(price_date_obj.get('value'))
            if price_date:
                nav_as_of = price_date
        
        # Expense ratio (net expense ratio 사용)
        fees = portfolio.get('fees', [])
        expense_ratio = self._extract_fee_value(fees, 'net-exp-ratio')
        
        # 수익률 데이터 (returnsMonthly 사용)
        returns_monthly = portfolio.get('returnsMonthly', [])
        ytd_return = None
        one_year_return = None
        three_year_return = None
        five_year_return = None
        ten_year_return = None
        since_inception_return = None
        
        if returns_monthly and len(returns_monthly) > 0:
            latest_returns = returns_monthly[0]
            one_year_return = self._extract_return_value(latest_returns, 'annualizedReturn1Year')
            three_year_return = self._extract_return_value(latest_returns, 'annualizedReturn3Year')
            five_year_return = self._extract_return_value(latest_returns, 'annualizedReturn5Year')
            ten_year_return = self._extract_return_value(latest_returns, 'annualizedReturn10Year')
            since_inception_return = self._extract_return_value(latest_returns, 'annualizedReturnSincePortfolioInception')
        
        # YTD는 returnsDaily에서 추출
        returns_daily = portfolio.get('returnsDaily', [])
        if returns_daily and len(returns_daily) > 0:
            latest_daily = returns_daily[0]
            ytd_return = self._extract_return_value(latest_daily, 'annualizedReturnYtd')
        
        # 자산 분류
        category = meta.get('category', 'Unknown')
        asset_class = category
        
        # 지역 추정
        region = "North America"
        market_type = "Developed"
        
        # URL
        portfolio_number = portfolio.get('portfolioNumber')
        product_page_url = f"https://etf.dimensional.com/us/en/funds/{ticker.lower()}" if ticker else "https://etf.dimensional.com"
        
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
                distribution_yield=None,  # API에서 제공 안 함
                product_page_url=product_page_url,
                detail_page_url=product_page_url
            )
        except Exception as e:
            logger.error(f"Failed to create ETF object for {ticker}: {e}")
            return None
    
    async def fetch_data(self) -> Any:
        """
        Dimensional API에서 ETF 데이터를 가져옵니다.
        
        Returns:
            API 응답 데이터
        """
        logger.info(f"Fetching data from {self.BASE_URL}")
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(
                self.BASE_URL, 
                params=self.PARAMS,
                headers=self.HEADERS
            )
            response.raise_for_status()
            data = response.json()
            
            portfolios = data.get('data', {}).get('portfolios', [])
            logger.info(f"Fetched {len(portfolios)} portfolios from Dimensional")
            return data
    
    async def parse_data(self, raw_data: Any) -> List[ETF]:
        """
        Dimensional JSON 데이터를 ETF 모델 리스트로 변환합니다.
        
        Args:
            raw_data: API에서 받은 원시 데이터
            
        Returns:
            ETF 모델 리스트
        """
        if not isinstance(raw_data, dict):
            logger.warning(f"Expected dict but got {type(raw_data)}")
            return []
        
        portfolios = raw_data.get('data', {}).get('portfolios', [])
        
        etf_list = []
        for portfolio in portfolios:
            etf = self._extract_etf_data(portfolio)
            if etf:
                etf_list.append(etf)
        
        logger.info(f"Successfully parsed {len(etf_list)} ETFs from Dimensional")
        return etf_list
