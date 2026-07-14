import unittest

from fastapi.testclient import TestClient

from app.core.security import DEV_AUTH_TOKEN
from app.main import app


class ExceptionHandlerTest(unittest.TestCase):
    def test_http_exception_uses_unified_shape(self):
        response = TestClient(app).post("/agent/stream", json={"message": "hello"})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {"code": 401, "message": "Invalid authentication credentials", "data": None},
        )

    def test_validation_exception_uses_unified_shape(self):
        response = TestClient(app).post(
            "/agent/stream",
            json={"message": 1},
            headers={"Authorization": f"Bearer {DEV_AUTH_TOKEN}"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["code"], 422)
        self.assertEqual(response.json()["data"], None)
