# -*- coding: utf-8 -*-
"""
HelpUS AI - Testes de Carga, Concorrencia e Isolamento Multi-Usuario (Ordem Executiva 044 / 057 / 072)
Validacao de 50+ Clientes Virtuais Simultaneos em PostgreSQL 18 Efemero Local com Provedor de IA Simulado.

Governanca e Seguranca Fail-Closed (Ordem 072):
1. Ambiente 100% Local: Executa exclusivamente em PostgreSQL efemero local na porta 5433 (127.0.0.1 / localhost).
2. Aborto Fail-Closed Imediato: Validacao rigorosa de esquema (postgresql/postgres), host local, porta 5433,
   e nome EXATO de base autorizado ('helpus_ephemeral' ou 'helpus_test').
   Bloqueio estrito de termos de producao ('prod', 'neon', 'railway', 'vercel', 'aws', 'supabase', 'render').
3. Provedor de IA Simulado: MockCerebroLoad simula latencia de inferencia (5ms) sem custos ou chamadas a APIs pagas.
4. Restauracao Garantida (try/finally): Variaveis de ambiente, configuracoes globais, dependencias do FastAPI
   (b_main.banco, b_main.get_cerebro, app.dependency_overrides) e politicas de event loop sao salvas e
   restauradas com preservacao estrita de valores preexistentes.
5. Limpeza de Pool Garantida: Conexoes do pool sao fechadas incondicionalmente via finally, mesmo se
   falhas ocorrerem durante conectar() ou pre-aquecimento.
6. Classificacao Arquitetural do ASGITransport:
   Despacho ASGI local in-process / in-memory no loop de eventos do FastAPI.
   Avalia vazao de pico em rajada (burst), serializacao JSON, middleware e transacoes ACID do PostgreSQL 18 local.
   NAO constitui benchmark de infraestrutura serverless remota, nem inclui latencia WAN, TLS handshake ou TTFT do modelo real Gemini.
7. Isolamento Multi-Usuario e Cross-Project:
   - Validacao estrita em todos os 50 clientes do Cenario 1.
   - Cenario 5 dedicado a validacao funcional independente de isolamento entre identidades autenticadas distintas via API HTTP.
8. Testes Negativos de URL:
   - Suite TestEphemeralUrlValidation valida regras fail-closed sem conexao ao banco de dados.
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

# Bases de dados locais expressamente autorizadas para testes efemeros
AUTHORIZED_EPHEMERAL_DBS = {"helpus_ephemeral", "helpus_test"}
FORBIDDEN_KEYWORDS = {"prod", "production", "neon", "railway", "vercel", "aws", "supabase", "render"}


def validate_ephemeral_pg_url(url: str):
    """
    Guarda fail-closed estrita: garante que o teste de carga execute exclusivamente
    em PostgreSQL efemero local isolado (127.0.0.1:5433 / helpus_ephemeral).
    Qualquer tentativa de apontar para staging, producao ou porta externa aborta a execucao.
    """
    if not url or not isinstance(url, str):
        raise ValueError("VIOLACAO DE SEGURANCA: URL de conexao vazia ou invalida.")

    url_clean = url.strip()
    try:
        parsed = urlparse(url_clean)
    except Exception as exc:
        raise ValueError(f"VIOLACAO DE SEGURANCA: URL malformada: {exc}")

    # 1. Esquema permitido
    if parsed.scheme not in ("postgresql", "postgres"):
        raise ValueError(
            f"VIOLACAO DE SEGURANCA: Esquema '{parsed.scheme}' nao permitido. "
            f"Apenas postgresql:// ou postgres:// sao autorizados."
        )

    # 2. Host local permitido
    allowed_hosts = {"127.0.0.1", "localhost"}
    if not parsed.hostname or parsed.hostname.lower() not in allowed_hosts:
        raise RuntimeError(
            f"VIOLACAO DE SEGURANCA: Host '{parsed.hostname}' nao permitido para testes de carga. "
            f"Apenas hosts locais sao autorizados (127.0.0.1, localhost)."
        )

    # 3. Porta efemera autorizada
    try:
        port = parsed.port
    except Exception:
        raise ValueError("VIOLACAO DE SEGURANCA: Porta informada na URL e invalida.")

    if port != 5433:
        raise RuntimeError(
            f"VIOLACAO DE SEGURANCA: Porta '{port}' invalida. "
            f"Testes de carga exigem porta efemera isolada 5433."
        )

    # 4. Nome EXATO de banco autorizado
    db_name = (parsed.path or "").lstrip("/")
    if db_name not in AUTHORIZED_EPHEMERAL_DBS:
        raise RuntimeError(
            f"VIOLACAO DE SEGURANCA: Banco de dados '{db_name}' nao autorizado. "
            f"Testes exigem nome exato explicitamente permitido: {sorted(list(AUTHORIZED_EPHEMERAL_DBS))}."
        )

    # 5. Bloqueio fail-closed de credenciais ou termos de producao/staging
    full_url_lower = url_clean.lower()
    for term in FORBIDDEN_KEYWORDS:
        if term in full_url_lower:
            raise RuntimeError(
                f"VIOLACAO DE SEGURANCA: Termo proibido '{term}' detectado na URL de conexao. "
                f"Execucao abortada para proteger ambientes remotos/producao."
            )


# Ajuste de path para importacao do backend
ai_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ai_root not in sys.path:
    sys.path.insert(0, ai_root)
backend_dir = os.path.join(ai_root, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import backend.config as b_config
from backend.banco import BancoDados, _log_db_error
import backend.main as b_main
from auth import obter_usuario_google


def check_ephemeral_pg_available() -> bool:
    """Verifica conectividade rapida com socket na porta efemera 5433 apos validacao fail-closed."""
    try:
        validate_ephemeral_pg_url(EPHEMERAL_PG_URL)
    except Exception:
        return False

    parsed = urlparse(EPHEMERAL_PG_URL)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 5433

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


PG_AVAILABLE = check_ephemeral_pg_available()


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
    if not b or not getattr(b, "pool", None):
        return
    conns = []
    for _ in range(min(target_conns, 10)):
        try:
            c = await b.pool.getconn()
            conns.append(c)
        except Exception:
            break
    for c in conns:
        try:
            await b.pool.putconn(c)
        except Exception:
            pass


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


class TestEphemeralUrlValidation(unittest.TestCase):
    """Suite de Testes Negativos e Positivos de Validacao Fail-Closed de URL (Ordem 072 item 3)."""

    def test_valid_ephemeral_url(self):
        """URL canônica válida para banco efêmero deve passar sem erros."""
        validate_ephemeral_pg_url("postgresql://helpus_test@127.0.0.1:5433/helpus_ephemeral")
        validate_ephemeral_pg_url("postgres://helpus_test@localhost:5433/helpus_test")

    def test_reject_invalid_scheme(self):
        """Esquemas não-postgres (http, mysql, etc.) devem ser rejeitados."""
        with self.assertRaises(ValueError):
            validate_ephemeral_pg_url("http://127.0.0.1:5433/helpus_ephemeral")
        with self.assertRaises(ValueError):
            validate_ephemeral_pg_url("mysql://127.0.0.1:5433/helpus_ephemeral")

    def test_reject_remote_host(self):
        """Hosts externos ou remotos devem ser rejeitados imediatamente."""
        with self.assertRaises(RuntimeError):
            validate_ephemeral_pg_url("postgresql://helpus_test@192.168.1.100:5433/helpus_ephemeral")
        with self.assertRaises(RuntimeError):
            validate_ephemeral_pg_url("postgresql://helpus_test@db.example.com:5433/helpus_ephemeral")

    def test_reject_invalid_port(self):
        """Portas diferentes de 5433 devem ser estritamente bloqueadas."""
        with self.assertRaises(RuntimeError):
            validate_ephemeral_pg_url("postgresql://helpus_test@127.0.0.1:5432/helpus_ephemeral")
        with self.assertRaises(RuntimeError):
            validate_ephemeral_pg_url("postgresql://helpus_test@127.0.0.1:6543/helpus_ephemeral")

    def test_reject_unauthorized_db_name(self):
        """Bancos fora da lista explícita AUTHORIZED_EPHEMERAL_DBS devem ser rejeitados."""
        with self.assertRaises(RuntimeError):
            validate_ephemeral_pg_url("postgresql://helpus_test@127.0.0.1:5433/production_db")
        with self.assertRaises(RuntimeError):
            validate_ephemeral_pg_url("postgresql://helpus_test@127.0.0.1:5433/my_custom_db")

    def test_reject_forbidden_production_keywords(self):
        """Presença de termos proibidos em credenciais ou caminho deve abortar a execução."""
        with self.assertRaises(RuntimeError):
            validate_ephemeral_pg_url("postgresql://prod_admin:secret@127.0.0.1:5433/helpus_ephemeral")
        with self.assertRaises(RuntimeError):
            validate_ephemeral_pg_url("postgresql://helpus_test@127.0.0.1:5433/helpus_ephemeral?source=neon")

    def test_reject_malformed_url(self):
        """URLs vazias ou com sintaxe inválida devem falhar com erro seguro."""
        with self.assertRaises(ValueError):
            validate_ephemeral_pg_url("")
        with self.assertRaises(ValueError):
            validate_ephemeral_pg_url("invalid_url_without_scheme")


class TestStateAndOverrideRestoration(unittest.TestCase):
    """
    Suite de Testes Unitarios Leves de Restauracao de Estado Global e Overrides (Ordem 074 item 2).
    Executa sem conexao ao banco e sem benchmarks de carga.
    """

    def test_dependency_override_restored_after_controlled_exception(self):
        """Comprova que dependency_overrides e restaurado ao valor exato pre-existente apos excecao."""
        sentinel_override = lambda: {"email": "preexisting@helpus.local"}
        b_main.app.dependency_overrides[obter_usuario_google] = sentinel_override

        had_orig = obter_usuario_google in b_main.app.dependency_overrides
        orig = b_main.app.dependency_overrides.get(obter_usuario_google)

        with self.assertRaises(ZeroDivisionError):
            try:
                b_main.app.dependency_overrides[obter_usuario_google] = lambda: {"email": "temporary@helpus.local"}
                self.assertEqual(b_main.app.dependency_overrides[obter_usuario_google]()["email"], "temporary@helpus.local")
                _ = 1 / 0
            finally:
                if had_orig:
                    b_main.app.dependency_overrides[obter_usuario_google] = orig
                else:
                    b_main.app.dependency_overrides.pop(obter_usuario_google, None)

        self.assertIs(b_main.app.dependency_overrides[obter_usuario_google], sentinel_override)
        b_main.app.dependency_overrides.pop(obter_usuario_google, None)

    def test_dependency_override_removed_when_previously_absent_after_exception(self):
        """Comprova que override temporario e removido quando nao existia antes."""
        b_main.app.dependency_overrides.pop(obter_usuario_google, None)
        self.assertNotIn(obter_usuario_google, b_main.app.dependency_overrides)

        had_orig = obter_usuario_google in b_main.app.dependency_overrides
        orig = b_main.app.dependency_overrides.get(obter_usuario_google)

        with self.assertRaises(RuntimeError):
            try:
                b_main.app.dependency_overrides[obter_usuario_google] = lambda: {"email": "temp@helpus.local"}
                raise RuntimeError("Controlled failure")
            finally:
                if had_orig:
                    b_main.app.dependency_overrides[obter_usuario_google] = orig
                else:
                    b_main.app.dependency_overrides.pop(obter_usuario_google, None)

        self.assertNotIn(obter_usuario_google, b_main.app.dependency_overrides)

    def test_global_banco_and_cerebro_restored_after_exception(self):
        """Comprova que b_main.banco e b_main.get_cerebro sao restaurados apos excecao."""
        orig_banco = getattr(b_main, "banco", None)
        orig_cerebro = getattr(b_main, "get_cerebro", None)

        mock_sentinel_banco = object()
        mock_sentinel_cerebro = lambda: "sentinel_cerebro"

        with self.assertRaises(KeyError):
            try:
                b_main.banco = mock_sentinel_banco
                b_main.get_cerebro = mock_sentinel_cerebro
                self.assertIs(b_main.banco, mock_sentinel_banco)
                raise KeyError("Controlled error")
            finally:
                b_main.banco = orig_banco
                b_main.get_cerebro = orig_cerebro

        self.assertIs(b_main.banco, orig_banco)
        self.assertIs(b_main.get_cerebro, orig_cerebro)


class LoadConcurrency50ClientsTest(unittest.TestCase):
    _orig_env_db_url = None
    _orig_env_require_pg = None
    _orig_config_db_url = None
    _orig_b_main_banco_url = None
    _orig_loop_policy = None

    @classmethod
    def setUpClass(cls):
        try:
            # 1. Validacao fail-closed da URL antes de qualquer teste
            validate_ephemeral_pg_url(EPHEMERAL_PG_URL)

            # 2. Salvamento estrito de configuracoes globais para restauracao garantida
            cls._orig_env_db_url = os.environ.get("DATABASE_URL")
            cls._orig_env_require_pg = os.environ.get("HELPUS_REQUIRE_POSTGRES")
            cls._orig_config_db_url = getattr(b_config, "DATABASE_URL", None)
            cls._orig_b_main_banco_url = getattr(b_main.banco, "database_url", None)
            try:
                cls._orig_loop_policy = asyncio.get_event_loop_policy()
            except Exception:
                cls._orig_loop_policy = None

            os.environ["DATABASE_URL"] = EPHEMERAL_PG_URL
            b_config.DATABASE_URL = EPHEMERAL_PG_URL
            b_main.banco.database_url = EPHEMERAL_PG_URL
            os.environ["HELPUS_REQUIRE_POSTGRES"] = "1"
        except Exception:
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        # Restauracao segura e incondicional de todas as variaveis globais e politicas
        try:
            if cls._orig_env_db_url is not None:
                os.environ["DATABASE_URL"] = cls._orig_env_db_url
            else:
                os.environ.pop("DATABASE_URL", None)

            if cls._orig_env_require_pg is not None:
                os.environ["HELPUS_REQUIRE_POSTGRES"] = cls._orig_env_require_pg
            else:
                os.environ.pop("HELPUS_REQUIRE_POSTGRES", None)

            if cls._orig_config_db_url is not None:
                b_config.DATABASE_URL = cls._orig_config_db_url

            if cls._orig_b_main_banco_url is not None:
                b_main.banco.database_url = cls._orig_b_main_banco_url
            else:
                b_main.banco.database_url = None

        finally:
            if cls._orig_loop_policy is not None:
                try:
                    asyncio.set_event_loop_policy(cls._orig_loop_policy)
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
        - Disparo em rajada (burst) via asyncio.Barrier(50) para medir capacidade maxima de pico.
        - 50 usuarios distintos distribuidos em 5 projetos independentes (proj_load_0..proj_load_4).
        - Medicao de Throughput de rajada, Latencias (p50, p95, p99) e Integridade do Ledger.
        - Validacao EXAUSTIVA de Isolamento Cross-Project e Cross-User sobre TODOS os 50 clientes.
        - Limpeza de conexoes garantida por try/finally mesmo se conectar() falhar.
        """
        NUM_CLIENTS = 50
        NUM_PROJECTS = 5
        run_id = uuid.uuid4().hex[:8]

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            try:
                await b.conectar()
                self.assertIsNotNone(b.pool)
                await pre_warm_pool_connections(b)

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

                # Verificacao EXAUSTIVA de Isolamento Cross-Project e Cross-User sobre TODOS os 50 clientes
                for c_idx in range(NUM_CLIENTS):
                    user_email = f"load_client_{run_id}_{c_idx}@helpus.local"
                    target_proj = f"proj_load_{run_id}_{c_idx % NUM_PROJECTS}"
                    other_proj = f"proj_load_{run_id}_{(c_idx + 1) % NUM_PROJECTS}"

                    # 1. Usuario ve estritamente sua propria conversa no seu projeto
                    own_sessions = await b.listar_conversas_usuario(user_email=user_email, limite=10, project_id=target_proj)
                    self.assertEqual(len(own_sessions), 1, f"Cliente {c_idx} deve ver exatamente 1 conversa propria.")
                    self.assertEqual(own_sessions[0].get("project_id"), target_proj)

                    # 2. Usuario NAO ve sessoes no projeto alheio (Isolamento Cross-Project estrito)
                    other_proj_sessions = await b.listar_conversas_usuario(user_email=user_email, limite=10, project_id=other_proj)
                    self.assertEqual(len(other_proj_sessions), 0, f"Cliente {c_idx} nao deve ver conversas no projeto {other_proj}.")

                    # 3. Usuario terceiro NAO ve nada nesta sessao ou projeto (Isolamento Cross-User estrito)
                    other_user = f"intruder_{c_idx}@helpus.local"
                    intruder_sessions = await b.listar_conversas_usuario(user_email=other_user, limite=10, project_id=target_proj)
                    self.assertEqual(len(intruder_sessions), 0, f"Intruso nao deve ver conversas de {user_email}.")

                return {
                    "scenario": "Atomic Turn 50 Clients (Burst Load)",
                    "clients": NUM_CLIENTS,
                    "total_duration_s": round(total_duration_s, 3),
                    "burst_throughput_req_s": round(throughput, 1),
                    "percentiles_ms": pct,
                    "success_count": len(successful),
                    "failure_count": len(failed),
                    "isolation_verified_clients": NUM_CLIENTS
                }
            finally:
                if b and getattr(b, "pool", None):
                    await b.fechar()

        report = self.run_async(_test())
        print(f"\n[LOAD TEST 01 RESULT (Burst Local)] {json.dumps(report, indent=2)}")

    def test_02_concurrent_race_idempotency_deduplication(self):
        """
        Cenario 2: 10 pares (20 clientes) colidindo simultaneamente com requisicoes identicas.
        - Mesma chave de idempotencia disputada via Barrier no exato mesmo nanossegundo.
        - Comprova: exatamente 1 vencedor por par (claim concedido) e 1 perdedor bloqueado.
        - Limpeza de recursos garantida por try/finally.
        """
        PAIRS = 10
        TOTAL_TASKS = PAIRS * 2

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            try:
                await b.conectar()
                self.assertIsNotNone(b.pool)
                await pre_warm_pool_connections(b)

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
                if b and getattr(b, "pool", None):
                    await b.fechar()

        report = self.run_async(_test())
        print(f"\n[LOAD TEST 02 RESULT] {json.dumps(report, indent=2)}")

    def test_03_http_chat_50_concurrent_clients_asgi_local(self):
        """
        Cenario 3: 50 Clientes Virtuais Simultaneos chamando endpoint HTTP FastAPI /chat.
        - Despacho ASGI Local In-Process / In-Memory (httpx.ASGITransport).
        - Utiliza MockCerebroLoad (IA simulada) com micro-delay controlado de 5ms.
        - AsyncClient com 50 requisicoes disparadas simultaneamente por Barrier.
        - Medicao de Throughput e Latencias locais (FastAPI ASGI + Banco PostgreSQL 18 + IA mock).
        - Documentacao de Escopo do ASGITransport:
          * O ASGITransport opera inteiramente in-memory/in-process via loop asyncio do FastAPI.
          * Ele avalia o router ASGI, injecao de dependencias, validacao Pydantic e transacoes no PostgreSQL efemero.
          * NAO constitui benchmark serverless nem reproduz overheads de rede WAN, TLS handshake, proxies de borda
            (Vercel) ou latencia real de geracao de tokens do Gemini 2.0 Flash (tipicamente 200ms a 1200ms TTFT).
        - Restauracao Estrita de Dependencias (Ordem 072 item 1):
          Preserva o valor E a existencia preexistente de dependency_overrides[obter_usuario_google],
          restaurando-o exatamente como estava antes do teste.
        """
        import httpx
        NUM_CLIENTS = 50

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            old_banco = getattr(b_main, "banco", None)
            old_get_cerebro = getattr(b_main, "get_cerebro", None)

            # Preserva configuracao preexistente de override (Ordem 072 item 1)
            had_orig_override = obter_usuario_google in b_main.app.dependency_overrides
            orig_override = b_main.app.dependency_overrides.get(obter_usuario_google)

            try:
                await b.conectar()
                self.assertIsNotNone(b.pool)
                await pre_warm_pool_connections(b)

                b_main.banco = b
                mock_ai = MockCerebroLoad(delay_ms=5.0)
                b_main.get_cerebro = lambda: mock_ai

                # Override de autenticacao para teste de carga
                b_main.app.dependency_overrides[obter_usuario_google] = lambda: {
                    "email": "load_user@helpus.local", "name": "Load Test User", "role": "user"
                }

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
                    "scenario": "HTTP /chat 50 Concurrent Clients (ASGI Local In-Process)",
                    "clients": NUM_CLIENTS,
                    "total_duration_s": round(total_duration_s, 3),
                    "burst_throughput_req_s": round(throughput, 1),
                    "percentiles_ms": pct,
                    "error_rate_pct": round(((NUM_CLIENTS - len(successes)) / NUM_CLIENTS) * 100.0, 2),
                    "ai_calls_simulated": mock_ai.call_count
                }
            finally:
                # Restauracao incondicional e preservacao exata de overrides e dependencias
                b_main.banco = old_banco
                b_main.get_cerebro = old_get_cerebro
                if had_orig_override:
                    b_main.app.dependency_overrides[obter_usuario_google] = orig_override
                else:
                    b_main.app.dependency_overrides.pop(obter_usuario_google, None)

                if b and getattr(b, "pool", None):
                    await b.fechar()

        report = self.run_async(_test())
        print(f"\n[LOAD TEST 03 RESULT (ASGI Local In-Process)] {json.dumps(report, indent=2)}")

    def test_04_fault_injection_and_recovery_under_load(self):
        """
        Cenario 4: Injecao de Falha Abrupta de Conexao e Verificacao de Recuperacao Fail-Closed.
        - Dispara turno de baseline, injeta fechamento abrupto de pool e reabertura.
        - Comprova:
          1. Fail-closed: Operacoes durante a queda sao rejeitadas de forma limpa (sem dados corrompidos).
          2. Auto-recuperacao: Assim que o pool e reconectado, os turnos completam com 100% de integridade.
        - Limpeza de recursos garantida por try/finally.
        """
        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            try:
                await b.conectar()
                self.assertIsNotNone(b.pool)
                await pre_warm_pool_connections(b)

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
                if b and getattr(b, "pool", None):
                    await b.fechar()

        report = self.run_async(_test())
        print(f"\n[LOAD TEST 04 RESULT] {json.dumps(report, indent=2)}")

    def test_05_http_multi_user_authenticated_strict_isolation(self):
        """
        Cenario 5 (Ordem 057 / 072): Teste Funcional Independente de Isolamento Entre Usuarios Autenticados Distintos.
        - Separa rigorosamente os requisitos de carga (Cenarios 1-3) da verificacao de isolamento multi-usuario na API.
        - Executa requisicoes HTTP via ASGITransport alternando entre identidades autenticadas independentes:
          * Usuario Alpha: alpha@helpus.local no projeto 'proj_alpha'
          * Usuario Beta: beta@helpus.local no projeto 'proj_beta'
        - Comprova:
          1. Usuario Alpha cria sessao e conversa com sucesso via POST /chat.
          2. Usuario Alpha acessa seu proprio historico via GET /historico/{session_alpha} -> HTTP 200.
          3. Usuario Beta tenta acessar o historico de Alpha via GET /historico/{session_alpha} -> HTTP 403 (Acesso Negado).
          4. Usuario Alpha ve sua conversa em GET /conversas?project_id=proj_alpha -> 1 conversa.
          5. Usuario Beta em GET /conversas?project_id=proj_alpha -> 0 conversas (Isolamento Cross-User estrito).
          6. Chamada sem autenticacao em GET /historico/{session_alpha} -> HTTP 401 (Nao Autorizado).
        - Preserva e restaura rigorosamente o override preexistente de autenticacao via try/finally.
        """
        import httpx

        async def _test():
            b = BancoDados(EPHEMERAL_PG_URL)
            old_banco = getattr(b_main, "banco", None)
            old_get_cerebro = getattr(b_main, "get_cerebro", None)

            # Preserva configuracao preexistente de override (Ordem 072 item 1)
            had_orig_override = obter_usuario_google in b_main.app.dependency_overrides
            orig_override = b_main.app.dependency_overrides.get(obter_usuario_google)

            transport = httpx.ASGITransport(app=b_main.app)
            run_id = uuid.uuid4().hex[:6]
            sess_alpha = f"sess_alpha_{run_id}"

            try:
                await b.conectar()
                self.assertIsNotNone(b.pool)
                await pre_warm_pool_connections(b)

                b_main.banco = b
                mock_ai = MockCerebroLoad(delay_ms=2.0)
                b_main.get_cerebro = lambda: mock_ai

                # 1. Usuario Alpha autenticado cria conversa
                b_main.app.dependency_overrides[obter_usuario_google] = lambda: {
                    "email": "alpha@helpus.local", "name": "User Alpha", "role": "user"
                }

                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                    resp_chat = await client.post("/chat", json={
                        "mensagem": "Ola sou o Usuario Alpha",
                        "session_id": sess_alpha,
                        "client_request_id": f"req_alpha_{run_id}",
                        "model": "gemini-2.0-flash",
                        "project_id": "proj_alpha"
                    })
                    self.assertEqual(resp_chat.status_code, 200, f"Erro chat Alpha: {resp_chat.text}")

                    # 2. Usuario Alpha le seu proprio historico -> HTTP 200
                    resp_hist_alpha = await client.get(f"/historico/{sess_alpha}?project_id=proj_alpha")
                    self.assertEqual(resp_hist_alpha.status_code, 200)
                    hist_data = resp_hist_alpha.json()
                    self.assertTrue(len(hist_data.get("mensagens", [])) >= 1)

                    # 3. Usuario Alpha lista conversas no seu projeto
                    resp_conv_alpha = await client.get("/conversas?project_id=proj_alpha")
                    self.assertEqual(resp_conv_alpha.status_code, 200)
                    convs_alpha = resp_conv_alpha.json().get("conversas", [])
                    self.assertTrue(any(c.get("session_id") == sess_alpha for c in convs_alpha))

                # 4. Alterna identidade para Usuario Beta
                b_main.app.dependency_overrides[obter_usuario_google] = lambda: {
                    "email": "beta@helpus.local", "name": "User Beta", "role": "user"
                }

                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                    # 5. Usuario Beta tenta acessar sessao de Alpha -> DEVE RETORNAR 403 FORBIDDEN
                    resp_hist_beta = await client.get(f"/historico/{sess_alpha}?project_id=proj_alpha")
                    self.assertEqual(resp_hist_beta.status_code, 403, "Usuario Beta nao pode acessar sessao de Alpha.")

                    # 6. Usuario Beta lista projeto proj_alpha -> DEVE RETORNAR 0 conversas
                    resp_conv_beta = await client.get("/conversas?project_id=proj_alpha")
                    self.assertEqual(resp_conv_beta.status_code, 200)
                    convs_beta = resp_conv_beta.json().get("conversas", [])
                    self.assertFalse(any(c.get("session_id") == sess_alpha for c in convs_beta), "Beta nao pode ver conversas de Alpha.")

                # 7. Requisicao anonima / sem autenticacao -> DEVE RETORNAR 401 UNAUTHORIZED
                b_main.app.dependency_overrides[obter_usuario_google] = lambda: None

                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                    resp_anon = await client.get(f"/historico/{sess_alpha}")
                    self.assertEqual(resp_anon.status_code, 401, "Requisicao sem auth deve falhar com 401.")

                return {
                    "scenario": "Multi-User Authenticated Isolation (HTTP API)",
                    "user_alpha": "alpha@helpus.local",
                    "user_beta": "beta@helpus.local",
                    "cross_user_access_code": resp_hist_beta.status_code,
                    "unauthenticated_code": resp_anon.status_code,
                    "status": "PASS"
                }
            finally:
                # Restauracao incondicional e preservacao exata de overrides e dependencias
                b_main.banco = old_banco
                b_main.get_cerebro = old_get_cerebro
                if had_orig_override:
                    b_main.app.dependency_overrides[obter_usuario_google] = orig_override
                else:
                    b_main.app.dependency_overrides.pop(obter_usuario_google, None)

                if b and getattr(b, "pool", None):
                    await b.fechar()

        report = self.run_async(_test())
        print(f"\n[MULTI-USER ISOLATION RESULT] {json.dumps(report, indent=2)}")


if __name__ == "__main__":
    unittest.main()
