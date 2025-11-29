"""GraniteShares ETF 크롤러"""

import re
from datetime import date
from decimal import Decimal
from typing import List

import httpx
from bs4 import BeautifulSoup

from ...models.etf import ETF
from .base import BaseCrawler


class GraniteSharesCrawler(BaseCrawler):
    """GraniteShares ETF 크롤러 클래스"""

    def __init__(self):
        super().__init__()
        self.provider_name = "GraniteShares"
        self.url = "https://graniteshares.com/institutional/us/en-us/etfs/"

    async def fetch_data(self) -> str:
        """GraniteShares 웹사이트에서 HTML 데이터를 가져옵니다."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(self.url, headers=headers)
            response.raise_for_status()
            return response.text

    def parse_data(self, html: str) -> List[ETF]:
        """HTML에서 ETF 티커를 추출합니다."""
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        etf_list = []

        # 모든 링크에서 /etf/ 패턴을 찾아 티커 추출
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if not isinstance(href, str):
                continue

            # /etf/ticker 패턴 매칭
            match = re.search(r"/etf/([A-Z]{1,5})/?", href, re.IGNORECASE)
            if match:
                ticker = match.group(1).upper()

                # 중복 체크
                if any(etf.ticker == ticker for etf in etf_list):
                    continue

                # 펀드명 추출 (링크 텍스트 또는 title 속성)
                text = link.get_text(strip=True)
                title = link.get("title", "")
                fund_name = str(text or title or ticker)

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
                        product_page_url=href,
                        detail_page_url=href
                    )
                )

        return etf_list
