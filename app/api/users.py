from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.response import success
from app.core.security import get_current_user
from app.schemas.common import APIResponse
from app.schemas.user import CurrentUser

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=APIResponse[CurrentUser])
async def read_current_user(
    current_user: Annotated[dict[str, str], Depends(get_current_user)],
):
    return success(current_user)
