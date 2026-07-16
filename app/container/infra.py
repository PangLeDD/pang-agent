from loguru import logger
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.config import settings


class InfraContainer:
    """基础设施层长生命周期资源：数据库连接池、缓存、Checkpointer 等。"""

    def __init__(self) -> None:
        self._checkpointer: AsyncPostgresSaver | None = None
        self._conn: AsyncConnection | None = None

    @property
    def checkpointer(self) -> AsyncPostgresSaver | None:
        """LangGraph Checkpointer 单例，未初始化或连接失败时返回 None。"""
        return self._checkpointer

    async def init_checkpointer(self) -> None:
        """初始化 PG Checkpointer 并建表。

        连接或建表失败时关闭连接并向上抛出异常，阻断启动。
        成功后才设置 _conn / _checkpointer，失败时两者均保持 None。
        """
        db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await AsyncConnection.connect(db_url, autocommit=True, row_factory=dict_row)
        try:
            checkpointer = AsyncPostgresSaver(conn)
            await checkpointer.setup()
        except Exception:
            logger.exception("PG checkpointer initialization failed")
            try:
                await conn.close()
            except Exception:
                logger.exception("Failed to close connection during cleanup")
            raise
        self._conn, self._checkpointer = conn, checkpointer
        logger.info("PG checkpointer initialized")

    async def close(self) -> None:
        """关闭 PG 连接，应用关闭时由 lifespan cleanup 调用。"""
        if self._conn is not None:
            await self._conn.close()
            logger.info("PG checkpointer connection closed")
