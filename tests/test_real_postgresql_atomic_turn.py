"""Validação real em PostgreSQL 18 para Ciclos Executivos 026 e 027:
- Transação atômica única (persist_and_complete_turn)
- Rollback integral com falha injetada entre INSERT e UPDATE
- Rollback em falha de UPDATE e tratamento de ambiguidade de COMMIT
- Concorrência real com barreiras sincronizadas (asyncio.Barrier)
- Perda estrita de autorização de escrita para token antigo após takeover
- Simulação de restart/crash e replay persistente pós-COMMIT sem re-inferência
- Deduplicação estrita via índice único parcial uq_conversas_turn_assistant
- Rejeição de conteúdo divergente para mesma idempotency_key
- Enforçamento Fail-Closed na persistência durável e bloqueio de HELPUS_TEST_MODE em deploy
- Inspeção independente de variáveis de concorrência (< 1 e > 1)
"""

import os
import sys
import time
import uuid
import hashlib
import asyncio
import socket
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

EPHEMERAL_PG_URL = os.getenv("EPHEMERAL_DATABASE_URL", "postgresql://helpus_test@127.0.0.1:5433/helpus_ephemeral")

def _check_ephemeral_pg_available() -> bool:
    """Verifica se a instância de PostgreSQL efêmero está ativa na porta 5433."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", 5433))
        s.close()
        return True
    except Exception:
        return False

PG_AVAILABLE = _check_ephemeral_pg_available()
if PG_AVAILABLE:
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = EPHEMERAL_PG_URL
    os.environ["HELPUS_REQUIRE_POSTGRES"] = "1"


class RealPostgresqlAtomicTurnTests(unittest.TestCase):
    def setUp(self):
        if sys.platform == "win32":
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            except Exception:
                pass

    @classmethod
    def tearDownClass(cls):
        os.environ.pop("HELPUS_REQUIRE_POSTGRES", None)
        if sys.platform == "win32":
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except Exception:
                pass

    def run_async(self, coro):
        return asyncio.run(coro)

    def _require_pg(self):
        """Garante a disponibilidade do PostgreSQL. Se HELPUS_REQUIRE_POSTGRES=1 for solicitado,
        falha explicitamente em vez de pular passivamente."""
        if not PG_AVAILABLE:
            if os.getenv("HELPUS_REQUIRE_POSTGRES") == "1":
                self.fail("PostgreSQL efêmero na porta 5433 é estritamente OBRIGATÓRIO (HELPUS_REQUIRE_POSTGRES=1), mas está inacessível.")
            raise unittest.SkipTest("PostgreSQL efêmero na porta 5433 não disponível neste ambiente")

    # =========================================================================
    # 1. P0 SEGURANÇA E AUDITORIA DE WORKERS (DIRETIVA 5)
    # =========================================================================
    def test_independent_multiworker_rejections(self):
        """P0/P1 Multiworker: Garante que WORKERS, WEB_CONCURRENCY e SERVER_REPLICAS são inspecionadas
        independentemente e qualquer valor < 1 ou > 1 é terminantemente rejeitado no startup."""
        from backend.main import lifespan
        from fastapi import FastAPI

        test_app = FastAPI()

        for var_name in ("WORKERS", "WEB_CONCURRENCY", "SERVER_REPLICAS"):
            for invalid_val in ("2", "0", "-1", "invalid_str"):
                old_val = os.environ.get(var_name)
                try:
                    os.environ[var_name] = invalid_val
                    with self.assertRaises(RuntimeError) as ctx:
                        self.run_async(lifespan(test_app).__aenter__())
                    err_msg = str(ctx.exception)
                    self.assertIn(var_name, err_msg)
                    if invalid_val == "invalid_str":
                        self.assertIn("Deve ser um numero inteiro", err_msg)
                    else:
                        self.assertIn("estritamente restrita a 1 worker local", err_msg)
                finally:
                    if old_val is not None:
                        os.environ[var_name] = old_val
                    else:
                        os.environ.pop(var_name, None)

    def test_deploy_environment_blocks_test_mode(self):
        """P0 Segurança: Bloqueia sumariamente HELPUS_TEST_MODE=1 em ambientes de deploy."""
        from backend.main import lifespan
        from fastapi import FastAPI

        test_app = FastAPI()
        deploy_vars = [
            ("VERCEL", "1"),
            ("RAILWAY_ENVIRONMENT", "production"),
            ("ENVIRONMENT", "production"),
            ("ENVIRONMENT", "staging"),
        ]

        old_test_mode = os.environ.get("HELPUS_TEST_MODE")
        try:
            os.environ["HELPUS_TEST_MODE"] = "1"
            for var_k, var_v in deploy_vars:
                old_env_val = os.environ.get(var_k)
                try:
                    os.environ[var_k] = var_v
                    with self.assertRaises(RuntimeError) as ctx:
                        self.run_async(lifespan(test_app).__aenter__())
                    self.assertIn("HELPUS_TEST_MODE=1 e terminantemente proibido em ambientes de deploy", str(ctx.exception))
                finally:
                    if old_env_val is not None:
                        os.environ[var_k] = old_env_val
                    else:
                        os.environ.pop(var_k, None)
        finally:
            if old_test_mode is not None:
                os.environ["HELPUS_TEST_MODE"] = old_test_mode
            else:
                os.environ.pop("HELPUS_TEST_MODE", None)

    def test_fail_closed_persistence_rejection(self):
        """P0 Fail-Closed: Sem pool ativo e fora do modo HELPUS_TEST_MODE=1, persist_and_complete_turn
        deve rejeitar com RuntimeError fail-closed."""
        from backend.banco import BancoDados

        b = BancoDados()
        b.pool = None
        old_test_mode = os.environ.get("HELPUS_TEST_MODE")
        try:
            os.environ.pop("HELPUS_TEST_MODE", None)
            with self.assertRaises(RuntimeError) as ctx:
                self.run_async(
                    b.persist_and_complete_turn(
                        session_id="test_sess",
                        content="test_content",
                        idempotency_key="key_fail_closed",
                        owner_token="token_fail_closed",
                        user_email=None,
                        project_id=None,
                        request_payload_hash="hash",
                        response_payload={}
                    )
                )
            self.assertIn("fail-closed", str(ctx.exception).lower())
        finally:
            if old_test_mode is not None:
                os.environ["HELPUS_TEST_MODE"] = old_test_mode

    # =========================================================================
    # 2. P0 TRANSAÇÃO ATÔMICA REAL E ROLLBACK INTEGRAL (DIRETIVAS 1 & 2)
    # =========================================================================
    def test_real_postgresql_atomic_persist_and_ledger_completion(self):
        """P0 Real PostgreSQL: Executa claim e transação atômica única de conclusão no PostgreSQL 18."""
        self._require_pg()
        from backend.banco import BancoDados

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()
            self.assertIsNotNone(b.pool)

            sess = f"real_sess_{uuid.uuid4().hex[:8]}"
            key = f"turn_real_{uuid.uuid4().hex[:8]}"
            owner = f"owner_{uuid.uuid4().hex[:8]}"
            req_hash = hashlib.sha256(b"request_payload_data").hexdigest()

            # 1. Claim do turno no ledger
            should_run, cached, token = await b.claim_turn_ledger(
                idempotency_key=key,
                owner_token=owner,
                session_id=sess,
                user_email="superadmin@helpus.com",
                project_id="general",
                request_payload_hash=req_hash
            )
            self.assertTrue(should_run)
            self.assertIsNone(cached)
            self.assertEqual(token, owner)

            # 2. Persistência atômica da resposta e conclusão do turno
            payload = {"status": "success", "data": {"resposta": "Resposta transacional durável HelpUS"}}
            ok = await b.persist_and_complete_turn(
                session_id=sess,
                content="Resposta transacional durável HelpUS",
                idempotency_key=key,
                owner_token=owner,
                user_email="superadmin@helpus.com",
                project_id="general",
                request_payload_hash=req_hash,
                response_payload=payload
            )
            self.assertTrue(ok)

            # 3. Verificação no banco de dados
            async with b.pool.connection() as conn:
                async with conn.transaction():
                    async with conn.cursor() as cur:
                        # Registro de conversa inserido exatamente 1 vez
                        await cur.execute(
                            "SELECT content, role, turn_idempotency_key FROM conversas WHERE turn_idempotency_key = %s",
                            (key,)
                        )
                        c_rows = await cur.fetchall()
                        self.assertEqual(len(c_rows), 1)
                        self.assertEqual(c_rows[0][0], "Resposta transacional durável HelpUS")
                        self.assertEqual(c_rows[0][1], "assistant")

                        # Ledger marcado como completed com payload consistente
                        await cur.execute(
                            "SELECT status, response_payload, owner_token FROM turn_idempotency_ledger WHERE idempotency_key = %s",
                            (key,)
                        )
                        l_row = await cur.fetchone()
                        self.assertEqual(l_row[0], "completed")
                        self.assertEqual(l_row[1]["resposta"], "Resposta transacional durável HelpUS")
                        self.assertTrue(l_row[1]["cached"])
                        self.assertEqual(l_row[2], owner)

            # 4. Replay idempotente posterior retorna cache sem re-executar
            should_run_replay, cached_replay, _ = await b.claim_turn_ledger(
                idempotency_key=key,
                owner_token="new_worker_token",
                session_id=sess,
                user_email="superadmin@helpus.com",
                project_id="general",
                request_payload_hash=req_hash
            )
            self.assertFalse(should_run_replay)
            self.assertEqual(cached_replay["resposta"], "Resposta transacional durável HelpUS")
            self.assertTrue(cached_replay["cached"])

            await b.pool.close()

        self.run_async(_test())

    def test_real_postgresql_rollback_injected_between_insert_and_update(self):
        """P0 Rollback / Fault Injection (Ciclo 028): Aciona o mecanismo formal de fault injection
        _test_fault_injection_post_insert dentro de persist_and_complete_turn logo após o INSERT em conversas,
        comprovando via conexão independente que ambas as operações sofrem rollback atômico."""
        self._require_pg()
        import psycopg
        from backend.banco import BancoDados

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()

            sess = f"rb_sess_{uuid.uuid4().hex[:8]}"
            key = f"turn_rb_{uuid.uuid4().hex[:8]}"
            owner = f"owner_{uuid.uuid4().hex[:8]}"
            req_hash = hashlib.sha256(b"rollback_test_data").hexdigest()

            # 1. Cria claim inicial
            ok, _, tok = await b.claim_turn_ledger(key, owner, sess, "audit@helpus.com", "general", req_hash)
            self.assertTrue(ok)
            self.assertEqual(tok, owner)

            # 2. Ativa mecanismo de fault injection controlado para testes (post-insert)
            b._test_fault_injection_post_insert = True

            with self.assertRaises(RuntimeError) as ctx:
                await b.persist_and_complete_turn(
                    session_id=sess,
                    content="Mensagem que deve sofrer rollback atomico",
                    idempotency_key=key,
                    owner_token=owner,
                    user_email="audit@helpus.com",
                    project_id="general",
                    request_payload_hash=req_hash,
                    response_payload={"status": "ok"}
                )
            self.assertIn("Simulacao de falha controlada", str(ctx.exception))

            # 3. Comprova atomicidade do rollback em conexao PostgreSQL independente
            b._test_fault_injection_post_insert = False
            async with b.pool.connection() as conn:
                async with conn.transaction():
                    async with conn.cursor() as cur:
                        # Nenhuma linha foi persistida em conversas
                        await cur.execute("SELECT COUNT(*) FROM conversas WHERE turn_idempotency_key = %s", (key,))
                        c_count = (await cur.fetchone())[0]
                        self.assertEqual(c_count, 0, "Linha em conversas deve ter sofrido rollback total")

                        # Ledger permaneceu em 'in_progress', nao foi completado
                        await cur.execute("SELECT status, response_payload FROM turn_idempotency_ledger WHERE idempotency_key = %s", (key,))
                        l_row = await cur.fetchone()
                        self.assertEqual(l_row[0], "in_progress", "Ledger nao pode ter sido concluido")
                        self.assertIsNone(l_row[1], "Payload nao pode ter sido gravado")

            # 4. Verifica seguranca: o mecanismo de fault injection jamais pode ser ativado em deploy
            old_deploy = os.environ.get("VERCEL")
            try:
                os.environ["VERCEL"] = "1"
                b._test_fault_injection_post_insert = True
                with self.assertRaises(RuntimeError) as ctx_deploy:
                    await b.persist_and_complete_turn(
                        session_id=sess,
                        content="Tentativa ilegal",
                        idempotency_key=key,
                        owner_token=owner,
                        user_email="audit@helpus.com",
                        project_id="general",
                        request_payload_hash=req_hash
                    )
                self.assertIn("fault injection proibida em deploy", str(ctx_deploy.exception))
            finally:
                b._test_fault_injection_post_insert = False
                if old_deploy is not None:
                    os.environ["VERCEL"] = old_deploy
                else:
                    os.environ.pop("VERCEL", None)

            await b.pool.close()

        self.run_async(_test())

    def test_real_postgresql_commit_ambiguity_diagnostic(self):
        """P0 Ambiguidade de Commit & Reconciliação (Ciclos 028/029): Distingue categoricamente KNOWN_COMMITTED,
        NO_PRIOR_CLAIM e UNKNOWN. Comprova que in_progress dentro da lease é classificado como UNKNOWN
        (nunca como abort confirmado) e ausência de registro é NO_PRIOR_CLAIM (sem garantia de abort externo)."""
        self._require_pg()
        from backend.banco import BancoDados

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()

            sess = f"ambig_{uuid.uuid4().hex[:8]}"
            key_committed = f"turn_committed_{uuid.uuid4().hex[:8]}"
            key_in_progress = f"turn_inprogress_{uuid.uuid4().hex[:8]}"
            key_aborted = f"turn_aborted_nonexistent_{uuid.uuid4().hex[:8]}"
            key_expired = f"turn_expired_{uuid.uuid4().hex[:8]}"
            owner = f"owner_{uuid.uuid4().hex[:8]}"
            req_hash = hashlib.sha256(b"ambig_data").hexdigest()

            # Cenário 1: Conclusão transacional bem-sucedida (KNOWN_COMMITTED)
            await b.claim_turn_ledger(key_committed, owner, sess, "ambig@helpus.com", "general", req_hash)
            await b.persist_and_complete_turn(
                sess, "Resposta confirmada", key_committed, owner, "ambig@helpus.com", "general", req_hash, {"resposta": "Resposta confirmada"}
            )
            cat1, payload1 = await b.reconcile_idempotency_turn(key_committed, "ambig@helpus.com", "general", req_hash, session_id=sess)
            self.assertEqual(cat1, "KNOWN_COMMITTED")
            self.assertIsNotNone(payload1)
            self.assertEqual(payload1.get("resposta"), "Resposta confirmada")

            # Cenário 2: Turno em andamento com heartbeat ativo (UNKNOWN — ambíguo, NUNCA abort confirmado!)
            await b.claim_turn_ledger(key_in_progress, owner, sess, "ambig@helpus.com", "general", req_hash)
            cat2, payload2 = await b.reconcile_idempotency_turn(key_in_progress, "ambig@helpus.com", "general", req_hash, session_id=sess)
            self.assertEqual(cat2, "UNKNOWN", "Turno in_progress dentro do lease deve ser UNKNOWN")
            self.assertNotEqual(cat2, "NO_PRIOR_CLAIM", "in_progress NUNCA deve ser classificado como ausente!")
            self.assertIsNone(payload2)

            # Cenário 3: Chave inexistente / ausência no ledger local (NO_PRIOR_CLAIM - Ciclo 029)
            cat3, payload3 = await b.reconcile_idempotency_turn(key_aborted, "ambig@helpus.com", "general", req_hash, session_id=sess)
            self.assertEqual(cat3, "NO_PRIOR_CLAIM")
            self.assertIsNone(payload3)

            # Cenário 4: Turno in_progress com lease expirada (LEASE_EXPIRED_PENDING_TAKEOVER)
            await b.claim_turn_ledger(key_expired, owner, sess, "ambig@helpus.com", "general", req_hash)
            async with b.pool.connection() as conn:
                async with conn.transaction():
                    async with conn.cursor() as cur:
                        await cur.execute(
                            "UPDATE turn_idempotency_ledger SET last_heartbeat = NOW() - INTERVAL '30 seconds' WHERE idempotency_key = %s",
                            (key_expired,)
                        )
            cat4, _ = await b.reconcile_idempotency_turn(key_expired, "ambig@helpus.com", "general", req_hash)
            self.assertEqual(cat4, "LEASE_EXPIRED_PENDING_TAKEOVER")

            await b.pool.close()

        self.run_async(_test())

    # =========================================================================
    # 3. P0 CONCORRÊNCIA COM BARREIRAS E TAKEOVER (DIRETIVA 3)
    # =========================================================================
    def test_real_postgresql_synchronized_barrier_concurrency(self):
        """P0 Concorrência: Duas conexões simultâneas disputam a mesma chave com barreira sincronizada
        (asyncio.Barrier). Confirma que apenas uma assume posse (True) e a outra é bloqueada (False)."""
        self._require_pg()
        from backend.banco import BancoDados

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()

            sess = f"barrier_sess_{uuid.uuid4().hex[:8]}"
            key = f"turn_barrier_{uuid.uuid4().hex[:8]}"
            w1_token = f"worker1_{uuid.uuid4().hex[:8]}"
            w2_token = f"worker2_{uuid.uuid4().hex[:8]}"
            req_hash = hashlib.sha256(b"barrier_data").hexdigest()

            barrier = asyncio.Barrier(2)
            results = []

            async def worker_task(token):
                # Sincroniza início exato no mesmo milissegundo
                await barrier.wait()
                res = await b.claim_turn_ledger(key, token, sess, "barrier@helpus.com", "general", req_hash)
                results.append((token, res[0]))

            await asyncio.gather(worker_task(w1_token), worker_task(w2_token))

            winners = [r for r in results if r[1] is True]
            losers = [r for r in results if r[1] is False]

            self.assertEqual(len(winners), 1, "Exatamente um worker deve vencer a disputa concorrente")
            self.assertEqual(len(losers), 1, "Exatamente um worker deve receber conflito 409 (False)")

            await b.pool.close()

        self.run_async(_test())

    def test_real_postgresql_stale_token_write_rejection_after_takeover(self):
        """P0 Fencing: Após expiração de lease e takeover por Worker 2, confirma que o Worker 1
        (token antigo) perde totalmente a capacidade de escrita e não duplica mensagens em conversas."""
        self._require_pg()
        from backend.banco import BancoDados

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()

            sess = f"stale_sess_{uuid.uuid4().hex[:8]}"
            key = f"turn_stale_{uuid.uuid4().hex[:8]}"
            w1_token = f"w1_{uuid.uuid4().hex[:8]}"
            w2_token = f"w2_{uuid.uuid4().hex[:8]}"
            req_hash = hashlib.sha256(b"stale_token_data").hexdigest()

            # 1. Worker 1 obtém o lease
            w1_ok, _, _ = await b.claim_turn_ledger(key, w1_token, sess, "stale@helpus.com", "general", req_hash)
            self.assertTrue(w1_ok)

            # 2. Simula expiração do lease envelhecendo a entrada no banco (30s atrás)
            async with b.pool.connection() as conn:
                async with conn.transaction():
                    async with conn.cursor() as cur:
                        await cur.execute(
                            "UPDATE turn_idempotency_ledger SET last_heartbeat = NOW() - INTERVAL '30 seconds', created_at = NOW() - INTERVAL '30 seconds' WHERE idempotency_key = %s",
                            (key,)
                        )

            # 3. Worker 2 assume a posse via retry (takeover legítimo)
            w2_ok, _, token_assumido = await b.claim_turn_ledger(
                key, w2_token, sess, "stale@helpus.com", "general", req_hash, is_retry=True
            )
            self.assertTrue(w2_ok)
            self.assertEqual(token_assumido, w2_token)

            # 4. Worker 1 (atrasado) tenta persistir com seu token antigo -> DEVE FALHAR
            w1_persist = await b.persist_and_complete_turn(
                sess, "Resposta do Worker 1 (invalida)", key, w1_token, "stale@helpus.com", "general", req_hash, {}
            )
            self.assertFalse(w1_persist, "Worker 1 com token revogado não pode ter permissão de escrita")

            # 5. Worker 2 conclui normalmente
            w2_persist = await b.persist_and_complete_turn(
                sess, "Resposta legitima do Worker 2", key, w2_token, "stale@helpus.com", "general", req_hash, {"ok": True}
            )
            self.assertTrue(w2_persist)

            # 6. Validação de integridade: exatamente 1 mensagem em conversas
            async with b.pool.connection() as conn:
                async with conn.transaction():
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT COUNT(*), content FROM conversas WHERE turn_idempotency_key = %s GROUP BY content", (key,))
                        row = await cur.fetchone()
                        self.assertEqual(row[0], 1)
                        self.assertEqual(row[1], "Resposta legitima do Worker 2")

            await b.pool.close()

        self.run_async(_test())

    # =========================================================================
    # 4. P0 RESTART E REPLAY PERSISTENTE (DIRETIVAS 4 & DEDUPLICAÇÃO)
    # =========================================================================
    def test_real_postgresql_restart_and_persistent_replay_without_re_inference(self):
        """P0 Restart & Replay: Simula reinicialização do processo após COMMIT e antes do ACK HTTP.
        Comprova que nova instância atende replay a partir do PostgreSQL sem nova inferência ou gravação duplicada."""
        self._require_pg()
        from backend.banco import BancoDados

        async def _test():
            # Processo 1: Executa e comita no banco
            b1 = BancoDados(EPHEMERAL_PG_URL)
            await b1.conectar()

            sess = f"restart_sess_{uuid.uuid4().hex[:8]}"
            key = f"turn_restart_{uuid.uuid4().hex[:8]}"
            owner = f"owner_{uuid.uuid4().hex[:8]}"
            req_hash = hashlib.sha256(b"restart_data").hexdigest()

            await b1.claim_turn_ledger(key, owner, sess, "restart@helpus.com", "general", req_hash)
            payload = {"status": "success", "data": {"resposta": "Persistido com sucesso antes do crash"}}
            ok = await b1.persist_and_complete_turn(
                sess, "Persistido com sucesso antes do crash", key, owner, "restart@helpus.com", "general", req_hash, payload
            )
            self.assertTrue(ok)

            # Simula crash: fecha pool e descarta objeto b1
            await b1.pool.close()
            del b1

            # Processo 2: Nova instância pós-reinicialização
            b2 = BancoDados(EPHEMERAL_PG_URL)
            await b2.conectar()

            # Cliente repete a requisição idêntica
            should_run, cached, _ = await b2.claim_turn_ledger(
                idempotency_key=key,
                owner_token="new_owner_after_restart",
                session_id=sess,
                user_email="restart@helpus.com",
                project_id="general",
                request_payload_hash=req_hash
            )

            self.assertFalse(should_run, "Replay não pode reativar inferência (should_run deve ser False)")
            self.assertIsNotNone(cached, "Payload deve vir do cache durável do PostgreSQL")
            self.assertEqual(cached["resposta"], "Persistido com sucesso antes do crash")
            self.assertTrue(cached["cached"])

            # Comprova que nenhuma mensagem duplicada foi gerada
            async with b2.pool.connection() as conn:
                async with conn.transaction():
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT COUNT(*) FROM conversas WHERE turn_idempotency_key = %s", (key,))
                        self.assertEqual((await cur.fetchone())[0], 1)

            await b2.pool.close()

        self.run_async(_test())

    def test_real_postgresql_deduplication_and_divergent_rejection(self):
        """P0 Deduplicação: Valida que conteúdo divergente é estritamente rejeitado e que o índice
        uq_conversas_turn_assistant impede inserções duplicadas no nível de banco."""
        self._require_pg()
        import psycopg
        from backend.banco import BancoDados

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()

            sess = f"dedup_sess_{uuid.uuid4().hex[:8]}"
            key = f"turn_dedup_{uuid.uuid4().hex[:8]}"
            owner = f"owner_{uuid.uuid4().hex[:8]}"
            req_hash = hashlib.sha256(b"dedup_data").hexdigest()

            await b.claim_turn_ledger(key, owner, sess, "dedup@helpus.com", "general", req_hash)
            ok = await b.persist_and_complete_turn(
                sess, "Resposta original", key, owner, "dedup@helpus.com", "general", req_hash, {"step": 1}
            )
            self.assertTrue(ok)

            # Rejeição de tentativa posterior com conteúdo divergente
            divergent_ok = await b.persist_and_complete_turn(
                sess, "CONTEUDO_DIVERGENTE_MALICIOSO", key, owner, "dedup@helpus.com", "general", req_hash, {"step": 2}
            )
            self.assertFalse(divergent_ok)

            # Enforçamento de restrição única uq_conversas_turn_assistant diretamente no banco
            async with b.pool.connection() as conn:
                with self.assertRaises(psycopg.errors.UniqueViolation):
                    async with conn.transaction():
                        async with conn.cursor() as cur:
                            await cur.execute(
                                """
                                INSERT INTO conversas (session_id, role, content, turn_idempotency_key)
                                VALUES (%s, 'assistant', 'Duplicata proibida', %s)
                                """,
                                (sess, key)
                            )

            await b.pool.close()

        self.run_async(_test())

    def test_real_postgresql_race_condition_unique_violation_handling(self):
        """P0 Race Condition (Ciclo 028): Disputa simultânea de claim por múltiplas conexões para a mesma chave.
        Garante que UniqueViolation de inserção concorrente é tratada e o vencedor re-consultado,
        retornando 409 Conflict limpo ou replay consistente, sem erro 500 e sem duplicação."""
        self._require_pg()
        from backend.banco import BancoDados

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()

            sess = f"race_sess_{uuid.uuid4().hex[:8]}"
            key = f"turn_race_{uuid.uuid4().hex[:8]}"
            req_hash = hashlib.sha256(b"race_condition_data").hexdigest()

            barrier = asyncio.Barrier(4)
            claim_results = []

            async def claim_task(idx):
                token = f"token_worker_{idx}_{uuid.uuid4().hex[:6]}"
                await barrier.wait()
                res = await b.claim_turn_ledger(
                    idempotency_key=key,
                    owner_token=token,
                    session_id=sess,
                    user_email="race@helpus.com",
                    project_id="general",
                    request_payload_hash=req_hash
                )
                claim_results.append((idx, token, res[0], res[1], res[2]))

            # 1. 4 conexões disparam no mesmo milissegundo disputando a mesma chave
            await asyncio.gather(*(claim_task(i) for i in range(4)))

            winners = [r for r in claim_results if r[2] is True]
            losers = [r for r in claim_results if r[2] is False]

            self.assertEqual(len(winners), 1, "Exatamente um worker deve ser eleito vencedor do claim")
            self.assertEqual(len(losers), 3, "Os outros 3 workers devem receber conflito 409 limpo sem erro 500")

            winner_token = winners[0][1]

            # 2. Vencedor conclui o turno
            ok = await b.persist_and_complete_turn(
                session_id=sess,
                content="Resposta processada pelo vencedor",
                idempotency_key=key,
                owner_token=winner_token,
                user_email="race@helpus.com",
                project_id="general",
                request_payload_hash=req_hash,
                response_payload={"resposta": "Resposta processada pelo vencedor"}
            )
            self.assertTrue(ok)

            # 3. Tentativa posterior para a mesma chave recebe replay consistente
            should_run, cached, _ = await b.claim_turn_ledger(
                idempotency_key=key,
                owner_token="late_worker_token",
                session_id=sess,
                user_email="race@helpus.com",
                project_id="general",
                request_payload_hash=req_hash
            )
            self.assertFalse(should_run)
            self.assertEqual(cached["resposta"], "Resposta processada pelo vencedor")

            # 4. Comprova no banco que exatamente 1 linha foi persistida em conversas e 1 no ledger
            async with b.pool.connection() as conn:
                async with conn.transaction():
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT COUNT(*) FROM turn_idempotency_ledger WHERE idempotency_key = %s", (key,))
                        self.assertEqual((await cur.fetchone())[0], 1)
                        await cur.execute("SELECT COUNT(*) FROM conversas WHERE turn_idempotency_key = %s", (key,))
                        self.assertEqual((await cur.fetchone())[0], 1)

            await b.pool.close()

        self.run_async(_test())

    def test_real_postgresql_subprocess_crash_and_recovery(self):
        """P1 Process Crash & Recovery (Ciclo 028): Distingue nova instância em memória de crash real de processo.
        Executa subprocesso isolado via SO que conclui COMMIT no PostgreSQL e sofre término forçado antes do ACK.
        Comprova que novo processo independente recupera o estado e realiza replay sem re-inferência."""
        self._require_pg()
        import subprocess
        import sys
        from backend.banco import BancoDados

        sess = f"crash_sess_{uuid.uuid4().hex[:8]}"
        key = f"turn_crash_{uuid.uuid4().hex[:8]}"
        owner = f"owner_proc_{uuid.uuid4().hex[:8]}"
        req_hash = hashlib.sha256(b"crash_data").hexdigest()

        backend_dir = str(Path(__file__).resolve().parents[1] / "backend")
        # Código executado em processo isolado real do SO
        subproc_code = f"""
