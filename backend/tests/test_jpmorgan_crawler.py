"""JPMorgan 크롤러 테스트"""
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.etf import ETF
from app.services.crawlers.jpmorgan import JPMorganCrawler


@pytest.fixture
def sample_jpmorgan_response():
    """JPMorgan API 응답 샘플 데이터"""
    return [
        {
            "name": "JPMorgan Equity Premium Income ETF",
            "displayName": "Equity Premium Income ETF",
            "displayId": "JEPI",
            "ticker": "JEPI",
            "identifier": "46641Q332",
            "assetClass": "U.S. Equity",
            "fundInceptionDate": "2020-05-20",
            "shareClassInceptionDate": "2020-05-20",
            "nav": 57.88329363,
            "navDate": "2025-11-28",
            "secYield": 0.0724,
            "secYieldEffectiveDate": "2025-10-31",
            "atNavPerformanceReturn": {
                "ytd": 0.0528,
                "mt1": 0.0021,
                "mt3": 0.0266,
                "mt6": 0.0692,
                "yr1": 0.0527,
                "yr2": None,
                "yr3": 0.1033,
                "yr5": 0.1093,
                "yr10": None,
                "inception": 0.1147
            },
            "currencyCode": "USD"
        },
        {
            "name": "JPMorgan Ultra-Short Income ETF",
            "displayName": "Ultra-Short Income ETF",
            "displayId": "JPST",
            "ticker": "JPST",
            "identifier": "46641Q878",
            "assetClass": "Taxable Bond",
            "fundInceptionDate": "2017-05-17",
            "shareClassInceptionDate": "2017-05-17",
            "nav": 50.48,
            "navDate": "2025-11-28",
            "secYield": 0.0467,
            "atNavPerformanceReturn": {
                "ytd": 0.0436,
                "yr1": 0.0477,
                "yr3": 0.0273,
                "yr5": 0.0233,
                "inception": 0.0241
            },
            "currencyCode": "USD"
        },
        {
            "name": "JPMorgan BetaBuilders U.S. Equity ETF",
            "displayName": "BetaBuilders U.S. Equity ETF",
            "displayId": "BBUS",
            "ticker": "BBUS",
            "identifier": "46641Q761",
            "assetClass": "U.S. Equity",
            "nav": 108.52,
            "navDate": "2025-11-28",
            "atNavPerformanceReturn": {
                "ytd": 0.2645,
                "yr1": 0.3287,
                "yr3": 0.1019,
                "yr5": 0.1687,
                "inception": 0.1448
            },
            "currencyCode": "USD"
        }
    ]


@pytest.fixture
def crawler():
    """JPMorganCrawler 인스턴스"""
    return JPMorganCrawler()


