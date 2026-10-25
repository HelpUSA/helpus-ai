import re
import json
import asyncio
import socket
import hashlib
import base64
import binascii
import ipaddress
import urllib.parse
# -*- coding: utf-8 -*-
"""
API Principal - HelpUS.
Orquestra: banco de dados, cerebro IA e motor de busca.
"""
from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import List, Optional, Dict
import time
import uuid
import os
import hmac
from pathlib import Path
from contextlib import asynccontextmanager

import config as app_config
from config import DEBUG, CORS_ORIGINS
from banco import BancoDados
from cerebro import CerebroIA, set_request_model, get_request_model, get_request_metadata, set_request_metadata, reset_request_context
from buscador import MotorBusca
from auth import obter_usuario_google, obter_admin_google
from admin_telemetry import summarize_events
from local_readonly_files import LocalReadonlyFiles
from local_repo_status import LocalRepoStatus
from helpus_internal_memory_recorder import safe_record_chat_memory_event
from helpus_operational_lesson_context import append_operational_lesson_context
from helpus_operational_lessons import build_admin_operational_lessons_panel
from helpus_memory_context import build_helpus_memory_context
from helpus_internal_agents import (
    build_agent_trace_items,
    internal_agents_enabled,
    internal_agents_visible_trace_enabled,
    run_internal_agents,
)

# ===== INICIALIZACAO DOS SERVICOS =====
banco = BancoDados()
cerebro: Optional[CerebroIA] = None
buscador: Optional[MotorBusca] = None

try:
    cerebro = CerebroIA()
    print(f"[OK] CerebroIA carregado no startup: {cerebro.nome_modelo}")
except Exception as _e:
    print(f"[WARN] Erro ao carregar CerebroIA no startup: {_e}")
    cerebro = None

try:
    buscador = MotorBusca(banco)
    print("[OK] Buscador pronto")
except Exception as _e:
    print(f"[WARN] Erro ao inicializar buscador no startup: {_e}")
    buscador = None

def get_cerebro() -> Optional[CerebroIA]:
    global cerebro
    if cerebro is None:
        try:
            cerebro = CerebroIA()
        except Exception as e:
            if DEBUG:
                print(f"[WARN] Erro ao instanciar CerebroIA on-demand: {e}")
            cerebro = None
    return cerebro

