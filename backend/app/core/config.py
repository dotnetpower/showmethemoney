"""Application configuration powered by Pydantic settings."""

import logging
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings

# 모듈 레벨 로거 설정
logger = logging.getLogger(__name__)

# 디렉토리 상세 로깅이 이미 수행되었는지 추적하는 플래그
_data_dir_logged = False


def _get_local_data_dir() -> Path:
    """
    로컬 개발 환경용 기본 데이터 디렉토리 경로를 반환합니다.
    
    소스 코드 기준으로 상대 경로를 계산합니다.
    backend/app/core/config.py -> parents[3] = 프로젝트 루트
    """
    config_path = Path(__file__).resolve()
    data_dir = config_path.parents[3] / "data"
    logger.debug(f"[Config] Config file path: {config_path}")
    logger.debug(f"[Config] Calculated local data dir: {data_dir}")
    return data_dir


# 기본 CORS 허용 도메인 (개발 환경용)
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]


class Settings(BaseSettings):
    app_name: str = "show-me-the-money"
    # 데이터 디렉토리 경로 (환경변수 DATA_DIR로 재정의 가능)
    data_dir: Optional[str] = None
    applicationinsights_connection_string: str | None = None
    # CORS 허용 도메인 (콤마로 구분된 문자열 또는 기본값 사용)
    cors_origins: str | None = None

    model_config = {"env_file": ".env", "extra": "allow", "case_sensitive": False}

    @property
    def github_data_dir(self) -> Path:
        """
        데이터 디렉토리 경로를 반환합니다.
        
        환경변수 DATA_DIR가 설정되어 있으면 해당 경로를 사용하고,
        그렇지 않으면 로컬 개발 환경용 기본 경로를 사용합니다.
        
        Docker 환경에서는 DATA_DIR 환경변수가 반드시 설정되어야 합니다.
        """
        global _data_dir_logged
        
        if self.data_dir:
            data_path = Path(self.data_dir)
        else:
            data_path = _get_local_data_dir()
        
        # 상세 로깅은 최초 한 번만 수행 (성능 최적화)
        if not _data_dir_logged:
            _data_dir_logged = True
            
            if self.data_dir:
                logger.info(f"[Config] Using DATA_DIR from env: {data_path}")
            else:
                logger.info(f"[Config] Using calculated local data dir: {data_path}")
            
            # 디렉토리 존재 여부 확인 및 상세 로깅
            logger.info(f"[Config] Data directory path: {data_path}")
            logger.info(f"[Config] Data directory exists: {data_path.exists()}")
            logger.info(f"[Config] Data directory is_dir: {data_path.is_dir() if data_path.exists() else 'N/A'}")
            
            if data_path.exists() and data_path.is_dir():
                try:
                    items = list(data_path.iterdir())
                    logger.info(f"[Config] Data directory contents count: {len(items)}")
                    # 처음 5개 항목만 로깅
                    for item in items[:5]:
                        logger.info(f"[Config]   - {item.name} (is_dir: {item.is_dir()})")
                    if len(items) > 5:
                        logger.info(f"[Config]   ... and {len(items) - 5} more items")
                except PermissionError as e:
                    logger.error(f"[Config] Permission error reading data directory: {e}")
                except Exception as e:
                    logger.error(f"[Config] Error reading data directory: {e}")
            else:
                logger.warning(f"[Config] Data directory does not exist or is not a directory: {data_path}")
                # 상위 경로 확인
                parent_path = data_path.parent
                logger.info(f"[Config] Parent directory: {parent_path}")
                logger.info(f"[Config] Parent exists: {parent_path.exists()}")
                if parent_path.exists():
                    try:
                        parent_items = list(parent_path.iterdir())
                        logger.info(f"[Config] Parent contents: {[item.name for item in parent_items[:10]]}")
                    except Exception as e:
                        logger.error(f"[Config] Error reading parent directory: {e}")
        
        return data_path

    def get_cors_origins(self) -> List[str]:
        """CORS 허용 도메인 목록을 반환합니다."""
        if self.cors_origins:
            # 환경 변수에서 콤마로 구분된 도메인 목록 파싱
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return DEFAULT_CORS_ORIGINS


@lru_cache
def get_settings() -> Settings:
    return Settings()
