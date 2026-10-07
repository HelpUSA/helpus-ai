"""Módulo HelpUSDev Bridge.
Gerencia a conexão assíncrona bidirecional e transparente entre a AI HelpUS (nuvem)
e o HelpUSDev rodando no computador local do usuário.
"""
import os
import re
import time
import uuid
import asyncio
from typing import Dict, Optional, Tuple, List
from pydantic import BaseModel

# Fila assíncrona de comandos aguardando execução no HelpUSDev local
helpusdev_pending_commands: asyncio.Queue = asyncio.Queue()
helpusdev_command_results: Dict[str, asyncio.Future] = {}
helpusdev_last_seen: float = 0.0

class BridgeResultRequest(BaseModel):
    command_id: str
    status: str
    output: Optional[str] = ""

def registrar_presenca_helpusdev():
    global helpusdev_last_seen
    helpusdev_last_seen = time.time()

def is_helpusdev_online() -> bool:
    if helpusdev_last_seen <= 0:
        return False
    return (time.time() - helpusdev_last_seen) < 45.0

def segundos_desde_ultima_presenca() -> Optional[float]:
    if helpusdev_last_seen <= 0:
        return None
    return round(time.time() - helpusdev_last_seen, 1)

async def obter_proximo_comando(timeout: float = 20.0) -> Optional[dict]:
    registrar_presenca_helpusdev()
    try:
        return await asyncio.wait_for(helpusdev_pending_commands.get(), timeout=timeout)
    except asyncio.TimeoutError:
        return None

def processar_resultado_comando(command_id: str, status: str, output: str):
    registrar_presenca_helpusdev()
    fut = helpusdev_command_results.get(command_id)
    if fut and not fut.done():
        fut.set_result({"status": status, "output": output})

async def executar_no_computador_local(action: str, params: dict, timeout: float = 25.0) -> dict:
    """Envia um comando para o HelpUSDev local e aguarda o resultado."""
    cmd_id = f"cmd_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
    loop = asyncio.get_event_loop()
    fut = loop.create_future()
    helpusdev_command_results[cmd_id] = fut
    await helpusdev_pending_commands.put({"command_id": cmd_id, "action": action, "params": params})

    try:
        res = await asyncio.wait_for(fut, timeout=timeout)
        return res
    except asyncio.TimeoutError:
        return {
            "status": "error",
            "output": "Tempo esgotado: o HelpUSDev não respondeu à solicitação a tempo. Certifique-se de que a aplicação HelpUSDev está aberta no computador.",
        }
    finally:
        helpusdev_command_results.pop(cmd_id, None)

def extrair_caminho_ou_unidade(texto: str) -> Optional[str]:
    r"""Extrai caminhos como 'D:\', 'D:\AntiG', 'unidade D:', 'unidade D'."""
    if not texto:
        return None
    # 1. Unidade com letra explícita (ex: unidade D, unidade D:)
    m_unidade = re.search(r"unidade\s+([a-zA-Z])(?::)?", texto, re.IGNORECASE)
    if m_unidade:
        return f"{m_unidade.group(1).upper()}:\\"

    # 2. Caminho absoluto Windows com barra invertida (ex: D:\AntiG\teste.txt ou D:\)
    m_abs = re.search(r"([a-zA-Z]:\\[^ \t\n\r\"']*)", texto)
    if m_abs:
        return m_abs.group(1).strip()

    # 3. Apenas letra de unidade com dois-pontos (ex: D:, C:)
    m_drive = re.search(r"\b([a-zA-Z]):\b", texto)
    if m_drive:
        return f"{m_drive.group(1).upper()}:\\"

    # 4. Arquivo com extensão (ex: config.yaml, README.md)
    m_ext = re.search(r"([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9]{1,6})", texto)
    if m_ext:
        return m_ext.group(1).strip()

    return None

def detectar_intencao_local(texto: str, historico: list = None) -> Optional[Tuple[str, dict]]:
    """Analisa a mensagem do usuário (e histórico recente se necessário) para identificar comandos ou pedidos de acesso local."""
    if not texto:
        return None

    texto_lower = texto.lower()

    # Gatilhos indicativos de computador local / arquivos / comandos
    gatilhos = [
        "meu computador", "meu pc", "minha máquina", "minha maquina",
        "localmente", "no computador", "no pc", "helpusdev",
        "d:\\", "c:\\", "unidade d", "unidade c", "pasta", "diretorio", "diretório",
        "execute", "executar", "rode", "rodar", "terminal", "powershell", "cmd",
        "leia o arquivo", "ler o arquivo", "veja o arquivo", "ver o arquivo", "conteudo do arquivo", "conteúdo do arquivo",
        "liste", "listar", "listar arquivos", "liste os arquivos", "liste o diretório", "liste o diretorio", "liste a pasta"
    ]

    tem_gatilho = any(g in texto_lower for g in gatilhos)
    if not tem_gatilho:
        return None

    # Tenta extrair caminho da mensagem atual
    caminho = extrair_caminho_ou_unidade(texto)

    # Se não achou caminho na mensagem atual, busca nas mensagens recentes do histórico
    if not caminho and historico:
        for msg in reversed(historico[-4:]):
            conteudo_msg = msg.get("content", "") if isinstance(msg, dict) else ""
            caminho_ant = extrair_caminho_ou_unidade(conteudo_msg)
            if caminho_ant:
                caminho = caminho_ant
                break

    # 1. Comando de terminal / PowerShell
    if any(k in texto_lower for k in ["comando", "powershell", "terminal", "execute", "executar", "rode", "rodar"]):
        m_code = re.search(r"[`'\"]([^`'\"]+)[\"']", texto)
        if m_code:
            cmd_str = m_code.group(1).strip()
            if cmd_str and not cmd_str.startswith("http"):
                return ("run_command", {"command": cmd_str})

        m_cmd = re.search(r"(?:comando|rode|execute|rodar|executar)\s+(?:o\s+)?(?:powershell\s+|cmd\s+)?([^\n\.,;]+)", texto, re.IGNORECASE)
        if m_cmd:
            cmd_clean = m_cmd.group(1).strip()
            if len(cmd_clean) > 1 and not any(w in cmd_clean.lower() for w in ["arquivo", "pasta", "diretorio", "diretório"]):
                return ("run_command", {"command": cmd_clean})

    # 2. Listar pasta / diretório (prioridade se contiver 'diretório', 'diretorio', 'pasta', 'liste', 'listar')
    if any(k in texto_lower for k in ["diretorio", "diretório", "pasta", "liste", "listar"]):
        dir_final = caminho or "D:\\"
        return ("list_directory", {"path": dir_final})

    # 3. Ler arquivo local
    if any(k in texto_lower for k in ["leia", "ler", "veja", "abrir", "abra", "conteudo", "conteúdo"]):
        file_final = caminho or "D:\\AntiG"
        return ("view_file", {"path": file_final})

    return None
