"""iShares 크롤러 테스트"""
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from app.models.etf import ETF
from app.services.crawlers.ishares import ISharesCrawler


@pytest.fixture
def sample_ishares_response():
    """iShares API 응답 샘플 데이터 (실제 구조 반영)"""
    return {
            "239726": {
                "localExchangeTicker": "IVV",
                "fundName": "iShares Core S&P 500 ETF",
                "isin": "US4642872000",
                "cusip": "464287200",
                "portfolioId": 239726,
                "inceptionDate": {"d": "May 15, 2000", "r": 20000515},
                "navAmount": {"d": "580.50", "r": 580.50},
                "navAmountAsOf": {"d": "Nov 28, 2025", "r": 20251128},
                "fees": {"d": "0.03", "r": 0.03},
                "quarterlyNavYearToDate": {"d": "17.48", "r": 17.48},
                "quarterlyNavOneYearAnnualized": {"d": "21.49", "r": 21.49},
                "quarterlyNavThreeYearAnnualized": {"d": "22.65", "r": 22.65},
                "quarterlyNavFiveYearAnnualized": {"d": "17.59", "r": 17.59},
                "quarterlyNavTenYearAnnualized": {"d": "14.60", "r": 14.60},
                "quarterlyNavSinceInceptionAnnualized": {"d": "8.21", "r": 8.21},
                "priceYearToDate": {"d": "17.48", "r": 17.48},
                "priceOneYearAnnualized": {"d": "21.49", "r": 21.49},
                "priceThreeYearAnnualized": {"d": "22.65", "r": 22.65},
                "priceFiveYearAnnualized": {"d": "17.59", "r": 17.59},
                "priceTenYearAnnualized": {"d": "14.60", "r": 14.60},
                "priceSinceInceptionAnnualized": {"d": "8.21", "r": 8.21},
                "aladdinAssetClass": "Equity",
                "aladdinRegion": "North America",
                "aladdinMarketType": "Developed",
                "distributionYield": {"d": "1.35", "r": 1.35},
                "productPageUrl": "/us/products/239726/ishares-core-sp-500-etf"
            },
            "239619": {
                "localExchangeTicker": "MCHI",
                "fundName": "iShares MSCI China ETF",
                "isin": "US46429B6719",
                "cusip": "46429B671",
                "portfolioId": 239619,
                "inceptionDate": {"d": "Mar 29, 2011", "r": 20110329},
                "navAmount": {"d": "62.19", "r": 62.190296},
                "navAmountAsOf": {"d": "Nov 28, 2025", "r": 20251128},
                "fees": {"d": "0.59", "r": 0.59},
                "quarterlyNavYearToDate": {"d": "41.16", "r": 41.16},
                "quarterlyNavOneYearAnnualized": {"d": "32.87", "r": 32.87},
                "quarterlyNavThreeYearAnnualized": {"d": "18.76", "r": 18.76},
                "quarterlyNavFiveYearAnnualized": {"d": "-0.19", "r": -0.19},
                "quarterlyNavTenYearAnnualized": {"d": "6.16", "r": 6.16},
                "quarterlyNavSinceInceptionAnnualized": {"d": "3.95", "r": 3.95},
                "priceYearToDate": {"d": "36.98", "r": 36.98},
                "priceOneYearAnnualized": {"d": "32.79", "r": 32.79},
                "priceThreeYearAnnualized": {"d": "24.70", "r": 24.7},
                "priceFiveYearAnnualized": {"d": "-1.90", "r": -1.9},
                "priceTenYearAnnualized": {"d": "4.93", "r": 4.93},
                "priceSinceInceptionAnnualized": {"d": "3.68", "r": 3.68},
                "aladdinAssetClass": "Equity",
                "aladdinAssetClassCode": "43511",
                "aladdinCountry": "China",
                "aladdinRegion": "Asia Pacific",
                "aladdinMarketType": "Emerging",
                "productPageUrl": "/us/products/239619/ishares-msci-china-etf"
            },
        "invalid_etf": {
            # 필수 필드 누락 - 스킵되어야 함
            "fundName": "Invalid ETF"
        }
    }


@pytest.fixture
def crawler():
    """ISharesCrawler 인스턴스"""
    return ISharesCrawler()


@pytest.fixture(scope="session")
async def real_api_data():
    """실제 API 데이터 (세션당 한 번만 호출)"""
    crawler = ISharesCrawler()
    return await crawler.fetch_data()


