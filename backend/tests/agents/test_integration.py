"""
Agents 통합 테스트 예제
"""

import asyncio
import json
from pathlib import Path

from backend.app.agents import (APIAgent, DataIngestionAgent,
                                DataProcessingAgent, DataStorageAgent)


async def test_basic_workflow():
    """기본 워크플로우 테스트"""
    
    # 설정
    config = {
        "data_dir": "data",
        "max_file_size": 4 * 1024 * 1024,
        "use_branches": False,  # 테스트에서는 Git 작업 비활성화
        "cache_ttl": 300
    }
    
    print("=" * 60)
    print("Agents 통합 테스트 시작")
    print("=" * 60)
    
    # 1. 샘플 데이터 생성
    print("\n1. 샘플 데이터 생성...")
    sample_etf_data = [
        {
            "ticker": "SPY",
            "name": "SPDR S&P 500 ETF Trust",
            "provider": "SPDR",
            "price": 450.0,
            "dividend_yield": 1.5
        },
        {
            "ticker": "QQQ",
            "name": "Invesco QQQ Trust",
            "provider": "Invesco",
            "price": 380.0,
            "dividend_yield": 0.6
        },
        {
            "ticker": "IVV",
            "name": "iShares Core S&P 500 ETF",
            "provider": "iShares",
            "price": 449.0,
            "dividend_yield": 1.4
        }
    ]
    print(f"  - 생성된 ETF 데이터: {len(sample_etf_data)}개")
    
    # 2. 데이터 처리 Agent 테스트
    print("\n2. 데이터 처리 Agent 테스트...")
    processing_agent = DataProcessingAgent(config)
    
    # 중복 제거 테스트
    duplicated_data = sample_etf_data + [sample_etf_data[0]]  # SPY 중복
    deduplicated = await processing_agent.deduplicate(duplicated_data)
    print(f"  - 중복 제거: {len(duplicated_data)}개 -> {deduplicated['unique_count']}개")
    
    # 데이터 정제 테스트
    dirty_data = [
        {"ticker": "TEST", "name": "Test ETF", "empty": "", "null": None},
        {"ticker": "TEST2", "name": "Test ETF 2", "value": 100}
    ]
    cleaned = await processing_agent.clean(dirty_data)
    print(f"  - 데이터 정제 완료: {cleaned['status']}")
    
    # 3. 데이터 저장 Agent 테스트
    print("\n3. 데이터 저장 Agent 테스트...")
    storage_agent = DataStorageAgent(config)
    
    # 데이터 저장
    test_path = "test/sample_etf_list.json"
    save_result = await storage_agent.execute(
        operation="save",
        data=sample_etf_data,
        path=test_path
    )
    print(f"  - 저장 결과: {save_result['status']}")
    if save_result['status'] == 'success':
        print(f"  - 저장 경로: {save_result.get('path', 'N/A')}")
    
    # 데이터 로드
    load_result = await storage_agent.execute(
        operation="load",
        path=test_path
    )
    print(f"  - 로드 결과: {load_result['status']}")
    if load_result['status'] == 'success':
        loaded_data = load_result.get('data', {})
        if isinstance(loaded_data, dict):
            # Agent가 반환한 텍스트 결과를 파싱해야 할 수 있음
            print(f"  - 로드된 데이터 타입: {type(loaded_data)}")
        else:
            print(f"  - 로드된 항목 수: {len(loaded_data) if isinstance(loaded_data, list) else 'N/A'}")
    
    # 4. API Agent 테스트
    print("\n4. API Agent 테스트...")
    api_agent = APIAgent(config)
    
    # 운용사 목록 조회
    providers = await api_agent._get_provider_list()
    print(f"  - 운용사 목록: {len(providers)}개")
    if providers:
        print(f"  - 예시: {providers[0]['display_name']}")
    
    # ETF 상세 조회 (저장된 데이터가 있다면)
    if Path(config['data_dir']).exists():
        etf_detail = await api_agent._get_etf_detail("SPY")
        print(f"  - SPY 조회 결과: {etf_detail.get('name', 'Not found')}")
    
    # 5. 대용량 데이터 처리 테스트
    print("\n5. 대용량 데이터 처리 테스트...")
    large_data = [
        {"ticker": f"ETF{i:04d}", "name": f"Test ETF {i}", "price": 100.0 + i}
        for i in range(500)
    ]
    
    # 데이터 크기 확인
    data_size = len(json.dumps(large_data).encode('utf-8'))
    print(f"  - 생성된 데이터 크기: {data_size:,} bytes")
    
    # 압축 테스트
    compressed = await processing_agent.compress_data(large_data)
    print(f"  - 압축 후 크기: {len(compressed):,} bytes")
    print(f"  - 압축률: {(1 - len(compressed)/data_size)*100:.1f}%")
    
    # 압축 해제
    decompressed = await processing_agent.decompress_data(compressed)
    print(f"  - 압축 해제 후 항목 수: {len(decompressed)}")
    print(f"  - 데이터 무결성: {'OK' if decompressed == large_data else 'FAIL'}")
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)


