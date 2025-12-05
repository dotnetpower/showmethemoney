#!/usr/bin/env python3
"""
Agents 간단한 사용 예제
실제 OpenAI API 키 없이 동작하는 기본 기능 테스트
"""

import asyncio
import json
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.agents.data_processing_agent import (clean_data_item,
                                                      remove_duplicates,
                                                      validate_data_structure)
from backend.app.agents.data_storage_agent import (delete_file, load_json_file,
                                                   save_json_file)


async def example_1_basic_storage():
    """예제 1: 기본 파일 저장/로드"""
    print("\n" + "=" * 60)
    print("예제 1: 기본 파일 저장 및 로드")
    print("=" * 60)
    
    # 샘플 데이터
    sample_data = {
        "ticker": "SPY",
        "name": "SPDR S&P 500 ETF Trust",
        "price": 450.0,
        "holdings": ["AAPL", "MSFT", "GOOGL", "AMZN"]
    }
    
    # 임시 디렉토리 생성
    temp_dir = Path("temp_test_data")
    temp_dir.mkdir(exist_ok=True)
    
    file_path = temp_dir / "spy_data.json"
    
    try:
        # 저장
        print(f"\n1. 데이터 저장 중: {file_path}")
        result = save_json_file(str(file_path), sample_data)
        print(f"   {result}")
        
        # 로드
        print(f"\n2. 데이터 로드 중...")
        loaded_data = load_json_file(str(file_path))
        print(f"   로드된 데이터:")
        print(f"   - Ticker: {loaded_data['ticker']}")
        print(f"   - Name: {loaded_data['name']}")
        print(f"   - Price: ${loaded_data['price']}")
        print(f"   - Holdings: {len(loaded_data['holdings'])}개")
        
        # 검증
        print(f"\n3. 데이터 무결성 검증...")
        is_same = loaded_data == sample_data
        print(f"   무결성: {'✓ 통과' if is_same else '✗ 실패'}")
        
    finally:
        # 정리
        if file_path.exists():
            delete_file(str(file_path))
            print(f"\n4. 테스트 파일 삭제 완료")
        if temp_dir.exists() and not list(temp_dir.iterdir()):
            temp_dir.rmdir()


async def example_2_data_cleaning():
    """예제 2: 데이터 정제"""
    print("\n" + "=" * 60)
    print("예제 2: 데이터 정제")
    print("=" * 60)
    
    # 더러운 데이터
    dirty_data = {
        "ticker": "QQQ",
        "name": "Invesco QQQ Trust",
        "price": 380.0,
        "empty_field": "",
        "null_field": None,
        "zero_value": 0,
        "empty_list": [],
        "valid_list": ["AAPL", "MSFT"]
    }
    
    print(f"\n원본 데이터:")
    print(f"  필드 수: {len(dirty_data)}")
    for key, value in dirty_data.items():
        print(f"  - {key}: {repr(value)}")
    
    # 정제
    print(f"\n데이터 정제 중...")
    cleaned_data = clean_data_item(dirty_data)
    
    print(f"\n정제된 데이터:")
    print(f"  필드 수: {len(cleaned_data)}")
    for key, value in cleaned_data.items():
        print(f"  - {key}: {repr(value)}")
    
    print(f"\n제거된 필드: {set(dirty_data.keys()) - set(cleaned_data.keys())}")


async def example_3_duplicate_removal():
    """예제 3: 중복 제거"""
    print("\n" + "=" * 60)
    print("예제 3: 중복 데이터 제거")
    print("=" * 60)
    
    # 중복이 있는 데이터
    etf_list = [
        {"ticker": "SPY", "name": "SPDR S&P 500", "price": 450.0},
        {"ticker": "QQQ", "name": "Invesco QQQ", "price": 380.0},
        {"ticker": "SPY", "name": "SPDR S&P 500", "price": 450.0},  # 중복
        {"ticker": "IVV", "name": "iShares S&P 500", "price": 449.0},
        {"ticker": "QQQ", "name": "Invesco QQQ", "price": 380.0},  # 중복
    ]
    
    print(f"\n원본 데이터: {len(etf_list)}개")
    for i, etf in enumerate(etf_list, 1):
        print(f"  {i}. {etf['ticker']}: {etf['name']}")
    
    # 중복 제거
    print(f"\n중복 제거 중...")
    unique_list = remove_duplicates(etf_list, key="ticker")
    
    print(f"\n중복 제거 후: {len(unique_list)}개")
    for i, etf in enumerate(unique_list, 1):
        print(f"  {i}. {etf['ticker']}: {etf['name']}")
    
    print(f"\n제거된 중복: {len(etf_list) - len(unique_list)}개")


