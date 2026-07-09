from fastapi import FastAPI

from app.api.router import api_router
from app.config import settings
from app.core.logging import setup_logging


def create_app() -> FastAPI:
    setup_logging(settings.log_level)
    application = FastAPI(title=settings.app_name)
    application.include_router(api_router)
    return application


app = create_app()


@app.get("/")
async def read_root():
    return {"name": settings.app_name, "status": "ok"}
