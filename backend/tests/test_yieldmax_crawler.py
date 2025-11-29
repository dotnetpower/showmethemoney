"""Yieldmax 크롤러 테스트"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from app.models.etf import ETF, DistributionFrequency
from app.services.crawlers.yieldmax import YieldmaxCrawler


class TestYieldmaxCrawlerInit:
    """크롤러 초기화 테스트"""
    
    def test_base_url(self):
        """BASE_URL이 올바르게 설정되어 있는지 확인"""
        crawler = YieldmaxCrawler()
        assert crawler.BASE_URL == "https://yieldmaxetfs.com/our-etfs/"


class TestYieldmaxCrawlerFetch:
    """데이터 가져오기 테스트"""
    
    @pytest.mark.asyncio
    async def test_fetch_data_success(self):
        """정상적으로 HTML을 가져오는지 테스트"""
        crawler = YieldmaxCrawler()
        
        mock_html = """
        <html>
            <div id="fundsTableWrap">
                <table>
                    <thead><tr><th>Ticker</th></tr></thead>
                    <tbody><tr><td>TSLY</td></tr></tbody>
                </table>
            </div>
        </html>
        """
        
        mock_response = AsyncMock()
        mock_response.text = mock_html
        mock_response.raise_for_status = AsyncMock()
        
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            html = await crawler.fetch_data()
            assert "fundsTableWrap" in html
    
    @pytest.mark.asyncio
    async def test_fetch_data_http_error(self):
        """HTTP 오류 발생 시 예외가 발생하는지 테스트"""
        crawler = YieldmaxCrawler()
        
        with patch("httpx.AsyncClient.get", side_effect=httpx.HTTPStatusError(
            "404 Not Found",
            request=AsyncMock(),
            response=AsyncMock(status_code=404)
        )):
            with pytest.raises(httpx.HTTPStatusError):
                await crawler.fetch_data()


class TestYieldmaxCrawlerParse:
    """HTML 파싱 테스트"""
    
    @pytest.mark.asyncio
    async def test_parse_data_with_mock_table(self):
        """모의 테이블 데이터를 파싱하는지 테스트"""
        crawler = YieldmaxCrawler()
        
        mock_html = """
        <html>
            <div id="fundsTableWrap">
                <table>
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Name</th>
                            <th>Expense Ratio</th>
                            <th>AUM</th>
                            <th>Inception Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><a href="/etfs/tsly">TSLY</a></td>
                            <td>YieldMax TSLA Option Income Strategy ETF</td>
                            <td>0.99%</td>
                            <td>$1.5B</td>
                            <td>11/01/2022</td>
                        </tr>
                        <tr>
                            <td><a href="/etfs/msty">MSTY</a></td>
                            <td>YieldMax MSTR Option Income Strategy ETF</td>
                            <td>1.15%</td>
                            <td>$800M</td>
                            <td>03/15/2023</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </html>
        """
        
        etfs = await crawler.parse_data(mock_html)
        
        assert len(etfs) == 2
        
        # 첫 번째 ETF 검증
        assert etfs[0].ticker == "TSLY"
        assert "TSLA" in etfs[0].fund_name
        assert etfs[0].expense_ratio == Decimal("0.99")
        assert etfs[0].detail_page_url == "https://yieldmaxetfs.com/etfs/tsly"
        assert etfs[0].distribution_frequency == DistributionFrequency.UNKNOWN
        
        # 두 번째 ETF 검증
        assert etfs[1].ticker == "MSTY"
        assert "MSTR" in etfs[1].fund_name
        assert etfs[1].expense_ratio == Decimal("1.15")
        assert etfs[1].detail_page_url == "https://yieldmaxetfs.com/etfs/msty"
    
    @pytest.mark.asyncio
    async def test_parse_data_empty_table(self):
        """빈 테이블을 안전하게 처리하는지 테스트"""
        crawler = YieldmaxCrawler()
        
        mock_html = """
        <html>
            <div id="fundsTableWrap">
                <table>
                    <thead><tr><th>Ticker</th></tr></thead>
                    <tbody></tbody>
                </table>
            </div>
        </html>
        """
        
        etfs = await crawler.parse_data(mock_html)
        assert etfs == []
    
    @pytest.mark.asyncio
    async def test_parse_data_no_table(self):
        """테이블이 없는 HTML을 안전하게 처리하는지 테스트"""
        crawler = YieldmaxCrawler()
        
        mock_html = "<html><body>No table here</body></html>"
        
        etfs = await crawler.parse_data(mock_html)
        assert etfs == []


class TestYieldmaxCrawlerHelpers:
    """헬퍼 메서드 테스트"""
    
    def test_parse_expense_ratio(self):
        """Expense ratio 파싱 테스트"""
        crawler = YieldmaxCrawler()
        
        assert crawler._parse_expense_ratio("0.99%") == 0.99
        assert crawler._parse_expense_ratio("1.15%") == 1.15
        assert crawler._parse_expense_ratio("0.5%") == 0.5
        assert crawler._parse_expense_ratio("") is None
        assert crawler._parse_expense_ratio("N/A") is None
    
    def test_parse_aum(self):
        """AUM 파싱 테스트"""
        crawler = YieldmaxCrawler()
        
        # Billions
        assert crawler._parse_aum("$1.5B") == 1500.0
        assert crawler._parse_aum("$2B") == 2000.0
        
        # Millions
        assert crawler._parse_aum("$800M") == 800.0
        assert crawler._parse_aum("$1,200M") == 1200.0
        
        # Thousands
        assert crawler._parse_aum("$500K") == 0.5
        
        # Edge cases
        assert crawler._parse_aum("") is None
        assert crawler._parse_aum("N/A") is None
    
    def test_parse_inception_date(self):
        """Inception date 파싱 테스트"""
        crawler = YieldmaxCrawler()
        
        # MM/DD/YYYY 형식
        date1 = crawler._parse_inception_date("11/01/2022")
        assert date1 == datetime(2022, 11, 1)
        
        # YYYY-MM-DD 형식
        date2 = crawler._parse_inception_date("2023-03-15")
        assert date2 == datetime(2023, 3, 15)
        
        # 월 이름 형식
        date3 = crawler._parse_inception_date("Jan 15, 2023")
        assert date3 == datetime(2023, 1, 15)
        
        # Edge cases
        assert crawler._parse_inception_date("") is None
        assert crawler._parse_inception_date("Invalid") is None


@pytest.mark.integration
class TestYieldmaxCrawlerIntegration:
    """실제 API 통합 테스트"""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="JavaScript 렌더링 필요 - Playwright/Selenium 구현 후 활성화")
    async def test_fetch_and_parse_real_data(self):
        """
        실제 Yieldmax API에서 데이터를 가져와 파싱하는 통합 테스트
        
        Note: 현재는 JavaScript 렌더링이 필요하므로 skip 처리
        Playwright/Selenium 구현 후 활성화 필요
        """
        crawler = YieldmaxCrawler()
        
        html = await crawler.fetch_data()
        etfs = await crawler.parse_data(html)
        
        # 기본 검증
        assert len(etfs) > 0
        
        # 모든 ETF가 필수 필드를 가지고 있는지 확인
        for etf in etfs:
            assert etf.ticker
            assert etf.fund_name
            assert etf.distribution_frequency == DistributionFrequency.UNKNOWN
