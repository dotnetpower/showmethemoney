"""Franklin Templeton ETF 크롤러"""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import List

import httpx

from ...models.etf import ETF
from .base import BaseCrawler


class FranklinTempletonCrawler(BaseCrawler):
    """Franklin Templeton ETF 크롤러 클래스"""

    def __init__(self):
        super().__init__()
        self.provider_name = "Franklin Templeton"

    async def fetch_data(self) -> dict:
        """Franklin Templeton GraphQL API에서 ETF 데이터를 가져옵니다."""
        url = "https://www.franklintempleton.com/api/pds/price-and-performance?op=UsPpss&pt=etf&id=1"

        # GraphQL query
        graphql_query = {
            "query": """
  query UsPpss(
    $countrycode: String!
    $languagecode: String!
    $productType: String!
  ) {
    PPSS(
      countrycode: $countrycode
      languagecode: $languagecode
      productType: $productType
    ) {
      fundid
      fundname
      shareclass {
        identifiers {
          ticker
        }
      }
    }
  }
""",
            "variables": {
                "countrycode": "US",
                "productType": "etf",
                "languagecode": "en_US",
                "fetchPolicy": "no-cache",
            },
            "operationName": "UsPpss",
        }

        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "origin": "https://www.franklintempleton.com",
            "referer": "https://www.franklintempleton.com/investments/options/exchange-traded-funds",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.post(url, json=graphql_query, headers=headers)
            response.raise_for_status()
            return response.json()

    def parse_data(self, data: dict) -> List[ETF]:
        """GraphQL 응답 데이터를 ETF 객체 리스트로 변환합니다."""
        if not data:
            return []

        etf_list = []

        # GraphQL 응답에서 PPSS 데이터 추출
        ppss_data = data.get("data", {}).get("PPSS", [])

        if not ppss_data:
            return []

        for fund in ppss_data:
            try:
                fund_name = fund.get("fundname", "").strip()
                if not fund_name:
                    continue

                # shareclass 배열에서 ticker 추출
                shareclass_list = fund.get("shareclass", [])
                if not shareclass_list or not isinstance(shareclass_list, list):
                    continue

                for shareclass in shareclass_list:
                    identifiers = shareclass.get("identifiers", {})
                    if not identifiers:
                        continue

                    ticker = identifiers.get("ticker", "").strip()
                    if not ticker:
                        continue

                    # 티커가 유효한지 확인 (알파벳만 포함, 1-5자)
                    if not re.match(r"^[A-Z]{1,5}$", ticker):
                        continue

                    etf_list.append(
                        ETF(
                            ticker=ticker,
                            fund_name=fund_name,
                            isin="",
                            cusip="",
                            inception_date=None,
                            nav_amount=Decimal("0"),
                            nav_as_of=date.today(),
                            expense_ratio=Decimal("0"),
                            ytd_return=None,
                            one_year_return=None,
                            three_year_return=None,
                            five_year_return=None,
                            ten_year_return=None,
                            since_inception_return=None,
                            asset_class="",
                            region="",
                            market_type="",
                            distribution_yield=None,
                            product_page_url="",
                            detail_page_url=None
                        )
                    )

            except (ValueError, KeyError, AttributeError):
                continue

        return etf_list