class TestJPMorganCrawler:
    """JPMorganCrawler 테스트"""
    
    def test_crawler_initialization(self, crawler):
        """크롤러 초기화 테스트"""
        assert crawler.get_provider_name() == "JPMorgan"
        assert "jpmorgan.com" in crawler.BASE_URL
        assert crawler.PARAMS['country'] == 'us'
        assert crawler.PARAMS['fundType'] == 'etf'
    
    def test_parse_date_iso_format(self, crawler):
        """ISO 형식 날짜 파싱 테스트"""
        result = crawler._parse_date("2020-05-20")
        assert result == date(2020, 5, 20)
        
        result2 = crawler._parse_date("2017-05-17")
        assert result2 == date(2017, 5, 17)
    
    def test_parse_date_invalid(self, crawler):
        """잘못된 날짜 파싱 테스트"""
        assert crawler._parse_date(None) is None
        assert crawler._parse_date("") is None
        assert crawler._parse_date("invalid") is None
    
    def test_extract_return_value(self, crawler):
        """수익률 값 추출 테스트"""
        performance = {"ytd": 0.0528, "yr1": 0.0527, "yr3": 0.1033}
        
        # 0.0528 -> 5.28%
        assert crawler._extract_return_value(performance, 'ytd') == Decimal("5.28")
        assert crawler._extract_return_value(performance, 'yr1') == Decimal("5.27")
        assert crawler._extract_return_value(performance, 'yr3') == Decimal("10.33")
        
        # None 값
        assert crawler._extract_return_value(performance, 'yr10') is None
        assert crawler._extract_return_value(None, 'ytd') is None
    
    def test_extract_etf_data_full(self, crawler, sample_jpmorgan_response):
        """전체 정보가 있는 ETF 데이터 추출 테스트"""
        fund = sample_jpmorgan_response[0]
        etf = crawler._extract_etf_data(fund)
        
        assert etf is not None
        assert etf.ticker == "JEPI"
        assert etf.fund_name == "JPMorgan Equity Premium Income ETF"
        assert etf.cusip == "46641Q332"
        assert etf.isin == "N/A"  # API에서 제공 안 함
        assert etf.inception_date == date(2020, 5, 20)
        assert etf.nav_amount == Decimal("57.88329363")
        assert etf.nav_as_of == date(2025, 11, 28)
        assert etf.asset_class == "U.S. Equity"
        assert etf.ytd_return == Decimal("5.28")
        assert etf.one_year_return == Decimal("5.27")
        assert etf.three_year_return == Decimal("10.33")
        assert etf.five_year_return == Decimal("10.93")
        assert etf.since_inception_return == Decimal("11.47")
        assert "jpmorgan.com" in etf.product_page_url
    
    def test_extract_etf_data_bond(self, crawler, sample_jpmorgan_response):
        """채권 ETF 데이터 추출 테스트"""
        fund = sample_jpmorgan_response[1]
        etf = crawler._extract_etf_data(fund)
        
        assert etf is not None
        assert etf.ticker == "JPST"
        assert etf.fund_name == "JPMorgan Ultra-Short Income ETF"
        assert etf.asset_class == "Taxable Bond"
        assert etf.nav_amount == Decimal("50.48")
        assert etf.ytd_return == Decimal("4.36")
    
    def test_extract_etf_data_minimal(self, crawler, sample_jpmorgan_response):
        """최소 정보 ETF 데이터 추출 테스트"""
        fund = sample_jpmorgan_response[2]
        etf = crawler._extract_etf_data(fund)
        
        assert etf is not None
        assert etf.ticker == "BBUS"
        assert etf.fund_name == "JPMorgan BetaBuilders U.S. Equity ETF"
        assert etf.inception_date is None  # fundInceptionDate 없음
        assert etf.ytd_return == Decimal("26.45")
        assert etf.one_year_return == Decimal("32.87")
    
    def test_extract_etf_data_no_ticker(self, crawler):
        """티커 없는 펀드 테스트"""
        fund = {
            "name": "Some Fund",
            "displayName": "Some Fund"
        }
        etf = crawler._extract_etf_data(fund)
        assert etf is None
    
    def test_extract_etf_data_invalid_nav(self, crawler):
        """잘못된 NAV 처리 테스트"""
        fund = {
            "ticker": "TEST",
            "name": "Test Fund",
            "nav": "invalid",
            "assetClass": "U.S. Equity"
        }
        etf = crawler._extract_etf_data(fund)
        assert etf is not None
        assert etf.nav_amount == Decimal("0.00")
    
    def test_extract_etf_data_null_returns(self, crawler):
        """null 수익률 처리 테스트"""
        fund = {
            "ticker": "TEST",
            "name": "Test Fund",
            "assetClass": "U.S. Equity",
            "atNavPerformanceReturn": {
                "ytd": None,
                "yr1": None,
                "yr3": None,
                "yr5": None,
                "yr10": None,
                "inception": None
            }
        }
        etf = crawler._extract_etf_data(fund)
        assert etf is not None
        assert etf.ytd_return is None
        assert etf.one_year_return is None
        assert etf.three_year_return is None
    
    @pytest.mark.asyncio
    async def test_fetch_data_mock(self, crawler, sample_jpmorgan_response):
        """fetch_data 메서드 테스트 (Mock)"""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_jpmorgan_response
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            data = await crawler.fetch_data()
            
            assert data == sample_jpmorgan_response
            assert len(data) == 3
    
    @pytest.mark.asyncio
    async def test_parse_data(self, crawler, sample_jpmorgan_response):
        """parse_data 메서드 테스트"""
        etf_list = await crawler.parse_data(sample_jpmorgan_response)
        
        assert len(etf_list) == 3
        
        # 첫 번째 ETF 검증
        assert etf_list[0].ticker == "JEPI"
        assert etf_list[0].asset_class == "U.S. Equity"
        
        # 두 번째 ETF 검증
        assert etf_list[1].ticker == "JPST"
        assert etf_list[1].asset_class == "Taxable Bond"
        
        # 세 번째 ETF 검증
        assert etf_list[2].ticker == "BBUS"
        assert etf_list[2].ytd_return == Decimal("26.45")
    
    @pytest.mark.asyncio
    async def test_parse_data_invalid_input(self, crawler):
        """잘못된 입력 데이터 파싱 테스트"""
        etf_list = await crawler.parse_data({})
        assert len(etf_list) == 0
        
        etf_list2 = await crawler.parse_data(None)
        assert len(etf_list2) == 0
    
    @pytest.mark.asyncio
    async def test_crawl_integration_mock(self, crawler, sample_jpmorgan_response):
        """전체 크롤링 프로세스 통합 테스트 (Mock)"""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_jpmorgan_response
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            etf_list = await crawler.crawl()
            
            assert len(etf_list) == 3
            assert all(isinstance(etf, ETF) for etf in etf_list)
            assert all(etf.ticker for etf in etf_list)


class TestJPMorganCrawlerIntegration:
    """실제 API 호출 통합 테스트"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_real_data(self, crawler):
        """실제 JPMorgan API에서 데이터 가져오기 테스트"""
        data = await crawler.fetch_data()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # 첫 번째 항목이 예상 구조인지 확인
        first_item = data[0]
        assert 'ticker' in first_item
        assert 'name' in first_item
    
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
        assert "JPMorgan" in first_etf.fund_name
        assert first_etf.cusip != "N/A"
        assert first_etf.product_page_url.startswith("https://")
        
        # 모든 ETF가 올바른 형식인지 확인
        for etf in etf_list:
            assert isinstance(etf, ETF)
            assert etf.ticker
            assert len(etf.ticker) <= 5
            assert etf.cusip != "N/A"
        
        # 알려진 JPMorgan ETF가 포함되어 있는지 확인
        tickers = [etf.ticker for etf in etf_list]
        known_etfs = ["JEPI", "JPST", "JEPQ", "BBUS"]
        assert any(ticker in tickers for ticker in known_etfs)
        
        print(f"\nTotal JPMorgan ETFs found: {len(etf_list)}")
        print(f"Sample tickers: {tickers[:10]}")
