from fastapi import APIRouter

from .nextcloud import router as nextcloud_router

api_router = APIRouter(prefix="/api")
api_router.include_router(nextcloud_router)

__all__ = ["api_router"]
