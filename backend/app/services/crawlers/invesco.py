"""Invesco ETF 크롤러"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx
from app.models.etf import ETF

from .base import BaseCrawler
from .yfinance_enricher import enrich_etf_with_yfinance

logger = logging.getLogger(__name__)


class InvescoCrawler(BaseCrawler):
    """Invesco ETF 데이터 크롤러"""
    
    # Invesco API URL
    BASE_URL = "https://dng-api.invesco.com/product/search"
    
    # API 파라미터
    PARAMS = {
        'facet': 'true',
        'facet.field': 'assetClass',
        'fq': [
            'countryCode:"US"',
            'language:"en_us"',
            'accountType:"ETF"',
            'contentType:"Product"',
            'shareClassStatus:"open"',
            'userRoles:"IndividualInvestor"',
            'assetClass:[* TO *]',
            'assetSubClass:[* TO *]'
        ],
        'q': '_suggest_:*',
        'fl': 'url,uniqueIdentifier,shareClassStatus,shareClassState,primaryShareClassIndicator,assetSubClass,assetClass,cusip,title,accountName,isin,youngFund,fundId,inceptionDate,ticker,title,totalExpenseRatio,factsheet,footnotes',
        'rows': '2000',
        'start': '0',
        'sort': 'shareClassFullName asc'
    }
    
    async def fetch_data(self) -> Any:
        """
        Invesco API에서 JSON 데이터를 가져옵니다.
        
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
            num_found = data.get('response', {}).get('numFound', 0)
            logger.info(f"Fetched {num_found} Invesco ETFs")
            return data
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """
        날짜 문자열을 date 객체로 변환합니다.
        
        Args:
            date_str: ISO 형식 날짜 문자열 (예: "2017-09-22")
            
        Returns:
            date 객체 또는 None
        """
        if not date_str:
            return None
        
        try:
            # ISO 형식 (YYYY-MM-DD)
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, AttributeError):
            logger.warning(f"Failed to parse date: {date_str}")
            return None
    
    def _extract_etf_data(self, doc: Dict) -> Optional[ETF]:
        """
        API 응답의 문서 객체에서 ETF 데이터를 추출합니다.
        
        Args:
            doc: API 응답의 개별 문서
            
        Returns:
            ETF 모델 또는 None
        """
        ticker = doc.get('ticker', '').strip()
        if not ticker:
            return None
        
        # 기본 정보
        fund_name = doc.get('accountName', doc.get('title', ''))
        isin = doc.get('isin', 'N/A')
        cusip = doc.get('cusip', 'N/A')
        
        # 날짜 정보
        inception_date = self._parse_date(doc.get('inceptionDate'))
        
        # 비용 정보
        expense_ratio_str = doc.get('totalExpenseRatio', '0.00')
        try:
            expense_ratio = Decimal(expense_ratio_str)
        except (ValueError, TypeError, Exception):
            logger.warning(f"Invalid expense ratio for {ticker}: {expense_ratio_str}")
            expense_ratio = Decimal("0.00")
        
        # 자산 분류
        asset_class = doc.get('assetClass', 'Unknown')
        asset_sub_class = doc.get('assetSubClass', 'Unknown')
        
        # 지역 추정 (Invesco는 주로 미국 기반)
        region = "North America"
        market_type = "Developed"
        
        # URL
        url_path = doc.get('url', '')
        product_page_url = f"https://www.invesco.com{url_path}" if url_path else f"https://www.invesco.com/us/en/financial-products/etfs/{ticker.lower()}"
        
        # yfinance로 NAV 및 기타 데이터 보강
        nav_amount = Decimal("0.00")
        nav_amount, expense_ratio, inception_date = enrich_etf_with_yfinance(
            ticker, nav_amount, expense_ratio, inception_date
        )
        
        try:
            return ETF(
                ticker=ticker,
                fund_name=fund_name,
                isin=isin,
                cusip=cusip,
                inception_date=inception_date,
                nav_amount=nav_amount,
                nav_as_of=datetime.now().date(),
                expense_ratio=expense_ratio,
                ytd_return=None,  # API에서 제공하지 않음
                one_year_return=None,
                three_year_return=None,
                five_year_return=None,
                ten_year_return=None,
                since_inception_return=None,
                asset_class=asset_class,
                region=region,
                market_type=market_type,
                distribution_yield=None,  # API에서 제공하지 않음
                product_page_url=product_page_url,
                detail_page_url=product_page_url
            )
        except Exception as e:
            logger.error(f"Failed to create ETF object for {ticker}: {e}")
            return None
    
    async def parse_data(self, raw_data: Any) -> List[ETF]:
        """
        Invesco JSON 데이터를 ETF 모델 리스트로 변환합니다.
        
        Args:
            raw_data: Invesco API JSON 응답
            
        Returns:
            ETF 모델 리스트
        """
        etf_list = []
        
        try:
            docs = raw_data.get('response', {}).get('docs', [])
            
            logger.info(f"Processing {len(docs)} Invesco ETFs")
            
            for doc in docs:
                etf = self._extract_etf_data(doc)
                if etf:
                    etf_list.append(etf)
                    logger.info(f"Successfully parsed {etf.ticker}")
            
            logger.info(f"Successfully parsed {len(etf_list)} Invesco ETFs")
            
        except Exception as e:
            logger.error(f"Failed to parse Invesco data: {e}")
        
        return etf_list
