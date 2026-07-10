import unittest
from unittest.mock import patch

from app.agent import invoke_agent
from app.config import settings


class AgentGraphTest(unittest.TestCase):
    def test_graph_uses_echo_fallback_without_llm_key(self):
        old_key = settings.llm_api_key
        settings.llm_api_key = ""
        try:
            self.assertEqual(invoke_agent("hello"), "pang-agent received: hello")
        finally:
            settings.llm_api_key = old_key

    def test_graph_uses_llm_when_key_exists(self):
        old_key = settings.llm_api_key
        settings.llm_api_key = "fake-key"
        try:
            with patch("app.agent.graph.invoke_llm", return_value="llm reply") as mock_llm:
                self.assertEqual(invoke_agent("hello"), "llm reply")
                mock_llm.assert_called_once_with("hello")
        finally:
            settings.llm_api_key = old_key