async def test_error_handling():
    """에러 핸들링 테스트"""
    
    print("\n" + "=" * 60)
    print("에러 핸들링 테스트")
    print("=" * 60)
    
    config = {
        "data_dir": "data",
        "use_branches": False
    }
    
    storage_agent = DataStorageAgent(config)
    
    # 1. 존재하지 않는 파일 로드
    print("\n1. 존재하지 않는 파일 로드...")
    result = await storage_agent.execute(
        operation="load",
        path="non_existent_file.json"
    )
    print(f"  - 결과: {result['status']}")
    if result['status'] == 'error':
        print(f"  - 에러 메시지: {result.get('error', 'N/A')[:50]}...")
    
    # 2. 잘못된 작업
    print("\n2. 잘못된 작업 타입...")
    result = await storage_agent.execute(
        operation="invalid_operation",
        path="test.json"
    )
    print(f"  - 결과: {result['status']}")
    
    # 3. 필수 파라미터 누락
    print("\n3. 필수 파라미터 누락...")
    result = await storage_agent.execute(
        operation="save"
        # data와 path 파라미터 누락
    )
    print(f"  - 결과: {result['status']}")
    
    print("\n에러 핸들링 테스트 완료!")


async def test_validation():
    """유효성 검증 테스트"""
    
    print("\n" + "=" * 60)
    print("유효성 검증 테스트")
    print("=" * 60)
    
    config = {"data_dir": "data", "use_branches": False}
    storage_agent = DataStorageAgent(config)
    
    # 1. 올바른 save 작업
    print("\n1. 올바른 작업 검증...")
    valid = await storage_agent.validate(
        operation="save",
        data={"test": "data"},
        path="test.json"
    )
    print(f"  - save (유효한 파라미터): {valid}")
    
    # 2. 잘못된 작업
    print("\n2. 잘못된 작업 검증...")
    invalid = await storage_agent.validate(
        operation="invalid"
    )
    print(f"  - invalid operation: {invalid}")
    
    # 3. 파라미터 누락
    print("\n3. 파라미터 누락 검증...")
    missing = await storage_agent.validate(
        operation="save",
        data={"test": "data"}
        # path 누락
    )
    print(f"  - save (path 누락): {missing}")
    
    print("\n유효성 검증 테스트 완료!")


async def main():
    """메인 테스트 실행"""
    try:
        await test_basic_workflow()
        await test_error_handling()
        await test_validation()
        
        print("\n" + "=" * 60)
        print("모든 테스트 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Note: Agent들은 OpenAI API를 사용하므로 실제 실행시 API 키가 필요합니다
    # 환경 변수로 OPENAI_API_KEY를 설정하거나 config에 추가하세요
    
    print("\n⚠️  주의: 이 테스트는 OpenAI API를 사용합니다.")
    print("실행하려면 OPENAI_API_KEY 환경 변수를 설정하세요.\n")
    
    # asyncio.run(main())
    
    # 실제 실행 예시:
    print("실행 방법:")
    print("1. 환경 변수 설정: export OPENAI_API_KEY='your-api-key'")
    print("2. config에 openai_api_key 추가")
    print("3. python -m backend.tests.agents.test_integration")
