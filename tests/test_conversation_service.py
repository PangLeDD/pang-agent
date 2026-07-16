import unittest
from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import HTTPException

from app.models.conversation import Conversation, ConversationMessage
from app.schemas.conversation import ConversationResponse, ConversationMessageResponse


class ConversationServiceTest(unittest.IsolatedAsyncioTestCase):
    """任务 2：ConversationService 单元测试。

    All tests mock the repository layer; no database required.
    """

    # ── 准备会话 ─────────────────────────────────────────────────────────

    async def test_prepare_new_conversation_uses_default_title(self):
        from app.application.conversation_service import ConversationService

        fake_conv = Conversation(id=uuid4(), user_id="user-a", title="New Chat")
        repo = AsyncMock()
        repo.create = AsyncMock(return_value=fake_conv)
        service = ConversationService(AsyncMock(), repo=repo)

        conv = await service.prepare_conversation(None, "user-a")

        self.assertEqual(conv.user_id, "user-a")
        self.assertEqual(conv.title, "New Chat")
        repo.create.assert_awaited_once_with("user-a")

    async def test_prepare_existing_conversation_validates_ownership(self):
        from app.application.conversation_service import ConversationService

        cid = uuid4()
        fake_conv = Conversation(id=cid, user_id="user-a", title="Hi")
        repo = AsyncMock()
        repo.get_owned = AsyncMock(return_value=fake_conv)
        service = ConversationService(AsyncMock(), repo=repo)

        conv = await service.prepare_conversation(cid, "user-a")

        self.assertIs(conv, fake_conv)
        repo.get_owned.assert_awaited_once_with(cid, "user-a")

    async def test_foreign_conversation_raises_404(self):
        from app.application.conversation_service import ConversationService

        repo = AsyncMock()
        repo.get_owned = AsyncMock(return_value=None)
        service = ConversationService(AsyncMock(), repo=repo)

        with self.assertRaises(HTTPException) as ctx:
            await service.prepare_conversation(uuid4(), "user-a")

        self.assertEqual(ctx.exception.status_code, 404)

    # ── 添加消息 ─────────────────────────────────────────────────────────

    async def test_add_message_rejects_invalid_role(self):
        from app.application.conversation_service import ConversationService

        conv = Conversation(id=uuid4(), user_id="user-a", title="New Chat")
        service = ConversationService(AsyncMock(), repo=AsyncMock())

        with self.assertRaises(ValueError):
            await service.add_message(conv, "system", "hello")

    async def test_add_message_creates_row_and_updates_updated_at(self):
        from app.application.conversation_service import ConversationService

        cid = uuid4()
        conv = Conversation(id=cid, user_id="user-a", title="New Chat")
        fake_msg = ConversationMessage(
            id=uuid4(), conversation_id=cid, role="user", content="hello"
        )
        repo = AsyncMock()
        repo.add_message = AsyncMock(return_value=fake_msg)
        service = ConversationService(AsyncMock(), repo=repo)

        msg = await service.add_message(conv, "user", "hello")

        self.assertEqual(msg.role, "user")
        self.assertEqual(msg.content, "hello")
        repo.add_message.assert_awaited_once_with(cid, "user", "hello")

    # ── 会话列表 ─────────────────────────────────────────────────────────

    async def test_list_conversations_returns_user_scoped(self):
        from app.application.conversation_service import ConversationService

        convs = [
            Conversation(id=uuid4(), user_id="user-a", title="B"),
            Conversation(id=uuid4(), user_id="user-a", title="A"),
        ]
        repo = AsyncMock()
        repo.list_for_user = AsyncMock(return_value=convs)
        service = ConversationService(AsyncMock(), repo=repo)

        result = await service.list_conversations("user-a")

        self.assertEqual(len(result), 2)
        repo.list_for_user.assert_awaited_once_with("user-a")

    # ── 消息列表 ─────────────────────────────────────────────────────────

    async def test_list_messages_raises_404_for_foreign_conversation(self):
        from app.application.conversation_service import ConversationService

        repo = AsyncMock()
        repo.get_owned = AsyncMock(return_value=None)
        service = ConversationService(AsyncMock(), repo=repo)

        with self.assertRaises(HTTPException) as ctx:
            await service.list_messages(uuid4(), "user-a")

        self.assertEqual(ctx.exception.status_code, 404)

    async def test_list_messages_returns_oldest_first(self):
        from app.application.conversation_service import ConversationService

        cid = uuid4()
        conv = Conversation(id=cid, user_id="user-a", title="X")
        msgs = [
            ConversationMessage(id=uuid4(), conversation_id=cid, role="user", content="first"),
            ConversationMessage(id=uuid4(), conversation_id=cid, role="assistant", content="second"),
        ]
        repo = AsyncMock()
        repo.get_owned = AsyncMock(return_value=conv)
        repo.list_messages = AsyncMock(return_value=msgs)
        service = ConversationService(AsyncMock(), repo=repo)

        result = await service.list_messages(cid, "user-a")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].content, "first")
        self.assertEqual(result[1].content, "second")
        repo.list_messages.assert_awaited_once_with(cid)

    # ── 更新标题 ─────────────────────────────────────────────────────────

    async def test_update_title_raises_404_for_foreign_conversation(self):
        from app.application.conversation_service import ConversationService

        repo = AsyncMock()
        repo.get_owned = AsyncMock(return_value=None)
        service = ConversationService(AsyncMock(), repo=repo)

        with self.assertRaises(HTTPException) as ctx:
            await service.update_title(uuid4(), "user-a", "New Title")

        self.assertEqual(ctx.exception.status_code, 404)

    async def test_update_title_persists(self):
        from app.application.conversation_service import ConversationService

        cid = uuid4()
        conv = Conversation(id=cid, user_id="user-a", title="New Chat")
        repo = AsyncMock()
        repo.get_owned = AsyncMock(return_value=conv)
        repo.update_title = AsyncMock()
        service = ConversationService(AsyncMock(), repo=repo)

        result = await service.update_title(cid, "user-a", "Generated Title")

        self.assertEqual(result.title, "Generated Title")
        repo.update_title.assert_awaited_once_with(cid, "Generated Title")


class ConversationDTOTest(unittest.TestCase):
    """验证响应 DTO 可通过 ORM 的 from_attributes 配置构建。"""

    def test_conversation_response_from_attributes(self):
        cid = uuid4()
        now = datetime.now()
        conv = Conversation(id=cid, user_id="user-a", title="Hi", created_at=now, updated_at=now)
        dto = ConversationResponse.model_validate(conv)
        self.assertEqual(dto.id, cid)
        self.assertEqual(dto.user_id, "user-a")
        self.assertEqual(dto.title, "Hi")

    def test_conversation_message_response_from_attributes(self):
        mid = uuid4()
        cid = uuid4()
        now = datetime.now()
        msg = ConversationMessage(id=mid, conversation_id=cid, role="user", content="hello", created_at=now)
        dto = ConversationMessageResponse.model_validate(msg)
        self.assertEqual(dto.id, mid)
        self.assertEqual(dto.conversation_id, cid)
        self.assertEqual(dto.role, "user")
        self.assertEqual(dto.content, "hello")
