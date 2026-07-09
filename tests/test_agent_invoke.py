import unittest

from fastapi.testclient import TestClient

from app.config import settings
from app.core.security import DEV_AUTH_TOKEN
from app.main import app


class AgentInvokeTest(unittest.TestCase):
    def test_agent_invoke_requires_token(self):
        response = TestClient(app).post("/agent/invoke", json={"message": "hello"})

        self.assertEqual(response.status_code, 401)

    def test_agent_invoke_returns_graph_reply(self):
        old_key = settings.llm_api_key
        settings.llm_api_key = ""
        try:
            response = TestClient(app).post(
                "/agent/invoke",
                json={"message": "hello"},
                headers={"Authorization": f"Bearer {DEV_AUTH_TOKEN}"},
            )
        finally:
            settings.llm_api_key = old_key

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "code": 200,
                "message": "ok",
                "data": {"reply": "pang-agent received: hello", "conversation_id": None},
            },
        )

    def test_agent_invoke_keeps_conversation_id(self):
        old_key = settings.llm_api_key
        settings.llm_api_key = ""
        try:
            response = TestClient(app).post(
                "/agent/invoke",
                json={"message": "hello", "conversation_id": "c-1"},
                headers={"Authorization": f"Bearer {DEV_AUTH_TOKEN}"},
            )
        finally:
            settings.llm_api_key = old_key

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "code": 200,
                "message": "ok",
                "data": {"reply": "pang-agent received: hello", "conversation_id": "c-1"},
            },
        )
