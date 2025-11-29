"""Goldman Sachs ETF 크롤러 - GraphQL API 기반"""
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx
from app.models.etf import ETF, DistributionFrequency
from app.services.crawlers.base import BaseCrawler


class GoldmanSachsCrawler(BaseCrawler):
    """Goldman Sachs ETF 데이터 크롤러 (GraphQL API)"""
    
    BASE_URL = "https://am.gs.com/services/funds"
    
    # GraphQL 쿼리
    GRAPHQL_QUERY = """
    query getFunds($fundRequest: FundRequest) {
      fundData(fundRequest: $fundRequest) {
        funds {
          fundName
          fundType
          pvNumber
          shareClasses {
            shareClassId
            ticker
            shareClassInceptionDate
            baseCurrency
            distributionFrequency
            dailyPerformance {
              nav {
                asAtDate
                value
              }
              shareClassNetAssets {
                asAtDate
                value
              }
            }
            monthlyPerformance {
              asAtDate
              annualisedReturns1yr
              annualisedReturns3yr
              annualisedReturns5yr
              annualisedReturns10yr
              annualisedReturnsSinceIncept
            }
          }
        }
      }
    }
    """

    async def fetch_data(self) -> Dict[str, Any]:
        """Goldman Sachs GraphQL API에서 ETF 데이터 가져오기"""
        headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # GraphQL 요청 페이로드
        payload = {
            "operationName": "getFunds",
            "variables": {
                "fundRequest": {
                    "country": "us",
                    "language": "en",
                    "audience": "institutions",
                    "disabledFunds": [],
                    "limit": 500,  # 전체 펀드를 가져오기 위해 충분히 큰 값 설정
                    "offset": 0,
                    "sortBy": "FN",
                    "sortOrder": "ASC",
                    "filterParam": {
                        "searchText": ""
                    }
                }
            },
            "query": self.GRAPHQL_QUERY
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.BASE_URL, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def parse_data(self, raw_data: Dict[str, Any]) -> List[ETF]:
        """GraphQL 응답을 ETF 모델 리스트로 변환"""
        etf_list = []
        
        try:
            funds = raw_data.get("data", {}).get("fundData", {}).get("funds", [])
        except (KeyError, AttributeError):
            return etf_list
        
        for fund in funds:
            # ETF만 처리
            if fund.get("fundType") != "ETF":
                continue
            
            fund_name = fund.get("fundName", "")
            share_classes = fund.get("shareClasses", [])
            
            # 각 share class는 별도 ticker를 가질 수 있음
            for share_class in share_classes:
                try:
                    ticker = share_class.get("ticker")
                    if not ticker:
                        continue
                    
                    # Inception date 파싱
                    inception_date = self._parse_date(share_class.get("shareClassInceptionDate"))
                    
                    # NAV 정보
                    daily_perf = share_class.get("dailyPerformance", {})
                    nav_data = daily_perf.get("nav", {})
                    nav_amount = self._parse_decimal(nav_data.get("value"))
                    nav_as_of = self._parse_date(nav_data.get("asAtDate"))
                    
                    # AUM (shareClassNetAssets를 millions로 변환)
                    aum_data = daily_perf.get("shareClassNetAssets", {})
                    aum_value = aum_data.get("value")
                    aum_millions = None
                    if aum_value:
                        try:
                            aum_millions = float(aum_value) / 1_000_000  # millions로 변환
                        except (ValueError, TypeError):
                            pass
                    
                    # 수익률 정보
                    monthly_perf = share_class.get("monthlyPerformance", {})
                    ytd_return = self._parse_decimal(monthly_perf.get("annualisedReturns1yr"))
                    one_year = self._parse_decimal(monthly_perf.get("annualisedReturns1yr"))
                    three_year = self._parse_decimal(monthly_perf.get("annualisedReturns3yr"))
                    five_year = self._parse_decimal(monthly_perf.get("annualisedReturns5yr"))
                    ten_year = self._parse_decimal(monthly_perf.get("annualisedReturns10yr"))
                    since_incept = self._parse_decimal(monthly_perf.get("annualisedReturnsSinceIncept"))
                    
                    # Distribution frequency 매핑
                    dist_freq_str = share_class.get("distributionFrequency", "")
                    distribution_frequency = self._map_distribution_frequency(dist_freq_str)
                    
                    # 상세 페이지 URL 생성
                    detail_url = f"https://am.gs.com/en-us/institutions/products/{ticker}"
                    
                    etf = ETF(
                        ticker=ticker,
                        fund_name=fund_name,
                        isin=share_class.get("shareClassId", "N/A"),  # shareClassId를 ISIN 대신 사용
                        cusip="N/A",  # API에서 제공하지 않음
                        inception_date=inception_date or date.today(),
                        nav_amount=nav_amount or Decimal("0.00"),
                        nav_as_of=nav_as_of or date.today(),
                        expense_ratio=Decimal("0.00"),  # API 응답에 없음
                        ytd_return=ytd_return,
                        one_year_return=one_year,
                        three_year_return=three_year,
                        five_year_return=five_year,
                        ten_year_return=ten_year,
                        since_inception_return=since_incept,
                        asset_class="Unknown",  # 추가 매핑 필요
                        region="US",
                        market_type="ETF",
                        distribution_yield=None,
                        product_page_url=detail_url,
                        distribution_frequency=distribution_frequency,
                        detail_page_url=detail_url,
                    )
                    etf_list.append(etf)
                    
                except Exception as e:
                    # 개별 ETF 파싱 실패는 건너뛰기
                    continue
        
        return etf_list

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """날짜 문자열을 date 객체로 변환"""
        if not date_str:
            return None
        
        try:
            # ISO 8601 형식: "2022-02-15"
            return datetime.fromisoformat(date_str).date()
        except (ValueError, AttributeError):
            return None

    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """숫자 값을 Decimal로 변환"""
        if value is None:
            return None
        
        # 문자열 변환 및 검증
        str_value = str(value).strip()
        
        # '--', 'N/A', 빈 문자열 등은 None 반환
        if not str_value or str_value in ('--', 'N/A', 'n/a'):
            return None
        
        try:
            return Decimal(str_value)
        except (ValueError, TypeError, Exception):
            return None

    def _map_distribution_frequency(self, freq_str: str) -> DistributionFrequency:
        """배당 빈도 문자열을 DistributionFrequency enum으로 매핑"""
        if not freq_str:
            return DistributionFrequency.UNKNOWN
        
        freq_upper = freq_str.upper()
        
        if "MONTHLY" in freq_upper:
            return DistributionFrequency.MONTHLY
        elif "QUARTERLY" in freq_upper or "QUARTER" in freq_upper:
            return DistributionFrequency.QUARTERLY
        elif "SEMI" in freq_upper or "HALF" in freq_upper:
            return DistributionFrequency.SEMI_ANNUAL
        elif "ANNUAL" in freq_upper or "YEARLY" in freq_upper:
            return DistributionFrequency.ANNUAL
        elif "WEEKLY" in freq_upper or "WEEK" in freq_upper:
            return DistributionFrequency.WEEKLY
        elif "VARIABLE" in freq_upper or "VAR" in freq_upper:
            return DistributionFrequency.VARIABLE
        elif "NONE" in freq_upper or "NO" in freq_upper:
            return DistributionFrequency.NONE
        else:
            return DistributionFrequency.UNKNOWN
