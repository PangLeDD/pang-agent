import unittest

from fastapi.testclient import TestClient

from app.infrastructure.llm import get_llm
from app.config import settings
from app.core.security import DEV_AUTH_TOKEN
from app.main import app


class LlmClientTest(unittest.TestCase):
    def test_get_llm_requires_api_key(self):
        old_key = settings.llm_api_key
        settings.llm_api_key = ""
        try:
            with self.assertRaisesRegex(RuntimeError, "LLM_API_KEY is not configured"):
                get_llm()
        finally:
            settings.llm_api_key = old_key

    def test_llm_test_requires_token(self):
        response = TestClient(app).post("/agent/llm-test", json={"message": "hello"})

        self.assertEqual(response.status_code, 401)

    def test_llm_test_reports_missing_key_without_network_call(self):
        old_key = settings.llm_api_key
        settings.llm_api_key = ""
        try:
            response = TestClient(app).post(
                "/agent/llm-test",
                json={"message": "hello"},
                headers={"Authorization": f"Bearer {DEV_AUTH_TOKEN}"},
            )
        finally:
            settings.llm_api_key = old_key

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"code": 503, "message": "LLM_API_KEY is not configured", "data": None},
        )
