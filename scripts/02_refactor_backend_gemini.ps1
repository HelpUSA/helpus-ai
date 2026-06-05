param(
  [string]$ProjectRoot = "D:/dev/ai"
)

$ErrorActionPreference = "Stop"

function WriteFile($Path, $Lines) {
  $parent = Split-Path -Parent $Path
  New-Item -ItemType Directory -Force -Path $parent | Out-Null
  Set-Content -LiteralPath $Path -Value $Lines -Encoding utf8
}

$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$backend = Join-Path $root "backend"

Write-Output "[gemini] Refactoring backend in $backend"

WriteFile (Join-Path $backend "requirements.txt") @(
"fastapi==0.109.0",
"uvicorn[standard]==0.25.0",
"httpx==0.26.0",
"beautifulsoup4==4.12.2",
"asyncpg==0.29.0",
"python-dotenv==1.0.0",
"pydantic==2.5.3",
"google-genai==1.48.0"
)

WriteFile (Join-Path $backend "config.py") @(
"# -*- coding: utf-8 -*-",
"import os",
"from pathlib import Path",
"from dotenv import load_dotenv",
"",
"BASE_DIR = Path(__file__).parent",
"load_dotenv(BASE_DIR / '.env')",
"",
"DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/assistente')",
"AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini').lower().strip()",
"GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')",
"GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')",
"MODEL_PATH = os.getenv('MODEL_PATH', str(BASE_DIR / 'modelos' / 'qwen2.5-3b-instruct-q4_k_m.gguf'))",
"",
"MODEL_CONFIG = {",
"    'n_ctx': int(os.getenv('MODEL_N_CTX', '4096')),",
"    'n_threads': int(os.getenv('MODEL_N_THREADS', '4')),",
"    'n_batch': int(os.getenv('MODEL_N_BATCH', '256')),",
"    'max_tokens': int(os.getenv('MODEL_MAX_TOKENS', '800')),",
"    'temperature': float(os.getenv('MODEL_TEMPERATURE', '0.7')),",
"}",
"",
"SEARCH_CONFIG = {'user_agent': 'HelpUS/1.0', 'timeout': 15.0, 'max_results': 5}",
"ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')",
"DEBUG = ENVIRONMENT == 'development'"
)

WriteFile (Join-Path $backend "cerebro.py") @(
"# -*- coding: utf-8 -*-",
"import asyncio",
"import time",
"from typing import List, Dict, Tuple",
"from config import AI_PROVIDER, GEMINI_API_KEY, GEMINI_MODEL, MODEL_PATH, MODEL_CONFIG",
"",
"class CerebroIA:",
"    def __init__(self):",
"        self.provider = AI_PROVIDER",
"        self.nome_modelo = self.provider",
"        if self.provider == 'gemini':",
"            self.nome_modelo = GEMINI_MODEL",
"            if not GEMINI_API_KEY:",
"                raise RuntimeError('GEMINI_API_KEY não configurada.')",
"            from google import genai",
"            self.client = genai.Client(api_key=GEMINI_API_KEY)",
"            return",
"        if self.provider == 'local':",
"            self.nome_modelo = 'Local GGUF'",
"            from llama_cpp import Llama",
"            self.llm = Llama(model_path=MODEL_PATH, n_ctx=MODEL_CONFIG['n_ctx'], n_threads=MODEL_CONFIG['n_threads'], n_batch=MODEL_CONFIG['n_batch'], verbose=False)",
"            return",
"        raise RuntimeError(f'AI_PROVIDER inválido: {self.provider}')",
"",
"    def _construir_prompt(self, pergunta: str, contexto_busca: str = '', historico: List[Dict] = None) -> str:",
"        partes = ['Você é o HelpUS, um assistente virtual profissional em português do Brasil.', 'Responda de forma clara, amigável e objetiva.']",
"        if historico:",
"            partes.append('\nHistórico recente:')",
"            for msg in historico[-6:]:",
"                partes.append(f""{msg.get('role', 'user')}: {msg.get('content', '')}"")",
"        if contexto_busca:",
"            partes.append('\nContexto de pesquisa:')",
"            partes.append(contexto_busca)",
"        partes.append('\nPergunta:')",
"        partes.append(pergunta)",
"        return '\n'.join(partes)",
"",
"    async def pensar(self, pergunta: str, contexto_busca: str = '', historico: List[Dict] = None, max_tokens: int = None) -> Tuple[str, int, float]:",
"        inicio = time.time()",
"        prompt = self._construir_prompt(pergunta, contexto_busca, historico)",
"        max_tokens = max_tokens or MODEL_CONFIG['max_tokens']",
"        if self.provider == 'gemini':",
"            resposta = await asyncio.to_thread(self.client.models.generate_content, model=GEMINI_MODEL, contents=prompt)",
"            texto = (getattr(resposta, 'text', '') or '').strip()",
"            return texto, 0, round(time.time() - inicio, 2)",
"        def gerar():",
"            return self.llm(prompt, max_tokens=max_tokens, temperature=MODEL_CONFIG['temperature'], stop=['<|im_end|>'], echo=False)",
"        resultado = await asyncio.to_thread(gerar)",
"        texto = resultado['choices'][0]['text'].strip()",
"        tokens = resultado.get('usage', {}).get('completion_tokens', 0)",
"        return texto, tokens, round(time.time() - inicio, 2)"
)

WriteFile (Join-Path $backend ".env.example") @(
"DATABASE_URL=postgresql://postgres:postgres@localhost:5432/assistente",
"ENVIRONMENT=development",
"",
"AI_PROVIDER=gemini",
"GEMINI_API_KEY=coloque_sua_chave_aqui",
"GEMINI_MODEL=gemini-2.5-flash-lite",
"",
"# Somente para fallback local:",
"MODEL_PATH=./modelos/qwen2.5-3b-instruct-q4_k_m.gguf"
)

WriteFile (Join-Path $backend "Dockerfile") @(
"FROM python:3.11-slim",
"WORKDIR /app",
"RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*",
"COPY requirements.txt .",
"RUN pip install --no-cache-dir -r requirements.txt",
"COPY . .",
"EXPOSE 8000",
"CMD [""uvicorn"", ""main:app"", ""--host"", ""0.0.0.0"", ""--port"", ""8000"", ""--workers"", ""1""]"
)

WriteFile (Join-Path $root "docker-compose.yml") @(
'version: "3.8"',
"",
"services:",
"  db:",
"    image: postgres:15",
"    environment:",
"      POSTGRES_USER: postgres",
"      POSTGRES_PASSWORD: postgres",
"      POSTGRES_DB: assistente",
"    ports:",
'      - "5432:5432"',
"    volumes:",
"      - pgdata:/var/lib/postgresql/data",
"",
"  api:",
"    build:",
"      context: ./backend",
"      dockerfile: Dockerfile",
"    ports:",
'      - "8000:8000"',
"    environment:",
"      DATABASE_URL: postgresql://postgres:postgres@db:5432/assistente",
"      ENVIRONMENT: development",
"      AI_PROVIDER: gemini",
"      GEMINI_MODEL: gemini-2.5-flash-lite",
'      GEMINI_API_KEY: ${GEMINI_API_KEY}',
"    depends_on:",
"      - db",
"    restart: unless-stopped",
"",
"volumes:",
"  pgdata:"
)

Write-Output "[gemini] Python compile check..."
python -m py_compile `
  (Join-Path $backend "config.py") `
  (Join-Path $backend "cerebro.py") `
  (Join-Path $backend "main.py") `
  (Join-Path $backend "banco.py") `
  (Join-Path $backend "buscador.py")

Write-Output "[gemini] Done."