"""Version 1 API router."""

from fastapi import APIRouter

from .etf import router as etf_router
from .users import router as users_router

router = APIRouter()
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(etf_router, prefix="/etf", tags=["etf"])
