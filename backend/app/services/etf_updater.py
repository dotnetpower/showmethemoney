"""ETF 데이터 업데이트 서비스"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

from app.models.etf import ETF
from app.services.crawlers import (AlphaArchitectCrawler, BaseCrawler,
                                   DimensionalCrawler, DirexionCrawler,
                                   FidelityCrawler, FirstTrustCrawler,
                                   FranklinTempletonCrawler, GlobalXCrawler,
                                   GraniteSharesCrawler, InvescoCrawler,
                                   ISharesCrawler, JPMorganCrawler,
                                   PacerCrawler, PIMCOCrawler,
                                   RoundhillCrawler, SPDRCrawler,
                                   VanEckCrawler, VanguardCrawler,
                                   WisdomTreeCrawler)
from app.services.crawlers.goldmansachs import GoldmanSachsCrawler
from app.services.crawlers.yieldmax import YieldmaxCrawler
from app.services.data_manager import DataManager


class ETFUpdater:
    """ETF 데이터 수집 및 업데이트를 담당하는 서비스"""
    
    def __init__(self):
        self.data_manager = DataManager()
        # 등록된 크롤러들
        self.crawlers: List[BaseCrawler] = [
            ISharesCrawler(),
            RoundhillCrawler(),
            VanguardCrawler(),
            SPDRCrawler(),
            InvescoCrawler(),
            JPMorganCrawler(),
            DimensionalCrawler(),
            FirstTrustCrawler(),
            FidelityCrawler(),
            FranklinTempletonCrawler(),
            VanEckCrawler(),
            WisdomTreeCrawler(),
            GlobalXCrawler(),
            DirexionCrawler(),
            PIMCOCrawler(),
            GraniteSharesCrawler(),
            AlphaArchitectCrawler(),
            PacerCrawler(),
            GoldmanSachsCrawler(),
            YieldmaxCrawler(),
        ]
    
    async def is_recently_crawled(self, provider_name: str, hours: int = 24) -> bool:
        """
        지정된 시간 내에 크롤링이 이루어졌는지 확인합니다.
        
        Args:
            provider_name: 운용사 이름
            hours: 체크할 시간 (기본 24시간)
            
        Returns:
            최근 크롤링 여부
        """
        try:
            metadata_path = self.data_manager._get_metadata_path(provider_name, "etf_list")
            
            if not metadata_path.exists():
                return False
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = f.read()
                import json
                data = json.loads(metadata)
            
            updated_at_str = data.get('updated_at')
            if not updated_at_str:
                return False
            
            updated_at = datetime.fromisoformat(updated_at_str)
            time_diff = datetime.now() - updated_at
            
            return time_diff < timedelta(hours=hours)
            
        except Exception as e:
            print(f"[{provider_name}] Error checking last crawl time: {e}")
            return False
    
    async def update_single_provider(self, crawler: BaseCrawler, force: bool = False) -> Dict:
        """
        단일 운용사의 ETF 데이터를 업데이트합니다.
        
        Args:
            crawler: 크롤러 인스턴스
            force: True일 경우 24시간 체크 무시
            
        Returns:
            업데이트 결과
        """
        provider_name = crawler.get_provider_name()
        
        # 24시간 이내 크롤링 체크
        if not force and await self.is_recently_crawled(provider_name):
            print(f"[{provider_name}] Skipped - Already crawled within 24 hours")
            return {
                "provider": provider_name,
                "success": True,
                "skipped": True,
                "reason": "Already crawled within 24 hours",
                "count": 0
            }
        
        try:
            print(f"[{provider_name}] Starting data crawl...")
            
            # 데이터 크롤링
            etf_list = await crawler.crawl()
            
            if not etf_list:
                return {
                    "provider": provider_name,
                    "success": False,
                    "error": "No data retrieved",
                    "count": 0
                }
            
            print(f"[{provider_name}] Crawled {len(etf_list)} ETFs")
            
            # 데이터 저장 (개발: JSON, 운영: MessagePack 권장)
            use_msgpack = False  # 운영 환경에서는 True로 변경
            metadata = await self.data_manager.save_data(
                provider_name=provider_name,
                data_type="etf_list",
                data=etf_list,
                use_msgpack=use_msgpack
            )
            
            print(f"[{provider_name}] Saved data: {metadata.get('total_count')} ETFs, "
                  f"{metadata.get('total_size')} bytes, "
                  f"chunked: {metadata.get('chunked', False)}")
            
            return {
                "provider": provider_name,
                "success": True,
                "count": len(etf_list),
                "metadata": metadata
            }
            
        except Exception as e:
            print(f"[{provider_name}] Error during update: {e}")
            return {
                "provider": provider_name,
                "success": False,
                "error": str(e),
                "count": 0
            }
    
    async def update_all_providers(self, force: bool = False) -> Dict:
        """
        모든 등록된 운용사의 ETF 데이터를 업데이트합니다.
        
        Args:
            force: True일 경우 24시간 체크 무시하고 강제 업데이트
            
        Returns:
            전체 업데이트 결과
        """
        print(f"\n{'='*60}")
        print(f"Starting ETF data update at {datetime.now()}")
        print(f"Force update: {force}")
        print(f"{'='*60}\n")
        
        # 모든 크롤러를 병렬로 실행
        tasks = [self.update_single_provider(crawler, force=force) for crawler in self.crawlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 집계
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_providers": len(self.crawlers),
            "successful": sum(1 for r in results if isinstance(r, dict) and r.get("success") and not r.get("skipped")),
            "skipped": sum(1 for r in results if isinstance(r, dict) and r.get("skipped")),
            "failed": sum(1 for r in results if isinstance(r, dict) and not r.get("success")),
            "total_etfs": sum(r.get("count", 0) for r in results if isinstance(r, dict)),
            "results": [r for r in results if isinstance(r, dict)]
        }
        
        print(f"\n{'='*60}")
        print(f"Update completed at {datetime.now()}")
        print(f"Success: {summary['successful']}/{summary['total_providers']} providers")
        print(f"Skipped: {summary['skipped']} providers (already updated within 24h)")
        print(f"Failed: {summary['failed']} providers")
        print(f"Total ETFs: {summary['total_etfs']}")
        print(f"{'='*60}\n")
        
        return summary
    
    async def get_etf_list(self, provider_name: str) -> List[ETF]:
        """
        저장된 ETF 리스트를 조회합니다.
        
        Args:
            provider_name: 운용사 이름
            
        Returns:
            ETF 모델 리스트
        """
        data = await self.data_manager.load_data(provider_name, "etf_list")
        return [ETF(**item) for item in data]
    
    async def get_all_etfs(self) -> Dict[str, List[ETF]]:
        """
        모든 운용사의 ETF 리스트를 조회합니다.
        
        Returns:
            운용사별 ETF 리스트 딕셔너리
        """
        result = {}
        for crawler in self.crawlers:
            provider_name = crawler.get_provider_name()
            result[provider_name] = await self.get_etf_list(provider_name)
        return result
