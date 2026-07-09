from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    # Shared metadata entrypoint for ORM models and Alembic autogenerate.
    pass


engine = create_async_engine(settings.database_url)
# Keep attributes readable after commit inside API handlers.
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    # FastAPI dependency: one request gets one session, then closes it.
    async with AsyncSessionLocal() as session:
        yield session
