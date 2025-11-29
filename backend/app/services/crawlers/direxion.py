"""Direxion ETF crawler"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional

import httpx
import yfinance as yf
from app.models.etf import ETF

from .base import BaseCrawler

logger = logging.getLogger(__name__)


class DirexionCrawler(BaseCrawler):
    """Crawler for Direxion ETFs using a curated list"""

    def __init__(self):
        super().__init__()
        self.base_url = "https://www.direxion.com"
        # Direxion의 주요 ETF 목록 (ticker, name)
        # 실제 웹사이트에서 수동으로 수집한 데이터
        self.etf_list = [
            # Leveraged Bull 3X ETFs
            ("TQQQ", "Direxion Daily NASDAQ-100 Bull 3X Shares"),
            ("SOXL", "Direxion Daily Semiconductor Bull 3X Shares"),
            ("SPXL", "Direxion Daily S&P 500 Bull 3X Shares"),
            ("TNA", "Direxion Daily Small Cap Bull 3X Shares"),
            ("TECL", "Direxion Daily Technology Bull 3X Shares"),
            ("CURE", "Direxion Daily Healthcare Bull 3X Shares"),
            ("DPST", "Direxion Daily Regional Banks Bull 3X Shares"),
            ("FAS", "Direxion Daily Financial Bull 3X Shares"),
            ("LABU", "Direxion Daily S&P Biotech Bull 3X Shares"),
            ("NAIL", "Direxion Daily Homebuilders & Supplies Bull 3X Shares"),
            ("WANT", "Direxion Daily Consumer Discretionary Bull 3X Shares"),
            ("UTSL", "Direxion Daily Utilities Bull 3X Shares"),
            ("ERX", "Direxion Daily Energy Bull 2X Shares"),
            ("RETL", "Direxion Daily Retail Bull 3X Shares"),
            ("DFEN", "Direxion Daily Aerospace & Defense Bull 3X Shares"),
            ("PILL", "Direxion Daily Pharmaceutical & Medical Bull 3X Shares"),
            ("HIBL", "Direxion Daily S&P 500 High Beta Bull 3X Shares"),
            ("DUSL", "Direxion Daily Industrials Bull 3X Shares"),
            
            # Leveraged Bear 3X ETFs
            ("SQQQ", "Direxion Daily NASDAQ-100 Bear 3X Shares"),
            ("SOXS", "Direxion Daily Semiconductor Bear 3X Shares"),
            ("SPXS", "Direxion Daily S&P 500 Bear 3X Shares"),
            ("TZA", "Direxion Daily Small Cap Bear 3X Shares"),
            ("TECS", "Direxion Daily Technology Bear 3X Shares"),
            ("FAZ", "Direxion Daily Financial Bear 3X Shares"),
            ("LABD", "Direxion Daily S&P Biotech Bear 3X Shares"),
            ("DRV", "Direxion Daily Real Estate Bear 3X Shares"),
            
            # Bear 1X ETFs
            ("SPDN", "Direxion Daily S&P 500 Bear 1X Shares"),
            
            # Single Stock Leveraged ETFs
            ("NVDU", "Direxion Daily NVDA Bull 2X Shares"),
            ("NVDD", "Direxion Daily NVDA Bear 1X Shares"),
            ("TSLQ", "Direxion Daily TSLA Bear 1X Shares"),
            ("TSLL", "Direxion Daily TSLA Bull 2X Shares"),
            ("GOOU", "Direxion Daily GOOGL Bull 2X Shares"),
            ("GOOD", "Direxion Daily GOOGL Bear 1X Shares"),
            ("APLY", "Direxion Daily AAPL Bear 1X Shares"),
            ("AAPU", "Direxion Daily AAPL Bull 2X Shares"),
            ("AMZU", "Direxion Daily AMZN Bull 2X Shares"),
            ("AMZD", "Direxion Daily AMZN Bear 1X Shares"),
            ("MSFU", "Direxion Daily MSFT Bull 2X Shares"),
            ("MSFD", "Direxion Daily MSFT Bear 1X Shares"),
            ("NFLU", "Direxion Daily NFLX Bull 2X Shares"),
            ("NFLD", "Direxion Daily NFLX Bear 1X Shares"),
            
            # Gold Miners
            ("JNUG", "Direxion Daily Junior Gold Miners Index Bull 2X Shares"),
            ("JDST", "Direxion Daily Junior Gold Miners Index Bear 2X Shares"),
            ("NUGT", "Direxion Daily Gold Miners Index Bull 2X Shares"),
            ("DUST", "Direxion Daily Gold Miners Index Bear 2X Shares"),
            
            # International
            ("YINN", "Direxion Daily FTSE China Bull 3X Shares"),
            ("YANG", "Direxion Daily FTSE China Bear 3X Shares"),
            ("BRZU", "Direxion Daily MSCI Brazil Bull 2X Shares"),
            ("MEXX", "Direxion Daily MSCI Mexico Bull 3X Shares"),
            
            # Others
            ("GDXD", "Direxion Daily Gold Miners Index Bear 1X Shares"),
            ("GDXU", "Direxion Daily Gold Miners Index Bull 1.25X Shares"),
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def fetch_data(self) -> Optional[Any]:
        """Return curated ETF list"""
        return self.etf_list

    async def parse_data(self, etf_list: List[tuple]) -> List[ETF]:
        """Parse ETF list and create ETF objects with real-time data from yfinance"""
        if not etf_list:
            return []

        etfs = []
        
        for ticker, name in etf_list:
            try:
                # Fetch real-time data from Yahoo Finance using yfinance
                nav_amount = Decimal("0.00")
                expense_ratio = Decimal("0.00")
                inception_date = datetime.now().date()
                
                try:
                    # Get ticker info from yfinance
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    # Get NAV (current price)
                    if "regularMarketPrice" in info and info["regularMarketPrice"]:
                        nav_amount = Decimal(str(info["regularMarketPrice"]))
                    elif "previousClose" in info and info["previousClose"]:
                        nav_amount = Decimal(str(info["previousClose"]))
                    
                    # Get expense ratio (use netExpenseRatio or totalExpenseRatio)
                    if "netExpenseRatio" in info and info["netExpenseRatio"]:
                        expense_ratio = Decimal(str(info["netExpenseRatio"]))
                    elif "totalExpenseRatio" in info and info["totalExpenseRatio"]:
                        # Yahoo returns as decimal (e.g., 0.0095 for 0.95%)
                        expense_ratio = Decimal(str(info["totalExpenseRatio"] * 100))
                    
                    # Get inception date
                    if "fundInceptionDate" in info and info["fundInceptionDate"]:
                        try:
                            inception_date = datetime.fromtimestamp(info["fundInceptionDate"]).date()
                        except:
                            pass
                    
                    logger.debug(f"{ticker}: NAV=${nav_amount}, Expense={expense_ratio}%")
                
                except Exception as e:
                    logger.debug(f"Could not fetch yfinance data for {ticker}: {e}")
                
                etf = ETF(
                    ticker=ticker,
                    fund_name=name,
                    isin="N/A",
                    cusip="N/A",
                    inception_date=inception_date,
                    nav_amount=nav_amount,
                    nav_as_of=datetime.now().date(),
                    expense_ratio=expense_ratio,
                    ytd_return=None,
                    one_year_return=None,
                    three_year_return=None,
                    five_year_return=None,
                    ten_year_return=None,
                    since_inception_return=None,
                    asset_class="Leveraged/Inverse",
                    region="US",
                    market_type="ETF",
                    distribution_yield=None,
                    product_page_url=f"{self.base_url}/product/{ticker.lower()}",
                    detail_page_url=f"{self.base_url}/product/{ticker.lower()}",
                )
                etfs.append(etf)
                
            except Exception as e:
                logger.warning(f"Failed to create ETF {ticker}: {e}")
                continue

        logger.info(f"Parsed {len(etfs)} ETFs from Direxion")
        return etfs
