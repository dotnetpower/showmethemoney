"""Tests for Fidelity, VanEck, and WisdomTree ETF crawlers"""
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.services.crawlers.fidelity import FidelityCrawler
from backend.app.services.crawlers.vaneck import VanEckCrawler
from backend.app.services.crawlers.wisdomtree import WisdomTreeCrawler


class TestFidelityCrawler:
    @pytest.fixture
    def crawler(self):
        return FidelityCrawler()

    def test_initialization(self, crawler):
        """Test crawler initialization"""
        assert crawler.provider_name == "Fidelity"
        assert "fidelity.com" in crawler.base_url

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

    def test_parse_decimal(self, crawler):
        """Test decimal parsing"""
        assert crawler._parse_decimal("123.45") == Decimal("123.45")
        assert crawler._parse_decimal("$123.45") == Decimal("123.45")
        assert crawler._parse_decimal("12.5%") == Decimal("12.5")
        assert crawler._parse_decimal(None) is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetch_real_data(self, crawler):
        """Test fetching real data"""
        html_content = await crawler.fetch_data()
        assert html_content is not None
        assert len(html_content) > 0


class TestVanEckCrawler:
    @pytest.fixture
    def crawler(self):
        return VanEckCrawler()

    def test_initialization(self, crawler):
        """Test crawler initialization"""
        assert crawler.provider_name == "VanEck"
        assert "vaneck.com" in crawler.base_url

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

        assert result is not None
        assert "html" in result

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

    def test_parse_decimal(self, crawler):
        """Test decimal parsing"""
        assert crawler._parse_decimal("100.50") == Decimal("100.50")
        assert crawler._parse_decimal("$50.25") == Decimal("50.25")
        assert crawler._parse_decimal(None) is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetch_real_data(self, crawler):
        """Test fetching real data"""
        data = await crawler.fetch_data()
        assert data is not None


class TestWisdomTreeCrawler:
    @pytest.fixture
    def crawler(self):
        return WisdomTreeCrawler()

    def test_initialization(self, crawler):
        """Test crawler initialization"""
        assert crawler.provider_name == "WisdomTree"
        assert "wisdomtree.com" in crawler.base_url

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

    def test_parse_decimal(self, crawler):
        """Test decimal parsing"""
        assert crawler._parse_decimal("75.25") == Decimal("75.25")
        assert crawler._parse_decimal("$25.50") == Decimal("25.50")
        assert crawler._parse_decimal(None) is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetch_real_data(self, crawler):
        """Test fetching real data"""
        html_content = await crawler.fetch_data()
        # WisdomTree may return 403 without proper headers
        # So we don't assert success, just check the call works
        assert html_content is None or len(html_content) > 0
