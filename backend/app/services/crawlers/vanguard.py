"""Vanguard ETF 크롤러"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx
from app.models.etf import ETF

from .base import BaseCrawler

logger = logging.getLogger(__name__)


class VanguardCrawler(BaseCrawler):
    """Vanguard ETF 데이터 크롤러"""
    
    # Vanguard JSON API URL
    BASE_URL = "https://investor.vanguard.com/investment-products/list/funddetail/all"
    
    async def fetch_data(self) -> Any:
        """
        Vanguard API에서 JSON 데이터를 가져옵니다.
        
        Returns:
            JSON 응답 데이터
        """
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        ) as client:
            response = await client.get(self.BASE_URL)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Fetched {data.get('size', 0)} Vanguard funds")
            return data
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """
        날짜 문자열을 date 객체로 변환합니다.
        
        Args:
            date_str: ISO 형식 날짜 문자열 (예: "2025-02-07T00:00:00-05:00")
            
        Returns:
            date 객체 또는 None
        """
        if not date_str:
            return None
        
        try:
            # ISO 형식 파싱
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.date()
        except (ValueError, AttributeError):
            logger.warning(f"Failed to parse date: {date_str}")
            return None
    
    def _extract_etf_data(self, entity: Dict) -> Optional[ETF]:
        """
        API 응답의 entity 객체에서 ETF 데이터를 추출합니다.
        
        Args:
            entity: API 응답의 개별 펀드 엔티티
            
        Returns:
            ETF 모델 또는 None
        """
        profile = entity.get('profile', {})
        
        # ETF가 아닌 경우 스킵
        if not profile.get('isETF'):
            return None
        
        try:
            ticker = profile.get('ticker', '').strip()
            if not ticker:
                return None
            
            # 기본 정보
            fund_name = profile.get('longName', profile.get('shortName', ''))
            cusip = profile.get('cusip', 'N/A')
            
            # 날짜 정보
            inception_date = self._parse_date(profile.get('inceptionDate'))
            
            # 가격 정보
            daily_price = entity.get('dailyPrice', {}).get('regular', {})
            nav_amount = Decimal(daily_price.get('price', '0.00'))
            nav_as_of = self._parse_date(daily_price.get('asOfDate'))
            
            # 비용 정보
            expense_ratio = Decimal(profile.get('expenseRatio', '0.00'))
            
            # 수익률 정보
            month_end_return = entity.get('monthEndAvgAnnualRtn', {})
            fund_return = month_end_return.get('fundReturn', {})
            
            ytd_return = None
            one_year_return = Decimal(fund_return.get('oneYearPct', '0')) if fund_return.get('oneYearPct') else None
            three_year_return = Decimal(fund_return.get('threeYearPct', '0')) if fund_return.get('threeYearPct') else None
            five_year_return = Decimal(fund_return.get('fiveYearPct', '0')) if fund_return.get('fiveYearPct') else None
            ten_year_return = Decimal(fund_return.get('tenYearPct', '0')) if fund_return.get('tenYearPct') else None
            since_inception_return = Decimal(fund_return.get('sinceInceptionPct', '0')) if fund_return.get('sinceInceptionPct') else None
            
            # 자산 분류
            asset_class = profile.get('style', 'Unknown')
            region = "North America"  # Vanguard는 주로 미국 기반
            market_type = "Developed"
            
            # 배당 수익률
            yield_data = entity.get('yield', {})
            distribution_yield = Decimal(yield_data.get('yieldPct', '0')) if yield_data.get('yieldPct') else None
            
            # URL
            product_page_url = f"https://investor.vanguard.com/investment-products/etfs/profile/{ticker.lower()}"
            
            return ETF(
                ticker=ticker,
                fund_name=fund_name,
                isin="N/A",  # API에서 제공하지 않음
                cusip=cusip,
                inception_date=inception_date,
                nav_amount=nav_amount,
                nav_as_of=nav_as_of or datetime.now().date(),
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
            logger.error(f"Failed to extract ETF data: {e}")
            return None
    
    async def parse_data(self, raw_data: Any) -> List[ETF]:
        """
        Vanguard JSON 데이터를 ETF 모델 리스트로 변환합니다.
        
        Args:
            raw_data: Vanguard API JSON 응답
            
        Returns:
            ETF 모델 리스트
        """
        etf_list = []
        
        try:
            entities = raw_data.get('fund', {}).get('entity', [])
            
            for entity in entities:
                etf = self._extract_etf_data(entity)
                if etf:
                    etf_list.append(etf)
                    logger.info(f"Successfully parsed {etf.ticker}")
            
            logger.info(f"Successfully parsed {len(etf_list)} Vanguard ETFs")
            
        except Exception as e:
            logger.error(f"Failed to parse Vanguard data: {e}")
        
        return etf_list
