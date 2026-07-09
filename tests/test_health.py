import unittest

from fastapi.testclient import TestClient

from app.main import app


class HealthTest(unittest.TestCase):
    def test_health(self):
        response = TestClient(app).get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
