from fastapi import FastAPI
from app.config import settings
from app.api.router import api_router
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.response import success


def create_app() -> FastAPI:
    setup_logging(settings.log_level)
    application = FastAPI(title=settings.app_name)
    register_exception_handlers(application)
    application.include_router(api_router)
    return application


app = create_app()


@app.get("/")
async def read_root() -> dict:
    return success({"name": settings.app_name, "status": "ok"})
