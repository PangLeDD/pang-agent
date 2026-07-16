import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessageChunk
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.events import AgentEvent, EventType
from app.application.chat_service import ChatService
from app.core.database import get_session
from app.core.security import DEV_AUTH_TOKEN
from app.models.conversation import Conversation, ConversationMessage
from app.presentation import sse_event
from app.main import app


class AgentStreamTest(unittest.TestCase):
    def test_sse_event_returns_structured_dict(self):
        result = sse_event(EventType.CONVERSATION_START, {"conversation_id": "abc"})

        self.assertIsInstance(result, dict)
        self.assertEqual(result["event"], EventType.CONVERSATION_START)
        self.assertIsInstance(result["data"], str)
        envelope = json.loads(result["data"])
        self.assertIsInstance(envelope["id"], str)
        self.assertIsInstance(envelope["timestamp"], int)
        self.assertGreater(envelope["timestamp"], 0)
        self.assertEqual(envelope["payload"], {"conversation_id": "abc"})

    def test_agent_stream_requires_token(self):
        response = TestClient(app).post("/agent/stream", json={"message": "hello"})
        self.assertEqual(response.status_code, 401)

    def test_agent_stream_returns_dotted_event_names(self):
        chunk = AIMessageChunk(content="mock delta")
        astream_call_args = {}

        async def fake_astream(*args, **kwargs):
            astream_call_args["args"] = args
            astream_call_args["kwargs"] = kwargs
            yield chunk, {}

        fake_graph = MagicMock()
        fake_graph.astream.side_effect = fake_astream

        with unittest.mock.patch("app.agent.factory.GraphFactory.create", return_value=fake_graph):
            response = TestClient(app).post(
                "/agent/stream",
                json={"message": "hello"},
                headers={"Authorization": f"Bearer {DEV_AUTH_TOKEN}"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers["content-type"])

        body = response.text.replace("\r", "")
        blocks = [block for block in body.strip().split("\n\n") if block]
        self.assertEqual(len(blocks), 3, f"Expected 3 SSE blocks, got {len(blocks)}")
        self.assertEqual(
            [block.split("\n", 1)[0] for block in blocks],
            [
                f"event: {EventType.CONVERSATION_START}",
                f"event: {EventType.MESSAGE_DELTA}",
                f"event: {EventType.CONVERSATION_END}",
            ],
        )

        for block in blocks:
            event_line, data_line = block.split("\n", 1)
            self.assertTrue(data_line.startswith("data: "))
            envelope = json.loads(data_line.removeprefix("data: "))
            self.assertIsInstance(envelope["id"], str)
            self.assertIsInstance(envelope["timestamp"], int)

        start_data = json.loads(blocks[0].split("\n", 1)[1].removeprefix("data: "))
        sse_conversation_id = start_data["payload"]["conversation_id"]
        self.assertIsInstance(sse_conversation_id, str)
        self.assertGreater(len(sse_conversation_id), 0)

        delta_data = json.loads(blocks[1].split("\n", 1)[1].removeprefix("data: "))
        self.assertEqual(delta_data["payload"]["delta"], "mock delta")

        done_data = json.loads(blocks[2].split("\n", 1)[1].removeprefix("data: "))
        self.assertEqual(done_data["payload"]["reason"], "stop")

        # --- astream 配置断言 ---
        self.assertIn("args", astream_call_args, "astream was not called")
        astream_config = astream_call_args["args"][1]  # config 是第二个位置参数。
        thread_id = astream_config.get("configurable", {}).get("thread_id", "")
        self.assertTrue(
            thread_id.startswith("dev-user:"),
            f"thread_id should be namespaced as dev-user:..., got {thread_id!r}",
        )
        # SSE 发出的 conversation_id 必须和 thread_id 后缀一致。
        expected_namespaced = f"dev-user:{sse_conversation_id}"
        self.assertEqual(
            thread_id,
            expected_namespaced,
            f"astream config thread_id {thread_id!r} does not match SSE conversation_id {sse_conversation_id!r}",
        )


class AgentStreamValidationTest(unittest.TestCase):
    """任务 5：在流执行前于 API 边界校验 conversation_id。"""

    def test_invalid_conversation_id_returns_422(self):
        """非 UUID 的 conversation_id 必须在流开始前触发 FastAPI 的 422 校验错误。"""
        response = TestClient(app).post(
            "/agent/stream",
            json={"message": "hello", "conversation_id": "not-a-uuid"},
            headers={"Authorization": f"Bearer {DEV_AUTH_TOKEN}"},
        )
        self.assertEqual(response.status_code, 422)

        body = response.json()
        # 确认这是统一错误响应，而不是 SSE 流。
        self.assertIn("code", body)
        self.assertIn("message", body)


class ChatServiceThreadIdTest(unittest.IsolatedAsyncioTestCase):
    """验证 per-user thread 命名空间隔离。

    内部 thread_id 格式: <user_id>:<conversation_id>
    外部 SSE 事件中仍使用裸 conversation_id。
    """

    async def test_same_conversation_is_namespaced_by_user(self):
        executor = MagicMock()
        shared_id = uuid4()

        async def run(message, thread_id):
            yield AgentEvent(type=EventType.CONVERSATION_START)

        executor.run.side_effect = run
        service = ChatService(executor=executor)

        first = [item async for item in service.stream("hello", shared_id, "user-a")]
        second = [item async for item in service.stream("hello", shared_id, "user-b")]

        self.assertEqual(executor.run.call_args_list[0].kwargs["thread_id"], f"user-a:{shared_id}")
        self.assertEqual(executor.run.call_args_list[1].kwargs["thread_id"], f"user-b:{shared_id}")
        self.assertIn(f'"conversation_id": "{shared_id}"', first[0]["data"])
        self.assertIn(f'"conversation_id": "{shared_id}"', second[0]["data"])


class AgentStreamOwnershipValidationTest(unittest.TestCase):
    """任务 5：在 SSE 流开始前于 API 边界校验 conversation_id 归属。"""

    def setUp(self):
        app.dependency_overrides[get_session] = lambda: AsyncMock(spec=AsyncSession)

    def tearDown(self):
        app.dependency_overrides.clear()

    @patch("app.repositories.conversation_repo.ConversationRepository.get_owned")
    def test_foreign_uuid_returns_404_not_sse(self, mock_get_owned):
        """当前用户无权访问的有效 UUID 必须在 SSE 开始前返回 HTTP 404。"""
        mock_get_owned.return_value = None
        foreign_id = uuid4()

        response = TestClient(app).post(
            "/agent/stream",
            json={"message": "hello", "conversation_id": str(foreign_id)},
            headers={"Authorization": f"Bearer {DEV_AUTH_TOKEN}"},
        )

        self.assertEqual(response.status_code, 404)
        body = response.json()
        self.assertEqual(body["code"], 404)
        self.assertEqual(body["message"], "Conversation not found")
        self.assertIsNone(body["data"])
        self.assertNotEqual(response.headers.get("content-type"), "text/event-stream")

    @patch("app.repositories.conversation_repo.ConversationRepository.get_owned")
    @patch("app.repositories.conversation_repo.ConversationRepository.add_message")
    def test_foreign_conversation_no_user_message_persisted(self, mock_add_message, mock_get_owned):
        """外部会话不得持久化用户消息。"""
        mock_get_owned.return_value = None
        foreign_id = uuid4()

        TestClient(app).post(
            "/agent/stream",
            json={"message": "hello", "conversation_id": str(foreign_id)},
            headers={"Authorization": f"Bearer {DEV_AUTH_TOKEN}"},
        )

        mock_add_message.assert_not_called()

    @patch.object(ChatService, "_generate_title", new=AsyncMock())
    @patch("app.agent.factory.GraphFactory.create")
    @patch("app.repositories.conversation_repo.ConversationRepository.create")
    @patch("app.repositories.conversation_repo.ConversationRepository.add_message")
    def test_new_conversation_none_unchanged(self, mock_add_message, mock_create, mock_graph):
        """conversation_id=None 仍应创建新会话并返回 SSE 流。"""
        new_id = uuid4()
        mock_create.return_value = Conversation(id=new_id, user_id="dev-user", title="New Chat")
        mock_add_message.return_value = ConversationMessage(
            id=uuid4(), conversation_id=new_id, role="user", content="hello",
        )

        async def fake_astream(*_a, **_kw):
            yield AIMessageChunk(content="hi"), {}

        fake_graph = MagicMock()
        fake_graph.astream.side_effect = fake_astream
        mock_graph.return_value = fake_graph

        response = TestClient(app).post(
            "/agent/stream",
            json={"message": "hello"},
            headers={"Authorization": f"Bearer {DEV_AUTH_TOKEN}"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers["content-type"])

    @patch("app.agent.factory.GraphFactory.create")
    @patch("app.repositories.conversation_repo.ConversationRepository.get_owned")
    @patch("app.repositories.conversation_repo.ConversationRepository.add_message")
    def test_owned_conversation_still_works(self, mock_add_message, mock_get_owned, mock_graph):
        """所属会话应正常执行，get_owned 仅调用一次，避免重复查询。"""
        owned_id = uuid4()
        conv = Conversation(id=owned_id, user_id="dev-user", title="My Chat")
        mock_get_owned.return_value = conv
        mock_add_message.return_value = ConversationMessage(
            id=uuid4(), conversation_id=owned_id, role="user", content="hello",
        )

        async def fake_astream(*_a, **_kw):
            yield AIMessageChunk(content="hi"), {}

        fake_graph = MagicMock()
        fake_graph.astream.side_effect = fake_astream
        mock_graph.return_value = fake_graph

        response = TestClient(app).post(
            "/agent/stream",
            json={"message": "hello", "conversation_id": str(owned_id)},
            headers={"Authorization": f"Bearer {DEV_AUTH_TOKEN}"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers["content-type"])
        # get_owned 只在预检调用一次，_prepare 中不应重复查询。
        mock_get_owned.assert_called_once_with(owned_id, "dev-user")
