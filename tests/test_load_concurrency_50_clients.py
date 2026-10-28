# -*- coding: utf-8 -*-
"""
HelpUS AI - Testes Complementares de Carga e Concorrencia (Ordem Executiva 044 / 057)
Validacao de 50+ Clientes Virtuais Simultaneos em PostgreSQL 18 Efemero Local com Provedor de IA Simulado.

Governanca e Seguranca Fail-Closed:
1. Ambiente 100% Local: Executa exclusivamente em PostgreSQL efemero local na porta 5433 (127.0.0.1).
2. Aborto Fail-Closed Imediato: Se qualquer URL de banco apontar para host remoto, staging ou porta diferente de 5433,
   o harness falha imediatamente antes de qualquer operacao.
3. Provedor de IA Simulado: MockCerebroLoad simula latencia de inferencia (5ms) sem custos ou chamadas a APIs pagas.
4. Restauracao Garantida (try/finally): Variaveis globais de ambiente (DATABASE_URL), dependencias do FastAPI
   e conexoes do pool sao rigorosamente restauradas apos os testes.
5. Escopo e Limitacoes do ASGITransport:
   O ASGITransport (httpx) executa in-process sobre o loop assincrono do FastAPI, exercitando roteamento,
   injecao de dependencias, serializacao JSON, middleware e transacoes ACID no PostgreSQL 18.
   Ele isola a camada de aplicacao e banco, nao incluindo overhead de rede fisica (TCP/TLS), balanceadores
   de borda (Cloudflare/Vercel) ou latencia externa de geracao de tokens do Gemini (TTFT 200-1200ms).
"""

import asyncio
import hashlib
import json
import os
import platform
import socket
import sys
import time
import unittest
import uuid
from urllib.parse import urlparse
from typing import Dict, List, Any

# Definicao canonica da URL efemera local
EPHEMERAL_PG_URL = os.getenv("EPHEMERAL_DATABASE_URL", "postgresql://helpus_test@127.0.0.1:5433/helpus_ephemeral")


def validate_ephemeral_pg_url(url: str):
    """
    Guarda fail-closed estrita: garante que o teste de carga execute exclusivamente
    em PostgreSQL efemero local isolado (127.0.0.1:5433 / helpus_ephemeral).
    Qualquer tentativa de apontar para staging, producao ou porta externa aborta a execucao.
    """
    parsed = urlparse(url)
    allowed_hosts = {"127.0.0.1", "localhost"}
    if parsed.hostname not in allowed_hosts:
        raise RuntimeError(
            f"VIOLACAO DE SEGURANCA: Host '{parsed.hostname}' nao permitido para testes de carga. "
            f"Apenas hosts locais sao autorizados (127.0.0.1, localhost)."
        )
    if parsed.port != 5433:
        raise RuntimeError(
            f"VIOLACAO DE SEGURANCA: Porta '{parsed.port}' invalida. "
            f"Testes de carga exigem porta efemera isolada 5433."
        )
    db_name = (parsed.path or "").lstrip("/")
    if "ephemeral" not in db_name and "test" not in db_name:
        raise RuntimeError(
            f"VIOLACAO DE SEGURANCA: Banco de dados '{db_name}' nao permitido. "
            f"Testes de carga exigem banco efemero/teste ('ephemeral' ou 'test')."
        )


# Validacao fail-closed imediata na carga do modulo
validate_ephemeral_pg_url(EPHEMERAL_PG_URL)

# Configuracao global imediata para garantir que imports usem a porta efemera 5433
_MODULE_ORIG_ENV_DB_URL = os.environ.get("DATABASE_URL")
os.environ["DATABASE_URL"] = EPHEMERAL_PG_URL
os.environ["HELPUS_REQUIRE_POSTGRES"] = "1"

# Ajuste de path para importacao do backend
ai_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ai_root not in sys.path:
    sys.path.insert(0, ai_root)
