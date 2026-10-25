"""Tests for server-verified model catalog and multi-model routing invariants."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from backend.multi_ai_provider import resolve_model_alias, MultiAIConfig, MultiAIProvider
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

class ModelRoutingCatalogTests(unittest.TestCase):
    def test_catalog_endpoint_returns_authorized_models(self):
        response = client.get("/modelos")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("modelos", data)
        model_ids = [m["id"] for m in data["modelos"]]
        self.assertIn("gemini-2.5-flash-lite", model_ids)
        self.assertIn("gemini-2.5-flash", model_ids)
        self.assertIn("gemini-2.5-pro", model_ids)
        self.assertIn("deepseek-chat", model_ids)
        self.assertEqual(data["default_model"], "gemini-2.5-flash")

    def test_resolve_model_alias_mapping(self):
        self.assertEqual(resolve_model_alias("gemini-2.5-flash-lite"), "helpus-fast")
        self.assertEqual(resolve_model_alias("gemini-2.5-flash"), "helpus-general")
        self.assertEqual(resolve_model_alias("gemini-2.5-pro"), "helpus-reasoner")
        self.assertEqual(resolve_model_alias("deepseek-chat"), "helpus-code")
        self.assertEqual(resolve_model_alias("helpus-code"), "helpus-code")
        self.assertEqual(resolve_model_alias(None), "helpus-general")

    def test_multi_ai_provider_uses_custom_alias(self):
        class CaptureClient:
            def __init__(self, *args, **kwargs):
                self.calls = []

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, headers=None, json=None):
                self.calls.append({"url": url, "headers": headers, "json": json})
                class MockResp:
                    status_code = 200
                    def json(self):
                        return {
                            "choices": [{"message": {"content": "ok"}}],
                            "usage": {"completion_tokens": 5},
                            "_helpus": {"route": {"primary": json.get("model", "helpus-general")}},
                        }
                return MockResp()

        mock_client = CaptureClient()
        config = MultiAIConfig(
            enabled=True,
            base_url="http://mock-router",
            api_key="mock-key",
            timeout_seconds=10.0,
            mode="single",
            fallback_to_legacy=False,
            default_alias="helpus-general",
        )
        provider = MultiAIProvider(config=config, client_factory=lambda **kwargs: mock_client)

        import asyncio
        result = asyncio.run(provider.generate("test prompt", max_tokens=100, temperature=0.7, alias="helpus-code"))
        self.assertEqual(result.text, "ok")
        self.assertEqual(mock_client.calls[0]["json"]["model"], "helpus-code")

if __name__ == "__main__":
    unittest.main()
