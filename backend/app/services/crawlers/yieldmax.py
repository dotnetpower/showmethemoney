"""Yieldmax ETF 크롤러"""
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import httpx
from app.models.etf import ETF, DistributionFrequency
from app.services.crawlers.base import BaseCrawler
from bs4 import BeautifulSoup


class YieldmaxCrawler(BaseCrawler):
    """Yieldmax ETF 데이터 크롤러"""
    
    BASE_URL = "https://yieldmaxetfs.com/our-etfs/"

    async def fetch_data(self) -> str:
        """Yieldmax ETF 목록 페이지에서 HTML 가져오기"""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = await client.get(self.BASE_URL, headers=headers)
            response.raise_for_status()
            return response.text

    async def parse_data(self, html: str) -> list[ETF]:
        """
        HTML에서 ETF 데이터 파싱
        
        Note: Yieldmax 페이지는 JavaScript로 테이블을 렌더링하므로
        정적 HTML 파싱으로는 데이터를 가져올 수 없습니다.
        
        해결 방법:
        1. Playwright/Selenium으로 JavaScript 렌더링 후 파싱
        2. Yieldmax API 엔드포인트 찾아서 직접 호출
        3. 위 방법 구현 후 아래 파싱 로직 추가
        
        현재는 빈 리스트 반환
        """
        soup = BeautifulSoup(html, 'html.parser')
        etfs = []
        
        # TODO: JavaScript 렌더링 필요
        # fundsTableWrap ID를 가진 요소 내부의 table 찾기
        table_wrap = soup.find(id='fundsTableWrap')
        if not table_wrap:
            return etfs
        
        table = table_wrap.find('table')
        if not table:
            return etfs
        
        tbody = table.find('tbody')
        if not tbody:
            return etfs
        
        rows = tbody.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 2:  # 최소한 ticker, name 필요
                continue
            
            try:
                # 실제 데이터 구조에 맞춰 조정 필요
                ticker = cells[0].get_text(strip=True)
                name = cells[1].get_text(strip=True)
                
                # 상세 페이지 링크 찾기
                detail_link: Optional[str] = None
                link_elem = cells[0].find('a') or cells[1].find('a')
                if link_elem:
                    href = link_elem.get('href')
                    if href and isinstance(href, str):
                        detail_link = href if href.startswith('http') else f"https://yieldmaxetfs.com{href}"
                
                # Expense ratio 파싱 (있는 경우)
                expense_ratio = None
                if len(cells) > 2:
                    expense_text = cells[2].get_text(strip=True)
                    expense_ratio = self._parse_expense_ratio(expense_text)
                
                # AUM 파싱 (있는 경우)
                aum = None
                if len(cells) > 3:
                    aum_text = cells[3].get_text(strip=True)
                    aum = self._parse_aum(aum_text)
                
                # Inception date 파싱 (있는 경우)
                inception_date = None
                if len(cells) > 4:
                    date_text = cells[4].get_text(strip=True)
                    inception_date = self._parse_inception_date(date_text)
                
                etf = ETF(
                    ticker=ticker,
                    fund_name=name,
                    isin="N/A",
                    cusip="N/A",
                    inception_date=inception_date or date.today(),
                    nav_amount=Decimal("0.00"),
                    nav_as_of=date.today(),
                    expense_ratio=Decimal(str(expense_ratio)) if expense_ratio else Decimal("0.00"),
                    ytd_return=None,
                    one_year_return=None,
                    three_year_return=None,
                    five_year_return=None,
                    ten_year_return=None,
                    since_inception_return=None,
                    asset_class="Unknown",
                    region="Unknown",
                    market_type="Unknown",
                    distribution_yield=None,
                    product_page_url=detail_link or "https://yieldmaxetfs.com/our-etfs/",
                    distribution_frequency=DistributionFrequency.UNKNOWN,
                    detail_page_url=detail_link,
                )
                etfs.append(etf)
                
            except Exception as e:
                # 개별 행 파싱 실패는 건너뛰기
                continue
        
        return etfs

    def _parse_expense_ratio(self, text: str) -> Optional[float]:
        """Expense ratio 텍스트를 float로 변환 (예: "0.99%" → 0.99)"""
        if not text:
            return None
        
        # % 제거하고 숫자만 추출
        match = re.search(r'(\d+\.?\d*)', text.replace(',', ''))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def _parse_aum(self, text: str) -> Optional[float]:
        """AUM 텍스트를 millions 단위로 변환 (예: "$1.2B" → 1200.0)"""
        if not text:
            return None
        
        # $, 쉼표 제거
        cleaned = text.replace('$', '').replace(',', '').strip().upper()
        
        # 숫자와 단위(B/M/K) 추출
        match = re.search(r'([\d.]+)\s*([BMK])?', cleaned)
        if match:
            try:
                value = float(match.group(1))
                unit = match.group(2)
                
                # 단위에 따라 millions로 변환
                if unit == 'B':  # Billions
                    return value * 1000.0
                elif unit == 'M':  # Millions
                    return value
                elif unit == 'K':  # Thousands
                    return value / 1000.0
                else:
                    # 단위 없으면 그대로 (millions 단위로 가정)
                    return value
            except ValueError:
                return None
        return None

    def _parse_inception_date(self, text: str) -> Optional[datetime]:
        """Inception date 텍스트를 datetime으로 변환"""
        if not text:
            return None
        
        # 일반적인 날짜 형식들 시도
        date_formats = [
            '%m/%d/%Y',  # 01/15/2023
            '%Y-%m-%d',  # 2023-01-15
            '%b %d, %Y',  # Jan 15, 2023
            '%B %d, %Y',  # January 15, 2023
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(text.strip(), fmt)
            except ValueError:
                continue
        
        return None
