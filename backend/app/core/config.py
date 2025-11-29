"""Application configuration powered by Pydantic settings."""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings


def _get_local_data_dir() -> Path:
    """
    로컬 개발 환경용 기본 데이터 디렉토리 경로를 반환합니다.
    
    소스 코드 기준으로 상대 경로를 계산합니다.
    backend/app/core/config.py -> parents[3] = 프로젝트 루트
    """
    return Path(__file__).resolve().parents[3] / "data"


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
        if self.data_dir:
            return Path(self.data_dir)
        return _get_local_data_dir()

    def get_cors_origins(self) -> List[str]:
        """CORS 허용 도메인 목록을 반환합니다."""
        if self.cors_origins:
            # 환경 변수에서 콤마로 구분된 도메인 목록 파싱
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return DEFAULT_CORS_ORIGINS


@lru_cache
def get_settings() -> Settings:
    return Settings()
