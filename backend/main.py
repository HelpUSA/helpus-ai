# -*- coding: utf-8 -*-
"""
API Principal - HelpUS.
Orquestra: banco de dados, cerebro IA e motor de busca.
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import time
import uuid
import os
from contextlib import asynccontextmanager

import config as app_config
from config import DEBUG, CORS_ORIGINS
from banco import BancoDados
from cerebro import CerebroIA
from buscador import MotorBusca
from auth import obter_usuario_google, obter_admin_google

# ===== INICIALIZACAO DOS SERVICOS =====
banco = BancoDados()
cerebro: CerebroIA = None
buscador: MotorBusca = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa e finaliza os servicos"""
    global cerebro, buscador
    
    print("=" * 60)
    print("🚀 INICIANDO HelpUS")
    print("=" * 60)
    
    # 1. Conectar ao banco
    print("📦 Conectando ao PostgreSQL...")
    try:
        await banco.conectar()
        await banco.criar_tabelas()
        print("✅ Banco de dados pronto")
    except Exception as e:
        print(f"⚠️ Banco de dados nao disponivel: {e}")
        print("   Rodando sem banco de dados...")
    
    # 2. Carregar modelo IA
    print("🧠 Carregando modelo de IA...")
    try:
        cerebro = CerebroIA()
        print(f"✅ Modelo carregado: {cerebro.nome_modelo}")
    except Exception as e:
        print(f"❌ Erro ao carregar modelo: {e}")
        print("   A API funcionara, mas sem IA.")
    
    # 3. Inicializar buscador
    print("🔍 Inicializando motor de busca...")
    buscador = MotorBusca(banco)
    print("✅ Buscador pronto")
    
    print("=" * 60)
    print("🎯 HelpUS PRONTO PARA USO")
    print("=" * 60)
    
    yield
    
    print("👋 Encerrando servidor...")

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

def _provider_metrics(latency_ms: Optional[float] = None) -> Dict[str, object]:
    return {
        "provider_configured": getattr(app_config, "AI_PROVIDER", ""),
        "provider_used": getattr(cerebro, "last_provider_used", getattr(cerebro, "provider", "")) if cerebro else "",
        "fallback_reason": getattr(cerebro, "last_fallback_reason", None) if cerebro else None,
        "model": getattr(cerebro, "nome_modelo", "") if cerebro else "",
        "latency_ms": latency_ms,
    }

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
    return StatusResponse(
        status="online",
        modelo=cerebro.nome_modelo if cerebro else "nao carregado",
        modelo_carregado=cerebro is not None,
        paginas_indexadas=getattr(buscador, 'paginas_indexadas', 0) if buscador else 0,
        app_version=app_config.APP_VERSION,
        build_commit=app_config.BUILD_COMMIT,
        auth_required=app_config.AUTH_REQUIRED,
        provider_order=app_config.AI_PROVIDER_ORDER,
        **_provider_metrics()
    )


@app.get("/admin/status", response_model=StatusResponse)
async def admin_status(usuario = Depends(obter_admin_google)):
    """Verifica o status de todos os servicos"""
    return StatusResponse(
        status="online",
        modelo=cerebro.nome_modelo if cerebro else "nao carregado",
        modelo_carregado=cerebro is not None,
        paginas_indexadas=getattr(buscador, 'paginas_indexadas', 0) if buscador else 0,
        app_version=app_config.APP_VERSION,
        build_commit=app_config.BUILD_COMMIT,
        auth_required=app_config.AUTH_REQUIRED,
        provider_order=app_config.AI_PROVIDER_ORDER,
        **_provider_metrics()
    )

@app.post("/internal/smoke-chat", response_model=InternalSmokeChatResponse)
async def internal_smoke_chat(
    request: InternalSmokeChatRequest,
    x_internal_smoke_token: Optional[str] = Header(default=None),
):
    expected_token = os.getenv("INTERNAL_SMOKE_TOKEN", "")
    if not expected_token or x_internal_smoke_token != expected_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not cerebro:
        raise HTTPException(status_code=503, detail="Modelo de IA nao carregado.")

    inicio = time.time()
    resposta, tokens, tempo_ia = await cerebro.pensar(
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
    if not cerebro:
        raise HTTPException(
            status_code=503, 
            detail="Modelo de IA nao carregado."
        )
    
    inicio_total = time.time()
    session_id = request.session_id or str(uuid.uuid4())
    project_id = (request.project_id or 'general')[:80]
    
    try:
        # Carrega historico
        historico = []
        try:
            historico = await banco.carregar_mensagens(session_id, limite=10)
        except:
            pass
        
        # Busca na web
        fontes = []
        contexto_busca = ""
        
        if request.pesquisar_web and buscador:
            try:
                resultados = await buscador.buscar(request.mensagem)
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
                    print(f"⚠️ Erro na busca: {e}")
        
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
        
        # Gera resposta
        resposta, tokens, tempo_ia = await cerebro.pensar(
            pergunta=request.mensagem,
            contexto_busca=contexto_busca,
            historico=historico
        )
        
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
        
        tempo_total = round(time.time() - inicio_total, 2)
        
        return MensagemResponse(
            resposta=resposta,
            session_id=session_id,
            project_id=project_id,
            fontes=fontes,
            tempo_total=tempo_total,
            tokens_gerados=tokens,
            provider_used=getattr(cerebro, "last_provider_used", getattr(cerebro, "provider", "")),
            fallback_reason=getattr(cerebro, "last_fallback_reason", None),
            provider_configured=getattr(app_config, "AI_PROVIDER", ""),
            model=getattr(cerebro, "nome_modelo", ""),
            latency_ms=round(tempo_ia * 1000, 2) if isinstance(tempo_ia, (int, float)) else None
        )
        
    except Exception as e:
        if DEBUG:
            print(f"❌ Erro no chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))



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
