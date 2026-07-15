from loguru import logger
from psycopg import Connection
from psycopg.rows import dict_row

from langgraph.checkpoint.postgres import PostgresSaver

from app.config import settings


class InfraContainer:
    """基础设施层长生命周期资源：数据库连接池、缓存、Checkpointer 等。"""

    def __init__(self) -> None:
        self._checkpointer: PostgresSaver | None = None
        self._conn: Connection | None = None

    @property
    def checkpointer(self) -> PostgresSaver | None:
        """LangGraph Checkpointer 单例，未初始化或连接失败时返回 None。"""
        return self._checkpointer

    def init_checkpointer(self) -> None:
        """初始化 PG Checkpointer 并建表。

        pg 不可用时仅记录警告，不阻断应用启动；
        此时 checkpointer 保持 None，图仍可正常运行。
        """
        try:
            db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
            self._conn = Connection.connect(db_url, autocommit=True, row_factory=dict_row)
            self._checkpointer = PostgresSaver(self._conn)
            self._checkpointer.setup()
            logger.info("PG checkpointer initialized")
        except Exception:
            logger.warning("PG checkpointer unavailable, running without persistence")
