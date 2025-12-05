"""
Data Ingestion 및 Processing Agents 사용 예제
실제 OpenAI API 키 없이 동작하는 기본 기능 테스트
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.agents import DataIngestionAgent, DataProcessingAgent


async def example_1_data_ingestion():
    """예제 1: 데이터 수집 Agent"""
    print("\n" + "=" * 60)
    print("예제 1: DataIngestionAgent 기본 사용")
    print("=" * 60)
    
    config = {
        "providers": ["ishares", "vanguard", "spdr"]
    }
    
    agent = DataIngestionAgent(config)
    
    # 1. 작업 검증
    print("\n1. 작업 검증 테스트...")
    
    valid_cases = [
        ("fetch_provider", {"provider": "ishares"}, True),
        ("fetch_dividend", {}, True),
        ("fetch_total_return", {}, True),
        ("invalid_operation", {}, False),
        ("fetch_provider", {}, False),  # provider 누락
    ]
    
    for operation, kwargs, expected in valid_cases:
        result = await agent.validate(operation=operation, **kwargs)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {operation} with {kwargs}: {result} (expected {expected})")
    
    # 2. execute 메서드 테스트
    print("\n2. Execute 메서드 테스트...")
    
    # 유효한 작업 (실제 API 호출 없이 에러 처리 확인)
    result = await agent.execute(
        operation="fetch_provider",
        provider="ishares"
    )
    print(f"  - fetch_provider 결과: {result['status']}")
    
    # 잘못된 작업
    result = await agent.execute(
        operation="invalid_operation"
    )
    print(f"  - invalid_operation 결과: {result['status']}")
    
    # 파라미터 누락
    result = await agent.execute(
        operation="fetch_provider"
    )
    print(f"  - fetch_provider (파라미터 누락) 결과: {result['status']}")
    
    # 리소스 정리
    await agent.close()
    print("\n리소스 정리 완료")


async def example_2_data_processing():
    """예제 2: 데이터 처리 Agent"""
    print("\n" + "=" * 60)
    print("예제 2: DataProcessingAgent 기본 사용")
    print("=" * 60)
    
    config = {
        "use_msgpack": False
    }
    
    agent = DataProcessingAgent(config)
    
    # 테스트 데이터
    sample_data = [
        {"ticker": "SPY", "name": "SPDR S&P 500", "price": 450.0, "empty": ""},
        {"ticker": "QQQ", "name": "Invesco QQQ", "price": 380.0, "null": None},
        {"ticker": "SPY", "name": "SPDR S&P 500", "price": 450.0},  # 중복
    ]
    
    # 1. 작업 검증
    print("\n1. 작업 검증 테스트...")
    
    valid_cases = [
        ("clean", sample_data, True),
        ("transform", sample_data, True),
        ("validate", sample_data, True),
        ("deduplicate", sample_data, True),
        ("invalid_operation", sample_data, False),
        ("clean", None, False),  # 데이터 누락
    ]
    
    for operation, data, expected in valid_cases:
        result = await agent.validate_operation(operation=operation, data=data)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {operation} with data={data is not None}: {result} (expected {expected})")
    
    # 2. Execute 메서드 테스트
    print("\n2. Execute 메서드 테스트...")
    
    # 중복 제거
    result = await agent.execute(
        operation="deduplicate",
        data=sample_data,
        key="ticker"
    )
    if result['status'] == 'success':
        print(f"  - deduplicate: {result['original_count']} → {result['unique_count']}개")
    else:
        print(f"  - deduplicate 실패: {result.get('error', 'Unknown')}")
    
    # 데이터 변환
    result = await agent.execute(
        operation="transform",
        data={"ticker": "SPY", "price": 450.0},
        format_type="json"
    )
    print(f"  - transform (json): {result['status']}")
    
    # 잘못된 작업
    result = await agent.execute(
        operation="invalid_operation",
        data=sample_data
    )
    print(f"  - invalid_operation: {result['status']}")


async def example_3_compression():
    """예제 3: 데이터 압축/해제"""
    print("\n" + "=" * 60)
    print("예제 3: 데이터 압축 및 해제")
    print("=" * 60)
    
    agent = DataProcessingAgent()
    
    # 원본 데이터
    original_data = [
        {"ticker": f"ETF{i:03d}", "price": 100.0 + i}
        for i in range(100)
    ]
    
    original_json = json.dumps(original_data, ensure_ascii=False)
    original_size = len(original_json.encode('utf-8'))
    
    print(f"\n원본 데이터:")
    print(f"  - 항목 수: {len(original_data)}")
    print(f"  - JSON 크기: {original_size:,} bytes")
    
    # 압축
    compressed = await agent.compress_data(original_data)
    print(f"\n압축 후:")
    print(f"  - 크기: {len(compressed):,} bytes")
    print(f"  - 압축률: {(1 - len(compressed)/original_size)*100:.1f}%")
    
    # 압축 해제
    decompressed = await agent.decompress_data(compressed)
    print(f"\n압축 해제:")
    print(f"  - 항목 수: {len(decompressed)}")
    print(f"  - 데이터 무결성: {'✓ 통과' if decompressed == original_data else '✗ 실패'}")


async def example_4_integration():
    """예제 4: 통합 워크플로우"""
    print("\n" + "=" * 60)
    print("예제 4: 통합 워크플로우 (수집 → 처리 → 저장)")
    print("=" * 60)
    
    # 1. 샘플 수집 데이터 시뮬레이션
    print("\n1. 데이터 수집 시뮬레이션...")
    collected_data = [
        {"ticker": "SPY", "name": "SPDR S&P 500", "price": 450.0, "empty": "", "null": None},
        {"ticker": "QQQ", "name": "Invesco QQQ", "price": 380.0, "volume": 50000000},
        {"ticker": "SPY", "name": "SPDR S&P 500", "price": 450.0},  # 중복
        {"ticker": "IVV", "name": "iShares S&P 500", "price": 449.0, "": "invalid_key"},
    ]
    print(f"  - 수집된 데이터: {len(collected_data)}개")
    
    # 2. 데이터 처리
    print("\n2. 데이터 처리...")
    processing_agent = DataProcessingAgent()
    
    # 2.1. 중복 제거
    dedup_result = await processing_agent.execute(
        operation="deduplicate",
        data=collected_data,
        key="ticker"
    )
    
    if dedup_result['status'] == 'success':
        unique_data = dedup_result['data']
        print(f"  - 중복 제거: {dedup_result['original_count']} → {dedup_result['unique_count']}개")
    else:
        print(f"  - 중복 제거 실패")
        unique_data = collected_data
    
    # 2.2. 데이터 정제 (실제로는 tools 함수 직접 사용)
    from backend.app.agents.data_processing_agent import clean_data_item
    
    cleaned_data = [clean_data_item(item) for item in unique_data]
    print(f"  - 데이터 정제 완료: {len(cleaned_data)}개")
    
    # 2.3. 유효성 검증
    from backend.app.agents.data_processing_agent import \
        validate_data_structure
    
    validation_result = validate_data_structure(cleaned_data)
    print(f"  - 유효성 검증: {'✓ 통과' if validation_result['is_valid'] else '✗ 실패'}")
    if validation_result['errors']:
        print(f"    에러: {validation_result['errors']}")
    if validation_result['warnings']:
        print(f"    경고: {validation_result['warnings']}")
    
    # 3. 최종 데이터
    print("\n3. 최종 처리된 데이터:")
    for i, item in enumerate(cleaned_data, 1):
        print(f"  {i}. {item['ticker']}: {item.get('name', 'N/A')} - ${item.get('price', 0)}")
    
    # 4. 압축 (선택)
    compressed = await processing_agent.compress_data(cleaned_data)
    json_size = len(json.dumps(cleaned_data).encode('utf-8'))
    print(f"\n4. 압축:")
    print(f"  - JSON 크기: {json_size:,} bytes")
    print(f"  - 압축 크기: {len(compressed):,} bytes")
    print(f"  - 압축률: {(1 - len(compressed)/json_size)*100:.1f}%")


async def main():
    """모든 예제 실행"""
    print("\n" + "=" * 80)
    print(" " * 15 + "Data Ingestion & Processing Agents 예제")
    print("=" * 80)
    
    examples = [
        ("DataIngestionAgent", example_1_data_ingestion),
        ("DataProcessingAgent", example_2_data_processing),
        ("데이터 압축/해제", example_3_compression),
        ("통합 워크플로우", example_4_integration),
    ]
    
    for name, example_func in examples:
        try:
            await example_func()
            print(f"\n✓ {name} 완료")
        except Exception as e:
            print(f"\n✗ {name} 실패: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(" " * 20 + "모든 예제 실행 완료!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
