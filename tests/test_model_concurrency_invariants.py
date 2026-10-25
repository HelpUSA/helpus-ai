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

if __name__ == "__main__":
    unittest.main()
