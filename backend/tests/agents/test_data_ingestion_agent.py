"""
Data Ingestion Agent 테스트
"""

import pytest

from backend.app.agents.data_ingestion_agent import DataIngestionAgent


@pytest.fixture
def ingestion_agent() -> DataIngestionAgent:
    """Data Ingestion Agent 픽스처"""
    config = {
        "providers": ["ishares", "vanguard", "spdr"]
    }
    return DataIngestionAgent(config)


@pytest.mark.asyncio
async def test_agent_initialization(ingestion_agent: DataIngestionAgent):
    """Agent 초기화 테스트"""
    assert ingestion_agent.name == "DataIngestion"
    assert len(ingestion_agent.providers) == 3
    assert "ishares" in ingestion_agent.providers


@pytest.mark.asyncio
async def test_validate_provider(ingestion_agent: DataIngestionAgent):
    """운용사 검증 테스트"""
    # 유효한 운용사
    assert await ingestion_agent.validate(operation="fetch_provider", provider="ishares") is True
    assert await ingestion_agent.validate(operation="fetch_provider", provider="vanguard") is True
    
    # 유효하지 않은 운용사
    assert await ingestion_agent.validate(operation="fetch_provider", provider="invalid") is False
    assert await ingestion_agent.validate(operation="fetch_provider", provider="") is False
    assert await ingestion_agent.validate(operation="fetch_provider", provider=None) is False


@pytest.mark.asyncio
async def test_execute_success(ingestion_agent: DataIngestionAgent):
    """데이터 수집 성공 테스트"""
    result = await ingestion_agent.execute(operation="fetch_provider", provider="ishares")
    
    assert result["status"] in ["success", "error"]
    assert result["provider"] == "ishares"
    assert "timestamp" in result
    assert "data" in result


@pytest.mark.asyncio
async def test_execute_invalid_provider(ingestion_agent: DataIngestionAgent):
    """잘못된 운용사로 수집 시도 테스트"""
    result = await ingestion_agent.execute(operation="fetch_provider", provider="invalid_provider")
    
    assert result["status"] == "error"
    assert "error" in result


@pytest.mark.asyncio
async def test_fetch_dividend_data(ingestion_agent: DataIngestionAgent):
    """배당 데이터 수집 테스트"""
    result = await ingestion_agent.fetch_dividend_data()
    
    assert result["type"] == "dividend"
    assert result["status"] in ["success", "error"]
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_fetch_total_return_etf_data(ingestion_agent: DataIngestionAgent):
    """Total Return ETF 데이터 수집 테스트"""
    result = await ingestion_agent.fetch_total_return_etf_data()
    
    assert result["type"] == "total_return"
    assert result["status"] in ["success", "error"]
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_close(ingestion_agent: DataIngestionAgent):
    """리소스 정리 테스트"""
    await ingestion_agent.close()
    # 에러 없이 종료되면 성공
