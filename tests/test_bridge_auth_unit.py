"""Runtime unit tests for the dedicated HelpUSDev bridge authorization dependency."""
import asyncio
import importlib
import os
from unittest import TestCase
from unittest.mock import patch

from fastapi import HTTPException

class BridgeAuthUnitTests(TestCase):
    def test_authorization_negative_and_positive(self):
        for namespace in ("api.main", "backend.main"):
            with self.subTest(namespace=namespace):
                module = importlib.import_module(namespace)
                guard = module.require_bridge_token
                with patch.dict(os.environ, {}, clear=False):
                    os.environ.pop("HELPUS_BRIDGE_API_TOKEN", None)
                    with self.assertRaises(HTTPException) as error:
                        guard("Bearer anything")
                    self.assertEqual(error.exception.status_code, 503)
                with patch.dict(os.environ, {"HELPUS_BRIDGE_API_TOKEN": "unit-test-secret"}):
                    for bad in (None, "", "Basic unit-test-secret", "Bearer incorrect", "Bearer"):
                        with self.assertRaises(HTTPException) as error:
                            guard(bad)
                        self.assertEqual(error.exception.status_code, 401)
                    self.assertIsNone(guard("Bearer unit-test-secret"))
