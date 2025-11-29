"""iShares ETF 크롤러"""
import csv
import io
from datetime import datetime
from decimal import Decimal
from typing import Any, List

import httpx
from app.models.etf import ETF

from .base import BaseCrawler


class ISharesCrawler(BaseCrawler):
    """iShares ETF 데이터 크롤러"""
    
    # iShares product screener URL
    BASE_URL = "https://www.ishares.com/us/product-screener/product-screener-v3.1.jsn"
    PARAMS = {
        "dcrPath": "/templatedata/config/product-screener-v3/data/en/us-ishares/ishares-product-screener-backend-config",
        "siteEntryPassthrough": "true"
    }
    
    async def fetch_data(self) -> Any:
        """
        iShares API에서 JSON 데이터를 가져옵니다.
        
        Returns:
            JSON 응답 데이터
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.BASE_URL, params=self.PARAMS)
            response.raise_for_status()
            return response.json()
    
    async def parse_data(self, raw_data: Any) -> List[ETF]:
        """
        iShares JSON 데이터를 ETF 모델 리스트로 변환합니다.
        
        Args:
            raw_data: iShares API JSON 응답
            
        Returns:
            ETF 모델 리스트
        """
        etf_list = []
        
        # 날짜 파싱 함수
        def parse_date(date_obj):
            if not date_obj or not isinstance(date_obj, dict):
                return None
            date_str = date_obj.get("d")
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str, "%b %d, %Y").date()
            except:
                return None
        
        # Decimal 값 파싱 (r 키 값 사용)
        def parse_decimal(value_obj):
            if not value_obj or not isinstance(value_obj, dict):
                return None
            val = value_obj.get("r")
            if val is None:
                return None
            try:
                return Decimal(str(val))
            except:
                return None
        
        # raw_data는 portfolio ID를 키로 하는 딕셔너리
        # 예: {"239619": {...}, "239618": {...}, ...}
        if isinstance(raw_data, dict):
            for portfolio_id, etf_data in raw_data.items():
                try:
                    # 필수 필드 확인
                    if not all([
                        etf_data.get("localExchangeTicker"),
                        etf_data.get("fundName"),
                        etf_data.get("isin")
                    ]):
                        continue
                    
                    # portfolioId를 정수로 변환 (키가 문자열일 수 있음)
                    try:
                        portfolio_id_int = int(portfolio_id) if isinstance(portfolio_id, str) else portfolio_id
                    except:
                        portfolio_id_int = etf_data.get("portfolioId", 0)
                    
                    etf = ETF(
                        ticker=etf_data.get("localExchangeTicker", ""),
                        fund_name=etf_data.get("fundName", ""),
                        isin=etf_data.get("isin", ""),
                        cusip=etf_data.get("cusip", ""),
                        inception_date=parse_date(etf_data.get("inceptionDate")) or datetime.now().date(),
                        nav_amount=parse_decimal(etf_data.get("navAmount")) or Decimal("0"),
                        nav_as_of=parse_date(etf_data.get("navAmountAsOf")) or datetime.now().date(),
                        expense_ratio=parse_decimal(etf_data.get("fees")) or Decimal("0"),
                        
                        # Quarterly 데이터 우선 사용 (실제 데이터 구조에 맞춤)
                        ytd_return=parse_decimal(etf_data.get("quarterlyNavYearToDate")) or parse_decimal(etf_data.get("priceYearToDate")),
                        one_year_return=parse_decimal(etf_data.get("quarterlyNavOneYearAnnualized")) or parse_decimal(etf_data.get("priceOneYearAnnualized")),
                        three_year_return=parse_decimal(etf_data.get("quarterlyNavThreeYearAnnualized")) or parse_decimal(etf_data.get("priceThreeYearAnnualized")),
                        five_year_return=parse_decimal(etf_data.get("quarterlyNavFiveYearAnnualized")) or parse_decimal(etf_data.get("priceFiveYearAnnualized")),
                        ten_year_return=parse_decimal(etf_data.get("quarterlyNavTenYearAnnualized")) or parse_decimal(etf_data.get("priceTenYearAnnualized")),
                        since_inception_return=parse_decimal(etf_data.get("quarterlyNavSinceInceptionAnnualized")) or parse_decimal(etf_data.get("priceSinceInceptionAnnualized")),
                        
                        asset_class=etf_data.get("aladdinAssetClass", "Unknown"),
                        region=etf_data.get("aladdinRegion", "Unknown"),
                        market_type=etf_data.get("aladdinMarketType", "Unknown"),
                        distribution_yield=parse_decimal(etf_data.get("distributionYield")),
                        product_page_url=etf_data.get("productPageUrl", ""),
                        detail_page_url=etf_data.get("productPageUrl", "")
                    )
                    
                    etf_list.append(etf)
                except Exception as e:
                    # 개별 ETF 파싱 실패는 로깅하고 계속 진행
                    print(f"Failed to parse ETF {portfolio_id}: {e}")
                    continue
        
        return etf_list
