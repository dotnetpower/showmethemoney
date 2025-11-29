"""Direxion ETF crawler"""
import logging
import re
from datetime import date
from decimal import Decimal
from typing import Any, Optional

import httpx
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

    def parse_data(self, html_content: str) -> list[dict[str, Any]]:
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
                    etfs.append({
                        "ticker": ticker,
                        "name": name,
                        "detail_url": (
                            href if href.startswith("http") else self.base_url + href
                        ),
                    })

        logger.info(f"Parsed {len(etfs)} ETFs from Direxion")
        return etfs
