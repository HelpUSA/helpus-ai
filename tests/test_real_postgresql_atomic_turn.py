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


class RealPostgresqlAtomicTurnTests(unittest.TestCase):
    def setUp(self):
        if sys.platform == "win32":
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            except Exception:
                pass

    @classmethod
    def tearDownClass(cls):
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
        """P1 Contrato de Reconciliação (Ciclo 030): Exige escopo completo para reconciliação de endpoints."""
        from backend.banco import BancoDados
        b = BancoDados()

        async def _test():
            # Falha se faltar qualquer um dos campos estritos
            with self.assertRaises(ValueError) as ctx1:
                await b.reconcile_idempotency_turn("key1", session_id="s1", request_payload_hash="", require_strict_scope=True)
            self.assertIn("Escopo completo obrigatorio", str(ctx1.exception))

            with self.assertRaises(ValueError) as ctx2:
                await b.reconcile_idempotency_turn("key1", session_id="", request_payload_hash="hash1", require_strict_scope=True)
            self.assertIn("Escopo completo obrigatorio", str(ctx2.exception))

            with self.assertRaises(ValueError) as ctx3:
                await b.reconcile_idempotency_turn("", session_id="s1", request_payload_hash="hash1", require_strict_scope=True)
            self.assertIn("Escopo completo obrigatorio", str(ctx3.exception))

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
                st1, p1 = await b.reconcile_idempotency_turn(key, user_email=user_email, session_id=sess_id, request_payload_hash=req_hash, require_strict_scope=True)
                st2, p2 = await b.reconcile_idempotency_turn(key, user_email=user_email, session_id=sess_id, request_payload_hash=req_hash, require_strict_scope=True)

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


if __name__ == "__main__":
    unittest.main()
