# -*- coding: utf-8 -*-
"""
API Principal - HelpUS.
Orquestra: banco de dados, cerebro IA e motor de busca.
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import List, Optional, Dict
import time
import uuid
import os
from pathlib import Path
from contextlib import asynccontextmanager

import config as app_config
from config import DEBUG, CORS_ORIGINS
from banco import BancoDados
from cerebro import CerebroIA
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
class MensagemRequest(BaseModel):
    mensagem: str
    session_id: Optional[str] = None
    pesquisar_web: bool = True
    project_id: Optional[str] = 'general'
    image_base64: Optional[str] = None
    image_url: Optional[str] = None

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
    # Agentes internos controlados por HELPUS_INTERNAL_AGENTS_ENABLED.
    agent_trace = [
        {"label": "Analisando pedido", "status": "done"}
    ]

    try:
        # Carrega historico
        historico = []
        try:
            historico = await banco.carregar_mensagens(session_id, limite=10)
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


        # Salva pergunta
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

        # Gera resposta
        agent_trace.append({"label": "Chamando modelo de IA", "status": "running"})
        resposta, tokens, tempo_ia = await c.pensar(
            pergunta=request.mensagem,
            contexto_busca="\n\n".join([parte for parte in [contexto_memorias, contexto_memoria_interna, contexto_busca] if parte]),
            historico=historico,
            image_base64=request.image_base64,
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

        return MensagemResponse(
            resposta=resposta,
            session_id=session_id,
            project_id=project_id,
            fontes=fontes,
            tempo_total=tempo_total,
            tokens_gerados=tokens,
            provider_used=getattr(c, "last_provider_used", getattr(c, "provider", "")),
            fallback_reason=getattr(c, "last_fallback_reason", None),
            provider_configured=getattr(app_config, "AI_PROVIDER", ""),
            model=getattr(c, "nome_modelo", ""),
            latency_ms=round(tempo_ia * 1000, 2) if isinstance(tempo_ia, (int, float)) else None,
            agent_trace=agent_trace,
        )


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

    async def event_generator():
        async for chunk in c.pensar_stream(
            pergunta=request.mensagem,
            image_base64=request.image_base64,
            image_url=request.image_url,
        ):
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
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

    try:
        memoria = await banco.criar_memoria_projeto(
            project_id=(request.project_id or "general")[:80],
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


@app.get("/conversas")
async def listar_conversas(usuario = Depends(obter_usuario_google)):
    """Lista conversas do usuario autenticado"""
    if not usuario:
        raise HTTPException(status_code=401, detail="Login Google obrigatorio.")

    try:
        return {
            "conversas": await banco.listar_conversas_usuario(usuario["email"], limite=50)
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
