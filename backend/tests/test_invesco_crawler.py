"""Invesco 크롤러 테스트"""
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.etf import ETF
from app.services.crawlers.invesco import InvescoCrawler


@pytest.fixture
def sample_invesco_response():
    """Invesco API 응답 샘플 데이터"""
    return {
        "responseHeader": {
            "zkConnected": True,
            "status": 0,
            "QTime": 15
        },
        "response": {
            "numFound": 240,
            "start": 0,
            "numFoundExact": True,
            "docs": [
                {
                    "url": "/content/invesco/us/en/financial-products/etfs/invesco-qqq-trust-series-1.html",
                    "title": "Invesco QQQ Trust Series 1",
                    "isin": "US46090E1038",
                    "cusip": "46090E103",
                    "uniqueIdentifier": "cusip",
                    "accountName": "Invesco QQQ Trust Series 1",
                    "assetClass": "Equity",
                    "assetSubClass": "Large Cap Growth",
                    "shareClassStatus": "open",
                    "ticker": "QQQ",
                    "inceptionDate": "1999-03-10",
                    "primaryShareClassIndicator": "true",
                    "totalExpenseRatio": "0.20",
                    "youngFund": "false"
                },
                {
                    "url": "/content/invesco/us/en/financial-products/etfs/invesco-0-5-yr-us-tips-etf.html",
                    "title": "Invesco 0-5 Yr US TIPS ETF",
                    "isin": "US46138E4952",
                    "cusip": "46138E495",
                    "uniqueIdentifier": "cusip",
                    "accountName": "Invesco 0-5 Yr US TIPS ETF",
                    "assetClass": "Fixed Income",
                    "assetSubClass": "Inflation-Protected Bond",
                    "shareClassStatus": "open",
                    "ticker": "PBTP",
                    "inceptionDate": "2017-09-22",
                    "primaryShareClassIndicator": "true",
                    "totalExpenseRatio": "0.07",
                    "youngFund": "false"
                },
                {
                    "url": "/content/invesco/us/en/financial-products/etfs/invesco-db-oil-fund.html",
                    "title": "Invesco DB Oil Fund",
                    "isin": "US26922A8033",
                    "cusip": "26922A803",
                    "accountName": "Invesco DB Oil Fund",
                    "assetClass": "Commodity",
                    "assetSubClass": "Energy",
                    "shareClassStatus": "open",
                    "ticker": "DBO",
                    "inceptionDate": "2007-01-05",
                    "totalExpenseRatio": "0.77"
                }
            ]
        },
        "facet_counts": {
            "facet_fields": {
                "assetClass": ["Equity", 120, "Fixed Income", 80, "Commodity", 40]
            }
        }
    }


@pytest.fixture
def crawler():
    """InvescoCrawler 인스턴스"""
    return InvescoCrawler()


