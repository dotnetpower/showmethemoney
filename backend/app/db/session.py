"""Session helpers for treating the repository as a lightweight data store."""

from pathlib import Path

from ..core.config import get_settings


def get_repo_path() -> Path:
    settings = get_settings()
    return settings.github_data_dir
