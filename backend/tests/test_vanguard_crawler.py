"""Vanguard 크롤러 테스트"""
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.etf import ETF
from app.services.crawlers.vanguard import VanguardCrawler


@pytest.fixture
def sample_vanguard_response():
    """Vanguard API 응답 샘플 데이터"""
    return {
        "size": 369,
        "self": {
            "type": "application/xml,application/json",
            "href": "http://api.vanguard.com/rs/ire/01/ind/etf,mf/vfa-month-end",
            "ref": "self"
        },
        "fund": {
            "entity": [
                {
                    "type": "priceMonthEndPerformance",
                    "profile": {
                        "fundId": "V001",
                        "ticker": "VTI",
                        "instrumentId": 12345678,
                        "shortName": "Total Stock Market ETF",
                        "longName": "Vanguard Total Stock Market ETF",
                        "cusip": "922906101",
                        "inceptionDate": "2001-05-24T00:00:00-04:00",
                        "style": "Stock Funds",
                        "type": "Large Blend",
                        "category": "Large Blend",
                        "expenseRatio": "0.0300",
                        "isETF": True,
                        "isMutualFund": False
                    },
                    "dailyPrice": {
                        "regular": {
                            "asOfDate": "2025-11-28T00:00:00-05:00",
                            "price": "285.50",
                            "priceChangeAmount": "1.25",
                            "priceChangePct": "0.44"
                        }
                    },
                    "yield": {
                        "asOfDate": "2025-11-25T00:00:00-05:00",
                        "yieldPct": "1.45"
                    },
                    "monthEndAvgAnnualRtn": {
                        "fundReturn": {
                            "oneYearPct": "25.30",
                            "threeYearPct": "12.50",
                            "fiveYearPct": "15.20",
                            "tenYearPct": "13.80",
                            "sinceInceptionPct": "8.50"
                        }
                    }
                },
                {
                    "type": "priceMonthEndPerformance",
                    "profile": {
                        "fundId": "M001",
                        "ticker": "VFIAX",
                        "longName": "Vanguard 500 Index Fund",
                        "cusip": "922908769",
                        "isETF": False,
                        "isMutualFund": True
                    }
                },
                {
                    "type": "priceMonthEndPerformance",
                    "profile": {
                        "fundId": "V002",
                        "ticker": "VOO",
                        "shortName": "S&P 500 ETF",
                        "longName": "Vanguard S&P 500 ETF",
                        "cusip": "922908363",
                        "inceptionDate": "2010-09-07T00:00:00-04:00",
                        "style": "Stock Funds",
                        "expenseRatio": "0.0300",
                        "isETF": True
                    },
                    "dailyPrice": {
                        "regular": {
                            "asOfDate": "2025-11-28T00:00:00-05:00",
                            "price": "580.25"
                        }
                    },
                    "monthEndAvgAnnualRtn": {
                        "fundReturn": {
                            "oneYearPct": "27.10"
                        }
                    }
                }
            ]
        }
    }


@pytest.fixture
def crawler():
    """VanguardCrawler 인스턴스"""
    return VanguardCrawler()


