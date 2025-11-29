"""Tests for First Trust ETF crawler"""
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.services.crawlers.firsttrust import FirstTrustCrawler


class TestFirstTrustCrawler:
    @pytest.fixture
    def crawler(self):
        return FirstTrustCrawler()

    @pytest.fixture
    def sample_html(self):
        """Sample HTML with ETF data"""
        return """
        <html>
        <body>
            <table>
                <tr>
                    <td>Fund Name</td>
                    <td>TickerSymbol</td>
                    <td>InceptionDate</td>
                    <td>CloseNAV</td>
                    <td>30-DaySEC Yield1</td>
                    <td>YieldAs OfDate</td>
                </tr>
                <tr>
                    <td>First Trust Alternative Absolute Return Strategy ETF</td>
                    <td><a href="/Retail/etf/etfsummary.aspx?Ticker=FAAR">FAAR</a></td>
                    <td>05/18/16</td>
                    <td>$30.12</td>
                    <td>2.31%</td>
                    <td>10/31/25</td>
                </tr>
                <tr>
                    <td>First Trust Cloud Computing ETF</td>
                    <td><a href="/Retail/etf/etfsummary.aspx?Ticker=SKYY">SKYY</a></td>
                    <td>07/05/11</td>
                    <td>$127.79</td>
                    <td>-------</td>
                    <td>10/31/25</td>
                </tr>
                <tr>
                    <td>First Trust Dow Jones Internet Index Fund</td>
                    <td><a href="/Retail/etf/etfsummary.aspx?Ticker=FDN">FDN</a></td>
                    <td>06/19/06</td>
                    <td>$266.88</td>
                    <td>-------</td>
                    <td>10/31/25</td>
                </tr>
            </table>
        </body>
        </html>
        """

    def test_initialization(self, crawler):
        """Test crawler initialization"""
        assert crawler.provider_name == "FirstTrust"
        assert "ftportfolios.com" in crawler.base_url
        assert "etflist.aspx" in crawler.etf_list_url

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
        """Test data fetching with HTTP error"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(side_effect=Exception("Network error"))
            mock_client.return_value.__aenter__.return_value.get = mock_get
            result = await crawler.fetch_data()

        assert result is None

    def test_parse_data_empty(self, crawler):
        """Test parsing empty data"""
        result = crawler.parse_data("")
        assert result == []

        result = crawler.parse_data(None)
        assert result == []

    def test_parse_data_success(self, crawler, sample_html):
        """Test parsing valid HTML data"""
        result = crawler.parse_data(sample_html)

        assert len(result) == 3

        # Check FAAR
        faar = next((etf for etf in result if etf["ticker"] == "FAAR"), None)
        assert faar is not None
        assert faar["name"] == "First Trust Alternative Absolute Return Strategy ETF"
        assert faar["inception_date"] == date(2016, 5, 18)
        assert faar["nav"] == Decimal("30.12")
        assert faar["expense_ratio"] == Decimal("2.31")
        assert "/etfsummary.aspx?Ticker=FAAR" in faar["detail_url"]

        # Check SKYY
        skyy = next((etf for etf in result if etf["ticker"] == "SKYY"), None)
        assert skyy is not None
        assert "Cloud Computing" in skyy["name"]
        assert skyy["inception_date"] == date(2011, 7, 5)
        assert skyy["nav"] == Decimal("127.79")
        assert skyy["expense_ratio"] is None  # No SEC yield

        # Check FDN
        fdn = next((etf for etf in result if etf["ticker"] == "FDN"), None)
        assert fdn is not None
        assert "Internet" in fdn["name"]
        assert fdn["inception_date"] == date(2006, 6, 19)
        assert fdn["nav"] == Decimal("266.88")

    def test_is_etf_table(self, crawler):
        """Test ETF table identification"""
        # Valid headers
        headers = ["Fund Name", "TickerSymbol", "InceptionDate", "NAV"]
        assert crawler._is_etf_table(headers) is True

        # Invalid headers (missing required fields)
        headers = ["Column1", "Column2"]
        assert crawler._is_etf_table(headers) is False

    def test_find_column_index(self, crawler):
        """Test finding column index by name"""
        headers = ["Fund Name", "TickerSymbol", "InceptionDate"]

        assert crawler._find_column_index(headers, "ticker") == 1
        assert crawler._find_column_index(headers, "fund") == 0
        assert crawler._find_column_index(headers, "inception") == 2
        assert crawler._find_column_index(headers, "nonexistent") is None

    def test_parse_date(self, crawler):
        """Test date parsing"""
        assert crawler._parse_date("05/18/16") == date(2016, 5, 18)
        assert crawler._parse_date("07/05/11") == date(2011, 7, 5)
        assert crawler._parse_date("-------") is None
        assert crawler._parse_date("") is None
        assert crawler._parse_date("invalid") is None

    def test_parse_price(self, crawler):
        """Test price parsing"""
        assert crawler._parse_price("$30.12") == Decimal("30.12")
        assert crawler._parse_price("$127.79") == Decimal("127.79")
        assert crawler._parse_price("$1,234.56") == Decimal("1234.56")
        assert crawler._parse_price("-------") is None
        assert crawler._parse_price("") is None
        assert crawler._parse_price("invalid") is None

    def test_parse_percentage(self, crawler):
        """Test percentage parsing"""
        assert crawler._parse_percentage("2.31%") == Decimal("2.31")
        assert crawler._parse_percentage("0.99%") == Decimal("0.99")
        assert crawler._parse_percentage("-------") is None
        assert crawler._parse_percentage("") is None
        assert crawler._parse_percentage("invalid") is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetch_real_data(self, crawler):
        """Test fetching real data from First Trust"""
        html_content = await crawler.fetch_data()
        assert html_content is not None
        assert len(html_content) > 0
        assert "ftportfolios" in html_content.lower() or "first trust" in html_content.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_parse_real_data(self, crawler):
        """Test parsing real data from First Trust"""
        html_content = await crawler.fetch_data()
        etfs = crawler.parse_data(html_content)

        assert len(etfs) > 0
        print(f"\nFound {len(etfs)} ETFs from First Trust")

        # Check for known ETFs
        tickers = [etf["ticker"] for etf in etfs]
        print(f"Sample tickers: {tickers[:10]}")

        known_etfs = ["FDN", "SKYY", "FAAR"]
        for ticker in known_etfs:
            assert ticker in tickers, f"{ticker} not found in results"

        # Verify data structure
        for etf in etfs[:5]:
            assert "ticker" in etf
            assert "name" in etf
            assert etf["ticker"]
            assert etf["name"]
            print(f"ETF: {etf['ticker']} - {etf['name']}")
