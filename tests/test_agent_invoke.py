import unittest

from fastapi.testclient import TestClient

from app.core.security import DEV_AUTH_TOKEN
from app.main import app


class AgentInvokeTest(unittest.TestCase):
    def test_agent_invoke_requires_token(self):
        response = TestClient(app).post("/agent/invoke", json={"message": "hello"})

        self.assertEqual(response.status_code, 401)

    def test_agent_invoke_returns_graph_reply(self):
        response = TestClient(app).post(
            "/agent/invoke",
            json={"message": "hello"},
            headers={"Authorization": f"Bearer {DEV_AUTH_TOKEN}"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"reply": "pang-agent received: hello"})
