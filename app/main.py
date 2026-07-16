from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.config import settings
from app.container import get_container, init_container
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.response import success
from app.core.validation import validate_settings
from app.schemas.common import APIResponse, RootData


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_container().infra.init_checkpointer()
    yield
    await get_container().infra.close()


def create_app() -> FastAPI:
    setup_logging(settings.log_level)
    validate_settings()
    init_container()
    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    register_exception_handlers(application)
    application.include_router(api_router)
    return application


app = create_app()


@app.get("/", response_model=APIResponse[RootData])
async def read_root():
    return success({"name": settings.app_name, "status": "ok"})
