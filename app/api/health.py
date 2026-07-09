from fastapi import APIRouter

from app.core.response import success

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    return success({"status": "ok"})