def get_buscador() -> Optional[MotorBusca]:
    global buscador
    if buscador is None:
        try:
            buscador = MotorBusca(banco)
        except Exception as e:
            buscador = None
    return buscador

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa e finaliza os servicos"""
    global cerebro, buscador

    # P0 CONCORRENCIA (Ciclo 021): Verificacao efetiva das condicoes operacionais no startup
    workers_env = int(os.getenv("WEB_CONCURRENCY", os.getenv("WORKERS", "1")))
    has_db = bool(getattr(banco, "database_url", None) or os.getenv("DATABASE_URL"))
    if workers_env > 1 and not has_db:
        raise RuntimeError(
            f"Incompatibilidade operacional critica: foram solicitados {workers_env} workers, "
            "mas DATABASE_URL nao esta configurada. Em memoria local, multiplos workers violam o isolamento "
            "e nao garantem exactly-once. Restrinja a WORKERS=1 ou forneca DATABASE_URL com suporte a advisory locks."
        )

    print("=" * 60)
    print("[INFO] INICIANDO HelpUS")
    print("=" * 60)

    # 1. Conectar ao banco
    print("[INFO] Conectando ao PostgreSQL...")
    try:
        await banco.conectar()
        await banco.criar_tabelas()
        print("[OK] Banco de dados pronto")
    except Exception as e:
        print(f"[WARN] Banco de dados nao disponivel: {e}")
        print("   Rodando sem banco de dados...")

    # 2. Carregar modelo IA se ainda nao carregado
    if cerebro is None:
        try:
            cerebro = CerebroIA()
            print(f"[OK] Modelo carregado: {cerebro.nome_modelo}")
        except Exception as e:
            print(f"[ERROR] Erro ao carregar modelo: {e}")

    # 3. Inicializar buscador se ainda nao inicializado
    if buscador is None:
        buscador = MotorBusca(banco)

    print("=" * 60)
    print("[OK] HelpUS PRONTO PARA USO")
    print("=" * 60)

    yield

    print("[INFO] Encerrando servidor...")



# ===== CRIACAO DO APP =====
app = FastAPI(
    title="HelpUS",
    description="HelpUS - Seu Assistente Inteligente",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== MODELOS DE DADOS =====
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
BLOCKED_EXTENSIONS = {".env", ".exe", ".bat", ".cmd", ".sh", ".ps1", ".vbs", ".dll", ".so", ".bin", ".py", ".js"}
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "internal"}
TRUSTED_IMAGE_DOMAINS = {
    "images.unsplash.com",
    "storage.googleapis.com",
    "helpusbr.com",
    "ai.helpusbr.com",
}

def resolver_provedor_modelo(model_name: Optional[str]) -> str:
    if not model_name:
        return "google"
    m = model_name.strip().lower()
    if "gemini" in m:
        return "google"
    if "deepseek" in m:
        return "deepseek"
    if "gpt" in m or "openai" in m:
        return "openai"
    return "google"

def validar_url_remota(url: Optional[str]):
    if not url:
        return
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Apenas URLs HTTP/HTTPS sao permitidas.")
    hostname = (parsed.hostname or "").lower()
    if not hostname or hostname in BLOCKED_HOSTS:
        raise HTTPException(status_code=400, detail="Host remoto nao permitido (protecao SSRF).")

    # Bloqueio definitivo de URLs externas arbitrarias para mitigar qualquer risco de SSRF/Rebinding
    dominio_permitido = hostname in ("ai.helpusbr.com", "helpusbr.com") or hostname.endswith(".helpusbr.com")
    if not dominio_permitido:
        raise HTTPException(
            status_code=400,
            detail="URLs externas arbitrarias estao desabilitadas por seguranca (protecao SSRF). Por favor, anexe a imagem diretamente via upload (base64)."
        )

    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise HTTPException(status_code=400, detail="IP privado ou loopback nao permitido (protecao SSRF).")
    except ValueError:
        # Mitigacao contra DNS rebinding e resolucao para IPs privados/locais
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for _, _, _, _, sockaddr in addr_info:
                ip_str = sockaddr[0]
                resolved_ip = ipaddress.ip_address(ip_str)
                if resolved_ip.is_private or resolved_ip.is_loopback or resolved_ip.is_link_local or resolved_ip.is_reserved:
                    raise HTTPException(status_code=400, detail=f"Dominio resolve para IP privado ({ip_str}) bloqueado por protecao SSRF.")
        except socket.gaierror:
            raise HTTPException(status_code=400, detail="Nao foi possivel resolver o dominio remoto especificado.")

def _detectar_tipo_binario(dados: bytes) -> Optional[str]:
    if len(dados) < 4:
        return None
    if dados.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if dados.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if dados.startswith(b"GIF87a") or dados.startswith(b"GIF89a"):
        return "image/gif"
    if len(dados) >= 12 and dados[:4] == b"RIFF" and dados[8:12] == b"WEBP":
        return "image/webp"
    if dados.startswith(b"%PDF-"):
        return "application/pdf"
    return None

def validar_anexo(image_base64: Optional[str] = None, file_name: Optional[str] = None):
    if file_name:
        fn_lower = file_name.strip().lower()
        if fn_lower.startswith(".env") or any(fn_lower.endswith(ext) for ext in BLOCKED_EXTENSIONS):
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo '{file_name}' nao permitido por questoes de seguranca."
            )
    if image_base64:
        raw_b64 = image_base64
        mime = None
        if image_base64.startswith("data:"):
            header, _, data_part = image_base64.partition(",")
            mime = header.split(";")[0].replace("data:", "").strip().lower()
            if mime and mime not in ALLOWED_IMAGE_MIMES and mime != "application/pdf":
                raise HTTPException(
                    status_code=400,
                    detail=f"Tipo MIME '{mime}' nao permitido. Permitidos: {sorted(list(ALLOWED_IMAGE_MIMES))}"
                )
            raw_b64 = data_part
        try:
            decoded = base64.b64decode(raw_b64, validate=True)
        except (binascii.Error, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Formato base64 corrompido ou invalido."
            )
        if len(decoded) > MAX_IMAGE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Tamanho decodificado do anexo excede o limite de 10MB."
            )
        tipo_detectado = _detectar_tipo_binario(decoded)
        if not tipo_detectado:
            raise HTTPException(
                status_code=400,
                detail="Assinatura binaria de anexo incompativel com os tipos permitidos (PNG, JPEG, WEBP, GIF, PDF)."
            )
        if mime and tipo_detectado != mime:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo MIME declarado ('{mime}') incompativel com a assinatura binaria real ('{tipo_detectado}')."
            )

class MensagemRequest(BaseModel):
    mensagem: str
    session_id: Optional[str] = None
    pesquisar_web: bool = True
    project_id: Optional[str] = 'general'
    image_base64: Optional[str] = None
    imagem_base64: Optional[str] = None
    file_name: Optional[str] = None
    image_url: Optional[str] = None
    model: Optional[str] = None
    client_request_id: Optional[str] = None
    is_retry: bool = False

class MensagemResponse(BaseModel):
    resposta: str
    session_id: str
    project_id: str = 'general'
    fontes: List[Dict[str, str]] = []
    tempo_total: float = 0.0
    tokens_gerados: int = 0
    provider_used: str = ""
    fallback_reason: Optional[str] = None
    provider_configured: str = ""
    model: str = ""
    model_requested: Optional[str] = None
    model_used: Optional[str] = None
    latency_ms: Optional[float] = None
    agent_trace: List[Dict[str, str]] = []

class StatusResponse(BaseModel):
    status: str
    modelo: str
    modelo_carregado: bool
    paginas_indexadas: int
    app_version: str
    build_commit: str = ''
    auth_required: bool = False
    provider_order: List[str] = []
    provider_configured: str = ""
    provider_used: str = ""
    fallback_reason: Optional[str] = None
    model: str = ""
    latency_ms: Optional[float] = None

class IndexarRequest(BaseModel):
    url: str
    profundidade: int = 2

class ProjectMemoryRequest(BaseModel):
    project_id: Optional[str] = "general"
    title: str
    content: str
    tags: Optional[str] = ""


class ProjectMemoryUpdateRequest(BaseModel):
    project_id: Optional[str] = "general"
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    enabled: Optional[bool] = None


class InternalSmokeChatRequest(BaseModel):
    mensagem: str = "Responda apenas: HELPUS_INTERNAL_SMOKE_OK"
    project_id: Optional[str] = "internal-smoke"

class InternalSmokeChatResponse(BaseModel):
    ok: bool
    resposta: str
    provider_configured: str = ""
    provider_used: str = ""
    fallback_reason: Optional[str] = None
    model: str = ""
    latency_ms: Optional[float] = None

def construir_contexto_memorias(memorias: List[Dict], limite_total: int = 2500) -> str:
    """Monta contexto curto e seguro com memorias ativas do projeto."""
    if not memorias:
        return ""

    partes = [
        "Memoria ativa do projeto:",
        "Use estas memorias como contexto operacional persistente. Elas nao substituem a pergunta atual, politicas de seguranca, autorizacoes explicitas nem validacao de dados.",
    ]

    total = sum(len(p) for p in partes)
    for memoria in memorias[:12]:
        titulo = str(memoria.get("title") or "").strip()
        conteudo = str(memoria.get("content") or "").strip()
        tags = str(memoria.get("tags") or "").strip()

        if not titulo or not conteudo:
            continue

        item = f"- {titulo}: {conteudo}"
        if tags:
            item += f" [tags: {tags}]"

        if len(item) > 700:
            item = item[:697] + "..."

        if total + len(item) > limite_total:
            break

        partes.append(item)
        total += len(item)

    return "\n".join(partes) if len(partes) > 2 else ""


def _provider_metrics(latency_ms: Optional[float] = None) -> Dict[str, object]:
    c = get_cerebro()
    return {
        "provider_configured": getattr(app_config, "AI_PROVIDER", ""),
        "provider_used": getattr(c, "last_provider_used", getattr(c, "provider", "")) if c else "",
        "fallback_reason": getattr(c, "last_fallback_reason", None) if c else None,
        "model": getattr(c, "nome_modelo", "") if c else "",
        "latency_ms": latency_ms,
    }

LOCAL_REPO_ROOT = Path(__file__).resolve().parents[1]
local_readonly_files = LocalReadonlyFiles(LOCAL_REPO_ROOT)
local_repo_status = LocalRepoStatus(LOCAL_REPO_ROOT)

# ===== ENDPOINTS =====
@app.get("/")
async def raiz():
    """Endpoint raiz"""
    return {
        "mensagem": "HelpUS - Seu Assistente Inteligente",
        "versao": "1.0.0",
        "docs": "/docs"
    }


_provider_health_cache: Dict[str, Dict[str, Any]] = {}
HEALTH_CHECK_TTL_SECONDS = 60.0

def _get_provider_health(provider: str) -> str:
    """Retorna 'healthy', 'unhealthy', 'unknown' ou 'not_configured'. Nunca divulga credenciais."""
    if not _is_provider_configured(provider):
        return "not_configured"
    cached = _provider_health_cache.get(provider)
    if cached and (time.time() - cached.get("timestamp", 0) < HEALTH_CHECK_TTL_SECONDS):
        return cached.get("status", "unknown")
    return cached.get("status", "unknown") if cached else "unknown"

def record_provider_health(provider: str, success: bool):
    _provider_health_cache[provider] = {
        "status": "healthy" if success else "unhealthy",
        "timestamp": time.time(),
    }

def _is_provider_configured(provider: str) -> bool:
    if provider == "google":
        return bool(getattr(app_config, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY"))
    if provider == "deepseek":
        return bool(getattr(app_config, "DEEPSEEK_API_KEY", None) or os.getenv("DEEPSEEK_API_KEY"))
    if provider == "openai":
        return bool(getattr(app_config, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY"))
    return False

def _is_provider_healthy(provider: str) -> bool:
    return _get_provider_health(provider) == "healthy"

def _is_provider_available(provider: str) -> bool:
    return _is_provider_configured(provider) and (_get_provider_health(provider) in ("healthy", "unknown"))

_idempotency_cache: Dict[str, Dict[str, Any]] = {}
IDEMPOTENCY_TTL_SECONDS = 120.0

def _gerar_chave_idempotencia(user_email: Optional[str], session_id: str, client_request_id: Optional[str], mensagem: str) -> Optional[str]:
    if not client_request_id:
        return None
    msg_hash = hashlib.sha256((mensagem or "").encode("utf-8")).hexdigest()[:16]
    return f"{user_email or 'anon'}:{session_id}:{client_request_id}:{msg_hash}"

LEASE_TIMEOUT_SECONDS = 30.0
HEARTBEAT_TIMEOUT_SECONDS = 15.0

def claim_or_get_idempotent_request(
    idempotency_key: Optional[str],
    is_retry: bool = False
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Reivindica a execucao atomica com token de posse (fencing token) ou retorna a resposta em cache.

    Garantias e Comportamento:
    - Retorna tupla: (should_run: bool, cached_response: Optional[dict], owner_token: Optional[str]).
    - Se uma resposta concluida existir, retorna (False, cached_response, None).
    - Se uma requisicao identica ja estiver in_progress:
      - Verifica o heartbeat da inferencia original:
        - Se heartbeat recente (< HEARTBEAT_TIMEOUT_SECONDS, 15s), a inferencia esta ATIVA independentemente
          do tempo decorrido total (mesmo > 30s). Rejeita com HTTP 409 Conflict.
        - Se o heartbeat expirou (>= 15s sem atualizacao) E is_retry=True: o processo anterior falhou/travou.
          Assume o lease com um NOVO owner_token seguro (fencing token).
        - Se nao for retry: rejeita com HTTP 409 Conflict (concorrencia bloqueada).
    - Se for nova requisicao: gera owner_token unico (UUID4), armazena timestamps e retorna (True, None, owner_token).

    Limitacao Multi-Worker:
    - Este mecanismo em memoria opera por processo de worker. Em arquiteturas com multiplos workers
      independentes sem afinidade de conexao, a sincronizacao atomica requer armazenamento distribuido
      (Redis com SET NX PX e redlock ou PostgreSQL Advisory Lock pg_try_advisory_xact_lock).
    """
    if not idempotency_key:
        return True, None, None

    now = time.time()
    for k in [k for k, v in _idempotency_cache.items() if now - v.get("timestamp", 0) > IDEMPOTENCY_TTL_SECONDS]:
        _idempotency_cache.pop(k, None)

    entry = _idempotency_cache.get(idempotency_key)
    if entry:
        if entry.get("status") == "completed":
            return False, entry.get("response"), None
        if entry.get("status") == "in_progress":
            last_hb = entry.get("last_heartbeat", entry.get("timestamp", 0))
            hb_elapsed = now - last_hb
            if is_retry:
                if hb_elapsed < HEARTBEAT_TIMEOUT_SECONDS:
                    raise HTTPException(
                        status_code=409,
                        detail="Inferencia original ainda em processamento ativo (heartbeat ativo). Aguarde a conclusao antes de reenviar."
                    )
                _idempotency_cache.pop(idempotency_key, None)
            else:
                raise HTTPException(
                    status_code=409,
                    detail="Requisicao identica ja esta sendo processada simultaneamente (concorrencia bloqueada)."
                )

    owner_token = str(uuid.uuid4())
    _idempotency_cache[idempotency_key] = {
        "status": "in_progress",
        "timestamp": now,
        "last_heartbeat": now,
        "owner_token": owner_token,
    }
    return True, None, owner_token

