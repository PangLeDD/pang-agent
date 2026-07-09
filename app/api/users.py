from fastapi import APIRouter

from app.core.response import success

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def read_current_user() -> dict:
    return success({"id": "dev-user", "username": "dev"})
