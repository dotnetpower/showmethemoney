"""Application configuration powered by Pydantic settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "show-me-the-money"
    github_data_dir: Path = _REPO_ROOT / "data"
    application_insights_connection_string: str | None = None

    model_config = {"env_file": ".env", "extra": "allow"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
