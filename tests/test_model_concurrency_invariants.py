"""Regression guards for request-scoped model routing.

These are structural gates; concurrency integration testing is still required.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ModelConcurrencyGuards(unittest.TestCase):
    def test_no_shared_request_model_state_in_routes(self):
        for directory in ("api", "backend"):
            with self.subTest(directory=directory):
                code = (ROOT / directory / "main.py").read_text(encoding="utf-8")
                self.assertNotIn("c.active_model = request.model", code,
                    "Request model must be passed explicitly, not stored on global CerebroIA singleton.")

    def test_model_catalog_must_not_claim_unconditional_availability(self):
        for directory in ("api", "backend"):
            with self.subTest(directory=directory):
                code = (ROOT / directory / "main.py").read_text(encoding="utf-8")
                start = code.find('@app.get("/modelos")')
                end = code.find('@app.get("/status")', start)
                self.assertGreaterEqual(start, 0)
                catalog = code[start:end]
                self.assertNotIn('"available": True', catalog,
                    "Availability must be derived from actual configured state.")

    def test_concurrent_request_model_isolation(self):
        import asyncio
        import sys
        sys.path.insert(0, str(ROOT / "backend"))
        from cerebro import set_request_model, get_request_model

        async def _simulate_request(model_name: str, delay: float):
            set_request_model(model_name)
            await asyncio.sleep(delay)
            return get_request_model()

        async def runner():
            tasks = [
                _simulate_request("gemini-2.5-pro", 0.02),
                _simulate_request("gemini-2.5-flash-lite", 0.01),
                _simulate_request("deepseek-chat", 0.015),
            ]
            results = await asyncio.gather(*tasks)
            self.assertEqual(results, ["gemini-2.5-pro", "gemini-2.5-flash-lite", "deepseek-chat"])

        asyncio.run(runner())

if __name__ == "__main__":
    unittest.main()
