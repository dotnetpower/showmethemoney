"""
Data Processing Agent 테스트
"""

import pytest

from backend.app.agents.data_processing_agent import DataProcessingAgent


@pytest.fixture
def processing_agent():
    """Data Processing Agent 픽스처"""
    return DataProcessingAgent({"use_msgpack": False})


@pytest.fixture
def sample_data():
    """테스트용 샘플 데이터"""
    return [
        {"ticker": "SPY", "name": "SPDR S&P 500 ETF", "price": 450.0, "empty_field": ""},
        {"ticker": "QQQ", "name": "Invesco QQQ Trust", "price": 380.0, "null_field": None},
        {"ticker": "SPY", "name": "Duplicate", "price": 450.0},  # 중복
    ]


@pytest.mark.asyncio
async def test_agent_initialization(processing_agent: DataProcessingAgent):
    """Agent 초기화 테스트"""
    assert processing_agent.name == "DataProcessing"
    assert processing_agent.use_msgpack is False


@pytest.mark.asyncio
async def test_validate_operations(processing_agent: DataProcessingAgent):
    """작업 검증 테스트"""
    # 유효한 작업
    assert await processing_agent.validate_operation(operation="clean", data=[1, 2, 3]) is True
    assert await processing_agent.validate_operation(operation="transform", data={"key": "value"}) is True
    assert await processing_agent.validate_operation(operation="deduplicate", data=[1, 2]) is True
    
    # 유효하지 않은 작업
    assert await processing_agent.validate_operation(operation="clean", data=None) is False
    assert await processing_agent.validate_operation(operation="invalid", data=[1]) is False


@pytest.mark.asyncio
async def test_clean_data(processing_agent: DataProcessingAgent, sample_data):
    """데이터 정제 테스트"""
    result = await processing_agent.execute(operation="clean", data=sample_data)
    
    assert result["status"] == "success"
    assert result["operation"] == "clean"
    
    cleaned_data = result["data"]
    assert len(cleaned_data) > 0
    
    # empty_field와 null_field가 제거되었는지 확인
    for item in cleaned_data:
        assert "empty_field" not in item
        assert "null_field" not in item


@pytest.mark.asyncio
async def test_transform_to_json(processing_agent: DataProcessingAgent, sample_data):
    """șON 변환 테스트"""
    result = await processing_agent.execute(
        operation="transform",
        data=sample_data,
        format="json"
    )
    
    assert result["status"] == "success"
    assert isinstance(result["data"], str)
    
    # JSON 문자열인지 확인
    import json
    parsed = json.loads(result["data"])
    assert isinstance(parsed, list)


@pytest.mark.asyncio
async def test_transform_to_msgpack(processing_agent: DataProcessingAgent, sample_data):
    """MessagePack 변환 테스트"""
    result = await processing_agent.execute(
        operation="transform",
        data=sample_data,
        format="msgpack"
    )
    
    assert result["status"] == "success"
    assert isinstance(result["data"], bytes)


@pytest.mark.asyncio
async def test_validate_data(processing_agent: DataProcessingAgent, sample_data):
    """데이터 유효성 검사 테스트"""
    result = await processing_agent.execute(operation="validate", data=sample_data)
    
    assert result["status"] == "success"
    assert "data" in result
    
    validation_result = result["data"]
    assert "is_valid" in validation_result
    assert "errors" in validation_result
    assert "warnings" in validation_result


@pytest.mark.asyncio
async def test_deduplicate_data(processing_agent: DataProcessingAgent, sample_data):
    """중복 제거 테스트"""
    result = await processing_agent.execute(operation="deduplicate", data=sample_data)
    
    assert result["status"] == "success"
    deduplicated = result["data"]
    
    # SPY가 하나만 남아야 함
    spy_count = sum(1 for item in deduplicated if item.get("ticker") == "SPY")
    assert spy_count == 1


@pytest.mark.asyncio
async def test_compress_decompress(processing_agent: DataProcessingAgent, sample_data):
    """압축/압축 해제 테스트"""
    # 압축
    compressed = await processing_agent.compress_data(sample_data)
    assert isinstance(compressed, bytes)
    
    # 압축 해제
    decompressed = await processing_agent.decompress_data(compressed)
    assert decompressed == sample_data


@pytest.mark.asyncio
async def test_invalid_format(processing_agent: DataProcessingAgent, sample_data):
    """잘못된 형식 변환 테스트"""
    result = await processing_agent.execute(
        operation="transform",
        data=sample_data,
        format="invalid_format"
    )
    
    assert result["status"] == "error"
    assert "error" in result
