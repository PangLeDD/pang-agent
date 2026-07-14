"""ServiceFactory：创建短生命周期业务对象。

与 Container 不同——Container 管理全局共享的长生命周期单例，
Factory 按请求/对话创建短生命周期的 Service 对象。
"""

from app.application.chat_service import ChatService


def create_chat_service() -> ChatService:
    """每个请求创建一个新的 ChatService 实例。

    后续按需从 Container 注入 checkpointer、ToolRegistry 等依赖。
    """
    return ChatService()
