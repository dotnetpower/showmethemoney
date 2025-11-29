"""Goldman Sachs ETF 크롤러 테스트"""
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from app.models.etf import ETF, DistributionFrequency
from app.services.crawlers.goldmansachs import GoldmanSachsCrawler


class TestGoldmanSachsCrawlerInit:
    """초기화 테스트"""
    
    def test_base_url(self):
        """BASE_URL이 올바르게 설정되어 있는지 확인"""
        crawler = GoldmanSachsCrawler()
        assert crawler.BASE_URL == "https://am.gs.com/services/funds"


class TestGoldmanSachsCrawlerFetch:
    """데이터 가져오기 테스트"""
    
    @pytest.mark.asyncio
    async def test_fetch_data_success(self):
        """정상적으로 GraphQL API에서 데이터를 가져오는지 테스트"""
        crawler = GoldmanSachsCrawler()
        
        mock_response_data = {
            "data": {
                "fundData": {
                    "funds": [
                        {
                            "fundName": "Test ETF",
                            "fundType": "ETF",
                            "shareClasses": [{"ticker": "TEST"}]
                        }
                    ]
                }
            }
        }
        
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            result = await crawler.fetch_data()
            assert result == mock_response_data
            assert "data" in result
    
    @pytest.mark.asyncio
    async def test_fetch_data_http_error(self):
        """HTTP 오류 발생 시 예외가 발생하는지 테스트"""
        crawler = GoldmanSachsCrawler()
        
        with patch("httpx.AsyncClient.post", side_effect=httpx.HTTPStatusError(
            "404 Not Found",
            request=AsyncMock(),
            response=AsyncMock(status_code=404)
        )):
            with pytest.raises(httpx.HTTPStatusError):
                await crawler.fetch_data()


