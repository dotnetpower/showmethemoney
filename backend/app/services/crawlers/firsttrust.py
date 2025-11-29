"""First Trust ETF crawler"""
import logging
from datetime import date
from decimal import Decimal
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

from .base import BaseCrawler

logger = logging.getLogger(__name__)


class FirstTrustCrawler(BaseCrawler):
    """Crawler for First Trust ETFs"""

    def __init__(self):
        super().__init__()
        self.base_url = "https://www.ftportfolios.com"
        self.etf_list_url = f"{self.base_url}/Retail/etf/etflist.aspx"

    async def fetch_data(self) -> Optional[str]:
        """Fetch HTML page containing ETF data"""
        try:
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=30.0
            ) as client:
                response = await client.get(self.etf_list_url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Failed to fetch First Trust ETF data: {e}")
            return None

    def parse_data(self, html_content: str) -> list[dict[str, Any]]:
        """Parse HTML content to extract ETF data"""
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        etfs = []

        # Find all tables in the page
        tables = soup.find_all("table")

        for table in tables:
            # Check if this table has ETF data by looking for header row
            header_row = table.find("tr")
            if not header_row:
                continue

            headers = [
                cell.get_text(strip=True)
                for cell in header_row.find_all(["th", "td"])
            ]

            # Verify this is an ETF data table
            if not self._is_etf_table(headers):
                continue

            # Process data rows (skip header row)
            data_rows = table.find_all("tr")[1:]

            for row in data_rows:
                etf = self._extract_etf_from_row(row, headers)
                if etf:
                    etfs.append(etf)

        logger.info(f"Parsed {len(etfs)} ETFs from First Trust")
        return etfs

    def _is_etf_table(self, headers: list[str]) -> bool:
        """Check if headers indicate this is an ETF data table"""
        # Look for key columns
        header_text = " ".join(headers).lower()
        required_fields = ["ticker", "fund", "inception"]

        return all(field in header_text for field in required_fields)

    def _extract_etf_from_row(
        self, row, headers: list[str]
    ) -> Optional[dict[str, Any]]:
        """Extract ETF data from a table row"""
        cells = row.find_all(["td", "th"])
        if len(cells) < 3:
            return None

        try:
            # Map cells to data
            cell_texts = [cell.get_text(strip=True) for cell in cells]

            # Find column indices
            ticker_idx = self._find_column_index(headers, "ticker")
            name_idx = self._find_column_index(headers, "fund")
            inception_idx = self._find_column_index(headers, "inception")
            nav_idx = self._find_column_index(headers, "nav")
            expense_idx = self._find_column_index(headers, "sec yield")

            if (
                ticker_idx is None
                or name_idx is None
                or inception_idx is None
            ):
                return None

            ticker = cell_texts[ticker_idx] if ticker_idx < len(cell_texts) else ""
            name = cell_texts[name_idx] if name_idx < len(cell_texts) else ""

            # Skip empty rows or invalid tickers
            if not ticker or not name or ticker == "TickerSymbol":
                return None

            inception_date = None
            if inception_idx is not None and inception_idx < len(cell_texts):
                inception_date = self._parse_date(cell_texts[inception_idx])

            nav = None
            if nav_idx is not None and nav_idx < len(cell_texts):
                nav = self._parse_price(cell_texts[nav_idx])

            expense_ratio = None
            if expense_idx is not None and expense_idx < len(cell_texts):
                expense_ratio = self._parse_percentage(cell_texts[expense_idx])

            # Get detail URL from ticker link
            detail_url = None
            ticker_cell = cells[ticker_idx] if ticker_idx < len(cells) else None
            if ticker_cell:
                link = ticker_cell.find("a", href=True)
                if link:
                    detail_url = self.base_url + link["href"]

            # Return dictionary instead of ETF model
            return {
                "ticker": ticker,
                "fund_name": name,
                "inception_date": inception_date.isoformat() if inception_date else None,
                "nav_amount": float(nav) if nav else None,
                "expense_ratio": float(expense_ratio) if expense_ratio else None,
                "detail_page_url": detail_url,
            }

        except Exception as e:
            logger.warning(f"Failed to extract ETF data from row: {e}")
            return None

    def _find_column_index(
        self, headers: list[str], column_name: str
    ) -> Optional[int]:
        """Find the index of a column by name"""
        for i, header in enumerate(headers):
            if column_name.lower() in header.lower():
                return i
        return None

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string in MM/DD/YY format"""
        if not date_str or date_str == "-------":
            return None

        try:
            # Format: 05/18/16
            from datetime import datetime

            dt = datetime.strptime(date_str, "%m/%d/%y")
            return dt.date()
        except (ValueError, AttributeError):
            logger.warning(f"Failed to parse date: {date_str}")
            return None

    def _parse_price(self, price_str: str) -> Optional[Decimal]:
        """Parse price string like '$30.12'"""
        if not price_str or price_str == "-------":
            return None

        try:
            # Remove $ and convert to Decimal
            price_str = price_str.replace("$", "").replace(",", "")
            return Decimal(price_str)
        except (ValueError, AttributeError, Exception):
            logger.warning(f"Failed to parse price: {price_str}")
            return None

    def _parse_percentage(self, pct_str: str) -> Optional[Decimal]:
        """Parse percentage string like '2.31%'"""
        if not pct_str or pct_str == "-------":
            return None

        try:
            # Remove % and convert to Decimal
            pct_str = pct_str.replace("%", "")
            value = Decimal(pct_str)
            return round(value, 2)
        except (ValueError, AttributeError, Exception):
            logger.warning(f"Failed to parse percentage: {pct_str}")
            return None
