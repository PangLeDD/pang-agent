from fastapi import APIRouter, Depends

from app.api.agent import router as agent_router
from app.api.health import router as health_router
from app.api.users import router as users_router
from app.core.security import get_current_user

api_router = APIRouter()
public_router = APIRouter()
protected_router = APIRouter(dependencies=[Depends(get_current_user)])

public_router.include_router(health_router)
protected_router.include_router(agent_router)
protected_router.include_router(users_router)

# Public and protected routers stay separate so new APIs choose auth explicitly.
api_router.include_router(public_router)
api_router.include_router(protected_router)
