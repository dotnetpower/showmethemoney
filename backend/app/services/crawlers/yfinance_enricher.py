"""yfinance를 사용하여 ETF 데이터를 보강하는 헬퍼 모듈"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)


def enrich_etf_with_yfinance(
    ticker: str,
    current_nav: Decimal,
    current_expense_ratio: Decimal,
    current_inception_date: Optional[date] = None
) -> tuple[Decimal, Decimal, Optional[date]]:
    """
    yfinance를 사용하여 ETF 데이터를 보강합니다.
    
    Args:
        ticker: ETF 티커
        current_nav: 현재 NAV (0이면 yfinance에서 가져옴)
        current_expense_ratio: 현재 expense ratio (0이면 yfinance에서 가져옴)
        current_inception_date: 현재 inception date (None이면 yfinance에서 가져옴)
    
    Returns:
        tuple: (nav_amount, expense_ratio, inception_date)
    """
    nav_amount = current_nav
    expense_ratio = current_expense_ratio
    inception_date = current_inception_date
    
    # NAV나 expense ratio가 0이면 yfinance에서 시도
    if nav_amount == 0 or expense_ratio == 0 or inception_date is None:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get NAV (current price) if not available
            if nav_amount == 0:
                if "regularMarketPrice" in info and info["regularMarketPrice"]:
                    nav_amount = Decimal(str(info["regularMarketPrice"]))
                    logger.debug(f"{ticker}: Got NAV from yfinance: ${nav_amount}")
                elif "previousClose" in info and info["previousClose"]:
                    nav_amount = Decimal(str(info["previousClose"]))
                    logger.debug(f"{ticker}: Got NAV from yfinance (previousClose): ${nav_amount}")
            
            # Get expense ratio if not available
            if expense_ratio == 0:
                if "netExpenseRatio" in info and info["netExpenseRatio"]:
                    expense_ratio = Decimal(str(info["netExpenseRatio"]))
                    logger.debug(f"{ticker}: Got expense ratio from yfinance: {expense_ratio}%")
                elif "totalExpenseRatio" in info and info["totalExpenseRatio"]:
                    expense_ratio = Decimal(str(info["totalExpenseRatio"] * 100))
                    logger.debug(f"{ticker}: Got expense ratio from yfinance: {expense_ratio}%")
            
            # Get inception date if not available
            if inception_date is None or inception_date == datetime.now().date():
                if "fundInceptionDate" in info and info["fundInceptionDate"]:
                    try:
                        inception_date = datetime.fromtimestamp(info["fundInceptionDate"]).date()
                        logger.debug(f"{ticker}: Got inception date from yfinance: {inception_date}")
                    except:
                        pass
        
        except Exception as e:
            logger.debug(f"Could not enrich {ticker} with yfinance: {e}")
    
    return nav_amount, expense_ratio, inception_date
