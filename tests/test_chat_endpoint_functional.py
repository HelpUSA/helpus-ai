"""Functional HTTP integration tests for /chat and /chat/stream endpoints and security safeguards."""
import os
os.environ["HELPUS_TEST_MODE"] = "1"
import unittest
import sys
import uuid
import time
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

client = TestClient(app, raise_server_exceptions=False)

class ChatEndpointFunctionalTests(unittest.TestCase):
    def setUp(self):
        self.orig_db_url = os.environ.pop('DATABASE_URL', None)
        self.orig_banco_url = getattr(banco, 'database_url', None)
        banco.database_url = None

    def tearDown(self):
        app.dependency_overrides.clear()
        if self.orig_db_url is not None:
            os.environ['DATABASE_URL'] = self.orig_db_url
        else:
            os.environ.pop('DATABASE_URL', None)
        banco.database_url = self.orig_banco_url

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

    def test_retry_during_active_inference_rejected_409(self):
        # Se a inferencia original ainda estiver ativa dentro do lease (ex: 5s atras), retry deve ser rejeitado com 409
        import time
        fake_key = f"anon:sess_active:req_active:hash888"
        _idempotency_cache[fake_key] = {"status": "in_progress", "timestamp": time.time() - 5.0}
        try:
            with patch("backend.main._gerar_chave_idempotencia", return_value=fake_key):
                payload = {
                    "mensagem": "Pergunta retry enquanto original ativa",
                    "session_id": "sess_active",
                    "client_request_id": "req_active",
                    "is_retry": True,
                }
                res = client.post("/chat", json=payload)
                self.assertEqual(res.status_code, 409)
                self.assertIn("processamento ativo", res.text)
        finally:
            _idempotency_cache.pop(fake_key, None)

    def test_retry_resumes_interrupted_in_progress(self):
        # Se um turno anterior ficou preso in_progress e o lease expirou (>30s), cliente com retry=True assume execucao
        import time
        fake_key = f"anon:sess_stale_retry:req_stale:hash999"
        _idempotency_cache[fake_key] = {"status": "in_progress", "timestamp": time.time() - 45.0}
        try:
            with patch("backend.main._gerar_chave_idempotencia", return_value=fake_key):
                payload = {
                    "mensagem": "Pergunta retry pos interrupcao com lease expirado",
                    "session_id": "sess_stale_retry",
                    "client_request_id": "req_stale",
                    "is_retry": True,
                }
                res = client.post("/chat", json=payload)
                self.assertEqual(res.status_code, 200)
        finally:
            _idempotency_cache.pop(fake_key, None)

    def test_admin_audit_log_authorized_and_sanitized(self):
        from auth import obter_admin_google
        app.dependency_overrides[obter_admin_google] = lambda: {"email": "superadmin@helpusbr.com", "role": "admin"}
        try:
            res = client.get("/admin/audit-log")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data.get("ok"))
            self.assertEqual(data.get("admin"), "superadmin@helpusbr.com")
            self.assertNotIn("secret", str(data).lower())
            self.assertNotIn("token", str(data).lower())
        finally:
            app.dependency_overrides.clear()

    def test_admin_audit_log_unauthenticated_rejected(self):
        # Sem credencial de admin deve retornar 401 ou 403
        res = client.get("/admin/audit-log")
        self.assertIn(res.status_code, [401, 403])

    def test_idempotency_heartbeat_keeps_long_inference_alive(self):
        # Inferencia com mais de 35s de duracao mas com heartbeat ativo (<15s) rejeita retries com 409
        fake_key = f"anon:sess_long_hb:req_long_hb:hash123"
        now = time.time()
        _idempotency_cache[fake_key] = {
            "status": "in_progress",
            "timestamp": now - 45.0, # inicio ha 45s (>30s)
            "last_heartbeat": now - 3.0, # ultimo chunk emitido ha apenas 3s
            "owner_token": "token_original_alive"
        }
        try:
            with patch("backend.main._gerar_chave_idempotencia", return_value=fake_key):
                payload = {
                    "mensagem": "Pergunta retry enquanto inferencia longa ainda esta ativa",
                    "session_id": "sess_long_hb",
                    "client_request_id": "req_long_hb",
                    "is_retry": True,
                }
                res = client.post("/chat", json=payload)
                self.assertEqual(res.status_code, 409)
                self.assertIn("heartbeat ativo", res.text)
        finally:
            _idempotency_cache.pop(fake_key, None)

    def test_idempotency_fencing_token_rejects_late_worker(self):
        from backend.main import claim_or_get_idempotent_request, complete_idempotent_request
        test_key = "test_fencing_key"
        now = time.time()
        # 1. Worker 1 reivindica
        should_run1, _, token1 = claim_or_get_idempotent_request(test_key)
        self.assertTrue(should_run1)
        self.assertIsNotNone(token1)

        # 2. Worker 1 simula travamento de heartbeat (> 15s sem heartbeat)
        _idempotency_cache[test_key]["last_heartbeat"] = now - 20.0

        # 3. Worker 2 chega como retry e assume com sucesso com NOVO token
        should_run2, _, token2 = claim_or_get_idempotent_request(test_key, is_retry=True)
        self.assertTrue(should_run2)
        self.assertNotEqual(token1, token2)

        # 4. Worker 1 acorda tardiamente e tenta finalizar com o token antigo
        ok_late = complete_idempotent_request(test_key, {"resposta": "late"}, owner_token=token1)
        self.assertFalse(ok_late, "Worker tardio cercado (fenced) DEVE ser rejeitado e nao sobrescrever")

        # 5. Worker 2 finaliza com o token correto
        ok_valid = complete_idempotent_request(test_key, {"resposta": "valid"}, owner_token=token2)
        self.assertTrue(ok_valid)
        self.assertEqual(_idempotency_cache[test_key]["response"]["resposta"], "valid")
        _idempotency_cache.pop(test_key, None)

    def test_fail_closed_in_production_environment(self):
        import asyncio
        # Em producao, mesmo com HELPUS_TEST_MODE=1, se o banco falhar, nega acesso (FAIL-CLOSED)
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "HELPUS_TEST_MODE": "1"}),              patch.object(banco, "pool", None):
            allowed = asyncio.run(banco.verificar_propriedade_sessao("sess_prod_fail", "user@helpusbr.com"))
            self.assertFalse(allowed, "Producao DEVE ser fail-closed estrito sem memoria")

    def test_fail_closed_when_database_url_configured_and_pool_is_none(self):
        import asyncio
        # Se DATABASE_URL estiver configurada mas o pool for None (banco caiu), nega acesso mesmo em test mode
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:pass@localhost:5432/helpus", "HELPUS_TEST_MODE": "1"}),              patch.object(banco, "pool", None):
            allowed = asyncio.run(banco.verificar_propriedade_sessao("sess_down_fail", "user@helpusbr.com"))
            self.assertFalse(allowed, "Se banco estiver configurado e pool indisponivel, DEVE ser fail-closed")

    def test_admin_audit_log_empty_when_no_events_and_paginates(self):
        from auth import obter_admin_google
        app.dependency_overrides[obter_admin_google] = lambda: {"email": "superadmin@helpusbr.com", "role": "admin"}
        try:
            banco._audit_log_memoria.clear()
            # 1. Sem eventos previos, deve retornar lista vazia
            res = client.get("/admin/audit-log?limite=10&offset=0")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["total_eventos"], 0)
            self.assertEqual(data["eventos"], [])
            self.assertEqual(data["admin"], "superadmin@helpusbr.com")

            # 2. Segunda chamada: o evento da primeira chamada (ADMIN_AUDIT_LOG_VIEWED) foi persistido!
            res2 = client.get("/admin/audit-log?limite=10&offset=0")
            self.assertEqual(res2.status_code, 200)
            data2 = res2.json()
            self.assertGreaterEqual(data2["total_eventos"], 1)
            self.assertEqual(data2["eventos"][0]["action"], "ADMIN_AUDIT_LOG_VIEWED")
        finally:
            app.dependency_overrides.clear()

    def test_tenant_project_memories_forbidden_for_other_users(self):
        from auth import obter_usuario_google
        # Simula usuario Alice sendo dono do projeto 'proj_alice'
        banco._projetos_memoria["proj_alice"] = "alice@helpusbr.com"

        # Bob tenta acessar as memorias de Alice
        app.dependency_overrides[obter_usuario_google] = lambda: {"email": "bob@helpusbr.com", "name": "Bob"}
        try:
            res_get = client.get("/memorias?project_id=proj_alice")
            self.assertEqual(res_get.status_code, 403)
            self.assertIn("Acesso negado", res_get.text)

            res_post = client.post("/memorias", json={
                "project_id": "proj_alice",
                "title": "Invadir memoria",
                "content": "Conteudo nao autorizado"
            })
            self.assertEqual(res_post.status_code, 403)
            self.assertIn("Acesso negado", res_post.text)
        finally:
            app.dependency_overrides.clear()

    def test_audit_log_fail_closed_raises_503_when_db_down(self):
        from auth import obter_admin_google
        app.dependency_overrides[obter_admin_google] = lambda: {"email": "superadmin@helpusbr.com", "role": "admin"}
        try:
            # Com DATABASE_URL configurada e pool inativo (banco caiu), deve retornar 503 e NAO memoria
            with patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:pass@localhost:5432/helpus"}),                  patch.object(banco, "pool", None):
                banco.database_url = "postgresql://user:pass@localhost:5432/helpus"
                res = client.get("/admin/audit-log")
                self.assertEqual(res.status_code, 503)
                self.assertIn("indisponivel", res.text.lower())
        finally:
            app.dependency_overrides.clear()
            banco.database_url = None

    def test_audit_log_sanitization_allowlist_and_secret_masking(self):
        import asyncio
        from backend.banco import sanitizar_detalhes_auditoria
        raw_details = {
            "limite": 25,
            "api_key": "minha_chave_secreta_123",
            "bearer_token": "bearer eyJhbGciOi...",
            "session_id": "sess_safe_audit",
            "password": "senha_insegura",
            "unknown_custom_field": "dado_qualquer"
        }
        sanitized = sanitizar_detalhes_auditoria(raw_details)
        # Chaves permitidas
        self.assertIn("limite", sanitized)
        self.assertEqual(sanitized["limite"], 25)
        self.assertIn("session_id", sanitized)
        # Chaves proibidas/desconhecidas DEVEM ser descartadas
        self.assertNotIn("api_key", sanitized)
        self.assertNotIn("bearer_token", sanitized)
        self.assertNotIn("password", sanitized)
        self.assertNotIn("unknown_custom_field", sanitized)

    def test_complete_idempotent_request_strict_cas_and_fencing(self):
        from backend.main import (
            claim_or_get_idempotent_request,
            complete_idempotent_request,
            release_idempotent_request,
            _idempotency_cache
        )
        key = f"anon:cas_test:req_{uuid.uuid4().hex[:6]}:hash"
        # 1. Escrita sem claim previo (chave inexistente) DEVE falhar
        self.assertFalse(complete_idempotent_request(key, {"resposta": "fake"}, owner_token="qualquer"))

        # 2. Claim valido
        should_run, _, token = claim_or_get_idempotent_request(key)
        self.assertTrue(should_run)
        self.assertIsNotNone(token)

        # 3. Escrita com token None ou vazio DEVE falhar
        self.assertFalse(complete_idempotent_request(key, {"resposta": "fake"}, owner_token=None))
        self.assertFalse(complete_idempotent_request(key, {"resposta": "fake"}, owner_token=""))

        # 4. Escrita com token divergente (outro executor) DEVE falhar
        self.assertFalse(complete_idempotent_request(key, {"resposta": "fake"}, owner_token="wrong_token"))

        # 5. Release com token divergente DEVE falhar
        self.assertFalse(release_idempotent_request(key, owner_token="wrong_token"))

        # 6. Conclusao valida com token correto
        self.assertTrue(complete_idempotent_request(key, {"resposta": "correta"}, owner_token=token))
        self.assertEqual(_idempotency_cache[key]["status"], "completed")

        # 7. Tentativa de re-escrever quando ja concluida DEVE falhar
        self.assertFalse(complete_idempotent_request(key, {"resposta": "sobrescrever"}, owner_token=token))

        _idempotency_cache.pop(key, None)

    def test_independent_heartbeat_during_silent_inference(self):
        import asyncio
        from backend.main import (
            claim_or_get_idempotent_request,
            IdempotencyHeartbeatSession,
            _idempotency_cache
        )
        async def run_silent_test():
            key = f"anon:silent_hb:req_{uuid.uuid4().hex[:6]}:hash"
            should_run, _, token = claim_or_get_idempotent_request(key)
            self.assertTrue(should_run)

            # Simula inicio ha 40s
            now = time.time()
            _idempotency_cache[key]["timestamp"] = now - 40.0
            _idempotency_cache[key]["last_heartbeat"] = now - 40.0

            # Inicia sessao independente de heartbeat com intervalo de 0.1s para o teste
            hb = IdempotencyHeartbeatSession(key, token, interval=0.05)
            hb.start()
            # Aguarda 0.2s para garantir que o loop de heartbeat executou ao menos uma renovacao
            await asyncio.sleep(0.2)
            await hb.stop()

            # Comprova que last_heartbeat foi renovado para carimbo recente (< 1s)
            updated_hb = _idempotency_cache[key]["last_heartbeat"]
            self.assertGreater(updated_hb, now - 2.0)
            _idempotency_cache.pop(key, None)

        asyncio.run(run_silent_test())

    def test_audit_log_503_constant_error_message_ciclo_017(self):
        # Garante que falha no log de auditoria retorna HTTP 503 com mensagem publica constante
        from auth import obter_admin_google
        app.dependency_overrides[obter_admin_google] = lambda: {"email": "superadmin@helpusbr.com", "role": "admin"}
        try:
            with patch.object(banco, "listar_eventos_auditoria", new=AsyncMock(side_effect=Exception("sensitive internal db detail"))):
                response = client.get("/admin/audit-log")
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()["detail"], "Servico de auditoria temporariamente indisponivel.")
        finally:
            app.dependency_overrides.pop(obter_admin_google, None)

    def test_pure_get_idempotent_response_no_side_effects(self):
        from backend.main import get_idempotent_response, claim_or_get_idempotent_request, complete_idempotent_request, _idempotency_cache
        test_key = f"pure_test_key_{uuid.uuid4().hex[:6]}"
        
        # 1. Chave inexistente retorna None sem criar entrada
        self.assertIsNone(get_idempotent_response(test_key))
        self.assertNotIn(test_key, _idempotency_cache)

        # 2. Requisicao in_progress ainda nao retorna resposta
        should_run, cached, token = claim_or_get_idempotent_request(test_key)
        self.assertTrue(should_run)
        self.assertIsNone(get_idempotent_response(test_key))

        # 3. Apenas quando completada retorna a resposta
        complete_idempotent_request(test_key, {"resposta": "teste puro"}, owner_token=token)
        cached_result = get_idempotent_response(test_key)
        self.assertIsNotNone(cached_result)
        self.assertEqual(cached_result.get("resposta"), "teste puro")

        _idempotency_cache.pop(test_key, None)

    def test_fenced_worker_aborts_db_persistence_in_chat(self):
        # Simula worker perdendo seu fencing token (substituido por retry/timeout)
        from backend.main import claim_or_get_idempotent_request, _idempotency_cache
        req_id = f"fenced_req_{uuid.uuid4().hex[:8]}"
        session_id = f"sess_fence_{uuid.uuid4().hex[:8]}"
        payload = {
            "mensagem": "Teste de fencing de worker",
            "session_id": session_id,
            "model": "gemini-2.5-flash",
            "client_request_id": req_id,
        }

        with patch.object(banco, "salvar_mensagem", new=AsyncMock()) as mock_salvar:
            # Primeiro claim legitimo
            # Forcamos que durante a chamada o token de cache mude para simular um fence
            orig_is_owner = sys.modules["backend.main"].is_owner_token_valid
            def mock_fence_check(key, token):
                if key and req_id in key:
                    return False # Simula worker cercado
                return orig_is_owner(key, token)

            with patch("backend.main.is_owner_token_valid", side_effect=mock_fence_check):
                res = client.post("/chat", json=payload)
                self.assertEqual(res.status_code, 409)
                self.assertIn("fenced", res.json()["detail"].lower())

            # Garante que salvar_mensagem NAO foi invocado com role 'assistant' por worker cercado
            for call_args in mock_salvar.call_args_list:
                args, kwargs = call_args
                if len(args) >= 2:
                    self.assertNotEqual(args[1], "assistant")
                if "role" in kwargs:
                    self.assertNotEqual(kwargs["role"], "assistant")

    def test_no_startup_ddl_when_persistent_database_configured(self):
        import asyncio
        from backend.banco import BancoDados
        
        # Cria banco com database_url configurado
        banco_test = BancoDados()
        banco_test.database_url = "postgresql://mock_user:pass@localhost:5432/mock_db"
        
        with patch.object(banco_test, "pool") as mock_pool:
            from unittest.mock import MagicMock
            mock_conn = MagicMock()
            mock_cur = AsyncMock()
            mock_pool.connection.return_value.__aenter__.return_value = mock_conn
            mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
            mock_conn.cursor.return_value.__aexit__.return_value = None
            # Simula todas as tabelas obrigatorias presentes e versao nominal aplicada
            mock_cur.fetchall.side_effect = [
                [("conversas",), ("admin_audit_events",), ("schema_migrations",), ("sessoes",)],
                [("003_sessoes_schema_and_diagnostic",)]
            ]
            
            asyncio.run(banco_test.criar_tabelas())
            
            # Como tem database_url, apenas SELECT de verificacao ocorre, nunca DDL
            for call in mock_cur.execute.call_args_list:
                sql = call[0][0].upper()
                self.assertNotIn("CREATE TABLE", sql)
                self.assertNotIn("ALTER TABLE", sql)

    def test_http_sse_turn_persists_exactly_one_assistant_message(self):
        # Garante que um turno completo via /chat/stream salva EXATAMENTE UMA mensagem do assistente
        session_id = f"sess_sse_exact1_{uuid.uuid4().hex[:8]}"
        req_id = f"req_sse_exact1_{uuid.uuid4().hex[:8]}"
        payload = {
            "mensagem": "Pergunta para SSE persistencia exata",
            "session_id": session_id,
            "model": "gemini-2.5-flash",
            "client_request_id": req_id,
        }

        with patch.object(banco, "salvar_mensagem", new=AsyncMock()) as mock_salvar:
            with client.stream("POST", "/chat/stream", json=payload) as response:
                self.assertEqual(response.status_code, 200)
                body = "".join(response.iter_text())
                self.assertIn("data:", body)
                self.assertIn("[DONE]", body)

            # Verifica chamadas a salvar_mensagem
            assistant_saves = [
                call for call in mock_salvar.call_args_list
                if (len(call[0]) >= 2 and call[0][1] == "assistant") or call[1].get("role") == "assistant"
            ]
            self.assertEqual(len(assistant_saves), 1, f"Esperado exatamente 1 assistant salvo, obtido {len(assistant_saves)}")
            # Confirma que a resposta persistida nao e vazia
            saved_content = assistant_saves[0][1].get("content") if "content" in assistant_saves[0][1] else assistant_saves[0][0][2]
            self.assertTrue(len(saved_content) > 0)

    def test_http_sse_fencing_prevents_late_persistence(self):
        # Simula cancelamento ou retry concorrente que faz o worker perder a posse antes de gravar
        session_id = f"sess_sse_fence_{uuid.uuid4().hex[:8]}"
        req_id = f"req_sse_fence_{uuid.uuid4().hex[:8]}"
        payload = {
            "mensagem": "Pergunta para teste de stream cercado",
            "session_id": session_id,
            "model": "gemini-2.5-flash",
            "client_request_id": req_id,
        }

        with patch.object(banco, "salvar_mensagem", new=AsyncMock()) as mock_salvar:
            # Forcamos is_owner_token_valid a retornar False ao final do stream
            orig_valid = sys.modules["backend.main"].is_owner_token_valid
            def mock_fence(k, t):
                if k and req_id in k:
                    return False
                return orig_valid(k, t)

            with patch("backend.main.is_owner_token_valid", side_effect=mock_fence):
                with client.stream("POST", "/chat/stream", json=payload) as response:
                    self.assertEqual(response.status_code, 200)
                    body = "".join(response.iter_text())
                    self.assertIn("[DONE]", body)

            # Worker cercado DEVE ter a persistencia de assistant abortada
            assistant_saves = [
                call for call in mock_salvar.call_args_list
                if (len(call[0]) >= 2 and call[0][1] == "assistant") or call[1].get("role") == "assistant"
            ]
            self.assertEqual(len(assistant_saves), 0, "Worker cercado nao deve persistir mensagem")

    def test_http_sse_retry_flag_does_not_duplicate_user_message(self):
        # Testa chamada com is_retry=True garantindo que mensagem do usuario nao seja reinserida
        session_id = f"sess_sse_retry_{uuid.uuid4().hex[:8]}"
        req_id = f"req_sse_retry_{uuid.uuid4().hex[:8]}"
        payload = {
            "mensagem": "Pergunta de retry",
            "session_id": session_id,
            "model": "gemini-2.5-flash",
            "client_request_id": req_id,
            "is_retry": True,
        }

        with patch.object(banco, "salvar_mensagem", new=AsyncMock()) as mock_salvar:
            with client.stream("POST", "/chat/stream", json=payload) as response:
                self.assertEqual(response.status_code, 200)

            user_saves = [
                call for call in mock_salvar.call_args_list
                if (len(call[0]) >= 2 and call[0][1] == "user") or call[1].get("role") == "user"
            ]
            self.assertEqual(len(user_saves), 0, "Chamada com is_retry=True nao deve salvar mensagem de usuario duplicada")

    def test_schema_verification_fails_closed_when_tables_missing_under_persistent_db(self):
        import asyncio
        from backend.banco import BancoDados
        
        banco_test = BancoDados()
        banco_test.database_url = "postgresql://user:pass@localhost:5432/helpus_test"
        
        with patch.object(banco_test, "pool") as mock_pool:
            from unittest.mock import MagicMock
            mock_conn = MagicMock()
            mock_cur = AsyncMock()
            mock_pool.connection.return_value.__aenter__.return_value = mock_conn
            mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
            mock_conn.cursor.return_value.__aexit__.return_value = None
            
            # Simula tabelas obrigatorias ausentes
            mock_cur.fetchall.return_value = [("conversas",)] # faltando audit e migrations
            
            with self.assertRaises(RuntimeError) as ctx:
                asyncio.run(banco_test.criar_tabelas())
            
            self.assertIn("Tabelas obrigatorias ausentes no banco persistente", str(ctx.exception))
            # Garante que nenhum CREATE TABLE DDL foi executado
            for call in mock_cur.execute.call_args_list:
                sql = call[0][0].upper()
                self.assertNotIn("CREATE TABLE", sql)
                self.assertNotIn("ALTER TABLE", sql)

    def test_http_sse_persistence_failure_releases_claim_without_completion(self):
        # Garante que erro em salvar_mensagem no stream NAO conclui claim, NAO emite done:true e emite erro SSE
        from backend.main import _idempotency_cache, _gerar_chave_idempotencia
        session_id = f"sess_sse_fail_{uuid.uuid4().hex[:8]}"
        req_id = f"req_sse_fail_{uuid.uuid4().hex[:8]}"
        payload = {
            "mensagem": "Pergunta simulando falha de banco",
            "session_id": session_id,
            "model": "gemini-2.5-flash",
            "client_request_id": req_id,
        }
        
        async def mock_salvar_error(*args, **kwargs):
            if kwargs.get("role") == "assistant" or (len(args) >= 2 and args[1] == "assistant"):
                raise RuntimeError("Simulated DB connection failure on save")
            return None

        with patch.object(banco, "salvar_mensagem", side_effect=mock_salvar_error):
            with client.stream("POST", "/chat/stream", json=payload) as response:
                self.assertEqual(response.status_code, 200)
                body = "".join(response.iter_text())
                self.assertNotIn('"done": true', body.lower(), "done:true NAO deve ser emitido quando a persistencia falha")
                self.assertIn("PERSISTENCE_FAILED", body, "Evento SSE deve emitir codigo PERSISTENCE_FAILED")
                self.assertIn("[DONE]", body)

        # A chave de idempotencia gerada NAO DEVE estar no status 'completed'
        key = _gerar_chave_idempotencia(None, session_id, req_id, payload["mensagem"])
        entry = _idempotency_cache.get(key)
        if entry:
            self.assertNotEqual(entry.get("status"), "completed", "Claim nao pode ser concluido se persistencia falhou")

    def test_schema_verification_fails_closed_when_nominal_migration_missing(self):
        import asyncio
        from backend.banco import BancoDados
        
        banco_test = BancoDados()
        banco_test.database_url = "postgresql://user:pass@localhost:5432/helpus_test"
        
        with patch.object(banco_test, "pool") as mock_pool:
            from unittest.mock import MagicMock
            mock_conn = MagicMock()
            mock_cur = AsyncMock()
            mock_pool.connection.return_value.__aenter__.return_value = mock_conn
            mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
            mock_conn.cursor.return_value.__aexit__.return_value = None
            
            # Tabelas estao presentes
            mock_cur.fetchall.side_effect = [
                [("conversas",), ("admin_audit_events",), ("schema_migrations",), ("sessoes",)],
                [("001_old_migration",)]  # Faltando '003_sessoes_schema_and_diagnostic'
            ]
            
            with self.assertRaises(RuntimeError) as ctx:
                asyncio.run(banco_test.criar_tabelas())
            
            self.assertIn("Migracoes nominais obrigatorias ausentes no banco persistente", str(ctx.exception))
            self.assertIn("003_sessoes_schema_and_diagnostic", str(ctx.exception))

    def test_turn_locks_cleanup_prevents_memory_leak(self):
        import asyncio
        from backend.main import turn_lock_context, _turn_locks

        test_key = f"key_leak_test_{uuid.uuid4().hex[:8]}"

        async def _run_lock():
            async with turn_lock_context(test_key):
                self.assertIn(test_key, _turn_locks)
            self.assertNotIn(test_key, _turn_locks, "Lock deve ser removido de _turn_locks apos conclusao")

        asyncio.run(_run_lock())

    def test_structured_logging_allowlist_drops_forbidden_fields(self):
        import io
        import json
        from contextlib import redirect_stdout
        from backend.main import log_structured

        buf = io.StringIO()
        with redirect_stdout(buf):
            log_structured("INFO", "test_event", correlation_id="op_id_123", details={
                "masked_key": "***:***:abc",
                "forbidden_secret": "sk-proj-supersecret123",
                "raw_password": "supersecretpassword",
            })
        out = buf.getvalue().strip()
        data = json.loads(out)
        self.assertEqual(data["event"], "test_event")
        self.assertIn("masked_key", data["details"])
        self.assertNotIn("forbidden_secret", data["details"])
        self.assertNotIn("raw_password", data["details"])

if __name__ == "__main__":
    unittest.main()
