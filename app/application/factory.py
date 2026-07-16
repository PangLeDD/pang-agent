"""ServiceFactory：创建短生命周期业务对象。

与 Container 不同——Container 管理全局共享的长生命周期单例，
Factory 按请求/对话创建短生命周期的 Service 对象。
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import AgentExecutor
from app.application.chat_service import ChatService
from app.application.conversation_service import ConversationService
from app.container import get_container


def create_chat_service(session: AsyncSession) -> ChatService:
    """每个请求创建一个新的 ChatService 实例。

    session 由 API 层通过 FastAPI Depends(get_session) 注入，
    ConversationService 复用同一个 request-scoped session。
    """
    executor = AgentExecutor(
        llm=get_container().ai.llm,
        checkpointer=get_container().infra.checkpointer,
    )
    conversations = ConversationService(session)
    # ponytail: 复用既有长生命周期 LLM 生成标题；标题质量不足时再拆分专用模型。
    title_llm = get_container().ai.llm
    return ChatService(executor=executor, conversations=conversations, title_llm=title_llm)