backend_dir = os.path.join(ai_root, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import backend.config as b_config
_MODULE_ORIG_CONFIG_DB_URL = getattr(b_config, "DATABASE_URL", None)
b_config.DATABASE_URL = EPHEMERAL_PG_URL


def check_ephemeral_pg_available() -> bool:
    """Verifica conectividade rapida com socket na porta efemera 5433."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", 5433))
        s.close()
        return True
    except Exception:
        return False


PG_AVAILABLE = check_ephemeral_pg_available()

from backend.banco import BancoDados, _log_db_error
import backend.main as b_main
from auth import obter_usuario_google


def compute_percentiles(latencies_ms: List[float]) -> Dict[str, float]:
    """Calcula distribuicao estatistica de latencias (p50, p95, p99, min, max, avg)."""
    if not latencies_ms:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "min": 0.0, "max": 0.0, "avg": 0.0}
    sorted_lats = sorted(latencies_ms)
    n = len(sorted_lats)

    def _pct(p: float) -> float:
        idx = int(round(p * (n - 1)))
        return round(sorted_lats[idx], 2)

    return {
        "p50": _pct(0.50),
        "p95": _pct(0.95),
        "p99": _pct(0.99),
        "min": round(sorted_lats[0], 2),
        "max": round(sorted_lats[-1], 2),
        "avg": round(sum(sorted_lats) / n, 2),
    }


async def pre_warm_pool_connections(b: BancoDados, target_conns: int = 10):
    """Pre-aquece o pool no Windows para evitar concorrencia de sockets TCP na inicializacao."""
    if not b.pool:
        return
    conns = []
    for _ in range(min(target_conns, 10)):
        try:
            c = await b.pool.getconn()
            conns.append(c)
        except Exception:
            break
    for c in conns:
        await b.pool.putconn(c)


class MockCerebroLoad:
    """Provedor de IA simulado deterministico com micro-delay realista de inferencia."""
    def __init__(self, delay_ms: float = 5.0):
        self.call_count = 0
        self.delay_ms = delay_ms
        self.nome_modelo = "gemini-2.0-flash"
        self.provider = "mock_ai_load"
        self.last_provider_used = "mock_ai_load"
        self.last_fallback_reason = None

    async def pensar(self, pergunta: str, image_base64=None, image_url=None, contexto_busca=None, **kwargs):
        self.call_count += 1
        if self.delay_ms > 0:
            await asyncio.sleep(self.delay_ms / 1000.0)
        return f"Resposta sintetica simulada para: {pergunta}", 45, 0.05


class LoadConcurrency50ClientsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Validacao fail-closed da URL antes de qualquer teste
        validate_ephemeral_pg_url(EPHEMERAL_PG_URL)
        os.environ["DATABASE_URL"] = EPHEMERAL_PG_URL
        b_config.DATABASE_URL = EPHEMERAL_PG_URL
        os.environ["HELPUS_REQUIRE_POSTGRES"] = "1"

    @classmethod
    def tearDownClass(cls):
        # Restauracao segura de variaveis globais
        try:
            if _MODULE_ORIG_ENV_DB_URL is not None:
                os.environ["DATABASE_URL"] = _MODULE_ORIG_ENV_DB_URL
            else:
                os.environ.pop("DATABASE_URL", None)

            if _MODULE_ORIG_CONFIG_DB_URL is not None:
                b_config.DATABASE_URL = _MODULE_ORIG_CONFIG_DB_URL

            os.environ.pop("HELPUS_REQUIRE_POSTGRES", None)
        finally:
            if sys.platform == "win32":
                try:
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                except Exception:
                    pass

    def setUp(self):
        if not PG_AVAILABLE:
            raise unittest.SkipTest("PostgreSQL efemero na porta 5433 indisponivel.")
        if sys.platform == "win32":
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            except Exception:
                pass

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_01_load_50_concurrent_clients_atomic_turn(self):
        """
        Cenario 1: 50 Clientes Virtuais Simultaneos executando turnos atomicos completos no PostgreSQL 18.
        - Sincronizacao estrita via asyncio.Barrier(50) garantindo disparo simultaneo no mesmo instante.
        - 50 usuarios distintos distribuidos em 5 projetos independentes (proj_load_0..proj_load_4).
        - Medicao de Throughput, Latencias (p50, p95, p99), Integridade do Ledger e Isolamento Cross-Project / Cross-User.
        - Limpeza garantida de recursos com try/finally.
        """
        NUM_CLIENTS = 50
        NUM_PROJECTS = 5
        run_id = uuid.uuid4().hex[:8]

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()
            self.assertIsNotNone(b.pool)
            await pre_warm_pool_connections(b)

            try:
                barrier = asyncio.Barrier(NUM_CLIENTS)

                async def virtual_client_worker(client_idx: int):
                    proj_id = f"proj_load_{run_id}_{client_idx % NUM_PROJECTS}"
                    user_email = f"load_client_{run_id}_{client_idx}@helpus.local"
                    sess_id = f"sess_load_{run_id}_{client_idx}_{uuid.uuid4().hex[:6]}"
                    turn_key = f"turn_load_{run_id}_{client_idx}_{uuid.uuid4().hex[:6]}"
                    owner = f"worker_load_{run_id}_{client_idx}"

                    canonical_body = json.dumps({"client": client_idx, "msg": f"Carga cliente {client_idx}"}, sort_keys=True)
                    payload_hash = hashlib.sha256(canonical_body.encode("utf-8")).hexdigest()

                    # Sincroniza todos os 50 clientes na barreira
                    await barrier.wait()

                    t0 = time.perf_counter()
                    try:
                        # 1. Claim do turno no ledger
                        should_run, cached, token = await b.claim_turn_ledger(
                            idempotency_key=turn_key,
                            owner_token=owner,
                            session_id=sess_id,
                            user_email=user_email,
                            project_id=proj_id,
                            request_payload_hash=payload_hash
                        )
                        if not should_run:
                            return {"client_idx": client_idx, "success": False, "error": "claim_rejected"}

                        # 2. Persistencia atomica da resposta e conclusao do turno
                        payload_resp = {"status": "success", "data": {"resposta": f"Resposta persistida para cliente {client_idx}"}}
                        ok = await b.persist_and_complete_turn(
                            session_id=sess_id,
                            content=f"Resposta persistida para cliente {client_idx}",
                            idempotency_key=turn_key,
                            owner_token=owner,
                            user_email=user_email,
                            project_id=proj_id,
                            request_payload_hash=payload_hash,
                            response_payload=payload_resp,
                            is_nominal_legacy_eligible=False
                        )
                        t1 = time.perf_counter()
                        lat_ms = (t1 - t0) * 1000.0
                        return {
                            "client_idx": client_idx,
                            "success": bool(ok),
                            "lat_ms": lat_ms,
                            "sess_id": sess_id,
                            "turn_key": turn_key,
                            "proj_id": proj_id,
                            "user_email": user_email
                        }
                    except Exception as exc:
                        t1 = time.perf_counter()
                        lat_ms = (t1 - t0) * 1000.0
                        return {
                            "client_idx": client_idx,
                            "success": False,
                            "lat_ms": lat_ms,
                            "error": str(exc)
                        }

                start_total = time.perf_counter()
                tasks = [virtual_client_worker(i) for i in range(NUM_CLIENTS)]
                raw_results = await asyncio.gather(*tasks)
                end_total = time.perf_counter()

                total_duration_s = end_total - start_total
                successful = [r for r in raw_results if r["success"]]
                failed = [r for r in raw_results if not r["success"]]
                latencies = [r["lat_ms"] for r in successful]

                pct = compute_percentiles(latencies)
                throughput = len(successful) / total_duration_s if total_duration_s > 0 else 0.0

                # Verificacoes de Integridade
                self.assertEqual(len(successful), NUM_CLIENTS, f"Falhas observadas: {failed}")
                self.assertEqual(len(failed), 0)

                # Verificacao no Banco: exatamente 50 turnos no ledger em estado 'completed' para esta execucao
                async with b.pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute("""
                            SELECT count(*), status 
                              FROM turn_idempotency_ledger 
                             WHERE idempotency_key LIKE %s
                             GROUP BY status
                        """, (f"turn_load_{run_id}_%",))
                        rows = await cur.fetchall()
                        ledger_counts = {r[1]: r[0] for r in rows}
                        self.assertEqual(ledger_counts.get("completed", 0), NUM_CLIENTS)

                # Verificacao Rigorosa de Isolamento Cross-Project e Cross-User
                for c_idx in range(min(NUM_CLIENTS, 10)):
                    user_email = f"load_client_{run_id}_{c_idx}@helpus.local"
                    target_proj = f"proj_load_{run_id}_{c_idx % NUM_PROJECTS}"
                    other_proj = f"proj_load_{run_id}_{(c_idx + 1) % NUM_PROJECTS}"

                    # 1. Usuario ve sua propria conversa no seu projeto
                    own_sessions = await b.listar_conversas_usuario(user_email=user_email, limite=10, project_id=target_proj)
                    self.assertEqual(len(own_sessions), 1)
                    self.assertEqual(own_sessions[0].get("project_id"), target_proj)

                    # 2. Usuario nao ve nada no projeto alheio (Isolamento Cross-Project estrito)
                    other_proj_sessions = await b.listar_conversas_usuario(user_email=user_email, limite=10, project_id=other_proj)
                    self.assertEqual(len(other_proj_sessions), 0)

                    # 3. Outro usuario nao ve nada nesta sessao ou projeto (Isolamento Cross-User estrito)
                    other_user = f"intruder_{c_idx}@helpus.local"
                    intruder_sessions = await b.listar_conversas_usuario(user_email=other_user, limite=10, project_id=target_proj)
                    self.assertEqual(len(intruder_sessions), 0)

                return {
                    "scenario": "Atomic Turn 50 Clients",
                    "clients": NUM_CLIENTS,
                    "total_duration_s": round(total_duration_s, 3),
                    "throughput_req_s": round(throughput, 1),
                    "percentiles_ms": pct,
                    "success_count": len(successful),
                    "failure_count": len(failed)
                }
            finally:
                await b.fechar()

        report = self.run_async(_test())
        print(f"\n[LOAD TEST 01 RESULT] {json.dumps(report, indent=2)}")

    def test_02_concurrent_race_idempotency_deduplication(self):
        """
        Cenario 2: 10 pares (20 clientes) colidindo simultaneamente com requisicoes identicas.
        - Mesma chave de idempotencia disputada via Barrier no exato mesmo nanossegundo.
        - Comprova: exatamente 1 vencedor por par (claim concedido) e 1 perdedor bloqueado.
        - Limpeza garantida de recursos com try/finally.
        """
        PAIRS = 10
        TOTAL_TASKS = PAIRS * 2

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()
            self.assertIsNotNone(b.pool)
            await pre_warm_pool_connections(b)

            try:
                barrier = asyncio.Barrier(TOTAL_TASKS)
                race_keys = [f"race_pair_{i}_{uuid.uuid4().hex[:6]}" for i in range(PAIRS)]

                async def race_worker(task_id: int):
                    pair_idx = task_id % PAIRS
                    turn_key = race_keys[pair_idx]
                    sess_id = f"sess_{turn_key}"
                    user_email = f"user_race_{pair_idx}@helpus.local"
                    worker_owner = f"worker_race_{task_id}"
                    body_hash = hashlib.sha256(f"payload_{pair_idx}".encode()).hexdigest()

                    await barrier.wait()
                    try:
                        should_run, cached, token = await b.claim_turn_ledger(
                            idempotency_key=turn_key,
                            owner_token=worker_owner,
                            session_id=sess_id,
                            user_email=user_email,
                            project_id="proj_race",
                            request_payload_hash=body_hash
                        )
                        return {"task_id": task_id, "pair_idx": pair_idx, "claimed": should_run}
                    except Exception as exc:
                        return {"task_id": task_id, "pair_idx": pair_idx, "claimed": False, "error": str(exc)}

                tasks = [race_worker(i) for i in range(TOTAL_TASKS)]
                results = await asyncio.gather(*tasks)

                for p_idx in range(PAIRS):
                    pair_results = [r for r in results if r["pair_idx"] == p_idx]
                    claimed_count = sum(1 for r in pair_results if r["claimed"])
                    self.assertEqual(claimed_count, 1, f"Par {p_idx} deveria ter exatamente 1 vencedor: {pair_results}")

                return {"scenario": "Race Idempotency Collision", "pairs": PAIRS, "status": "PASS"}
            finally:
                await b.fechar()

        report = self.run_async(_test())
        print(f"\n[LOAD TEST 02 RESULT] {json.dumps(report, indent=2)}")

    def test_03_http_chat_50_concurrent_clients(self):
        """
        Cenario 3: 50 Clientes Virtuais Simultaneos chamando o endpoint HTTP FastAPI /chat.
        - Utiliza MockCerebroLoad (IA simulada) com micro-delay controlado de 5ms.
        - AsyncClient com 50 conexoes assincronas simultaneas sincronizadas por Barrier.
        - Medicao de Latencias ponta a ponta (HTTP ASGI + Banco PostgreSQL + IA mock + Commit).
        - Documentacao de Escopo do ASGITransport:
          * O ASGITransport opera inteiramente in-memory/in-process via loop asyncio do FastAPI.
          * Ele testa a capacidade de processamento concorrente do ASGI router, injecao de dependencias,
            validacao Pydantic, isolamento de sessao e transacoes no PostgreSQL efemero.
          * NAO reproduz overheads de rede WAN, TLS handshake, proxies de borda (Vercel) ou latencia
            de geracao de tokens do modelo real Gemini 2.0 Flash (tipicamente 200ms a 1200ms TTFT).
        - Restauracao Estrita de Dependencias: old_banco, old_get_cerebro e dependency_overrides
          sao restaurados incondicionalmente em bloco try/finally.
        """
        import httpx
        NUM_CLIENTS = 50

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()
            self.assertIsNotNone(b.pool)
            await pre_warm_pool_connections(b)

            old_banco = getattr(b_main, "banco", None)
            old_get_cerebro = getattr(b_main, "get_cerebro", None)

            b_main.banco = b
            mock_ai = MockCerebroLoad(delay_ms=5.0)
            b_main.get_cerebro = lambda: mock_ai

            # Override de autenticacao para simular usuario autorizado
            b_main.app.dependency_overrides[obter_usuario_google] = lambda: {
                "email": "load_user@helpus.local", "name": "Load Test User", "role": "user"
            }

            try:
                barrier = asyncio.Barrier(NUM_CLIENTS)
                transport = httpx.ASGITransport(app=b_main.app)

                async def http_client_task(idx: int, client: httpx.AsyncClient):
                    sess_id = f"sess_http_50_{idx}_{uuid.uuid4().hex[:6]}"
                    client_req_id = f"req_http_50_{idx}_{uuid.uuid4().hex[:6]}"

                    payload = {
                        "mensagem": f"Carga HTTP cliente virtual {idx}",
                        "session_id": sess_id,
                        "client_request_id": client_req_id,
                        "model": "gemini-2.0-flash",
                        "project_id": f"proj_http_{idx % 5}"
                    }

                    await barrier.wait()
                    t0 = time.perf_counter()
                    try:
                        resp = await client.post("/chat", json=payload, timeout=20.0)
                        t1 = time.perf_counter()
                        lat_ms = (t1 - t0) * 1000.0
                        return {
                            "idx": idx,
                            "status_code": resp.status_code,
                            "lat_ms": lat_ms,
                            "data": resp.json() if resp.status_code == 200 else resp.text
                        }
                    except Exception as exc:
                        t1 = time.perf_counter()
                        return {"idx": idx, "status_code": 500, "lat_ms": (t1 - t0) * 1000.0, "error": str(exc)}

                start_total = time.perf_counter()
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                    tasks = [http_client_task(i, client) for i in range(NUM_CLIENTS)]
                    results = await asyncio.gather(*tasks)
                end_total = time.perf_counter()

                total_duration_s = end_total - start_total
                successes = [r for r in results if r["status_code"] == 200]
                latencies = [r["lat_ms"] for r in successes]
                pct = compute_percentiles(latencies)
                throughput = len(successes) / total_duration_s if total_duration_s > 0 else 0.0

                self.assertEqual(len(successes), NUM_CLIENTS, f"Erros HTTP observados: {[r for r in results if r['status_code'] != 200]}")
                self.assertEqual(mock_ai.call_count, NUM_CLIENTS)

                return {
                    "scenario": "HTTP /chat 50 Concurrent Clients",
                    "clients": NUM_CLIENTS,
                    "total_duration_s": round(total_duration_s, 3),
                    "throughput_req_s": round(throughput, 1),
                    "percentiles_ms": pct,
                    "error_rate_pct": round(((NUM_CLIENTS - len(successes)) / NUM_CLIENTS) * 100.0, 2),
                    "ai_calls_simulated": mock_ai.call_count
                }
            finally:
                # Restauracao incondicional de dependencias e conexao
                b_main.banco = old_banco
                b_main.get_cerebro = old_get_cerebro
                b_main.app.dependency_overrides.pop(obter_usuario_google, None)
                await b.fechar()

        report = self.run_async(_test())
        print(f"\n[LOAD TEST 03 RESULT] {json.dumps(report, indent=2)}")

    def test_04_fault_injection_and_recovery_under_load(self):
        """
        Cenario 4: Injecao de Falha Abrupta de Conexao e Verificacao de Recuperacao Fail-Closed.
        - Dispara turno de baseline, injeta fechamento abrupto de pool e reabertura.
        - Comprova:
          1. Fail-closed: Operacoes durante a queda sao rejeitadas de forma limpa (sem dados corrompidos).
          2. Auto-recuperacao: Assim que o pool e reconectado, os turnos completam com 100% de integridade.
        - Limpeza garantida com try/finally.
        """
        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            await b.conectar()
            self.assertIsNotNone(b.pool)
            await pre_warm_pool_connections(b)

            try:
                sess_id = f"sess_fault_{uuid.uuid4().hex[:6]}"
                turn_key = f"turn_fault_{uuid.uuid4().hex[:6]}"
                user_email = "fault_test@helpus.local"
                owner = "worker_fault"

                # 1. Turno de baseline funciona normalmente
                should_run, cached, token = await b.claim_turn_ledger(
                    idempotency_key=turn_key,
                    owner_token=owner,
                    session_id=sess_id,
                    user_email=user_email,
                    project_id="proj_fault",
                    request_payload_hash="pre_fault_hash"
                )
                self.assertTrue(should_run)
                ok = await b.persist_and_complete_turn(
                    session_id=sess_id,
                    content="Resposta baseline",
                    idempotency_key=turn_key,
                    owner_token=owner,
                    user_email=user_email,
                    project_id="proj_fault"
                )
                self.assertTrue(ok)

                # 2. Injeta falha forcada: fecha o pool abruptamente e remove referencia
                await b.fechar()
                b.pool = None
                self.assertIsNone(b.pool)

                # 3. Operacao durante a queda deve falhar fail-closed (RuntimeError explicito)
                with self.assertRaises(RuntimeError):
                    await b.claim_turn_ledger(
                        idempotency_key=f"turn_during_fault_{uuid.uuid4().hex[:6]}",
                        owner_token=owner,
                        session_id=sess_id,
                        user_email=user_email,
                        project_id="proj_fault",
                        request_payload_hash="fault_hash"
                    )

                # 4. Recuperacao: reconecta o pool
                await b.conectar()
                self.assertIsNotNone(b.pool)
                await pre_warm_pool_connections(b)

                # 5. Proximo turno completa com 100% de sucesso
                turn_post = f"turn_post_recovery_{uuid.uuid4().hex[:6]}"
                should_run2, _, _ = await b.claim_turn_ledger(
                    idempotency_key=turn_post,
                    owner_token=owner,
                    session_id=sess_id,
                    user_email=user_email,
                    project_id="proj_fault",
                    request_payload_hash="post_fault_hash"
                )
                self.assertTrue(should_run2)
                ok2 = await b.persist_and_complete_turn(
                    session_id=sess_id,
                    content="Resposta pos-recuperacao",
                    idempotency_key=turn_post,
                    owner_token=owner,
                    user_email=user_email,
                    project_id="proj_fault"
                )
                self.assertTrue(ok2)

                return {"scenario": "Fault Injection and Post-Crash Recovery", "status": "PASS"}
            finally:
                if b.pool:
                    await b.fechar()

        report = self.run_async(_test())
        print(f"\n[LOAD TEST 04 RESULT] {json.dumps(report, indent=2)}")


if __name__ == "__main__":
    unittest.main()
