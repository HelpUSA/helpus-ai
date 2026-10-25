"""Functional HTTP integration tests for /chat endpoint and security safeguards."""
import unittest
import sys
import uuid
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient
from backend.main import app
from auth import obter_usuario_google

client = TestClient(app)

class ChatEndpointFunctionalTests(unittest.TestCase):
    def test_chat_unbound_local_session_id_fixed(self):
        # Envia requisicao sem session_id para comprovar que nao ocorre UnboundLocalError
        payload = {
            "mensagem": "Ola assistente",
            "model": "gemini-2.5-flash",
            "client_request_id": f"req_init_{uuid.uuid4().hex[:8]}",
        }
        response = client.post("/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("session_id"))
        self.assertEqual(data.get("model_requested"), "gemini-2.5-flash")

    def test_chat_idempotency_caching(self):
        req_id = f"req_idem_{uuid.uuid4().hex[:8]}"
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        payload = {
            "mensagem": "Pergunta com idempotencia",
            "session_id": session_id,
            "model": "gemini-2.5-flash-lite",
            "client_request_id": req_id,
        }
        res1 = client.post("/chat", json=payload)
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()

        # Segunda chamada com o mesmo client_request_id deve retornar o cache identico
        res2 = client.post("/chat", json=payload)
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(data1["resposta"], data2["resposta"])
        self.assertEqual(data1["session_id"], data2["session_id"])

    def test_chat_idempotency_cross_user_isolation(self):
        req_id = f"req_cross_{uuid.uuid4().hex[:8]}"
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        payload = {
            "mensagem": "Pergunta do usuario A",
            "session_id": session_id,
            "model": "gemini-2.5-flash",
            "client_request_id": req_id,
        }

        # Simula Usuario 1
        app.dependency_overrides[obter_usuario_google] = lambda: {"email": "user1@helpusbr.com", "name": "User 1"}
        res1 = client.post("/chat", json=payload)
        self.assertEqual(res1.status_code, 200)

        # Simula Usuario 2 com o mesmo client_request_id e session_id
        # Deve processar independentemente e nao reutilizar o cache de User 1
        app.dependency_overrides[obter_usuario_google] = lambda: {"email": "user2@helpusbr.com", "name": "User 2"}
        payload["mensagem"] = "Pergunta diferente do usuario B"
        res2 = client.post("/chat", json=payload)
        self.assertEqual(res2.status_code, 200)

        app.dependency_overrides.clear()

    def test_chat_ssrf_rejects_arbitrary_urls(self):
        payload = {
            "mensagem": "Analise esta imagem remota",
            "image_url": "http://evil-attacker-site.com/exploit.jpg",
        }
        response = client.post("/chat", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("SSRF", response.text)

    def test_chat_ssrf_allows_trusted_url(self):
        payload = {
            "mensagem": "Analise imagem de dominio confiavel",
            "image_url": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119",
        }
        response = client.post("/chat", json=payload)
        self.assertEqual(response.status_code, 200)

    def test_chat_retry_flag_accepted(self):
        session_id = f"sess_retry_{uuid.uuid4().hex[:8]}"
        payload = {
            "mensagem": "Pergunta inicial para retry",
            "session_id": session_id,
            "is_retry": True,
            "client_request_id": f"req_retry_{uuid.uuid4().hex[:8]}",
        }
        response = client.post("/chat", json=payload)
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
