"""PIMCO ETF crawler"""
import logging
from datetime import date
from decimal import Decimal
from typing import Any, Optional

import httpx

from .base import BaseCrawler

logger = logging.getLogger(__name__)


class PIMCOCrawler(BaseCrawler):
    """Crawler for PIMCO ETFs"""

    def __init__(self):
        super().__init__()
        self.api_url = "https://fundexp-ui.pimco.com/fund-explorer-api/api/dashboard/usPerformanceDetails"
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "countrycode": "US",
            "langcode": "en",
            "origin": "https://www.pimco.com",
            "referer": "https://www.pimco.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "userrole": "IND",
        }

    async def fetch_data(self) -> Optional[dict]:
        """Fetch ETF data from PIMCO API"""
        try:
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=30.0
            ) as client:
                response = await client.get(
                    self.api_url,
                    headers=self.headers,
                    params={"selectedViewNav": "NAV"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch PIMCO ETF data: {e}")
            return None

    def parse_data(self, raw_data: Optional[dict]) -> list[dict[str, Any]]:
        """Parse API response to extract ETF data"""
        if not raw_data or "data" not in raw_data:
            return []

        etfs = []
        
        for item in raw_data["data"]:
            try:
                # Filter for ETFs - check Vehicle type or Investment Vehicle
                vehicle = item.get("Vehicle", "")
                inv_vehicle = item.get("Investment Vehicle Two", "")
                
                # PIMCO ETFs typically have "ETF" in the vehicle field
                if "ETF" not in vehicle.upper() and "ETF" not in inv_vehicle.upper():
                    continue

                ticker = item.get("Ticker")
                name = item.get("Name") or item.get("Cusip Name")

                if not ticker or not name:
                    continue

                etf_data = {
                    "ticker": ticker.strip().upper(),
                    "name": name.strip(),
                    "inception_date": self._parse_date(
                        item.get("Share Class Inception Date")
                        or item.get("Share Class Perf Inception Date")
                    ),
                    "nav": None,  # NAV is in returns, not basic info
                    "expense_ratio": self._parse_decimal(
                        item.get("Net Expense Ratio %2")
                        or item.get("Gross Expense Ratio %")
                    ),
                }

                etfs.append(etf_data)

            except Exception as e:
                logger.warning(f"Failed to parse PIMCO fund data: {e}")
                continue

        logger.info(f"Parsed {len(etfs)} ETFs from PIMCO")
        return etfs

    def _parse_date(self, date_str: Any) -> Optional[date]:
        """Parse date string in YYYY-MM-DD format"""
        if not date_str:
            return None

        try:
            from datetime import datetime

            # PIMCO uses YYYY-MM-DD format
            dt = datetime.strptime(str(date_str), "%Y-%m-%d")
            return dt.date()
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
