"""수동으로 ETF 데이터를 업데이트하는 스크립트"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.etf_updater import ETFUpdater


async def main():
    """메인 실행 함수"""
    updater = ETFUpdater()
    
    print("Starting manual ETF data update...")
    print("=" * 60)
    
    result = await updater.update_all_providers()
    
    print("\n" + "=" * 60)
    print("Update Summary:")
    print(f"  Total providers: {result['total_providers']}")
    print(f"  Successful: {result['successful']}")
    print(f"  Failed: {result['failed']}")
    print(f"  Total ETFs: {result['total_etfs']}")
    print("=" * 60)
    
    # 각 운용사별 결과 출력
    for provider_result in result['results']:
        status = "✓" if provider_result['success'] else "✗"
        print(f"\n{status} {provider_result['provider']}: {provider_result['count']} ETFs")
        if not provider_result['success']:
            print(f"  Error: {provider_result.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
