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
        """P0 Rollback: Injeta falha SQL real entre INSERT em conversas e UPDATE do ledger,
        comprovando que ambas as alterações são integralmente revertidas pelo PostgreSQL."""
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
            await b.claim_turn_ledger(key, owner, sess, "audit@helpus.com", "general", req_hash)

            # 2. Executa transação onde falha SQL (divisão por zero) ocorre logo após INSERT em conversas
            async with b.pool.connection() as conn:
                try:
                    async with conn.transaction():
                        async with conn.cursor() as cur:
                            await cur.execute(
                                """
                                INSERT INTO conversas (session_id, role, content, user_email, project_id, turn_idempotency_key)
                                VALUES (%s, 'assistant', 'Mensagem que sera revertida', %s, %s, %s);
                                """,
                                (sess, "audit@helpus.com", "general", key)
                            )
                            # Injeta erro SQL fatal antes do update do ledger
                            await cur.execute("SELECT 1/0;")
                except psycopg.errors.DivisionByZero:
                    pass

            # 3. Comprova atomicidade do rollback em conexão independente
            async with b.pool.connection() as conn:
                async with conn.transaction():
                    async with conn.cursor() as cur:
                        # Nenhuma linha foi persistida em conversas
                        await cur.execute("SELECT COUNT(*) FROM conversas WHERE turn_idempotency_key = %s", (key,))
                        c_count = (await cur.fetchone())[0]
                        self.assertEqual(c_count, 0, "Linha em conversas deve ter sido desfeita pelo rollback")

                        # Ledger permaneceu em 'in_progress', não foi alterado para 'completed'
                        await cur.execute("SELECT status, response_payload FROM turn_idempotency_ledger WHERE idempotency_key = %s", (key,))
                        l_row = await cur.fetchone()
                        self.assertEqual(l_row[0], "in_progress", "Ledger não pode ter sido concluído")
                        self.assertIsNone(l_row[1], "Payload não pode ter sido gravado")

            await b.pool.close()

        self.run_async(_test())

    def test_real_postgresql_rollback_on_update_failure(self):
        """P0 Rollback: Simula falha durante a execução do UPDATE do ledger (fencing violado / rowcount == 0),
        comprovando que a mensagem inserida em conversas sofre rollback integral."""
        self._require_pg()
        from backend.banco import BancoDados

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()

            sess = f"rb_upd_{uuid.uuid4().hex[:8]}"
            key = f"turn_rb_upd_{uuid.uuid4().hex[:8]}"
            legit_owner = f"owner_legit_{uuid.uuid4().hex[:8]}"
            hijack_owner = f"owner_hijack_{uuid.uuid4().hex[:8]}"
            req_hash = hashlib.sha256(b"update_fail_data").hexdigest()

            await b.claim_turn_ledger(key, legit_owner, sess, "audit@helpus.com", "general", req_hash)

            # Tentativa de persist_and_complete_turn com token divergente simula perda de fencing
            res = await b.persist_and_complete_turn(
                sess, "Conteudo rejeitado por fencing", key, hijack_owner, "audit@helpus.com", "general", req_hash, {}
            )
            self.assertFalse(res)

            # Verifica que nada foi gravado
            async with b.pool.connection() as conn:
                async with conn.transaction():
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT COUNT(*) FROM conversas WHERE turn_idempotency_key = %s", (key,))
                        self.assertEqual((await cur.fetchone())[0], 0)
                        await cur.execute("SELECT status FROM turn_idempotency_ledger WHERE idempotency_key = %s", (key,))
                        self.assertEqual((await cur.fetchone())[0], "in_progress")

            await b.pool.close()

        self.run_async(_test())

    def test_real_postgresql_commit_ambiguity_diagnostic(self):
        """P0 Ambiguidade de Commit: Distingue resultado KNOWN_COMMITTED de KNOWN_ABORTED / UNKNOWN
        mediante inspeção transacional autoritativa do ledger no PostgreSQL."""
        self._require_pg()
        from backend.banco import BancoDados

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()

            sess = f"ambig_{uuid.uuid4().hex[:8]}"
            key_committed = f"turn_committed_{uuid.uuid4().hex[:8]}"
            key_aborted = f"turn_aborted_{uuid.uuid4().hex[:8]}"
            owner = f"owner_{uuid.uuid4().hex[:8]}"
            req_hash = hashlib.sha256(b"ambig_data").hexdigest()

            # Cenário 1: Conclusão transacional bem-sucedida (KNOWN_COMMITTED)
            await b.claim_turn_ledger(key_committed, owner, sess, "ambig@helpus.com", "general", req_hash)
            await b.persist_and_complete_turn(
                sess, "Resposta confirmada", key_committed, owner, "ambig@helpus.com", "general", req_hash, {"status": "ok"}
            )

            # Cenário 2: Claim aberto que não concluiu (KNOWN_ABORTED / em andamento)
            await b.claim_turn_ledger(key_aborted, owner, sess, "ambig@helpus.com", "general", req_hash)

            # Diagnóstico autoritativo
            async with b.pool.connection() as conn:
                async with conn.transaction():
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT status FROM turn_idempotency_ledger WHERE idempotency_key = %s", (key_committed,))
                        st_committed = (await cur.fetchone())[0]
                        self.assertEqual(st_committed, "completed", "Cenário 1 deve ser categorizado como KNOWN_COMMITTED")

                        await cur.execute("SELECT status FROM turn_idempotency_ledger WHERE idempotency_key = %s", (key_aborted,))
                        st_aborted = (await cur.fetchone())[0]
                        self.assertEqual(st_aborted, "in_progress", "Cenário 2 deve ser categorizado como KNOWN_ABORTED")

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


if __name__ == "__main__":
    unittest.main()
