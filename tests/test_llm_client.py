import unittest

from app.infrastructure.llm import get_llm
from app.config import settings


class LlmClientTest(unittest.TestCase):
    def test_get_llm_requires_api_key(self):
        old_key = settings.llm_api_key
        settings.llm_api_key = ""
        try:
            with self.assertRaisesRegex(RuntimeError, "LLM_API_KEY is not configured"):
                get_llm()
        finally:
            settings.llm_api_key = old_key