class TestISharesCrawler:
    """ISharesCrawler 테스트"""
    
    def test_crawler_initialization(self, crawler):
        """크롤러 초기화 테스트"""
        assert crawler.get_provider_name() == "IShares"
        assert crawler.BASE_URL == "https://www.ishares.com/us/product-screener/product-screener-v3.1.jsn"
        assert "dcrPath" in crawler.PARAMS
    
    @pytest.mark.asyncio
    async def test_parse_data_success(self, crawler, sample_ishares_response):
        """정상적인 데이터 파싱 테스트"""
        etf_list = await crawler.parse_data(sample_ishares_response)
        
        # 유효한 2개의 ETF만 파싱되어야 함 (invalid_etf는 제외)
        assert len(etf_list) == 2
        
        # 첫 번째 ETF (IVV) 검증
        ivv = next(etf for etf in etf_list if etf.ticker == "IVV")
        assert ivv.fund_name == "iShares Core S&P 500 ETF"
        assert ivv.isin == "US4642872000"
        assert ivv.cusip == "464287200"
        assert ivv.inception_date == date(2000, 5, 15)
        assert ivv.nav_amount == Decimal("580.50")
        assert ivv.nav_as_of == date(2025, 11, 28)
        assert ivv.expense_ratio == Decimal("0.03")
        assert ivv.ytd_return == Decimal("17.48")
        assert ivv.one_year_return == Decimal("21.49")
        assert ivv.three_year_return == Decimal("22.65")
        assert ivv.five_year_return == Decimal("17.59")
        assert ivv.ten_year_return == Decimal("14.60")
        assert ivv.since_inception_return == Decimal("8.21")
        assert ivv.asset_class == "Equity"
        assert ivv.region == "North America"
        assert ivv.market_type == "Developed"
        assert ivv.distribution_yield == Decimal("1.35")
        assert ivv.product_page_url == "/us/products/239726/ishares-core-sp-500-etf"
        
        # 두 번째 ETF (MCHI) 검증
        mchi = next(etf for etf in etf_list if etf.ticker == "MCHI")
        assert mchi.fund_name == "iShares MSCI China ETF"
        assert mchi.isin == "US46429B6719"
        assert mchi.cusip == "46429B671"
        assert mchi.inception_date == date(2011, 3, 29)
        assert mchi.nav_amount == Decimal("62.190296")
        assert mchi.expense_ratio == Decimal("0.59")
        assert mchi.ytd_return == Decimal("41.16")  # quarterlyNavYearToDate 우선
        assert mchi.one_year_return == Decimal("32.87")
        assert mchi.three_year_return == Decimal("18.76")
        assert mchi.five_year_return == Decimal("-0.19")  # 음수 값 테스트
        assert mchi.ten_year_return == Decimal("6.16")
        assert mchi.since_inception_return == Decimal("3.95")
        assert mchi.asset_class == "Equity"
        assert mchi.region == "Asia Pacific"
        assert mchi.market_type == "Emerging"
        assert mchi.distribution_yield is None  # 값 없음
    
    
    @pytest.mark.asyncio
    async def test_parse_data_empty(self, crawler):
        """빈 데이터 파싱 테스트"""
        empty_data = {}
        etf_list = await crawler.parse_data(empty_data)
        assert len(etf_list) == 0
    
    @pytest.mark.asyncio
    async def test_parse_data_missing_fields(self, crawler):
        """필수 필드 누락 시 스킵 테스트"""
        data = {
            "1": {"fundName": "ETF 1"},  # ticker, isin 누락
            "2": {"localExchangeTicker": "ETF2"},  # fundName, isin 누락
            "3": {
                "localExchangeTicker": "VALID",
                "fundName": "Valid ETF",
                "isin": "US1234567890",
                "cusip": "123456789",
                "inceptionDate": {"d": "Jan 01, 2020", "r": 20200101},
                "navAmount": {"d": "100.00", "r": 100.00},
                "navAmountAsOf": {"d": "Nov 28, 2025", "r": 20251128},
                "fees": {"d": "0.05", "r": 0.05},
                "aladdinAssetClass": "Equity",
                "aladdinRegion": "Global",
                "aladdinMarketType": "Developed",
                "productPageUrl": "/us/products/valid"
            }
        }
        
        etf_list = await crawler.parse_data(data)
        
        # 유효한 1개만 파싱되어야 함
        assert len(etf_list) == 1
        assert etf_list[0].ticker == "VALID"
    
    @pytest.mark.asyncio
    async def test_parse_data_invalid_date_format(self, crawler):
        """잘못된 날짜 형식 처리 테스트"""
        data = {
            "1": {
                "localExchangeTicker": "TEST",
                "fundName": "Test ETF",
                "isin": "US1234567890",
                "cusip": "123456789",
                "inceptionDate": {"d": "Invalid Date", "r": 20200101},
                "navAmount": {"d": "100.00", "r": 100.00},
                "navAmountAsOf": {"d": "Invalid Date", "r": 20251128},
                "fees": {"d": "0.05", "r": 0.05},
                "aladdinAssetClass": "Equity",
                "aladdinRegion": "Global",
                "aladdinMarketType": "Developed",
                "productPageUrl": "/test"
            }
        }
        
        etf_list = await crawler.parse_data(data)
        
        # 날짜 파싱 실패 시 현재 날짜 사용
        assert len(etf_list) == 1
        assert etf_list[0].ticker == "TEST"
        assert etf_list[0].inception_date is not None
        assert etf_list[0].nav_as_of is not None
    
    @pytest.mark.asyncio
    async def test_parse_data_invalid_decimal(self, crawler):
        """잘못된 Decimal 값 처리 테스트"""
        data = {
            "1": {
                "localExchangeTicker": "TEST",
                "fundName": "Test ETF",
                "isin": "US1234567890",
                "cusip": "123456789",
                "inceptionDate": {"d": "Jan 01, 2020", "r": 20200101},
                "navAmount": {"d": "invalid", "r": "not_a_number"},
                "navAmountAsOf": {"d": "Nov 28, 2025", "r": 20251128},
                "fees": {"d": "0.05", "r": 0.05},
                "priceYearToDate": {"d": "invalid", "r": None},
                "aladdinAssetClass": "Equity",
                "aladdinRegion": "Global",
                "aladdinMarketType": "Developed",
                "productPageUrl": "/test"
            }
        }
        
        etf_list = await crawler.parse_data(data)
        
        # Decimal 파싱 실패 시 None 또는 0 사용
        assert len(etf_list) == 1
        assert etf_list[0].ticker == "TEST"
        assert etf_list[0].ytd_return is None
    
    @pytest.mark.asyncio
    async def test_crawl_integration(self, crawler, monkeypatch, sample_ishares_response):
        """전체 crawl 프로세스 통합 테스트 (fetch + parse)"""
        
        # fetch_data를 모킹하여 실제 API 호출 대신 샘플 데이터 반환
        async def mock_fetch_data():
            return sample_ishares_response
        
        monkeypatch.setattr(crawler, "fetch_data", mock_fetch_data)
        
        # crawl 실행
        etf_list = await crawler.crawl()
        
        # 결과 검증
        assert len(etf_list) == 2
        assert all(isinstance(etf, ETF) for etf in etf_list)
        assert any(etf.ticker == "IVV" for etf in etf_list)
        assert any(etf.ticker == "MCHI" for etf in etf_list)
    
    @pytest.mark.asyncio
    async def test_parse_data_with_null_values(self, crawler):
        """null 값 처리 테스트"""
        data = {
            "1": {
                "localExchangeTicker": "NULL",
                "fundName": "Null Test ETF",
                "isin": "US1234567890",
                "cusip": "123456789",
                "inceptionDate": None,
                "navAmount": None,
                "navAmountAsOf": None,
                "fees": None,
                "priceYearToDate": None,
                "priceOneYearAnnualized": None,
                "distributionYield": None,
                "aladdinAssetClass": "Equity",
                "aladdinRegion": "Global",
                "aladdinMarketType": "Developed",
                "productPageUrl": "/null"
            }
        }
        
        etf_list = await crawler.parse_data(data)
        
        # null 값들이 적절히 처리되어야 함
        assert len(etf_list) == 1
        etf = etf_list[0]
        assert etf.ticker == "NULL"
        assert etf.nav_amount == Decimal("0")  # null인 경우 기본값
        assert etf.expense_ratio == Decimal("0")
        assert etf.ytd_return is None
        assert etf.one_year_return is None
        assert etf.distribution_yield is None


@pytest.mark.integration
class TestISharesCrawlerIntegration:
    """실제 API 호출 통합 테스트 (세션당 한 번만 실행)"""
    
    @pytest.mark.asyncio
    async def test_fetch_data_real_api(self, real_api_data):
        """실제 iShares API 호출 테스트 (캐싱됨)"""
        crawler = ISharesCrawler()
        data = real_api_data
        
        # 응답 구조 검증
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # 샘플 ETF 존재 확인 (포트폴리오 ID가 키)
        portfolio_ids = list(data.keys())
        assert len(portfolio_ids) > 0
        
        # 샘플 ETF 파싱 테스트
        etf_list = await crawler.parse_data(data)
        assert len(etf_list) > 0
        
        # 첫 번째 ETF 구조 검증
        first_etf = etf_list[0]
        assert isinstance(first_etf, ETF)
        assert first_etf.ticker
        assert first_etf.fund_name
        assert first_etf.isin