def heartbeat_idempotent_request(idempotency_key: Optional[str], owner_token: Optional[str]) -> bool:
    """Atualiza o batimento cardiaco da requisicao em progresso pelo detentor valido do token."""
    if not idempotency_key or not owner_token:
        return False
    entry = _idempotency_cache.get(idempotency_key)
    if entry and entry.get("status") == "in_progress" and entry.get("owner_token") == owner_token:
        entry["last_heartbeat"] = time.time()
        return True
    return False

def _mask_key(key: Optional[str]) -> str:
    """Mascara chaves de idempotencia em logs para proteger dados de usuario, emails e session IDs."""
    if not key:
        return "none"
    parts = key.split(":")
    if len(parts) >= 4:
        return f"***:***:***:{parts[-1][:8]}"
    return f"***_{hashlib.sha256(key.encode()).hexdigest()[:8]}"

def _sanitize_log_message(msg: Any) -> str:
    """Sanitiza mensagens de log impedindo vazamento de credenciais, URLs internas de banco ou tokens."""
    s = str(msg)
    s = re.sub(r'postgres(ql)?://[^@\s]+@', 'postgresql://***:***@', s)
    s = re.sub(r'(bearer\s+)[a-zA-Z0-9_\-\.]+', r'\1***', s, flags=re.IGNORECASE)
    s = re.sub(r'(key|token|secret|password|senha)\s*[:=]\s*[^\s,]+', r'\1=***', s, flags=re.IGNORECASE)
    return s

class _RefCountLock:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.ref_count = 0

_turn_locks: Dict[str, _RefCountLock] = {}
_turn_locks_mutex = asyncio.Lock()

@asynccontextmanager
async def turn_lock_context(idempotency_key: Optional[str]):
    """Adquire lock exclusivo por idempotency_key com limpeza segura e atomica (sem vazamento nem corrida)."""
    if not idempotency_key:
        yield
        return

    async with _turn_locks_mutex:
        if idempotency_key not in _turn_locks:
            _turn_locks[idempotency_key] = _RefCountLock()
        entry = _turn_locks[idempotency_key]
        entry.ref_count += 1

    await entry.lock.acquire()
    try:
        yield
    finally:
        entry.lock.release()
        async with _turn_locks_mutex:
            entry.ref_count -= 1
            if entry.ref_count <= 0 and not entry.lock.locked():
                _turn_locks.pop(idempotency_key, None)

async def get_turn_lock(idempotency_key: Optional[str]):
    """Helper compativel com turn_lock_context."""
    return turn_lock_context(idempotency_key)

ALLOWED_DETAIL_KEYS = {
    "masked_key", "error_kind", "model_eff", "model_req", "provider", "duration_ms", "status_code", "retryable"
}
SAFE_CORR_ID_RE = re.compile(r'^[a-zA-Z0-9\-_]{8,64}$')
SAFE_EVENT_RE = re.compile(r'^[a-zA-Z0-9_]{3,64}$')

def log_structured(level: str, event: str, correlation_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
    """Emite log estruturado padronizado em JSON com allowlist estrita e correlation_id opaco, sem secrets (P1 - Ciclo 021)."""
    safe_details = {}
    if details and isinstance(details, dict):
        for k, v in details.items():
            if k in ALLOWED_DETAIL_KEYS:
                safe_details[k] = _sanitize_log_message(str(v)) if isinstance(v, str) else v

    safe_corr_id = "opaque_none"
    if correlation_id and isinstance(correlation_id, str):
        c_str = correlation_id.strip()
        if SAFE_CORR_ID_RE.match(c_str):
            safe_corr_id = c_str[:64]

    safe_event = "unknown_event"
    if event and isinstance(event, str):
        e_str = event.strip()
        if SAFE_EVENT_RE.match(e_str):
            safe_event = e_str[:64]

    entry = {
        "timestamp": round(time.time(), 3),
        "level": str(level).upper() if level else "INFO",
        "event": safe_event,
        "correlation_id": safe_corr_id,
        "details": safe_details,
    }
    print(json.dumps(entry, ensure_ascii=False))

def is_owner_token_valid(idempotency_key: Optional[str], owner_token: Optional[str]) -> bool:
    """Valida se o owner_token ainda e o detentor ativo e legitimo da execucao in_progress."""
    if not idempotency_key or not owner_token or not isinstance(owner_token, str) or not owner_token.strip():
        return False
    entry = _idempotency_cache.get(idempotency_key)
    if not entry or entry.get("status") != "in_progress":
        return False
    return entry.get("owner_token") == owner_token

def complete_idempotent_request(
    idempotency_key: Optional[str],
    response_data: Dict[str, Any],
    owner_token: str
) -> bool:
    """Finaliza a requisicao atomica com a resposta calculada (CAS com fencing token estrito).
    
    Invariantes Estritas (P0 - Ciclo 017):
    1. EXIGE owner_token valido e nao-vazio do executor legitimo.
    2. Rejeita se a chave nao existir no cache.
    3. Rejeita se o status atual nao for 'in_progress' (ja concluida ou cancelada).
    4. Rejeita se o owner_token nao corresponder exatamente ao executor atual (fenced).
    5. Transicao atomica para status 'completed' com carimbo temporal.
    """
    if not idempotency_key or not owner_token or not isinstance(owner_token, str) or not owner_token.strip():
        return False

    entry = _idempotency_cache.get(idempotency_key)
    if not entry:
        return False

    if entry.get("status") != "in_progress":
        return False

    if entry.get("owner_token") != owner_token:
        return False

    entry["status"] = "completed"
    entry["response"] = response_data
    entry["completed_at"] = time.time()
    entry["timestamp"] = time.time()
    return True

def release_idempotent_request(idempotency_key: Optional[str], owner_token: str) -> bool:
    """Libera a trava in_progress se a requisicao falhar antes da conclusao.
    
    Invariantes Estritas (P0 - Ciclo 017):
    1. EXIGE owner_token valido e nao-vazio; impede release desautorizado ou sem token.
    2. Rejeita se chave inexistente ou se status nao for 'in_progress'.
    3. Rejeita se owner_token pertencer a outro executor.
    """
    if not idempotency_key or not owner_token or not isinstance(owner_token, str) or not owner_token.strip():
        return False

    entry = _idempotency_cache.get(idempotency_key)
    if not entry or entry.get("status") != "in_progress":
        return False

    if entry.get("owner_token") != owner_token:
        return False

    _idempotency_cache.pop(idempotency_key, None)
    return True

class IdempotencyHeartbeatSession:
    """Mantem renovacao independente e periodica de heartbeat em background durante inferencias silenciosas.
    Garante que o lease seja renovado mesmo se o modelo demorar > 15s ou > 30s sem emitir chunks."""
    def __init__(self, idempotency_key: Optional[str], owner_token: Optional[str], interval: float = 3.0):
        self.idempotency_key = idempotency_key
        self.owner_token = owner_token
        self.interval = interval
        self._stop_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    def start(self):
        if not self.idempotency_key or not self.owner_token:
            return
        self._task = asyncio.create_task(self._run_loop())

    async def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval)
                break
            except asyncio.TimeoutError:
                ok = heartbeat_idempotent_request(self.idempotency_key, self.owner_token)
                if not ok:
                    break

    async def stop(self):
        self._stop_event.set()
        if self._task and not self._task.done():
            try:
                await asyncio.wait_for(self._task, timeout=0.5)
            except Exception:
                pass

def get_idempotent_response(idempotency_key: Optional[str]) -> Optional[Dict[str, Any]]:
    """Helper de leitura PURA: consulta resposta concluida em cache sem qualquer side effect ou criacao de claim."""
    if not idempotency_key:
        return None
    entry = _idempotency_cache.get(idempotency_key)
    if entry and entry.get("status") == "completed":
        return entry.get("response")
    return None

def save_idempotent_response(idempotency_key: Optional[str], response_data: Dict[str, Any], owner_token: str) -> bool:
    """Salva a resposta idempotente concluida. EXIGE owner_token explicito e valido do executor legitimo.
    Sem recuperacao automatica ou fallback para impedir side effects ou bypass de fencing."""
    if not idempotency_key or not owner_token or not isinstance(owner_token, str) or not owner_token.strip():
        return False
    return complete_idempotent_request(idempotency_key, response_data, owner_token=owner_token)

