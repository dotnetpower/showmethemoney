"""Roundhill 크롤러 테스트"""
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from app.models.etf import ETF
from app.services.crawlers.roundhill import RoundhillCrawler
from bs4 import BeautifulSoup


@pytest.fixture
def sample_etf_list_html():
    """Roundhill ETF 리스트 페이지 샘플 HTML"""
    return """
    <html>
        <body>
            <div class="etf-list">
                <a href="../etf/metv/">METV</a>
                <a href="../etf/betz/">BETZ</a>
                <a href="../etf/nerd/">NERD</a>
                <a href="../etf/chat/">CHAT</a>
                <a href="../etf/weed/">WEED</a>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def sample_etf_detail_html():
    """Roundhill ETF 상세 페이지 샘플 HTML (METV)"""
    return """
    <html>
        <head>
            <meta name="description" content="Get exposure to the Metaverse as it looks to completely transform how we use the internet.">
        </head>
        <body>
            <h1>METV Metaverse ETF</h1>
            <div class="fund-details">
                <p>Expense Ratio: 0.59%</p>
                <p>NAV: $25.30</p>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def crawler():
    """RoundhillCrawler 인스턴스"""
    return RoundhillCrawler()


class TestRoundhillCrawler:
    """RoundhillCrawler 테스트"""
    
    def test_crawler_initialization(self, crawler):
        """크롤러 초기화 테스트"""
        assert crawler.get_provider_name() == "Roundhill"
        assert crawler.BASE_URL == "https://www.roundhillinvestments.com/etf"
        assert "roundhillinvestments.com" in crawler.DETAIL_URL_TEMPLATE
    
    def test_extract_tickers(self, crawler, sample_etf_list_html):
        """티커 추출 테스트"""
        soup = BeautifulSoup(sample_etf_list_html, 'html.parser')
        tickers = crawler._extract_tickers(soup)
        
        assert len(tickers) == 5
        assert "METV" in tickers
        assert "BETZ" in tickers
        assert "NERD" in tickers
        assert "CHAT" in tickers
        assert "WEED" in tickers
    
    def test_extract_tickers_with_invalid_hrefs(self, crawler):
        """잘못된 href 처리 테스트"""
        html = """
        <html>
            <body>
                <a href="../etf/metv/">METV</a>
                <a href="/some/other/path/">Other</a>
                <a href="">Empty</a>
                <a>No Href</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        tickers = crawler._extract_tickers(soup)
        
        assert len(tickers) == 1
        assert "METV" in tickers
    
    @pytest.mark.asyncio
    async def test_fetch_data_mock(self, crawler, sample_etf_list_html):
        """fetch_data 메서드 테스트 (Mock)"""
        mock_response = MagicMock()
        mock_response.text = sample_etf_list_html
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            tickers = await crawler.fetch_data()
            
            assert len(tickers) == 5
            assert "METV" in tickers
    
    @pytest.mark.asyncio
    async def test_fetch_etf_details_mock(self, crawler, sample_etf_detail_html):
        """개별 ETF 상세 정보 가져오기 테스트 (Mock)"""
        mock_response = MagicMock()
        mock_response.text = sample_etf_detail_html
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        
        etf = await crawler._fetch_etf_details(mock_client, "METV")
        
        assert etf is not None
        assert etf.ticker == "METV"
        assert "Metaverse ETF" in etf.fund_name
        assert etf.expense_ratio == Decimal("0.59")
        assert etf.isin == "N/A"
        assert etf.cusip == "N/A"
    
    @pytest.mark.asyncio
    async def test_fetch_etf_details_no_h1(self, crawler):
        """H1 태그 없는 경우 테스트"""
        html = "<html><body><p>No H1 here</p></body></html>"
        
        mock_response = MagicMock()
        mock_response.text = html
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        
        etf = await crawler._fetch_etf_details(mock_client, "TEST")
        
        assert etf is None
    
    @pytest.mark.asyncio
    async def test_fetch_etf_details_http_error(self, crawler):
        """HTTP 에러 처리 테스트"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Not Found", 
            request=MagicMock(), 
            response=mock_response
        ))
        
        etf = await crawler._fetch_etf_details(mock_client, "INVALID")
        
        assert etf is None
    
    @pytest.mark.asyncio
    async def test_parse_data_mock(self, crawler, sample_etf_detail_html):
        """parse_data 메서드 테스트 (Mock)"""
        tickers = {"METV", "BETZ"}
        
        mock_response = MagicMock()
        mock_response.text = sample_etf_detail_html
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            etf_list = await crawler.parse_data(tickers)
            
            assert len(etf_list) == 2
            assert all(isinstance(etf, ETF) for etf in etf_list)
    
    @pytest.mark.asyncio
    async def test_crawl_integration_mock(self, crawler, sample_etf_list_html, sample_etf_detail_html):
        """전체 크롤링 프로세스 통합 테스트 (Mock)"""
        # 리스트 페이지 mock
        mock_list_response = MagicMock()
        mock_list_response.text = sample_etf_list_html
        mock_list_response.raise_for_status = MagicMock()
        
        # 상세 페이지 mock
        mock_detail_response = MagicMock()
        mock_detail_response.text = sample_etf_detail_html
        mock_detail_response.raise_for_status = MagicMock()
        
        async def mock_get(url, **kwargs):
            if '/etf/' in url and url.count('/') > 3:
                # 상세 페이지
                return mock_detail_response
            else:
                # 리스트 페이지
                return mock_list_response
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=mock_get)
            
            etf_list = await crawler.crawl()
            
            assert len(etf_list) > 0
            assert all(isinstance(etf, ETF) for etf in etf_list)
            assert all(etf.ticker for etf in etf_list)


class TestRoundhillCrawlerIntegration:
    """실제 API 호출 통합 테스트"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_real_data(self, crawler):
        """실제 Roundhill API에서 데이터 가져오기 테스트"""
        tickers = await crawler.fetch_data()
        
        assert isinstance(tickers, set)
        assert len(tickers) > 0
        # 알려진 Roundhill ETF가 포함되어 있는지 확인
        known_tickers = {"METV", "BETZ", "NERD", "CHAT"}
        assert any(ticker in tickers for ticker in known_tickers)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_real_etf_detail(self, crawler):
        """실제 개별 ETF 상세 정보 가져오기 테스트"""
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        ) as client:
            etf = await crawler._fetch_etf_details(client, "METV")
            
            assert etf is not None
            assert etf.ticker == "METV"
            assert etf.fund_name
            assert etf.expense_ratio >= Decimal("0.00")
            assert "roundhillinvestments.com" in etf.product_page_url
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_crawl_real(self, crawler):
        """실제 전체 크롤링 프로세스 테스트"""
        etf_list = await crawler.crawl()
        
        assert len(etf_list) > 0
        
        # 첫 번째 ETF 검증
        first_etf = etf_list[0]
        assert first_etf.ticker
        assert first_etf.fund_name
        assert first_etf.expense_ratio >= Decimal("0.00")
        assert first_etf.product_page_url.startswith("https://")
        
        # 모든 ETF가 올바른 형식인지 확인
        for etf in etf_list:
            assert isinstance(etf, ETF)
            assert etf.ticker
            assert len(etf.ticker) <= 5
