import unittest

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import AsyncSessionLocal, Base, get_session


class DatabaseFoundationTest(unittest.TestCase):
    def test_database_foundation_imports_without_connection(self):
        self.assertEqual(
            settings.database_url,
            "postgresql+asyncpg://postgres:postgres@192.168.1.51:5432/pang_agent",
        )
        self.assertIsNotNone(Base.metadata)
        self.assertEqual(AsyncSessionLocal.class_, AsyncSession)
        self.assertTrue(callable(get_session))
