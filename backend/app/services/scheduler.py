"""주기적인 데이터 업데이트 스케줄러"""
import asyncio
from datetime import datetime, time
from typing import Optional

from app.services.etf_updater import ETFUpdater
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


class DataUpdateScheduler:
    """ETF 데이터 주기적 업데이트 스케줄러"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.etf_updater = ETFUpdater()
        self._is_running = False
    
    async def _update_job(self):
        """스케줄러에서 실행될 업데이트 작업"""
        try:
            print(f"\n[Scheduler] Running scheduled update at {datetime.now()}")
            result = await self.etf_updater.update_all_providers()
            print(f"[Scheduler] Update completed: {result['successful']}/{result['total_providers']} successful")
        except Exception as e:
            print(f"[Scheduler] Error during scheduled update: {e}")
    
    def start(
        self,
        hour: int = 18,
        minute: int = 0,
        timezone: str = "America/New_York"
    ):
        """
        스케줄러를 시작합니다.
        
        Args:
            hour: 실행 시간 (시)
            minute: 실행 시간 (분)
            timezone: 타임존 (기본: 미국 동부 시간)
        """
        if self._is_running:
            print("[Scheduler] Already running")
            return
        
        # 매일 지정된 시간에 실행
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone=timezone
        )
        
        self.scheduler.add_job(
            self._update_job,
            trigger=trigger,
            id="etf_daily_update",
            name="Daily ETF Data Update",
            replace_existing=True
        )
        
        self.scheduler.start()
        self._is_running = True
        
        print(f"[Scheduler] Started - will run daily at {hour:02d}:{minute:02d} {timezone}")
    
    def stop(self):
        """스케줄러를 중지합니다."""
        if not self._is_running:
            print("[Scheduler] Not running")
            return
        
        self.scheduler.shutdown()
        self._is_running = False
        print("[Scheduler] Stopped")
    
    def run_now(self):
        """즉시 업데이트를 실행합니다."""
        asyncio.create_task(self._update_job())
    
    def get_next_run_time(self) -> Optional[datetime]:
        """다음 실행 예정 시간을 반환합니다."""
        job = self.scheduler.get_job("etf_daily_update")
        if job:
            return job.next_run_time
        return None


# 전역 스케줄러 인스턴스
scheduler = DataUpdateScheduler()