@app.get("/modelos")
async def listar_modelos():
    """Retorna o catalogo oficial de modelos homologados e sua disponibilidade real no servidor"""
    google_configured = _is_provider_configured("google")
    google_health = _get_provider_health("google")
    google_healthy = (google_health == "healthy")
    google_available = google_configured and google_healthy

    deepseek_configured = _is_provider_configured("deepseek")
    deepseek_health = _get_provider_health("deepseek")
    deepseek_healthy = (deepseek_health == "healthy")
    deepseek_available = deepseek_configured and deepseek_healthy

    return {
        "modelos": [
            {
                "id": "gemini-2.5-flash-lite",
                "name": "Flash-Lite",
                "provider": "google",
                "alias": "helpus-fast",
                "desc": "Rapido e eficiente",
                "capabilities": ["text", "code", "fast"],
                "configured": google_configured,
                "health": google_health,
                "healthy": google_healthy,
                "available": google_available,
            },
            {
                "id": "gemini-2.5-flash",
                "name": "Flash",
                "provider": "google",
                "alias": "helpus-general",
                "desc": "Equilibrio ideal de inteligencia",
                "capabilities": ["text", "code", "vision", "reasoning"],
                "configured": google_configured,
                "health": google_health,
                "healthy": google_healthy,
                "available": google_available,
            },
            {
                "id": "gemini-2.5-pro",
                "name": "Pro",
                "provider": "google",
                "alias": "helpus-reasoner",
                "desc": "Raciocinio profundo e analise",
                "capabilities": ["text", "code", "vision", "deep_thinking"],
                "configured": google_configured,
                "health": google_health,
                "healthy": google_healthy,
                "available": google_available,
            },
            {
                "id": "deepseek-chat",
                "name": "DeepSeek Chat",
                "provider": "deepseek",
                "alias": "helpus-code",
                "desc": "Especialista em codigo e arquitetura",
                "capabilities": ["text", "code"],
                "configured": deepseek_configured,
                "health": deepseek_health,
                "healthy": deepseek_healthy,
                "available": deepseek_available,
            },
            {
                "id": "deepseek-reasoner",
                "name": "DeepSeek R1",
                "provider": "deepseek",
                "alias": "helpus-reasoner",
                "desc": "Raciocinio logico avancado",
                "capabilities": ["text", "code", "deep_reasoning"],
                "configured": deepseek_configured,
                "health": deepseek_health,
                "healthy": deepseek_healthy,
                "available": deepseek_available,
            },
        ],
        "default_model": "gemini-2.5-flash",
    }

@app.get("/status", response_model=StatusResponse)
async def status():
    """Verifica o status de todos os servicos"""
    c = get_cerebro()
    b = get_buscador()
    return StatusResponse(
        status="online",
        modelo=c.nome_modelo if c else "nao carregado",
        modelo_carregado=c is not None,
        paginas_indexadas=getattr(b, 'paginas_indexadas', 0) if b else 0,
        app_version=app_config.APP_VERSION,
        build_commit=app_config.BUILD_COMMIT,
        auth_required=app_config.AUTH_REQUIRED,
        provider_order=app_config.AI_PROVIDER_ORDER,
        **_provider_metrics()
    )


# ===== HELPUSDEV LOCAL BRIDGE ENDPOINTS =====
try:
    from backend.helpusdev_bridge import (
        obter_proximo_comando,
        processar_resultado_comando,
        is_helpusdev_online,
        segundos_desde_ultima_presenca,
        BridgeResultRequest,
        detectar_intencao_local,
        executar_no_computador_local,
    )
except ModuleNotFoundError:
    from helpusdev_bridge import (
        obter_proximo_comando,
        processar_resultado_comando,
        is_helpusdev_online,
        segundos_desde_ultima_presenca,
        BridgeResultRequest,
        detectar_intencao_local,
        executar_no_computador_local,
    )

def require_bridge_token(authorization: Optional[str] = Header(default=None)) -> None:
    """Fail closed unless a dedicated bridge credential matches.

    Configure HELPUS_BRIDGE_API_TOKEN on both the server and the trusted
    HelpUSDev client. Never reuse a Google user token or public API key.
    """
    configured = os.getenv("HELPUS_BRIDGE_API_TOKEN", "")
    if not configured:
        raise HTTPException(status_code=503, detail={"error": "bridge_not_configured"})
    scheme, _, presented = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not presented or not hmac.compare_digest(presented, configured):
        raise HTTPException(status_code=401, detail={"error": "bridge_unauthorized"})


@app.get("/bridge/poll")
async def bridge_poll(_bridge_auth: None = Depends(require_bridge_token)):
    """Endpoint de long-polling para a aplicação HelpUSDev local receber tarefas"""
    cmd = await obter_proximo_comando(timeout=20.0)
    return {"command": cmd}

@app.post("/bridge/result")
async def bridge_result(res: BridgeResultRequest, _bridge_auth: None = Depends(require_bridge_token)):
    """Recebe o resultado da execução realizada pelo HelpUSDev local"""
    processar_resultado_comando(res.command_id, res.status, res.output or "")
    return {"ok": True}

@app.get("/bridge/status")
async def bridge_status(_bridge_auth: None = Depends(require_bridge_token)):
    """Retorna o status da conexão com a aplicação HelpUSDev local"""
    return {
        "online": is_helpusdev_online(),
        "last_seen_seconds_ago": segundos_desde_ultima_presenca(),
    }



@app.get("/admin/status", response_model=StatusResponse)
async def admin_status(usuario = Depends(obter_admin_google)):
    """Verifica o status de todos os servicos"""
    c = get_cerebro()
    b = get_buscador()
    return StatusResponse(
        status="online",
        modelo=c.nome_modelo if c else "nao carregado",
        modelo_carregado=c is not None,
        paginas_indexadas=getattr(b, 'paginas_indexadas', 0) if b else 0,
        app_version=app_config.APP_VERSION,
        build_commit=app_config.BUILD_COMMIT,
        auth_required=app_config.AUTH_REQUIRED,
        provider_order=app_config.AI_PROVIDER_ORDER,
        **_provider_metrics()
    )



@app.get("/admin/operational-lessons")
async def admin_operational_lessons(usuario = Depends(obter_admin_google)):
 """Readonly operational lessons panel for admin review."""
 return build_admin_operational_lessons_panel()

@app.get("/admin/telemetry")
async def admin_telemetry(usuario = Depends(obter_admin_google)):
    telemetry_path = os.getenv("HELPUS_TELEMETRY_LOG", "reports/helpus_telemetry.jsonl")
    return summarize_events(telemetry_path)

@app.get("/local/status")
async def local_status(usuario = Depends(obter_admin_google)):
    """Read-only local repository status for admin diagnostics."""
    return local_repo_status.status()


@app.get("/local/diff")
async def local_diff(usuario = Depends(obter_admin_google)):
    """Read-only local repository diff summary for admin diagnostics."""
    return local_repo_status.diff()


@app.get("/local/files/read")
async def local_files_read(path: str, usuario = Depends(obter_admin_google)):
    """Read an allowlisted local file with secret/path safeguards."""
    return local_readonly_files.read_text(path)


@app.get("/local/files/list")
async def local_files_list(path: str = "docs/", limit: int = 200, usuario = Depends(obter_admin_google)):
    """List allowlisted local files with secret/path safeguards."""
    return local_readonly_files.list_files(path, limit=limit)


@app.get("/local/docs/search")
async def local_docs_search(q: str, path: str = "docs/", limit: int = 50, usuario = Depends(obter_admin_google)):
    """Search allowlisted local text files with secret/path safeguards."""
    return local_readonly_files.search_text(q, path, limit=limit)


@app.post("/local/plan")
async def local_plan(request: dict, usuario = Depends(obter_admin_google)):
    """Create a plan-only local action decision. This endpoint never executes commands."""
    try:
        from backend.local_safe_plan import plan_local_action
    except ModuleNotFoundError:
        from local_safe_plan import plan_local_action
    return plan_local_action(request)

@app.get("/local/plan/intents")
async def local_plan_intents(usuario = Depends(obter_admin_google)):
    try:
        from backend.local_safe_plan import list_local_plan_intents
    except ModuleNotFoundError:
        from local_safe_plan import list_local_plan_intents
    return list_local_plan_intents()

@app.post("/internal/smoke-chat", response_model=InternalSmokeChatResponse)
async def internal_smoke_chat(
    request: InternalSmokeChatRequest,
    x_internal_smoke_token: Optional[str] = Header(default=None),
):
    expected_token = os.getenv("INTERNAL_SMOKE_TOKEN", "")
    if not expected_token or x_internal_smoke_token != expected_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    c = get_cerebro()
    if not c:
        raise HTTPException(status_code=503, detail="Modelo de IA nao carregado.")

    inicio = time.time()
    resposta, tokens, tempo_ia = await c.pensar(
        pergunta=request.mensagem,
        contexto_busca="",
        historico=[],
    )
    latency_ms = round((time.time() - inicio) * 1000, 2)

    return InternalSmokeChatResponse(
        ok=True,
        resposta=resposta,
        **_provider_metrics(latency_ms=latency_ms),
    )



ALLOWED_MODELS = {
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "deepseek-chat",
    "deepseek-reasoner",
    "gpt-4o",
    "gpt-4o-mini",
}

def validar_modelo(model: Optional[str]) -> Optional[str]:
    if not model or not str(model).strip():
        return None
    m = str(model).strip().lower()
    if m not in ALLOWED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Modelo '{model}' invalido ou nao permitido. Modelos permitidos: {sorted(list(ALLOWED_MODELS))}"
        )
    return m

