"""Unit and security tests for /admin endpoints and telemetry privacy."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient
from backend.main import app, obter_admin_google, obter_usuario_google
import backend.auth as auth
from fastapi import HTTPException

client = TestClient(app)

class AdminTelemetryUnitTests(unittest.TestCase):
    def test_admin_status_unauthenticated_returns_401(self):
        resp = client.get("/admin/status")
        self.assertIn(resp.status_code, (401, 403))

    def test_admin_status_non_admin_returns_403(self):
        async def fake_non_admin():
            raise HTTPException(status_code=403, detail="Acesso administrativo negado.")

        app.dependency_overrides[obter_admin_google] = fake_non_admin
        try:
            resp = client.get("/admin/status")
            self.assertEqual(resp.status_code, 403)
            self.assertIn("negado", resp.json().get("detail", "").lower())
        finally:
            app.dependency_overrides.pop(obter_admin_google, None)

    def test_admin_status_authorized_admin_returns_telemetry_without_secrets(self):
        async def fake_admin():
            return {"email": "admin@helpusbr.com", "name": "SuperAdmin"}

        app.dependency_overrides[obter_admin_google] = fake_admin
        try:
            resp = client.get("/admin/status")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("status", data)
            self.assertIn("app_version", data)
            self.assertIn("provider_configured", data)
            # Ensure no secrets or private keys are exposed in telemetry
            raw_text = resp.text
            self.assertNotIn("AIzaSy", raw_text)
            self.assertNotIn("sk-", raw_text)
            self.assertNotIn("password", raw_text.lower())
        finally:
            app.dependency_overrides.pop(obter_admin_google, None)

    def test_admin_telemetry_unauthenticated_denies_access(self):
        resp = client.get("/admin/telemetry")
        self.assertIn(resp.status_code, (401, 403))

if __name__ == "__main__":
    unittest.main()
