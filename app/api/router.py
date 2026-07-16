from fastapi import APIRouter, Depends

from app.api.agent import router as agent_router
from app.api.conversations import router as conversations_router
from app.api.health import router as health_router
from app.api.users import router as users_router
from app.core.security import get_current_user

api_router = APIRouter()
public_router = APIRouter()
protected_router = APIRouter(dependencies=[Depends(get_current_user)])

public_router.include_router(health_router)
protected_router.include_router(agent_router)
protected_router.include_router(conversations_router)
protected_router.include_router(users_router)

# 公开与受保护路由保持分离，新增接口时必须显式选择认证策略。
api_router.include_router(public_router)
api_router.include_router(protected_router)
