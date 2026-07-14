from typing import Any

from app.config import settings


class InfraContainer:
    """基础设施层长生命周期资源：数据库连接池、缓存、Checkpointer 等。"""

    def __init__(self) -> None:
        self._checkpointer: Any = None

    @property
    def checkpointer(self) -> Any:
        """LangGraph Checkpointer 单例。"""
        return self._checkpointer

    def init_checkpointer(self) -> None:
        """ponytail: PostgresSaver(settings.database_url) 尚未实现。"""
        pass
