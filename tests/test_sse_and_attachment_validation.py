"""Tests for SSE incremental streaming, attachment security validation, and retry deduplication."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.main import (
    app,
    validar_anexo,
    validar_url_remota,
    MensagemRequest,
    save_idempotent_response,
    get_idempotent_response,
    _gerar_chave_idempotencia,
    claim_or_get_idempotent_request,
)
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

    def test_attachment_rejects_spoofed_magic_bytes(self):
        # Plain text disguised as image
        fake_b64 = "data:image/png;base64,SGVsbG8gd29ybGQgdGhpcyBpcyBub3QgYSBwbmc="
        with self.assertRaises(HTTPException) as ctx:
            validar_anexo(fake_b64, "fake.png")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_attachment_rejects_mime_mismatch(self):
        # Valid PNG declared as image/jpeg
        png_b64 = "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        with self.assertRaises(HTTPException) as ctx:
            validar_anexo(png_b64, "photo.jpg")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_ssrf_blocks_private_ips_and_loopback(self):
        for bad_url in (
            "http://localhost:8080/admin",
            "http://127.0.0.1:3000/api",
            "http://169.254.169.254/latest/meta-data",
            "http://192.168.1.50/photo.jpg",
            "http://10.0.0.1/doc.pdf",
            "file:///etc/passwd",
            "ftp://ftp.server.com/file",
        ):
            with self.subTest(url=bad_url):
                with self.assertRaises(HTTPException) as ctx:
                    validar_url_remota(bad_url)
                self.assertEqual(ctx.exception.status_code, 400)

    def test_ssrf_allows_trusted_internal_domain(self):
        # Should not raise
        validar_url_remota("https://ai.helpusbr.com/assets/logo.png")

    def test_catalog_differentiates_configured_and_healthy(self):
        response = client.get("/modelos")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for modelo in data["modelos"]:
            self.assertIn("configured", modelo)
            self.assertIn("healthy", modelo)
            self.assertIn("health", modelo)
            self.assertIn("available", modelo)
            self.assertIsInstance(modelo["configured"], bool)
            self.assertIsInstance(modelo["healthy"], bool)
            self.assertIsInstance(modelo["health"], str)
            self.assertIsInstance(modelo["available"], bool)
            # Semantica correta: available requer healthy comprovado
            if modelo["health"] == "unknown":
                self.assertFalse(modelo["available"])

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

    def test_idempotency_cache_behavior_and_cross_account_isolation(self):
        key_user1 = _gerar_chave_idempotencia("user1@helpusbr.com", "sess_1", "req_999", "Minha pergunta")
        key_user2 = _gerar_chave_idempotencia("user2@helpusbr.com", "sess_1", "req_999", "Minha pergunta")
        
        self.assertNotEqual(key_user1, key_user2)
        save_idempotent_response(key_user1, {"resposta": "resp_user1", "session_id": "sess_1"})
        
        self.assertIsNotNone(get_idempotent_response(key_user1))
        self.assertEqual(get_idempotent_response(key_user1)["resposta"], "resp_user1")
        # User 2 cannot replay or view User 1's cached response
        self.assertIsNone(get_idempotent_response(key_user2))

    def test_idempotency_atomic_concurrent_blocking(self):
        key = _gerar_chave_idempotencia("user_conc@helpusbr.com", "sess_conc", "req_conc_1", "Pergunta concorrente")
        # Primeiro claim deve ter sucesso
        should_run, cached = claim_or_get_idempotent_request(key)
        self.assertTrue(should_run)
        self.assertIsNone(cached)

        # Segundo claim com a mesma chave enquanto in_progress deve levantar HTTP 409
        with self.assertRaises(HTTPException) as ctx:
            claim_or_get_idempotent_request(key)
        self.assertEqual(ctx.exception.status_code, 409)

if __name__ == "__main__":
    unittest.main()