@app.post("/chat", response_model=MensagemResponse)
async def chat(request: MensagemRequest, usuario = Depends(obter_usuario_google)):
    """Endpoint principal de conversa"""
    c = get_cerebro()
    if not c:
        raise HTTPException(
            status_code=503,
            detail="Modelo de IA nao carregado."
        )


    inicio_total = time.time()
    session_id = request.session_id or str(uuid.uuid4())
    project_id = (request.project_id or 'general')[:80]
    user_email = usuario["email"] if usuario else None

    # Validacao estrita de propriedade de sessao (FAIL-CLOSED)
    if banco and session_id:
        try:
            eh_dono = await banco.verificar_propriedade_sessao(session_id, user_email, project_id)
            if not eh_dono:
                raise HTTPException(
                    status_code=403,
                    detail="Acesso negado: sessao pertence a outra conta ou autorizacao nao pode ser confirmada."
                )
        except HTTPException:
            raise
        except Exception as e:
            if getattr(banco, "database_url", None):
                raise HTTPException(
                    status_code=503,
                    detail="Servico de validacao de sessao temporariamente indisponivel."
                )

    validar_modelo(request.model)
    if request.model:
        set_request_model(request.model.strip().lower())
    effective_image_b64 = request.image_base64 or request.imagem_base64
    validar_anexo(effective_image_b64, request.file_name)
    validar_url_remota(request.image_url)

    idempotency_key = _gerar_chave_idempotencia(user_email, session_id, request.client_request_id, request.mensagem)
    is_claimed = False
    owner_token = None
    if idempotency_key:
        should_run, cached_resp, owner_token = claim_or_get_idempotent_request(idempotency_key, is_retry=request.is_retry)
        if not should_run and cached_resp:
            return MensagemResponse(**cached_resp)
        is_claimed = should_run

    hb_session = IdempotencyHeartbeatSession(idempotency_key, owner_token, interval=3.0)
    hb_session.start()
    # Agentes internos controlados por HELPUS_INTERNAL_AGENTS_ENABLED.
    agent_trace = [
        {"label": "Analisando pedido", "status": "done"}
    ]
    completed_successfully = False

    try:
        # Carrega historico
        historico = []
        try:
            historico = await banco.carregar_mensagens(session_id, limite=10, user_email=user_email)
        except:
            pass

        # Memoria ativa do projeto
        contexto_memorias = ""
        try:
            memorias_ativas = await banco.listar_memorias_projeto(
                project_id=project_id,
                include_disabled=False,
                limite=12,
            )
            contexto_memorias = construir_contexto_memorias(memorias_ativas)
        except:
            contexto_memorias = ""

        agent_trace.append({
            "label": "Consultando memorias do projeto",
            "status": "done" if contexto_memorias else "skipped",
        })

        # Busca na web
        fontes = []
        contexto_busca = ""

        if request.pesquisar_web and buscador:
            try:
                resultados = await asyncio.wait_for(buscador.buscar(request.mensagem), timeout=3.0)
                if resultados:
                    contexto_busca = "📚 Informacoes encontradas:\n\n"
                    for i, r in enumerate(resultados[:5], 1):
                        contexto_busca += f"{i}. {r['titulo']}\n"
                        contexto_busca += f"   {r['snippet'][:200]}\n"
                        contexto_busca += f"   🔗 Fonte: {r['url']}\n\n"
                        fontes.append({
                            "titulo": r['titulo'],
                            "url": r.get('url', ''),
                            "fonte": r.get('fonte', 'Web')
                        })
            except Exception as e:
                if DEBUG:
                    print(f"[WARN] Erro ou timeout na busca: {e}")


        # Salva pergunta (evita duplicacao se for retry explicito)
        if not request.is_retry:
            try:
                await banco.salvar_mensagem(
                    session_id,
                    "user",
                    request.mensagem,
                    user_email=usuario["email"] if usuario else None,
                    project_id=project_id,
                    title=request.mensagem[:80],
                )
            except:
                pass

        # Memoria interna recente/relevante, controlada por HELPUS_MEMORY_CONTEXT_ENABLED.
        contexto_memoria_interna = ""
        try:
            contexto_memoria_interna = await run_in_threadpool(
                build_helpus_memory_context,
                conversation_id=session_id,
                project_id=project_id,
                limit=8,
            )
        except Exception as e:
            if DEBUG:
                print(f"Erro ao carregar memoria interna: {e}")
            contexto_memoria_interna = ""
        agent_trace.append({
            "label": "Consultando memoria interna",
            "status": "done" if contexto_memoria_interna else "skipped",
        })

        # HELPUS_OPERATIONAL_LESSON_CONTEXT_V1
        _helpus_user_message_for_lessons = (
            getattr(request, "mensagem", None)
            or getattr(request, "message", None)
            or getattr(request, "pergunta", None)
            or ""
        )
        contexto_busca = append_operational_lesson_context(
            base_context=contexto_busca,
            user_message=str(_helpus_user_message_for_lessons),
        )

        # Execução transparente no computador local via HelpUSDev
        contexto_local = ""
        acao_local = detectar_intencao_local(request.mensagem, historico=historico)
        if acao_local:
            action, params = acao_local
            agent_trace.append({"label": f"Executando no computador local via HelpUSDev ({action})", "status": "running"})
            res_local = await executar_no_computador_local(action, params)
            if res_local.get("status") == "success":
                saida = res_local.get("output", "")
                contexto_local = f"\n\n[DADOS OBTIDOS DIRETAMENTE DO COMPUTADOR LOCAL VIA HELPUSDEV]:\nAção: {action}\nResultado:\n{saida}\n[FIM DOS DADOS LOCAIS]\nInstrução: Responda ao usuário com base nesses dados reais do computador dele de forma prestativa e transparente."
                agent_trace[-1]["status"] = "done"
            else:
                aviso = res_local.get("output", "Falha de conexão.")
                contexto_local = f"\n\n[AVISO HELPUSDEV LOCAL]: {aviso}\nInstrução: Informe educadamente que você tentou acessar o computador local, mas a aplicação HelpUSDev precisa estar aberta e rodando na máquina."
                agent_trace[-1]["status"] = "warning"

        pergunta_para_ia = request.mensagem + (contexto_local if contexto_local else "")

        # Gera resposta
        agent_trace.append({"label": "Chamando modelo de IA", "status": "running"})
        resposta, tokens, tempo_ia = await c.pensar(
            pergunta=pergunta_para_ia,
            contexto_busca="\n\n".join([parte for parte in [contexto_memorias, contexto_memoria_interna, contexto_busca] if parte]),
            historico=historico,
            image_base64=effective_image_b64,
            image_url=request.image_url,
        )
        internal_agents_result = await run_internal_agents(
            pergunta=request.mensagem,
            contexto_busca="\n\n".join([parte for parte in [contexto_memorias, contexto_memoria_interna, contexto_busca] if parte]),
            historico=historico,
            thinker=c.pensar,
            base_response=resposta,
            base_tokens=tokens,
            base_latency_seconds=tempo_ia if isinstance(tempo_ia, (int, float)) else 0.0,
        )
        if internal_agents_result.enabled:
            resposta = internal_agents_result.final_response or resposta
            tokens = internal_agents_result.tokens
            tempo_ia = internal_agents_result.latency_seconds
            if internal_agents_visible_trace_enabled():
                agent_trace.extend(build_agent_trace_items(internal_agents_result.steps))
                for idx in range(len(agent_trace)):
                    if agent_trace[idx].get("label") == "Agentes internos":
                        agent_trace[idx] = {"label": "Agentes internos", "status": "done"}
                        break

        agent_trace[-1] = {"label": "Chamando modelo de IA", "status": "done"}

        # P0 Concorrencia: aborta persistencia se o worker foi cercado (fenced por retry/timeout)
        is_fenced = bool(is_claimed and owner_token and not is_owner_token_valid(idempotency_key, owner_token))
        if is_fenced:
            print(f"[WARN] Worker cercado (fenced): abortando persistencia para chave {_mask_key(idempotency_key)}")
            cached_now = get_idempotent_response(idempotency_key)
            if cached_now:
                return MensagemResponse(**cached_now)
            raise HTTPException(status_code=409, detail="Requisicao cancelada ou substituida por concorrencia (fenced).")

        # Salva resposta
        try:
            await banco.salvar_mensagem(
            session_id,
            "assistant",
            resposta,
            user_email=usuario["email"] if usuario else None,
            project_id=project_id,
        )
        except:
            pass

        # Grava evento de memoria interna sem afetar a resposta do chat.
        await run_in_threadpool(
            safe_record_chat_memory_event,
            user_message=request.mensagem,
            assistant_reply=resposta,
            conversation_id=session_id,
            actor="assistant",
            provider=getattr(c, "last_provider_used", getattr(c, "provider", "")),
            route="chat",
            project_id=project_id,
            extra={
                "tokens_gerados": tokens,
                "tempo_ia": tempo_ia,
                "fontes_count": len(fontes),
            },
        )

        agent_trace.append({"label": "Salvando memoria da conversa", "status": "done"})
        agent_trace.append({"label": "Preparando resposta final", "status": "done"})

        tempo_total = round(time.time() - inicio_total, 2)

        meta = get_request_metadata()
        prov_used = meta.get("provider_used") or getattr(c, "last_provider_used", getattr(c, "provider", ""))
        fb_reason = meta.get("fallback_reason") or getattr(c, "last_fallback_reason", None)
        model_eff = meta.get("model_used") or get_request_model() or getattr(c, "nome_modelo", request.model or "")
        model_req = request.model or model_eff

        resp_obj = MensagemResponse(
            resposta=resposta,
            session_id=session_id,
            project_id=project_id,
            fontes=fontes,
            tempo_total=tempo_total,
            tokens_gerados=tokens,
            provider_used=prov_used,
            fallback_reason=fb_reason,
            provider_configured=getattr(app_config, "AI_PROVIDER", ""),
            model=model_eff,
            model_requested=model_req,
            model_used=model_eff,
            latency_ms=round(tempo_ia * 1000, 2) if isinstance(tempo_ia, (int, float)) else None,
            agent_trace=agent_trace,
        )
        if idempotency_key:
            save_idempotent_response(idempotency_key, resp_obj.model_dump() if hasattr(resp_obj, 'model_dump') else resp_obj.dict(), owner_token=owner_token)
        upstream_prov = resolver_provedor_modelo(model_eff)
        record_provider_health(upstream_prov, success=(fb_reason is None))
        record_provider_health(prov_used, success=(fb_reason is None))
        completed_successfully = True
        return resp_obj


    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Erro no chat: {e}")
        return MensagemResponse(
            resposta="Olá! O assistente HelpUS está ativo. No momento, o serviço de inteligência artificial generativa está processando a sua requisição ou aguardando credenciais ativas de IA. Como posso te ajudar com os nossos serviços e plataformas?",
            session_id=session_id,
            project_id=project_id,
            fontes=[],
            tempo_total=round(time.time() - inicio_total, 2),
            tokens_gerados=0,
            provider_used="",
            fallback_reason=str(e)[:200],
            provider_configured=getattr(app_config, "AI_PROVIDER", ""),
            model="",
            latency_ms=None,
            agent_trace=agent_trace,
        )
    finally:
        await hb_session.stop()
        if is_claimed and not completed_successfully and idempotency_key and owner_token:
            release_idempotent_request(idempotency_key, owner_token=owner_token)


