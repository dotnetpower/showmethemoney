"""
Monitoring Agent 테스트
"""

from datetime import datetime, timedelta

import pytest

from backend.app.agents.monitoring_agent import MonitoringAgent


@pytest.fixture
def monitoring_agent():
    """Monitoring Agent 픽스처"""
    # Azure Monitor 없이 테스트
    return MonitoringAgent()


@pytest.mark.asyncio
async def test_agent_initialization(monitoring_agent):
    """Agent 초기화 테스트"""
    assert monitoring_agent.name == "Monitoring"
    assert len(monitoring_agent.metrics_data) == 0
    assert len(monitoring_agent.traces_data) == 0


@pytest.mark.asyncio
async def test_validate_operations(monitoring_agent):
    """작업 검증 테스트"""
    # 유효한 작업
    assert await monitoring_agent.validate(operation="track_request") is True
    assert await monitoring_agent.validate(operation="track_error") is True
    assert await monitoring_agent.validate(operation="track_metric") is True
    assert await monitoring_agent.validate(operation="get_metrics") is True
    assert await monitoring_agent.validate(operation="get_health") is True
    
    # 유효하지 않은 작업
    assert await monitoring_agent.validate(operation="invalid") is False


@pytest.mark.asyncio
async def test_track_request(monitoring_agent):
    """API 요청 추적 테스트"""
    result = await monitoring_agent.execute(
        operation="track_request",
        name="test_api_call",
        duration=125.5,
        success=True,
        endpoint="/test"
    )
    
    assert result["status"] == "success"
    assert result["operation"] == "track_request"
    assert result["name"] == "test_api_call"
    
    # 메트릭 데이터에 저장되었는지 확인
    assert len(monitoring_agent.metrics_data) == 1
    assert monitoring_agent.metrics_data[0]["type"] == "request"
    assert monitoring_agent.metrics_data[0]["name"] == "test_api_call"
    assert monitoring_agent.metrics_data[0]["duration"] == 125.5


@pytest.mark.asyncio
async def test_track_error(monitoring_agent):
    """에러 추적 테스트"""
    result = await monitoring_agent.execute(
        operation="track_error",
        error_type="ValueError",
        message="Invalid input",
        component="data_processor"
    )
    
    assert result["status"] == "success"
    assert result["operation"] == "track_error"
    assert result["error_type"] == "ValueError"
    
    # 메트릭 데이터에 저장되었는지 확인
    assert len(monitoring_agent.metrics_data) == 1
    assert monitoring_agent.metrics_data[0]["type"] == "error"
    assert monitoring_agent.metrics_data[0]["error_type"] == "ValueError"


@pytest.mark.asyncio
async def test_track_metric(monitoring_agent):
    """커스텀 메트릭 추적 테스트"""
    result = await monitoring_agent.execute(
        operation="track_metric",
        name="etf_count",
        value=150.0,
        provider="ishares"
    )
    
    assert result["status"] == "success"
    assert result["name"] == "etf_count"
    assert result["value"] == 150.0
    
    # 메트릭 데이터 확인
    assert len(monitoring_agent.metrics_data) == 1
    assert monitoring_agent.metrics_data[0]["type"] == "metric"


@pytest.mark.asyncio
async def test_get_metrics(monitoring_agent):
    """메트릭 조회 테스트"""
    # 먼저 몇 개의 메트릭 추가
    await monitoring_agent.execute(
        operation="track_request",
        name="api1",
        duration=100,
        success=True
    )
    await monitoring_agent.execute(
        operation="track_error",
        error_type="TestError",
        message="Test"
    )
    await monitoring_agent.execute(
        operation="track_metric",
        name="custom",
        value=42
    )
    
    # 전체 메트릭 조회
    result = await monitoring_agent.execute(operation="get_metrics")
    
    assert result["status"] == "success"
    assert result["count"] == 3
    assert len(result["data"]) == 3
    
    # 특정 타입 필터링
    result = await monitoring_agent.execute(
        operation="get_metrics",
        metric_type="error"
    )
    
    assert result["count"] == 1
    assert result["data"][0]["type"] == "error"


@pytest.mark.asyncio
async def test_get_health(monitoring_agent):
    """헬스 체크 테스트"""
    # 정상 상태
    result = await monitoring_agent.execute(operation="get_health")
    
    assert result["status"] == "healthy"
    assert "details" in result
    assert "recent_errors" in result["details"]
    assert "avg_latency_ms" in result["details"]
    
    # 에러가 많은 상태
    for i in range(15):
        await monitoring_agent.execute(
            operation="track_error",
            error_type="TestError",
            message=f"Error {i}"
        )
    
    result = await monitoring_agent.execute(operation="get_health")
    assert result["status"] == "unhealthy"


@pytest.mark.asyncio
async def test_start_trace(monitoring_agent):
    """트레이스 시작 테스트"""
    span = monitoring_agent.start_trace("test_operation")
    
    assert span is not None
    
    # with 문으로 사용 가능해야 함
    with monitoring_agent.start_trace("test_op_2") as span:
        assert span is not None
