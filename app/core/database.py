from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    # ORM 模型与 Alembic 自动生成迁移共用的 metadata 入口。
    pass


engine = create_async_engine(settings.database_url)
# 提交后仍可在 API 处理函数中读取对象属性。
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    # FastAPI 依赖：每个请求使用一个 session，请求结束后关闭。
    async with AsyncSessionLocal() as session:
        yield session
