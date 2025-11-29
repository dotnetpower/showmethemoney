"""SPDR 크롤러 테스트"""
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.etf import ETF
from app.services.crawlers.spdr import SPDRCrawler


@pytest.fixture
def sample_spdr_response():
    """SPDR API 응답 샘플 데이터"""
    return {
        "data": {
            "fundType": [
                {
                    "key": "etfs",
                    "name": "ETFs",
                    "size": 176
                }
            ],
            "funds": {
                "etfs": {
                    "datas": [
                        {
                            "domicile": "US",
                            "fundName": "SPDR® S&P 500® ETF Trust",
                            "fundTicker": "SPY",
                            "fundUri": "/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy",
                            "ter": ["0.09%", 0.09],
                            "nav": ["$585.25", 585.25],
                            "aum": ["$575,000.00 M", 575000.0],
                            "asOfDate": ["Nov 26 2025", "2025-11-26"],
                            "ytd": ["25.50%", 25.50],
                            "yr1": ["30.25%", 30.25],
                            "yr3": ["18.50%", 18.50],
                            "yr5": ["16.75%", 16.75],
                            "yr10": ["14.25%", 14.25],
                            "sinceInception": ["10.50%", 10.50],
                            "inceptionDate": ["Jan 22 1993", "1993-01-22"]
                        },
                        {
                            "domicile": "US",
                            "fundName": "SPDR® Bloomberg Emerging Markets Local Bond ETF",
                            "fundTicker": "EBND",
                            "fundUri": "/us/en/intermediary/etfs/spdr-bloomberg-emerging-markets-local-bond-etf-ebnd",
                            "ter": ["0.30%", 0.30],
                            "nav": ["$21.27", 21.27],
                            "aum": ["$2,218.02 M", 2218.02],
                            "asOfDate": ["Nov 26 2025", "2025-11-26"],
                            "ytd": ["13.05%", 13.05],
                            "yr1": ["10.94%", 10.94],
                            "yr3": ["9.94%", 9.94],
                            "yr5": ["0.67%", 0.67],
                            "yr10": ["2.06%", 2.06],
                            "sinceInception": ["0.96%", 0.96],
                            "inceptionDate": ["Feb 23 2011", "2011-02-23"]
                        },
                        {
                            "domicile": "US",
                            "fundName": "SPDR® Portfolio S&P 500 ETF",
                            "fundTicker": "SPLG",
                            "fundUri": "/us/en/intermediary/etfs/spdr-portfolio-sp-500-etf-splg",
                            "ter": ["0.02%", 0.02],
                            "nav": ["$71.50", 71.50],
                            "asOfDate": ["Nov 26 2025", "2025-11-26"],
                            "inceptionDate": ["Nov 08 2005", "2005-11-08"]
                        }
                    ]
                }
            }
        },
        "msg": "success",
        "status": 200
    }


@pytest.fixture
def crawler():
    """SPDRCrawler 인스턴스"""
    return SPDRCrawler()


