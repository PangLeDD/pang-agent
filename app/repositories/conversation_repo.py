from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, ConversationMessage


class ConversationRepository:
    """按用户范围查询会话和消息的 SQLAlchemy 数据访问对象。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_owned(self, conversation_id: UUID, user_id: str) -> Conversation | None:
        return await self._session.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )

    async def create(self, user_id: str, title: str = "New Chat") -> Conversation:
        conv = Conversation(user_id=user_id, title=title)
        self._session.add(conv)
        await self._session.commit()
        return conv

    async def list_for_user(self, user_id: str) -> list[Conversation]:
        result = await self._session.scalars(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        return list(result)

    async def add_message(self, conversation_id: UUID, role: str, content: str) -> ConversationMessage:
        msg = ConversationMessage(conversation_id=conversation_id, role=role, content=content)
        self._session.add(msg)
        await self._session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=func.now())
        )
        await self._session.commit()
        return msg

    async def list_messages(self, conversation_id: UUID) -> list[ConversationMessage]:
        result = await self._session.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.asc())
        )
        return list(result)

    async def update_title(self, conversation_id: UUID, title: str) -> None:
        await self._session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(title=title, updated_at=func.now())
        )
        await self._session.commit()
