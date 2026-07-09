import unittest

from fastapi.testclient import TestClient

from app.api.router import protected_router
from app.core.security import DEV_AUTH_TOKEN
from app.core.security import get_current_user
from app.main import app


class AuthStubTest(unittest.TestCase):
    def test_protected_router_has_auth_dependency(self):
        self.assertEqual(protected_router.dependencies[0].dependency, get_current_user)

    def test_missing_token_is_rejected(self):
        response = TestClient(app).get("/users/me")

        self.assertEqual(response.status_code, 401)

    def test_wrong_token_is_rejected(self):
        response = TestClient(app).get(
            "/users/me",
            headers={"Authorization": "Bearer wrong-token"},
        )

        self.assertEqual(response.status_code, 401)

    def test_dev_token_returns_current_user(self):
        response = TestClient(app).get(
            "/users/me",
            headers={"Authorization": f"Bearer {DEV_AUTH_TOKEN}"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"code": 200, "message": "ok", "data": {"id": "dev-user", "username": "dev"}},
        )
