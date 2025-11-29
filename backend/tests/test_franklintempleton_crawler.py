"""Franklin Templeton ETF 크롤러 테스트"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.services.crawlers.franklintempleton import \
    FranklinTempletonCrawler


class TestFranklinTempletonCrawler:
    """Franklin Templeton 크롤러 테스트"""

    @pytest.fixture
    def crawler(self):
        """크롤러 인스턴스 생성"""
        return FranklinTempletonCrawler()

    @pytest.fixture
    def sample_response(self):
        """샘플 응답 데이터"""
        return {
            "data": {
                "PPSS": [
                    {
                        "fundid": "001",
                        "fundname": "Franklin U.S. Core Bond ETF",
                        "shareclass": [
                            {"identifiers": {"ticker": "FLCB"}},
                        ],
                    },
                    {
                        "fundid": "002",
                        "fundname": "Franklin International Core Dividend Tilt Index ETF",
                        "shareclass": [
                            {"identifiers": {"ticker": "FIDI"}},
                        ],
                    },
                ]
            }
        }

    def test_initialization(self, crawler):
        """크롤러 초기화 테스트"""
        assert crawler.provider_name == "Franklin Templeton"

    @pytest.mark.asyncio
    async def test_fetch_data_success(self, crawler, sample_response, monkeypatch):
        """데이터 가져오기 성공 테스트"""
        mock_response = MagicMock()
        mock_response.json = lambda: sample_response
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        def mock_async_client(*args, **kwargs):
            return mock_client

        monkeypatch.setattr("httpx.AsyncClient", mock_async_client)

        result = await crawler.fetch_data()
        assert result == sample_response

    @pytest.mark.asyncio
    async def test_fetch_data_error(self, crawler, monkeypatch):
        """데이터 가져오기 실패 테스트"""
        import httpx

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = AsyncMock(
            side_effect=httpx.HTTPError("Network error")
        )

        def mock_async_client(*args, **kwargs):
            return mock_client

        monkeypatch.setattr("httpx.AsyncClient", mock_async_client)

        with pytest.raises(httpx.HTTPError):
            await crawler.fetch_data()

    def test_parse_data_empty(self, crawler):
        """빈 데이터 파싱 테스트"""
        result = crawler.parse_data({})
        assert result == []

    def test_parse_data_success(self, crawler, sample_response):
        """데이터 파싱 성공 테스트"""
        etf_list = crawler.parse_data(sample_response)

        assert len(etf_list) == 2
        assert etf_list[0].ticker == "FLCB"
        assert etf_list[0].fund_name == "Franklin U.S. Core Bond ETF"
        assert etf_list[1].ticker == "FIDI"
        assert (
            etf_list[1].fund_name == "Franklin International Core Dividend Tilt Index ETF"
        )

    def test_parse_data_invalid_ticker(self, crawler):
        """잘못된 티커 필터링 테스트"""
        data = {
            "data": {
                "PPSS": [
                    {
                        "fundid": "001",
                        "fundname": "Test Fund",
                        "shareclass": [
                            {"identifiers": {"ticker": "TOOLONG"}},  # 6자 이상
                        ],
                    },
                    {
                        "fundid": "002",
                        "fundname": "Test Fund 2",
                        "shareclass": [
                            {"identifiers": {"ticker": "ABC123"}},  # 숫자 포함
                        ],
                    },
                ]
            }
        }

        etf_list = crawler.parse_data(data)
        assert len(etf_list) == 0

    def test_parse_data_missing_ticker(self, crawler):
        """티커 없는 데이터 처리 테스트"""
        data = {
            "data": {
                "PPSS": [
                    {
                        "fundid": "001",
                        "fundname": "Test Fund",
                        "shareclass": [
                            {"identifiers": {}},  # ticker 없음
                        ],
                    },
                ]
            }
        }

        etf_list = crawler.parse_data(data)
        assert len(etf_list) == 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_real_data(self, crawler):
        """실제 API 연동 테스트"""
        data = await crawler.fetch_data()
        assert "data" in data
        assert "PPSS" in data["data"]
        assert isinstance(data["data"]["PPSS"], list)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_parse_real_data(self, crawler):
        """실제 데이터 파싱 테스트"""
        data = await crawler.fetch_data()
        etf_list = crawler.parse_data(data)

        assert len(etf_list) > 0
        for etf in etf_list:
            assert etf.ticker
            assert etf.fund_name
            assert len(etf.ticker) <= 5
            assert etf.ticker.isalpha()
            assert etf.ticker.isupper()
