import json
import unittest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.agent.events import AgentEvent, EventType
from app.application.chat_service import ChatService
from app.core.security import DEV_AUTH_TOKEN
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
        chunk = MagicMock()
        chunk.content = "mock delta"
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

        # --- Assertions on astream config ---
        self.assertIn("args", astream_call_args, "astream was not called")
        astream_config = astream_call_args["args"][1]  # config is second positional arg
        thread_id = astream_config.get("configurable", {}).get("thread_id", "")
        self.assertTrue(
            thread_id.startswith("dev-user:"),
            f"thread_id should be namespaced as dev-user:..., got {thread_id!r}",
        )
        # The conversation_id emitted via SSE must match the thread_id suffix
        expected_namespaced = f"dev-user:{sse_conversation_id}"
        self.assertEqual(
            thread_id,
            expected_namespaced,
            f"astream config thread_id {thread_id!r} does not match SSE conversation_id {sse_conversation_id!r}",
        )


class ChatServiceThreadIdTest(unittest.IsolatedAsyncioTestCase):
    """验证 per-user thread 命名空间隔离。

    内部 thread_id 格式: <user_id>:<conversation_id>
    外部 SSE 事件中仍使用裸 conversation_id。
    """

    async def test_same_conversation_is_namespaced_by_user(self):
        executor = MagicMock()

        async def run(message, thread_id):
            yield AgentEvent(type=EventType.CONVERSATION_START)

        executor.run.side_effect = run
        service = ChatService(executor=executor)

        first = [item async for item in service.stream("hello", "shared", "user-a")]
        second = [item async for item in service.stream("hello", "shared", "user-b")]

        self.assertEqual(executor.run.call_args_list[0].kwargs["thread_id"], "user-a:shared")
        self.assertEqual(executor.run.call_args_list[1].kwargs["thread_id"], "user-b:shared")
        self.assertIn('"conversation_id": "shared"', first[0]["data"])
        self.assertIn('"conversation_id": "shared"', second[0]["data"])
