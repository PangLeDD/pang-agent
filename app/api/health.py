from fastapi import APIRouter

from app.core.response import success
from app.schemas.common import APIResponse, HealthData

router = APIRouter(tags=["health"])


@router.get("/health", response_model=APIResponse[HealthData])
async def health_check():
    return success({"status": "ok"})
