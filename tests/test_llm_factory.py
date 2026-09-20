import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import Message, get_llm_provider
from core.llm.mock_provider import MockProvider


class TestLLMFactory(unittest.TestCase):
    def test_defaults_to_mock_provider(self):
        os.environ.pop("ARTEMIS_LLM_PROVIDER", None)

        provider = get_llm_provider()

        self.assertIsInstance(provider, MockProvider)

    def test_explicit_mock_provider(self):
        provider = get_llm_provider("mock")

        self.assertIsInstance(provider, MockProvider)

    def test_env_var_selects_provider(self):
        os.environ["ARTEMIS_LLM_PROVIDER"] = "mock"
        try:
            provider = get_llm_provider()
            self.assertIsInstance(provider, MockProvider)
        finally:
            os.environ.pop("ARTEMIS_LLM_PROVIDER", None)

    def test_unknown_provider_raises(self):
        with self.assertRaises(ValueError):
            get_llm_provider("gpt-quinhentos")

    def test_mock_provider_returns_canned_reply_when_given(self):
        provider = MockProvider(canned_reply="resposta fixa")

        reply = provider.generate([Message(role="user", content="oi")])

        self.assertEqual(reply, "resposta fixa")

    def test_mock_provider_echoes_last_user_message_by_default(self):
        provider = MockProvider()

        reply = provider.generate(
            [Message(role="user", content="devo contratar agora?")]
        )

        self.assertIn("devo contratar agora?", reply)

    def test_local_provider_is_importable_without_extra_deps(self):
        # requests já é uma dependência do projeto; não deve levantar ImportError.
        provider = get_llm_provider("local", base_url="http://localhost:11434/v1")

        from core.llm.openai_compatible_provider import OpenAICompatibleProvider

        self.assertIsInstance(provider, OpenAICompatibleProvider)


if __name__ == "__main__":
    unittest.main()