class TestVanguardCrawler:
    """VanguardCrawler 테스트"""
    
    def test_crawler_initialization(self, crawler):
        """크롤러 초기화 테스트"""
        assert crawler.get_provider_name() == "Vanguard"
        assert "vanguard.com" in crawler.BASE_URL
    
    def test_parse_date(self, crawler):
        """날짜 파싱 테스트"""
        # 정상적인 ISO 날짜
        date_str = "2001-05-24T00:00:00-04:00"
        result = crawler._parse_date(date_str)
        assert result == date(2001, 5, 24)
        
        # None
        assert crawler._parse_date(None) is None
        
        # 빈 문자열
        assert crawler._parse_date("") is None
        
        # 잘못된 형식
        assert crawler._parse_date("invalid") is None
    
    def test_extract_etf_data_valid(self, crawler, sample_vanguard_response):
        """유효한 ETF 데이터 추출 테스트"""
        entity = sample_vanguard_response['fund']['entity'][0]
        etf = crawler._extract_etf_data(entity)
        
        assert etf is not None
        assert etf.ticker == "VTI"
        assert etf.fund_name == "Vanguard Total Stock Market ETF"
        assert etf.cusip == "922906101"
        assert etf.inception_date == date(2001, 5, 24)
        assert etf.nav_amount == Decimal("285.50")
        assert etf.expense_ratio == Decimal("0.03")
        assert etf.one_year_return == Decimal("25.30")
        assert etf.distribution_yield == Decimal("1.45")
        assert "vanguard.com" in etf.product_page_url
    
    def test_extract_etf_data_mutual_fund(self, crawler, sample_vanguard_response):
        """뮤추얼 펀드 스킵 테스트"""
        entity = sample_vanguard_response['fund']['entity'][1]
        etf = crawler._extract_etf_data(entity)
        
        assert etf is None
    
    def test_extract_etf_data_minimal(self, crawler, sample_vanguard_response):
        """최소 정보만 있는 ETF 테스트"""
        entity = sample_vanguard_response['fund']['entity'][2]
        etf = crawler._extract_etf_data(entity)
        
        assert etf is not None
        assert etf.ticker == "VOO"
        assert etf.fund_name == "Vanguard S&P 500 ETF"
        assert etf.nav_amount == Decimal("580.25")
    
    def test_extract_etf_data_no_ticker(self, crawler):
        """티커 없는 엔티티 테스트"""
        entity = {
            "profile": {
                "isETF": True,
                "longName": "Some ETF"
            }
        }
        etf = crawler._extract_etf_data(entity)
        assert etf is None
    
    @pytest.mark.asyncio
    async def test_fetch_data_mock(self, crawler, sample_vanguard_response):
        """fetch_data 메서드 테스트 (Mock)"""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_vanguard_response
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            data = await crawler.fetch_data()
            
            assert data == sample_vanguard_response
            assert data['size'] == 369
    
    @pytest.mark.asyncio
    async def test_parse_data(self, crawler, sample_vanguard_response):
        """parse_data 메서드 테스트"""
        etf_list = await crawler.parse_data(sample_vanguard_response)
        
        # 3개 엔티티 중 ETF 2개만 파싱되어야 함
        assert len(etf_list) == 2
        
        # 첫 번째 ETF 검증
        assert etf_list[0].ticker == "VTI"
        assert etf_list[0].fund_name == "Vanguard Total Stock Market ETF"
        
        # 두 번째 ETF 검증
        assert etf_list[1].ticker == "VOO"
        assert etf_list[1].fund_name == "Vanguard S&P 500 ETF"
    
    @pytest.mark.asyncio
    async def test_crawl_integration_mock(self, crawler, sample_vanguard_response):
        """전체 크롤링 프로세스 통합 테스트 (Mock)"""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_vanguard_response
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            etf_list = await crawler.crawl()
            
            assert len(etf_list) == 2
            assert all(isinstance(etf, ETF) for etf in etf_list)
            assert all(etf.ticker for etf in etf_list)


class TestVanguardCrawlerIntegration:
    """실제 API 호출 통합 테스트"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_real_data(self, crawler):
        """실제 Vanguard API에서 데이터 가져오기 테스트"""
        data = await crawler.fetch_data()
        
        assert isinstance(data, dict)
        assert 'fund' in data
        assert 'entity' in data['fund']
        assert len(data['fund']['entity']) > 0
    
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
        assert first_etf.expense_ratio >= Decimal("0.00")
        assert first_etf.product_page_url.startswith("https://")
        
        # 모든 ETF가 올바른 형식인지 확인
        for etf in etf_list:
            assert isinstance(etf, ETF)
            assert etf.ticker
            assert len(etf.ticker) <= 5
            assert "Vanguard" in etf.fund_name or etf.fund_name
        
        # 알려진 Vanguard ETF가 포함되어 있는지 확인
        tickers = [etf.ticker for etf in etf_list]
        known_etfs = ["VTI", "VOO", "VEA", "BND"]
        assert any(ticker in tickers for ticker in known_etfs)
        
        print(f"\nTotal Vanguard ETFs found: {len(etf_list)}")
        print(f"Sample tickers: {tickers[:10]}")
