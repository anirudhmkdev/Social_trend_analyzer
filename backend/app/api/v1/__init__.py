from fastapi import APIRouter

from app.api.v1.datasets import router as datasets_router
from app.api.v1.health import router as health_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(health_router, tags=["Health"])
v1_router.include_router(datasets_router)

__all__ = ["v1_router"]
