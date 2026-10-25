"""Functional HTTP integration tests for /chat and /chat/stream endpoints and security safeguards."""
import unittest
import sys
import uuid
from pathlib import Path
from unittest.mock import patch, AsyncMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient
from backend.main import (
    app,
    banco,
    claim_or_get_idempotent_request,
    release_idempotent_request,
    _idempotency_cache,
)
from auth import obter_usuario_google

client = TestClient(app)

class ChatEndpointFunctionalTests(unittest.TestCase):
    def tearDown(self):
        app.dependency_overrides.clear()

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
        session_id_u1 = f"sess_u1_{uuid.uuid4().hex[:8]}"
        session_id_u2 = f"sess_u2_{uuid.uuid4().hex[:8]}"
        payload1 = {
            "mensagem": "Pergunta do usuario A",
            "session_id": session_id_u1,
            "model": "gemini-2.5-flash",
            "client_request_id": req_id,
        }

        # Simula Usuario 1
        app.dependency_overrides[obter_usuario_google] = lambda: {"email": "user1@helpusbr.com", "name": "User 1"}
        res1 = client.post("/chat", json=payload1)
        self.assertEqual(res1.status_code, 200)

        # Simula Usuario 2 com o mesmo client_request_id mas em sua propria sessao
        # Deve processar independentemente e nao reutilizar o cache de User 1
        app.dependency_overrides[obter_usuario_google] = lambda: {"email": "user2@helpusbr.com", "name": "User 2"}
        payload2 = {
            "mensagem": "Pergunta do usuario B",
            "session_id": session_id_u2,
            "model": "gemini-2.5-flash",
            "client_request_id": req_id,
        }
        res2 = client.post("/chat", json=payload2)
        self.assertEqual(res2.status_code, 200)

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
            "image_url": "https://ai.helpusbr.com/assets/logo.png",
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

    def test_chat_stream_idempotency_and_cached_replay(self):
        req_id = f"req_stream_{uuid.uuid4().hex[:8]}"
        session_id = f"sess_stream_{uuid.uuid4().hex[:8]}"
        payload = {
            "mensagem": "Pergunta via streaming",
            "session_id": session_id,
            "client_request_id": req_id,
        }
        res1 = client.post("/chat/stream", json=payload)
        self.assertEqual(res1.status_code, 200)
        body1 = res1.text
        self.assertIn("data:", body1)
        self.assertIn("[DONE]", body1)

        # Segunda chamada para o stream deve responder com o cache (replay)
        res2 = client.post("/chat/stream", json=payload)
        self.assertEqual(res2.status_code, 200)
        body2 = res2.text
        self.assertIn("data:", body2)
        self.assertIn('"cached": true', body2.lower())

    def test_chat_stream_concurrency_conflict_409(self):
        # Simula uma requisicao stream que ja esta in_progress
        fake_key = f"anon:sess_conflict:req_conflict:hash1234"
        _idempotency_cache[fake_key] = {"status": "in_progress", "timestamp": 9999999999}
        try:
            with patch("backend.main._gerar_chave_idempotencia", return_value=fake_key):
                payload = {
                    "mensagem": "Pergunta concorrente",
                    "session_id": "sess_conflict",
                    "client_request_id": "req_conflict",
                }
                res = client.post("/chat/stream", json=payload)
                self.assertEqual(res.status_code, 409)
                self.assertIn("concorrencia bloqueada", res.text.lower())
        finally:
            _idempotency_cache.pop(fake_key, None)

    def test_chat_in_progress_released_on_error_allowing_retry(self):
        # Comprova que se houver falha, o finally libera o lock in_progress
        session_id = f"sess_fail_{uuid.uuid4().hex[:8]}"
        client_req_id = f"req_fail_{uuid.uuid4().hex[:8]}"
        payload = {
            "mensagem": "Pergunta que vai simular erro no cerebro",
            "session_id": session_id,
            "client_request_id": client_req_id,
        }
        with patch("backend.main.get_cerebro") as mock_c:
            mock_inst = mock_c.return_value
            mock_inst.pensar = AsyncMock(side_effect=RuntimeError("Simulacao de falha de timeout"))
            res1 = client.post("/chat", json=payload)
            self.assertEqual(res1.status_code, 200)  # Cai no fallback gracefully

        # O lock in_progress DEVE ter sido liberado no finally, permitindo nova tentativa sem 409
        res2 = client.post("/chat", json=payload)
        self.assertEqual(res2.status_code, 200)

    def test_session_ownership_cross_account_forbidden(self):
        # Usuario 1 cria a sessao
        session_id = f"sess_priv_{uuid.uuid4().hex[:8]}"
        app.dependency_overrides[obter_usuario_google] = lambda: {"email": "owner@empresa.com", "name": "Owner"}

        # Mock para simular que no banco a sessao pertence exclusivamente ao owner
        with patch.object(banco, "verificar_propriedade_sessao", new=AsyncMock(side_effect=lambda s, email, proj=None: email == "owner@empresa.com")):
            # Owner consegue acessar
            res1 = client.post("/chat", json={"mensagem": "Mensagem do dono", "session_id": session_id})
            self.assertEqual(res1.status_code, 200)

            # Invasor tenta postar na mesma sessao
            app.dependency_overrides[obter_usuario_google] = lambda: {"email": "attacker@alheio.com", "name": "Attacker"}
            res2 = client.post("/chat", json={"mensagem": "Invasao de sessao", "session_id": session_id})
            self.assertEqual(res2.status_code, 403)
            self.assertIn("pertence a outra conta", res2.text)

            # Invasor tenta no stream
            res3 = client.post("/chat/stream", json={"mensagem": "Invasao stream", "session_id": session_id})
            self.assertEqual(res3.status_code, 403)

    def test_session_verification_fail_closed_on_db_error(self):
        # Comprova que se o banco estiver configurado e falhar, o comportamento e FAIL-CLOSED (503 ou 403, nunca 200 desautorizado)
        session_id = f"sess_err_{uuid.uuid4().hex[:8]}"
        with patch.object(banco, "database_url", "postgresql://user:pass@localhost:5432/helpus"), \
             patch.object(banco, "verificar_propriedade_sessao", new=AsyncMock(side_effect=RuntimeError("Falha de conexao com PostgreSQL"))):
            res = client.post("/chat", json={"mensagem": "Mensagem sob falha de banco", "session_id": session_id})
            self.assertEqual(res.status_code, 503)
            self.assertIn("indisponivel", res.text.lower())

    def test_retry_preserves_idempotency_cache(self):
        # Requisicoes com is_retry=True quando a resposta ja foi concluida devem retornar o cache em vez de re-executar
        req_id = f"req_cached_retry_{uuid.uuid4().hex[:8]}"
        session_id = f"sess_cached_retry_{uuid.uuid4().hex[:8]}"
        payload = {
            "mensagem": "Pergunta para teste de cache em retry",
            "session_id": session_id,
            "client_request_id": req_id,
        }
        res1 = client.post("/chat", json=payload)
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()

        payload["is_retry"] = True
        res2 = client.post("/chat", json=payload)
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(data1["resposta"], data2["resposta"])

    def test_retry_resumes_interrupted_in_progress(self):
        # Se um turno anterior ficou preso in_progress e o cliente envia retry=True, assume execucao sem 409
        fake_key = f"anon:sess_stale_retry:req_stale:hash999"
        _idempotency_cache[fake_key] = {"status": "in_progress", "timestamp": 9999999999}
        try:
            with patch("backend.main._gerar_chave_idempotencia", return_value=fake_key):
                payload = {
                    "mensagem": "Pergunta retry pos interrupcao",
                    "session_id": "sess_stale_retry",
                    "client_request_id": "req_stale",
                    "is_retry": True,
                }
                res = client.post("/chat", json=payload)
                self.assertEqual(res.status_code, 200)
        finally:
            _idempotency_cache.pop(fake_key, None)

if __name__ == "__main__":
    unittest.main()
