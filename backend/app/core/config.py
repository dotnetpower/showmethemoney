"""Application configuration powered by Pydantic settings."""

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings

# 기본 데이터 디렉토리 (환경변수로 재정의 가능)
_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data"

# 기본 CORS 허용 도메인 (개발 환경용)
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]


class Settings(BaseSettings):
    app_name: str = "show-me-the-money"
    # 환경변수 DATA_DIR로 재정의 가능, 기본값은 /app/data
    github_data_dir: Path = Path(os.getenv("DATA_DIR", str(_DEFAULT_DATA_DIR)))
    application_insights_connection_string: str | None = None
    # CORS 허용 도메인 (콤마로 구분된 문자열 또는 기본값 사용)
    cors_origins: str | None = None

    model_config = {"env_file": ".env", "extra": "allow"}

    def get_cors_origins(self) -> List[str]:
        """CORS 허용 도메인 목록을 반환합니다."""
        if self.cors_origins:
            # 환경 변수에서 콤마로 구분된 도메인 목록 파싱
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return DEFAULT_CORS_ORIGINS


@lru_cache
def get_settings() -> Settings:
    return Settings()
