"""
Data Storage Agent 테스트
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from backend.app.agents.data_storage_agent import DataStorageAgent


@pytest.fixture
def temp_dir():
    """임시 디렉토리 픽스처"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # 테스트 후 정리
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def storage_agent(temp_dir):
    """Data Storage Agent 픽스처"""
    config = {
        "data_dir": str(temp_dir),
        "max_file_size": 1024,  # 1KB (테스트용 작은 크기)
        "use_branches": False  # Git 작업 비활성화
    }
    return DataStorageAgent(config)


@pytest.fixture
def sample_data():
    """테스트용 샘플 데이터"""
    return {
        "ticker": "SPY",
        "name": "SPDR S&P 500 ETF",
        "price": 450.0,
        "holdings": ["AAPL", "MSFT", "GOOGL"]
    }


@pytest.mark.asyncio
async def test_agent_initialization(storage_agent, temp_dir):
    """Agent 초기화 테스트"""
    assert storage_agent.name == "DataStorage"
    assert storage_agent.data_dir == temp_dir
    assert storage_agent.max_file_size == 1024


@pytest.mark.asyncio
async def test_validate_operations(storage_agent, sample_data):
    """작업 검증 테스트"""
    # 유효한 작업
    assert await storage_agent.validate(operation="save", data=sample_data, path="test.json") is True
    assert await storage_agent.validate(operation="load", path="test.json") is True
    assert await storage_agent.validate(operation="delete", path="test.json") is True
    
    # 유효하지 않은 작업
    assert await storage_agent.validate(operation="invalid") is False
    assert await storage_agent.validate(operation="save", data=sample_data) is False
    assert await storage_agent.validate(operation="load") is False


@pytest.mark.asyncio
async def test_save_and_load_data(storage_agent: DataStorageAgent, sample_data):
    """데이터 저장 및 로드 테스트"""
    path = "test/data.json"
    
    # 저장
    save_result = await storage_agent.execute(
        operation="save",
        data=sample_data,
        path=path
    )
    
    assert save_result["status"] == "success"
    assert save_result["operation"] == "save"
    
    # 로드
    load_result = await storage_agent.execute(
        operation="load",
        path=path
    )
    
    assert load_result["status"] == "success"
    assert load_result["data"] == sample_data


@pytest.mark.asyncio
async def test_save_large_data(storage_agent: DataStorageAgent):
    """대용량 데이터 분할 저장 테스트"""
    # 큰 데이터 생성 (max_file_size를 초과하도록)
    large_data = [
        {"ticker": f"TICK{i}", "name": f"Stock {i}", "price": i * 10.0}
        for i in range(100)
    ]
    
    path = "test/large_data.json"
    
    # 저장
    save_result = await storage_agent.execute(
        operation="save",
        data=large_data,
        path=path
    )
    
    assert save_result["status"] == "success"
    # 분할 저장되었는지 확인
    if save_result.get("type") == "chunked":
        assert save_result["chunks"] > 1
    
    # 로드
    load_result = await storage_agent.execute(
        operation="load",
        path=path
    )
    
    assert load_result["status"] == "success"
    assert len(load_result["data"]) == len(large_data)


@pytest.mark.asyncio
async def test_delete_data(storage_agent: DataStorageAgent, sample_data):
    """데이터 삭제 테스트"""
    path = "test/delete_me.json"
    
    # 먼저 저장
    await storage_agent.execute(
        operation="save",
        data=sample_data,
        path=path
    )
    
    # 삭제
    delete_result = await storage_agent.execute(
        operation="delete",
        path=path
    )
    
    assert delete_result["status"] == "success"
    
    # 로드 시도 - 실패해야 함
    load_result = await storage_agent.execute(
        operation="load",
        path=path
    )
    
    assert load_result["status"] == "error"


@pytest.mark.asyncio
async def test_metadata_creation(storage_agent: DataStorageAgent, sample_data, temp_dir):
    """메타데이터 생성 테스트"""
    path = "test/with_metadata.json"
    
    await storage_agent.execute(
        operation="save",
        data=sample_data,
        path=path
    )
    
    # 메타데이터 파일이 생성되었는지 확인
    metadata_path = temp_dir / "test" / "with_metadata_metadata.json"
    assert metadata_path.exists()
    
    # 메타데이터 내용 확인
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert "path" in metadata
    assert "size" in metadata
    assert "timestamp" in metadata


@pytest.mark.asyncio
async def test_load_nonexistent_file(storage_agent: DataStorageAgent):
    """존재하지 않는 파일 로드 테스트"""
    result = await storage_agent.execute(
        operation="load",
        path="nonexistent/file.json"
    )
    
    assert result["status"] == "error"
    assert "error" in result
