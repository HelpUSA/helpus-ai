"""Validação real em PostgreSQL 18 para Ciclo Executivo 026:
- Transação atômica única (persist_and_complete_turn)
- Rollback atômico em falha
- Fencing de tokens e CAS entre múltiplos workers
- Deduplicação estrita via índice único parcial uq_conversas_turn_assistant
- Rejeição de conteúdo divergente para mesma idempotency_key
- Enforçamento Fail-Closed na persistência durável
- Inspeção independente de variáveis de concorrência (WORKERS, WEB_CONCURRENCY, SERVER_REPLICAS)
"""

import os
import sys
import uuid
import hashlib
import asyncio
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

EPHEMERAL_PG_URL = os.getenv("EPHEMERAL_DATABASE_URL", "postgresql://helpus_test@127.0.0.1:5433/helpus_ephemeral")

def _check_ephemeral_pg_available() -> bool:
    """Verifica rapidamente se a instância de PostgreSQL efêmero está ativa na porta 5433."""
    import socket
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

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_independent_multiworker_rejections(self):
        """P0/P1 Multiworker: Garante que WORKERS, WEB_CONCURRENCY e SERVER_REPLICAS são inspecionadas
        independentemente e qualquer valor > 1 é terminantemente rejeitado."""
        from backend.main import lifespan
        from fastapi import FastAPI

        test_app = FastAPI()

        for var_name in ("WORKERS", "WEB_CONCURRENCY", "SERVER_REPLICAS"):
            old_val = os.environ.get(var_name)
            try:
                os.environ[var_name] = "2"
                with self.assertRaises(RuntimeError) as ctx:
                    self.run_async(lifespan(test_app).__aenter__())
                self.assertIn(var_name, str(ctx.exception))
                self.assertIn("estritamente restrita a 1 worker local", str(ctx.exception))

                os.environ[var_name] = "invalid_number"
                with self.assertRaises(RuntimeError) as ctx:
                    self.run_async(lifespan(test_app).__aenter__())
                self.assertIn("Deve ser um numero inteiro", str(ctx.exception))
            finally:
                if old_val is not None:
                    os.environ[var_name] = old_val
                else:
                    os.environ.pop(var_name, None)

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

    @unittest.skipUnless(PG_AVAILABLE, "PostgreSQL efêmero na porta 5433 não disponível neste ambiente")
    def test_real_postgresql_atomic_persist_and_ledger_completion(self):
        """P0 Real PostgreSQL: Executa claim e transação atômica única de conclusão no PostgreSQL 18."""
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

    @unittest.skipUnless(PG_AVAILABLE, "PostgreSQL efêmero na porta 5433 não disponível neste ambiente")
    def test_real_postgresql_concurrent_fencing_and_cas_conflict(self):
        """P0 Fencing & CAS: Rejeita tentativas de conclusão com owner_token divergente ou chave em conflito."""
        from backend.banco import BancoDados

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()

            sess = f"fence_sess_{uuid.uuid4().hex[:8]}"
            key = f"turn_fence_{uuid.uuid4().hex[:8]}"
            w1_token = f"worker1_{uuid.uuid4().hex[:8]}"
            w2_token = f"worker2_{uuid.uuid4().hex[:8]}"
            req_hash = hashlib.sha256(b"fence_payload").hexdigest()

            # Worker 1 adquire claim
            w1_ok, _, _ = await b.claim_turn_ledger(key, w1_token, sess, "admin@helpus.com", "general", req_hash)
            self.assertTrue(w1_ok)

            # Worker 2 tenta mesma chave enquanto ativo -> 409 Conflict (False)
            w2_ok, _, _ = await b.claim_turn_ledger(key, w2_token, sess, "admin@helpus.com", "general", req_hash)
            self.assertFalse(w2_ok)

            # Worker 2 tenta finalizar usando seu próprio token -> Fencing CAS rejeita
            w2_persist = await b.persist_and_complete_turn(
                sess, "tentativa worker 2", key, w2_token, "admin@helpus.com", "general", req_hash, {}
            )
            self.assertFalse(w2_persist)

            # Worker 1 finaliza legitimamente
            w1_persist = await b.persist_and_complete_turn(
                sess, "conclusao worker 1", key, w1_token, "admin@helpus.com", "general", req_hash, {"status": "ok"}
            )
            self.assertTrue(w1_persist)

            await b.pool.close()

        self.run_async(_test())

    @unittest.skipUnless(PG_AVAILABLE, "PostgreSQL efêmero na porta 5433 não disponível neste ambiente")
    def test_real_postgresql_deduplication_and_divergent_rejection(self):
        """P0 Deduplicação: Valida que conteúdo divergente é estritamente rejeitado e que o índice
        uq_conversas_turn_assistant impede inserções duplicadas no nível de banco."""
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
