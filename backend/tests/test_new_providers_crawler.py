"""GraniteShares, Alpha Architect, Pacer Advisors ETF 크롤러 테스트"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.services.crawlers.alphaarchitect import AlphaArchitectCrawler
from backend.app.services.crawlers.graniteshares import GraniteSharesCrawler
from backend.app.services.crawlers.pacer import PacerCrawler


class TestGraniteSharesCrawler:
    """GraniteShares 크롤러 테스트"""

    @pytest.fixture
    def crawler(self):
        """크롤러 인스턴스 생성"""
        return GraniteSharesCrawler()

    @pytest.fixture
    def sample_html(self):
        """샘플 HTML 데이터"""
        return """
        <html>
            <body>
                <a href="/etf/BAR">GraniteShares Gold Trust</a>
                <a href="/etf/BBAR/">GraniteShares Gold Trust BAR</a>
                <a href="/etf/URA">GraniteShares Uranium Trust</a>
            </body>
        </html>
        """

    def test_initialization(self, crawler):
        """크롤러 초기화 테스트"""
        assert crawler.provider_name == "GraniteShares"

    @pytest.mark.asyncio
    async def test_fetch_data_success(self, crawler, sample_html, monkeypatch):
        """데이터 가져오기 성공 테스트"""
        mock_response = MagicMock()
        mock_response.text = sample_html
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        def mock_async_client(*args, **kwargs):
            return mock_client

        monkeypatch.setattr("httpx.AsyncClient", mock_async_client)

        result = await crawler.fetch_data()
        assert result == sample_html

    @pytest.mark.asyncio
    async def test_fetch_data_error(self, crawler, monkeypatch):
        """데이터 가져오기 실패 테스트"""
        import httpx

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(
            side_effect=httpx.HTTPError("Network error")
        )

        def mock_async_client(*args, **kwargs):
            return mock_client

        monkeypatch.setattr("httpx.AsyncClient", mock_async_client)

        with pytest.raises(httpx.HTTPError):
            await crawler.fetch_data()

    def test_parse_data_empty(self, crawler):
        """빈 데이터 파싱 테스트"""
        result = crawler.parse_data("")
        assert result == []

    def test_parse_data_success(self, crawler, sample_html):
        """데이터 파싱 성공 테스트"""
        etf_list = crawler.parse_data(sample_html)

        assert len(etf_list) == 3
        assert etf_list[0].ticker == "BAR"
        assert etf_list[1].ticker == "BBAR"
        assert etf_list[2].ticker == "URA"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_real_data(self, crawler):
        """실제 API 연동 테스트"""
        html = await crawler.fetch_data()
        assert html
        assert isinstance(html, str)


class TestAlphaArchitectCrawler:
    """Alpha Architect 크롤러 테스트"""

    @pytest.fixture
    def crawler(self):
        """크롤러 인스턴스 생성"""
        return AlphaArchitectCrawler()

    @pytest.fixture
    def sample_html(self):
        """샘플 HTML 데이터"""
        return """
        <html>
            <body>
                <a href="/fund/QVAL">Alpha Architect U.S. Quantitative Value ETF</a>
                <a href="/fund/IVAL/">Alpha Architect International Quantitative Value ETF</a>
                <a href="/etf/QMOM">Alpha Architect U.S. Quantitative Momentum ETF</a>
            </body>
        </html>
        """

    def test_initialization(self, crawler):
        """크롤러 초기화 테스트"""
        assert crawler.provider_name == "Alpha Architect"

    @pytest.mark.asyncio
    async def test_fetch_data_success(self, crawler, sample_html, monkeypatch):
        """데이터 가져오기 성공 테스트"""
        mock_response = MagicMock()
        mock_response.text = sample_html
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        def mock_async_client(*args, **kwargs):
            return mock_client

        monkeypatch.setattr("httpx.AsyncClient", mock_async_client)

        result = await crawler.fetch_data()
        assert result == sample_html

    @pytest.mark.asyncio
    async def test_fetch_data_error(self, crawler, monkeypatch):
        """데이터 가져오기 실패 테스트"""
        import httpx

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(
            side_effect=httpx.HTTPError("Network error")
        )

        def mock_async_client(*args, **kwargs):
            return mock_client

        monkeypatch.setattr("httpx.AsyncClient", mock_async_client)

        with pytest.raises(httpx.HTTPError):
            await crawler.fetch_data()

    def test_parse_data_empty(self, crawler):
        """빈 데이터 파싱 테스트"""
        result = crawler.parse_data("")
        assert result == []

    def test_parse_data_success(self, crawler, sample_html):
        """데이터 파싱 성공 테스트"""
        etf_list = crawler.parse_data(sample_html)

        assert len(etf_list) == 3
        assert etf_list[0].ticker == "QVAL"
        assert etf_list[1].ticker == "IVAL"
        assert etf_list[2].ticker == "QMOM"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_real_data(self, crawler):
        """실제 API 연동 테스트"""
        html = await crawler.fetch_data()
        assert html
        assert isinstance(html, str)


class TestPacerCrawler:
    """Pacer Advisors 크롤러 테스트"""

    @pytest.fixture
    def crawler(self):
        """크롤러 인스턴스 생성"""
        return PacerCrawler()

    @pytest.fixture
    def sample_html(self):
        """샘플 HTML 데이터"""
        return """
        <html>
            <body>
                <a href="/products/COWZ">Pacer US Cash Cows 100 ETF</a>
                <a href="/products/TPSC/">Pacer Trendpilot US Small Cap ETF</a>
                <a href="/products/VAMO">Pacer Valkyrie Global Asset Management ETF</a>
            </body>
        </html>
        """

    def test_initialization(self, crawler):
        """크롤러 초기화 테스트"""
        assert crawler.provider_name == "Pacer Advisors"

    @pytest.mark.asyncio
    async def test_fetch_data_success(self, crawler, sample_html, monkeypatch):
        """데이터 가져오기 성공 테스트"""
        mock_response = MagicMock()
        mock_response.text = sample_html
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

        def mock_async_client(*args, **kwargs):
            return mock_client

        monkeypatch.setattr("httpx.AsyncClient", mock_async_client)

        result = await crawler.fetch_data()
        assert result == sample_html

    @pytest.mark.asyncio
    async def test_fetch_data_error(self, crawler, monkeypatch):
        """데이터 가져오기 실패 테스트"""
        import httpx

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = AsyncMock(
            side_effect=httpx.HTTPError("Network error")
        )

        def mock_async_client(*args, **kwargs):
            return mock_client

        monkeypatch.setattr("httpx.AsyncClient", mock_async_client)

        with pytest.raises(httpx.HTTPError):
            await crawler.fetch_data()

    def test_parse_data_empty(self, crawler):
        """빈 데이터 파싱 테스트"""
        result = crawler.parse_data("")
        assert result == []

    def test_parse_data_success(self, crawler, sample_html):
        """데이터 파싱 성공 테스트"""
        etf_list = crawler.parse_data(sample_html)

        assert len(etf_list) == 3
        assert etf_list[0].ticker == "COWZ"
        assert etf_list[1].ticker == "TPSC"
        assert etf_list[2].ticker == "VAMO"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_real_data(self, crawler):
        """실제 API 연동 테스트"""
        html = await crawler.fetch_data()
        assert html
        assert isinstance(html, str)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_parse_real_data(self, crawler):
        """실제 데이터 파싱 테스트"""
        html = await crawler.fetch_data()
        etf_list = crawler.parse_data(html)

        assert len(etf_list) > 0
        for etf in etf_list:
            assert etf.ticker
            assert etf.fund_name
            assert len(etf.ticker) <= 5
            assert etf.ticker.isalpha()
            assert etf.ticker.isupper()