class TestGoldmanSachsCrawlerParse:
    """GraphQL 응답 파싱 테스트"""
    
    @pytest.mark.asyncio
    async def test_parse_data_with_mock_response(self):
        """모의 GraphQL 응답을 파싱하는지 테스트"""
        crawler = GoldmanSachsCrawler()
        
        mock_data = {
            "data": {
                "fundData": {
                    "funds": [
                        {
                            "fundName": "Goldman Sachs Access High Yield Corporate Bond ETF",
                            "fundType": "ETF",
                            "shareClasses": [
                                {
                                    "shareClassId": "381430453",
                                    "ticker": "GHYB",
                                    "shareClassInceptionDate": "2017-09-05",
                                    "baseCurrency": "USD",
                                    "distributionFrequency": "MONTHLY",
                                    "dailyPerformance": {
                                        "nav": {
                                            "asAtDate": "2025-11-26",
                                            "value": "45.46"
                                        },
                                        "shareClassNetAssets": {
                                            "asAtDate": "2025-11-26",
                                            "value": "93199045.86"
                                        }
                                    },
                                    "monthlyPerformance": {
                                        "asAtDate": "2025-10-31",
                                        "annualisedReturns1yr": "8.5",
                                        "annualisedReturns3yr": "3.2",
                                        "annualisedReturns5yr": "4.1"
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        etfs = await crawler.parse_data(mock_data)
        
        assert len(etfs) == 1
        
        etf = etfs[0]
        assert etf.ticker == "GHYB"
        assert "High Yield" in etf.fund_name
        assert etf.nav_amount == Decimal("45.46")
        assert etf.inception_date == date(2017, 9, 5)
        assert etf.distribution_frequency == DistributionFrequency.MONTHLY
        assert etf.one_year_return == Decimal("8.5")
        assert etf.three_year_return == Decimal("3.2")
        assert etf.five_year_return == Decimal("4.1")
        assert etf.detail_page_url and "GHYB" in etf.detail_page_url
    
    @pytest.mark.asyncio
    async def test_parse_data_filters_non_etf(self):
        """ETF가 아닌 펀드는 필터링하는지 테스트"""
        crawler = GoldmanSachsCrawler()
        
        mock_data = {
            "data": {
                "fundData": {
                    "funds": [
                        {
                            "fundName": "Mutual Fund",
                            "fundType": "MUTUAL_FUND",
                            "shareClasses": [{"ticker": "MFUND"}]
                        },
                        {
                            "fundName": "Test ETF",
                            "fundType": "ETF",
                            "shareClasses": [
                                {
                                    "ticker": "TETF",
                                    "shareClassInceptionDate": "2020-01-01",
                                    "dailyPerformance": {
                                        "nav": {"value": "50.00"}
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        etfs = await crawler.parse_data(mock_data)
        
        assert len(etfs) == 1
        assert etfs[0].ticker == "TETF"
    
    @pytest.mark.asyncio
    async def test_parse_data_empty_response(self):
        """빈 응답을 안전하게 처리하는지 테스트"""
        crawler = GoldmanSachsCrawler()
        
        empty_data = {"data": {"fundData": {"funds": []}}}
        
        etfs = await crawler.parse_data(empty_data)
        assert etfs == []


class TestGoldmanSachsCrawlerHelpers:
    """헬퍼 메서드 테스트"""
    
    def test_parse_date(self):
        """날짜 파싱 테스트"""
        crawler = GoldmanSachsCrawler()
        
        assert crawler._parse_date("2017-09-05") == date(2017, 9, 5)
        assert crawler._parse_date("2025-11-26") == date(2025, 11, 26)
        assert crawler._parse_date("") is None
        assert crawler._parse_date(None) is None
        assert crawler._parse_date("invalid") is None
    
    def test_parse_decimal(self):
        """Decimal 파싱 테스트"""
        crawler = GoldmanSachsCrawler()
        
        assert crawler._parse_decimal("45.46") == Decimal("45.46")
        assert crawler._parse_decimal("8.5") == Decimal("8.5")
        assert crawler._parse_decimal(100) == Decimal("100")
        assert crawler._parse_decimal(None) is None
    
    def test_map_distribution_frequency(self):
        """배당 빈도 매핑 테스트"""
        crawler = GoldmanSachsCrawler()
        
        assert crawler._map_distribution_frequency("MONTHLY") == DistributionFrequency.MONTHLY
        assert crawler._map_distribution_frequency("monthly") == DistributionFrequency.MONTHLY
        assert crawler._map_distribution_frequency("QUARTERLY") == DistributionFrequency.QUARTERLY
        assert crawler._map_distribution_frequency("SEMI-ANNUAL") == DistributionFrequency.SEMI_ANNUAL
        assert crawler._map_distribution_frequency("ANNUAL") == DistributionFrequency.ANNUAL
        assert crawler._map_distribution_frequency("WEEKLY") == DistributionFrequency.WEEKLY
        assert crawler._map_distribution_frequency("VARIABLE") == DistributionFrequency.VARIABLE
        assert crawler._map_distribution_frequency("NONE") == DistributionFrequency.NONE
        assert crawler._map_distribution_frequency("") == DistributionFrequency.UNKNOWN


@pytest.mark.integration
class TestGoldmanSachsCrawlerIntegration:
    """실제 API 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_fetch_and_parse_real_data(self):
        """실제 Goldman Sachs GraphQL API에서 데이터를 가져와 파싱하는 통합 테스트"""
        crawler = GoldmanSachsCrawler()
        
        # 실제 API 호출
        raw_data = await crawler.fetch_data()
        etfs = await crawler.parse_data(raw_data)
        
        # 기본 검증
        assert len(etfs) > 0
        
        # 모든 ETF가 필수 필드를 가지고 있는지 확인
        for etf in etfs:
            assert etf.ticker
            assert etf.fund_name
            assert etf.inception_date
            assert etf.nav_amount >= Decimal("0")
            assert etf.detail_page_url
