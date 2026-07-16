import unittest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import DEV_AUTH_TOKEN
from app.main import app
from app.models.conversation import Conversation, ConversationMessage

AUTH_HEADERS = {"Authorization": f"Bearer {DEV_AUTH_TOKEN}"}


class ConversationsAPITest(unittest.TestCase):
    """任务 3：受保护的会话历史 API 测试。

    All tests use mocked repositories — no real database needed.
    """

    def setUp(self):
        # 覆盖 get_session，避免连接真实数据库。
        # ponytail: 使用全局依赖覆盖；并行执行有需求时再改为每测试独立数据库。
        app.dependency_overrides[get_session] = lambda: AsyncMock(spec=AsyncSession)

    def tearDown(self):
        app.dependency_overrides.clear()

    # ── 认证 ──────────────────────────────────────────────────────────

    def test_list_conversations_requires_auth(self):
        response = TestClient(app).get("/conversations")
        self.assertEqual(response.status_code, 401)

    def test_list_messages_requires_auth(self):
        response = TestClient(app).get(f"/conversations/{uuid4()}/messages")
        self.assertEqual(response.status_code, 401)

    # ── 会话列表 ──────────────────────────────────────────────────────

    @patch("app.application.conversation_service.ConversationRepository.list_for_user")
    def test_list_conversations_uses_unified_payload(self, mock_list):
        cid = uuid4()
        now = datetime.now()
        mock_list.return_value = [
            Conversation(id=cid, user_id="dev-user", title="Hi", created_at=now, updated_at=now)
        ]

        response = TestClient(app).get("/conversations", headers=AUTH_HEADERS)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["code"], 200)
        self.assertEqual(body["message"], "ok")
        self.assertIsInstance(body["data"], list)
        self.assertEqual(len(body["data"]), 1)
        self.assertEqual(body["data"][0]["id"], str(cid))
        self.assertEqual(body["data"][0]["title"], "Hi")

    @patch("app.application.conversation_service.ConversationRepository.list_for_user")
    def test_list_conversations_empty_returns_empty_array(self, mock_list):
        mock_list.return_value = []

        response = TestClient(app).get("/conversations", headers=AUTH_HEADERS)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], [])

    @patch("app.application.conversation_service.ConversationRepository.list_for_user")
    def test_list_conversations_is_user_scoped(self, mock_list):
        mock_list.return_value = []

        response = TestClient(app).get("/conversations", headers=AUTH_HEADERS)

        self.assertEqual(response.status_code, 200)
        mock_list.assert_called_once_with("dev-user")

    # ── 消息列表 ──────────────────────────────────────────────────────

    @patch("app.application.conversation_service.ConversationRepository.get_owned")
    @patch("app.application.conversation_service.ConversationRepository.list_messages")
    def test_list_messages_uses_unified_payload(self, mock_list_msgs, mock_get_owned):
        cid = uuid4()
        now = datetime.now()
        mock_get_owned.return_value = Conversation(
            id=cid, user_id="dev-user", title="Hi", created_at=now, updated_at=now
        )
        mock_list_msgs.return_value = [
            ConversationMessage(
                id=uuid4(), conversation_id=cid, role="user", content="hello", created_at=now,
            )
        ]

        response = TestClient(app).get(f"/conversations/{cid}/messages", headers=AUTH_HEADERS)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["code"], 200)
        self.assertIsInstance(body["data"], list)
        self.assertEqual(len(body["data"]), 1)
        self.assertEqual(body["data"][0]["role"], "user")
        self.assertEqual(body["data"][0]["content"], "hello")

    @patch("app.application.conversation_service.ConversationRepository.get_owned")
    def test_list_messages_404_for_missing_conversation(self, mock_get_owned):
        mock_get_owned.return_value = None

        response = TestClient(app).get(f"/conversations/{uuid4()}/messages", headers=AUTH_HEADERS)

        self.assertEqual(response.status_code, 404)
        body = response.json()
        self.assertEqual(body["code"], 404)
        self.assertIsNone(body["data"])

    @patch("app.application.conversation_service.ConversationRepository.get_owned")
    def test_list_messages_404_for_foreign_conversation(self, mock_get_owned):
        """其他用户所属的会话同样必须返回 404。"""
        mock_get_owned.return_value = None

        response = TestClient(app).get(f"/conversations/{uuid4()}/messages", headers=AUTH_HEADERS)

        self.assertEqual(response.status_code, 404)
        body = response.json()
        self.assertEqual(body["code"], 404)
        self.assertIsNone(body["data"])