class TestInvescoCrawler:
    """InvescoCrawler 테스트"""
    
    def test_crawler_initialization(self, crawler):
        """크롤러 초기화 테스트"""
        assert crawler.get_provider_name() == "Invesco"
        assert "invesco.com" in crawler.BASE_URL
        assert crawler.PARAMS['rows'] == '2000'
    
    def test_parse_date_iso_format(self, crawler):
        """ISO 형식 날짜 파싱 테스트"""
        result = crawler._parse_date("2017-09-22")
        assert result == date(2017, 9, 22)
        
        result2 = crawler._parse_date("1999-03-10")
        assert result2 == date(1999, 3, 10)
    
    def test_parse_date_invalid(self, crawler):
        """잘못된 날짜 파싱 테스트"""
        assert crawler._parse_date(None) is None
        assert crawler._parse_date("") is None
        assert crawler._parse_date("invalid") is None
    
    def test_extract_etf_data_full(self, crawler, sample_invesco_response):
        """전체 정보가 있는 ETF 데이터 추출 테스트"""
        doc = sample_invesco_response['response']['docs'][0]
        etf = crawler._extract_etf_data(doc)
        
        assert etf is not None
        assert etf.ticker == "QQQ"
        assert etf.fund_name == "Invesco QQQ Trust Series 1"
        assert etf.isin == "US46090E1038"
        assert etf.cusip == "46090E103"
        assert etf.inception_date == date(1999, 3, 10)
        assert etf.expense_ratio == Decimal("0.20")
        assert etf.asset_class == "Equity"
        assert "invesco.com" in etf.product_page_url
    
    def test_extract_etf_data_fixed_income(self, crawler, sample_invesco_response):
        """채권 ETF 데이터 추출 테스트"""
        doc = sample_invesco_response['response']['docs'][1]
        etf = crawler._extract_etf_data(doc)
        
        assert etf is not None
        assert etf.ticker == "PBTP"
        assert etf.fund_name == "Invesco 0-5 Yr US TIPS ETF"
        assert etf.asset_class == "Fixed Income"
        assert etf.expense_ratio == Decimal("0.07")
    
    def test_extract_etf_data_commodity(self, crawler, sample_invesco_response):
        """상품 ETF 데이터 추출 테스트"""
        doc = sample_invesco_response['response']['docs'][2]
        etf = crawler._extract_etf_data(doc)
        
        assert etf is not None
        assert etf.ticker == "DBO"
        assert etf.asset_class == "Commodity"
        assert etf.expense_ratio == Decimal("0.77")
    
    def test_extract_etf_data_no_ticker(self, crawler):
        """티커 없는 문서 테스트"""
        doc = {
            "title": "Some Fund",
            "accountName": "Some Fund"
        }
        etf = crawler._extract_etf_data(doc)
        assert etf is None
    
    def test_extract_etf_data_invalid_expense_ratio(self, crawler):
        """잘못된 expense ratio 처리 테스트"""
        doc = {
            "ticker": "TEST",
            "accountName": "Test Fund",
            "totalExpenseRatio": "invalid",
            "assetClass": "Equity"
        }
        etf = crawler._extract_etf_data(doc)
        assert etf is not None
        assert etf.expense_ratio == Decimal("0.00")
    
    @pytest.mark.asyncio
    async def test_fetch_data_mock(self, crawler, sample_invesco_response):
        """fetch_data 메서드 테스트 (Mock)"""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_invesco_response
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            data = await crawler.fetch_data()
            
            assert data == sample_invesco_response
            assert data['response']['numFound'] == 240
    
    @pytest.mark.asyncio
    async def test_parse_data(self, crawler, sample_invesco_response):
        """parse_data 메서드 테스트"""
        etf_list = await crawler.parse_data(sample_invesco_response)
        
        assert len(etf_list) == 3
        
        # 첫 번째 ETF 검증
        assert etf_list[0].ticker == "QQQ"
        assert etf_list[0].fund_name == "Invesco QQQ Trust Series 1"
        
        # 두 번째 ETF 검증
        assert etf_list[1].ticker == "PBTP"
        assert etf_list[1].asset_class == "Fixed Income"
        
        # 세 번째 ETF 검증
        assert etf_list[2].ticker == "DBO"
        assert etf_list[2].asset_class == "Commodity"
    
    @pytest.mark.asyncio
    async def test_crawl_integration_mock(self, crawler, sample_invesco_response):
        """전체 크롤링 프로세스 통합 테스트 (Mock)"""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_invesco_response
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            etf_list = await crawler.crawl()
            
            assert len(etf_list) == 3
            assert all(isinstance(etf, ETF) for etf in etf_list)
            assert all(etf.ticker for etf in etf_list)


class TestInvescoCrawlerIntegration:
    """실제 API 호출 통합 테스트"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_real_data(self, crawler):
        """실제 Invesco API에서 데이터 가져오기 테스트"""
        data = await crawler.fetch_data()
        
        assert isinstance(data, dict)
        assert 'response' in data
        assert 'docs' in data['response']
        assert data['response']['numFound'] > 0
        assert len(data['response']['docs']) > 0
    
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
        assert "Invesco" in first_etf.fund_name
        assert first_etf.expense_ratio >= Decimal("0.00")
        assert first_etf.product_page_url.startswith("https://")
        
        # 모든 ETF가 올바른 형식인지 확인
        for etf in etf_list:
            assert isinstance(etf, ETF)
            assert etf.ticker
            assert len(etf.ticker) <= 5
            assert etf.isin != "N/A" or etf.cusip != "N/A"  # 최소 하나는 있어야 함
        
        # 알려진 Invesco ETF가 포함되어 있는지 확인
        tickers = [etf.ticker for etf in etf_list]
        known_etfs = ["QQQ", "QQQM", "PBTP", "DBO"]
        assert any(ticker in tickers for ticker in known_etfs)
        
        print(f"\nTotal Invesco ETFs found: {len(etf_list)}")
        print(f"Sample tickers: {tickers[:10]}")