async def example_4_data_validation():
    """예제 4: 데이터 유효성 검사"""
    print("\n" + "=" * 60)
    print("예제 4: 데이터 유효성 검사")
    print("=" * 60)
    
    # 테스트 케이스 1: 올바른 데이터
    valid_data = [
        {"ticker": "SPY", "name": "SPDR S&P 500", "price": 450.0},
        {"ticker": "QQQ", "name": "Invesco QQQ", "price": 380.0},
    ]
    
    print(f"\n테스트 1: 올바른 데이터")
    result = validate_data_structure(valid_data)
    print(f"  유효성: {result['is_valid']}")
    print(f"  에러: {result['errors']}")
    print(f"  경고: {result['warnings']}")
    
    # 테스트 케이스 2: ticker 누락
    invalid_data = [
        {"ticker": "SPY", "name": "SPDR S&P 500"},
        {"name": "Invesco QQQ"},  # ticker 누락
    ]
    
    print(f"\n테스트 2: ticker 누락")
    result = validate_data_structure(invalid_data)
    print(f"  유효성: {result['is_valid']}")
    print(f"  에러: {result['errors']}")
    print(f"  경고: {result['warnings']}")
    
    # 테스트 케이스 3: 혼합 데이터 타입
    mixed_data = [
        {"ticker": "SPY", "name": "SPDR S&P 500"},
        "Not a dictionary",  # 잘못된 타입
        {"ticker": "QQQ", "name": "Invesco QQQ"},
    ]
    
    print(f"\n테스트 3: 혼합 데이터 타입")
    result = validate_data_structure(mixed_data)
    print(f"  유효성: {result['is_valid']}")
    print(f"  에러: {result['errors']}")
    print(f"  경고: {result['warnings']}")


async def example_5_large_data():
    """예제 5: 대용량 데이터 처리"""
    print("\n" + "=" * 60)
    print("예제 5: 대용량 데이터 분할 저장")
    print("=" * 60)
    
    # 대용량 데이터 생성
    print(f"\n1. 대용량 데이터 생성 중...")
    large_dataset = [
        {
            "ticker": f"ETF{i:04d}",
            "name": f"Test ETF Number {i}",
            "price": 100.0 + (i * 0.5),
            "volume": 1000000 + i,
            "dividend_yield": 1.0 + (i % 10) * 0.1
        }
        for i in range(1000)
    ]
    
    # 크기 계산
    data_json = json.dumps(large_dataset, ensure_ascii=False)
    data_size = len(data_json.encode('utf-8'))
    
    print(f"   - 항목 수: {len(large_dataset):,}")
    print(f"   - 데이터 크기: {data_size:,} bytes ({data_size/1024:.1f} KB)")
    
    # 분할 기준 (예: 100KB)
    max_chunk_size = 100 * 1024
    
    if data_size > max_chunk_size:
        print(f"\n2. 데이터가 크기 제한({max_chunk_size:,} bytes)을 초과합니다.")
        
        # 청크 수 계산
        num_chunks = (data_size // max_chunk_size) + 1
        chunk_size = len(large_dataset) // num_chunks + 1
        
        print(f"   - 필요한 청크 수: {num_chunks}")
        print(f"   - 청크당 항목 수: ~{chunk_size}")
        
        # 분할
        print(f"\n3. 데이터 분할 중...")
        chunks = []
        for i in range(0, len(large_dataset), chunk_size):
            chunk = large_dataset[i:i + chunk_size]
            chunk_json = json.dumps(chunk, ensure_ascii=False)
            chunk_bytes = len(chunk_json.encode('utf-8'))
            chunks.append({
                "index": len(chunks) + 1,
                "items": len(chunk),
                "size": chunk_bytes
            })
            print(f"   - Chunk {len(chunks)}: {len(chunk)} 항목, {chunk_bytes:,} bytes")
        
        print(f"\n4. 분할 완료!")
        print(f"   - 총 청크: {len(chunks)}")
        print(f"   - 총 항목: {sum(c['items'] for c in chunks)}")
        print(f"   - 총 크기: {sum(c['size'] for c in chunks):,} bytes")


async def main():
    """모든 예제 실행"""
    print("\n" + "=" * 80)
    print(" " * 20 + "Agents 사용 예제")
    print("=" * 80)
    
    examples = [
        ("기본 저장/로드", example_1_basic_storage),
        ("데이터 정제", example_2_data_cleaning),
        ("중복 제거", example_3_duplicate_removal),
        ("유효성 검사", example_4_data_validation),
        ("대용량 데이터", example_5_large_data),
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
