from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def read_current_user() -> dict[str, str]:
    return {"id": "dev-user", "username": "dev"}
