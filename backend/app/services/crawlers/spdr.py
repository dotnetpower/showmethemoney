"""SPDR ETF 크롤러"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx
from app.models.etf import ETF

from .base import BaseCrawler

logger = logging.getLogger(__name__)


class SPDRCrawler(BaseCrawler):
    """SPDR ETF 데이터 크롤러"""
    
    # SPDR JSON API URL
    BASE_URL = "https://www.ssga.com/bin/v1/ssmp/fund/fundfinder"
    PARAMS = {
        "country": "us",
        "language": "en",
        "role": "intermediary",
        "product": "",
        "ui": "fund-finder"
    }
    
    async def fetch_data(self) -> Any:
        """
        SPDR API에서 JSON 데이터를 가져옵니다.
        
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
            response = await client.get(self.BASE_URL, params=self.PARAMS)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Fetched SPDR fund data")
            return data
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """
        날짜 문자열을 date 객체로 변환합니다.
        
        Args:
            date_str: 날짜 문자열 (예: "2011-02-23" 또는 "Feb 23 2011")
            
        Returns:
            date 객체 또는 None
        """
        if not date_str:
            return None
        
        try:
            # ISO 형식 (YYYY-MM-DD)
            if '-' in date_str and len(date_str) == 10:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            # "Feb 23 2011" 형식
            return datetime.strptime(date_str, '%b %d %Y').date()
        except (ValueError, AttributeError):
            logger.warning(f"Failed to parse date: {date_str}")
            return None
    
    def _extract_value(self, field: Any) -> Optional[Decimal]:
        """
        필드에서 숫자 값을 추출합니다.
        SPDR API는 ["$21.27", 21.27] 형식으로 데이터를 제공합니다.
        
        Args:
            field: 필드 값 (리스트 또는 단일 값)
            
        Returns:
            Decimal 값 또는 None
        """
        if field is None:
            return None
        
        try:
            # 리스트 형식인 경우 두 번째 값 (숫자) 사용
            if isinstance(field, list) and len(field) > 1:
                return Decimal(str(field[1]))
            # 단일 값인 경우
            elif isinstance(field, (int, float, str)):
                return Decimal(str(field))
        except (ValueError, TypeError, IndexError):
            logger.warning(f"Failed to extract value from: {field}")
        
        return None
    
    def _extract_etf_data(self, fund_data: Dict) -> Optional[ETF]:
        """
        API 응답의 펀드 객체에서 ETF 데이터를 추출합니다.
        
        Args:
            fund_data: API 응답의 개별 펀드 데이터
            
        Returns:
            ETF 모델 또는 None
        """
        try:
            ticker = fund_data.get('fundTicker', '').strip()
            if not ticker:
                return None
            
            # 기본 정보
            fund_name = fund_data.get('fundName', '')
            
            # 날짜 정보
            inception_date_raw = fund_data.get('inceptionDate', [])
            inception_date_str = inception_date_raw[1] if isinstance(inception_date_raw, list) and len(inception_date_raw) > 1 else None
            inception_date = self._parse_date(inception_date_str)
            
            # 가격 정보
            nav_amount = self._extract_value(fund_data.get('nav')) or Decimal("0.00")
            
            # NAV 기준일
            as_of_date_raw = fund_data.get('asOfDate', [])
            as_of_date_str = as_of_date_raw[1] if isinstance(as_of_date_raw, list) and len(as_of_date_raw) > 1 else None
            nav_as_of = self._parse_date(as_of_date_str) or datetime.now().date()
            
            # 비용 정보 (TER = Total Expense Ratio)
            expense_ratio = self._extract_value(fund_data.get('ter')) or Decimal("0.00")
            
            # 수익률 정보 (월말 기준)
            ytd_return = self._extract_value(fund_data.get('ytd'))
            one_year_return = self._extract_value(fund_data.get('yr1'))
            three_year_return = self._extract_value(fund_data.get('yr3'))
            five_year_return = self._extract_value(fund_data.get('yr5'))
            ten_year_return = self._extract_value(fund_data.get('yr10'))
            since_inception_return = self._extract_value(fund_data.get('sinceInception'))
            
            # 자산 분류 (SPDR는 상세 분류 정보 제한적)
            asset_class = "Unknown"
            region = "Unknown"
            market_type = "Developed"
            
            # domicile로 지역 추정
            domicile = fund_data.get('domicile', '')
            if domicile == 'US':
                region = "North America"
            
            # URL
            fund_uri = fund_data.get('fundUri', '')
            product_page_url = f"https://www.ssga.com{fund_uri}" if fund_uri else f"https://www.ssga.com/us/en/intermediary/etfs/{ticker.lower()}"
            
            return ETF(
                ticker=ticker,
                fund_name=fund_name,
                isin="N/A",  # API에서 제공하지 않음
                cusip="N/A",  # API에서 제공하지 않음
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
                distribution_yield=None,  # API에서 제공하지 않음
                product_page_url=product_page_url,
                detail_page_url=product_page_url
            )
            
        except Exception as e:
            logger.error(f"Failed to extract ETF data: {e}")
            return None
    
    async def parse_data(self, raw_data: Any) -> List[ETF]:
        """
        SPDR JSON 데이터를 ETF 모델 리스트로 변환합니다.
        
        Args:
            raw_data: SPDR API JSON 응답
            
        Returns:
            ETF 모델 리스트
        """
        etf_list = []
        
        try:
            # ETF 데이터 추출
            funds_data = raw_data.get('data', {}).get('funds', {}).get('etfs', {})
            etf_data_list = funds_data.get('datas', [])
            
            logger.info(f"Found {len(etf_data_list)} SPDR ETFs")
            
            for fund_data in etf_data_list:
                etf = self._extract_etf_data(fund_data)
                if etf:
                    etf_list.append(etf)
                    logger.info(f"Successfully parsed {etf.ticker}")
            
            logger.info(f"Successfully parsed {len(etf_list)} SPDR ETFs")
            
        except Exception as e:
            logger.error(f"Failed to parse SPDR data: {e}")
        
        return etf_list
