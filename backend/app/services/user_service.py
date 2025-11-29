"""Business logic that reads JSON snapshots stored in the repository."""

import json
from functools import lru_cache
from pathlib import Path

from ..core.config import get_settings
from ..models.user import User


@lru_cache
def _data_file() -> Path:
    settings = get_settings()
    return settings.github_data_dir / "users.json"


def _ensure_data_file() -> None:
    path = _data_file()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[]", encoding="utf-8")


def list_users() -> list[User]:
    _ensure_data_file()
    path = _data_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    return [User(**item) for item in data]


def get_user(user_id: str) -> User | None:
    return next((user for user in list_users() if user.id == user_id), None)