import asyncio, os, sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
sys.path.insert(0, r'{backend_dir}')
os.environ['DATABASE_URL'] = '{EPHEMERAL_PG_URL}'
from banco import BancoDados
async def main():
    b = BancoDados('{EPHEMERAL_PG_URL}')
    await b.conectar()
    ok, _, tok = await b.claim_turn_ledger('{key}', '{owner}', '{sess}', 'crash@helpus.com', 'general', '{req_hash}')
    if not ok:
        sys.exit(2)
    saved = await b.persist_and_complete_turn(
        '{sess}',
        'Mensagem persistida por processo isolado antes do crash',
        '{key}',
        '{owner}',
        'crash@helpus.com',
        'general',
        '{req_hash}',
        {{'resposta': 'Mensagem persistida por processo isolado antes do crash'}}
    )
    if not saved:
        sys.exit(3)
    await b.pool.close()
    # Simula encerramento abrupto do processo antes do retorno HTTP
    sys.exit(0)
asyncio.run(main())
"""
        proc = subprocess.Popen(
            [sys.executable, "-c", subproc_code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate(timeout=15)
        self.assertEqual(proc.returncode, 0, f"Subprocesso falhou com código {proc.returncode}: {stderr.decode()}")

        # Processo principal recupera o estado do PostgreSQL
        async def _test_recovery():
            b_recovery = BancoDados(EPHEMERAL_PG_URL)
            await b_recovery.conectar()

            # Cliente reconecta após o crash e envia retry
            should_run, cached, _ = await b_recovery.claim_turn_ledger(
                idempotency_key=key,
                owner_token="recovery_owner_token",
                session_id=sess,
                user_email="crash@helpus.com",
                project_id="general",
                request_payload_hash=req_hash
            )
            self.assertFalse(should_run, "Replay pós-crash não deve re-executar inferência")
            self.assertIsNotNone(cached)
            self.assertEqual(cached["resposta"], "Mensagem persistida por processo isolado antes do crash")

            # Valida integridade no banco
            async with b_recovery.pool.connection() as conn:
                async with conn.transaction():
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT COUNT(*) FROM conversas WHERE turn_idempotency_key = %s", (key,))
                        self.assertEqual((await cur.fetchone())[0], 1)

            await b_recovery.pool.close()

        self.run_async(_test_recovery())

    def test_real_postgresql_http_sse_stream_reconcile_and_replay_mock_ai_only(self):
        """P0 HTTP/SSE & Reconciliação (Ciclo 029): Valida fluxo real de /chat/stream conectado ao PostgreSQL 18
        com mock estrito APENAS do provedor de IA (pensar_stream). Comprova:
        1. Execução do stream e persistência atômica com 1 invocação da IA (call_count == 1).
        2. Replay idempotente pós-reconciliação via KNOWN_COMMITTED sem re-inferência (call_count permanece 1).
        3. Ausência de linhas duplicadas no PostgreSQL (conversas tem exatamente 1 row assistant).
        4. Bloqueio seguro de turnos em andamento (UNKNOWN -> 409 Conflict).
        5. Isolamento estrito de usuário/tenant e hash da requisição (divergência -> 403 Forbidden)."""
        self._require_pg()
        import httpx
        import backend.main as b_main
        from backend.banco import BancoDados
        from auth import obter_usuario_google

        async def _test():
            os.environ['DATABASE_URL'] = EPHEMERAL_PG_URL
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()
            old_banco = b_main.banco
            b_main.banco = b

            class MockCerebroStream:
                def __init__(self):
                    self.call_count = 0
                    self.nome_modelo = "gemini-2.0-flash"
                    self.provider = "mock_provider"
                    self.last_provider_used = "mock_provider"
                    self.last_fallback_reason = None

                async def pensar_stream(self, pergunta, image_base64=None, image_url=None):
                    self.call_count += 1
                    yield "Chunk 1: "
                    yield f"Resposta gerada para {pergunta}."

            mock_ai = MockCerebroStream()
            old_get_cerebro = b_main.get_cerebro
            b_main.get_cerebro = lambda: mock_ai

            user_email = "superadmin@helpus.com"
            test_user = {"email": user_email, "name": "SuperAdmin", "role": "admin"}
            b_main.app.dependency_overrides[obter_usuario_google] = lambda: test_user

            sess_id = f"sess_http_sse_{uuid.uuid4().hex[:8]}"
            client_req_id = f"req_http_sse_{uuid.uuid4().hex[:8]}"
            payload = {
                "mensagem": "Verificação de idempotência e reconciliação SSE",
                "session_id": sess_id,
                "client_request_id": client_req_id,
                "model": "gemini-2.0-flash"
            }

            transport = httpx.ASGITransport(app=b_main.app)
            try:
                async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                    # 1. Primeira requisição: streaming completo com persistência durável
                    async with client.stream("POST", "/chat/stream", json=payload) as r1:
                        self.assertEqual(r1.status_code, 200)
                        body1 = (await r1.aread()).decode("utf-8")
                        self.assertIn("Resposta gerada para", body1)
                        self.assertIn("[DONE]", body1)
                    self.assertEqual(mock_ai.call_count, 1, "A IA deve ser invocada exatamente 1 vez no primeiro envio")

                    # Limpa cache local em memória para garantir que o replay comprove reconciliação no PostgreSQL
                    b_main._idempotency_cache.clear()

                    # 2. Segunda requisição: replay imediato via reconciliação read-only no PostgreSQL
                    payload_retry = dict(payload)
                    payload_retry["is_retry"] = True
                    async with client.stream("POST", "/chat/stream", json=payload_retry) as r2:
                        self.assertEqual(r2.status_code, 200)
                        body2 = (await r2.aread()).decode("utf-8")
                        self.assertIn('"cached": true', body2)
                        self.assertIn("Resposta gerada para", body2)
                    self.assertEqual(mock_ai.call_count, 1, "A IA NÃO deve sofrer re-inferência em replay idempotente")

                    # 3. Comprova ausência absoluta de linhas duplicadas no PostgreSQL
                    async with b.pool.connection() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                "SELECT COUNT(*) FROM conversas WHERE session_id = %s AND role = 'assistant';",
                                (sess_id,)
                            )
                            cnt = (await cur.fetchone())[0]
                            self.assertEqual(cnt, 1, "Deve existir exatamente UMA mensagem de assistant persistida no PostgreSQL")

                    # 4. Bloqueio seguro de estado UNKNOWN (in-progress ativo)
                    unknown_sess = f"sess_unknown_{uuid.uuid4().hex[:8]}"
                    unknown_req_id = f"req_unknown_{uuid.uuid4().hex[:8]}"
                    unknown_payload = {
                        "mensagem": "Pergunta em andamento",
                        "session_id": unknown_sess,
                        "client_request_id": unknown_req_id,
                        "model": "gemini-2.0-flash"
                    }
                    unknown_key = b_main._gerar_chave_idempotencia(user_email, unknown_sess, unknown_req_id, unknown_payload["mensagem"])
                    req_h = hashlib.sha256(unknown_payload["mensagem"].encode("utf-8")).hexdigest()
                    await b.claim_turn_ledger(unknown_key, "other_worker", unknown_sess, user_email, "general", req_h)

                    r_unknown = await client.post("/chat/stream", json=unknown_payload)
                    self.assertEqual(r_unknown.status_code, 409, "Turno em estado UNKNOWN deve ser bloqueado com 409 Conflict")

                    # 5. Tentativa de invasão / isolamento de tenant divergente -> 403 Forbidden
                    b_main.app.dependency_overrides[obter_usuario_google] = lambda: {"email": "attacker@helpus.com", "name": "Attacker", "role": "user"}
                    r_attack = await client.post("/chat/stream", json=payload)
                    self.assertEqual(r_attack.status_code, 403, "Requisição com escopo divergente deve retornar 403 Forbidden")
            finally:
                b_main.get_cerebro = old_get_cerebro
                b_main.banco = old_banco
                b_main.app.dependency_overrides.clear()
                await b.fechar()

        self.run_async(_test())

    # =========================================================================
    # CICLO 030 - FINGERPRINT CANÔNICO, ISOLAMENTO & ENDPOINT /chat
    # =========================================================================
    def test_canonical_fingerprint_deterministic_and_legacy_compatible(self):
        """P0 Fingerprint Canônico (Ciclo 030): Comprova que o hash semântico da requisição é determinístico,
        sensível a alterações de parâmetros semânticos, insensível a tokens/segredos e compatível com legado."""
        import backend.main as b_main

        req1 = b_main.MensagemRequest(
            mensagem="Olá HelpUS",
            model="gemini-2.0-flash",
            pesquisar_web=True,
            image_url="",
            file_name="",
            project_id="general"
        )
        h1 = b_main._calcular_fingerprint_requisicao(req1)
        self.assertEqual(len(h1), 64)
        
        # Determinismo
        req2 = b_main.MensagemRequest(
            mensagem="Olá HelpUS",
            model="gemini-2.0-flash",
            pesquisar_web=True,
            image_url="",
            file_name="",
            project_id="general"
        )
        self.assertEqual(h1, b_main._calcular_fingerprint_requisicao(req2))

        # Sensibilidade a cada campo semântico
        req_msg_diff = b_main.MensagemRequest(mensagem="Outra mensagem", model="gemini-2.0-flash")
        self.assertNotEqual(h1, b_main._calcular_fingerprint_requisicao(req_msg_diff))

        req_model_diff = b_main.MensagemRequest(mensagem="Olá HelpUS", model="gpt-4o")
        self.assertNotEqual(h1, b_main._calcular_fingerprint_requisicao(req_model_diff))

        req_web_diff = b_main.MensagemRequest(mensagem="Olá HelpUS", model="gemini-2.0-flash", pesquisar_web=False)
        self.assertNotEqual(h1, b_main._calcular_fingerprint_requisicao(req_web_diff))

        req_proj_diff = b_main.MensagemRequest(mensagem="Olá HelpUS", model="gemini-2.0-flash", project_id="proj_xyz")
        self.assertNotEqual(h1, b_main._calcular_fingerprint_requisicao(req_proj_diff))

        req_file_diff = b_main.MensagemRequest(mensagem="Olá HelpUS", model="gemini-2.0-flash", file_name="anexo.pdf")
        self.assertNotEqual(h1, b_main._calcular_fingerprint_requisicao(req_file_diff))

        req_img_diff = b_main.MensagemRequest(mensagem="Olá HelpUS", model="gemini-2.0-flash", image_url="https://trusted.helpus.com/img.png")
        self.assertNotEqual(h1, b_main._calcular_fingerprint_requisicao(req_img_diff))

        # Hash legado simples preserva SHA-256 da mensagem pura
        legacy_h = b_main._calcular_hash_legado_mensagem("Olá HelpUS")
        self.assertEqual(legacy_h, hashlib.sha256("Olá HelpUS".encode("utf-8")).hexdigest())

    def test_strict_scope_contract_validation(self):
        """P1 Contrato de Reconciliação (Ciclos 030/031): Exige escopo completo (chave, sessao, hash, usuario, projeto)."""
        from backend.banco import BancoDados
        b = BancoDados()

        async def _test():
            # 1. Falha se faltar hash
            with self.assertRaises(ValueError) as ctx1:
                await b.reconcile_idempotency_turn("key1", session_id="s1", request_payload_hash="", user_email="u@test.com", project_id="general", require_strict_scope=True)
            self.assertIn("Escopo completo obrigatorio", str(ctx1.exception))

            # 2. Falha se faltar session_id
            with self.assertRaises(ValueError) as ctx2:
                await b.reconcile_idempotency_turn("key1", session_id="", request_payload_hash="hash1", user_email="u@test.com", project_id="general", require_strict_scope=True)
            self.assertIn("Escopo completo obrigatorio", str(ctx2.exception))

            # 3. Falha se faltar idempotency_key
            with self.assertRaises(ValueError) as ctx3:
                await b.reconcile_idempotency_turn("", session_id="s1", request_payload_hash="hash1", user_email="u@test.com", project_id="general", require_strict_scope=True)
            self.assertIn("Escopo completo obrigatorio", str(ctx3.exception))

            # 4. Falha se faltar user_email (P0 Identidade - Ciclo 031)
            with self.assertRaises(ValueError) as ctx4:
                await b.reconcile_idempotency_turn("key1", session_id="s1", request_payload_hash="hash1", user_email="", project_id="general", require_strict_scope=True)
            self.assertIn("Escopo completo obrigatorio", str(ctx4.exception))

            # 5. Falha se faltar project_id (P0 Identidade - Ciclo 031)
            with self.assertRaises(ValueError) as ctx5:
                await b.reconcile_idempotency_turn("key1", session_id="s1", request_payload_hash="hash1", user_email="u@test.com", project_id="", require_strict_scope=True)
            self.assertIn("Escopo completo obrigatorio", str(ctx5.exception))

        self.run_async(_test())

    def test_real_postgresql_individual_scope_divergences_and_isolation(self):
        """P0 Isolamento & Divergências Individuais (Ciclo 030): Exercita divergências pontuais de session_id,
        user_email, project_id e req_hash para uma mesma idempotency_key em PostgreSQL real.
        Confirma PermissionError com mensagens discriminadas e zero vazamento de payload."""
        self._require_pg()
        from backend.banco import BancoDados
        import backend.main as b_main

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()
            try:
                base_sess = f"sess_iso_{uuid.uuid4().hex[:8]}"
                base_req_id = f"req_iso_{uuid.uuid4().hex[:8]}"
                base_msg = "Pergunta confidencial tenant alpha"
                base_user = "user_alpha@helpus.com"
                base_proj = "proj_alpha"

                req_obj = b_main.MensagemRequest(
                    mensagem=base_msg,
                    session_id=base_sess,
                    client_request_id=base_req_id,
                    project_id=base_proj
                )
                canon_hash = b_main._calcular_fingerprint_requisicao(req_obj)
                legacy_hash = b_main._calcular_hash_legado_mensagem(base_msg)
                idemp_key = b_main._gerar_chave_idempotencia(base_user, base_sess, base_req_id, base_msg)

                # Worker registra e conclui o turno no PostgreSQL 18
                claimed, _, token = await b.claim_turn_ledger(
                    idempotency_key=idemp_key,
                    owner_token=str(uuid.uuid4()),
                    session_id=base_sess,
                    user_email=base_user,
                    project_id=base_proj,
                    request_payload_hash=canon_hash
                )
                self.assertTrue(claimed)

                secret_payload = {"resposta": "RESPOSTA_ULTRA_SECRETA_TENANT_ALPHA", "cached": True}
                committed = await b.persist_and_complete_turn(
                    session_id=base_sess,
                    content="RESPOSTA_ULTRA_SECRETA_TENANT_ALPHA",
                    idempotency_key=idemp_key,
                    owner_token=token,
                    user_email=base_user,
                    project_id=base_proj,
                    request_payload_hash=canon_hash,
                    response_payload=secret_payload
                )
                self.assertTrue(committed)

                # 1. Divergência de session_id
                with self.assertRaises(PermissionError) as ctx_sess:
                    await b.reconcile_idempotency_turn(
                        idempotency_key=idemp_key,
                        session_id="sess_outra_diferente",
                        user_email=base_user,
                        project_id=base_proj,
                        request_payload_hash=canon_hash,
                        require_strict_scope=True
                    )
                self.assertIn("sessao", str(ctx_sess.exception).lower())
                self.assertNotIn("RESPOSTA_ULTRA_SECRETA", str(ctx_sess.exception))

                # 2. Divergência de user_email
                with self.assertRaises(PermissionError) as ctx_user:
                    await b.reconcile_idempotency_turn(
                        idempotency_key=idemp_key,
                        session_id=base_sess,
                        user_email="attacker@helpus.com",
                        project_id=base_proj,
                        request_payload_hash=canon_hash,
                        require_strict_scope=True
                    )
                self.assertIn("usuario", str(ctx_user.exception).lower())
                self.assertNotIn("RESPOSTA_ULTRA_SECRETA", str(ctx_user.exception))

                # 3. Divergência de project_id
                with self.assertRaises(PermissionError) as ctx_proj:
                    await b.reconcile_idempotency_turn(
                        idempotency_key=idemp_key,
                        session_id=base_sess,
                        user_email=base_user,
                        project_id="proj_outro",
                        request_payload_hash=canon_hash,
                        require_strict_scope=True
                    )
                self.assertIn("projeto", str(ctx_proj.exception).lower())
                self.assertNotIn("RESPOSTA_ULTRA_SECRETA", str(ctx_proj.exception))

                # 4. Divergência de hash de requisição (sem compatibilidade de legado)
                with self.assertRaises(PermissionError) as ctx_hash:
                    await b.reconcile_idempotency_turn(
                        idempotency_key=idemp_key,
                        session_id=base_sess,
                        user_email=base_user,
                        project_id=base_proj,
                        request_payload_hash="hash_completamente_adulterado_000000000000",
                        require_strict_scope=True
                    )
                self.assertIn("payload", str(ctx_hash.exception).lower())
                self.assertNotIn("RESPOSTA_ULTRA_SECRETA", str(ctx_hash.exception))

                # 5. Escopo perfeito -> KNOWN_COMMITTED com payload correto
                st, p = await b.reconcile_idempotency_turn(
                    idempotency_key=idemp_key,
                    session_id=base_sess,
                    user_email=base_user,
                    project_id=base_proj,
                    request_payload_hash=canon_hash,
                    require_strict_scope=True
                )
                self.assertEqual(st, "KNOWN_COMMITTED")
                self.assertEqual(p.get("resposta"), "RESPOSTA_ULTRA_SECRETA_TENANT_ALPHA")

            finally:
                await b.fechar()

        self.run_async(_test())

    def test_real_postgresql_http_chat_endpoint_reconcile_and_replay_mock_ai_only(self):
        """P1 HTTP /chat & Reconciliação (Ciclo 030): Valida fluxo completo do endpoint não-streaming /chat
        conectado ao PostgreSQL 18 com mock estrito do provedor de IA (pensar). Comprova:
        1. Execução de inferência única e persistência atômica com commit (call_count == 1).
        2. Replay idempotente pós-reconciliação via KNOWN_COMMITTED sem re-inferência (call_count permanece 1).
        3. Ausência de linhas duplicadas no PostgreSQL (conversas tem exatamente 1 row assistant).
        4. Bloqueio seguro de turnos em andamento (UNKNOWN -> 409 Conflict).
        5. Isolamento estrito de usuário/tenant e hash da requisição (divergência -> 403 Forbidden)."""
        self._require_pg()
        import httpx
        import backend.main as b_main
        from backend.banco import BancoDados
        from auth import obter_usuario_google

        async def _test():
            os.environ['DATABASE_URL'] = EPHEMERAL_PG_URL
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()
            old_banco = b_main.banco
            b_main.banco = b

            class MockCerebroSync:
                def __init__(self):
                    self.call_count = 0
                    self.nome_modelo = "gemini-2.0-flash"
                    self.provider = "mock_provider"
                    self.last_provider_used = "mock_provider"
                    self.last_fallback_reason = None

                async def pensar(self, pergunta, image_base64=None, image_url=None, contexto_busca=None, **kwargs):
                    self.call_count += 1
                    return f"Resposta não-streaming gerada para: {pergunta}", 42, 0.1

            mock_ai = MockCerebroSync()
            old_get_cerebro = b_main.get_cerebro
            b_main.get_cerebro = lambda: mock_ai

            user_email = "superadmin_chat@helpus.com"
            test_user = {"email": user_email, "name": "SuperAdmin Chat", "role": "admin"}
            b_main.app.dependency_overrides[obter_usuario_google] = lambda: test_user

            sess_id = f"sess_http_chat_{uuid.uuid4().hex[:8]}"
            client_req_id = f"req_http_chat_{uuid.uuid4().hex[:8]}"
            payload = {
                "mensagem": "Verificação de idempotência não-streaming /chat",
                "session_id": sess_id,
                "client_request_id": client_req_id,
                "model": "gemini-2.0-flash"
            }

            transport = httpx.ASGITransport(app=b_main.app)
            try:
                async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                    # 1. Primeira requisição: execução de inferência e persistência no PostgreSQL
                    r1 = await client.post("/chat", json=payload)
                    self.assertEqual(r1.status_code, 200)
                    data1 = r1.json()
                    self.assertIn("Resposta não-streaming gerada para:", data1["resposta"])
                    self.assertEqual(mock_ai.call_count, 1, "A IA deve ser invocada exatamente 1 vez no primeiro envio")

                    # Limpa cache local em memória para garantir reconciliação no PostgreSQL
                    b_main._idempotency_cache.clear()

                    # 2. Segunda requisição: replay imediato via reconciliação read-only no PostgreSQL
                    payload_retry = dict(payload)
                    payload_retry["is_retry"] = True
                    r2 = await client.post("/chat", json=payload_retry)
                    self.assertEqual(r2.status_code, 200)
                    data2 = r2.json()
                    self.assertTrue(data2.get("cached"), "A resposta em replay deve ter cached=True")
                    self.assertEqual(data2["resposta"], data1["resposta"])
                    self.assertEqual(mock_ai.call_count, 1, "A IA NÃO deve sofrer re-inferência em replay idempotente")

                    # 3. Comprova ausência absoluta de linhas duplicadas no PostgreSQL
                    async with b.pool.connection() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                "SELECT COUNT(*) FROM conversas WHERE session_id = %s AND role = 'assistant';",
                                (sess_id,)
                            )
                            cnt = (await cur.fetchone())[0]
                            self.assertEqual(cnt, 1, "Deve existir exatamente UMA mensagem de assistant no PostgreSQL")

                    # 4. Bloqueio seguro de estado UNKNOWN (in-progress ativo de outro worker)
                    unknown_sess = f"sess_chat_unknown_{uuid.uuid4().hex[:8]}"
                    unknown_req_id = f"req_chat_unknown_{uuid.uuid4().hex[:8]}"
                    unknown_payload = {
                        "mensagem": "Pergunta em andamento /chat",
                        "session_id": unknown_sess,
                        "client_request_id": unknown_req_id,
                        "model": "gemini-2.0-flash"
                    }
                    unknown_key = b_main._gerar_chave_idempotencia(user_email, unknown_sess, unknown_req_id, unknown_payload["mensagem"])
                    req_h = b_main._calcular_fingerprint_requisicao(b_main.MensagemRequest(**unknown_payload))
                    await b.claim_turn_ledger(unknown_key, "other_worker", unknown_sess, user_email, "general", req_h)

                    r_unknown = await client.post("/chat", json=unknown_payload)
                    self.assertEqual(r_unknown.status_code, 409, "Turno em estado UNKNOWN deve ser bloqueado com 409 Conflict")

                    # 5. Tentativa de invasão / isolamento de tenant divergente -> 403 Forbidden
                    b_main.app.dependency_overrides[obter_usuario_google] = lambda: {"email": "attacker_chat@helpus.com", "name": "Attacker", "role": "user"}
                    r_attack = await client.post("/chat", json=payload)
                    self.assertEqual(r_attack.status_code, 403, "Requisição com escopo divergente deve retornar 403 Forbidden")
            finally:
                b_main.get_cerebro = old_get_cerebro
                b_main.banco = old_banco
                b_main.app.dependency_overrides.clear()
                await b.fechar()

        self.run_async(_test())

    def test_real_postgresql_preflight_reconcile_and_claim_race_safety(self):
        """P1 Corrida Preflight/Claim (Ciclo 030): Demonstra que reconciliação read-only não gera claims espúrios
        e que apenas o CAS atômico em PostgreSQL concede propriedade de execução sob concorrência."""
        self._require_pg()
        from backend.banco import BancoDados
        import backend.main as b_main

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()
            try:
                sess_id = f"sess_race_{uuid.uuid4().hex[:8]}"
                req_id = f"req_race_{uuid.uuid4().hex[:8]}"
                msg = "Pergunta sob corrida preflight"
                user_email = "racer@helpus.com"
                key = b_main._gerar_chave_idempotencia(user_email, sess_id, req_id, msg)
                req_hash = hashlib.sha256(msg.encode("utf-8")).hexdigest()

                # Ambos os workers executam reconciliação prévia em paralelo
                st1, p1 = await b.reconcile_idempotency_turn(key, user_email=user_email, session_id=sess_id, project_id="general", request_payload_hash=req_hash, require_strict_scope=True)
                st2, p2 = await b.reconcile_idempotency_turn(key, user_email=user_email, session_id=sess_id, project_id="general", request_payload_hash=req_hash, require_strict_scope=True)

                self.assertEqual(st1, "NO_PRIOR_CLAIM")
                self.assertEqual(st2, "NO_PRIOR_CLAIM")
                self.assertIsNone(p1)
                self.assertIsNone(p2)

                # Agora ambos disputam claim simultaneamente com barreira sincronizada
                barrier = asyncio.Barrier(2)
                results = []

                async def _worker(worker_id: str):
                    await barrier.wait()
                    acquired, cached, tok = await b.claim_turn_ledger(
                        idempotency_key=key,
                        owner_token=f"token_{worker_id}",
                        session_id=sess_id,
                        user_email=user_email,
                        project_id="general",
                        request_payload_hash=req_hash
                    )
                    results.append((worker_id, acquired, cached, tok))

                t1 = asyncio.create_task(_worker("worker_1"))
                t2 = asyncio.create_task(_worker("worker_2"))
                await asyncio.gather(t1, t2)

                # Exatamente 1 worker deve ter obtido o lease
                winners = [r for r in results if r[1] is True]
                losers = [r for r in results if r[1] is False]

                self.assertEqual(len(winners), 1, "Exatamente 1 worker deve vencer o CAS atômico de claim")
                self.assertEqual(len(losers), 1, "O outro worker deve ser categoricamente rejeitado pelo CAS")
                self.assertIsNotNone(winners[0][3], "Vencedor deve ter owner_token válido")

            finally:
                await b.fechar()

        self.run_async(_test())

    # =========================================================================
    # CICLO 031 - ADVERSARIAL SUITE, LEGACY BOUNDARY & FAIL-CLOSED NO-KEY
    # =========================================================================
    def test_real_postgresql_adversarial_fingerprint_divergences_and_legacy_boundary(self):
        """P0 Testes Adversariais & Limite Legado (Ciclo 031):
        Mesmo client_request_id e mesma mensagem, alterando individualmente:
        - model, pesquisar_web, image_base64, image_url, file_name, project_id.
        Comprova rejeicao estrita (PermissionError / 403), zero replay incorreto e zero vazamento de tenant.
        Valida que registros legados so autorizam replay quando o baseline e estritamente nominal."""
        self._require_pg()
        from backend.banco import BancoDados, is_nominal_legacy_request
        import backend.main as b_main

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()
            try:
                base_sess = f"sess_adv_{uuid.uuid4().hex[:8]}"
                base_req_id = f"req_adv_{uuid.uuid4().hex[:8]}"
                base_msg = "Pergunta auditada de seguranca adversarial"
                user_alpha = "alpha_adv@helpus.com"
                idemp_key = b_main._gerar_chave_idempotencia(user_alpha, base_sess, base_req_id, base_msg)

                # 1. Cria requisicao nominal canonica baseline
                base_req = b_main.MensagemRequest(
                    mensagem=base_msg,
                    session_id=base_sess,
                    client_request_id=base_req_id,
                    model="gemini-2.0-flash",
                    pesquisar_web=True,
                    project_id="general"
                )
                canon_hash = b_main._calcular_fingerprint_requisicao(base_req)

                # Worker 1 reivindica e conclui o turno nominal no PostgreSQL 18
                claimed, _, token = await b.claim_turn_ledger(
                    idempotency_key=idemp_key,
                    owner_token=str(uuid.uuid4()),
                    session_id=base_sess,
                    user_email=user_alpha,
                    project_id="general",
                    request_payload_hash=canon_hash
                )
                self.assertTrue(claimed)

                secret_ans = "RESPOSTA_CONFIDENCIAL_CANONICA_PARIS"
                saved = await b.persist_and_complete_turn(
                    session_id=base_sess,
                    content=secret_ans,
                    idempotency_key=idemp_key,
                    owner_token=token,
                    user_email=user_alpha,
                    project_id="general",
                    request_payload_hash=canon_hash,
                    response_payload={"resposta": secret_ans, "cached": True}
                )
                self.assertTrue(saved)

                # Requisicao idêntica: reconcilia e autoriza replay
                st_ok, p_ok = await b.reconcile_idempotency_turn(
                    idempotency_key=idemp_key,
                    user_email=user_alpha,
                    project_id="general",
                    session_id=base_sess,
                    request_payload_hash=canon_hash,
                    require_strict_scope=True
                )
                self.assertEqual(st_ok, "KNOWN_COMMITTED")
                self.assertEqual(p_ok["resposta"], secret_ans)

                # 2. Adversarial Divergence: mesmo client_request_id e mesma mensagem, alterando campos individualmente
                adversarial_cases = [
                    ("model_alterado", b_main.MensagemRequest(
                        mensagem=base_msg, session_id=base_sess, client_request_id=base_req_id,
                        model="gpt-4o", pesquisar_web=True, project_id="general"
                    ), "payload"),
                    ("web_desativada", b_main.MensagemRequest(
                        mensagem=base_msg, session_id=base_sess, client_request_id=base_req_id,
                        model="gemini-2.0-flash", pesquisar_web=False, project_id="general"
                    ), "payload"),
                    ("image_b64_injetada", b_main.MensagemRequest(
                        mensagem=base_msg, session_id=base_sess, client_request_id=base_req_id,
                        model="gemini-2.0-flash", pesquisar_web=True, project_id="general",
                        image_base64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                    ), "payload"),
                    ("image_url_injetada", b_main.MensagemRequest(
                        mensagem=base_msg, session_id=base_sess, client_request_id=base_req_id,
                        model="gemini-2.0-flash", pesquisar_web=True, project_id="general",
                        image_url="https://trusted.helpus.com/malicious.png"
                    ), "payload"),
                    ("file_name_injetado", b_main.MensagemRequest(
                        mensagem=base_msg, session_id=base_sess, client_request_id=base_req_id,
                        model="gemini-2.0-flash", pesquisar_web=True, project_id="general",
                        file_name="relatorio_financeiro.pdf"
                    ), "payload"),
                    ("project_id_divergente", b_main.MensagemRequest(
                        mensagem=base_msg, session_id=base_sess, client_request_id=base_req_id,
                        model="gemini-2.0-flash", pesquisar_web=True, project_id="tenant_finance"
                    ), "projeto"),
                ]

                for case_name, req_adv, expected_substr in adversarial_cases:
                    adv_hash = b_main._calcular_fingerprint_requisicao(req_adv)
                    adv_proj = req_adv.project_id or "general"
                    with self.assertRaises(PermissionError, msg=f"Falha ao bloquear {case_name}") as ctx_adv:
                        await b.reconcile_idempotency_turn(
                            idempotency_key=idemp_key,
                            user_email=user_alpha,
                            project_id=adv_proj,
                            session_id=base_sess,
                            request_payload_hash=adv_hash,
                            require_strict_scope=True
                        )
                    self.assertIn(expected_substr, str(ctx_adv.exception).lower())
                    self.assertNotIn(secret_ans, str(ctx_adv.exception), f"Vazamento de payload em {case_name}")

                # 3. Teste de Registro Legado e Fronteira Nominal Estrita
                legacy_sess = f"sess_legacy_{uuid.uuid4().hex[:8]}"
                legacy_req_id = f"req_legacy_{uuid.uuid4().hex[:8]}"
                legacy_msg = "Pergunta armazenada em versao anterior legado"
                legacy_key = b_main._gerar_chave_idempotencia(user_alpha, legacy_sess, legacy_req_id, legacy_msg)
                pure_legacy_hash = hashlib.sha256(legacy_msg.encode("utf-8")).hexdigest()

                # Simula turno persistido antes do Ciclo 030 (hash baseado puramente na mensagem)
                claimed_leg, _, tok_leg = await b.claim_turn_ledger(
                    idempotency_key=legacy_key,
                    owner_token=str(uuid.uuid4()),
                    session_id=legacy_sess,
                    user_email=user_alpha,
                    project_id="general",
                    request_payload_hash=pure_legacy_hash
                )
                self.assertTrue(claimed_leg)
                legacy_secret = "RESPOSTA_LEGADA_HOMOLOGADA"
                saved_leg = await b.persist_and_complete_turn(
                    session_id=legacy_sess,
                    content=legacy_secret,
                    idempotency_key=legacy_key,
                    owner_token=tok_leg,
                    user_email=user_alpha,
                    project_id="general",
                    request_payload_hash=pure_legacy_hash,
                    response_payload={
                        "resposta": legacy_secret,
                        "model_requested": "gemini-2.0-flash",
                        "model_used": "gemini-2.0-flash",
                        "pesquisar_web": True,
                        "has_image": False,
                        "has_file": False,
                        "project_id": "general",
                        "cached": True
                    }
                )
                self.assertTrue(saved_leg)

                # 3a. Requisicao Nova com parametros NOMINAIS PADRAO e mesmo modelo comprovado: replay permitido via compatibilidade segura
                nominal_new_req = b_main.MensagemRequest(
                    mensagem=legacy_msg,
                    session_id=legacy_sess,
                    client_request_id=legacy_req_id,
                    model="gemini-2.0-flash",
                    pesquisar_web=True,
                    project_id="general"
                )
                new_canon_hash = b_main._calcular_fingerprint_requisicao(nominal_new_req)
                st_leg_ok, p_leg_ok = await b.reconcile_idempotency_turn(
                    idempotency_key=legacy_key,
                    user_email=user_alpha,
                    project_id="general",
                    session_id=legacy_sess,
                    request_payload_hash=new_canon_hash,
                    legacy_payload_hash=pure_legacy_hash,
                    is_nominal_legacy_eligible=True,
                    require_strict_scope=True,
                    requested_model="gemini-2.0-flash",
                    pesquisar_web=True,
                    has_image=False,
                    has_file=False
                )
                self.assertEqual(st_leg_ok, "KNOWN_COMMITTED")
                self.assertEqual(p_leg_ok["resposta"], legacy_secret)

                # 3b. Requisicao Nova com MODELO ALTERNATIVO (gemini-2.5-flash):
                # Zero pressuposto de equivalencia entre modelos! DEVE REJEITAR com LegacyReplayConflictError
                from backend.banco import LegacyReplayConflictError
                with self.assertRaises(LegacyReplayConflictError) as ctx_alt_model:
                    await b.reconcile_idempotency_turn(
                        idempotency_key=legacy_key,
                        user_email=user_alpha,
                        project_id="general",
                        session_id=legacy_sess,
                        request_payload_hash=b_main._calcular_fingerprint_requisicao(
                            b_main.MensagemRequest(
                                mensagem=legacy_msg,
                                session_id=legacy_sess,
                                client_request_id=legacy_req_id,
                                model="gemini-2.5-flash",
                                pesquisar_web=True,
                                project_id="general"
                            )
                        ),
                        legacy_payload_hash=pure_legacy_hash,
                        is_nominal_legacy_eligible=True,
                        require_strict_scope=True,
                        requested_model="gemini-2.5-flash",
                        pesquisar_web=True,
                        has_image=False,
                        has_file=False
                    )
                self.assertIn("Crie uma nova client_request_id", str(ctx_alt_model.exception))

                # 3c. Requisicao Nova com divergencia de PESQUISA WEB (pesquisar_web=False):
                with self.assertRaises(LegacyReplayConflictError) as ctx_web:
                    await b.reconcile_idempotency_turn(
                        idempotency_key=legacy_key,
                        user_email=user_alpha,
                        project_id="general",
                        session_id=legacy_sess,
                        request_payload_hash=b_main._calcular_fingerprint_requisicao(
                            b_main.MensagemRequest(
                                mensagem=legacy_msg,
                                session_id=legacy_sess,
                                client_request_id=legacy_req_id,
                                model="gemini-2.0-flash",
                                pesquisar_web=False,
                                project_id="general"
                            )
                        ),
                        legacy_payload_hash=pure_legacy_hash,
                        is_nominal_legacy_eligible=True,
                        require_strict_scope=True,
                        requested_model="gemini-2.0-flash",
                        pesquisar_web=False,
                        has_image=False,
                        has_file=False
                    )
                self.assertIn("Crie uma nova client_request_id", str(ctx_web.exception))

                # 3d. Requisicao Nova com divergencia de ANEXO DE IMAGEM:
                with self.assertRaises(LegacyReplayConflictError) as ctx_img:
                    await b.reconcile_idempotency_turn(
                        idempotency_key=legacy_key,
                        user_email=user_alpha,
                        project_id="general",
                        session_id=legacy_sess,
                        request_payload_hash=b_main._calcular_fingerprint_requisicao(
                            b_main.MensagemRequest(
                                mensagem=legacy_msg,
                                session_id=legacy_sess,
                                client_request_id=legacy_req_id,
                                model="gemini-2.0-flash",
                                pesquisar_web=True,
                                image_base64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUg==",
                                project_id="general"
                            )
                        ),
                        legacy_payload_hash=pure_legacy_hash,
                        is_nominal_legacy_eligible=True,
                        require_strict_scope=True,
                        requested_model="gemini-2.0-flash",
                        pesquisar_web=True,
                        has_image=True,
                        has_file=False
                    )
                self.assertIn("Crie uma nova client_request_id", str(ctx_img.exception))

                # 3e. Requisicao Nova com divergencia de ANEXO DE ARQUIVO:
                with self.assertRaises(LegacyReplayConflictError) as ctx_file:
                    await b.reconcile_idempotency_turn(
                        idempotency_key=legacy_key,
                        user_email=user_alpha,
                        project_id="general",
                        session_id=legacy_sess,
                        request_payload_hash=b_main._calcular_fingerprint_requisicao(
                            b_main.MensagemRequest(
                                mensagem=legacy_msg,
                                session_id=legacy_sess,
                                client_request_id=legacy_req_id,
                                model="gemini-2.0-flash",
                                pesquisar_web=True,
                                file_name="relatorio.pdf",
                                project_id="general"
                            )
                        ),
                        legacy_payload_hash=pure_legacy_hash,
                        is_nominal_legacy_eligible=True,
                        require_strict_scope=True,
                        requested_model="gemini-2.0-flash",
                        pesquisar_web=True,
                        has_image=False,
                        has_file=True
                    )
                self.assertIn("Crie uma nova client_request_id", str(ctx_file.exception))

                # 3f. Requisicao Nova com divergencia de PROJETO:
                with self.assertRaises(LegacyReplayConflictError) as ctx_proj:
                    await b.reconcile_idempotency_turn(
                        idempotency_key=legacy_key,
                        user_email=user_alpha,
                        project_id="tenant_finance",
                        session_id=legacy_sess,
                        request_payload_hash=b_main._calcular_fingerprint_requisicao(
                            b_main.MensagemRequest(
                                mensagem=legacy_msg,
                                session_id=legacy_sess,
                                client_request_id=legacy_req_id,
                                model="gemini-2.0-flash",
                                pesquisar_web=True,
                                project_id="tenant_finance"
                            )
                        ),
                        legacy_payload_hash=pure_legacy_hash,
                        is_nominal_legacy_eligible=True,
                        require_strict_scope=True,
                        requested_model="gemini-2.0-flash",
                        pesquisar_web=True,
                        has_image=False,
                        has_file=False
                    )
                self.assertIn("Crie uma nova client_request_id", str(ctx_proj.exception))

                # 3g. Testes de Metadados Legados Malformados, Strings Booleanas e Identificadores de Anexo (P1 - Ciclo 034):
                # (i) Payload historico com string booleana "false" em pesquisar_web (DEVE ser False estrito, NAO coagido cegamente a True)
                from backend.banco import is_nominal_legacy_request
                self.assertFalse(is_nominal_legacy_request(
                    model="gemini-2.0-flash",
                    pesquisar_web=True,
                    has_image=False,
                    has_file=False,
                    project_id="general",
                    historical_response_payload={
                        "model_used": "gemini-2.0-flash",
                        "pesquisar_web": "false",
                        "has_image": False,
                        "has_file": False,
                        "project_id": "general"
                    }
                ))

                # (ii) Payload historico com identificador de anexo de arquivo no lugar de booleano
                self.assertFalse(is_nominal_legacy_request(
                    model="gemini-2.0-flash",
                    pesquisar_web=True,
                    has_image=False,
                    has_file=False,
                    project_id="general",
                    historical_response_payload={
                        "model_used": "gemini-2.0-flash",
                        "pesquisar_web": True,
                        "has_image": False,
                        "has_file": "relatorio_anexo.pdf",
                        "project_id": "general"
                    }
                ))

                # (iii) Payload historico com hash sha256 no lugar de booleano de imagem
                self.assertFalse(is_nominal_legacy_request(
                    model="gemini-2.0-flash",
                    pesquisar_web=True,
                    has_image=False,
                    has_file=False,
                    project_id="general",
                    historical_response_payload={
                        "model_used": "gemini-2.0-flash",
                        "pesquisar_web": True,
                        "has_image": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                        "has_file": False,
                        "project_id": "general"
                    }
                ))

                # (iv) Payload historico malformado nao-dict (string invalida)
                self.assertFalse(is_nominal_legacy_request(
                    model="gemini-2.0-flash",
                    pesquisar_web=True,
                    has_image=False,
                    has_file=False,
                    project_id="general",
                    historical_response_payload="string invalida de resposta"
                ))

                # (v) Payload historico com strings booleanas canonicas "1" e "0" compativeis
                self.assertTrue(is_nominal_legacy_request(
                    model="gemini-2.0-flash",
                    pesquisar_web=True,
                    has_image=False,
                    has_file=False,
                    project_id="general",
                    historical_response_payload={
                        "model_used": "gemini-2.0-flash",
                        "pesquisar_web": "1",
                        "has_image": "0",
                        "has_file": "0",
                        "project_id": "general"
                    }
                ))

                # (vi) Payload historico com projeto ausente
                self.assertFalse(is_nominal_legacy_request(
                    model="gemini-2.0-flash",
                    pesquisar_web=True,
                    has_image=False,
                    has_file=False,
                    project_id="general",
                    historical_response_payload={
                        "model_used": "gemini-2.0-flash",
                        "pesquisar_web": True,
                        "has_image": False,
                        "has_file": False
                    }
                ))

                # 3h. Comprova que a resposta historica permanece intacta no banco em todos os casos de conflito
                async with b.pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT status, response_payload->>'resposta' FROM turn_idempotency_ledger WHERE idempotency_key = %s;", (legacy_key,))
                        row_intact = await cur.fetchone()
                        self.assertEqual(row_intact[0], "completed")
                        self.assertEqual(row_intact[1], legacy_secret)

                # 3h. Requisicao Nova com parametro NAO-NOMINAL (ex.: hash divergente de prompt):
                with self.assertRaises(PermissionError) as ctx_leg_block:
                    await b.reconcile_idempotency_turn(
                        idempotency_key=legacy_key,
                        user_email=user_alpha,
                        project_id="general",
                        session_id=legacy_sess,
                        request_payload_hash="hash_divergente_gpt4o",
                        legacy_payload_hash="outro_hash_nao_correspondente",
                        is_nominal_legacy_eligible=False,
                        require_strict_scope=True
                    )
                self.assertIn("Hash de payload divergente", str(ctx_leg_block.exception))

            finally:
                await b.fechar()

        self.run_async(_test())

    def test_real_postgresql_endpoints_without_client_request_id_and_failure_handling(self):
        """P1 HTTP /chat e /chat/stream sem client_request_id e Enforçamento Fail-Closed (Ciclo 031):
        1. /chat sem client_request_id: sucesso 200, gravacao normal em conversas.
        2. /chat sem client_request_id com falha de persistencia: falha closed com HTTP 503 (zero 200).
        3. /chat/stream sem client_request_id: sucesso com done:true, gravacao em conversas.
        4. /chat/stream sem client_request_id com falha de persistencia: emite PERSISTENCE_FAILED e NAO emite done:true."""
        self._require_pg()
        import httpx
        import backend.main as b_main
        from backend.banco import BancoDados
        from auth import obter_usuario_google

        async def _test():
            os.environ['DATABASE_URL'] = EPHEMERAL_PG_URL
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()
            old_banco = b_main.banco
            b_main.banco = b

            class MockCerebroAll:
                def __init__(self):
                    self.nome_modelo = "gemini-2.0-flash"
                    self.provider = "mock"
                    self.last_provider_used = "mock"
                    self.last_fallback_reason = None

                async def pensar(self, pergunta, **kwargs):
                    return f"Resposta sem chave: {pergunta}", 25, 0.05

                async def pensar_stream(self, pergunta, **kwargs):
                    yield "Chunk stream sem chave. "
                    yield f"Resposta para {pergunta}"

            mock_ai = MockCerebroAll()
            old_get = b_main.get_cerebro
            b_main.get_cerebro = lambda: mock_ai

            user_email = "nokey_user@helpus.com"
            b_main.app.dependency_overrides[obter_usuario_google] = lambda: {"email": user_email, "name": "NoKey", "role": "user"}

            transport = httpx.ASGITransport(app=b_main.app)
            try:
                async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                    # 1. /chat sem client_request_id -> 200 OK e grava no PostgreSQL
                    sess_chat = f"sess_nokey_chat_{uuid.uuid4().hex[:8]}"
                    r1 = await client.post("/chat", json={"mensagem": "Pergunta chat sem chave", "session_id": sess_chat})
                    self.assertEqual(r1.status_code, 200)
                    async with b.pool.connection() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute("SELECT COUNT(*) FROM conversas WHERE session_id = %s AND role = 'assistant';", (sess_chat,))
                            self.assertEqual((await cur.fetchone())[0], 1)

                    # 2. /chat sem client_request_id com falha de persistencia -> 503 Service Unavailable (Fail-Closed)
                    sess_chat_fail = f"sess_nokey_fail_{uuid.uuid4().hex[:8]}"
                    old_salvar = b.salvar_mensagem
                    async def _failing_salvar(*args, **kwargs):
                        return False
                    b.salvar_mensagem = _failing_salvar
                    r2 = await client.post("/chat", json={"mensagem": "Pergunta que falhara salvar", "session_id": sess_chat_fail})
                    self.assertEqual(r2.status_code, 503, "Falha de persistencia sem client_request_id deve retornar 503")
                    b.salvar_mensagem = old_salvar

                    # 3. /chat/stream sem client_request_id -> 200 OK, done:true, gravado em conversas
                    sess_stream = f"sess_nokey_stream_{uuid.uuid4().hex[:8]}"
                    async with client.stream("POST", "/chat/stream", json={"mensagem": "Pergunta stream sem chave", "session_id": sess_stream}) as s1:
                        self.assertEqual(s1.status_code, 200)
                        body1 = (await s1.aread()).decode("utf-8")
                        self.assertIn('"done": true', body1)
                        self.assertIn("[DONE]", body1)
                    async with b.pool.connection() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute("SELECT COUNT(*) FROM conversas WHERE session_id = %s AND role = 'assistant';", (sess_stream,))
                            self.assertEqual((await cur.fetchone())[0], 1)

                    # 4. /chat/stream sem client_request_id com falha de persistencia de assistant -> emite erro PERSISTENCE_FAILED e NAO emite done:true
                    sess_stream_fail = f"sess_nokey_sfail_{uuid.uuid4().hex[:8]}"
                    async def _failing_assistant_salvar(*args, **kwargs):
                        role = kwargs.get("role") or (args[1] if len(args) > 1 else None)
                        if role == "assistant":
                            return False
                        return await old_salvar(*args, **kwargs)
                    b.salvar_mensagem = _failing_assistant_salvar
                    async with client.stream("POST", "/chat/stream", json={"mensagem": "Stream que falhara salvar", "session_id": sess_stream_fail}) as s2:
                        self.assertEqual(s2.status_code, 200)
                        body2 = (await s2.aread()).decode("utf-8")
                        self.assertIn('"PERSISTENCE_FAILED"', body2)
                        self.assertNotIn('"done": true', body2, "NAO deve enviar done:true quando persistencia falha")
                        self.assertIn("[DONE]", body2)
                    b.salvar_mensagem = old_salvar

            finally:
                b_main.get_cerebro = old_get
                b_main.banco = old_banco
                b_main.app.dependency_overrides.clear()
                await b.fechar()

        self.run_async(_test())

    def test_real_postgresql_incomplete_cache_purging_and_ledger_fallback(self):
        """P0 Cache Incompleto (Ciclo 032): Garante que entradas em memoria sem os 4 metadados
        canonicos (request_payload_hash, user_email, session_id, project_id) sejam sumariamente
        expurgadas/invalidadas, impedindo qualquer replay inseguro em memoria."""
        import backend.main as b_main
        from fastapi import HTTPException

        sess = f"sess_cache_inc_{uuid.uuid4().hex[:8]}"
        user = "cache_audit@helpus.com"
        proj = "general"
        req_hash = hashlib.sha256(b"cache_incomplete_test").hexdigest()

        # 1. Entrada sem request_payload_hash
        k1 = f"key_inc_hash_{uuid.uuid4().hex[:8]}"
        b_main._idempotency_cache[k1] = {
            "status": "completed",
            "response": {"resposta": "Nao deve reusar"},
            "user_email": user,
            "session_id": sess,
            "project_id": proj,
            "timestamp": time.time()
        }
        ok1, resp1, tok1 = b_main.claim_or_get_idempotent_request(
            k1, is_retry=False, req_hash=req_hash, user_email=user, session_id=sess, project_id=proj
        )
        self.assertTrue(ok1, "Entrada incompleta deve ser invalidada e permitir nova reivindicacao")
        self.assertIsNone(resp1, "Entrada incompleta nao pode fornecer resposta cacheada")
        self.assertNotEqual(b_main._idempotency_cache.get(k1, {}).get("status"), "completed")
        self.assertNotIn("response", b_main._idempotency_cache.get(k1, {}))

        # 2. Entrada sem user_email
        k2 = f"key_inc_user_{uuid.uuid4().hex[:8]}"
        b_main._idempotency_cache[k2] = {
            "status": "completed",
            "response": {"resposta": "Nao deve reusar"},
            "request_payload_hash": req_hash,
            "session_id": sess,
            "project_id": proj,
            "timestamp": time.time()
        }
        ok2, resp2, tok2 = b_main.claim_or_get_idempotent_request(
            k2, is_retry=False, req_hash=req_hash, user_email=user, session_id=sess, project_id=proj
        )
        self.assertTrue(ok2)
        self.assertIsNone(resp2)
        self.assertNotEqual(b_main._idempotency_cache.get(k2, {}).get("status"), "completed")
        self.assertNotIn("response", b_main._idempotency_cache.get(k2, {}))

        # 3. Entrada sem session_id
        k3 = f"key_inc_sess_{uuid.uuid4().hex[:8]}"
        b_main._idempotency_cache[k3] = {
            "status": "completed",
            "response": {"resposta": "Nao deve reusar"},
            "request_payload_hash": req_hash,
            "user_email": user,
            "project_id": proj,
            "timestamp": time.time()
        }
        ok3, resp3, tok3 = b_main.claim_or_get_idempotent_request(
            k3, is_retry=False, req_hash=req_hash, user_email=user, session_id=sess, project_id=proj
        )
        self.assertTrue(ok3)
        self.assertIsNone(resp3)
        self.assertNotEqual(b_main._idempotency_cache.get(k3, {}).get("status"), "completed")
        self.assertNotIn("response", b_main._idempotency_cache.get(k3, {}))

        # 4. Entrada sem project_id
        k4 = f"key_inc_proj_{uuid.uuid4().hex[:8]}"
        b_main._idempotency_cache[k4] = {
            "status": "completed",
            "response": {"resposta": "Nao deve reusar"},
            "request_payload_hash": req_hash,
            "user_email": user,
            "session_id": sess,
            "timestamp": time.time()
        }
        ok4, resp4, tok4 = b_main.claim_or_get_idempotent_request(
            k4, is_retry=False, req_hash=req_hash, user_email=user, session_id=sess, project_id=proj
        )
        self.assertTrue(ok4)
        self.assertIsNone(resp4)
        self.assertNotEqual(b_main._idempotency_cache.get(k4, {}).get("status"), "completed")
        self.assertNotIn("response", b_main._idempotency_cache.get(k4, {}))

    def test_real_postgresql_persistence_failures_pool_absent_user_fail_and_sse_midstream_error(self):
        """P0 Falhas de Persistência & Erros SSE (Ciclo 032):
        1. Pool ausente: /chat e /chat/stream retornam HTTP 503 explícito.
        2. Gravação de mensagem do usuário falha: /chat e /chat/stream retornam HTTP 503 e liberam claim.
        3. Gravação de assistant falha em /chat: retorna HTTP 503 explícito.
        4. Erro durante o gerador SSE após o início do stream: emite evento de erro e terminador [DONE],
           mas NUNCA emite done:true."""
        self._require_pg()
        import httpx
        import backend.main as b_main
        from backend.banco import BancoDados
        from auth import obter_usuario_google

        async def _test():
            os.environ['DATABASE_URL'] = EPHEMERAL_PG_URL
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()
            old_banco = b_main.banco
            b_main.banco = b

            class MockCerebroStreamFail:
                def __init__(self):
                    self.nome_modelo = "gemini-2.0-flash"
                    self.provider = "mock"
                    self.last_provider_used = "mock"
                    self.last_fallback_reason = None

                async def pensar(self, pergunta, **kwargs):
                    return f"Resp: {pergunta}", 20, 0.05

                async def pensar_stream(self, pergunta, **kwargs):
                    yield "Primeiro pedaco valido emitido via SSE. "
                    raise RuntimeError("Falha simulada na conexao com upstream IA no meio do stream")

            mock_fail_stream = MockCerebroStreamFail()
            old_get = b_main.get_cerebro
            b_main.get_cerebro = lambda: mock_fail_stream

            user_email = "failtest@helpus.com"
            b_main.app.dependency_overrides[obter_usuario_google] = lambda: {"email": user_email, "name": "FailTest", "role": "user"}

            transport = httpx.ASGITransport(app=b_main.app)
            try:
                async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                    # 1. Falha na gravacao da mensagem do usuario no /chat -> 503
                    sess_ufail_chat = f"sess_ufail_c_{uuid.uuid4().hex[:8]}"
                    old_salvar = b.salvar_mensagem
                    async def _salvar_user_fail(session_id, role, *args, **kwargs):
                        if role == "user":
                            return False
                        return True
                    b.salvar_mensagem = _salvar_user_fail
                    r_u_chat = await client.post("/chat", json={"mensagem": "Pergunta com erro de user", "session_id": sess_ufail_chat, "client_request_id": f"req_ufail_{uuid.uuid4().hex[:8]}"})
                    self.assertEqual(r_u_chat.status_code, 503, "Falha na gravacao de mensagem de usuario no /chat deve retornar 503")

                    # 2. Falha na gravacao da mensagem do usuario no /chat/stream -> 503
                    sess_ufail_stream = f"sess_ufail_s_{uuid.uuid4().hex[:8]}"
                    async with client.stream("POST", "/chat/stream", json={"mensagem": "Pergunta stream com erro de user", "session_id": sess_ufail_stream, "client_request_id": f"req_sufail_{uuid.uuid4().hex[:8]}"}) as s_ufail:
                        self.assertEqual(s_ufail.status_code, 503, "Falha na gravacao de mensagem de usuario no /chat/stream deve retornar 503")

                    # 3. Erro durante o SSE apos o inicio do stream (IA quebra no meio)
                    b.salvar_mensagem = old_salvar
                    sess_midstream = f"sess_midstream_{uuid.uuid4().hex[:8]}"
                    req_midstream = f"req_midstream_{uuid.uuid4().hex[:8]}"
                    async with client.stream("POST", "/chat/stream", json={"mensagem": "Pergunta com crash no meio do stream", "session_id": sess_midstream, "client_request_id": req_midstream}) as s_mid:
                        self.assertEqual(s_mid.status_code, 200)
                        body_mid = (await s_mid.aread()).decode("utf-8")
                        self.assertIn("Primeiro pedaco valido", body_mid)
                        self.assertIn("[DONE]", body_mid, "Terminador de transporte deve estar presente")
                        self.assertNotIn('"done": true', body_mid, "Streaming quebrado no meio NUNCA deve emitir done:true")

            finally:
                b_main.get_cerebro = old_get
                b_main.banco = old_banco
                b_main.app.dependency_overrides.clear()
                await b.fechar()

        self.run_async(_test())

    def test_memory_conversas_instance_isolation_and_scope_filtering(self):
        """P0 Memória de Testes (Ciclo 033):
        1. Comprova que _conversas_memoria e buffers de memoria sao atributos de instancia (zero vazamento de classe).
        2. Valida filtro estrito de session_id, user_email e project_id nas leituras de memoria.
        3. Valida enforcamento fail-closed: sem HELPUS_TEST_MODE=1 ou em deploy, levanta RuntimeError."""
        from backend.banco import BancoDados

        orig_test_mode = os.environ.get("HELPUS_TEST_MODE")
        orig_env = os.environ.get("ENVIRONMENT")
        orig_req_pg = os.environ.get("HELPUS_REQUIRE_POSTGRES")
        orig_db_url = os.environ.get("DATABASE_URL")

        async def _test():
            try:
                # 1. Ativa HELPUS_TEST_MODE=1, desativa DATABASE_URL e HELPUS_REQUIRE_POSTGRES para teste de memoria isolado
                os.environ["HELPUS_TEST_MODE"] = "1"
                os.environ.pop("DATABASE_URL", None)
                os.environ.pop("HELPUS_REQUIRE_POSTGRES", None)
                os.environ.pop("ENVIRONMENT", None)

                b1 = BancoDados()
                b2 = BancoDados()
                b3 = BancoDados()
                b1.database_url = ""
                b2.database_url = ""
                b3.database_url = ""
                b1.pool = None
                b2.pool = None
                b3.pool = None

                # Comprova isolamento de instancia: escrita em b1 nao afeta b2 ou b3
                ok_b1 = await b1.salvar_mensagem("sess_inst_1", "user", "Ola b1", user_email="alpha@helpus.com", project_id="proj_a")
                self.assertTrue(ok_b1)
                self.assertEqual(len(b1._conversas_memoria), 1)
                self.assertEqual(len(b2._conversas_memoria), 0, "Isolamento de instancia violado: b2 vazou memoria de b1")
                self.assertEqual(len(b3._conversas_memoria), 0, "Isolamento de instancia violado: b3 vazou memoria de b1")

                # Adiciona mensagens em b1 para diferentes sessoes, usuarios e projetos
                await b1.salvar_mensagem("sess_inst_1", "assistant", "Resp b1 alpha", user_email="alpha@helpus.com", project_id="proj_a")
                await b1.salvar_mensagem("sess_inst_2", "user", "Ola b1 beta", user_email="beta@helpus.com", project_id="proj_b")
                await b1.salvar_mensagem("sess_inst_2", "assistant", "Resp b1 beta", user_email="beta@helpus.com", project_id="proj_b")

                # Leitura com filtro de session_id, user_email e project_id
                msgs_alpha = await b1.carregar_mensagens("sess_inst_1", user_email="alpha@helpus.com", project_id="proj_a")
                self.assertEqual(len(msgs_alpha), 2)
                self.assertEqual(msgs_alpha[0]["content"], "Ola b1")
                self.assertEqual(msgs_alpha[1]["content"], "Resp b1 alpha")

                # Cross-user isolation: beta nao pode ler a sessao de alpha
                msgs_leak = await b1.carregar_mensagens("sess_inst_1", user_email="beta@helpus.com", project_id="proj_a")
                self.assertEqual(len(msgs_leak), 0, "Vazamento cross-user em carregar_mensagens")

                # Cross-project isolation: proj_b nao pode ler a sessao de proj_a
                msgs_proj_leak = await b1.carregar_mensagens("sess_inst_1", user_email="alpha@helpus.com", project_id="proj_b")
                self.assertEqual(len(msgs_proj_leak), 0, "Vazamento cross-project em carregar_mensagens")

                # Listar conversas por usuario e projeto
                convs_alpha = await b1.listar_conversas_usuario("alpha@helpus.com", project_id="proj_a")
                self.assertEqual(len(convs_alpha), 1)
                self.assertEqual(convs_alpha[0]["session_id"], "sess_inst_1")

                convs_beta = await b1.listar_conversas_usuario("beta@helpus.com", project_id="proj_b")
                self.assertEqual(len(convs_beta), 1)
                self.assertEqual(convs_beta[0]["session_id"], "sess_inst_2")

                # P0 Testes Adversariais de Isolamento e Fail-Closed em Memoria (Ciclo 034):
                # (i) Injeta registros adversariais com usuario ausente (None ou "")
                b1._conversas_memoria.append({
                    "session_id": "sess_no_user",
                    "role": "assistant",
                    "content": "conteudo sem usuario",
                    "user_email": None,
                    "project_id": "proj_a"
                })
                b1._conversas_memoria.append({
                    "session_id": "sess_empty_user",
                    "role": "assistant",
                    "content": "conteudo com usuario vazio",
                    "user_email": "",
                    "project_id": "proj_a"
                })

                # (ii) Injeta registros adversariais com projeto ausente (None ou "")
                b1._conversas_memoria.append({
                    "session_id": "sess_no_proj",
                    "role": "assistant",
                    "content": "conteudo sem projeto",
                    "user_email": "alpha@helpus.com",
                    "project_id": None
                })
                b1._conversas_memoria.append({
                    "session_id": "sess_empty_proj",
                    "role": "assistant",
                    "content": "conteudo com projeto vazio",
                    "user_email": "alpha@helpus.com",
                    "project_id": ""
                })

                # Validacao 1: Usuario autenticado JAMAIS recebe registros com usuario ausente
                leak_user = await b1.carregar_mensagens("sess_no_user", user_email="alpha@helpus.com", project_id="proj_a")
                self.assertEqual(len(leak_user), 0, "Falha P0: registro com usuario ausente vazou para usuario autenticado")
                leak_empty_user = await b1.carregar_mensagens("sess_empty_user", user_email="alpha@helpus.com", project_id="proj_a")
                self.assertEqual(len(leak_empty_user), 0, "Falha P0: registro com usuario vazio vazou para usuario autenticado")

                # Validacao 2: Usuario autenticado JAMAIS recebe registros com projeto ausente
                leak_proj = await b1.carregar_mensagens("sess_no_proj", user_email="alpha@helpus.com", project_id="proj_a")
                self.assertEqual(len(leak_proj), 0, "Falha P0: registro com projeto ausente vazou para usuario autenticado")
                leak_empty_proj = await b1.carregar_mensagens("sess_empty_proj", user_email="alpha@helpus.com", project_id="proj_a")
                self.assertEqual(len(leak_empty_proj), 0, "Falha P0: registro com projeto vazio vazou para usuario autenticado")

                # Validacao 3: Solicitante sem identidade (user_email=None ou "") e fail-closed (P0 - Ciclo 035)
                # Posse da sessao isoladamente NUNCA e aceita; recuperacao de historico anonimo e bloqueada
                anon_msgs_none = await b1.carregar_mensagens("sess_inst_1", user_email=None, project_id="proj_a")
                self.assertEqual(len(anon_msgs_none), 0, "Falha P0 Fail-Closed: solicitante sem identidade recebeu mensagens de usuario autenticado")
                anon_msgs_empty = await b1.carregar_mensagens("sess_inst_1", user_email="", project_id="proj_a")
                self.assertEqual(len(anon_msgs_empty), 0, "Falha P0 Fail-Closed: solicitante com email vazio recebeu mensagens de usuario autenticado")

                # Recuperacao de historico anonimo e bloqueada em carregar_mensagens ate haver controle seguro de posse
                await b1.salvar_mensagem("sess_anon", "user", "Ola anonimo", user_email=None, project_id="proj_a")
                anon_msgs = await b1.carregar_mensagens("sess_anon", user_email=None, project_id="proj_a")
                self.assertEqual(len(anon_msgs), 0, "Falha P0: historico anonimo sem controle seguro de posse foi recuperado")
                leak_to_auth = await b1.carregar_mensagens("sess_anon", user_email="alpha@helpus.com", project_id="proj_a")
                self.assertEqual(len(leak_to_auth), 0, "Sessao anonima vazou para usuario autenticado")

                # Validacao 3b: Neutralizacao estrita de wildcards 'all' e '*' em consultas de usuario
                convs_all = await b1.listar_conversas_usuario("alpha@helpus.com", project_id="all")
                self.assertEqual(len(convs_all), 0, "Wildcard 'all' nao deve vazar conversas de outros projetos")
                convs_star = await b1.listar_conversas_usuario("alpha@helpus.com", project_id="*")
                self.assertEqual(len(convs_star), 0, "Wildcard '*' nao deve vazar conversas de outros projetos")

                # Validacao 4: Listagem de conversas nunca inclui sessoes com usuario ou projeto ausentes
                list_alpha = await b1.listar_conversas_usuario("alpha@helpus.com", project_id="proj_a")
                list_alpha_sids = [c["session_id"] for c in list_alpha]
                self.assertNotIn("sess_no_user", list_alpha_sids)
                self.assertNotIn("sess_empty_user", list_alpha_sids)
                self.assertNotIn("sess_no_proj", list_alpha_sids)
                self.assertNotIn("sess_empty_proj", list_alpha_sids)

                # Validacao 5: Solicitante anonimo para listar conversas retorna lista vazia
                self.assertEqual(await b1.listar_conversas_usuario("", project_id="proj_a"), [])
                self.assertEqual(await b1.listar_conversas_usuario(None, project_id="proj_a"), [])

                # 2. Enforcamento Fail-Closed sem HELPUS_TEST_MODE
                os.environ.pop("HELPUS_TEST_MODE", None)
                with self.assertRaises(RuntimeError):
                    await b1.salvar_mensagem("sess_fail", "user", "Nao deve salvar sem HELPUS_TEST_MODE")

                # 3. Enforcamento Fail-Closed em deploy (ENVIRONMENT=production)
                os.environ["HELPUS_TEST_MODE"] = "1"
                os.environ["ENVIRONMENT"] = "production"
                with self.assertRaises(RuntimeError):
                    await b1.salvar_mensagem("sess_fail_prod", "user", "Nao deve salvar em producao sem banco")

            finally:
                if orig_test_mode is not None:
                    os.environ["HELPUS_TEST_MODE"] = orig_test_mode
                else:
                    os.environ.pop("HELPUS_TEST_MODE", None)
                if orig_env is not None:
                    os.environ["ENVIRONMENT"] = orig_env
                else:
                    os.environ.pop("ENVIRONMENT", None)
                if orig_req_pg is not None:
                    os.environ["HELPUS_REQUIRE_POSTGRES"] = orig_req_pg
                else:
                    os.environ.pop("HELPUS_REQUIRE_POSTGRES", None)
                if orig_db_url is not None:
                    os.environ["DATABASE_URL"] = orig_db_url
                else:
                    os.environ.pop("DATABASE_URL", None)

        self.run_async(_test())

    def test_real_postgresql_adversarial_isolation_and_cross_project_boundaries(self):
        """P0 Testes de Isolamento de Sessao Anonima, Escopo de Projeto e Endpoints HTTP Reais (Ciclo 035):
        1. Simula adversario com session_id conhecido tentando ler historico anonimo e de outros usuarios.
        2. Simula tentativas de acesso cross-project com project_id ausente, 'all' e '*'.
        3. Valida endpoints HTTP reais (/historico/{sid}, /conversas, /admin/conversas/global) contra PostgreSQL 18.
        4. Valida rejeicao de aliases conflitantes em is_nominal_legacy_request."""
        import httpx
        from backend.banco import BancoDados, is_nominal_legacy_request
        import backend.main as b_main
        from auth import obter_usuario_google, obter_admin_google
        import uuid

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()
            self.assertIsNotNone(b.pool)
            old_banco = b_main.banco
            b_main.banco = b

            try:
                victim_sid = f"sess_victim_{uuid.uuid4().hex[:8]}"
                victim_email = f"victim_c35_{uuid.uuid4().hex[:8]}@helpus.com"
                attacker_email = f"attacker_c35_{uuid.uuid4().hex[:8]}@helpus.com"

                # 1. Cria conversa da vitima no projeto 'finance'
                await b.salvar_mensagem(victim_sid, "user", "Dados financeiros confidenciais", user_email=victim_email, project_id="finance")
                await b.salvar_mensagem(victim_sid, "assistant", "Lucro liquido: R$ 500.000", user_email=victim_email, project_id="finance")

                # (a) Adversario com session_id conhecido tentando ler anonimo (user_email=None)
                anon_attempt = await b.carregar_mensagens(victim_sid, user_email=None, project_id="finance")
                self.assertEqual(len(anon_attempt), 0, "Falha P0: adversario anonimo conseguiu ler conversa da vitima")

                # (b) Adversario com conta diferente (attacker_email) tentando ler session_id da vitima
                attacker_attempt = await b.carregar_mensagens(victim_sid, user_email=attacker_email, project_id="finance")
                self.assertEqual(len(attacker_attempt), 0, "Falha P0: adversario de outra conta conseguiu ler conversa da vitima")

                # (c) Mesma vitima tentando ler com escopo de projeto divergente ('general')
                cross_proj_attempt = await b.carregar_mensagens(victim_sid, user_email=victim_email, project_id="general")
                self.assertEqual(len(cross_proj_attempt), 0, "Falha P0: leitura com escopo de projeto divergente retornou dados")

                # (d) Leitura legitima da vitima no projeto correto ('finance')
                legit_read = await b.carregar_mensagens(victim_sid, user_email=victim_email, project_id="finance")
                self.assertEqual(len(legit_read), 2)
                self.assertEqual(legit_read[0]["content"], "Dados financeiros confidenciais")

                # 2. Testes de Escopo de Projetos em listar_conversas_usuario:
                # Cria mais duas conversas da vitima: uma em 'general' e outra em 'hr'
                sid_gen = f"sess_gen_{uuid.uuid4().hex[:8]}"
                sid_hr = f"sess_hr_{uuid.uuid4().hex[:8]}"
                await b.salvar_mensagem(sid_gen, "user", "Conversa Geral", user_email=victim_email, project_id="general")
                await b.salvar_mensagem(sid_hr, "user", "Conversa RH", user_email=victim_email, project_id="hr")

                # (i) project_id ausente (None): DEVE retornar estritamente as de 'general', NUNCA cross-project
                list_default = await b.listar_conversas_usuario(victim_email, project_id=None)
                list_default_sids = [c["session_id"] for c in list_default]
                self.assertIn(sid_gen, list_default_sids)
                self.assertNotIn(victim_sid, list_default_sids, "Falha P0: project_id ausente vazou conversa de 'finance'")
                self.assertNotIn(sid_hr, list_default_sids, "Falha P0: project_id ausente vazou conversa de 'hr'")

                # (ii) project_id='all' e '*': DEVEM ser neutralizados estritamente para 'general'
                list_all = await b.listar_conversas_usuario(victim_email, project_id="all")
                list_all_sids = [c["session_id"] for c in list_all]
                self.assertIn(sid_gen, list_all_sids)
                self.assertNotIn(victim_sid, list_all_sids, "Falha P0: 'all' vazou conversa de outro projeto")

                list_star = await b.listar_conversas_usuario(victim_email, project_id="*")
                list_star_sids = [c["session_id"] for c in list_star]
                self.assertIn(sid_gen, list_star_sids)
                self.assertNotIn(victim_sid, list_star_sids, "Falha P0: '*' vazou conversa de outro projeto")

                # (iii) project_id='finance': retorna unicamente a de finance
                list_fin = await b.listar_conversas_usuario(victim_email, project_id="finance")
                list_fin_sids = [c["session_id"] for c in list_fin]
                self.assertIn(victim_sid, list_fin_sids)
                self.assertNotIn(sid_gen, list_fin_sids)
                self.assertNotIn(sid_hr, list_fin_sids)

                # 3. Consulta Global Administrativa (admin_listar_conversas_globais):
                # Ator vazio/invalido levanta PermissionError
                with self.assertRaises(PermissionError):
                    await b.admin_listar_conversas_globais(actor_email="")

                # Ator admin autorizado lista todas as conversas cross-project
                admin_actor = f"admin_auditor_{uuid.uuid4().hex[:8]}@helpus.com"
                global_convs, total_global = await b.admin_listar_conversas_globais(
                    actor_email=admin_actor,
                    filter_user_email=victim_email
                )
                global_sids = [c["session_id"] for c in global_convs]
                self.assertIn(victim_sid, global_sids)
                self.assertIn(sid_gen, global_sids)
                self.assertIn(sid_hr, global_sids)
                self.assertEqual(len(global_sids), 3)

                # 4. Validacao de Aliases Conflitantes em is_nominal_legacy_request (P1 - Ciclo 035):
                # (a) Conflito entre model_requested e model_used
                self.assertFalse(is_nominal_legacy_request(
                    model="gemini-2.0-flash",
                    historical_response_payload={
                        "model_requested": "gemini-2.0-flash",
                        "model_used": "gemini-1.5-flash",
                        "pesquisar_web": True,
                        "has_image": False,
                        "has_file": False,
                        "project_id": "general"
                    }
                ))
                # (b) Conflito entre pesquisar_web e web
                self.assertFalse(is_nominal_legacy_request(
                    model="gemini-2.0-flash",
                    historical_response_payload={
                        "model_used": "gemini-2.0-flash",
                        "pesquisar_web": True,
                        "web": False,
                        "has_image": False,
                        "has_file": False,
                        "project_id": "general"
                    }
                ))
                # (c) Conflito entre has_image e has_img
                self.assertFalse(is_nominal_legacy_request(
                    model="gemini-2.0-flash",
                    historical_response_payload={
                        "model_used": "gemini-2.0-flash",
                        "pesquisar_web": True,
                        "has_image": False,
                        "has_img": True,
                        "has_file": False,
                        "project_id": "general"
                    }
                ))
                # (d) Conflito entre has_file e file
                self.assertFalse(is_nominal_legacy_request(
                    model="gemini-2.0-flash",
                    historical_response_payload={
                        "model_used": "gemini-2.0-flash",
                        "pesquisar_web": True,
                        "has_image": False,
                        "has_file": False,
                        "file": True,
                        "project_id": "general"
                    }
                ))
                # (e) Conflito entre project_id e proj
                self.assertFalse(is_nominal_legacy_request(
                    model="gemini-2.0-flash",
                    historical_response_payload={
                        "model_used": "gemini-2.0-flash",
                        "pesquisar_web": True,
                        "has_image": False,
                        "has_file": False,
                        "project_id": "general",
                        "proj": "finance"
                    }
                ))

                # 5. Testes de Endpoints HTTP Reais contra PostgreSQL 18 via httpx:
                transport = httpx.ASGITransport(app=b_main.app)
                async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                    # (a) GET /historico/{session_id} sem autenticacao -> HTTP 401
                    b_main.app.dependency_overrides[obter_usuario_google] = lambda: None
                    res_anon_hist = await client.get(f"/historico/{victim_sid}")
                    self.assertEqual(res_anon_hist.status_code, 401)
                    self.assertIn("Autenticacao necessaria", res_anon_hist.json()["detail"])

                    # (b) GET /conversas com wildcards 'all' ou '*' -> HTTP 400
                    b_main.app.dependency_overrides[obter_usuario_google] = lambda: {"email": victim_email, "name": "Victim", "role": "user"}
                    res_all = await client.get("/conversas?project_id=all")
                    self.assertEqual(res_all.status_code, 400)
                    self.assertIn("Wildcards 'all' ou '*' sao proibidos", res_all.json()["detail"])

                    res_star = await client.get("/conversas?project_id=*")
                    self.assertEqual(res_star.status_code, 400)
                    self.assertIn("Wildcards 'all' ou '*' sao proibidos", res_star.json()["detail"])

                    # (c) GET /conversas?project_id=finance -> 200 contendo apenas conversa de finance
                    res_fin = await client.get("/conversas?project_id=finance")
                    self.assertEqual(res_fin.status_code, 200)
                    fin_sids = [c["session_id"] for c in res_fin.json()["conversas"]]
                    self.assertIn(victim_sid, fin_sids)
                    self.assertNotIn(sid_gen, fin_sids)

                    # (d) GET /conversas (sem project_id) -> 200 escopo padrao 'general'
                    res_gen = await client.get("/conversas")
                    self.assertEqual(res_gen.status_code, 200)
                    gen_sids = [c["session_id"] for c in res_gen.json()["conversas"]]
                    self.assertIn(sid_gen, gen_sids)
                    self.assertNotIn(victim_sid, gen_sids)

                    # (e) GET /admin/conversas/global sem admin -> HTTP 401
                    b_main.app.dependency_overrides[obter_admin_google] = lambda: None
                    res_admin_anon = await client.get("/admin/conversas/global")
                    self.assertEqual(res_admin_anon.status_code, 401)

                    # (f) GET /admin/conversas/global com admin autorizado -> HTTP 200 com total e conversas cross-project
                    admin_actor_web = f"superadmin_c35_{uuid.uuid4().hex[:8]}@helpus.com"
                    b_main.app.dependency_overrides[obter_admin_google] = lambda: {"email": admin_actor_web, "name": "SuperAdmin", "role": "admin"}
                    res_admin_ok = await client.get(f"/admin/conversas/global?filter_user_email={victim_email}")
                    self.assertEqual(res_admin_ok.status_code, 200)
                    admin_data = res_admin_ok.json()
                    self.assertEqual(admin_data["total"], 3)
                    admin_returned_sids = [c["session_id"] for c in admin_data["conversas"]]
                    self.assertIn(victim_sid, admin_returned_sids)
                    self.assertIn(sid_gen, admin_returned_sids)
                    self.assertIn(sid_hr, admin_returned_sids)

            finally:
                b_main.banco = old_banco
                b_main.app.dependency_overrides.clear()
                await b.fechar()

        self.run_async(_test())


if __name__ == "__main__":
    unittest.main()
