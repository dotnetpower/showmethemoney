"""User-facing endpoints for demo purposes."""

from fastapi import APIRouter, HTTPException

from ...services.user_service import get_user, list_users

router = APIRouter()


@router.get("/", summary="사용자 목록 조회")
def read_users():
    """Return every cached user record from the repository-backed store."""
    return list_users()


@router.get("/{user_id}", summary="사용자 상세 조회")
def read_user(user_id: str):
    """Return the requested user if it exists in the repository."""
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