@app.post("/chat/stream")
async def chat_stream(request: MensagemRequest, usuario = Depends(obter_usuario_google)):
    """Endpoint de conversa com streaming SSE (Server-Sent Events)"""
    c = get_cerebro()
    if not c:
        raise HTTPException(
            status_code=503,
            detail="Modelo de IA nao carregado."
        )

    import json

    session_id = request.session_id or str(uuid.uuid4())
    user_email = usuario["email"] if usuario else None
    project_id = request.project_id or "general"

    # Validacao estrita de propriedade de sessao (FAIL-CLOSED)
    if banco and session_id:
        try:
            eh_dono = await banco.verificar_propriedade_sessao(session_id, user_email, project_id)
            if not eh_dono:
                raise HTTPException(
                    status_code=403,
                    detail="Acesso negado: sessao pertence a outra conta ou autorizacao nao pode ser confirmada."
                )
        except HTTPException:
            raise
        except Exception as e:
            if getattr(banco, "database_url", None):
                raise HTTPException(
                    status_code=503,
                    detail="Servico de validacao de sessao temporariamente indisponivel."
                )

    validar_modelo(request.model)
    if request.model:
        set_request_model(request.model.strip().lower())
    effective_image_b64 = request.image_base64 or request.imagem_base64
    validar_anexo(effective_image_b64, request.file_name)
    validar_url_remota(request.image_url)

    idempotency_key = _gerar_chave_idempotencia(user_email, session_id, request.client_request_id, request.mensagem)
    is_stream_claimed = False
    owner_token = None
    if idempotency_key:
        should_run, cached_resp, owner_token = claim_or_get_idempotent_request(idempotency_key, is_retry=request.is_retry)
        if not should_run and cached_resp:
            async def replay_cached_stream():
                text_content = cached_resp.get("resposta", "")
                yield f"data: {json.dumps({'content': text_content, 'text': text_content, 'session_id': session_id, 'model_requested': cached_resp.get('model_requested'), 'model_used': cached_resp.get('model_used'), 'provider_used': cached_resp.get('provider_used'), 'fallback_reason': cached_resp.get('fallback_reason'), 'cached': True}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'done': True, 'session_id': session_id}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(replay_cached_stream(), media_type="text/event-stream")
        is_stream_claimed = should_run

    # Salva mensagem do usuario imediatamente (se nao for retry)
    if banco and not request.is_retry:
        try:
            await banco.salvar_mensagem(
                session_id=session_id,
                role="user",
                content=request.mensagem,
                user_email=user_email,
                project_id=project_id,
            )
        except Exception as e:
            if DEBUG:
                print(f"[WARN] Erro ao salvar mensagem do usuario em stream: {e}")

    # Carrega historico recente para contexto conversacional
    historico_recente = []
    if banco:
        try:
            historico_recente = await banco.carregar_mensagens(session_id, limite=6, user_email=user_email)
        except:
            pass

    # Public chat must never trigger local device operations.
    pergunta_stream = request.mensagem

    captured_model = get_request_model() or request.model or "gemini-2.5-flash"
    captured_metadata = dict(get_request_metadata())
    stream_hb_session = IdempotencyHeartbeatSession(idempotency_key, owner_token, interval=3.0)
    stream_hb_session.start()

    async def event_generator():
        set_request_model(captured_model)
        set_request_metadata(captured_metadata)
        full_chunks = []
        stream_completed_ok = False
        last_model_req = request.model or getattr(c, "nome_modelo", "gemini-2.5-flash")
        last_model_eff = getattr(c, "nome_modelo", last_model_req)
        last_prov_used = getattr(c, "last_provider_used", getattr(c, "provider", "fallback"))
        last_fb_reason = getattr(c, "last_fallback_reason", None)
        try:
            async for chunk in c.pensar_stream(
                pergunta=pergunta_stream,
                image_base64=request.image_base64,
                image_url=request.image_url,
            ):
                heartbeat_idempotent_request(idempotency_key, owner_token)
                full_chunks.append(chunk)
                meta = get_request_metadata()
                model_eff = meta.get("model_used") or get_request_model() or request.model or "gemini-2.5-flash"
                prov_used = meta.get("provider_used") or resolver_provedor_modelo(model_eff)
                fb_reason = meta.get("fallback_reason")
                yield f"data: {json.dumps({'content': chunk, 'text': chunk, 'session_id': session_id, 'model_requested': request.model or model_eff, 'model_used': model_eff, 'provider_used': prov_used, 'fallback_reason': fb_reason}, ensure_ascii=False)}\n\n"
            stream_completed_ok = True
        except Exception as err:
            err_msg = f"Erro durante streaming: {str(err)}"
            yield f"data: {json.dumps({'error': err_msg, 'session_id': session_id}, ensure_ascii=False)}\n\n"
        finally:
            await stream_hb_session.stop()
            # Atualizacao de saude executada apenas UMA VEZ no encerramento do stream
            upstream_prov = resolver_provedor_modelo(last_model_eff)
            record_provider_health(upstream_prov, success=stream_completed_ok and (last_fb_reason is None))
            record_provider_health(last_prov_used, success=stream_completed_ok and (last_fb_reason is None))

            # 1. P0 FENCING & STREAMING PERSISTENCIA (protegido contra TOCTOU):
            resposta_completa = "".join(full_chunks)
            persisted_ok = False
            stream_corr_id = str(uuid.uuid4())
            
            async def _persist_under_lock():
                nonlocal persisted_ok
                if is_stream_claimed and owner_token and not is_owner_token_valid(idempotency_key, owner_token):
                    log_structured("WARN", "stream_fenced_persistence_aborted", correlation_id=stream_corr_id, details={"masked_key": _mask_key(idempotency_key)})
                    if idempotency_key and owner_token:
                        release_idempotent_request(idempotency_key, owner_token=owner_token)
                    return

                if banco and resposta_completa and stream_completed_ok:
                    try:
                        res_save = await banco.salvar_mensagem(
                            session_id=session_id,
                            role="assistant",
                            content=resposta_completa,
                            user_email=user_email,
                            project_id=project_id,
                        )
                        persisted_ok = bool(res_save is True)
                    except Exception as e:
                        persisted_ok = False
                        log_structured("ERROR", "stream_assistant_persistence_failed", correlation_id=stream_corr_id, details={"error_kind": type(e).__name__})

                # 2. P0 IDEMPOTENCIA: Conclui CAS apenas se HOUVE PERSISTENCIA EFETIVA e stream completou
                if is_stream_claimed and idempotency_key and owner_token:
                    if stream_completed_ok and persisted_ok:
                        complete_idempotent_request(idempotency_key, {
                            "resposta": resposta_completa,
                            "session_id": session_id,
                            "project_id": project_id,
                            "model_requested": last_model_req,
                            "model_used": last_model_eff,
                            "provider_used": last_prov_used,
                            "fallback_reason": last_fb_reason,
                        }, owner_token=owner_token)
                    else:
                        # Falha de persistencia ou stream: libera claim para permitir retry seguro
                        release_idempotent_request(idempotency_key, owner_token=owner_token)

            async with turn_lock_context(idempotency_key):
                await _persist_under_lock()

        # P0 STREAMING: Em erro de persistencia ou falha de stream, NAO enviar done:true
        if stream_completed_ok and persisted_ok:
            yield f"data: {json.dumps({'done': True, 'session_id': session_id}, ensure_ascii=False)}\n\n"
        else:
            error_code = "PERSISTENCE_FAILED" if not persisted_ok else "STREAM_INCOMPLETE"
            error_detail = "Falha ao persistir a resposta da IA de forma duravel." if not persisted_ok else "Streaming interrompido antes da conclusao."
            yield f"data: {json.dumps({'error': error_detail, 'code': error_code, 'retryable': True, 'session_id': session_id}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")




