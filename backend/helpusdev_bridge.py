"""Módulo HelpUSDev Bridge.
Gerencia a conexão assíncrona bidirecional e transparente entre a AI HelpUS (nuvem)
e o HelpUSDev rodando no computador local do usuário.
"""
import os
import re
import time
import uuid
import asyncio
from typing import Dict, Optional, Tuple
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

def detectar_intencao_local(texto: str) -> Optional[Tuple[str, dict]]:
    """Analisa a mensagem do usuário para identificar comandos ou pedidos de acesso ao computador local."""
    if not texto:
        return None

    texto_lower = texto.lower()

    # Gatilhos indicativos de computador local / arquivos / comandos
    gatilhos = [
        "meu computador", "meu pc", "minha máquina", "minha maquina",
        "localmente", "no computador", "no pc", "helpusdev",
        "d:\\", "c:\\", "pasta", "diretorio", "diretório",
        "execute", "executar", "rode", "rodar", "terminal", "powershell", "cmd",
        "leia o arquivo", "ler o arquivo", "veja o arquivo", "ver o arquivo", "conteudo do arquivo", "conteúdo do arquivo",
        "liste os arquivos", "listar arquivos", "liste a pasta", "listar pasta"
    ]

    tem_gatilho = any(g in texto_lower for g in gatilhos)
    if not tem_gatilho:
        return None

    # 1. Comando de terminal / PowerShell / script
    if any(k in texto_lower for k in ["comando", "powershell", "terminal", "execute", "executar", "rode", "rodar"]):
        # Tenta extrair comando entre aspas ou crases
        m_code = re.search(r"[`'\"]([^`'\"]+)[\"']", texto)
        if m_code:
            cmd_str = m_code.group(1).strip()
            if cmd_str and not cmd_str.startswith("http"):
                return ("run_command", {"command": cmd_str})
        
        # Tenta extrair comando após palavras-chave
        m_cmd = re.search(r"(?:comando|rode|execute|rodar|executar)\s+(?:o\s+)?(?:powershell\s+|cmd\s+)?([^\n\.,;]+)", texto, re.IGNORECASE)
        if m_cmd:
            cmd_clean = m_cmd.group(1).strip()
            if len(cmd_clean) > 1 and not any(w in cmd_clean.lower() for w in ["arquivo", "pasta", "diretorio"]):
                return ("run_command", {"command": cmd_clean})

    # 2. Ler arquivo local
    if any(k in texto_lower for k in ["leia", "ler", "veja", "abrir", "abra", "conteudo", "conteúdo"]):
        m_path = re.search(r"([a-zA-Z]:\\[^ \t\n\r\"']+|[\w\-\.\/\\_]+\.[a-zA-Z0-9]{1,6})", texto)
        if m_path:
            return ("view_file", {"path": m_path.group(1).strip()})

    # 3. Listar pasta / diretório
    if any(k in texto_lower for k in ["liste", "listar", "quais arquivos", "conteudo da pasta", "arquivos da pasta", "arquivos em"]):
        m_dir = re.search(r"([a-zA-Z]:\\[^ \t\n\r\"']+|[\w\-\.\/\\_]+)", texto)
        dir_path = m_dir.group(1).strip() if m_dir else "D:\\AntiG"
        return ("list_directory", {"path": dir_path})

    return None
