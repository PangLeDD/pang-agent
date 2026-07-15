import json
import unittest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.agent.events import EventType
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

        async def fake_astream(*args, **kwargs):
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
        self.assertIsInstance(start_data["payload"]["conversation_id"], str)

        delta_data = json.loads(blocks[1].split("\n", 1)[1].removeprefix("data: "))
        self.assertEqual(delta_data["payload"]["delta"], "mock delta")

        done_data = json.loads(blocks[2].split("\n", 1)[1].removeprefix("data: "))
        self.assertEqual(done_data["payload"]["reason"], "stop")