@app.post("/internal/smoke-chat-auth-flow", response_model=MensagemResponse)
async def internal_smoke_chat_auth_flow(
    x_internal_smoke_token: Optional[str] = Header(default=None),
):
    """Executa o fluxo real de /chat com usuario sintetico interno."""
    expected = getattr(app_config, "INTERNAL_SMOKE_TOKEN", "")
    if not expected or x_internal_smoke_token != expected:
        raise HTTPException(status_code=401, detail="invalid_internal_smoke_token")

    request = MensagemRequest(
        mensagem="Responda apenas: HELPUS_INTERNAL_AUTH_FLOW_OK",
        pesquisar_web=False,
        project_id="internal-smoke",
    )
    usuario = {
        "email": "smoke@internal.helpus",
        "name": "HelpUS Internal Smoke",
        "sub": "internal-smoke-user",
    }
    return await chat(request, usuario=usuario)

@app.get("/memorias")
async def listar_memorias(
    project_id: str = "general",
    include_disabled: bool = False,
    usuario = Depends(obter_usuario_google),
):
    """Lista memorias ativas do projeto para o usuario autenticado."""
    if not usuario:
        raise HTTPException(status_code=401, detail="Login Google obrigatorio.")
    user_email = usuario.get("email") if isinstance(usuario, dict) else str(usuario)
    if project_id and project_id != "general":
        if not await banco.verificar_propriedade_projeto(project_id, user_email):
            raise HTTPException(status_code=403, detail="Acesso negado: projeto pertence a outra conta.")

    try:
        return {
            "project_id": project_id or "general",
            "memorias": await banco.listar_memorias_projeto(
                project_id=project_id or "general",
                include_disabled=include_disabled,
                limite=100,
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memorias")
async def criar_memoria(
    request: ProjectMemoryRequest,
    usuario = Depends(obter_usuario_google),
):
    """Cria uma memoria ativa de projeto."""
    if not usuario:
        raise HTTPException(status_code=401, detail="Login Google obrigatorio.")

    title = (request.title or "").strip()
    content = (request.content or "").strip()

    if not title:
        raise HTTPException(status_code=400, detail="Titulo da memoria e obrigatorio.")
    if not content:
        raise HTTPException(status_code=400, detail="Conteudo da memoria e obrigatorio.")

    if len(title) > 160:
        raise HTTPException(status_code=400, detail="Titulo da memoria deve ter ate 160 caracteres.")
    if len(content) > 4000:
        raise HTTPException(status_code=400, detail="Conteudo da memoria deve ter ate 4000 caracteres.")

    user_email = usuario.get("email") if isinstance(usuario, dict) else str(usuario)
    target_project = (request.project_id or "general")[:80]
    if target_project and target_project != "general":
        if not await banco.verificar_propriedade_projeto(target_project, user_email):
            raise HTTPException(status_code=403, detail="Acesso negado: projeto pertence a outra conta.")

    try:
        memoria = await banco.criar_memoria_projeto(
            project_id=target_project,
            title=title,
            content=content,
            tags=(request.tags or "")[:300],
            created_by=usuario.get("email"),
        )
        return {"memoria": memoria}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/memorias/{memory_id}")
async def atualizar_memoria(
    memory_id: int,
    request: ProjectMemoryUpdateRequest,
    usuario = Depends(obter_usuario_google),
):
    """Atualiza ou ativa/desativa uma memoria de projeto."""
    if not usuario:
        raise HTTPException(status_code=401, detail="Login Google obrigatorio.")

    if request.title is not None and len(request.title.strip()) > 160:
        raise HTTPException(status_code=400, detail="Titulo da memoria deve ter ate 160 caracteres.")
    if request.content is not None and len(request.content.strip()) > 4000:
        raise HTTPException(status_code=400, detail="Conteudo da memoria deve ter ate 4000 caracteres.")

    try:
        memoria = await banco.atualizar_memoria_projeto(
            memory_id=memory_id,
            project_id=(request.project_id or "general")[:80],
            title=request.title.strip() if request.title is not None else None,
            content=request.content.strip() if request.content is not None else None,
            tags=(request.tags or "")[:300] if request.tags is not None else None,
            enabled=request.enabled,
        )
        if not memoria:
            raise HTTPException(status_code=404, detail="Memoria nao encontrada.")
        return {"memoria": memoria}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RenomearConversaRequest(BaseModel):
    titulo: str

class MoverConversaProjetoRequest(BaseModel):
    project_id: str

class CriarProjetoRequest(BaseModel):
    project_id: Optional[str] = None
    nome: str
    descricao: Optional[str] = ""
    instrucoes: Optional[str] = ""

@app.get("/conversas")
async def listar_conversas(project_id: Optional[str] = None, usuario = Depends(obter_usuario_google)):
    if not usuario:
        return {"conversas": []}

    try:
        return {
            "conversas": await banco.listar_conversas_usuario(usuario["email"], limite=50, project_id=project_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/historico/{session_id}")
async def historico(session_id: str, usuario = Depends(obter_usuario_google)):
    """Recupera historico de uma conversa"""
    try:
        mensagens = await banco.carregar_mensagens(session_id, limite=100, user_email=usuario["email"] if usuario else None)
        return {
            "session_id": session_id,
            "quantidade": len(mensagens),
            "mensagens": mensagens
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/conversa/{session_id}")
async def apagar_conversa(session_id: str, usuario = Depends(obter_usuario_google)):
    """Apaga uma conversa inteira"""
    try:
        await banco.apagar_conversa(session_id, user_email=usuario["email"] if usuario else None)
        return {"status": "apagada", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/conversa/{session_id}")
async def renomear_conversa(session_id: str, request: RenomearConversaRequest, usuario = Depends(obter_usuario_google)):
    """Renomeia o titulo de uma conversa"""
    try:
        await banco.renomear_conversa(session_id, request.titulo, user_email=usuario["email"] if usuario else None)
        return {"status": "renomeada", "session_id": session_id, "titulo": request.titulo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/conversa/{session_id}/projeto")
async def mover_conversa_projeto(session_id: str, request: MoverConversaProjetoRequest, usuario = Depends(obter_usuario_google)):
    """Move uma conversa para outro projeto"""
    try:
        await banco.mover_conversa_projeto(session_id, request.project_id, user_email=usuario["email"] if usuario else None)
        return {"status": "movida", "session_id": session_id, "project_id": request.project_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projetos")
async def listar_projetos(usuario = Depends(obter_usuario_google)):
    """Lista todos os projetos disponiveis para o usuario"""
    try:
        email = usuario["email"] if usuario else None
        return {"projetos": await banco.listar_projetos(email)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projetos")
async def criar_projeto(request: CriarProjetoRequest, usuario = Depends(obter_usuario_google)):
    """Cria um novo projeto com instrucoes personalizadas"""
    try:
        email = usuario["email"] if usuario else None
        pid = request.project_id or f"proj_{uuid.uuid4().hex[:8]}"
        projeto = await banco.criar_projeto(
            project_id=pid,
            nome=request.nome,
            descricao=request.descricao or "",
            instrucoes=request.instrucoes or "",
            user_email=email,
        )
        return {"projeto": projeto}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/indexar")
async def indexar_site(request: IndexarRequest):
    """Indexa um site para buscas offline"""
    if not buscador:
        raise HTTPException(status_code=503, detail="Buscador nao inicializado")

    try:
        paginas = await buscador.indexar_site(request.url, request.profundidade)
        return {
            "status": "sucesso",
            "url": request.url,
            "paginas_indexadas": paginas,
            "total_acumulado": getattr(buscador, 'paginas_indexadas', 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/audit-log")
async def admin_audit_log(
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    usuario = Depends(obter_admin_google)
):
    """Retorna a trilha de auditoria administrativa real e persistida (sem segredos, tokens ou dados sensiveis)."""
    admin_email = usuario.get("email") if isinstance(usuario, dict) else str(usuario)
    try:
        eventos, total = await banco.listar_eventos_auditoria(limite=limite, offset=offset)
        await banco.registrar_evento_auditoria(
            action="ADMIN_AUDIT_LOG_VIEWED",
            actor=admin_email,
            details={"limite": limite, "offset": offset, "returned_count": len(eventos)},
            correlation_id=str(uuid.uuid4())
        )
        corr_id = str(uuid.uuid4())
        return {
            "ok": True,
            "admin": admin_email,
            "total_eventos": total,
            "limite": limite,
            "offset": offset,
            "correlation_id": corr_id,
            "eventos": eventos
        }
    except Exception as err:
        print(f"[ERROR] Falha ao processar trilha de auditoria administrativa: {_sanitize_log_message(err)}")
        raise HTTPException(status_code=503, detail="Servico de auditoria temporariamente indisponivel.") from None

@app.get("/saude")
async def verificar_saude():
    """Endpoint de health check"""
    return {
        "status": "saudavel",
        "modelo_ok": cerebro is not None
    }

@app.post("/local/plan/proposals")
async def local_plan_proposal_create(request: dict, usuario = Depends(obter_admin_google)):
    try:
        from backend.local_plan_audit import create_local_plan_proposal
    except ModuleNotFoundError:
        from local_plan_audit import create_local_plan_proposal
    return create_local_plan_proposal(request)


@app.get("/local/plan/proposals")
async def local_plan_proposal_list(limit: int = 50, usuario = Depends(obter_admin_google)):
    try:
        from backend.local_plan_audit import list_local_plan_proposals
    except ModuleNotFoundError:
        from local_plan_audit import list_local_plan_proposals
    return list_local_plan_proposals(limit)

@app.get("/local/plan/proposals/summary")
async def local_plan_proposal_summary(limit: int = 200, usuario = Depends(obter_admin_google)):
    try:
        from backend.local_plan_audit import summarize_local_plan_proposals
    except ModuleNotFoundError:
        from local_plan_audit import summarize_local_plan_proposals

    return summarize_local_plan_proposals(limit)

@app.get("/local/plan/proposals/verify")
async def get_local_plan_proposal_integrity():
    try:
        from backend.local_plan_audit import verify_local_plan_proposal_integrity
    except ModuleNotFoundError:
        from local_plan_audit import verify_local_plan_proposal_integrity

    return verify_local_plan_proposal_integrity()


@app.get("/local/plan/proposals/{proposal_id}")
async def local_plan_proposal_detail(proposal_id: str, usuario=Depends(obter_admin_google)):
    return get_local_plan_proposal(proposal_id)


# ===== MÓDULOS AVANÇADOS: CRM, GOOGLE CALENDAR E GERADOR DE PROPOSTAS =====

class AgendamentoRequest(BaseModel):
    titulo: str = "Reunião Comercial HelpUS"
    data: str = "2026-09-15"
    hora: str = "14:00"
    duracao_minutos: int = 45
    descricao: Optional[str] = "Alinhamento de projeto de Inteligência Artificial e Desenvolvimento."
    cliente_email: Optional[str] = None

class PropostaRequest(BaseModel):
    cliente_nome: str = "Cliente HelpUS"
    servico: str = "Desenvolvimento de Plataforma Web com IA Integrada"
    valor_estimado: str = "R$ 3.500,00"
    detalhes: Optional[str] = "Inclusão de módulo de chat multimodal, integração com WhatsApp e síntese de voz neural."

# Armazenamento em memória para estados de handoff do CRM
crm_handoff_states: Dict[str, Dict] = {}

@app.get("/admin/atendimentos")
async def admin_atendimentos(usuario = Depends(obter_admin_google)):
    """Retorna listagem de atendimentos ativos para o CRM Administrativo"""
    conversas_banco = []
    try:
        if banco:
            conversas_banco = await banco.listar_conversas_usuario(usuario["email"], limite=50)
    except Exception as _e:
        pass

    return {
        "total": len(conversas_banco),
        "handoff_ativos": crm_handoff_states,
        "conversas": conversas_banco
    }

@app.post("/admin/handoff")
async def admin_toggle_handoff(request: dict, usuario = Depends(obter_admin_google)):
    """Ativa ou desativa o atendimento humano para uma conversa"""
    session_id = request.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id e obrigatorio")

    status_atual = crm_handoff_states.get(session_id, {}).get("ativo", False)
    novo_status = not status_atual

    crm_handoff_states[session_id] = {
        "ativo": novo_status,
        "alterado_por": usuario.get("email"),
        "timestamp": time.time()
    }

    return {
        "session_id": session_id,
        "handoff_ativo": novo_status,
        "mensagem": f"Transbordo humano {'ativado' if novo_status else 'desativado'} com sucesso."
    }

@app.post("/admin/responder")
async def admin_responder_atendimento(request: dict, usuario = Depends(obter_admin_google)):
    """Permite ao atendente humano enviar uma resposta manual"""
    session_id = request.get("session_id")
    mensagem = request.get("mensagem", "").strip()

    if not session_id or not mensagem:
        raise HTTPException(status_code=400, detail="session_id e mensagem sao obrigatorios")

    try:
        if banco:
            await banco.salvar_mensagem(
                session_id=session_id,
                role="assistant",
                content=f"[Atendente Humano - {usuario.get('name', 'Equipe')}]: {mensagem}",
                user_email=usuario.get("email"),
                project_id="crm-human"
            )
    except Exception as _e:
        pass

    return {
        "status": "enviado",
        "session_id": session_id,
        "mensagem": mensagem
    }

@app.post("/agendar")
async def criar_agendamento_calendar(request: AgendamentoRequest):
    """Gera link direto de agendamento no Google Calendar e formato ICS"""
    import urllib.parse
    from datetime import datetime, timedelta

    titulo = request.titulo or "Reunião Comercial HelpUS"
    desc = request.descricao or "Reunião de alinhamento técnico HelpUS"
    
    # Formatação de datas
    data_hora_str = f"{request.data} {request.hora}"
    try:
        dt_inicio = datetime.strptime(data_hora_str, "%Y-%m-%d %H:%M")
    except Exception:
        dt_inicio = datetime.now() + timedelta(days=1)

    dt_fim = dt_inicio + timedelta(minutes=request.duracao_minutos)

    fmt_cal = "%Y%m%dT%H%M00"
    dates_param = f"{dt_inicio.strftime(fmt_cal)}/{dt_fim.strftime(fmt_cal)}"

    params = {
        "action": "TEMPLATE",
        "text": titulo,
        "details": desc,
        "location": "Google Meet / HelpUS Online",
        "dates": dates_param
    }
    
    if request.cliente_email:
        params["add"] = request.cliente_email

    google_calendar_url = f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//HelpUS AI//Agendamento Comercial//PT
BEGIN:VEVENT
SUMMARY:{titulo}
DESCRIPTION:{desc}
DTSTART:{dt_inicio.strftime(fmt_cal)}
DTEND:{dt_fim.strftime(fmt_cal)}
LOCATION:Google Meet / HelpUS Online
END:VEVENT
END:VCALENDAR"""

    return {
        "status": "sucesso",
        "titulo": titulo,
        "inicio": dt_inicio.isoformat(),
        "fim": dt_fim.isoformat(),
        "google_calendar_url": google_calendar_url,
        "ics_content": ics_content
    }

@app.post("/gerar-proposta")
async def gerar_proposta_comercial(request: PropostaRequest):
    """Gera proposta comercial corporativa formatada em HTML/SVG pronta para exportacao em PDF"""
    html_proposta = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Proposta Comercial - HelpUS AI</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; color: #1f2937; background: #f9fafb; }}
        .card {{ background: #ffffff; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #e5e7eb; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #3b82f6; padding-bottom: 20px; }}
        .logo {{ font-size: 28px; font-weight: 800; color: #1e3a8a; }}
        .badge {{ background: #dbeafe; color: #1e40af; padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 12px; }}
        .section {{ margin-top: 30px; }}
        .title {{ font-size: 18px; font-weight: 700; color: #1f2937; margin-bottom: 10px; }}
        .value {{ font-size: 24px; font-weight: 800; color: #059669; margin-top: 10px; }}
        .footer {{ margin-top: 40px; font-size: 12px; color: #6b7280; text-align: center; border-top: 1px solid #e5e7eb; padding-top: 20px; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <div class="logo">HelpUS <span style="color:#3b82f6;">AI</span></div>
            <div class="badge">PROPOSTA COMERCIAL</div>
        </div>
        <div class="section">
            <p><strong>Cliente:</strong> {request.cliente_nome}</p>
            <p><strong>Data de Emissão:</strong> {time.strftime("%d/%m/%Y")}</p>
        </div>
        <div class="section">
            <div class="title">Escopo do Serviço</div>
            <p>{request.servico}</p>
            <p style="color:#4b5563; font-size:14px; line-height:1.6;">{request.detalhes}</p>
        </div>
        <div class="section">
            <div class="title">Investimento Estimado</div>
            <div class="value">{request.valor_estimado}</div>
        </div>
        <div class="footer">
            HelpUS Inteligência Artificial & Soluções Tecnológicas · www.helpusbr.com · ai.helpusbr.com
        </div>
    </div>
</body>
</html>"""
    return {
        "status": "sucesso",
        "cliente_nome": request.cliente_nome,
        "servico": request.servico,
        "valor_estimado": request.valor_estimado,
        "html_content": html_proposta
    }
