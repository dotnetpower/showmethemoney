"""VanEck ETF crawler"""
import logging
import re
from datetime import date
from decimal import Decimal
from typing import Any, Optional

import httpx

from .base import BaseCrawler

logger = logging.getLogger(__name__)


class VanEckCrawler(BaseCrawler):
    """Crawler for VanEck ETFs"""

    def __init__(self):
        super().__init__()
        self.base_url = "https://www.vaneck.com"
        self.api_url = f"{self.base_url}/us/en/etf-mutual-fund-finder/"

    async def fetch_data(self) -> Optional[dict]:
        """Fetch ETF data from VanEck"""
        try:
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=30.0
            ) as client:
                # First try to get the page to extract any API endpoints
                response = await client.get(self.api_url)
                response.raise_for_status()
                
                # Parse HTML to find ETF data
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Look for JSON data in script tags
                scripts = soup.find_all("script")
                for script in scripts:
                    if script.string and "etf" in script.string.lower():
                        import json
                        import re

                        # Try to find JSON data
                        json_matches = re.findall(r'({[^{}]*"ticker"[^{}]*})', script.string, re.IGNORECASE)
                        if json_matches:
                            return {"scripts": json_matches}
                
                return {"html": response.text}
                
        except Exception as e:
            logger.error(f"Failed to fetch VanEck ETF data: {e}")
            return None

    def parse_data(self, raw_data: Optional[dict]) -> list[dict[str, Any]]:
        """Parse ETF data"""
        if not raw_data:
            return []

        etfs = []

        # If we have script data
        if "scripts" in raw_data:
            import json
            for script_text in raw_data["scripts"]:
                try:
                    data = json.loads(script_text)
                    if isinstance(data, dict):
                        etf_data = self._extract_etf_from_json(data)
                        if etf_data:
                            etfs.append(etf_data)
                except json.JSONDecodeError:
                    continue

        # If we have HTML, try to parse tables
        if "html" in raw_data and not etfs:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(raw_data["html"], "html.parser")
            
            # Look for links to ETF pages
            etf_links = soup.find_all("a", href=re.compile(r'/etf/[a-z]+/?$', re.IGNORECASE))
            for link in etf_links:
                href = link.get("href")
                if not href or not isinstance(href, str):
                    continue
                    
                ticker = href.split("/")[-1].upper()
                name = link.get_text(strip=True)
                
                if ticker and name:
                    etfs.append({
                        "ticker": ticker,
                        "name": name,
                        "detail_url": self.base_url + href,
                    })

        logger.info(f"Parsed {len(etfs)} ETFs from VanEck")
        return etfs

    def _extract_etf_from_json(self, data: dict) -> Optional[dict[str, Any]]:
        """Extract ETF information from JSON object"""
        try:
            ticker = data.get("ticker") or data.get("symbol")
            name = data.get("name") or data.get("fundName")

            if not ticker or not name:
                return None

            return {
                "ticker": ticker.upper(),
                "name": name,
                "inception_date": self._parse_date(
                    data.get("inceptionDate") or data.get("inception")
                ),
                "nav": self._parse_decimal(data.get("nav") or data.get("price")),
                "expense_ratio": self._parse_decimal(
                    data.get("expenseRatio") or data.get("expense")
                ),
            }

        except Exception as e:
            logger.warning(f"Failed to extract VanEck ETF from JSON: {e}")
            return None

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
            return None
