"""Alpha Architect ETF 크롤러"""

import re
from datetime import date
from decimal import Decimal
from typing import List

import httpx
from bs4 import BeautifulSoup

from ...models.etf import ETF
from .base import BaseCrawler


class AlphaArchitectCrawler(BaseCrawler):
    """Alpha Architect ETF 크롤러 클래스"""

    def __init__(self):
        super().__init__()
        self.provider_name = "Alpha Architect"
        self.url = "https://funds.alphaarchitect.com/"

    async def fetch_data(self) -> str:
        """Alpha Architect 웹사이트에서 HTML 데이터를 가져옵니다."""
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
        seen_tickers = set()

        # 모든 링크에서 티커 패턴 찾기
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if not isinstance(href, str):
                continue

            # /ticker 패턴 매칭 (예: /aaeq/, /qval, /ival 등)
            # funds는 ETF 티커가 아니므로 제외
            match = re.search(r'^/([a-z]{3,5})/?$', href, re.IGNORECASE)
            if match:
                ticker = match.group(1).upper()
                
                # 'FUNDS' 같은 일반 단어는 제외
                if ticker in ('FUNDS', 'HOME', 'ABOUT', 'NEWS', 'BLOG'):
                    continue

                # 중복 체크
                if ticker in seen_tickers:
                    continue
                seen_tickers.add(ticker)

                # 펀드명 추출
                text = link.get_text(strip=True)
                title = link.get("title", "")
                fund_name = str(text or title or ticker)

                # 전체 URL 생성
                full_url = f"https://funds.alphaarchitect.com{href}" if href.startswith('/') else href

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
                        region="US",
                        market_type="ETF",
                        distribution_yield=None,
                        product_page_url=full_url,
                        detail_page_url=full_url
                    )
                )

        return etf_list
