"""WisdomTree ETF crawler"""
import logging
from datetime import date
from decimal import Decimal
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

from .base import BaseCrawler

logger = logging.getLogger(__name__)


class WisdomTreeCrawler(BaseCrawler):
    """Crawler for WisdomTree ETFs"""

    def __init__(self):
        super().__init__()
        self.base_url = "https://www.wisdomtree.com"
        self.etf_list_url = f"{self.base_url}/investments/etfs"
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
            logger.error(f"Failed to fetch WisdomTree ETF data: {e}")
            return None

    def parse_data(self, html_content: str) -> list[dict[str, Any]]:
        """Parse HTML content to extract ETF data"""
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        etfs = []

        # Try to find ETF data in script tags
        scripts = soup.find_all("script")
        for script in scripts:
            if script.string and "etf" in script.string.lower():
                import json
                import re

                # Look for JSON arrays containing ETF data
                json_matches = re.findall(r'\[{[^\]]+}\]', script.string)
                for match in json_matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data, list) and data:
                            first_item = data[0]
                            if isinstance(first_item, dict) and any(
                                key in str(first_item).lower()
                                for key in ["ticker", "symbol", "fund"]
                            ):
                                etfs.extend(self._parse_json_data(data))
                                if etfs:
                                    break
                    except json.JSONDecodeError:
                        continue

        # If no JSON data found, try parsing HTML structure
        if not etfs:
            etfs = self._parse_html_structure(soup)

        logger.info(f"Parsed {len(etfs)} ETFs from WisdomTree")
        return etfs

    def _parse_json_data(self, data: list[dict]) -> list[dict[str, Any]]:
        """Parse JSON data to extract ETF information"""
        etfs = []

        for item in data:
            try:
                ticker = (
                    item.get("ticker")
                    or item.get("symbol")
                    or item.get("Symbol")
                )
                name = item.get("name") or item.get("fundName") or item.get("Name")

                if not ticker or not name:
                    continue

                etf_data = {
                    "ticker": ticker.upper(),
                    "name": name,
                    "inception_date": self._parse_date(
                        item.get("inceptionDate") or item.get("InceptionDate")
                    ),
                    "nav": self._parse_decimal(
                        item.get("nav") or item.get("NAV") or item.get("price")
                    ),
                    "expense_ratio": self._parse_decimal(
                        item.get("expenseRatio") or item.get("ExpenseRatio")
                    ),
                }

                etfs.append(etf_data)

            except Exception as e:
                logger.warning(f"Failed to parse WisdomTree ETF data: {e}")
                continue

        return etfs

    def _parse_html_structure(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Parse HTML structure to find ETF links"""
        etfs = []

        # Look for links to ETF detail pages
        import re
        etf_links = soup.find_all("a", href=re.compile(r'/etf/[a-z]+', re.IGNORECASE))

        for link in etf_links:
            href = link.get("href")
            if not href or not isinstance(href, str):
                continue
                
            ticker_match = re.search(r'/etf/([a-z]+)', href, re.IGNORECASE)

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

        return etfs

    def _parse_date(self, date_str: Any) -> Optional[date]:
        """Parse date string"""
        if not date_str:
            return None

        try:
            from datetime import datetime

            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"]:
                try:
                    dt = datetime.strptime(str(date_str), fmt)
                    return dt.date()
                except ValueError:
                    continue

            return None
        except Exception:
            logger.warning(f"Failed to parse date: {date_str}")
            return None

    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """Parse decimal value"""
        if value is None or value == "":
            return None

        try:
            if isinstance(value, str):
                value = value.replace("$", "").replace("%", "").replace(",", "")

            return Decimal(str(value))
        except Exception:
            logger.warning(f"Failed to parse decimal: {value}")
            return None
