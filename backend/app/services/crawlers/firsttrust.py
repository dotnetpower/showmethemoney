"""FirstTrust ETF Crawler"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

import httpx
from app.models.etf import ETF, DistributionFrequency
from bs4 import BeautifulSoup

from .base import BaseCrawler
from .yfinance_enricher import enrich_etf_with_yfinance

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

    def parse_data(self, html_content: str) -> List[ETF]:
        """Parse HTML content to extract ETF data"""
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        etfs = []

        # Find ETF data tables by class name
        tables = soup.find_all("table", class_="searchResults")
        logger.info(f"Found {len(tables)} ETF tables")

        for table in tables:
            # Get all rows (skip the header row)
            rows = table.find_all("tr")[1:]  # Skip header row
            
            for row in rows:
                etf = self._extract_etf_from_row(row)
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

    def _extract_etf_from_row(self, row) -> Optional[ETF]:
        """Extract ETF data from a table row
        
        Expected column order:
        0: Fund Name (with link)
        1: Ticker Symbol
        2: Inception Date
        3: Close NAV
        4: 30-Day SEC Yield
        5: Unsubsidized 30-Day SEC Yield
        6: Index Yield
        7: Yield As Of Date
        8: Fact Sheet
        """
        cells = row.find_all("td")
        if len(cells) < 4:  # Need at least Name, Ticker, Inception, NAV
            return None

        try:
            # Extract data from cells based on column position
            # Column 0: Fund Name (with link)
            name_cell = cells[0]
            name_link = name_cell.find("a")
            if not name_link:
                return None
            
            name = name_link.get_text(strip=True)
            detail_url = self.base_url + name_link.get("href", "")
            
            # Column 1: Ticker
            ticker = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            
            # Skip if ticker is empty or invalid
            if not ticker or len(ticker) > 10:
                return None
            
            # Column 2: Inception Date
            inception_str = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            inception_date = self._parse_date(inception_str)
            
            # Column 3: Close NAV
            nav_str = cells[3].get_text(strip=True) if len(cells) > 3 else ""
            nav = self._parse_price(nav_str)
            
            # Column 4: 30-Day SEC Yield (can use as distribution yield)
            yield_str = cells[4].get_text(strip=True) if len(cells) > 4 else ""
            distribution_yield = self._parse_percentage(yield_str)

            # yfinance로 NAV 및 기타 데이터 보강
            nav_enriched, expense_enriched, inception_enriched = enrich_etf_with_yfinance(
                ticker, nav or Decimal("0.00"), Decimal("0.00"), inception_date
            )
            
            # enriched 값이 더 나으면 사용
            if nav_enriched and nav_enriched != Decimal("0.00"):
                nav = nav_enriched
            expense_ratio = expense_enriched if expense_enriched and expense_enriched != Decimal("0.00") else Decimal("0.00")
            if inception_enriched:
                inception_date = inception_enriched

            # Return ETF model
            return ETF(
                ticker=ticker,
                fund_name=name,
                isin="N/A",
                cusip="N/A",
                inception_date=inception_date or datetime.now().date(),
                nav_amount=nav or Decimal("0.00"),
                nav_as_of=datetime.now().date(),
                expense_ratio=expense_ratio,
                ytd_return=None,
                one_year_return=None,
                three_year_return=None,
                five_year_return=None,
                ten_year_return=None,
                since_inception_return=None,
                asset_class="Equity",
                region="North America",
                market_type="Developed",
                distribution_yield=distribution_yield,
                product_page_url=detail_url,
                detail_page_url=detail_url,
            )

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
