"""Tests for SSE incremental streaming, attachment security validation, and retry deduplication."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.main import app, validar_anexo, MensagemRequest
from auth import obter_usuario_google

client = TestClient(app)

class SSEAndAttachmentValidationTests(unittest.TestCase):
    def test_attachment_blocks_env_files(self):
        with self.assertRaises(HTTPException) as ctx:
            validar_anexo(None, ".env")
        self.assertEqual(ctx.exception.status_code, 400)

        with self.assertRaises(HTTPException) as ctx:
            validar_anexo(None, ".env.production")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_attachment_blocks_dangerous_extensions(self):
        for bad_ext in ("malware.exe", "script.bat", "runner.sh", "exploit.ps1", "payload.bin"):
            with self.subTest(file_name=bad_ext):
                with self.assertRaises(HTTPException) as ctx:
                    validar_anexo(None, bad_ext)
                self.assertEqual(ctx.exception.status_code, 400)

    def test_attachment_rejects_disallowed_mime(self):
        bad_mime_b64 = "data:application/x-msdownload;base64,TVqQAAMAAAAEAAAA"
        with self.assertRaises(HTTPException) as ctx:
            validar_anexo(bad_mime_b64, "file.bin")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_attachment_rejects_oversized_payload(self):
        # 14MB base64 string
        oversized = "data:image/png;base64," + "A" * (15 * 1024 * 1024)
        with self.assertRaises(HTTPException) as ctx:
            validar_anexo(oversized, "huge.png")
        self.assertEqual(ctx.exception.status_code, 413)

    def test_attachment_accepts_valid_image(self):
        valid_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        # Should not raise
        validar_anexo(valid_b64, "image.png")

    def test_catalog_differentiates_configured_and_healthy(self):
        response = client.get("/modelos")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for modelo in data["modelos"]:
            self.assertIn("configured", modelo)
            self.assertIn("healthy", modelo)
            self.assertIn("available", modelo)
            self.assertIsInstance(modelo["configured"], bool)
            self.assertIsInstance(modelo["healthy"], bool)
            self.assertIsInstance(modelo["available"], bool)

    def test_request_model_supports_both_image_keys_and_retry(self):
        req = MensagemRequest(
            mensagem="Ola",
            imagem_base64="data:image/png;base64,abc",
            file_name="test.png",
            is_retry=True,
            client_request_id="req_123",
        )
        self.assertEqual(req.imagem_base64, "data:image/png;base64,abc")
        self.assertTrue(req.is_retry)
        self.assertEqual(req.client_request_id, "req_123")

if __name__ == "__main__":
    unittest.main()
