"""Global X ETF crawler"""
import logging
import re
from datetime import date
from decimal import Decimal
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

from .base import BaseCrawler

logger = logging.getLogger(__name__)


class GlobalXCrawler(BaseCrawler):
    """Crawler for Global X ETFs"""

    def __init__(self):
        super().__init__()
        self.base_url = "https://www.globalxetfs.com"
        self.explore_url = f"{self.base_url}/explore"

    async def fetch_data(self) -> Optional[str]:
        """Fetch HTML page containing ETF data"""
        try:
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=30.0
            ) as client:
                response = await client.get(self.explore_url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Failed to fetch Global X ETF data: {e}")
            return None

    def parse_data(self, html_content: str) -> list[dict[str, Any]]:
        """Parse HTML content to extract ETF data"""
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        etfs = []

        # Look for ETF links in the page
        etf_links = soup.find_all("a", href=re.compile(r'/funds/[a-z]+/?$', re.IGNORECASE))

        for link in etf_links:
            href = link.get("href")
            if not href or not isinstance(href, str):
                continue

            ticker_match = re.search(r'/funds/([a-z]+)', href, re.IGNORECASE)
            if ticker_match:
                ticker = ticker_match.group(1).upper()
                name = link.get_text(strip=True)

                if ticker and name:
                    etfs.append({
                        "ticker": ticker,
                        "name": name,
                        "detail_url": (
                            href if href.startswith("http") else self.base_url + href
                        ),
                    })

        logger.info(f"Parsed {len(etfs)} ETFs from Global X")
        return etfs
