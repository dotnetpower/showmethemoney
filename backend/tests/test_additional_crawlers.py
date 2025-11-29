"""Tests for Global X, Direxion, and PIMCO ETF crawlers"""
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.services.crawlers.direxion import DirexionCrawler
from backend.app.services.crawlers.globalx import GlobalXCrawler
from backend.app.services.crawlers.pimco import PIMCOCrawler


class TestGlobalXCrawler:
    @pytest.fixture
    def crawler(self):
        return GlobalXCrawler()

    def test_initialization(self, crawler):
        """Test crawler initialization"""
        assert crawler.provider_name == "GlobalX"
        assert "globalxetfs.com" in crawler.base_url

    @pytest.mark.asyncio
    async def test_fetch_data_success(self, crawler):
        """Test successful data fetching"""
        mock_response = AsyncMock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.raise_for_status = AsyncMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await crawler.fetch_data()

        assert result == "<html><body>Test</body></html>"

    @pytest.mark.asyncio
    async def test_fetch_data_error(self, crawler):
        """Test data fetching with error"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(side_effect=Exception("Network error"))
            mock_client.return_value.__aenter__.return_value.get = mock_get
            result = await crawler.fetch_data()

        assert result is None

    def test_parse_data_empty(self, crawler):
        """Test parsing empty data"""
        result = crawler.parse_data("")
        assert result == []

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetch_real_data(self, crawler):
        """Test fetching real data"""
        html_content = await crawler.fetch_data()
        assert html_content is not None
        assert len(html_content) > 0


class TestDirexionCrawler:
    @pytest.fixture
    def crawler(self):
        return DirexionCrawler()

    def test_initialization(self, crawler):
        """Test crawler initialization"""
        assert crawler.provider_name == "Direxion"
        assert "direxion.com" in crawler.base_url

    @pytest.mark.asyncio
    async def test_fetch_data_success(self, crawler):
        """Test successful data fetching"""
        mock_response = AsyncMock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.raise_for_status = AsyncMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await crawler.fetch_data()

        assert result == "<html><body>Test</body></html>"

    @pytest.mark.asyncio
    async def test_fetch_data_error(self, crawler):
        """Test data fetching with error"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(side_effect=Exception("Network error"))
            mock_client.return_value.__aenter__.return_value.get = mock_get
            result = await crawler.fetch_data()

        assert result is None

    def test_parse_data_empty(self, crawler):
        """Test parsing empty data"""
        result = crawler.parse_data("")
        assert result == []

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetch_real_data(self, crawler):
        """Test fetching real data"""
        html_content = await crawler.fetch_data()
        # Direxion may return 403, so we don't assert success
        assert html_content is None or len(html_content) > 0


class TestPIMCOCrawler:
    @pytest.fixture
    def crawler(self):
        return PIMCOCrawler()

    @pytest.fixture
    def sample_response(self):
        """Sample API response"""
        return {
            "asOfDate": "2024-01-01",
            "data": [
                {
                    "Ticker": "MINT",
                    "Name": "PIMCO Enhanced Short Maturity Active ETF",
                    "Vehicle": "ETF",
                    "Investment Vehicle Two": "ETF",
                    "Share Class Inception Date": "2009-11-16",
                    "Net Expense Ratio %2": 0.35,
                    "Gross Expense Ratio %": 0.36,
                },
                {
                    "Ticker": "ZROZ",
                    "Name": "PIMCO 25+ Year Zero Coupon US Treasury ETF",
                    "Vehicle": "ETF",
                    "Share Class Inception Date": "2010-10-04",
                    "Net Expense Ratio %2": 0.15,
                },
            ],
        }

    def test_initialization(self, crawler):
        """Test crawler initialization"""
        assert crawler.provider_name == "PIMCO"
        assert "pimco.com" in crawler.api_url

    @pytest.mark.asyncio
    async def test_fetch_data_success(self, crawler):
        """Test successful data fetching"""
        mock_response = AsyncMock()
        mock_response.json = lambda: {"data": []}
        mock_response.raise_for_status = AsyncMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await crawler.fetch_data()

        assert result == {"data": []}

    @pytest.mark.asyncio
    async def test_fetch_data_error(self, crawler):
        """Test data fetching with error"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(side_effect=Exception("Network error"))
            mock_client.return_value.__aenter__.return_value.get = mock_get
            result = await crawler.fetch_data()

        assert result is None

    def test_parse_data_empty(self, crawler):
        """Test parsing empty data"""
        result = crawler.parse_data(None)
        assert result == []

        result = crawler.parse_data({})
        assert result == []

    def test_parse_data_success(self, crawler, sample_response):
        """Test parsing valid data"""
        result = crawler.parse_data(sample_response)

        assert len(result) == 2

        # Check MINT
        mint = next((etf for etf in result if etf["ticker"] == "MINT"), None)
        assert mint is not None
        assert "Enhanced Short Maturity" in mint["name"]
        assert mint["inception_date"] == date(2009, 11, 16)
        assert mint["expense_ratio"] == Decimal("0.35")

        # Check ZROZ
        zroz = next((etf for etf in result if etf["ticker"] == "ZROZ"), None)
        assert zroz is not None
        assert "25+ Year" in zroz["name"]
        assert zroz["inception_date"] == date(2010, 10, 4)

    def test_parse_date(self, crawler):
        """Test date parsing"""
        assert crawler._parse_date("2009-11-16") == date(2009, 11, 16)
        assert crawler._parse_date("2010-10-04") == date(2010, 10, 4)
        assert crawler._parse_date(None) is None
        assert crawler._parse_date("invalid") is None

    def test_parse_decimal(self, crawler):
        """Test decimal parsing"""
        assert crawler._parse_decimal(0.35) == Decimal("0.35")
        assert crawler._parse_decimal("0.15") == Decimal("0.15")
        assert crawler._parse_decimal(None) is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetch_real_data(self, crawler):
        """Test fetching real data"""
        data = await crawler.fetch_data()
        assert data is not None
        assert "data" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_parse_real_data(self, crawler):
        """Test parsing real data"""
        data = await crawler.fetch_data()
        etfs = crawler.parse_data(data)

        print(f"\nFound {len(etfs)} ETFs from PIMCO")

        # Check for known ETFs
        if etfs:
            tickers = [etf["ticker"] for etf in etfs]
            print(f"Sample tickers: {tickers[:10]}")

            # Verify data structure
            for etf in etfs[:3]:
                assert "ticker" in etf
                assert "name" in etf
                assert etf["ticker"]
                assert etf["name"]
                print(f"ETF: {etf['ticker']} - {etf['name']}")
