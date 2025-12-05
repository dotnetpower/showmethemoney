"""
API Agent 테스트
"""

import pytest

from backend.app.agents.api_agent import APIAgent


@pytest.fixture
def api_agent():
    """API Agent 픽스처"""
    config = {
        "cache_ttl": 60  # 60초
    }
    return APIAgent(config)


@pytest.mark.asyncio
async def test_agent_initialization(api_agent):
    """Agent 초기화 테스트"""
    assert api_agent.name == "API"
    assert api_agent.cache_ttl == 60
    assert len(api_agent.cache) == 0


@pytest.mark.asyncio
async def test_validate_endpoints(api_agent):
    """엔드포인트 검증 테스트"""
    # 유효한 엔드포인트
    assert await api_agent.validate(endpoint="/etf/list") is True
    assert await api_agent.validate(endpoint="/dividend/daily") is True
    assert await api_agent.validate(endpoint="/provider/list") is True
    
    # ticker 필수 파라미터가 있는 경우
    assert await api_agent.validate(endpoint="/etf/detail", ticker="SPY") is True
    assert await api_agent.validate(endpoint="/etf/detail") is False
    
    # 유효하지 않은 엔드포인트
    assert await api_agent.validate(endpoint="/invalid/endpoint") is False


@pytest.mark.asyncio
async def test_get_etf_list(api_agent):
    """ETF 목록 조회 테스트"""
    result = await api_agent.execute(endpoint="/etf/list")
    
    assert result["endpoint"] == "/etf/list"
    assert result["status"] in ["success", "error"]
    assert "data" in result


@pytest.mark.asyncio
async def test_get_etf_detail(api_agent):
    """ETF 상세 정보 조회 테스트"""
    result = await api_agent.execute(endpoint="/etf/detail", ticker="SPY")
    
    assert result["endpoint"] == "/etf/detail"
    assert result["status"] in ["success", "error"]
    assert "data" in result


@pytest.mark.asyncio
async def test_get_provider_list(api_agent):
    """운용사 목록 조회 테스트"""
    result = await api_agent.execute(endpoint="/provider/list")
    
    assert result["endpoint"] == "/provider/list"
    assert result["status"] in ["success", "error"]
    assert "data" in result


@pytest.mark.asyncio
async def test_cache_functionality(api_agent):
    """캐시 기능 테스트"""
    # 첫 번째 요청
    result1 = await api_agent.execute(endpoint="/provider/list")
    assert result1.get("cached") is False
    
    # 두 번째 요청 (캐시 사용)
    result2 = await api_agent.execute(endpoint="/provider/list")
    assert result2.get("cached") is True
    
    # 캐시 클리어
    api_agent.clear_cache()
    
    # 세 번째 요청 (캐시 미사용)
    result3 = await api_agent.execute(endpoint="/provider/list")
    assert result3.get("cached") is False


@pytest.mark.asyncio
async def test_invalid_endpoint(api_agent):
    """잘못된 엔드포인트 테스트"""
    result = await api_agent.execute(endpoint="/invalid/path")
    
    assert result["status"] == "error"
    assert "error" in result
