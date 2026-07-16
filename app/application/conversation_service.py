from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, ConversationMessage
from app.repositories.conversation_repo import ConversationRepository


class ConversationService:
    """请求级会话 CRUD 服务。

    Owns product-level conversation/message data. Receives AsyncSession
    per request via FastAPI Depends. Not a Container singleton.

    Title generation via LLM is delegated to Task 4; update_title accepts
    a pre-generated string so callers can feed LLM output here.
    """

    # ponytail: 暂不支持分页、编辑、删除；有实际需求时再添加。

    def __init__(self, session: AsyncSession, repo: ConversationRepository | None = None) -> None:
        self._repo = repo or ConversationRepository(session)

    async def prepare_conversation(self, conversation_id: UUID | None, user_id: str) -> Conversation:
        """返回用户所属的既有会话；没有会话 ID 时创建新会话。"""
        if conversation_id is None:
            return await self._repo.create(user_id)

        conv = await self._repo.get_owned(conversation_id, user_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conv

    async def add_message(self, conversation: Conversation, role: str, content: str) -> ConversationMessage:
        """持久化一条消息，角色只能是 user 或 assistant。"""
        if role not in ("user", "assistant"):
            raise ValueError(f"Invalid role: {role!r}. Must be 'user' or 'assistant'.")
        return await self._repo.add_message(conversation.id, role, content)

    async def list_conversations(self, user_id: str) -> list[Conversation]:
        """返回用户的全部会话，按最近更新时间倒序排列。"""
        return await self._repo.list_for_user(user_id)

    async def list_messages(self, conversation_id: UUID, user_id: str) -> list[ConversationMessage]:
        """返回会话消息，按创建时间正序排列；非所属会话返回 404。"""
        conv = await self._repo.get_owned(conversation_id, user_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return await self._repo.list_messages(conversation_id)

    async def update_title(self, conversation_id: UUID, user_id: str, title: str) -> Conversation:
        """使用预生成的标题更新会话。

        Task 4 will call this with LLM-generated title. On failure to
        generate, the caller simply does not invoke this — title stays
        'New Chat'.
        """
        conv = await self._repo.get_owned(conversation_id, user_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        await self._repo.update_title(conversation_id, title)
        # 同步更新内存对象，调用方无需重新查询即可读到新标题。
        conv.title = title
        return conv