class TestSPDRCrawler:
    """SPDRCrawler 테스트"""
    
    def test_crawler_initialization(self, crawler):
        """크롤러 초기화 테스트"""
        assert crawler.get_provider_name() == "SPDR"
        assert "ssga.com" in crawler.BASE_URL
        assert crawler.PARAMS['country'] == 'us'
    
    def test_parse_date_iso_format(self, crawler):
        """ISO 형식 날짜 파싱 테스트"""
        result = crawler._parse_date("2011-02-23")
        assert result == date(2011, 2, 23)
    
    def test_parse_date_text_format(self, crawler):
        """텍스트 형식 날짜 파싱 테스트"""
        result = crawler._parse_date("Feb 23 2011")
        assert result == date(2011, 2, 23)
        
        result2 = crawler._parse_date("Jan 22 1993")
        assert result2 == date(1993, 1, 22)
    
    def test_parse_date_invalid(self, crawler):
        """잘못된 날짜 파싱 테스트"""
        assert crawler._parse_date(None) is None
        assert crawler._parse_date("") is None
        assert crawler._parse_date("invalid") is None
    
    def test_extract_value_from_list(self, crawler):
        """리스트에서 값 추출 테스트"""
        result = crawler._extract_value(["$585.25", 585.25])
        assert result == Decimal("585.25")
        
        result2 = crawler._extract_value(["0.09%", 0.09])
        assert result2 == Decimal("0.09")
    
    def test_extract_value_from_single(self, crawler):
        """단일 값 추출 테스트"""
        result = crawler._extract_value(100.5)
        assert result == Decimal("100.5")
        
        result2 = crawler._extract_value("50.25")
        assert result2 == Decimal("50.25")
    
    def test_extract_value_none(self, crawler):
        """None 값 처리 테스트"""
        assert crawler._extract_value(None) is None
        assert crawler._extract_value([]) is None
    
    def test_extract_etf_data_full(self, crawler, sample_spdr_response):
        """전체 정보가 있는 ETF 데이터 추출 테스트"""
        fund_data = sample_spdr_response['data']['funds']['etfs']['datas'][0]
        etf = crawler._extract_etf_data(fund_data)
        
        assert etf is not None
        assert etf.ticker == "SPY"
        assert etf.fund_name == "SPDR® S&P 500® ETF Trust"
        assert etf.inception_date == date(1993, 1, 22)
        assert etf.nav_amount == Decimal("585.25")
        assert etf.nav_as_of == date(2025, 11, 26)
        assert etf.expense_ratio == Decimal("0.09")
        assert etf.ytd_return == Decimal("25.50")
        assert etf.one_year_return == Decimal("30.25")
        assert etf.three_year_return == Decimal("18.50")
        assert etf.ten_year_return == Decimal("14.25")
        assert "ssga.com" in etf.product_page_url
    
    def test_extract_etf_data_minimal(self, crawler, sample_spdr_response):
        """최소 정보만 있는 ETF 데이터 추출 테스트"""
        fund_data = sample_spdr_response['data']['funds']['etfs']['datas'][2]
        etf = crawler._extract_etf_data(fund_data)
        
        assert etf is not None
        assert etf.ticker == "SPLG"
        assert etf.fund_name == "SPDR® Portfolio S&P 500 ETF"
        assert etf.nav_amount == Decimal("71.50")
        assert etf.expense_ratio == Decimal("0.02")
    
    def test_extract_etf_data_no_ticker(self, crawler):
        """티커 없는 펀드 데이터 테스트"""
        fund_data = {
            "fundName": "Some Fund",
            "nav": ["$100.00", 100.0]
        }
        etf = crawler._extract_etf_data(fund_data)
        assert etf is None
    
    @pytest.mark.asyncio
    async def test_fetch_data_mock(self, crawler, sample_spdr_response):
        """fetch_data 메서드 테스트 (Mock)"""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_spdr_response
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            data = await crawler.fetch_data()
            
            assert data == sample_spdr_response
            assert data['status'] == 200
    
    @pytest.mark.asyncio
    async def test_parse_data(self, crawler, sample_spdr_response):
        """parse_data 메서드 테스트"""
        etf_list = await crawler.parse_data(sample_spdr_response)
        
        assert len(etf_list) == 3
        
        # 첫 번째 ETF 검증
        assert etf_list[0].ticker == "SPY"
        assert etf_list[0].fund_name == "SPDR® S&P 500® ETF Trust"
        
        # 두 번째 ETF 검증
        assert etf_list[1].ticker == "EBND"
        assert etf_list[1].fund_name == "SPDR® Bloomberg Emerging Markets Local Bond ETF"
        
        # 세 번째 ETF 검증
        assert etf_list[2].ticker == "SPLG"
    
    @pytest.mark.asyncio
    async def test_crawl_integration_mock(self, crawler, sample_spdr_response):
        """전체 크롤링 프로세스 통합 테스트 (Mock)"""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_spdr_response
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            etf_list = await crawler.crawl()
            
            assert len(etf_list) == 3
            assert all(isinstance(etf, ETF) for etf in etf_list)
            assert all(etf.ticker for etf in etf_list)


class TestSPDRCrawlerIntegration:
    """실제 API 호출 통합 테스트"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_real_data(self, crawler):
        """실제 SPDR API에서 데이터 가져오기 테스트"""
        data = await crawler.fetch_data()
        
        assert isinstance(data, dict)
        assert 'data' in data
        assert 'funds' in data['data']
        assert 'etfs' in data['data']['funds']
        assert 'datas' in data['data']['funds']['etfs']
        assert len(data['data']['funds']['etfs']['datas']) > 0
    
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
        assert "SPDR" in first_etf.fund_name
        assert first_etf.expense_ratio >= Decimal("0.00")
        assert first_etf.product_page_url.startswith("https://")
        
        # 모든 ETF가 올바른 형식인지 확인
        for etf in etf_list:
            assert isinstance(etf, ETF)
            assert etf.ticker
            assert len(etf.ticker) <= 5
        
        # 알려진 SPDR ETF가 포함되어 있는지 확인
        tickers = [etf.ticker for etf in etf_list]
        known_etfs = ["SPY", "GLD", "XLF", "XLE"]
        assert any(ticker in tickers for ticker in known_etfs)
        
        print(f"\nTotal SPDR ETFs found: {len(etf_list)}")
        print(f"Sample tickers: {tickers[:10]}")
