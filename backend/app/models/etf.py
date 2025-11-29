"""ETF 데이터 모델"""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DistributionFrequency(str, Enum):
    """배당 주기"""
    WEEKLY = "Weekly"  # 주배당
    MONTHLY = "Monthly"  # 월배당
    QUARTERLY = "Quarterly"  # 분기배당
    SEMI_ANNUAL = "Semi-Annual"  # 반기배당
    ANNUAL = "Annual"  # 연배당
    VARIABLE = "Variable"  # 가변
    NONE = "None"  # 무배당
    UNKNOWN = "Unknown"  # 알 수 없음


class ETF(BaseModel):
    """ETF 기본 정보"""
    
    # 기본 식별 정보
    ticker: str = Field(..., description="티커 심볼 (예: SCHD)")
    fund_name: str = Field(..., description="펀드명")
    isin: str = Field(..., description="ISIN 코드")
    cusip: str = Field(..., description="CUSIP 코드")
    inception_date: Optional[date] = Field(None, description="설정일")
    
    # 가격 정보
    # NAV (Net Asset Value)는 ETF의 순자산가치로, 일반적으로 시장 가격(market price)과 유사합니다.
    # ETF는 NAV를 기준으로 거래되므로, nav_amount가 실질적으로 price의 역할을 합니다.
    # 대부분의 ETF는 NAV와 시장 가격의 차이가 1% 미만입니다.
    nav_amount: Decimal = Field(..., description="현재 NAV (순자산가치, ETF의 실질 가격)")
    nav_as_of: date = Field(..., description="NAV 기준일")
    
    # 비용 정보
    expense_ratio: Decimal = Field(..., description="운용 보수율 (예: 0.06 = 0.06%)")
    
    # 수익률 정보
    ytd_return: Optional[Decimal] = Field(None, description="연초 대비 수익률 (%)")
    one_year_return: Optional[Decimal] = Field(None, description="1년 수익률 (%)")
    three_year_return: Optional[Decimal] = Field(None, description="3년 수익률 (%)")
    five_year_return: Optional[Decimal] = Field(None, description="5년 수익률 (%)")
    ten_year_return: Optional[Decimal] = Field(None, description="10년 수익률 (%)")
    since_inception_return: Optional[Decimal] = Field(None, description="설정 이후 수익률 (%)")
    
    # 자산 분류
    asset_class: str = Field(..., description="자산군 (Equity, Fixed Income 등)")
    region: str = Field(..., description="지역 (North America, Global 등)")
    market_type: str = Field(..., description="시장 유형 (Developed, Emerging 등)")
    
    # 배당 정보 (있는 경우)
    distribution_yield: Optional[Decimal] = Field(None, description="배당 수익률 (%)")
    distribution_frequency: DistributionFrequency = Field(
        default=DistributionFrequency.UNKNOWN, 
        description="배당 주기 (Monthly, Quarterly, Semi-Annual, Annual, Variable, None, Unknown)"
    )
    
    # URL
    product_page_url: str = Field(..., description="상품 페이지 URL")
    detail_page_url: Optional[str] = Field(None, description="상세 정보 페이지 URL (ETF 정보 갱신용)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "SCHD",
                "fund_name": "Schwab U.S. Dividend Equity ETF",
                "isin": "US8085241054",
                "cusip": "808524105",
                "inception_date": "2011-10-20",
                "nav_amount": "31.45",
                "nav_as_of": "2025-11-28",
                "expense_ratio": "0.06",
                "ytd_return": "12.50",
                "one_year_return": "15.30",
                "three_year_return": "18.20",
                "five_year_return": "12.10",
                "ten_year_return": "11.50",
                "since_inception_return": "10.80",
                "asset_class": "Equity",
                "region": "North America",
                "market_type": "Developed",
                "distribution_yield": "3.45",
                "distribution_frequency": "Quarterly",
                "product_page_url": "/us/products/239737/schwab-us-dividend-equity-etf",
                "detail_page_url": "https://www.schwabassetmanagement.com/products/schd"
            }
        }


class ETFDetail(ETF):
    """ETF 상세 정보 (추가 필드)"""
    
    # 포트폴리오 정보
    portfolio_id: Optional[int] = Field(None, description="포트폴리오 ID")
    
    # 분기별 성과 정보
    quarterly_nav_ytd: Optional[Decimal] = Field(None, description="분기별 NAV YTD")
    quarterly_nav_one_year: Optional[Decimal] = Field(None, description="분기별 NAV 1년")
    quarterly_nav_three_year: Optional[Decimal] = Field(None, description="분기별 NAV 3년")
    quarterly_nav_five_year: Optional[Decimal] = Field(None, description="분기별 NAV 5년")
    
    # 투자 스타일
    investment_style: Optional[str] = Field(None, description="투자 스타일 (Index, Active 등)")
    
    class Config:
        json_schema_extra = {
            "example": {
                **ETF.Config.json_schema_extra["example"],
                "portfolio_id": 239737,
                "quarterly_nav_ytd": "12.35",
                "quarterly_nav_one_year": "15.20",
                "quarterly_nav_three_year": "18.10",
                "quarterly_nav_five_year": "12.00",
                "investment_style": "Index"
            }
        }


class ETFDividendInfo(BaseModel):
    """ETF 배당 정보"""
    
    ticker: str = Field(..., description="티커 심볼")
    fund_name: str = Field(..., description="펀드명")
    
    # 배당 수익률
    distribution_yield: Decimal = Field(..., description="배당 수익률 (%)")
    
    # 배당 지급 주기 (월별, 분기별, 연별 등)
    distribution_frequency: str = Field(..., description="배당 지급 주기")
    
    # 다음 배당 예정일
    next_ex_dividend_date: Optional[date] = Field(None, description="다음 배당락일")
    
    # 요일 정보 (배당금 지급 요일별 분류용)
    ex_dividend_day_of_week: Optional[str] = Field(None, description="배당락일 요일")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "SCHD",
                "fund_name": "Schwab U.S. Dividend Equity ETF",
                "distribution_yield": "3.45",
                "distribution_frequency": "Quarterly",
                "next_ex_dividend_date": "2025-12-15",
                "ex_dividend_day_of_week": "Monday"
            }
        }


class TotalReturnETF(BaseModel):
    """Total Return ETF 정보"""
    
    ticker: str = Field(..., description="티커 심볼")
    fund_name: str = Field(..., description="펀드명")
    
    # Total Return 여부 식별
    is_total_return: bool = Field(True, description="Total Return ETF 여부")
    
    # 수익률 지표
    ytd_return: Decimal = Field(..., description="연초 대비 수익률 (%)")
    one_year_return: Optional[Decimal] = Field(None, description="1년 수익률 (%)")
    three_year_return: Optional[Decimal] = Field(None, description="3년 수익률 (%)")
    five_year_return: Optional[Decimal] = Field(None, description="5년 수익률 (%)")
    
    # 현재 가격
    nav_amount: Decimal = Field(..., description="현재 NAV")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "SCHD",
                "fund_name": "Schwab U.S. Dividend Equity ETF",
                "is_total_return": True,
                "ytd_return": "12.50",
                "one_year_return": "15.30",
                "three_year_return": "18.20",
                "five_year_return": "12.10",
                "nav_amount": "31.45"
            }
        }
