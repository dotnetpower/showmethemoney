"""Roundhill ETF 크롤러"""
import logging
import re
from datetime import date
from decimal import Decimal
from typing import Any, List, Set

import httpx
from app.models.etf import ETF
from bs4 import BeautifulSoup

from .base import BaseCrawler

logger = logging.getLogger(__name__)


class RoundhillCrawler(BaseCrawler):
    """Roundhill ETF 데이터 크롤러"""
    
    # Roundhill ETF 리스트 페이지
    BASE_URL = "https://www.roundhillinvestments.com/etf"
    DETAIL_URL_TEMPLATE = "https://www.roundhillinvestments.com/etf/{ticker}/"
    
    async def fetch_data(self) -> Any:
        """
        Roundhill 웹사이트에서 HTML 데이터를 가져옵니다.
        
        Returns:
            ETF 티커 목록
        """
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,  # 301/302 리다이렉트 자동 따라가기
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        ) as client:
            response = await client.get(self.BASE_URL)
            response.raise_for_status()
            
            # 메인 페이지에서 모든 ETF 티커 추출
            soup = BeautifulSoup(response.text, 'html.parser')
            tickers = self._extract_tickers(soup)
            
            logger.info(f"Found {len(tickers)} Roundhill ETF tickers")
            return tickers
    
    def _extract_tickers(self, soup: BeautifulSoup) -> Set[str]:
        """
        메인 페이지에서 모든 ETF 티커를 추출합니다.
        
        Args:
            soup: BeautifulSoup 객체
            
        Returns:
            티커 집합
        """
        tickers = set()
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            # href가 None이거나 리스트인 경우 스킵
            if not isinstance(href, str):
                continue
                
            # ../etf/TICKER/ 또는 /etf/TICKER/ 패턴 찾기
            if 'etf/' in href:
                if '../etf/' in href:
                    ticker = href.replace('../etf/', '').strip('/')
                elif '/etf/' in href:
                    ticker = href.split('/etf/')[-1].strip('/')
                else:
                    continue
                
                # 유효한 티커만 추가 (5자 이하)
                if ticker and len(ticker) <= 5 and ticker.replace('-', '').isalnum():
                    tickers.add(ticker.upper())
        
        return tickers
    
    async def parse_data(self, raw_data: Any) -> List[ETF]:
        """
        Roundhill ETF 티커 목록을 받아 각 ETF의 상세 정보를 수집합니다.
        
        Args:
            raw_data: ETF 티커 집합
            
        Returns:
            ETF 모델 리스트
        """
        tickers = raw_data
        etf_list = []
        
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        ) as client:
            for ticker in tickers:
                try:
                    etf = await self._fetch_etf_details(client, ticker)
                    if etf:
                        etf_list.append(etf)
                        logger.info(f"Successfully parsed {ticker}")
                except Exception as e:
                    logger.error(f"Failed to parse {ticker}: {e}")
                    continue
        
        logger.info(f"Successfully parsed {len(etf_list)} Roundhill ETFs")
        return etf_list
    
    async def _fetch_etf_details(self, client: httpx.AsyncClient, ticker: str) -> ETF | None:
        """
        개별 ETF의 상세 정보를 가져옵니다.
        
        Args:
            client: HTTP 클라이언트
            ticker: ETF 티커
            
        Returns:
            ETF 모델 또는 None
        """
        url = self.DETAIL_URL_TEMPLATE.format(ticker=ticker.lower())
        
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # ETF 이름 추출
            h1 = soup.find('h1')
            if not h1:
                logger.warning(f"No H1 found for {ticker}")
                return None
            
            full_name = h1.text.strip()
            # 티커를 제거하고 이름만 추출 (예: "METV Metaverse ETF" -> "Metaverse ETF")
            fund_name = full_name.replace(ticker, '').strip()
            
            # 텍스트에서 정보 추출
            text = soup.get_text()
            
            # Expense Ratio 추출
            expense_ratio = Decimal("0.00")
            expense_match = re.search(r'(?:Expense Ratio|Net Expense)[:\s]*(\d+\.\d+)%', text, re.IGNORECASE)
            if expense_match:
                expense_ratio = Decimal(expense_match.group(1))
            
            # 기본값 설정 (Roundhill은 제한된 정보만 제공)
            return ETF(
                ticker=ticker,
                fund_name=fund_name,
                isin="N/A",  # Roundhill 웹사이트에서 제공하지 않음
                cusip="N/A",  # Roundhill 웹사이트에서 제공하지 않음
                inception_date=None,  # 웹사이트에서 제공하지 않음
                nav_amount=Decimal("0.00"),  # 웹사이트에서 NAV 정보 추출 필요
                nav_as_of=date.today(),
                expense_ratio=expense_ratio,
                ytd_return=None,
                one_year_return=None,
                three_year_return=None,
                five_year_return=None,
                ten_year_return=None,
                since_inception_return=None,
                asset_class="Unknown",  # 추가 파싱 필요
                region="Unknown",  # 추가 파싱 필요
                market_type="Unknown",  # 추가 파싱 필요
                distribution_yield=None,
                product_page_url=url,
                detail_page_url=url
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for {ticker}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error fetching details for {ticker}: {e}")
            return None
