"""Dimensional Fund Advisors 크롤러 테스트"""
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.etf import ETF
from app.services.crawlers.dimensional import DimensionalCrawler


@pytest.fixture
def sample_dimensional_response():
    """Dimensional API 응답 샘플 데이터"""
    return {
        "data": {
            "isoCountryCode": "US",
            "region": "us",
            "portfolios": [
                {
                    "portfolioNumber": 1430,
                    "meta": {
                        "marketingName": "US Core Equity 1 ETF",
                        "category": "US Equity Funds",
                        "inceptionDate": {
                            "value": "2023-09-12",
                            "display": "09/12/2023"
                        },
                        "identifiers": [
                            {
                                "slug": "cusip",
                                "value": "25434V625"
                            },
                            {
                                "slug": "isin",
                                "value": "US25434V6258"
                            },
                            {
                                "slug": "ticker",
                                "value": "DCOR"
                            }
                        ],
                        "isEtf": True
                    },
                    "fees": [
                        {
                            "slug": "net-exp-ratio",
                            "value": {
                                "value": 0.0014,
                                "display": "0.14%"
                            }
                        }
                    ],
                    "prices": [
                        {
                            "date": {
                                "value": "2025-11-28",
                                "display": "11/28/2025"
                            },
                            "nav": {
                                "value": 73.5821,
                                "display": "73.58"
                            }
                        }
                    ],
                    "returnsMonthly": [
                        {
                            "asOfDate": {
                                "value": "2025-10-31"
                            },
                            "annualizedReturn1Year": {
                                "value": 0.17234477,
                                "display": "17.23%"
                            },
                            "annualizedReturn3Year": None,
                            "annualizedReturnSincePortfolioInception": {
                                "value": 0.20685397,
                                "display": "20.69%"
                            }
                        }
                    ],
                    "returnsDaily": [
                        {
                            "asOfDate": {
                                "value": "2025-11-28"
                            },
                            "annualizedReturnYtd": {
                                "value": 0.15714171,
                                "display": "15.71%"
                            }
                        }
                    ]
                },
                {
                    "portfolioNumber": 1450,
                    "meta": {
                        "marketingName": "International Core Equity ETF",
                        "category": "International Equity Funds",
                        "inceptionDate": {
                            "value": "2020-11-17",
                            "display": "11/17/2020"
                        },
                        "identifiers": [
                            {
                                "slug": "cusip",
                                "value": "25434V500"
                            },
                            {
                                "slug": "isin",
                                "value": "US25434V5008"
                            },
                            {
                                "slug": "ticker",
                                "value": "DFAI"
                            }
                        ],
                        "isEtf": True
                    },
                    "fees": [
                        {
                            "slug": "net-exp-ratio",
                            "value": {
                                "value": 0.0023,
                                "display": "0.23%"
                            }
                        }
                    ],
                    "prices": [
                        {
                            "date": {
                                "value": "2025-11-28"
                            },
                            "nav": {
                                "value": 34.52
                            }
                        }
                    ],
                    "returnsMonthly": [
                        {
                            "annualizedReturn1Year": {
                                "value": 0.0823
                            },
                            "annualizedReturn3Year": {
                                "value": 0.0567
                            },
                            "annualizedReturn5Year": {
                                "value": 0.0891
                            },
                            "annualizedReturnSincePortfolioInception": {
                                "value": 0.1025
                            }
                        }
                    ],
                    "returnsDaily": [
                        {
                            "annualizedReturnYtd": {
                                "value": 0.0634
                            }
                        }
                    ]
                },
                {
                    "portfolioNumber": 9999,
                    "meta": {
                        "marketingName": "Test Mutual Fund",
                        "category": "US Equity Funds",
                        "identifiers": [
                            {
                                "slug": "ticker",
                                "value": "TESTMF"
                            }
                        ],
                        "isEtf": False
                    }
                }
            ]
        }
    }


