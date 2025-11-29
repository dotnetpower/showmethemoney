"""Direxion ETF crawler"""
import logging
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

import httpx
from app.models.etf import ETF, DistributionFrequency
from bs4 import BeautifulSoup

from .base import BaseCrawler

logger = logging.getLogger(__name__)


class DirexionCrawler(BaseCrawler):
    """Crawler for Direxion ETFs"""

    def __init__(self):
        super().__init__()
        self.base_url = "https://www.direxion.com"
        self.etf_list_url = f"{self.base_url}/all-etfs"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def fetch_data(self) -> Optional[str]:
        """Fetch HTML page containing ETF data"""
        try:
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=30.0, headers=self.headers
            ) as client:
                response = await client.get(self.etf_list_url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Failed to fetch Direxion ETF data: {e}")
            return None

    def parse_data(self, html_content: str) -> List[ETF]:
        """Parse HTML content to extract ETF data"""
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        etfs = []

        # Look for ETF links
        etf_links = soup.find_all("a", href=re.compile(r'/product/[a-z]+', re.IGNORECASE))

        for link in etf_links:
            href = link.get("href")
            if not href or not isinstance(href, str):
                continue

            ticker_match = re.search(r'/product/([a-z]+)', href, re.IGNORECASE)
            if ticker_match:
                ticker = ticker_match.group(1).upper()
                name = link.get_text(strip=True)

                if ticker and name and len(ticker) <= 5:
                    detail_url = href if href.startswith("http") else self.base_url + href
                    
                    try:
                        etf = ETF(
                            ticker=ticker,
                            fund_name=name,
                            isin="N/A",
                            cusip="N/A",
                            inception_date=datetime.now().date(),
                            nav_amount=Decimal("0.00"),
                            nav_as_of=datetime.now().date(),
                            expense_ratio=Decimal("0.00"),
                            asset_class="Unknown",
                            region="US",
                            market_type="ETF",
                            product_page_url=detail_url,
                            detail_page_url=detail_url,
                        )
                        etfs.append(etf)
                    except Exception as e:
                        logger.warning(f"Failed to create ETF {ticker}: {e}")
                        continue

        logger.info(f"Parsed {len(etfs)} ETFs from Direxion")
        return etfs