@pytest.fixture
def crawler():
    """DimensionalCrawler 인스턴스"""
    return DimensionalCrawler()


class TestDimensionalCrawler:
    """DimensionalCrawler 테스트"""
    
    def test_crawler_initialization(self, crawler):
        """크롤러 초기화 테스트"""
        assert crawler.get_provider_name() == "Dimensional Fund Advisors"
        assert "dimensional.com" in crawler.BASE_URL
        assert crawler.HEADERS['X-Selected-Country'] == 'US'
    
    def test_parse_date_iso_format(self, crawler):
        """ISO 형식 날짜 파싱 테스트"""
        result = crawler._parse_date("2023-09-12")
        assert result == date(2023, 9, 12)
        
        result2 = crawler._parse_date("2020-11-17")
        assert result2 == date(2020, 11, 17)
    
    def test_parse_date_invalid(self, crawler):
        """잘못된 날짜 파싱 테스트"""
        assert crawler._parse_date(None) is None
        assert crawler._parse_date("") is None
        assert crawler._parse_date("invalid") is None
    
    def test_extract_identifier(self, crawler, sample_dimensional_response):
        """identifier 추출 테스트"""
        identifiers = sample_dimensional_response['data']['portfolios'][0]['meta']['identifiers']
        
        assert crawler._extract_identifier(identifiers, 'ticker') == 'DCOR'
        assert crawler._extract_identifier(identifiers, 'cusip') == '25434V625'
        assert crawler._extract_identifier(identifiers, 'isin') == 'US25434V6258'
        assert crawler._extract_identifier(identifiers, 'unknown') == 'N/A'
    
    def test_extract_return_value(self, crawler):
        """수익률 값 추출 테스트"""
        returns = {
            "annualizedReturn1Year": {
                "value": 0.17234477,
                "display": "17.23%"
            },
            "annualizedReturn3Year": None
        }
        
        assert crawler._extract_return_value(returns, 'annualizedReturn1Year') == Decimal("17.23")
        assert crawler._extract_return_value(returns, 'annualizedReturn3Year') is None
        assert crawler._extract_return_value(None, 'annualizedReturn1Year') is None
    
    def test_extract_fee_value(self, crawler, sample_dimensional_response):
        """수수료 값 추출 테스트"""
        fees = sample_dimensional_response['data']['portfolios'][0]['fees']
        
        # 0.0014 -> 0.14%
        assert crawler._extract_fee_value(fees, 'net-exp-ratio') == Decimal("0.14")
        assert crawler._extract_fee_value(fees, 'unknown') == Decimal("0.00")
    
    def test_extract_etf_data_full(self, crawler, sample_dimensional_response):
        """전체 정보가 있는 ETF 데이터 추출 테스트"""
        portfolio = sample_dimensional_response['data']['portfolios'][0]
        etf = crawler._extract_etf_data(portfolio)
        
        assert etf is not None
        assert etf.ticker == "DCOR"
        assert etf.fund_name == "Dimensional US Core Equity 1 ETF"
        assert etf.isin == "US25434V6258"
        assert etf.cusip == "25434V625"
        assert etf.inception_date == date(2023, 9, 12)
        assert etf.nav_amount == Decimal("73.5821")
        assert etf.nav_as_of == date(2025, 11, 28)
        assert etf.expense_ratio == Decimal("0.14")
        assert etf.ytd_return == Decimal("15.71")
        assert etf.one_year_return == Decimal("17.23")
        assert etf.since_inception_return == Decimal("20.69")
        assert etf.asset_class == "US Equity Funds"
        assert "dimensional.com" in etf.product_page_url
    
    def test_extract_etf_data_international(self, crawler, sample_dimensional_response):
        """국제 ETF 데이터 추출 테스트"""
        portfolio = sample_dimensional_response['data']['portfolios'][1]
        etf = crawler._extract_etf_data(portfolio)
        
        assert etf is not None
        assert etf.ticker == "DFAI"
        assert etf.fund_name == "Dimensional International Core Equity ETF"
        assert etf.asset_class == "International Equity Funds"
        assert etf.ytd_return == Decimal("6.34")
        assert etf.one_year_return == Decimal("8.23")
        assert etf.three_year_return == Decimal("5.67")
        assert etf.five_year_return == Decimal("8.91")
    
    def test_extract_etf_data_non_etf(self, crawler, sample_dimensional_response):
        """ETF가 아닌 상품 필터링 테스트"""
        portfolio = sample_dimensional_response['data']['portfolios'][2]
        etf = crawler._extract_etf_data(portfolio)
        
        # isEtf=False이므로 None 반환
        assert etf is None
    
    def test_extract_etf_data_no_ticker(self, crawler):
        """티커 없는 포트폴리오 테스트"""
        portfolio = {
            "meta": {
                "marketingName": "Some Fund",
                "isEtf": True,
                "identifiers": []
            }
        }
        etf = crawler._extract_etf_data(portfolio)
        assert etf is None
    
    @pytest.mark.asyncio
    async def test_fetch_data_mock(self, crawler, sample_dimensional_response):
        """fetch_data 메서드 테스트 (Mock)"""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_dimensional_response
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            data = await crawler.fetch_data()
            
            assert data == sample_dimensional_response
            assert len(data['data']['portfolios']) == 3
    
    @pytest.mark.asyncio
    async def test_parse_data(self, crawler, sample_dimensional_response):
        """parse_data 메서드 테스트"""
        etf_list = await crawler.parse_data(sample_dimensional_response)
        
        # 3개 중 ETF는 2개만
        assert len(etf_list) == 2
        
        # 첫 번째 ETF 검증
        assert etf_list[0].ticker == "DCOR"
        assert etf_list[0].asset_class == "US Equity Funds"
        
        # 두 번째 ETF 검증
        assert etf_list[1].ticker == "DFAI"
        assert etf_list[1].asset_class == "International Equity Funds"
    
    @pytest.mark.asyncio
    async def test_parse_data_invalid_input(self, crawler):
        """잘못된 입력 데이터 파싱 테스트"""
        etf_list = await crawler.parse_data([])
        assert len(etf_list) == 0
        
        etf_list2 = await crawler.parse_data(None)
        assert len(etf_list2) == 0
    
    @pytest.mark.asyncio
    async def test_crawl_integration_mock(self, crawler, sample_dimensional_response):
        """전체 크롤링 프로세스 통합 테스트 (Mock)"""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_dimensional_response
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            etf_list = await crawler.crawl()
            
            assert len(etf_list) == 2
            assert all(isinstance(etf, ETF) for etf in etf_list)
            assert all(etf.ticker for etf in etf_list)


class TestDimensionalCrawlerIntegration:
    """실제 API 호출 통합 테스트"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_real_data(self, crawler):
        """실제 Dimensional API에서 데이터 가져오기 테스트"""
        data = await crawler.fetch_data()
        
        assert isinstance(data, dict)
        assert 'data' in data
        assert 'portfolios' in data['data']
        assert len(data['data']['portfolios']) > 0
    
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
        assert "Dimensional" in first_etf.fund_name
        assert first_etf.isin != "N/A"
        assert first_etf.cusip != "N/A"
        assert first_etf.product_page_url.startswith("https://")
        
        # 모든 ETF가 올바른 형식인지 확인
        for etf in etf_list:
            assert isinstance(etf, ETF)
            assert etf.ticker
            assert len(etf.ticker) <= 5
        
        # 알려진 Dimensional ETF가 포함되어 있는지 확인
        tickers = [etf.ticker for etf in etf_list]
        known_etfs = ["DCOR", "DFAI", "DFAS", "DFAC"]
        assert any(ticker in tickers for ticker in known_etfs)
        
        print(f"\nTotal Dimensional ETFs found: {len(etf_list)}")
        print(f"Sample tickers: {tickers[:10]}")
